from shapely.geometry import box
from sqlalchemy import column, literal_column, select, table, text

from app.services.vector_tiles import _as_vector_tile, _group_mvt_table, get_mvt_table


def test_get_mvt_table():
    schema_name = "my_schema"
    table_name = "my_table"
    bbox = box(1, 1, 2, 2)
    columns = [column("column1"), column("column2")]
    filters = [text("column1 = 1"), text("column2 = 'abc")]
    extent = 4096
    sql = get_mvt_table(schema_name, table_name, bbox.bounds, extent, columns, *filters)
    expected_sql = "SELECT ST_AsMVTGeom(t.geom_wm, bounds.geom::box2d, 4096, 0,false) AS geom, column1, column2 FROM my_schema.my_table AS t, (SELECT ST_MakeEnvelope(:left, :bottom, :right, :top, 3857) AS geom) AS bounds WHERE ST_Intersects(t.geom_wm, bounds.geom) AND column1 = 1 AND column2 = 'abc"

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
