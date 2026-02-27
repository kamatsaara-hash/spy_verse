from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["SPYDATA"]
users_collection = db["users"]
events_collection = db["events"]

app = FastAPI()

# ✅ FIXED CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Student Event Management API is running"}


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    login: str
    password: str


class EventRegister(BaseModel):
    event_id: str


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


@app.get("/events")
def get_events():
    events = list(events_collection.find())
    for event in events:
        event["_id"] = str(event["_id"])
    return events


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