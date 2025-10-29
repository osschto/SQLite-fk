from pydantic import BaseModel

# ---Модель для пользователей---
class UserCreate(BaseModel):
    name : str
# ---Модель для пользователей---

# ---Модель для постов---
class PostCreate(BaseModel):
    user_id : int
    title : str
    content : str
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