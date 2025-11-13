import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Language Learning API running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ---------- Models for requests ----------
class CreateUserReq(BaseModel):
    username: str
    name: Optional[str] = None

class CreateCourseReq(BaseModel):
    name: str
    code: str
    base_language: str = "en"

class CreateLessonReq(BaseModel):
    course_id: str
    title: str
    order: int

class CreateExerciseReq(BaseModel):
    lesson_id: str
    type: str
    prompt: str
    options: Optional[List[str]] = None
    answer: str

class AnswerReq(BaseModel):
    exercise_id: str
    answer: str
    user_id: Optional[str] = None

# ---------- Helper ----------
def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")

# ---------- Endpoints ----------
@app.post("/api/users")
def create_user(payload: CreateUserReq):
    user = {
        "username": payload.username,
        "name": payload.name,
        "xp": 0,
        "streak": 0,
    }
    user_id = db["user"].insert_one(user).inserted_id
    return {"id": str(user_id), **user}

@app.get("/api/courses")
def list_courses():
    items = get_documents("course")
    for doc in items:
        doc["id"] = str(doc.pop("_id"))
    return items

@app.post("/api/courses")
def create_course(payload: CreateCourseReq):
    course_id = create_document("course", payload.model_dump())
    return {"id": course_id, **payload.model_dump()}

@app.get("/api/courses/{course_id}/lessons")
def list_lessons(course_id: str):
    items = get_documents("lesson", {"course_id": course_id})
    for doc in items:
        doc["id"] = str(doc.pop("_id"))
    return items

@app.post("/api/lessons")
def create_lesson(payload: CreateLessonReq):
    lesson_id = create_document("lesson", payload.model_dump())
    return {"id": lesson_id, **payload.model_dump()}

@app.get("/api/lessons/{lesson_id}/exercises")
def list_exercises(lesson_id: str):
    items = get_documents("exercise", {"lesson_id": lesson_id})
    for doc in items:
        doc["id"] = str(doc.pop("_id"))
    return items

@app.post("/api/exercises")
def create_exercise(payload: CreateExerciseReq):
    if payload.type not in ["mcq", "translate"]:
        raise HTTPException(status_code=400, detail="Invalid exercise type")
    exercise_id = create_document("exercise", payload.model_dump())
    return {"id": exercise_id, **payload.model_dump()}

@app.post("/api/answer")
def submit_answer(payload: AnswerReq):
    ex = db["exercise"].find_one({"_id": oid(payload.exercise_id)})
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    correct = str(payload.answer).strip().lower() == str(ex.get("answer", "")).strip().lower()
    return {"correct": correct, "expected": ex.get("answer")}

# Seed demo content endpoint
@app.post("/api/seed")
def seed_demo():
    # Create a demo course, lesson, and a few exercises if not exist
    course = db["course"].find_one({"code": "es"})
    if not course:
        course_id = db["course"].insert_one({"name": "Spanish", "code": "es", "base_language": "en"}).inserted_id
    else:
        course_id = course["_id"]

    lesson = db["lesson"].find_one({"course_id": str(course_id), "order": 1})
    if not lesson:
        lesson_id = db["lesson"].insert_one({"course_id": str(course_id), "title": "Basics 1", "order": 1}).inserted_id
    else:
        lesson_id = lesson["_id"]

    if db["exercise"].count_documents({"lesson_id": str(lesson_id)}) == 0:
        exercises = [
            {"lesson_id": str(lesson_id), "type": "mcq", "prompt": "How do you say 'Hello' in Spanish?", "options": ["Hola", "Adios", "Gracias"], "answer": "Hola"},
            {"lesson_id": str(lesson_id), "type": "translate", "prompt": "Translate: Gracias", "answer": "Thank you"},
        ]
        db["exercise"].insert_many(exercises)

    return {"seeded": True, "course_id": str(course_id), "lesson_id": str(lesson_id)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
