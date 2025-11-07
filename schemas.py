from typing import List
from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from sqlmodel import SQLModel


# -------------------USER------------------- #
class UserCreate(BaseModel):
    name : str

class UserRead(SQLModel):
    id : int
    name : str


# -------------------POST------------------- #
class PostCreate(BaseModel):
    user_id : int
    title : str
    content : str
    author : str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) < 3:
            raise HTTPException(status_code=400, detail="Длина заголовка должна быть больше трех символов")
        return v

class PostRead(SQLModel):
    title : str
    content : str
    author : str

class PostUser(SQLModel):
    user : str
    posts : List[PostRead]

class PostWithTag(SQLModel):
    tag : str
    posts : List[PostRead]


# -------------------COMMENT------------------- #
class CommentCreate(BaseModel):
    post_id : int
    user_id : int
    text : str

class CommentRead(SQLModel):
    user_id : int
    text : str

class CommentsPost(SQLModel):
    post : str
    comments : List[CommentRead]

# -------------------TAG------------------- #
class TagCreate(BaseModel):
    post_id : int
    name : str


# -------------------SUBSCRIPTION------------------- #
class FollowersRead(SQLModel):
    user : str
    followers : List[str]

class FollowingRead(SQLModel):
    user : str
    following : List[str]

class FeedRead(SQLModel):
    user : str
    feed : List[dict]