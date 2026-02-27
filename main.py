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
# AUTO SEED EVENTS
# =========================

def seed_events():
    if events_collection.count_documents({}) == 0:
        sample_events = [
            # TECHNICAL (3)
            {"name": "Hackathon", "category": "technical", "codename": "CODE-X"},
            {"name": "AI Challenge", "category": "technical", "codename": "NEURAL-7"},
            {"name": "Cyber Security", "category": "technical", "codename": "FIREWALL"},

            # CULTURAL (3)
            {"name": "Dance Battle", "category": "cultural", "codename": "RHYTHM"},
            {"name": "Music Fest", "category": "cultural", "codename": "MELODY"},
            {"name": "Drama Night", "category": "cultural", "codename": "STAGE-9"},

            # SPORTS (3)
            {"name": "Football League", "category": "sports", "codename": "GOAL-99"},
            {"name": "Basketball Cup", "category": "sports", "codename": "DUNK-3"},
            {"name": "Cricket Clash", "category": "sports", "codename": "SIXER"},

            # OTHERS (3)
            {"name": "Quiz Night", "category": "others", "codename": "BRAIN"},
            {"name": "Treasure Hunt", "category": "others", "codename": "HUNTER"},
            {"name": "Startup Pitch", "category": "others", "codename": "VISION"},
        ]

        events_collection.insert_many(sample_events)

seed_events()

# =========================
# ROOT
# =========================

@app.get("/")
def home():
    return {"message": "Student Event Management API is running"}

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

    formatted = []
    for event in events:
        formatted.append({
            "_id": str(event["_id"]),
            "name": event["name"],
            "category": event["category"],
            "codename": event["codename"]
        })

    return formatted