from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class IntentType(str, Enum):
    ORDER = "order"
    STATUS = "status"
    COMPLAINT = "complaint"
    RETURN = "return"
    OTHER = "other"


class UrgencyType(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class LineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sku: Optional[str] = Field(
        ..., description="Product SKU code if mentioned (e.g., 'MS-PPE-0002'), else null."
    )
    description: Optional[str] = Field(
        ..., description="Item name or specification if mentioned, else null."
    )
    quantity: float = Field(
        ..., gt=0, description="Numeric quantity ordered or referenced (convert words like 'dozen' to 12)."
    )
    unit: Optional[str] = Field(
        ..., description="Unit of measure (e.g., 'boxes', 'units', 'pcs'), else null."
    )


class OrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer: Optional[str] = Field(
        ..., description="Company name, or sender full name if company is not stated."
    )
    intent: IntentType = Field(
        ..., description="Primary intent of the email."
    )
    line_items: list[LineItem] = Field(
        ..., description="List of extracted line items. Empty list [] if none are specified."
    )
    requested_date: Optional[str] = Field(
        ..., description="Target future delivery date in YYYY-MM-DD format, else null."
    )
    urgency: UrgencyType = Field(
        ..., description="Urgency level inferred from the email."
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction confidence score from 0.0 to 1.0."
    )

