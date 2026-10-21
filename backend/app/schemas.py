from datetime import datetime
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict, field_validator

Positive = Annotated[int, Field(strict=True, gt=0, le=1_000_000)]
Nonnegative = Annotated[int, Field(strict=True, ge=0, le=1_000_000)]
Money = Annotated[int, Field(strict=True, ge=0, le=1_000_000_000)]

class Input(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

class ProductInput(Input):
    code: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    price_cents: Money
    minimum_stock: Nonnegative = 0
    active: bool = Field(default=True, strict=True)
    @field_validator('code')
    @classmethod
    def code_upper(cls, value):
        return value.upper()

class MovementInput(Input):
    product_id: Positive
    quantity: Positive
    kind: str = Field(pattern='^(entrada|saida|inicial)$')
    reason: str = Field(min_length=3, max_length=240)
    occurred_at: datetime | None = None

class ItemInput(Input):
    product_id: Positive
    quantity: Positive

class SaleInput(Input):
    items: list[ItemInput] = Field(min_length=1, max_length=100)
    occurred_at: datetime | None = None
