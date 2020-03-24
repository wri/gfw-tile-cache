from shapely.geometry import box
from sqlalchemy import column, text, select, table, literal_column

from app.services.vector_tiles import (
    get_mvt_table,
    _as_vector_tile,
    _group_mvt_table,
)


def test_get_mvt_table():
    table_name = "my_table"
    bbox = box(1, 1, 2, 2)
    columns = [column("column1"), column("column2")]
    filters = [text("column1 = 1"), text("column2 = 'abc")]
    values = {"a": "b"}
    sql, v = get_mvt_table(table_name, bbox.bounds, columns, *filters, **values)
    expected_sql = "SELECT ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d, 4096, 0,false) AS geom, column1, column2 FROM my_table AS t, (SELECT ST_MakeEnvelope(:left, :bottom, :right, :top, 3857) AS geom) AS bounds WHERE ST_Intersects(t.geom_wm, bounds.geom) AND column1 = 1 AND column2 = 'abc"

    assert str(sql).replace("\n", "") == expected_sql
    assert v == {"a": "b", "left": 1, "bottom": 1, "right": 2, "top": 2}


def test__as_vector_tile():
    query = select([column("my_column")])
    sql = _as_vector_tile(query)
    expected_sql = "SELECT ST_AsMVT(*) FROM (SELECT my_column)"

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
