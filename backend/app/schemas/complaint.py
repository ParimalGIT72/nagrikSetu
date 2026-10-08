from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ComplaintBase(BaseModel):
    text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed description of the grievance",
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="GPS Latitude (-90 to 90)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="GPS Longitude (-180 to 180)",
    )


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintSubmissionResponse(BaseModel):
    complaint_id: str
    status: str = "SUBMITTED"
    message: str = "Complaint successfully registered."


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    complaint_id: str
    text: str
    latitude: float
    longitude: float
    image_path: Optional[str] = None
    status: str
    is_flagged: bool = False
    flag_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ComplaintListResponse(BaseModel):
    total: int
    items: list[ComplaintResponse]
