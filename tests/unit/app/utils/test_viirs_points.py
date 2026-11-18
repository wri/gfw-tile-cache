import io
from datetime import date

import mercantile
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from PIL import Image

from app.utils.viirs_points import (
    COUNT_LUT,
    PointsStore,
    dot_radius,
    nearby_alerts,
    render_tile,
    spread_cells,
)


def rgba(color: str):
    return [int(color[i : i + 2], 16) for i in (1, 3, 5)] + [255]


def publish(directory, name, alerts) -> str:
    """Write alerts, as (lat, lon, date, time, confidence) tuples, to a points
    file. Returns its path."""
    path = str(directory / f"{name}.parquet")
    pq.write_table(
        pa.table(
            {
                "latitude": [a[0] for a in alerts],
                "longitude": [a[1] for a in alerts],
                "acq_date": pa.array([date.fromisoformat(a[2]) for a in alerts]),
                "acq_time": [a[3] for a in alerts],
                "confidence": [a[4] for a in alerts],
            }
        ),
        path,
    )
    return path


ALERTS = [
    (-12.30001, 22.30001, "2026-09-02", "1210", "n"),
    (-12.30001, 22.30001, "2026-09-01", "0130", "h"),
    (-12.30002, 22.30002, "2026-09-03", "0005", "l"),
    (10.5, -60.25, "2026-08-15", "1745", "n"),
]


@pytest.fixture
def store(tmp_path) -> PointsStore:
    return PointsStore(publish(tmp_path, "a", ALERTS), str(tmp_path / "cache"))


def decode(png: bytes) -> np.ndarray:
    return np.asarray(Image.open(io.BytesIO(png)).convert("RGBA"))


def pixel_of(lon: float, lat: float, z: int, size: int = 256):
    tile = mercantile.tile(lon, lat, z)
    left, bottom, right, top = mercantile.xy_bounds(tile)
    x, y = mercantile.xy(lon, lat)
    column = int((x - left) / (right - left) * size)
    row = int((top - y) / (top - bottom) * size)
    return tile, row, column


def test_count_colors_follow_gfw_ramp():
    assert COUNT_LUT[0][3] == 0
    assert list(COUNT_LUT[1]) == rgba("#FFCC00")
    assert list(COUNT_LUT[2]) == rgba("#F76000")
    assert list(COUNT_LUT[3]) == [
        round((0xF7 + 0xFF) / 2),
        round((0x60 + 0x00) / 2),
        0,
        255,
    ]
    assert list(COUNT_LUT[16]) == rgba("#000000")


def test_dot_sizes_follow_gfw_zoom_stops():
    # 256-pixel tile zoom z is shown at map zoom z - 1
    assert dot_radius(4) == 0.75
    assert dot_radius(1) == 0.75
    assert dot_radius(13) == 4
    assert dot_radius(20) == 4
    # a dot 2 * spread + 1 cells (half pixels) wide is about GFW's diameter
    assert (spread_cells(4), spread_cells(10), spread_cells(13)) == (1, 4, 8)


def test_points_are_sorted_by_date_and_time(store):
    points = store.get()

    assert list(points.day) == sorted(points.day)
    assert [int(t) for t in points.time] == [1745, 130, 1210, 5]
    assert len(points.high_rows) == 1
    assert points.max_alert_date == "2026-09-03"


def test_tile_dot_is_colored_by_alert_count(store):
    points = store.get()
    tile, row, column = pixel_of(22.30001, -12.30001, 10)

    all_alerts = decode(
        render_tile(
            points, tile.z, tile.x, tile.y, date(2026, 9, 1), date(2026, 9, 3), False
        )
    )
    one_day = decode(
        render_tile(
            points, tile.z, tile.x, tile.y, date(2026, 9, 2), date(2026, 9, 2), False
        )
    )

    # the three alerts here share one grid cell
    assert list(all_alerts[row, column]) == list(COUNT_LUT[3])
    assert list(one_day[row, column]) == rgba("#FFCC00")
    assert all_alerts.shape == (256, 256, 4)
    assert (all_alerts[..., 3] > 0).sum() < 100  # just one dot


def test_high_confidence_only_and_dates_filter_the_tile(store):
    points = store.get()
    tile, row, column = pixel_of(22.30001, -12.30001, 10)

    high = decode(
        render_tile(
            points, tile.z, tile.x, tile.y, date(2026, 9, 1), date(2026, 9, 3), True
        )
    )
    later = decode(
        render_tile(
            points, tile.z, tile.x, tile.y, date(2026, 9, 4), date(2026, 9, 30), False
        )
    )

    assert list(high[row, column]) == rgba("#FFCC00")
    assert later[..., 3].max() == 0


def test_retina_tiles_are_512_pixels(store):
    points = store.get()
    tile, row, column = pixel_of(-60.25, 10.5, 10, size=512)

    image = decode(
        render_tile(
            points,
            tile.z,
            tile.x,
            tile.y,
            date(2026, 8, 1),
            date(2026, 8, 30),
            False,
            scale=2,
        )
    )

    assert image.shape == (512, 512, 4)
    assert list(image[row, column]) == rgba("#FFCC00")


def test_dots_near_a_tile_edge_continue_into_the_next_tile(tmp_path):
    z = 12
    left, bottom, right, top = mercantile.bounds(2000, 1500, z)
    # just inside the tile's east edge
    lon, lat = right - (right - left) * 0.001, (bottom + top) / 2
    store = PointsStore(
        publish(tmp_path, "edge", [(lat, lon, "2026-09-01", "0100", "n")]),
        str(tmp_path / "cache"),
    )

    east = decode(
        render_tile(
            store.get(), z, 2001, 1500, date(2026, 9, 1), date(2026, 9, 1), False
        )
    )

    assert east[:, 0, 3].max() > 0


def test_nearby_alerts_are_newest_first_with_exact_coordinates(store):
    count, alerts = nearby_alerts(
        store.get(),
        22.30001,
        -12.30001,
        10,
        date(2026, 9, 1),
        date(2026, 9, 3),
        False,
        limit=2,
    )

    assert count == 3
    assert alerts == [
        {
            "latitude": -12.30002,
            "longitude": 22.30002,
            "alert__date": "2026-09-03",
            "alert__time_utc": "0005",
            "confidence__cat": "l",
        },
        {
            "latitude": -12.30001,
            "longitude": 22.30001,
            "alert__date": "2026-09-02",
            "alert__time_utc": "1210",
            "confidence__cat": "n",
        },
    ]


def test_nearby_alerts_respect_confidence_and_distance(store):
    points = store.get()

    high = nearby_alerts(
        points, 22.30001, -12.30001, 10, date(2026, 9, 1), date(2026, 9, 3), True
    )
    far = nearby_alerts(
        points, 23.0, -12.30001, 10, date(2026, 9, 1), date(2026, 9, 3), False
    )

    assert high[0] == 1 and high[1][0]["confidence__cat"] == "h"
    assert far == (0, [])


def test_store_reuses_arrays_converted_by_another_process(tmp_path):
    path = publish(tmp_path, "a", ALERTS)
    PointsStore(path, str(tmp_path / "cache")).get()
    (tmp_path / "a.parquet").unlink()  # a second store can't download it again

    points = PointsStore(path, str(tmp_path / "cache")).get()

    assert len(points.day) == len(ALERTS)


def test_unknown_confidence_values_fail_the_load(tmp_path):
    path = publish(tmp_path, "bad", [(1.0, 2.0, "2026-09-01", "0100", "x")])

    with pytest.raises(ValueError, match="Confidence"):
        PointsStore(path, str(tmp_path / "cache")).get()


def cluster_store(tmp_path, z, tile_x, tile_y, edge=False):
    """One cell with 20 alerts and single alerts in the 24 cells around it,
    at zoom z, in the middle of a tile or just inside its east edge."""
    cells = 512
    left, bottom, right, top = mercantile.bounds(tile_x, tile_y, z)
    size_lon = (right - left) / cells
    size_lat = (top - bottom) / cells
    column = cells - 3 if edge else cells // 2
    row = cells // 2
    alerts = []
    for dr in range(-2, 3):
        for dc in range(-2, 3):
            lon = left + (column + dc + 0.5) * size_lon
            lat = top - (row + dr + 0.5) * size_lat
            for _ in range(20 if (dr, dc) == (0, 0) else 1):
                alerts.append((lat, lon, "2026-09-01", "0100", "n"))
    return PointsStore(publish(tmp_path, "cluster", alerts), str(tmp_path / "cache"))


def test_a_dense_cell_does_not_cover_its_overlapping_neighbors(tmp_path):
    z, x, y = 9, 300, 200
    store = cluster_store(tmp_path, z, x, y)

    image = decode(
        render_tile(
            store.get(), z, x, y, date(2026, 9, 1), date(2026, 9, 1), False, scale=2
        )
    )

    drawn = image[..., 3] > 0
    black = (image[..., :3] == 0).all(axis=-1) & drawn
    assert spread_cells(z) >= 2  # the dots overlap
    # 1 of the 25 cells is black, and its dot is mostly or wholly under
    # others; drawing the highest count on top made about a quarter black
    assert black.sum() < drawn.sum() / 10


def test_a_cluster_across_a_tile_edge_is_drawn_whole(tmp_path):
    z, x, y = 9, 300, 200
    day = date(2026, 9, 1)
    (tmp_path / "middle").mkdir()
    (tmp_path / "edge").mkdir()
    middle = cluster_store(tmp_path / "middle", z, x, y)
    edge = cluster_store(tmp_path / "edge", z, x, y, edge=True)

    whole = decode(render_tile(middle.get(), z, x, y, day, day, False, scale=2))
    west = decode(render_tile(edge.get(), z, x, y, day, day, False, scale=2))
    east = decode(render_tile(edge.get(), z, x + 1, y, day, day, False, scale=2))

    # the dots spilling over the edge are drawn in the next tile
    assert (east[..., 3] > 0).any()
    assert (west[..., 3] > 0).sum() + (east[..., 3] > 0).sum() == (
        whole[..., 3] > 0
    ).sum()
