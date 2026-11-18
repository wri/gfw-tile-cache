"""VIIRS fire alert points held in memory, rendered into map tiles with
datashader and searched for click details.

The alerts come from one fixed Parquet file (latitude, longitude, acq_date,
acq_time, confidence), loaded once when a server process starts.

Loading converts the Parquet into flat arrays sorted by alert date, saved as
.npy files in a local cache directory and memory-mapped. One process per
machine does the conversion (under a file lock), and every process maps the
same files, so the operating system keeps one shared copy in memory however
many workers there are.

Tiles mimic GFW's dynamic VIIRS vector layer: alerts are counted on the same
grid it aggregates them on (1024 cells across a 512-pixel vector tile, so half
a CSS pixel), each cell is drawn as a dot sized by zoom, and the dot's color
follows GFW's count ramp, from yellow-orange (one alert) to black (16 or more).
"""

import fcntl
import io
import logging
import math
import os
import shutil
import tempfile
import threading
import time
from datetime import date
from typing import List, Optional, Tuple

import boto3
import datashader as ds
import datashader.transfer_functions as tf
import mercantile
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from boto3.s3.transfer import TransferConfig
from PIL import Image

logger = logging.getLogger(__name__)

EPOCH = np.datetime64("1970-01-01", "D")
CONFIDENCE_CODES = {"l": 0, "n": 1, "h": 2}
CONFIDENCE_NAMES = {code: name for name, code in CONFIDENCE_CODES.items()}
HIGH = CONFIDENCE_CODES["h"]
ARRAYS = ("x", "y", "lat_e5", "lon_e5", "day", "time", "confidence", "high_rows")

# GFW's VIIRS layer style (layerConfig of the Resource Watch layer
# "Fire-Alerts-VIIRS-PREPROD"): circle-color interpolated linearly on the
# aggregated alert count, and circle-radius in CSS pixels by map zoom.
COUNT_COLOR_STOPS = [
    (0, "#FFDA07"),
    (1, "#FFCC00"),
    (2, "#F76000"),
    (4, "#FF0000"),
    (8, "#B51212"),
    (16, "#000000"),
]
RADIUS_STOPS = [
    (3, 0.75),
    (5, 1),
    (7, 1.5),
    (8, 1.75),
    (9, 2),
    (10, 2.5),
    (11, 3),
    (12, 4),
]
# Grid cells per CSS pixel: GFW requests @0.25x vector tiles (1024 cells
# across a 512-pixel tile).
CELLS_PER_CSS_PIXEL = 2
TILE_CSS_PIXELS = 256


def _hex_to_rgba(color: str) -> Tuple[int, int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16), 255


def count_color_lut() -> np.ndarray:
    """RGBA color for each alert count 0..16 (16 means 16 or more), linearly
    interpolated between GFW's stops. Count 0 is transparent."""
    stops = np.array([count for count, _ in COUNT_COLOR_STOPS], dtype=float)
    colors = np.array([_hex_to_rgba(color) for _, color in COUNT_COLOR_STOPS], float)
    counts = np.arange(17)
    lut = np.stack(
        [np.interp(counts, stops, colors[:, channel]) for channel in range(4)], axis=1
    )
    lut = np.rint(lut).astype(np.uint8)
    lut[0] = 0
    return lut


COUNT_LUT = count_color_lut()


def dot_radius(z: int) -> float:
    """GFW's circle radius in CSS pixels for a 256-pixel raster tile at zoom z,
    which is displayed at the scale of map zoom z - 1 (map zoom is measured
    in 512-pixel tiles)."""
    zooms, radii = zip(*RADIUS_STOPS)
    return float(np.interp(z - 1, zooms, radii))


def spread_cells(z: int) -> int:
    """How many grid cells a dot extends beyond its own cell, so its diameter
    in cells (2 * spread + 1) is close to GFW's dot diameter."""
    return max(0, round(dot_radius(z) * CELLS_PER_CSS_PIXEL - 0.5))


def to_day(value: date) -> int:
    return int((np.datetime64(value, "D") - EPOCH).astype(int))


class Points:
    """Alert arrays sorted by day, with the rows of high-confidence alerts
    (also by day) for fast high-confidence tiles."""

    def __init__(self, arrays: dict):
        self.x = arrays["x"]
        self.y = arrays["y"]
        self.lat_e5 = arrays["lat_e5"]
        self.lon_e5 = arrays["lon_e5"]
        self.day = arrays["day"]
        self.time = arrays["time"]
        self.confidence = arrays["confidence"]
        self.high_rows = arrays["high_rows"]
        self.high_day = self.day[self.high_rows]
        self.max_alert_date = str(EPOCH + int(self.day[-1]))

    def rows(self, start: date, end: date, high_confidence_only: bool):
        """The rows with alerts from `start` to `end` (inclusive): a slice of
        all rows, or an array of high-confidence row numbers."""
        bounds = [to_day(start), to_day(end) + 1]
        if high_confidence_only:
            lo, hi = np.searchsorted(self.high_day, bounds)
            return self.high_rows[lo:hi]
        lo, hi = np.searchsorted(self.day, bounds)
        return slice(lo, hi)


def convert(parquet_path: str, out_dir: str) -> None:
    """Write the alert arrays of a points Parquet file, sorted by date and
    time, as .npy files in `out_dir`."""
    table = pq.read_table(
        parquet_path,
        columns=["latitude", "longitude", "acq_date", "acq_time", "confidence"],
    )
    day = (table.column("acq_date").to_numpy().astype("datetime64[D]") - EPOCH).astype(
        np.int32
    )
    time_hhmm = pc.cast(table.column("acq_time"), "int16").to_numpy()
    order = np.lexsort((time_hhmm, day))

    def save(name: str, values: np.ndarray) -> None:
        np.save(os.path.join(out_dir, f"{name}.npy"), values)

    save("day", day[order])
    save("time", time_hhmm[order])
    names = list(CONFIDENCE_CODES)  # in code order: l, n, h
    codes = pc.index_in(table.column("confidence"), value_set=pa.array(names))
    if codes.null_count:
        raise ValueError(f"Confidence values other than {names} in {parquet_path}")
    confidence = codes.to_numpy().astype(np.uint8)[order]
    save("confidence", confidence)
    save("high_rows", np.flatnonzero(confidence == HIGH).astype(np.int32))
    del confidence
    lat = table.column("latitude").to_numpy()[order]
    lon = table.column("longitude").to_numpy()[order]
    del table, order
    save("lat_e5", np.rint(lat * 1e5).astype(np.int32))
    save("lon_e5", np.rint(lon * 1e5).astype(np.int32))
    x, y = lnglat_to_meters(lon, lat)
    del lat, lon
    save("x", x.astype(np.float32))
    save("y", y.astype(np.float32))


def download(uri: str, local_path: str) -> None:
    """Copy an s3:// object (in parallel parts) or a local file."""
    if uri.startswith("s3://"):
        bucket, _, key = uri[len("s3://") :].partition("/")
        boto3.client("s3").download_file(
            bucket, key, local_path, Config=TransferConfig(max_concurrency=16)
        )
    else:
        shutil.copyfile(uri, local_path)


def lnglat_to_meters(lon: np.ndarray, lat: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Web Mercator coordinates (EPSG:3857) of WGS84 longitude and latitude."""
    origin_shift = math.pi * 6378137
    x = lon * origin_shift / 180.0
    y = np.log(np.tan((90 + lat) * math.pi / 360.0)) * origin_shift / math.pi
    return x, y


class PointsStore:
    """The alert points of one server process, loaded on first use."""

    def __init__(self, uri: str, cache_dir: str):
        self.uri = uri
        self.cache_dir = cache_dir
        self._points: Optional[Points] = None
        self._lock = threading.Lock()

    def get(self) -> Points:
        with self._lock:
            if self._points is None:
                self._points = self._load()
            return self._points

    def _load(self) -> Points:
        directory = os.path.join(self.cache_dir, "points")
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(os.path.join(self.cache_dir, ".lock"), "w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                if not os.path.isdir(directory):
                    self._build(directory)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)
        return Points(
            {
                name: np.load(os.path.join(directory, f"{name}.npy"), mmap_mode="r")
                for name in ARRAYS
            }
        )

    def _build(self, directory: str) -> None:
        """Download and convert the file, then move the arrays into place."""
        start = time.monotonic()
        work = tempfile.mkdtemp(dir=self.cache_dir, prefix=".build-")
        try:
            local = os.path.join(work, "points.parquet")
            download(self.uri, local)
            convert(local, work)
            os.remove(local)
            os.rename(work, directory)
        except BaseException:
            shutil.rmtree(work, ignore_errors=True)
            raise
        seconds = round(time.monotonic() - start)
        logger.info(f"Converted {self.uri} in {seconds}s")


def render_tile(
    points: Points,
    z: int,
    x: int,
    y: int,
    start: date,
    end: date,
    high_confidence_only: bool,
    scale: int = 1,
) -> bytes:
    """A PNG tile of the alerts from `start` to `end`, `256 * scale` pixels
    wide, styled like GFW's VIIRS layer."""
    rows = points.rows(start, end, high_confidence_only)
    cells = TILE_CSS_PIXELS * CELLS_PER_CSS_PIXEL
    margin = spread_cells(z)
    left, bottom, right, top = mercantile.xy_bounds(x, y, z)
    cell = (right - left) / cells
    frame = pd.DataFrame({"x": points.x[rows], "y": points.y[rows]}, copy=False)
    canvas = ds.Canvas(
        plot_width=cells + 2 * margin,
        plot_height=cells + 2 * margin,
        x_range=(left - margin * cell, right + margin * cell),
        y_range=(bottom - margin * cell, top + margin * cell),
    )
    counts = canvas.points(frame, "x", "y", agg=ds.count())
    if margin:
        counts = tf.spread(counts, px=margin, shape="circle", how="max")
    grid = counts.values[margin : margin + cells, margin : margin + cells]
    # datashader's rows run south to north; images run north to south
    grid = np.flipud(grid)
    block = CELLS_PER_CSS_PIXEL // scale
    if block > 1:
        grid = grid.reshape(cells // block, block, cells // block, block).max(
            axis=(1, 3)
        )
    rgba = COUNT_LUT[np.minimum(grid, 16)]
    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, "PNG")
    return buffer.getvalue()


def nearby_alerts(
    points: Points,
    longitude: float,
    latitude: float,
    z: int,
    start: date,
    end: date,
    high_confidence_only: bool,
    radius_pixels: float = 4,
    limit: int = 20,
) -> Tuple[int, List[dict]]:
    """The alerts within `radius_pixels` (in each direction) of a point on a
    zoom-z map, newest first: the total count and up to `limit` alerts."""
    rows = points.rows(start, end, high_confidence_only)
    x, y = lnglat_to_meters(np.array([longitude]), np.array([latitude]))
    meters_per_pixel = 2 * math.pi * 6378137 / (TILE_CSS_PIXELS * 2**z)
    reach = radius_pixels * meters_per_pixel
    xs, ys = points.x[rows], points.y[rows]
    near = np.flatnonzero((np.abs(xs - x[0]) <= reach) & (np.abs(ys - y[0]) <= reach))
    selected = rows.start + near if isinstance(rows, slice) else rows[near]
    newest = selected[np.lexsort((points.time[selected], points.day[selected]))[::-1]]
    alerts = [
        {
            "latitude": int(points.lat_e5[row]) / 1e5,
            "longitude": int(points.lon_e5[row]) / 1e5,
            "alert__date": str(EPOCH + int(points.day[row])),
            "alert__time_utc": f"{int(points.time[row]):04d}",
            "confidence__cat": CONFIDENCE_NAMES[int(points.confidence[row])],
        }
        for row in newest[:limit]
    ]
    return len(selected), alerts
