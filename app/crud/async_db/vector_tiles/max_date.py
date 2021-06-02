from ....application import db
from ....errors import RecordNotFoundError
from .nasa_viirs_fire_alerts import SCHEMA


async def get_max_date(version):
    t = db.table(version)
    t.schema = SCHEMA
    sql = db.select(
        [db.literal_column("max(alert__date)").label("Max alert date")]
    ).select_from(t)

    max_date = await db.scalar(sql)
    if max_date:
        return {"max_date": max_date}
    else:
        raise RecordNotFoundError(
            f"Error when trying to get max(alert__date) for {SCHEMA}.{version}."
        )
