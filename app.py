from flask import Flask, jsonify, request
from elasticsearch import Elasticsearch
import os
import requests
from models import (
    Prize, PrizeCreate, FlexibleSearchParams,
    SearchResult, ErrorResponse, SortField, SortOrder
)
import logging
import time
from elasticsearch.exceptions import ConnectionError
from pydantic import ValidationError
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize Elasticsearch client
es: Optional[Elasticsearch] = None

def get_elasticsearch() -> Elasticsearch:
    global es
    if es is None:
        es = wait_for_elasticsearch()
    return es

def wait_for_elasticsearch(max_retries=5, delay=1) -> Elasticsearch:
    """Wait for Elasticsearch to be available"""
    url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
    for i in range(max_retries):
        try:
            es = Elasticsearch(url)
            es.info()
            logger.info("Successfully connected to Elasticsearch")
            return es
        except Exception as e:
            if i < max_retries - 1:
                logger.warning(f"Failed to connect to Elasticsearch (attempt {i + 1}/{max_retries}): {e}")
                time.sleep(delay)
            else:
                logger.error(f"Could not connect to Elasticsearch after {max_retries} attempts")
                raise Exception("Could not connect to Elasticsearch after maximum retries")

def drop_index(es: Elasticsearch = None):
    """Drop the Nobel Prize index if it exists"""
    if es is None:
        es = get_elasticsearch()
    
    if es.indices.exists(index="nobel_prizes"):
        logger.info("Dropping nobel_prizes index...")
        es.indices.delete(index="nobel_prizes")
        logger.info("Index dropped successfully")
        return True
    return False

# Create index with mapping for fuzzy search
def create_index(es: Elasticsearch = None):
    """Create the Nobel Prize index with mapping"""
    if es is None:
        es = get_elasticsearch()
    
    try:
        # Drop the index if it exists
        drop_index(es)
        
        logger.info("Creating nobel_prizes index...")
        mapping = {
            "mappings": {
                "properties": {
                    "year": {"type": "keyword"},
                    "category": {"type": "text", "analyzer": "standard"},
                    "laureates": {
                        "type": "nested",
                        "properties": {
                            "id": {"type": "keyword"},
                            "firstname": {"type": "text", "analyzer": "standard"},
                            "surname": {"type": "text", "analyzer": "standard"},
                            "motivation": {"type": "text", "analyzer": "standard"}
                        }
                    }
                }
            }
        }
        es.indices.create(index="nobel_prizes", body=mapping)
        logger.info("Index created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def load_nobel_data(es: Elasticsearch = None):
    """Load Nobel Prize data from JSON file"""
    if es is None:
        es = get_elasticsearch()
    
    try:
        logger.info("Fetching Nobel Prize data...")
        response = requests.get("https://api.nobelprize.org/v1/prize.json")
        response.raise_for_status()
        data = response.json()
        
        logger.info(f"Found {len(data['prizes'])} prizes to index")
        
        # Prepare bulk operations
        bulk_operations = []
        for prize in data["prizes"]:
            try:
                # Create the document ID
                doc_id = f"{prize['year']}_{prize['category']}"
                
                # Add the index operation
                bulk_operations.append({
                    "index": {
                        "_index": "nobel_prizes",
                        "_id": doc_id
                    }
                })
                
                # Add the document
                bulk_operations.append(prize)
                
            except Exception as e:
                logger.error(f"Error preparing prize {prize.get('year', 'unknown')} for bulk indexing: {str(e)}")
        
        # Execute bulk indexing in chunks to avoid memory issues
        chunk_size = 100  # Process 100 documents at a time
        for i in range(0, len(bulk_operations), chunk_size * 2):  # Multiply by 2 because each document has 2 entries
            chunk = bulk_operations[i:i + chunk_size * 2]
            try:
                es.bulk(body=chunk, refresh=False)
                logger.info(f"Bulk indexed {len(chunk)//2} documents")
            except Exception as e:
                logger.error(f"Error in bulk indexing chunk: {str(e)}")
        
        # Force refresh to make all documents available for search
        es.indices.refresh(index="nobel_prizes")
        logger.info("Data loading completed")
        
    except Exception as e:
        logger.error(f"Error loading Nobel data: {str(e)}")
        raise

@app.route('/')
def index():
    return jsonify({"message": "Welcome to Nobel Prize Search API!"})

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        es = get_elasticsearch()
        es.info()
        return "OK", 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"error": "Service unhealthy", "detail": str(e)}), 500

@app.route('/prize', methods=['POST'])
def add_prize():
    """Add a new Nobel Prize record"""
    try:
        es = get_elasticsearch()
        data = request.get_json()
        prize = PrizeCreate(**data)
        
        result = es.index(index="nobel_prizes", body=prize.dict())
        return jsonify({"message": "Prize added successfully", "id": result["_id"]}), 201
    
    except Exception as e:
        logger.error(f"Error adding prize: {e}")
        return jsonify(ErrorResponse(error="Failed to add prize", detail=str(e)).dict()), 400

@app.route('/prize/<year>/<category>', methods=['PUT'])
def update_prize(year, category):
    """Update an existing Nobel Prize record"""
    try:
        es = get_elasticsearch()
        data = request.get_json()
        prize = PrizeCreate(**data)
        
        # Check if prize exists
        if not es.exists(index="nobel_prizes", id=f"{year}_{category}"):
            return jsonify(ErrorResponse(error="Prize not found", detail=f"No prize with id {f'{year}_{category}'}").dict()), 404
        
        result = es.index(index="nobel_prizes", id=f"{year}_{category}", body=prize.dict())
        return jsonify({"message": "Prize updated successfully", "id": result["_id"]}), 200
    
    except Exception as e:
        logger.error(f"Error updating prize: {e}")
        return jsonify(ErrorResponse(error="Failed to update prize", detail=str(e)).dict()), 400

@app.route('/search')
def flexible_search():
    try:
        # Validate and parse search parameters
        search_params = FlexibleSearchParams(
            q=request.args.get('q'),
            include=request.args.getlist('include'),
            exclude=request.args.getlist('exclude'),
            page=int(request.args.get('page', 1)),
            size=int(request.args.get('size', 10)),
            sort_by=request.args.get('sort_by', SortField.SCORE),
            sort_order=request.args.get('sort_order', SortOrder.DESC)
        )
        
        # Build the query
        query = {
            "query": {
                "bool": {
                    "should": []
                }
            },
            "from": (search_params.page - 1) * search_params.size,
            "size": search_params.size
        }
        
        # If no specific fields are provided, search across all relevant fields
        if not search_params.include:
            search_params.include = [
                "laureates.firstname",
                "laureates.surname",
                "laureates.motivation",
                "category",
                "year"
            ]
        
        # Remove excluded fields
        include_fields = [field for field in search_params.include 
                        if field not in (search_params.exclude or [])]
        
        # Build the multi-match query with boosting
        query["query"]["bool"]["should"].append({
            "multi_match": {
                "query": search_params.q,
                "fields": [
                    f"{field}^{boost}" for field, boost in [
                        ("laureates.firstname", 3),
                        ("laureates.surname", 3),
                        ("laureates.motivation", 2),
                        ("category", 1),
                        ("year", 1)
                    ] if field in include_fields
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
                "operator": "or"
            }
        })
        
        # Add nested queries for laureate fields
        laureate_fields = [f for f in include_fields if f.startswith('laureates.')]
        if laureate_fields:
            query["query"]["bool"]["should"].append({
                "nested": {
                    "path": "laureates",
                    "query": {
                        "multi_match": {
                            "query": search_params.q,
                            "fields": laureate_fields,
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                            "operator": "or"
                        }
                    },
                    "score_mode": "max"
                }
            })
        
        # Configure sorting
        if search_params.sort_by == SortField.SCORE:
            # When sorting by score, just use score
            query["sort"] = [{"_score": {"order": search_params.sort_order}}]
        else:
            # When sorting by other fields, use that field first, then score as a tiebreaker
            query["sort"] = [
                {search_params.sort_by: {"order": search_params.sort_order}},
                {"_score": {"order": "desc"}}  # Always use score as secondary sort
            ]
        
        # Execute search
        results = get_elasticsearch().search(index="nobel_prizes", body=query)
        
        # Process and validate results
        processed_results = []
        for hit in results["hits"]["hits"]:
            try:
                prize = Prize(**hit["_source"])
                processed_results.append({
                    **prize.dict(),
                    "score": hit["_score"]
                })
            except ValidationError as e:
                logger.error(f"Validation error for hit {hit['_id']}: {str(e)}")
                continue
        
        # Create and validate response
        response = SearchResult(
            total=results["hits"]["total"]["value"],
            page=search_params.page,
            size=search_params.size,
            results=processed_results
        )
        
        return jsonify(response.dict())
        
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Invalid search parameters",
            details=str(e)
        ).dict()), 400
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify(ErrorResponse(
            error="Internal server error",
            details=str(e)
        ).dict()), 500

if __name__ == '__main__':
    try:
        # Initialize Elasticsearch
        es = get_elasticsearch()
        create_index(es)
        load_nobel_data(es)
        app.run(host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        raise 