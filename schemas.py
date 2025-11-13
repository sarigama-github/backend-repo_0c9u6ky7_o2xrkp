"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    username: str = Field(..., description="Unique username")
    name: Optional[str] = Field(None, description="Display name")
    email: Optional[str] = Field(None, description="Email address")
    selected_course_id: Optional[str] = Field(None, description="Current course ID")
    xp: int = Field(0, ge=0, description="Total XP earned")
    streak: int = Field(0, ge=0, description="Daily streak count")

class Course(BaseModel):
    """Language course info"""
    name: str = Field(..., description="Course name, e.g., Spanish")
    code: str = Field(..., description="Language code, e.g., es")
    base_language: str = Field("en", description="Base language code, e.g., en")

class Lesson(BaseModel):
    """A lesson belongs to a course"""
    course_id: str = Field(..., description="Course ID")
    title: str = Field(...)
    order: int = Field(..., ge=0)

class Exercise(BaseModel):
    """Exercises inside a lesson"""
    lesson_id: str = Field(..., description="Lesson ID")
    type: Literal["mcq", "translate"]
    prompt: str
    options: Optional[List[str]] = None
    answer: str = Field(..., description="Correct answer")

class Progress(BaseModel):
    """User progress by lesson"""
    user_id: str = Field(...)
    lesson_id: str = Field(...)
    completed: bool = False
    correct_count: int = 0
    total_count: int = 0

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
