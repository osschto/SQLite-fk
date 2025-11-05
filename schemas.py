from fastapi import HTTPException
from pydantic import BaseModel, field_validator

# ---Модель для пользователей---
class UserCreate(BaseModel):
    name : str
# ---Модель для пользователей---

# ---Модель для постов---
class PostCreate(BaseModel):
    user_id : int
    title : str
    content : str
    author : str

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v) < 3:
            raise HTTPException(status_code=400, detail="Длина заголовка должна быть юольше трех символов")
        return v
# ---Модель для постов---

# ---Модель для комментариев---
class CommentCreate(BaseModel):
    post_id : int
    text : str
# ---Модель для комментариев---

# ---Модель для тэгов---
class TagCreate(BaseModel):
    post_id : int
    name : str
# ---Модель для тэгов---