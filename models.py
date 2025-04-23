from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

class SortField(str, Enum):
    SCORE = "score"
    YEAR = "year"
    CATEGORY = "category"

class Laureate(BaseModel):
    id: str
    firstname: str
    surname: Optional[str] = None
    motivation: Optional[str] = None
    share: Optional[str] = None

class Prize(BaseModel):
    year: str
    category: str
    laureates: List[Laureate]

class PrizeCreate(BaseModel):
    year: str = Field(..., pattern=r'^\d{4}$')
    category: str
    laureates: List[Laureate]

class SearchResponse(BaseModel):
    year: str
    category: str
    laureates: List[Laureate]
    score: float

class FlexibleSearchParams(BaseModel):
    q: str = Field(..., min_length=1, description="Search term")
    include: Optional[List[str]] = Field(default=None, description="Fields to include in search")
    exclude: Optional[List[str]] = Field(default=None, description="Fields to exclude from search")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=10, ge=1, le=100, description="Results per page")
    sort_by: Optional[SortField] = Field(default=SortField.SCORE, description="Field to sort by")
    sort_order: Optional[SortOrder] = Field(default=SortOrder.DESC, description="Sort order")

    @validator('include', 'exclude')
    def validate_fields(cls, v):
        if v is not None:
            valid_fields = {
                "laureates.firstname",
                "laureates.surname",
                "laureates.motivation",
                "category",
                "year"
            }
            for field in v:
                if field not in valid_fields:
                    raise ValueError(f"Invalid field: {field}. Valid fields are: {valid_fields}")
        return v

class SearchResult(BaseModel):
    total: int
    page: int
    size: int
    results: List[Prize]
    score: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None 