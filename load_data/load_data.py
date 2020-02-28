import os

import click
import psycopg2


@click.command()
@click.argument("input")
@click.option("--schema", default="viirs")
@click.option("--table", default="v20200224")
def cli(input, schema, table):
    connection = psycopg2.connect(
        database=os.environ["POSTGRES_NAME"],
        user=os.environ["POSTGRES_USERNAME"],
        password=os.environ["POSTGRES_PASSWORD"],
        port=os.environ["POSTGRES_PORT"],
        host=os.environ["POSTGRES_HOST"],
    )

    cursor = connection.cursor()
    with open(input, "r") as f:
        # Notice that we don't need the `csv` module.
        next(f)  # Skip the header row.
        cursor.copy_from(
            f,
            f"{schema}.{table}",
            columns=(
                "latitude",
                "longitude",
                "acq_date",
                "acq_time",
                "confidence",
                "bright_ti4",
                "bright_ti5",
                "frp",
            ),
        )

    connection.commit()
    cursor.close()
    connection.close()


if __name__ == "__main__":
    cli()
