import pytest
from unittest.mock import MagicMock, patch
from app import app as flask_app
from elasticsearch import Elasticsearch
import os
import sys

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    """Create a Flask test client."""
    flask_app.config.update({
        'TESTING': True,
    })
    return flask_app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def mock_es():
    """Create a mock Elasticsearch client."""
    mock = MagicMock(spec=Elasticsearch)
    
    # Mock common Elasticsearch responses
    mock.indices.exists.return_value = False
    mock.indices.create.return_value = {"acknowledged": True}
    mock.indices.delete.return_value = {"acknowledged": True}
    mock.info.return_value = {"version": {"number": "7.9.3"}}
    
    # Mock search response
    mock.search.return_value = {
        "hits": {
            "total": {"value": 1, "relation": "eq"},
            "hits": [{
                "_source": {
                    "year": "1921",
                    "category": "physics",
                    "laureates": [{
                        "id": "12",
                        "firstname": "Albert",
                        "surname": "Einstein",
                        "motivation": "for his services to Theoretical Physics",
                        "share": "1"
                    }]
                }
            }]
        }
    }
    
    # Mock index response
    mock.index.return_value = {
        "_index": "nobel_prizes",
        "_id": "test_id",
        "_version": 1,
        "result": "created",
        "_shards": {"total": 2, "successful": 1, "failed": 0},
        "_seq_no": 0,
        "_primary_term": 1
    }
    
    # Mock bulk response
    mock.bulk.return_value = {
        "took": 30,
        "errors": False,
        "items": []
    }
    
    return mock

@pytest.fixture
def test_prize():
    """Create a test prize record."""
    return {
        "year": "1921",
        "category": "physics",
        "laureates": [{
            "id": "12",
            "firstname": "Albert",
            "surname": "Einstein",
            "motivation": "for his services to Theoretical Physics",
            "share": "1"
        }]
    }

@pytest.fixture
def drop_index(mock_es):
    """Drop the test index before and after tests."""
    # Drop index if it exists before the test
    mock_es.indices.delete.return_value = {"acknowledged": True}
    mock_es.indices.delete(index="nobel_prizes", ignore=[404])
    
    yield
    
    # Drop index after the test
    mock_es.indices.delete(index="nobel_prizes", ignore=[404])

@pytest.fixture(autouse=True)
def mock_elasticsearch(monkeypatch, mock_es, drop_index):
    """Patch the Elasticsearch client in the app."""
    def mock_get_elasticsearch(*args, **kwargs):
        return mock_es
    
    monkeypatch.setattr('app.get_elasticsearch', mock_get_elasticsearch)
    return mock_es 