# Nobel Prize Search API

This project provides a Flask-based API for searching and managing Nobel Prize data, integrated with Elasticsearch.

## Prerequisites

- Docker
- Docker Compose

## Running the Project

1. Clone this repository
2. Navigate to the project directory
3. Run the following command to start the services:

```bash
docker-compose up --build
```

The services will be available at:
- Flask application: http://localhost:5001
- Elasticsearch: http://localhost:9200

## Endpoints

### Search Endpoint

- `GET /search`: Flexible search across all fields with field filtering and sorting
  Parameters:
  - `q`: Search term (required)
  - `include`: Fields to include in search (multiple allowed)
  - `exclude`: Fields to exclude from search (multiple allowed)
  - `page`: Page number (default: 1, min: 1)
  - `size`: Results per page (default: 10, min: 1, max: 100)
  - `sort_by`: Field to sort by (default: score, options: score, year, category)
  - `sort_order`: Sort order (default: desc, options: asc, desc)
  
  Examples:
  - Basic search: `GET /search?q=Albert`
  - Field-specific search: `GET /search?q=quantum&include=laureates.motivation&include=category`
  - Exclude fields: `GET /search?q=Einstein&exclude=year&exclude=category`
  - Combined include/exclude: `GET /search?q=physics&include=laureates.firstname&include=laureates.surname&exclude=laureates.motivation`
  - Sorted search: `GET /search?q=physics&sort_by=year&sort_order=desc`

### Data Management Endpoints

- `POST /prize`: Add a new prize
  ```json
  {
    "year": "2023",
    "category": "physics",
    "laureates": [
      {
        "id": "1",
        "firstname": "John",
        "surname": "Doe",
        "motivation": "For groundbreaking work",
        "share": "1/2"
      }
    ]
  }
  ```

- `PUT /prize/<year>/<category>`: Update an existing prize
  Example: `PUT /prize/2023/physics`

## Features

- Fuzzy search for names (handles typos and partial matches)
- Nested document structure for laureates
- Input validation using Pydantic
- Automatic data loading from the Nobel Prize API
- Elasticsearch integration for powerful search capabilities
- Flexible search across all fields with field filtering
- Relevance-based scoring and sorting
- Field boosting for better search results
- Pagination support
- Error handling and logging
- Input validation for all parameters
- Type-safe responses

## Search Relevance and Sorting

By default, search results are sorted by relevance (score) in descending order. When sorting by other fields (year or category), relevance is used as a secondary sort to break ties. This ensures that the most relevant results are always prioritized.

The search relevance is calculated using the following field weights:
- Laureate firstname: 3x
- Laureate surname: 3x
- Motivation: 2x
- Category: 1x
- Year: 1x

For example, when sorting by year:
1. Results are first sorted by year (ascending or descending as specified)
2. For results with the same year, they are then sorted by relevance score
3. This ensures that within each year, the most relevant matches appear first

## Error Handling

The API provides detailed error responses in the following format:
```json
{
    "error": "Error message",
    "details": "Additional error details (if available)"
}
```

## Stopping the Project

To stop the services, press Ctrl+C in the terminal where the services are running, or run:

```bash
docker-compose down
``` 
