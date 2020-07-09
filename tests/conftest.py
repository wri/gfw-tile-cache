import os

import pytest
from fastapi.testclient import TestClient

from app.application import get_synchronous_db


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """

    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_start.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    with get_synchronous_db() as db:
        sql_file = f"{os.path.dirname(__file__)}/fixtures/session_end.sql"
        with open(sql_file) as f:
            sql = f.read()

        db.execute(sql)
        db.commit()


@pytest.fixture(autouse=True)
def client():
    """
    Set up a clean database before running a test
    Run all migrations before test and downgrade afterwards
    """
    from app.main import app

    with TestClient(app) as client:
        yield client
