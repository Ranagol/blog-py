from fastapi import FastAPI

from app.routers import auth, comments, posts

app = FastAPI(title="blog-py")

# Health check endpoint. We simply check if the application is running.
@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(posts.router)



# Both routes blow are for comments.
# post_router has the /posts prefix, so it handles listing and creating comments under a post: /posts/{post_id}/comments.
app.include_router(comments.post_router)
# comment_router has the /comments prefix, so it handles updating and deleting a comment by its ID: /comments/{comment_id}.
app.include_router(comments.comment_router)

# @app.get('/hamsters', tags=['hamsters'])
# def get_hamsters() -> list[Hamster]

