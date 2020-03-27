import logging

from sqlalchemy.dialects import postgresql


def compile_sql(query):
    """
    Compile query using postgres dialact
    This will validate the binds and paste them into the query
    Normally this should be done server side, however, there is an incompability between SQLalchemy and asyncp
    This still needs some refactoring!
    """
    query = query.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    logging.debug(f"SQL: {query}")

    return query
