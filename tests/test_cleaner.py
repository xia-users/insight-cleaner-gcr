import json
import base64
import gzip
import pytest
from main import app

@pytest.fixture(scope="module")
def client():
    client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield client
    ctx.pop()

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Insight' in response.data


def test_clean(client):
    header = {'topic_id': 'test-001', 'table_id': 'aged_data', 'start_seq': '99991231000000000000'}
    envoloppe = {'message': {'attributes': header,
        'data': base64.b64encode(gzip.compress(b'[]')).decode()}}
    response = client.post('/', json=envoloppe)
    assert response.status_code == 200

"""
def test_exceptions(client):
    envoloppe = ['Hello', 'World']
    response = client.post('/', json=envoloppe)
    assert response.status_code == 204
    header = {"Hello": "World"}
    response = client.post('/', headers=header)
"""