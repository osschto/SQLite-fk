from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

# -------------------POSTTAG------------------- #
class PostTag(SQLModel, table=True):
    post_id : Optional[int] = Field(default=None, primary_key=True, foreign_key="post.id")
    tag_id : Optional[int] = Field(default=None, primary_key=True, foreign_key="tag.id")


# -------------------USER------------------- #
class User(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    name : str
    
    posts : List["Post"] = Relationship(back_populates="user")
    likes : List["Like"] = Relationship(back_populates="users")
    following: List["Subscription"] = Relationship(back_populates="follower", sa_relationship_kwargs={"foreign_keys": "[Subscription.follower_id]"})
    followers: List["Subscription"] = Relationship(back_populates="followed", sa_relationship_kwargs={"foreign_keys": "[Subscription.followed_id]"})
    

# -------------------POST------------------- #
class Post(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    user_id : Optional[int] = Field(foreign_key="user.id")
    title : str
    content : str
    author : str

    user : Optional["User"] = Relationship(back_populates="posts")
    comments : List["Comment"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade" : "all, delete"})
    tags : List["Tag"] = Relationship(back_populates="posts", link_model=PostTag)
    likes : List["Like"] = Relationship(back_populates="posts")


# -------------------COMMENT------------------- #
class Comment(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    post_id : Optional[int] = Field(foreign_key="post.id")
    user_id : Optional[int] = Field(foreign_key="user.id")
    text : str

    post : Optional["Post"] = Relationship(back_populates="comments")


# -------------------TAG------------------- #
class Tag(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    name : str

    posts : List["Post"] = Relationship(back_populates="tags", link_model=PostTag)


# -------------------LIKE------------------- #
class Like(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    user_id : Optional[int] = Field(foreign_key="user.id")
    post_id : Optional[int] = Field(foreign_key="post.id")

    users : Optional["User"] = Relationship(back_populates="likes")
    posts : Optional["Post"] = Relationship(back_populates="likes")

    __table_args__ = (UniqueConstraint("user_id", "post_id", name = "unique_args"),)


# -------------------SUBSCRIPTION------------------- #
class Subscription(SQLModel, table=True):
    id : Optional[int] = Field(default=None, primary_key=True)
    follower_id : Optional[int] = Field(foreign_key="user.id")
    followed_id : Optional[int] = Field(foreign_key="user.id")

    follower: Optional[User] = Relationship(back_populates="following", sa_relationship_kwargs={"foreign_keys": "[Subscription.follower_id]"})
    followed: Optional[User] = Relationship(back_populates="followers", sa_relationship_kwargs={"foreign_keys": "[Subscription.followed_id]"})
