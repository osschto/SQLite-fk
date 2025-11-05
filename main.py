import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import SQLModel, select
from db import *
from models import *
from schemas import *

app = FastAPI()

SQLModel.metadata.create_all(engine)

# -------------------USER------------------- #
@app.post("/users", tags=["Пользователь"], summary="Добавить нового пользователя")
def add_user(user : UserCreate, s : Session = Depends(get_session)):
    userdb = User(name = user.name)
    s.add(userdb)
    s.commit()
    s.refresh(userdb)
    return {f"Пользователь '{userdb.name}' успешно добавлен"}


@app.get("/users/posts/counts", tags=["Пользователь"], summary="Получить список всех пользователей и кол-во их постов")
def get_users_posts_count(s : Session = Depends(get_session)):
    userdb = s.exec(select(User)).all()
    
    return [{
            "user" : user.name, "post_count" : len(user.posts)
        } for user in userdb]


@app.get("/users/{user_id}/followers", tags=["Пользователь"], summary="Получить список подписчиков пользователя")
def get_followers(user_id : int, s : Session = Depends(get_session)):
    userdb = s.get(User, user_id)
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    followers = [u.follower.name for u in userdb.followers]

    return {
        "user" : userdb.name,
        "followers" : followers
    }


@app.get("/users/{user_id}/posts_with_comments", tags=["Пользователь"], summary="Получить список постов пользователя с комментариями")
def get_posts_with_comments(user_id : int, db : Session = Depends(get_session)):
    userdb = db.exec(select(User).where(User.id == user_id)).first()
    postdb = db.exec(select(Post).where(Post.user_id == user_id)).all()
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not postdb:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    post_with_comments = {}
    for post in postdb:
        comments = [c for c in post.comments]
        post_with_comments[post.title] = comments
        # a.append(comments)
    return {
        "user" : userdb.name,
        "comments" : post_with_comments
    }


# -------------------POST------------------- #
@app.post("/posts", tags=["Пост"], summary="Добавить новый пост")
def add_post(post : PostCreate, s : Session = Depends(get_session)):
    userdb = s.get(User, post.user_id)
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    postdb = Post(user_id = post.user_id, title = post.title, content = post.content, author = post.author)
    s.add(postdb)
    s.commit()
    s.refresh(postdb)
    return {
        "user" : userdb.name,
        "title" : postdb.title,
        "content" : postdb.content
    }


@app.get("/posts", tags=["Посты"], summary="получить список всех постов")
def get_all_posts(db : Session = Depends(get_session)):
    statement = select(Post).offset(2).limit(2)
    posts = db.exec(statement).all()
    return posts


@app.get("/users/{user_id}/posts", tags=["Пост"], summary="Получить список всех постов пользователя")
def get_posts(user_id : int, s : Session = Depends(get_session)):
    userdb = s.get(User, user_id)
    if not userdb:
        raise HTTPException(status_code=404, detail=f"Пользователь не найден")
    
    return {
        "user" : userdb.name,
        "posts" : [{
            "post_id" : p.id,
            "title" : p.title,
            "content" : p.content
        }for p in userdb.posts]
    }


@app.get("/posts/search", tags=["Пост"], summary="Получить пост по ключевому слову")
def search(keyword : str, db : Session = Depends(get_session)):
        posts = db.query(Post).filter(Post.title.ilike(f"%{keyword}%")).all()
        return {
            "keyword" : keyword,
            "posts" : [{   
                    "user_id" : p.user_id,
                    "title" : p.title,
                    "content" : p.content,
                    "author" : p.author
                }for p in posts]
        }

@app.delete("/posts/{post_id}", tags=["Пост"], summary="Удалить пост")
def delete_post(post_id : int, db : Session = Depends(get_session)):
    postdb = db.exec(select(Post).where(Post.id == post_id)).first()
    comments = db.exec(select(Comment).where(Comment.post_id == post_id)).all()
    if not postdb:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    for comment in comments:
        db.delete(comment)
        db.commit()

    db.delete(postdb)
    db.commit()


# -------------------COMMENT------------------- #
@app.post("/comments", tags=["Комментарий"], summary="Добавить комментарий к посту")
def add_comment(comment : CommentCreate, s : Session = Depends(get_session)):
    postdb = s.get(Post, comment.post_id)
    if not postdb:
        raise HTTPException(status_code=404, detail=f"Пост не найден")
    
    commentdb = Comment(post_id = comment.post_id, text = comment.text)
    s.add(commentdb)
    s.commit()
    s.refresh(commentdb)
    return {
        "message" : "Комментарий успешно добавлен"
    }


@app.get("/posts/{post_id}/comments/count", tags=["Комментарий"], summary="Получить кол-во комментариев конкретного поста")
def get_comm_count(post_id : int, db : Session = Depends(get_session)):
    postdb = db.exec(select(Post).where(Post.id == post_id)).first()
    if not postdb:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    return {
        "post" : postdb.title,
        "comment_count" : len(postdb.comments)
    }


@app.get("/posts/{post_id}/comments", tags=["Комментарий"], summary="Получить список всех комментариев конкретного поста")
def get_comments(post_id : int, s : Session = Depends(get_session)):
    postdb = s.get(Post, post_id)
    if not postdb:
        raise HTTPException(status_code=404, detail=f"Пост не найден")
    
    return {
        "post_id" : post_id,
        "comments" : [{
            "comment_id" : p.id,
            "text" : p.text
        }for p in postdb.comments]
    }


# -------------------TAG------------------- #
@app.post("/tags", tags=["Тэг"], summary="Добавить тэг к посту")
def add_tag(tag : TagCreate, s : Session = Depends(get_session)):
    postdb = s.get(Post, tag.post_id)
    tagdb = s.exec(select(Tag).where(Tag.name == tag.name)).first()
    if not postdb:
        raise HTTPException(status_code=404, detail=f"Пост не найден")

    if not tagdb:
        tagdb = Tag(name = tag.name)
        s.add(tagdb)
        s.commit()
        s.refresh(tagdb)

    if tagdb in postdb.tags:
        raise HTTPException(status_code=400, detail="Данный тэг уже был добавлен к посту")
    
    postdb.tags.append(tagdb)
    s.commit()
    s.refresh(postdb)

    return {"message" : f"Тэг '{tagdb.name}' успешно добавлен"}


@app.get("/tags/{tag_name}", tags=["Тэг"], summary= "Получить список постов по тэгу")
def get_posts_by_tag(tag_name : str, s : Session = Depends(get_session)):
    tagdb = s.exec(select(Tag).where(Tag.name == tag_name)).first()
    if not tagdb:
        raise HTTPException(status_code=404, detail=f"Тэг не найден")
    
    return {
        "tag_name" : tagdb.name,
        "posts" :[{
            "post_id" : p.id,
            "title" : p.title,
            "content" : p.content
        }for p in tagdb.posts]
    }


# -------------------LIKE------------------- #
@app.post("/posts/{post_id}/likes/users/{user_id}", tags=["Лайк"], summary="Поставить лайк")
def add_like(post_id : int, user_id : int, s : Session = Depends(get_session)):
    userdb = s.get(User, user_id)
    postdb = s.get(Post, post_id)
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if not postdb:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    like = Like(user_id = user_id, post_id = post_id)
    s.add(like)
    s.commit()
    s.refresh(like)
    return {"message" : f"Пользователь {userdb.name} поставил лайк на пост: '{postdb.title}'"}


@app.get("/posts/{post_id}/likes", tags=["Лайк"], summary="Получить кол-во лайков и список тех, кто их поставил")
def get_like_list(post_id : int, s : Session = Depends(get_session)):
    postdb = s.get(Post, post_id)
    if not postdb:
        raise HTTPException(status_code=404, detail="Пост не найден")
    
    likedb = s.exec(select(Like).where(Like.post_id == post_id)).all()
    userdb = [like.users.name for like in likedb]

    return [{
        "post_id" : p.post_id,
        "likes" : len(postdb.likes),
        "users" : userdb
    }for p in postdb.likes]


# -------------------SUBSCRIPTION------------------- #
@app.post("/users/{user_id}/follow/{target_id}", tags=["Подписки"], summary="Подписаться на пользователя")
def subscribe(user_id : int, target_id : int, s : Session = Depends(get_session)):
    subscription = Subscription(follower_id = user_id, followed_id = target_id)
    userdb = s.get(User, user_id)
    targetdb = s.get(User, target_id)
    if not userdb or not targetdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    if user_id == target_id:
        raise HTTPException(status_code=400, detail="Вы не можете подписаться на себя")
    
    for u in targetdb.followers:
        if subscription.follower_id == u.follower_id:
            raise HTTPException(status_code=400, detail="Вы уже подписаны на этого пользователя")
        
    s.add(subscription)
    s.commit()
    return {f"{userdb.name} подписался на {targetdb.name}"}


@app.get("/feed/{user_id}", tags=["Подписки"], summary="Получить все посты от пользователей, на которых подписан данный пользователь")
def get_followed_posts(user_id : int, s : Session = Depends(get_session)):
    userdb = s.get(User, user_id)
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    posts = []
    for f in userdb.following:
        posts.extend(f.followed.posts)
    
    return {
        "user" : userdb.name,
        "feed" : [
            {
                "author" : p.user.name,
                "title" : p.title
            } for p in posts
        ]
    }


@app.get("/users/{user_id}/following", tags=["Подписки"], summary="Получить список тех, на кого подписан пользователь")
def get_followed(user_id : int, s : Session = Depends(get_session)):
    userdb = s.get(User, user_id)
    if not userdb:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    following = [u.followed.name for u in userdb.following]

    return {
        "name" : userdb.name,
        "following" : following
    }


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)