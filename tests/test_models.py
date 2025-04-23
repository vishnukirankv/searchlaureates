import pytest
from pydantic import ValidationError
from models import (
    Laureate,
    Prize,
    PrizeCreate,
    FlexibleSearchParams,
    SearchResult,
    ErrorResponse,
    SortField,
    SortOrder
)

def test_laureate_model():
    laureate_data = {
        "id": "1",
        "firstname": "Albert",
        "surname": "Einstein",
        "motivation": "For his services to Theoretical Physics",
        "share": "1"
    }
    laureate = Laureate(**laureate_data)
    assert laureate.id == "1"
    assert laureate.firstname == "Albert"
    assert laureate.surname == "Einstein"

def test_prize_model():
    prize_data = {
        "year": "1921",
        "category": "physics",
        "laureates": [{
            "id": "1",
            "firstname": "Albert",
            "surname": "Einstein",
            "motivation": "For his services to Theoretical Physics",
            "share": "1"
        }]
    }
    prize = Prize(**prize_data)
    assert prize.year == "1921"
    assert prize.category == "physics"
    assert len(prize.laureates) == 1
    assert prize.laureates[0].firstname == "Albert"

def test_prize_create_model():
    prize_data = {
        "year": "2024",
        "category": "physics",
        "laureates": [{
            "id": "1",
            "firstname": "Test",
            "surname": "Scientist",
            "motivation": "For testing purposes",
            "share": "1"
        }]
    }
    prize = PrizeCreate(**prize_data)
    assert prize.year == "2024"
    assert prize.category == "physics"
    assert len(prize.laureates) == 1

def test_flexible_search_params():
    params = FlexibleSearchParams(
        q="Einstein",
        include_fields=["year", "category"],
        exclude_fields=["motivation"],
        sort_field=SortField.year,
        sort_order=SortOrder.desc,
        page=1,
        size=10
    )
    assert params.q == "Einstein"
    assert params.include_fields == ["year", "category"]
    assert params.exclude_fields == ["motivation"]
    assert params.sort_field == SortField.year
    assert params.sort_order == SortOrder.desc
    assert params.page == 1
    assert params.size == 10

    # Test invalid fields
    with pytest.raises(ValidationError):
        FlexibleSearchParams(
            q="Einstein",
            include_fields=["invalid_field"],
            sort_field="invalid_field"
        )

def test_search_result_model():
    result_data = {
        "hits": [
            {
                "year": "1921",
                "category": "physics",
                "laureates": [{
                    "firstname": "Albert",
                    "surname": "Einstein",
                    "motivation": "For his services to Theoretical Physics",
                    "share": "1"
                }]
            }
        ],
        "total": 1
    }
    result = SearchResult(**result_data)
    assert len(result.hits) == 1
    assert result.total == 1
    assert result.hits[0].year == "1921"

def test_error_response_model():
    error_data = {
        "error": "Validation Error",
        "detail": "Invalid field name"
    }
    error = ErrorResponse(**error_data)
    assert error.error == "Validation Error"
    assert error.detail == "Invalid field name" 