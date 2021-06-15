import pytest
from shapely.geometry import box
from sqlalchemy import column, literal_column, select, table, text

from app.crud.async_db.vector_tiles import (
    _as_vector_tile,
    _filter_mvt_table,
    _get_tile,
    _group_mvt_table,
    get_mvt_table,
)
from app.responses import VectorTileResponse


def test_get_mvt_table():
    schema_name = "my_schema"
    table_name = "my_table"
    bbox = box(1, 1, 2, 2)
    columns = [column("column1"), column("column2")]
    filters = [text("column1 = 1"), text("column2 = 'abc")]
    extent = 4096
    sql = get_mvt_table(schema_name, table_name, bbox.bounds, extent, columns, filters)
    expected_sql = "SELECT column1, column2, ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d, 4096, 0,false) AS geom FROM my_schema.my_table AS t, (SELECT ST_MakeEnvelope(:left, :bottom, :right, :top, 3857) AS geom) AS bounds WHERE ST_Intersects(t.geom_wm, bounds.geom) AND column1 = 1 AND column2 = 'abc"

    assert str(sql).replace("\n", "") == expected_sql


def test__as_vector_tile():
    query = select([column("my_column")]).alias("my_table")
    sql = _as_vector_tile(query)
    expected_sql = "SELECT ST_AsMVT(my_table.*, 'default', 4096) FROM (SELECT my_column) AS my_table"

    assert str(sql).replace("\n", "") == expected_sql


def test__group_mvt_table():
    query = select([column("column1"), column("column2")]).select_from(
        table("my_table")
    )

    columns = [literal_column("sum(column1)")]
    group_by_columns = [column("column2")]

    sql = _group_mvt_table(query, columns, group_by_columns)
    expected_sql = "SELECT sum(column1) FROM (SELECT column1, column2 FROM my_table) GROUP BY column2"

    assert str(sql).replace("\n", "") == expected_sql


def test__filter_mvt_tabe():
    query = select([column("column1"), column("column2")]).select_from(
        table("my_table")
    )
    filters = [text("column1 = 1"), text("column2 = 2")]

    sql = _filter_mvt_table(query, *filters)
    expected_sql = (
        "SELECT column1, column2 FROM my_table WHERE column1 = 1 AND column2 = 2"
    )

    assert str(sql).replace("\n", "") == expected_sql


@pytest.mark.asyncio
async def test__get_tile():
    query = (
        select([column("is_latest")])
        .select_from(table("versions"))
        .where(text("dataset='nasa_fire_alerts' and 'version' = 'v202003'"))
    )
    response: VectorTileResponse = await _get_tile(query)

    assert response.status_code == 200
    assert response.media_type == "application/x-protobuf"
