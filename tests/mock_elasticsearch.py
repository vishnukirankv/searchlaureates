from unittest.mock import MagicMock

SAMPLE_RESPONSE = {
    'hits': {
        'total': {'value': 1},
        'hits': [{
            '_source': {
                'year': '1921',
                'category': 'physics',
                'laureates': [{
                    'firstname': 'Albert',
                    'surname': 'Einstein',
                    'motivation': 'for his services to Theoretical Physics'
                }]
            }
        }]
    }
}

def get_mock_es():
    mock_es = MagicMock()
    mock_es.search.return_value = SAMPLE_RESPONSE
    
    # Mock index creation
    mock_es.indices.create.return_value = {'acknowledged': True}
    
    # Mock index deletion
    mock_es.indices.delete.return_value = {'acknowledged': True}
    
    # Mock index exists
    mock_es.indices.exists.return_value = True
    
    # Mock document indexing
    mock_es.index.return_value = {
        '_index': 'nobel_prizes',
        '_id': '1',
        '_version': 1,
        'result': 'created',
        '_shards': {'total': 2, 'successful': 1, 'failed': 0},
        '_seq_no': 0,
        '_primary_term': 1
    }
    
    # Mock bulk indexing
    mock_es.bulk.return_value = {
        'took': 30,
        'errors': False,
        'items': []
    }
    
    # Mock get document
    mock_es.get.return_value = {
        '_index': 'nobel_prizes',
        '_id': '1',
        '_version': 1,
        'found': True,
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
    }
    
    return mock_es 