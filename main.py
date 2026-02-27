from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

# -----------------------------
# Load Environment Variables
# -----------------------------
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# -----------------------------
# MongoDB Connection
# -----------------------------
client = MongoClient(MONGO_URI)
db = client["student_event_db"]
users_collection = db["users"]
events_collection = db["events"]

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI()

# ✅ CORS CONFIGURATION (IMPORTANT)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Student Event Management API is running"}


# -----------------------------
# Models
# -----------------------------
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    login: str  # username OR email
    password: str


class EventRegister(BaseModel):
    event_id: str


# =====================================================
# CREATE ACCOUNT
# =====================================================
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


# =====================================================
# LOGIN (Username OR Email)
# =====================================================
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


# =====================================================
# GET ALL EVENTS (Dashboard)
# =====================================================
@app.get("/events")
def get_events():

    events = list(events_collection.find())
    for event in events:
        event["_id"] = str(event["_id"])

    return events


# =====================================================
# REGISTER FOR EVENT
# =====================================================
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
        "registered_at": datetime.utcnow()
    }

    users_collection.update_one(
        {"username": username},
        {"$push": {"registered_events": registration_info}}
    )

    return {"message": "Event registered successfully"}


# =====================================================
# PROFILE PAGE
# =====================================================
@app.get("/profile/{username}")
def get_profile(username: str):

    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "username": user["username"],
        "email": user["email"],
        "registered_events": user["registered_events"]
    }


# =====================================================
# INSERT DEFAULT EVENTS (RUN ONLY ONCE)
# =====================================================
@app.post("/insert-default-events")
def insert_default_events():

    if events_collection.count_documents({}) > 0:
        return {"message": "Events already inserted"}

    events = [
        # Cultural
        {"name": "Dance", "category": "Cultural"},
        {"name": "Singing", "category": "Cultural"},
        {"name": "Nukkad", "category": "Cultural"},

        # Technical
        {"name": "Imagix", "category": "Technical"},
        {"name": "Hackathon", "category": "Technical"},
        {"name": "Invictus", "category": "Technical"},

        # Sports
        {"name": "Badminton", "category": "Sports"},
        {"name": "Cricket", "category": "Sports"},
        {"name": "Football", "category": "Sports"},

        # Others
        {"name": "Master and Miss", "category": "Others"},
        {"name": "Treasure Hunt", "category": "Others"},
        {"name": "Fashion Show", "category": "Others"}
    ]

    events_collection.insert_many(events)

    return {"message": "Default events inserted successfully"}