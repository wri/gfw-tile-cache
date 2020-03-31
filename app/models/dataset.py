import enum
import logging
from typing import Dict, Any

import psycopg2
from cachetools import cached, TTLCache
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import DictCursor

from app import get_pool


# memorize metadata for 15 min
@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_metadata():
    pool: SimpleConnectionPool = get_pool()
    sql: str = "SELECT * FROM metadata"

    conn = pool.getconn()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(sql)
    ans = cur.fetchall()
    metadata = []
    for row in ans:
        metadata.append(dict(row))
    return metadata


metadata = get_metadata()
fields: Dict[str, Any] = dict()
for row in metadata:
    if row["has_feature_info"]:
        fields[row["dataset"]] = row["dataset"]

Dataset = enum.Enum("DynamicFoobarModel", fields)  # type: ignore
