import pytest
from unittest.mock import Mock, patch
from app import app
import json
from tests.mock_elasticsearch import get_mock_es

@pytest.fixture
def mock_es():
    with patch('app.es') as mock_es:
        # Mock search response for Einstein query
        mock_search_response = {
            'hits': {
                'total': {'value': 1},
                'hits': [{
                    '_source': {
                        'year': '1921',
                        'category': 'physics',
                        'laureates': [{
                            'firstname': 'Albert',
                            'surname': 'Einstein',
                            'motivation': 'for his services to Theoretical Physics',
                            'share': '1'
                        }]
                    }
                }]
            }
        }
        mock_es.search.return_value = mock_search_response
        yield mock_es

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}

def test_add_prize(client, test_prize, mock_es):
    """Test adding a new prize."""
    response = client.post('/prizes', 
                         data=json.dumps(test_prize),
                         content_type='application/json')
    assert response.status_code == 201
    assert "id" in response.json

def test_update_prize(client, test_prize, mock_es):
    """Test updating an existing prize."""
    # First add a prize
    response = client.post('/prizes', 
                         data=json.dumps(test_prize),
                         content_type='application/json')
    prize_id = response.json["id"]
    
    # Update the prize
    updated_prize = test_prize.copy()
    updated_prize["year"] = "1922"
    response = client.put(f'/prizes/{prize_id}',
                        data=json.dumps(updated_prize),
                        content_type='application/json')
    assert response.status_code == 200

def test_search_flexible(client, mock_es):
    """Test the flexible search endpoint."""
    query_params = {
        "q": "Einstein",
        "include_fields": ["year", "category", "laureates.firstname"],
        "exclude_fields": ["laureates.motivation"],
        "sort_field": "year",
        "sort_order": "desc",
        "from_": 0,
        "size": 10
    }
    response = client.get('/search/flexible', query_string=query_params)
    assert response.status_code == 200
    assert "hits" in response.json
    assert "total" in response.json

def test_search_flexible_validation(client):
    """Test validation in flexible search endpoint."""
    # Test with invalid sort field
    query_params = {
        "q": "Einstein",
        "sort_field": "invalid_field"
    }
    response = client.get('/search/flexible', query_string=query_params)
    assert response.status_code == 400

def test_bulk_load(client, mock_es):
    """Test bulk loading of prizes."""
    prizes = [
        {
            "year": "1921",
            "category": "physics",
            "laureates": [{
                "id": "12",
                "firstname": "Albert",
                "surname": "Einstein",
                "motivation": "for his services to Theoretical Physics",
                "share": "1"
            }]
        },
        {
            "year": "1922",
            "category": "chemistry",
            "laureates": [{
                "id": "13",
                "firstname": "Niels",
                "surname": "Bohr",
                "motivation": "for his services to Atomic Structure",
                "share": "1"
            }]
        }
    ]
    response = client.post('/prizes/bulk',
                         data=json.dumps(prizes),
                         content_type='application/json')
    assert response.status_code == 200
    assert response.json["success"] is True

def test_invalid_prize_data(client):
    """Test validation of invalid prize data."""
    invalid_prize = {
        "year": "invalid",
        "category": "invalid_category",
        "laureates": []
    }
    response = client.post('/prizes',
                         data=json.dumps(invalid_prize),
                         content_type='application/json')
    assert response.status_code == 400

def test_flexible_search(client, monkeypatch):
    # Mock Elasticsearch
    mock_es = get_mock_es()
    monkeypatch.setattr('app.es', mock_es)
    
    # Test basic search
    response = client.get('/search/flexible?q=Albert Einstein')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['hits']) > 0
    
    # Test with field filtering
    response = client.get('/search/flexible?q=Albert Einstein&include_fields=firstname,surname')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['hits']) > 0
    
    # Test with sorting
    response = client.get('/search/flexible?q=Albert Einstein&sort_field=year&sort_order=desc')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['hits']) > 0

def test_search_with_field_filtering(client, mock_es):
    response = client.get('/search/flexible?q=Einstein&include_fields=laureates.firstname,laureates.surname')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data

    # Verify search was called with correct source filtering
    mock_es.search.assert_called_with(
        index='nobel_prizes',
        body={
            'query': {
                'multi_match': {
                    'query': 'Einstein',
                    'fields': ['laureates.firstname', 'laureates.surname'],
                    'type': 'best_fields'
                }
            },
            '_source': ['laureates.firstname', 'laureates.surname'],
            'size': 10,
            'from': 0
        }
    )

def test_search_with_sorting(client, mock_es):
    # Mock a different response for sorted results
    mock_es.search.return_value = {
        'hits': {
            'total': {'value': 2},
            'hits': [
                {
                    '_source': {
                        'year': '1922',
                        'category': 'physics'
                    }
                },
                {
                    '_source': {
                        'year': '1921',
                        'category': 'physics'
                    }
                }
            ]
        }
    }

    response = client.get('/search/flexible?q=physics&sort_field=year&sort_order=desc')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'hits' in data
    assert len(data['hits']) == 2
    assert data['hits'][0]['year'] == '1922'

    # Verify search was called with correct sorting
    mock_es.search.assert_called_with(
        index='nobel_prizes',
        body={
            'query': {
                'multi_match': {
                    'query': 'physics',
                    'fields': ['*'],
                    'type': 'best_fields'
                }
            },
            'sort': [{'year': 'desc'}],
            'size': 10,
            'from': 0
        }
    )

def test_invalid_search_params(client):
    # Test invalid sort field
    response = client.get('/search/flexible?q=Einstein&sort_field=invalid_field')
    assert response.status_code == 422

    # Test invalid sort order
    response = client.get('/search/flexible?q=Einstein&sort_order=invalid')
    assert response.status_code == 422

    # Test invalid include_fields
    response = client.get('/search/flexible?q=Einstein&include_fields=invalid_field')
    assert response.status_code == 422 