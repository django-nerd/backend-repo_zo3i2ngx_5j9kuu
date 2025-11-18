from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class WishlistItem(BaseModel):
    title: str
    url: Optional[str] = None
    affiliate_url: Optional[str] = None
    price: Optional[float] = None
    notes: Optional[str] = None


class Participant(BaseModel):
    name: str
    email: EmailStr
    wishlist: List[WishlistItem] = []
    matched_with: Optional[str] = None  # participant id they should gift to


class EventCreate(BaseModel):
    name: str
    organizer_name: str
    organizer_email: EmailStr
    budget: Optional[float] = None
    currency: str = Field(default="USD")
    draw_rules: Optional[str] = None
    event_date: Optional[datetime] = None


class Event(EventCreate):
    id: Optional[str] = None
    code: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ParticipantCreate(BaseModel):
    name: str
    email: EmailStr


class MatchResult(BaseModel):
    giver_id: str
    receiver_id: str


class GiftStatusUpdate(BaseModel):
    participant_id: str
    status: str  # requested, purchased, shipped, delivered
    tracking_number: Optional[str] = None
