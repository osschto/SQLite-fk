import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import SQLModel, select
from db import *
from models import *
from schemas import *

app = FastAPI()

SQLModel.metadata.create_all(engine)

# -----------------------------USER----------------------------- #
@app.post("/users", tags=["Пользователи"], summary="Добавить нового пользователя")
def add_user(user : UserCreate, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.name == user.name)).first()
    if db_user:
        raise HTTPException(status_code=400, detail=f"Пользователь с именем <{user.name}> уже существует")
    
    db_user = User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {f"Пользователь <{db_user.name}> успешно добавлен"}


@app.get("/users/", response_model=List[UserRead], tags=["Пользователи"], summary="Получить список всех пользователей")
def get_all_users(db : Session = Depends(get_session)):
    return db.exec(select(User)).all()


@app.get("/users/posts/count", tags=["Пользователи"], summary="Получить список всех пользователей и кол-во их постов")
def get_users_posts_count(db : Session = Depends(get_session)):
    users = db.exec(select(User)).all()
    return [{
        "user" : user.name,
        "posts_count" : len(user.posts)
        }for user in users]


@app.get("/users/{user_id}/post_with_comments", tags=["Пользователи"], summary="Получить список всех постов пользователя с комментариями")
def get_user_post_with_comments(user_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    db_post = db.exec(select(Post).where(Post.user_id == user_id)).all()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not db_post:
        raise HTTPException(status_code=404, detail="Посты не найдены")
    
    total = []
    for post in db_post:
        total.append({
            "user" : db_user.name,
            "post_title" : post.title,
            "content" : post.content,
            "comments" : [c.text for c in post.comments]
        })
        
    return total

# -----------------------------POST----------------------------- #
@app.post("/posts", tags=["Посты"], summary="Добавить новый пост")
def add_post(post : PostCreate, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where((Post.user_id == post.user_id) & (Post.title == post.title))).first()
    if db_post:
        raise HTTPException(status_code=400, detail=f"Пост с заголовком <{post.title}> уже существует")
    
    db_post = Post(**post.model_dump())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return {f"Пост с заголовком <{db_post.title}> успешно добавлен"}


@app.get("/posts/", response_model=List[PostRead], tags=["Посты"], summary="Получить список всех постов")
def get_all_posts(db : Session = Depends(get_session)):
    return db.exec(select(Post)).all()


@app.get("/user/{user_id}/posts", response_model=PostUser, tags=["Посты"], summary="Получить список всех постов конкретного пользователя")
def get_posts_by_user_id(user_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    posts = db.exec(select(Post).where(Post.user_id == user_id))
    return {"user" : db_user.name, "posts" : posts}


@app.get("/posts/search", response_model=List[PostRead], tags=["Посты"], summary="Получить список постов по ключевому слову из заголовка")
def search(keyword : str, db : Session = Depends(get_session)):
    db_post = db.query(Post).filter(Post.title.ilike(f"%{keyword}%")).all()
    return db_post


@app.delete("/posts/{post_id}", tags=["Посты"], summary="Удалить пост")
def delete_post(post_id : int, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == post_id)).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")

    db.delete(db_post)
    db.commit()
    return {"Пост успешно удален"}


# -----------------------------COMMENT----------------------------- #
@app.post("/comments", tags=["Комментарии"], summary="Написать комментарий к посту")
def add_comment(comment : CommentCreate, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == comment.user_id)).first()
    db_post = db.exec(select(Post).where(Post.id == comment.post_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    db_comment = Comment(**comment.model_dump())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return {f"Комментарий <{comment.text}> успешно добавлен"}


@app.get("/comments/", response_model=List[CommentRead], tags=["Комментарии"], summary="Получить список всех комментариев")
def get_all_comments(db : Session = Depends(get_session)):
    return db.exec(select(Comment)).all()
    

@app.get("/comments/{post_id}", response_model=CommentsPost, tags=["Комментарии"], summary="Получить список всех комментариев конкретного поста")
def get_post_comments(post_id : int, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == post_id)).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return {"post" : db_post.title, "comments" : db_post.comments}


@app.get("/post/{post_id}/comments/count", tags=["Комментарии"], summary="Получить кол-во комментариев конкретного поста")
def get_comments_count(post_id : int, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == post_id)).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return {"post" : db_post.title, "comment_count" : len(db_post.comments)}


# -----------------------------TAG----------------------------- #
@app.post("/tags", tags=["Тэги"], summary="Добавить тэг к посту")
def add_tag(tag : TagCreate, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == tag.post_id)).first()
    db_tag = db.exec(select(Tag).where(Tag.name == tag.name)).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if db_tag in db_post.tags:
        raise HTTPException(status_code=400, detail="Тэг с таким именем уже существует")
    if not db_tag:
        db_tag = Tag(**tag.model_dump())
        db.add(db_tag)
        db.commit
        db.refresh(db_tag)

    db_post.tags.append(db_tag)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return {f"Тэг <{db_tag.name}> успешно добавлен к посту <{db_post.title}>"}


@app.get("/posts/tags/{tag_name}", response_model=PostWithTag, tags=["Тэги"], summary="Получить список постов по тэгу")
def get_posts_by_tag(tag_name : str, db : Session = Depends(get_session)):
    db_tag = db.exec(select(Tag).where(Tag.name == tag_name)).first()
    if not db_tag:
        raise HTTPException(status_code=404, detail=f"Тэг с именем <{tag_name}> не найден")
    return {"tag" : db_tag.name, "posts" : db_tag.posts}


# -----------------------------LIKE----------------------------- #
@app.post("/posts/{post_id}/likes/users/{user_id}", tags=["Лайки"], summary="Поставить лайк посту")
def like(post_id : int, user_id : int, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == post_id)).first()
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    check = db.exec(select(Like).where((Like.user_id == user_id)&(Like.post_id == post_id))).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    if not db_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if check:
        raise HTTPException(status_code=400, detail="Вы уже ставили лайк этому посту")
    
    db_like = Like(user_id=user_id, post_id=post_id)
    db.add(db_like)
    db.commit()
    db.refresh(db_like)
    return {f"Пользователь <{db_user.name}> поставил лайк посту <{db_post.title}>"}


@app.get("/posts/{post_id}/likes", tags=["Лайки"], summary="Получить кол-во лайков поста и список тех, кто их поставил")
def get_likes_count(post_id : int, db : Session = Depends(get_session)):
    db_post = db.exec(select(Post).where(Post.id == post_id)).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    return {
        "post_title" : db_post.title,
        "likes" : len(db_post.likes),
        "users" : [u.users.name for u in db_post.likes]
    }


# -----------------------------SUBSCRIPTION----------------------------- #
@app.post("/users/{user_id}/follow/{target_id}", tags=["Подписки"], summary="Подписаться")
def subscribe(user_id : int, target_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    db_target = db.exec(select(User).where(User.id == target_id)).first()
    check = db.exec(select(Subscription).where((Subscription.follower_id == user_id)&(Subscription.followed_id == target_id))).first()
    if not db_user or not db_target:
        raise HTTPException(status_code=404, detail="пользователь не найден")
    if check:
        raise HTTPException(status_code=400, detail="Вы уже подписаны на данного пользователя")
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Вы не можете подписаться на себя")
    
    db_sub = Subscription(follower_id=user_id, followed_id=target_id)
    db.add(db_sub)
    db.commit()
    db.refresh(db_sub)
    return {f"Пользователь <{db_user.name}> подписался на <{db_target.name}>"}


@app.get("/users/{user_id}/followers", response_model=FollowersRead, tags=["Подписки"], summary="Получить список подписчиков пользователя")
def get_followers(user_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="пользователь не найден")
    
    followers = [f.follower.name for f in db_user.followers]
    return {"user" : db_user.name, "followers" : followers}


@app.get("/users/{user_id}/following", response_model=FollowingRead, tags=["Подписки"], summary="Получить список подписок пользователя")
def get_followers(user_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="пользователь не найден")
    
    following = [f.followed.name for f in db_user.following]
    return {"user" : db_user.name, "following" : following}


@app.get("/feed/{user_id}", response_model=FeedRead, tags=["Подписки"], summary="Получить все посты пользователей, на которых подписан данный пользователь")
def get_feed_posts(user_id : int, db : Session = Depends(get_session)):
    db_user = db.exec(select(User).where(User.id == user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="пользователь не найден")

    feed = []
    for f in db_user.following:
        for p in f.followed.posts:
            feed.append({"author" : p.author, "title" : p.title})

    return {"user" : db_user.name, "feed" : feed}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)