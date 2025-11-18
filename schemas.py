from pydantic import BaseModel, Field, HttpUrl, EmailStr
from typing import List, Optional
from datetime import datetime

# GiftFlow Schemas

class WishlistItem(BaseModel):
    title: str
    url: HttpUrl
    affiliate_url: Optional[HttpUrl] = None
    price: Optional[float] = Field(default=None, ge=0)
    notes: Optional[str] = None

class Event(BaseModel):
    name: str
    organizer_name: str
    organizer_email: EmailStr
    event_date: Optional[datetime] = None
    budget_min: Optional[float] = Field(default=None, ge=0)
    budget_max: Optional[float] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default="USD", min_length=3, max_length=3)
    rules: Optional[str] = None

class Participant(BaseModel):
    event_id: str
    name: str
    email: EmailStr
    wishlist: List[WishlistItem] = []
    match_id: Optional[str] = None

class GiftStatusUpdate(BaseModel):
    status: str  # requested, purchased, shipped, delivered
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
