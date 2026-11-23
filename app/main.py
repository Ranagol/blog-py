from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from tracefox.integrations.fastapi import init_tracefox

from app.config import settings
from app.database import engine
from app.routers import auth, comments, posts

# Create the app
app = FastAPI(title="blog-py")

# Add Tracefox integration. Tracefox = Telescope for Python
init_tracefox(app, engine=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# We add pagination to our app
add_pagination(app) 



