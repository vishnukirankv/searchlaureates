import pytest
from unittest.mock import MagicMock
import app as flask_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_app = flask_app.app
    test_app.config.update({
        "TESTING": True,
    })
    return test_app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def mock_es():
    """Create a mock Elasticsearch client."""
    mock = MagicMock()
    
    # Mock indices property
    mock.indices = MagicMock()
    mock.indices.exists.return_value = True
    
    # Mock search response
    mock.search.return_value = {
        'hits': {
            'total': {'value': 1},
            'hits': [
                {
                    '_id': '1',
                    '_score': 1.0,
                    '_source': {
                        'year': '1921',
                        'category': 'physics',
                        'laureates': [
                            {
                                'id': '12',
                                'firstname': 'Albert',
                                'surname': 'Einstein',
                                'motivation': 'for his services to Theoretical Physics',
                                'share': '1'
                            }
                        ]
                    }
                }
            ]
        }
    }
    
    # Mock index response
    mock.index.return_value = {'_id': '1'}
    
    return mock

@pytest.fixture
def test_prize():
    """Provide sample prize data for testing."""
    return {
        'year': '1921',
        'category': 'physics',
        'laureates': [
            {
                'id': '12',
                'firstname': 'Albert',
                'surname': 'Einstein',
                'motivation': 'for his services to Theoretical Physics',
                'share': '1'
            }
        ],
        'overallMotivation': None
    }

@pytest.fixture
def sample_prize():
    """Provide sample prize data for testing."""
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
def sample_prizes():
    """Sample prizes data for bulk testing."""
    return [
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