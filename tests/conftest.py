import pytest
from aftquery.api.rest.sousmarin import app, mongo


@pytest.fixture()
def sousmarin():
    client = app.test_client()
    context = app.app_context()
    context.push()

    yield client

    context.pop()


@pytest.fixture()
def sousmarin_db():
    return mongo.db
