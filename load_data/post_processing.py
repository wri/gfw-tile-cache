import os

import psycopg2
from pendulum.parsing.exceptions import ParserError


def get_sql(sql_tmpl, **kwargs):
    with open(sql_tmpl, "r") as tmpl:
        sql = tmpl.read().format(**kwargs)
    print(sql)
    return sql


def cli():
    connection = psycopg2.connect(
        database=os.environ["POSTGRES_NAME"],
        user=os.environ["POSTGRES_USERNAME"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ["POSTGRES_PORT"],
        host=os.environ["POSTGRES_HOST"],
    )

    years = range(2011, 2022)
    schema = "viirs"
    table = "v20200224"

    cursor = connection.cursor()
    cursor.execute(get_sql("sql/update_geometry.sql.tmpl", schema=schema, table=table))
    connection.commit()
    cursor.execute(get_sql("sql/create_indicies.sql.tmpl", schema=schema, table=table))
    connection.commit()

    for year in years:
        for week in range(1, 54):
            try:
                week = f"{week:02}"
                cursor.execute(
                    get_sql(
                        "sql/cluster_partitions.sql.tmpl",
                        schema=schema,
                        table=table,
                        year=year,
                        week=week,
                    )
                )
                connection.commit()
            except ParserError:
                # Year has only 52 weeks
                pass

    cursor.close()
    connection.close()


if __name__ == "__main__":
    cli()
