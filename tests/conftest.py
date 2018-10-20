import pytest
from aftquery.api.rest.sousmarin import app


@pytest.fixture(scope='function')
def sousmarin():
    client = app.test_client()
    context = app.app_context()
    context.push()

    yield client

    context.pop()