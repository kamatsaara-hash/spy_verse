print("🔥 NEW VERSION DEPLOYED")
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

# =========================
# ENV & DATABASE
# =========================

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["SPYDATA"]

users_collection = db["users"]
events_collection = db["events"]

app = FastAPI()

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# ROOT
# =========================

@app.get("/")
def home():
    return {"message": "Student Event Management API is running"}

# =========================
# FORCE SEED EVENTS (MANUAL)
# =========================

@app.get("/seed-events")
def seed_events():

    events_collection.delete_many({})  # clear existing

    sample_events = [
        # TECHNICAL
        {"name": "Hackathon", "category": "technical", "codename": "CODE-X"},
        {"name": "AI Challenge", "category": "technical", "codename": "NEURAL-7"},
        {"name": "Cyber Security", "category": "technical", "codename": "FIREWALL"},

        # CULTURAL
        {"name": "Dance Battle", "category": "cultural", "codename": "RHYTHM"},
        {"name": "Music Fest", "category": "cultural", "codename": "MELODY"},
        {"name": "Drama Night", "category": "cultural", "codename": "STAGE-9"},

        # SPORTS
        {"name": "Football League", "category": "sports", "codename": "GOAL-99"},
        {"name": "Basketball Cup", "category": "sports", "codename": "DUNK-3"},
        {"name": "Cricket Clash", "category": "sports", "codename": "SIXER"},

        # OTHERS
        {"name": "Quiz Night", "category": "others", "codename": "BRAIN"},
        {"name": "Treasure Hunt", "category": "others", "codename": "HUNTER"},
        {"name": "Startup Pitch", "category": "others", "codename": "VISION"},
    ]

    events_collection.insert_many(sample_events)

    return {"message": "12 events inserted successfully"}

# =========================
# MODELS
# =========================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    login: str
    password: str

class EventRegister(BaseModel):
    event_id: str

# =========================
# CREATE ACCOUNT
# =========================

@app.post("/create-account")
def create_account(user: UserCreate):

    existing_user = users_collection.find_one({
        "$or": [
            {"username": user.username},
            {"email": user.email}
        ]
    })

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    users_collection.insert_one({
        "username": user.username,
        "email": user.email,
        "password": user.password,
        "registered_events": []
    })

    return {"message": "Account created successfully"}

# =========================
# LOGIN
# =========================

@app.post("/login")
def login(user: UserLogin):

    db_user = users_collection.find_one({
        "$or": [
            {"username": user.login},
            {"email": user.login}
        ]
    })

    if not db_user or db_user["password"] != user.password:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "username": db_user["username"]
    }

# =========================
# GET EVENTS
# =========================

@app.get("/events")
def get_events():

    events = list(events_collection.find())

    return [
        {
            "_id": str(event["_id"]),
            "name": event["name"],
            "category": event["category"],
            "codename": event["codename"]
        }
        for event in events
    ]

# =========================
# REGISTER EVENT
# =========================

@app.post("/register-event/{username}")
def register_event(username: str, event: EventRegister):

    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    event_data = events_collection.find_one({"_id": ObjectId(event.event_id)})
    if not event_data:
        raise HTTPException(status_code=404, detail="Event not found")

    registration_info = {
        "event_name": event_data["name"],
        "category": event_data["category"],
        "registered_at": datetime.utcnow().isoformat()
    }

    users_collection.update_one(
        {"username": username},
        {"$push": {"registered_events": registration_info}}
    )

    return {"message": "Event registered successfully"}

# =========================
# PROFILE
# =========================

@app.get("/profile/{username}")
def get_profile(username: str):

    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user["username"],
        "email": user["email"],
        "registered_events": user.get("registered_events", [])
    }