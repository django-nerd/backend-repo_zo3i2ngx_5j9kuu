import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db
from schemas import Event, Participant, WishlistItem, GiftStatusUpdate

app = FastAPI(title="GiftFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility

def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")


@app.get("/")
def health():
    return {"ok": True, "service": "giftflow"}

# Events

@app.post("/events")
def create_event(event: Event):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    data = event.model_dump()
    res = db["event"].insert_one({**data})
    return {"id": str(res.inserted_id), **data}


@app.get("/events")
def list_events():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    events = []
    for doc in db["event"].find().sort("_id", -1).limit(50):
        doc["id"] = str(doc.pop("_id"))
        events.append(doc)
    return events

# Participants

@app.post("/events/{event_id}/participants")
def add_participant(event_id: str, participant: Participant):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # ensure event exists
    ev = db["event"].find_one({"_id": to_object_id(event_id)})
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    pdata = participant.model_dump()
    pdata["event_id"] = event_id
    res = db["participant"].insert_one(pdata)
    return {"id": str(res.inserted_id), **pdata}


@app.post("/participants/{participant_id}/wishlist")
def update_wishlist(participant_id: str, items: List[WishlistItem]):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    result = db["participant"].update_one(
        {"_id": to_object_id(participant_id)}, {"$set": {"wishlist": [i.model_dump() for i in items]}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {"ok": True}


# Draw names

@app.post("/events/{event_id}/draw")
def draw_names(event_id: str):
    import random
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    participants = list(db["participant"].find({"event_id": event_id}))
    if len(participants) < 2:
        raise HTTPException(status_code=400, detail="Need at least two participants")

    ids = [str(p["_id"]) for p in participants]
    receivers = ids.copy()
    for _ in range(100):
        random.shuffle(receivers)
        if all(g != r for g, r in zip(ids, receivers)):
            break
    else:
        raise HTTPException(status_code=500, detail="Could not compute non-self assignments")

    # update matches
    for giver_id, recv_id in zip(ids, receivers):
        db["participant"].update_one({"_id": ObjectId(giver_id)}, {"$set": {"match_id": recv_id}})

    return {"ok": True, "pairs": dict(zip(ids, receivers))}


# Gift status

@app.post("/participants/{participant_id}/gift-status")
def update_gift_status(participant_id: str, payload: GiftStatusUpdate):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    update = {k: v for k, v in payload.model_dump().items() if v is not None}
    res = db["participant"].update_one({"_id": to_object_id(participant_id)}, {"$set": {"gift_status": update}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Participant not found")
    return {"ok": True}


# Simple schema exposure for admin tools
class SchemaInfo(BaseModel):
    name: str
    fields: List[str]

@app.get("/schema")
def schema_info():
    return [
        SchemaInfo(name="event", fields=list(Event.model_fields.keys())).model_dump(),
        SchemaInfo(name="participant", fields=list(Participant.model_fields.keys())).model_dump(),
        SchemaInfo(name="wishlistitem", fields=list(WishlistItem.model_fields.keys())).model_dump(),
    ]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
