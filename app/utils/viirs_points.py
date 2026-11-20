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

Dots are drawn the way MapLibre draws GFW's circles. Its anti-aliasing fades
each circle from fully opaque one device pixel inside the edge to transparent
at the edge, so the small dots of low zooms are partly transparent (a 0.75
pixel radius peaks at 84% opacity on a standard screen) and pale colors almost
vanish into the basemap. Overlapping dots are blended: their colors averaged,
weighted by opacity, and their opacities combined as for layered dots, so the
result doesn't depend on drawing order. A 256-pixel tile is faded as on a
standard screen and a 512-pixel (@2x) tile as on a high-density screen.
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
from bisect import bisect_right
from datetime import date
from typing import List, Optional, Tuple

import boto3
import datashader as ds
import mercantile
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from boto3.s3.transfer import TransferConfig
from PIL import Image
from scipy.signal import fftconvolve

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
# Exponential interpolation between the radius stops, as in GFW's layer
# ({"base": 0.5, "stops": ...})
RADIUS_BASE = 0.5
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
    zoom = z - 1
    zooms, radii = zip(*RADIUS_STOPS)
    if zoom <= zooms[0]:
        return float(radii[0])
    if zoom >= zooms[-1]:
        return float(radii[-1])
    i = bisect_right(zooms, zoom) - 1
    t = (RADIUS_BASE ** (zoom - zooms[i]) - 1) / (
        RADIUS_BASE ** (zooms[i + 1] - zooms[i]) - 1
    )
    return radii[i] + t * (radii[i + 1] - radii[i])


def dot_kernel(z: int, scale: int) -> np.ndarray:
    """The opacity a dot gives each pixel around it, as a square array: entry
    [half + i, half + j] (`half` being the array's half width) is for the dot
    i grid points below and j right of the first grid point at or above and
    left of the pixel's center. Dots sit on grid points, as GFW's tiles round
    alerts to them, and a pixel of a 256 * scale tile spans
    `CELLS_PER_CSS_PIXEL / scale` grid steps each way.

    This is MapLibre's circle anti-aliasing (circle.fragment.glsl, with no blur
    or stroke): opacity is smoothstep of the distance inside the circle's edge,
    in device pixels, reaching 1 one device pixel in. A scale-1 tile is drawn
    as on a screen with one device pixel per CSS pixel, scale 2 as on one with
    two."""
    radius = dot_radius(z)
    step = CELLS_PER_CSS_PIXEL // scale  # cells across one pixel
    half = math.ceil(radius * CELLS_PER_CSS_PIXEL + step / 2)
    # grid steps from the pixel's center to each dot
    offsets = np.arange(-half, half + 1) - step / 2
    distance = np.hypot(offsets[:, None], offsets[None, :]) / CELLS_PER_CSS_PIXEL
    inside = np.clip((radius - distance) * scale, 0, 1)
    return inside * inside * (3 - 2 * inside)


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
    pixels = TILE_CSS_PIXELS * scale
    kernel = dot_kernel(z, scale)
    margin = kernel.shape[0] // 2
    left, bottom, right, top = mercantile.xy_bounds(x, y, z)
    cell = (right - left) / cells
    frame = pd.DataFrame({"x": points.x[rows], "y": points.y[rows]}, copy=False)
    # Count alerts by their nearest grid point, as GFW's tiles do: shift the
    # bins half a cell left and up, so bin i is centered on grid point i
    # (counted from the tile's west and north edges, from -margin).
    canvas = ds.Canvas(
        plot_width=cells + 2 * margin,
        plot_height=cells + 2 * margin,
        x_range=(left - (margin + 0.5) * cell, right + (margin - 0.5) * cell),
        y_range=(bottom - (margin - 0.5) * cell, top + (margin + 0.5) * cell),
    )
    # datashader's rows run south to north; images run north to south
    counts = np.flipud(canvas.points(frame, "x", "y", agg=ds.count()).values)
    rgba = np.zeros((pixels, pixels, 4), dtype=np.uint8)
    if counts.any():
        rgba = blend_dots(counts, kernel, CELLS_PER_CSS_PIXEL // scale)
    buffer = io.BytesIO()
    Image.fromarray(rgba).save(buffer, "PNG")
    return buffer.getvalue()


def blend_dots(counts: np.ndarray, kernel: np.ndarray, step: int) -> np.ndarray:
    """RGBA pixels of the dots of a grid of alert counts (with a margin of half
    the kernel's width), one pixel per `step` cells each way.

    Where dots overlap, the color is their colors' average weighted by
    opacity, and the opacity is 1 - (1 - a1)(1 - a2)..., as for dots drawn
    over each other in random order. Each is a sum over the dots around a
    pixel of a fixed function of their offset, so it's computed by
    convolution."""
    # single precision is plenty for 8-bit output and halves the FFT time
    present = (counts > 0).astype(np.float32)
    colors = COUNT_LUT[np.minimum(counts, 16), :3] * present[..., None]
    layers = np.concatenate([present[..., None], colors], axis=-1)
    # convolution flips the kernel; kernel[dy, dx] is for the dot at +dy, +dx
    flipped = kernel[::-1, ::-1].astype(np.float32)
    sums = fftconvolve(layers, flipped[..., None], mode="valid", axes=(0, 1))
    clear = np.log1p(-np.minimum(flipped, 1 - 1e-6))
    log_transparency = fftconvolve(present, clear, mode="valid")
    sums, log_transparency = sums[::step, ::step], log_transparency[::step, ::step]
    weight = sums[..., 0]
    drawn = weight > 1e-6
    rgba = np.zeros(weight.shape + (4,), dtype=np.uint8)
    rgba[drawn, :3] = np.rint(
        np.clip(sums[drawn, 1:] / weight[drawn, None], 0, 255)
    ).astype(np.uint8)
    rgba[drawn, 3] = np.rint(
        255 * np.clip(-np.expm1(log_transparency[drawn]), 0, 1)
    ).astype(np.uint8)
    return rgba


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
