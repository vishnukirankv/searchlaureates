from unittest.mock import patch

def test_health_check(client, mock_es):
    """Test the health check endpoint."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.data == b'OK'

def test_index_page(client):
    """Test the index page."""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "Welcome to Nobel Prize Search API!"


def test_update_prize(client, mock_es, sample_prize):
    """Test updating an existing prize."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.put(f'/prize/{sample_prize["year"]}/{sample_prize["category"]}', 
                            json=sample_prize)
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Prize updated successfully"
        assert "id" in data

def test_update_nonexistent_prize(client, mock_es, sample_prize):
    """Test updating a non-existent prize."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        mock_es.exists.return_value = False
        response = client.put(f'/prize/{sample_prize["year"]}/{sample_prize["category"]}', 
                            json=sample_prize)
        assert response.status_code == 404

def test_search_basic(client, mock_es):
    """Test basic search functionality."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.get('/search?q=Einstein')
        assert response.status_code == 200
        data = response.get_json()
        assert "hits" in data
        assert len(data["hits"]) > 0
        assert data["total"] > 0

def test_search_with_field_filtering(client, mock_es):
    """Test search with field filtering."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.get('/search?q=Einstein&include=laureates.firstname&include=laureates.surname')
        assert response.status_code == 200
        data = response.get_json()
        assert "hits" in data
        assert len(data["hits"]) > 0

def test_search_with_sorting(client, mock_es):
    """Test search with sorting."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.get('/search?q=Einstein&sort=year:desc')
        assert response.status_code == 200
        data = response.get_json()
        assert "hits" in data
        assert len(data["hits"]) > 0

def test_search_with_pagination(client, mock_es):
    """Test search with pagination."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        response = client.get('/search?q=Einstein&page=1&size=10')
        assert response.status_code == 200
        data = response.get_json()
        assert "hits" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data

def test_search_validation(client, mock_es):
    """Test search parameter validation."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        # Test invalid page number
        response = client.get('/search?q=Einstein&page=0')
        assert response.status_code == 400
        
        # Test invalid size
        response = client.get('/search?q=Einstein&size=0')
        assert response.status_code == 400
        
        # Test missing query
        response = client.get('/search')
        assert response.status_code == 400

def test_prize_validation(client, mock_es):
    """Test prize data validation."""
    with patch('app.get_elasticsearch', return_value=mock_es):
        # Test missing required fields
        invalid_prize = {
            "year": "1921",
            "category": "physics"
            # Missing laureates
        }
        response = client.post('/prize', json=invalid_prize)
        assert response.status_code == 400
        
        # Test invalid year format
        invalid_prize = {
            "year": "invalid",
            "category": "physics",
            "laureates": [{
                "id": "12",
                "firstname": "Albert",
                "surname": "Einstein",
                "motivation": "for his services to Theoretical Physics",
                "share": "1"
            }]
        }
        response = client.post('/prize', json=invalid_prize)
        assert response.status_code == 400

def test_elasticsearch_connection_error(client, mock_es):
    """Test handling of Elasticsearch connection errors."""
    with patch('app.get_elasticsearch', side_effect=Exception("Connection failed")):
        response = client.get('/health')
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data 