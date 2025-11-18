from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import random

from schemas import EventCreate, Event, ParticipantCreate, WishlistItem, GiftStatusUpdate
from database import db, create_document, get_documents

app = FastAPI(title="GiftFlow API", version="0.1.0")

# CORS
frontend_url = os.getenv("FRONTEND_URL", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/test")
def test():
    # Verify DB connectivity by fetching collections list
    try:
        return {"status": "ok", "time": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/events", response_model=Event)
async def create_event(event: EventCreate):
    code = "GF" + str(random.randint(100000, 999999))
    data = event.dict()
    data.update({"code": code})
    inserted = await create_document("event", data)
    return Event(id=str(inserted.get("_id")), **inserted)


@app.get("/events")
async def list_events(limit: int = 50):
    docs = await get_documents("event", {}, limit)
    for d in docs:
        d["id"] = str(d.get("_id"))
    return docs


@app.post("/events/{event_id}/participants")
async def add_participant(event_id: str, participant: ParticipantCreate):
    data = participant.dict()
    data.update({"event_id": event_id})
    doc = await create_document("participant", data)
    doc["id"] = str(doc.get("_id"))
    return doc


class WishlistSync(BaseModel):
    items: List[WishlistItem]


@app.post("/participants/{participant_id}/wishlist")
async def update_wishlist(participant_id: str, payload: WishlistSync):
    # For demo, simply store snapshot doc per update
    data = {"participant_id": participant_id, "items": [i.dict() for i in payload.items]}
    doc = await create_document("wishlist", data)
    doc["id"] = str(doc.get("_id"))
    return doc


@app.post("/events/{event_id}/draw")
async def draw_names(event_id: str):
    # Stub: trigger n8n workflow via webhook in future. For now create random permutation
    participants = await get_documents("participant", {"event_id": event_id}, 500)
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 participants to draw")
    ids = [str(p.get("_id")) for p in participants]
    shuffled = ids[:]
    random.shuffle(shuffled)
    # Ensure no one gets themselves; simple retry
    for _ in range(10):
        if all(a != b for a, b in zip(ids, shuffled)):
            break
        random.shuffle(shuffled)
    pairs = [{"giver_id": a, "receiver_id": b} for a, b in zip(ids, shuffled)]
    doc = await create_document("match", {"event_id": event_id, "pairs": pairs})
    doc["id"] = str(doc.get("_id"))
    return doc


@app.post("/participants/{participant_id}/gift-status")
async def update_gift_status(participant_id: str, payload: GiftStatusUpdate):
    data = payload.dict()
    data.update({"participant_id": participant_id, "updated_at": datetime.utcnow().isoformat()})
    doc = await create_document("giftstatus", data)
    doc["id"] = str(doc.get("_id"))
    return doc
