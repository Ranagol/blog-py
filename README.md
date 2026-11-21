# Global Application Specification --- Dockerized FastAPI Blog API

## 1. Project Goal

Build a simple Dockerized blog API using FastAPI.

The application should be intentionally small and easy to understand. It
is primarily a learning project, so avoid unnecessary complexity,
abstractions, or advanced features unless they are required for the
functionality described below.

The application will initially be **backend/API only**. It will be
tested manually through FastAPI's automatically generated
documentation/interface and automatically through an automated test
suite. A Vue.js frontend container may be added later, so the backend
should expose a clean REST API suitable for a future Vue.js frontend.

## 2. Technology Stack

Use:

-   Python
-   FastAPI
-   PostgreSQL
-   Docker
-   Docker Compose
-   SQLAlchemy 2.x as the ORM
-   Alembic for database migrations
-   `pytest` for automated tests
-   FastAPI `TestClient` and HTTPX for API tests
-   A maintained password-hashing library that supports Argon2 (prefer
    `pwdlib` with Argon2)

Use JWT access-token authentication. Keep the implementation
conventional and easy to understand.

The application should run through Docker Compose with at least:

-   `backend` --- FastAPI application
-   `database` --- PostgreSQL database

Do not add a frontend container yet.

The project should be structured so that a Vue.js frontend can be added
later without restructuring the entire backend.

## 3. Implementation Sequence

Implement the project in the following order. Keep each stage working
before moving to the next one.

1.  **Project and Compose setup:** Create the project structure,
    dependency management, Dockerfile, Docker Compose configuration,
    environment-variable handling, and a minimal FastAPI health
    endpoint.
2.  **Database, models, and migrations:** Configure SQLAlchemy and
    PostgreSQL, create the User, Post, and Comment models, define their
    relationships, and configure Alembic migrations.
3.  **Authentication:** Implement user registration, password hashing,
    login, JWT creation and validation, and the current-user dependency.
4.  **Posts:** Implement public post listing/detail endpoints and
    authenticated post creation, full updates, and deletion.
5.  **Comments and ownership:** Implement comment
    listing/creation/update/deletion and enforce ownership rules for
    posts and comments.
6.  **Full verification and documentation:** Run the complete automated
    test suite, fix failures, run relevant regression tests, and document
    setup, environment variables, commands, and API behavior in the
    README. Add and run focused tests as each earlier stage is
    implemented; do not defer all tests until this final stage.

Do not generate the entire application in one opaque step. Follow this
sequence and keep the code understandable.

## 4. Users

There is only **one type of user**.

There are no administrator roles, moderators, or special permissions.

A user has:

-   `id`
-   `email`
-   `hashed_password`
-   `created_at`

Passwords must never be stored in plaintext. They must be securely
hashed using the selected password-hashing library.

Email addresses must be unique. Email comparison is
**case-insensitive**: normalize email addresses to lowercase before
storing and comparing them; trim surrounding whitespace first and reject
invalid email addresses. Enforce uniqueness in the database as well as
in application validation, so concurrent registrations cannot create
duplicates. Registration with an email that differs only in letter case
from an existing account must be rejected as a duplicate.

Never return the password hash in an API response.

## 5. Authentication

Use **JWT-based access-token authentication**.

Keep the implementation intentionally simple and suitable for learning.

Required functionality:

-   User registration
-   User login
-   Password hashing and verification
-   JWT access-token generation
-   JWT validation
-   Authentication of protected endpoints
-   Identification of the current authenticated user

### Token configuration

-   Use the `HS256` signing algorithm.
-   Read the JWT signing secret from an environment variable named
    `SECRET_KEY`. Never hardcode the secret or commit a real secret to
    version control.
-   Configure access-token lifetime through an environment variable
    named `ACCESS_TOKEN_EXPIRE_MINUTES`.
-   Use **30 minutes** as the default access-token lifetime.
-   Include and validate the token expiration (`exp`) claim.
-   Identify the user in the token's `sub` claim using the user's ID as
    a string, and reject tokens with a missing or invalid subject.
-   Keep the algorithm fixed in application configuration; do not accept
    an arbitrary algorithm from an untrusted token.
-   Provide placeholder values, not real secrets, in `.env.example`.

Do not implement:

-   Refresh tokens
-   OAuth or social login
-   Roles
-   Permission systems
-   Complicated authentication flows

### Login request format

Use a **JSON request body** for login, with `email` and `password`
fields. Return a bearer access token in the response.

Document the bearer-token security scheme in OpenAPI so users can click
**Authorize** in Swagger UI and enter the token. Do not require the
OAuth2 password form flow.

## 6. Posts

A post contains:

-   `id`
-   `title`
-   `content`
-   `created_at`
-   `updated_at`
-   `author_id`

The author is a registered user.

### Public functionality

Unauthenticated users should be able to:

-   View posts
-   View individual posts
-   View comments belonging to posts

### Authenticated functionality

Authenticated users can:

-   Create posts
-   Update their own posts
-   Delete their own posts

A user **cannot update or delete another user's post**. No administrator
override exists.

### Content validation

-   A post title must contain at least one non-whitespace character.
-   Post content must contain at least one non-whitespace character.
-   Reject empty strings and whitespace-only values with a validation
    error.
-   Trim leading and trailing whitespace from titles before storing.
    Preserve content as submitted after checking it is not blank.

There is no need for the following at this stage:

-   Categories
-   Tags
-   Slugs
-   Images
-   Publishing workflow
-   Drafts
-   Likes
-   Post status
-   Pagination

List posts by `created_at` descending, then `id` descending. List
comments by `created_at` ascending, then `id` ascending.

## 7. Comments

A comment contains:

-   `id`
-   `content`
-   `created_at`
-   `updated_at`
-   `author_id`
-   `post_id`

A comment belongs to one user and one post.

Users must be authenticated to create comments.

Authenticated users can:

-   Create comments
-   Update their own comments
-   Delete their own comments

A user **cannot modify or delete another user's comments**.

### Content validation

Comment content must contain at least one non-whitespace character.
Reject empty strings and whitespace-only values with a validation error.
Preserve non-blank comment content as submitted.

Keep comments simple: **plain text only**.

## 8. Authorization Rules

The basic ownership rules are:

``` text
User
 ├── owns Posts
 │    ├── can create
 │    ├── can read
 │    ├── can update own posts
 │    └── can delete own posts
 │
 └── owns Comments
      ├── can create
      ├── can read
      ├── can update own comments
      └── can delete own comments
```

No roles or administrator privileges are required.

The API must verify ownership before allowing update or delete
operations.

### Missing resources and ownership errors

For update and delete operations, return **404 Not Found** both when the
requested resource does not exist and when it exists but belongs to
another user. This avoids revealing resource existence or ownership
through different responses. This rule applies to update and delete;
public read endpoints remain available regardless of resource owner.

For protected endpoints, missing, invalid, or expired bearer tokens
return **401 Unauthorized** and include the `WWW-Authenticate: Bearer`
header. Use **403 Forbidden** only where a resource exists and the
operation is forbidden for a reason other than resource ownership, if
such a case is introduced later.

## 9. Database

Use **PostgreSQL**.

The main entities are:

-   `User`
-   `Post`
-   `Comment`

Relationships:

``` text
User 1 ──── * Post
User 1 ──── * Comment
Post 1 ──── * Comment
```

A post belongs to one user.

A comment belongs to one user and one post.

Use SQLAlchemy 2.x for ORM models and Alembic for database migrations.
Use migrations to create and update the database schema; do not rely on
automatic table creation at application startup.

Store `created_at` and `updated_at` as timezone-aware UTC timestamps.
Update `updated_at` whenever a post or comment changes. Deleting a post
also deletes its comments; there is no user-deletion endpoint in this
version.

## 10. API

Create a clean REST-style API.

The API should provide the following endpoints.

### Health

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Return `{"status": "ok"}` without exposing configuration or secrets |

### Authentication / users

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/users/register` | Register a user |
| `POST` | `/users/login` | Log in and obtain a JWT access token |

### Posts

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/posts` | List posts |
| `GET` | `/posts/{post_id}` | Retrieve an individual post |
| `POST` | `/posts` | Create a post |
| `PUT` | `/posts/{post_id}` | Fully replace the user's own post |
| `DELETE` | `/posts/{post_id}` | Delete the user's own post |

### Comments

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/posts/{post_id}/comments` | List comments for a post |
| `POST` | `/posts/{post_id}/comments` | Create a comment on a post |
| `PUT` | `/comments/{comment_id}` | Fully replace the user's own comment |
| `DELETE` | `/comments/{comment_id}` | Delete the user's own comment |

### Update semantics

Keep `PUT` for updates and define it as **full replacement**, not
partial update:

-   Updating a post requires both `title` and `content`.
-   Updating a comment requires `content`.
-   Missing required fields must produce a validation error.
-   Do not implement `PATCH` at this stage.

The exact endpoint structure may be adjusted if there is a better
conventional FastAPI design, but keep the API simple and predictable.

Use these status-code conventions:

-   Registration and resource creation return `201 Created`.
-   Successful reads, login, and updates return `200 OK`.
-   Successful deletes return `204 No Content` with an empty response
    body.
-   Duplicate registration returns `409 Conflict`.
-   Invalid credentials and missing, invalid, or expired bearer tokens
    return `401 Unauthorized`.
-   Invalid request data returns `422 Unprocessable Entity`.
-   Missing resources, including a missing post when listing or creating
    its comments, return `404 Not Found`.
-   Update and delete return `404 Not Found` for both missing resources
    and resources owned by another user, as specified above.

Do not disclose whether an email address exists when login credentials
are invalid. Return the same authentication error for an unknown email
and an incorrect password.

## 11. Response Format and Privacy

Use consistent Pydantic response schemas. Do not return database model
objects or internal fields directly.

Use these response shapes:

-   Registration: `id`, normalized `email`, and `created_at`.
-   Login: `access_token` and `token_type` (`bearer`).
-   Post: `id`, `title`, `content`, `created_at`, `updated_at`, and
    `author: { id }`.
-   Comment: `id`, `content`, `created_at`, `updated_at`, `post_id`, and
    `author: { id }`.

**Do not include the author's email address** in public post or comment
responses. Do not expose password hashes or other internal
authentication data.

Do not also expose `author_id` when the `author.id` object already
provides that identifier. Update request bodies must not allow clients
to change resource IDs, authors, or timestamps. Document the response
shapes and error status codes in the API.

## 12. API Documentation and Manual Testing

The application should make full use of FastAPI's automatically
generated:

-   Swagger UI
-   OpenAPI documentation

The initial manual testing workflow should use the FastAPI documentation
interface rather than a frontend.

Document the JSON login request and bearer-token authorization flow
clearly. Users should be able to log in, copy the returned access token,
use Swagger UI's **Authorize** control, and then test protected
endpoints.

## 13. Pagination

**Do not implement pagination yet.**

The initial application should return the complete relevant collection.

Pagination may be added as a future feature if it becomes necessary.

## 14. Docker and Environment Configuration

Provide a `docker-compose.yml` that starts:

-   FastAPI backend
-   PostgreSQL database

The backend should communicate with PostgreSQL through the Docker
Compose network.

Configuration such as database credentials and JWT-related settings must
be handled through environment variables rather than hardcoded into the
application.

Provide an appropriate `.env.example`.

### Development database

Use a clearly named development database, for example `blog_dev`.

To add a default user and ten generated users, two posts per user, and two
comments per post to a migrated development database, run
`docker compose exec backend python -m app.seed`. Comment authors are randomly
selected from the seeded users. The default user's email and password can be
configured with `DEFAULT_USER_EMAIL` and `DEFAULT_USER_PASSWORD`. The generated
users use the password `factory-password`; Faker supplies their emails and the
post and comment text. None has special permissions. The command fails if a
seeded email already exists.

To delete all data from the application tables while preserving the tables and
migration history, run `docker compose exec backend python -m scripts.reset_db`.
This permanently removes the application data from the configured database.

### Test database

The automated tests must use a separate PostgreSQL database, for example
`blog_test`.

Make the test database setup explicit and reproducible. Configure
PostgreSQL initialization (for example, with an initialization SQL
script mounted into the database container) to create both databases
when the database volume is first initialized. Initialization scripts
do not run again for an already-initialized data volume, so document a
safe, targeted way to create a missing test database in that case. Do
not require deleting the database volume to set up tests.

Configure a dedicated environment variable such as `TEST_DATABASE_URL`
for the test database. The test configuration and fixtures must connect
using `TEST_DATABASE_URL`, never silently fall back to the development
`DATABASE_URL`.

Add safety checks in the test setup that:

-   Fail immediately if `TEST_DATABASE_URL` is missing.
-   Fail if the test database URL points to the configured development
    `DATABASE_URL` or, when configured, `PRODUCTION_DATABASE_URL`.
-   Verify the exact expected test database name (`blog_test`) before
    running tests.

Use a test-only database role that owns or has the required test
database privileges, and never provide production credentials to the
test process.

The test suite must never run destructive setup, cleanup, or migrations
against the development or production database.

Document the safe test command, for example:

``` bash
docker compose exec backend pytest
```

This command is safe only when the backend container has a correctly
configured `TEST_DATABASE_URL` pointing to the dedicated test database
and the test safety checks are enabled.

Test fixtures may create and clean up schema/data only in the verified
test database. They must never run migrations, schema drops, or cleanup
against development or production databases.

## 15. Code Quality and Learning Requirements

This is a learning project, not a production-scale enterprise
application.

The code should prioritize:

-   Clarity
-   Simplicity
-   Conventional FastAPI patterns
-   Understandable project structure
-   Separation of concerns
-   Type hints
-   Pydantic validation
-   Clear database models
-   Clear API schemas
-   Understandable authentication code
-   Sensible error handling

Avoid unnecessary:

-   Design patterns
-   Abstraction layers
-   Generic repositories
-   Excessive dependency injection
-   Microservices
-   Event systems
-   Background workers
-   Caching
-   Redis
-   Message queues
-   Complicated configuration systems

The goal is to understand how a real but small FastAPI application is
built, rather than hiding the implementation behind excessive
abstractions.

Document the selected dependency versions and the key implementation
choices in the README.

## 16. Future Vue.js Frontend

There is **no Vue.js frontend in the initial implementation**.

However, the API should be designed so that a Vue.js frontend can later
be added as a separate Docker Compose service.

The backend should remain a clean API with JSON request/response data
and JWT bearer authentication suitable for a future Vue.js client.

## 17. Explicitly Out of Scope

Do not implement the following in the initial version:

-   Admin users
-   User roles
-   Permission systems
-   Pagination
-   Tags
-   Categories
-   Images
-   Likes
-   Search
-   Post drafts
-   Publishing workflow
-   Email verification
-   Password reset
-   OAuth/social login
-   Refresh tokens
-   Redis
-   Background jobs
-   Notifications
-   Frontend
-   Microservices

These can be added later if needed.

## 18. Main Principle

**Keep the application as simple as possible while still making it a
realistic FastAPI project.**

Do not add features merely because they are common in larger
applications.

The finished project should be small enough for a developer learning
FastAPI to understand every important part of the application:

-   Docker
-   PostgreSQL
-   Database models
-   Migrations
-   Pydantic schemas
-   REST endpoints
-   JWT authentication
-   Password hashing
-   Authorization and ownership checks
-   Validation
-   FastAPI's dependency system
-   Automated testing

The architecture should also leave a clean path for adding a Vue.js
frontend later.

## 19. Automated Testing

Automated testing is a **mandatory part** of this project.

### Testing technology

Use:

-   `pytest`
-   FastAPI `TestClient`
-   `HTTPX`
-   `pytest` fixtures
-   SQLAlchemy
-   The dedicated PostgreSQL test database described in the Docker and
    environment configuration section

### Testing coverage

Implement tests for:

-   Health endpoint response
-   User registration and duplicate email handling, including
    case-insensitive duplicates
-   Password hashing and verification
-   Login and JWT authentication
-   Token expiration and invalid-token handling
-   Access to protected and public endpoints
-   Post creation, retrieval, updating, and deletion
-   Post ownership and authorization
-   Comment creation, retrieval, updating, and deletion
-   Comment ownership and authorization
-   Post deletion removing its associated comments
-   UTC timestamps and update-timestamp changes
-   Deterministic ordering of post and comment collections
-   Empty and whitespace-only title/content validation
-   Full-replacement `PUT` behavior and missing-field validation
-   404 behavior for nonexistent resources and resources owned by
    another user
-   Response privacy (author email and password hashes must not be
    exposed)
-   Database relationships between users, posts, and comments

### Testing rules

-   Every implemented feature must have corresponding automated tests.
-   Tests must use the dedicated PostgreSQL test database.
-   Tests must not modify development or production data.
-   Tests must be repeatable and independent of one another.
-   Database changes made during tests must be properly rolled back or
    cleaned up.
-   Both successful operations and expected failure cases must be
    tested.
-   Run the automated test suite after implementing functionality.
-   Fix failing tests before considering the implementation complete.
-   Run relevant regression tests after modifying existing
    functionality.
-   Test setup must fail safely if the dedicated test database is not
    configured correctly.

### AI development workflow

The AI must follow this cycle:

1.  Implement a feature.
2.  Write the corresponding tests.
3.  Execute the tests against the dedicated test database.
4.  Analyze and fix any failures.
5.  Execute the tests again.
6.  Report the results.

The AI must never claim that a feature is fully implemented and tested
without actually executing the corresponding tests.

Provide a clear command for running the complete test suite, for
example:

``` bash
docker compose exec backend pytest
```

The README must explain how the test database is created, configured,
verified, and safely used by this command.

## 20. Running the application

The implementation uses Python 3.12 in the backend image and PostgreSQL
16. The selected direct dependency versions are pinned in
`pyproject.toml`:

| Dependency | Version |
| --- | --- |
| FastAPI | 0.163.1 |
| SQLAlchemy | 2.1.9 |
| Alembic | 1.20.1 |
| psycopg | 3.3.9 |
| Pydantic | 2.14.3 |
| pydantic-settings | 2.16.3 |
| PyJWT | 2.15.1 |
| pwdlib | 0.4.2 |
| Uvicorn | 0.54.0 |
| pytest | 8.4.2 |
| HTTPX | 0.28.1 |

### Start the services

1. Copy `.env.example` to `.env`.
2. Replace the local database passwords and `SECRET_KEY`. Generate a
   local signing secret with `openssl rand -hex 32`. Do not use the
   example values outside local development. Set `HOST_UID` and `HOST_GID`
   in `.env` to the output of `id -u` and `id -g` on the host.
3. Build and start the services:

   ```bash
   docker compose up --build -d
   ```

4. Apply the database migrations to the development database:

   ```bash
   docker compose exec backend alembic upgrade head
   ```

5. Open Swagger UI at <http://localhost:8000/docs>.

The backend mounts the project directory read-write at `/app` and runs as
the configured host UID and GID, so container-generated files are writable
by the host user. Existing `.env` files should also set `HOST_UID` and
`HOST_GID`; if omitted, both default to `1000`. Recreate the backend after
changing these values. The development server automatically reloads when
Python files under `app/` change. Rebuild the image when dependencies change;
mounting files does not install packages. Database model changes still require
migrations.

To generate a migration in the running backend container:

```bash
docker compose exec backend alembic revision --autogenerate -m "Describe change"
```

Review the generated migration, then apply it with `docker compose exec backend
alembic upgrade head`.

The first database startup runs `scripts/init-databases.sql` and creates
the `blog_dev` and `blog_test` databases and their separate application
roles. PostgreSQL runs initialization scripts only when its data
directory is empty. If a database is missing from an already-initialized
volume, connect interactively:

```bash
docker compose exec database psql -U postgres -d postgres
```

In the `psql` prompt, use the container's environment values to create
only the missing role/database (skip any object that already exists):

```sql
\getenv app_db_password DB_PASSWORD
\getenv test_db_password TEST_DB_PASSWORD
CREATE ROLE blog_app LOGIN PASSWORD :'app_db_password';
CREATE DATABASE blog_dev OWNER blog_app;
CREATE ROLE blog_test LOGIN PASSWORD :'test_db_password';
CREATE DATABASE blog_test OWNER blog_test;
```

Do not delete the data volume to rerun initialization.
`docker compose down` stops services while preserving the database
volume.

### Run the tests

The backend container receives `TEST_DATABASE_URL` and the test suite
checks that it names `blog_test`, uses the `blog_test` database role,
and does not match the configured development or production database.
The test fixtures create and drop schema only in this verified test
database.

Run the complete suite with:

```bash
docker compose exec backend pytest
```

Tests use transaction rollback between cases and remove the test schema
after the session. They do not run Alembic migrations. Apply migrations
to the development database explicitly with the command above.
