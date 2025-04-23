import pytest
from unittest.mock import patch
from app import app
import json
from tests.mock_elasticsearch import get_mock_es

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_es():
    with patch('app.es', get_mock_es()) as mock:
        yield mock

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert b'OK' in response.data

def test_add_prize(client, mock_es):
    test_prize = {
        "year": "2024",
        "category": "physics",
        "laureates": [
            {
                "id": "1",
                "firstname": "Test",
                "surname": "Scientist",
                "motivation": "For testing purposes",
                "share": "1/1"
            }
        ]
    }
    response = client.post('/prizes', json=test_prize)
    assert response.status_code == 201
    mock_es.index.assert_called_once()

def test_add_prize_validation(client):
    invalid_prize = {
        "year": "invalid",
        "category": "invalid",
        "laureates": []
    }
    response = client.post('/prizes', json=invalid_prize)
    assert response.status_code == 422

def test_update_prize(client, mock_es):
    test_prize = {
        "year": "2024",
        "category": "physics",
        "laureates": [
            {
                "id": "1",
                "firstname": "Updated",
                "surname": "Scientist",
                "motivation": "For testing purposes",
                "share": "1/1"
            }
        ]
    }
    response = client.put('/prizes/1', json=test_prize)
    assert response.status_code == 200
    mock_es.index.assert_called_once()

def test_update_nonexistent_prize(client, mock_es):
    mock_es.get.side_effect = Exception("Not found")
    test_prize = {
        "year": "2024",
        "category": "physics",
        "laureates": []
    }
    response = client.put('/prizes/999', json=test_prize)
    assert response.status_code == 404

def test_search_endpoint(client, mock_es):
    response = client.get('/search?q=Einstein')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data
    mock_es.search.assert_called_once()

def test_search_with_pagination(client, mock_es):
    response = client.get('/search?q=physics&page=2&size=10')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data
    mock_es.search.assert_called_once()

def test_search_with_sorting(client, mock_es):
    response = client.get('/search?q=physics&sort_field=year&sort_order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data
    mock_es.search.assert_called_once()

def test_search_with_field_filtering(client, mock_es):
    response = client.get('/search?q=physics&include_fields=year,category')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data
    mock_es.search.assert_called_once()

def test_bulk_loading(client, mock_es):
    test_prizes = [
        {
            "year": "2024",
            "category": "physics",
            "laureates": [
                {
                    "id": "1",
                    "firstname": "Test",
                    "surname": "Scientist",
                    "motivation": "For testing purposes",
                    "share": "1/1"
                }
            ]
        }
    ]
    response = client.post('/prizes/bulk', json=test_prizes)
    assert response.status_code == 201
    mock_es.bulk.assert_called_once() 