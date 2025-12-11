# FastAPI Mastering

A comprehensive FastAPI application demonstrating modern Python web development best practices, featuring authentication, file uploads, email notifications, and cloud storage integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Technologies](#technologies)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Database Models](#database-models)
- [Testing](#testing)
- [Deployment](#deployment)
- [Key Insights](#key-insights)

## 🎯 Overview

This project is a production-ready FastAPI application showcasing:

- **Modern Python Practices**: Python 3.12+, type hints, async/await patterns
- **Clean Architecture**: Separation of concerns with routers, models, and core modules
- **Security**: JWT-based authentication, password hashing, email confirmation
- **Database Management**: SQLAlchemy 2.0 with Alembic migrations
- **Cloud Integration**: Backblaze B2 for file storage, Mailgun for email
- **Observability**: Structured logging with correlation IDs and Logtail integration
- **Testing**: Comprehensive test suite with pytest and async support

## ✨ Features

### Authentication & Authorization
- **User Registration**: Secure user registration with email validation
- **Email Confirmation**: Token-based email confirmation flow
- **JWT Authentication**: OAuth2 password flow with access tokens
- **Password Security**: SHA256 + bcrypt hashing (bypasses 72-byte limit)
- **Protected Routes**: Dependency-based authentication for protected endpoints

### Content Management
- **Posts**: Create, read, and list posts with sorting options (new, old, most likes)
- **Comments**: Comment on posts with full CRUD operations
- **Likes**: Like/unlike posts functionality
- **Post Details**: Get posts with associated comments and like counts

### File Management
- **File Upload**: Upload files to Backblaze B2 cloud storage
- **Chunked Uploads**: Efficient handling of large files (1MB chunks)
- **File Listing**: List all uploaded files with metadata
- **Temporary Storage**: Secure temporary file handling during upload

### Email Services
- **Registration Emails**: HTML email templates for user registration
- **Email Confirmation**: Automated confirmation email sending
- **Background Tasks**: Async email sending using FastAPI background tasks
- **Mailgun Integration**: Production-ready email delivery

### Logging & Monitoring
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Email Obfuscation**: Privacy-focused email masking in logs
- **Multiple Handlers**: Console, file rotation, and cloud logging (Logtail)
- **Request Tracking**: Correlation ID middleware for request tracing

### Database
- **Multi-Database Support**: Supabase, PostgreSQL, and SQLite (dev/test)
- **Supabase Integration**: Full support for Supabase with optimized connection pooling
- **Async Operations**: Full async/await support with SQLAlchemy 2.0
- **Migrations**: Alembic for database version control with Supabase support
- **Relationships**: Proper foreign keys with cascade deletes
- **SSL Support**: Automatic SSL configuration for Supabase connections

## 📁 Project Structure

```
fastapi-mastering/
├── alembic/                    # Database migrations
│   ├── versions/              # Migration files
│   ├── env.py                 # Alembic environment configuration
│   └── script.py.mako         # Migration template
├── app/
│   ├── core/                  # Core application logic
│   │   ├── config.py          # Environment-based configuration
│   │   ├── config_logging.py  # Logging configuration
│   │   ├── database.py        # Database session management
│   │   └── tasks.py           # Background tasks (email sending)
│   ├── libs/                  # Third-party integrations
│   │   └── b2/                # Backblaze B2 storage client
│   ├── models/                # Data models
│   │   ├── entities.py        # Pydantic models (request/response)
│   │   └── orm.py             # SQLAlchemy ORM models
│   ├── routers/               # API route handlers
│   │   ├── bucket.py          # File upload endpoints
│   │   ├── post.py            # Post and comment endpoints
│   │   ├── tasks.py           # Task endpoints
│   │   └── user.py            # User authentication endpoints
│   ├── tests/                 # Test suite
│   │   ├── conftest.py        # Pytest fixtures and configuration
│   │   └── routers/           # Router-specific tests
│   └── main.py                # FastAPI application entry point
├── docker-compose.yml         # Docker services configuration
├── Dockerfile                 # Container image definition
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project metadata and dependencies
├── alembic.ini               # Alembic configuration
└── README.md                # This file
```

## 🛠 Technologies

### Core Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Pydantic**: Data validation using Python type annotations

### Database
- **SQLAlchemy 2.0**: Modern ORM with async support
- **Alembic**: Database migration tool
- **PostgreSQL**: Production database (via asyncpg)
- **SQLite**: Development/testing database (via aiosqlite)

### Authentication & Security
- **python-jose**: JWT token encoding/decoding
- **bcrypt**: Password hashing
- **OAuth2**: Password flow implementation

### Storage & Services
- **Backblaze B2 SDK**: Cloud object storage
- **Mailgun**: Email delivery service
- **aiofiles**: Async file operations

### Logging & Monitoring
- **logtail-python**: Cloud log aggregation
- **python-json-logger**: JSON log formatting
- **rich**: Enhanced console output
- **asgi-correlation-id**: Request correlation tracking

### Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for testing

### Development Tools
- **ruff**: Fast Python linter and formatter
- **mypy**: Static type checking

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (optional, for containerized setup)
- PostgreSQL (optional, for production)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/tien-le/fastapi-mastering.git
   cd fastapi-mastering
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Docker Setup

1. **Start services**
   ```bash
   docker-compose up -d
   ```

2. **Run migrations** (in a separate container)
   ```bash
   docker-compose run alembic python -m alembic upgrade head
   ```

3. **Access services**
   - API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`
   - pgAdmin: `http://localhost:8090`

## ⚙️ Configuration

The application uses environment-based configuration with Pydantic Settings.

### Environment Variables

#### Base Configuration
- `ENV_STATE`: Environment state (`dev`, `prod`, or `test`)
- `DOMAIN`: Server domain name
- `BACKEND_CORS_ORIGINS`: Allowed CORS origins (comma-separated)

#### Authentication
- `DEV_JWT_SECRET_KEY`: JWT secret key (development)
- `DEV_JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `DEV_ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration (default: 30)
- `DEV_CONFIRM_TOKEN_EXPIRE_MINUTES`: Confirmation token expiration (default: 60)

#### Database

**Supabase (Recommended for Production)**
- `DEV_SUPABASE_DB_URL`: Supabase direct database connection URL (postgresql://...) - **OR**
- `DEV_SUPABASE_URL`: Supabase project URL (e.g., https://xxx.supabase.co) + `DEV_SUPABASE_DB_PASSWORD`: Database password (auto-constructs DB URL)
- `DEV_SUPABASE_KEY`: Supabase anon/service role key (for API access, different from DB password)
- `PROD_SUPABASE_DB_URL`: Production Supabase database URL - **OR**
- `PROD_SUPABASE_URL`: Production Supabase project URL + `PROD_SUPABASE_DB_PASSWORD`: Database password (auto-constructs DB URL)
- `PROD_SUPABASE_KEY`: Production Supabase key (for API access)

**PostgreSQL (Alternative)**
- `DEV_POSTGRESQL_USERNAME`: PostgreSQL username
- `DEV_POSTGRESQL_PASSWORD`: PostgreSQL password
- `DEV_POSTGRESQL_SERVER`: PostgreSQL host
- `DEV_POSTGRESQL_PORT`: PostgreSQL port
- `DEV_POSTGRESQL_DATABASE`: Database name

**Generic Database URL**
- `DEV_DATABASE_URL`: Full database connection URL
- `PROD_DATABASE_URL`: Production database connection URL

**Priority Order:**
1. Supabase (`SUPABASE_DB_URL`) - Highest priority
2. Generic `DATABASE_URL`
3. Individual PostgreSQL components
4. SQLite fallback (development only)

If no database credentials are provided, the app falls back to SQLite (`dev.db`) in development mode only.

#### Setting Up Supabase

1. **Create a Supabase Project**
   - Go to [https://supabase.com](https://supabase.com)
   - Create a new project
   - Wait for the database to be provisioned

2. **Get Your Database Connection Details**

   You have two options:

   **Option A: Use Direct Database Connection String (Recommended)**
   - Navigate to: Project Settings → Database → Connection string
   - Select "Direct connection" or "Connection pooling" mode
   - Copy the connection string (format: `postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres`)

   **Option B: Use Project URL + Database Password (Auto-constructs)**
   - Get your project URL from the dashboard (e.g., `https://xxx.supabase.co`)
   - Get your database password (set during project creation, can be reset in Settings → Database)
   - The app will automatically construct the database connection string

3. **Get Your API Keys**
   - Navigate to: Project Settings → API
   - Copy the "anon" key (for client-side) or "service_role" key (for server-side)
   - Note: API keys are different from the database password

4. **Configure Environment Variables**

   **For Development (Option A - Direct DB URL):**
   ```bash
   ENV_STATE=dev
   DEV_SUPABASE_DB_URL=postgresql://postgres:your_password@xxx.supabase.co:5432/postgres
   DEV_SUPABASE_URL=https://xxx.supabase.co
   DEV_SUPABASE_KEY=your_anon_key_here
   ```

   **For Development (Option B - Auto-construct):**
   ```bash
   ENV_STATE=dev
   DEV_SUPABASE_URL=https://xxx.supabase.co
   DEV_SUPABASE_DB_PASSWORD=your_database_password_here
   DEV_SUPABASE_KEY=your_anon_key_here
   ```

   **For Production (Option A - Direct DB URL):**
   ```bash
   ENV_STATE=prod
   PROD_SUPABASE_DB_URL=postgresql://postgres:your_password@xxx.supabase.co:5432/postgres
   PROD_SUPABASE_URL=https://xxx.supabase.co
   PROD_SUPABASE_KEY=your_service_role_key_here
   ```

   **For Production (Option B - Auto-construct):**
   ```bash
   ENV_STATE=prod
   PROD_SUPABASE_URL=https://xxx.supabase.co
   PROD_SUPABASE_DB_PASSWORD=your_database_password_here
   PROD_SUPABASE_KEY=your_service_role_key_here
   ```

   **Note:** If both `SUPABASE_DB_URL` and (`SUPABASE_URL` + `SUPABASE_DB_PASSWORD`) are provided, `SUPABASE_DB_URL` takes priority.

4. **Run Migrations**
   ```bash
   # The app will automatically detect Supabase and configure SSL
   alembic upgrade head
   ```

5. **Verify Connection**
   - Check application logs for: `Database configuration - Type: Supabase`
   - The app automatically configures SSL and optimized connection pooling for Supabase

**Note:** The application automatically:
- Detects Supabase connections (by checking for `supabase.co` in the URL)
- Configures SSL (`ssl=require`)
- Optimizes connection pooling (reduced pool size for Supabase limits)
- Converts connection strings for asyncpg (FastAPI) and psycopg2 (Alembic)

#### Email (Mailgun)
- `DEV_MAILGUN_API_KEY`: Mailgun API key
- `DEV_MAILGUN_DOMAIN`: Mailgun domain

#### Storage (Backblaze B2)
- `DEV_B2_KEY_ID`: B2 application key ID
- `DEV_DEV_B2_APPLICATION_KEY`: B2 application key
- `DEV_B2_BUCKET_NAME`: B2 bucket name

#### Logging
- `DEV_LOGTAIL_API_KEY`: Logtail API key (optional)

### Environment Prefixes

Configuration uses environment-specific prefixes:
- **Development**: `DEV_` prefix
- **Production**: `PROD_` prefix
- **Test**: `TEST_` prefix

Example: `DEV_JWT_SECRET_KEY`, `PROD_JWT_SECRET_KEY`, `TEST_JWT_SECRET_KEY`

## 📡 API Endpoints

### Authentication (`/users`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|----------------|
| POST | `/register` | Register a new user | No |
| POST | `/token` | Login and get access token | No |
| GET | `/users` | Get all users | No |
| GET | `/confirm/{token}` | Confirm email address | No |

### Posts (`/posts`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|----------------|
| POST | `/post` | Create a new post | Yes |
| GET | `/posts` | Get all posts (with sorting) | No |
| GET | `/posts/{post_id}` | Get post with comments and likes | No |
| POST | `/comment` | Create a comment on a post | Yes |
| GET | `/comments` | Get all comments | No |
| GET | `/posts/{post_id}/comments` | Get comments for a post | No |
| POST | `/like` | Like a post | Yes |

### File Management (`/bucket`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|----------------|
| POST | `/upload/` | Upload file to B2 storage | No |
| GET | `/files/` | List all uploaded files | No |

### Tasks (`/tasks`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|----------------|
| POST | `/send-email` | Send email via Mailgun | No |

### Root

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🗄 Database Models

### User
- `id`: Primary key
- `email`: Unique email address
- `password`: Hashed password (SHA256 + bcrypt)
- `confirmed`: Email confirmation status

### Post
- `id`: Primary key
- `body`: Post content
- `user_id`: Foreign key to User
- `image_url`: Optional image URL
- `comments`: Relationship to Comment (one-to-many)

### Comment
- `id`: Primary key
- `body`: Comment content
- `post_id`: Foreign key to Post
- `user_id`: Foreign key to User
- `post`: Relationship to Post (many-to-one)

### Like
- `id`: Primary key
- `post_id`: Foreign key to Post
- `user_id`: Foreign key to User

### Relationships

```
User (1) ──< (N) Post
User (1) ──< (N) Comment
User (1) ──< (N) Like
Post (1) ──< (N) Comment
Post (1) ──< (N) Like
```

All foreign keys use `CASCADE` delete for data integrity.

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest app/tests/ -v

# Run specific test file
pytest app/tests/routers/test_post.py -v

# Run with coverage
pytest --cov=app app/tests/

# Run with fixtures info
pytest --fixtures-per-test
```

### Test Structure

- **conftest.py**: Shared fixtures and test configuration
- **Test isolation**: Database cleaned before/after each test
- **Mocked services**: Email sending is mocked in tests
- **Async support**: Full async/await test support

### Test Fixtures

- `client`: Synchronous TestClient
- `async_client`: Async HTTP client
- `registered_user`: Creates a test user
- `confirmed_user`: Creates and confirms a test user
- `logged_in_token`: Returns JWT token for authenticated requests

## 🐳 Deployment

### Docker Compose

The project includes a `docker-compose.yml` with:

- **PostgreSQL**: Database service
- **pgAdmin**: Database administration UI
- **Backend**: FastAPI application
- **Alembic**: Migration runner

### Production Considerations

1. **Environment Variables**: Use `PROD_` prefixed variables
2. **Database**:
   - **Recommended**: Use Supabase for production (managed PostgreSQL with automatic backups)
   - **Alternative**: Use PostgreSQL in production (not SQLite)
   - Set `PROD_SUPABASE_DB_URL` or `PROD_DATABASE_URL` environment variable
3. **Security**:
   - Use strong JWT secrets and secure passwords
   - For Supabase: Use service role key only in secure server environments
   - Never commit production secrets to version control
4. **HTTPS**: Configure reverse proxy (nginx/traefik)
5. **Logging**: Configure Logtail or similar service
6. **Monitoring**: Set up health checks and monitoring
7. **Database Migrations**: Run Alembic migrations before deploying:
   ```bash
   ENV_STATE=prod alembic upgrade head
   ```

### Deploying on Render.com

When deploying on Render.com (or similar cloud platforms):

1. **Set Environment Variables in Render Dashboard:**
   ```bash
   ENV_STATE=dev  # or prod
   DATABASE_URL=<your-render-postgres-url>  # Render provides this automatically
   # OR use Supabase:
   DEV_SUPABASE_DB_URL=postgresql://postgres:password@xxx.supabase.co:5432/postgres
   ```

2. **Important Notes:**
   - Render.com provides `DATABASE_URL` automatically (unprefixed)
   - The app automatically detects and uses this
   - SSL is automatically configured for cloud PostgreSQL connections
   - Auto table creation is **disabled** on cloud platforms - use Alembic migrations instead

3. **Run Migrations:**
   - Add a build command: `alembic upgrade head`
   - Or run migrations manually after deployment

4. **Troubleshooting:**
   - If you see connection errors, ensure `DATABASE_URL` is set in Render dashboard
   - Check that SSL is enabled (automatically handled for cloud providers)
   - Verify database is accessible from Render's network

### Docker Command for Alembic

```bash
cd fastapi-mastering && docker run --rm --network fastapi-mastering_backend \
  -v "$(pwd):/app" -w /app \
  -e ENV_STATE=dev \
  -e DEV_POSTGRESQL_USERNAME=admin \
  -e DEV_POSTGRESQL_PASSWORD="Admin123!" \
  -e DEV_POSTGRESQL_SERVER=pg \
  -e DEV_POSTGRESQL_PORT=5432 \
  -e DEV_POSTGRESQL_DATABASE=quiz_db \
  python:3.12 bash -c "pip install -q -r requirements.txt && python -m alembic upgrade head"
```

## 💡 Key Insights

### Architecture Patterns

1. **Dependency Injection**: FastAPI's `Depends()` for clean dependency management
2. **Repository Pattern**: Separation between ORM models and Pydantic entities
3. **Environment-based Config**: Pydantic Settings with environment prefixes
4. **Lifespan Events**: Proper startup/shutdown handling with `@asynccontextmanager`

### Security Best Practices

1. **Password Hashing**: SHA256 pre-hash + bcrypt (bypasses 72-byte limit)
2. **JWT Tokens**: Separate access and confirmation tokens with expiration
3. **Email Confirmation**: Required before authentication
4. **CORS Configuration**: Environment-based CORS origins
5. **Email Obfuscation**: Privacy protection in logs

### Database Best Practices

1. **Async Operations**: Full async/await for database operations
2. **Session Management**: Automatic commit/rollback in dependency
3. **Migrations**: Alembic for version control
4. **Relationships**: Proper foreign keys with cascade deletes
5. **Connection Pooling**: SQLAlchemy connection pooling

### Logging Best Practices

1. **Structured Logging**: JSON format for machine parsing
2. **Correlation IDs**: Request tracking across services
3. **Multiple Handlers**: Console, file, and cloud logging
4. **Log Levels**: Environment-specific log levels
5. **Privacy**: Email obfuscation in logs

### Code Quality

1. **Type Hints**: Full type annotations throughout
2. **Pydantic Models**: Request/response validation
3. **Error Handling**: Proper HTTP exceptions with logging
4. **Documentation**: Docstrings and API documentation
5. **Testing**: Comprehensive test coverage

### Performance Optimizations

1. **Chunked File Uploads**: 1MB chunks for large files
2. **Background Tasks**: Async email sending
3. **Eager Loading**: `selectin` and `joined` loading strategies
4. **Connection Pooling**: Efficient database connections
5. **Caching**: LRU cache for B2 API and bucket instances

### Development Workflow

1. **Ruff**: Fast linting and formatting
2. **Alembic**: Database migration workflow
3. **Docker**: Containerized development environment
4. **Testing**: Automated test suite
5. **Hot Reload**: Uvicorn reload for development

## 📚 Additional Resources

### FastAPI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)

### SQLAlchemy
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

### Tools
- **Ruff**: [Ruff Documentation](https://docs.astral.sh/ruff/)
- **Pytest**: [Pytest Documentation](https://docs.pytest.org/)

### Services
- **Backblaze B2**: [B2 Documentation](https://www.backblaze.com/b2/docs/)
- **Mailgun**: [Mailgun Documentation](https://documentation.mailgun.com/)
- **Logtail**: [Logtail Documentation](https://betterstack.com/docs/logs/)

## 🔧 Development Tools

### Ruff (Linter & Formatter)

```bash
# Install
pip install ruff

# VS Code Extension
# https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff
```

### VS Code Settings

See the original README for recommended VS Code settings including:
- Python formatting with Ruff
- Tab size configuration
- Format on save
- Import organization

### Alembic Quick Reference

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "your message"

# Apply migrations
alembic upgrade head

# Check current version
alembic current

# Stamp database (mark as up-to-date without running)
alembic stamp head
```

### HTTP Status Codes

FastAPI exposes HTTP status code constants from Starlette:

```python
from fastapi import status

# Common status codes
status.HTTP_200_OK
status.HTTP_201_CREATED
status.HTTP_400_BAD_REQUEST
status.HTTP_401_UNAUTHORIZED
status.HTTP_404_NOT_FOUND
status.HTTP_500_INTERNAL_SERVER_ERROR
```

### OAuth2 Password Request Form

```python
from fastapi.security import OAuth2PasswordRequestForm

# Both are equivalent:
form: OAuth2PasswordRequestForm = Depends()
form: Annotated[OAuth2PasswordRequestForm, Depends()]

# Requires: application/x-www-form-urlencoded
# Fields: username, password, scope, client_id, client_secret
```

## 📖 Additional Notes & Reference

### GitHub Setup

```bash
# Create a new repository on the command line
echo "# fastapi-mastering" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/tien-le/fastapi-mastering.git
git push -u origin main
```

Or push an existing repository from the command line:
```bash
git remote add origin https://github.com/tien-le/fastapi-mastering.git
git branch -M main
git push -u origin main
```

### Running FastAPI

```bash
my-fastapi$ uvicorn app.main:app --reload
```

### Ruff Tool

#### Installation

Add to `requirements-dev.txt`:
```bash
ruff
```

#### VS Code Extension
https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff

#### VS Code User Settings

```json
{
    "terminal.integrated.fontSize": 16,
    "editor.fontSize": 16,
    "[typescript]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    },
    "[typescriptreact]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    },
    "[css]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    },
    "[json]": {
        "editor.tabSize": 2,
        "editor.insertSpaces": true
    },
    "[python]": {
        "editor.tabSize": 4,
        "editor.insertSpaces": true,
        "diffEditor.ignoreTrimWhitespace": false,
        "editor.defaultColorDecorators": "never",
        "gitlens.codeLens.symbolScopes": [
            "!Module"
        ],
        "editor.formatOnType": true,
        "editor.wordBasedSuggestions": "off",
        "editor.codeActionsOnSave": {
            "source.organizeImports": "explicit",
            "source.fixAll": "explicit"
        }
    },
    "editor.wordWrap": "on",
    "diffEditor.wordWrap": "on",
    "editor.guides.indentation": false,
    "editor.guides.bracketPairs": false,
    // Ctrl + Shift + P → Developer: Reload Window
    // Disable extension: Blockman
    "editor.stickyScroll.enabled": false,
    "editor.semanticHighlighting.enabled": false,
    "workbench.tree.enableStickyScroll": false,
    "editor.bracketPairColorization.enabled": false,
    "editor.stickyScroll.scrollWithEditor": false,
    "editor.renderWhitespace": "none",
    "editor.renderLineHighlight": "none",
    "open-in-browser.default": "firefox",
    "makefile.configureOnOpen": true,
    "editor.formatOnSave": true,
    "editor.defaultFormatter": "charliermarsh.ruff",
}
```

### Pytest Commands

```bash
pytest --fixtures-per-test
pytest --fixtures
pytest -v
pytest app/tests/ -v -q
```

### Alembic Detailed Guide

**Note**: alembic folder should be at the same level as the `app` folder.

#### Initialize Alembic

```bash
$ alembic init alembic
```

#### Update env.py

```python
from app.entities.models import Post, Comment
from app.core.config import settings

config = context.config  # existed line

# Set the DB URL
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))

from app.core.database import Base
target_metadata = Base.metadata
```

#### Create Tables - Generate the Migration

```bash
$ alembic revision --autogenerate -m "Create table Post, Comment"
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'posts'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_posts_id' on '('id',)'
INFO  [alembic.autogenerate.compare] Detected added table 'comments'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_comments_id' on '('id',)'
  Generating ...my_fastapi/alembic/versions/0b446e005cff_create_table_post_comment.py ...  done
```

#### Apply Migrations

```bash
$ alembic current
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.

$ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0b446e005cff, Create table Post, Comment
```

#### TL;DR Cheatsheet of Alembic

```bash
$ alembic init alembic
$ alembic revision --autogenerate -m "your message"
$ alembic upgrade head
```

#### Mark the Migration as Applied (Simpler)

```bash
# Mark the database as being up-to-date without actually running migrations.
# Use after the DB already exists
# stamp = mark only, not execute
$ alembic stamp head

$ alembic upgrade head

$ alembic current
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
1c5fb24a3a7c

$ alembic stamp head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running stamp_revision 1c5fb24a3a7c -> 2201620c5adc

$ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
```

#### After Adding ForeignKey into Tables ORM

```bash
# B1: Autogenerate the migration
# Alembic will inspect model metadata and emit a new migration file.
$ alembic revision --autogenerate -m "add user_id FK to comments/posts"

# B2: Fix the migration for SQLite (no ALTER CONSTRAINT support)
# Wrap table changes in op.batch_alter_table(..., recreate="always")
with op.batch_alter_table("comments", recreate="always") as batch:
    batch.add_column(sa.Column("user_id", sa.Integer(), nullable=False))
    batch.create_foreign_key("fk_comments_user_id_users", "users", ["user_id"], ["id"], ondelete="CASCADE")

# B3: Do the same for other affected tables (posts)

# B4: delete the local SQLite DB (e.g., rm local.db) to start clean.

# B5: Run the migration
$ alembic upgrade head

# B: Downgrade path
# Mirror the batch pattern in downgrade() so rollbacks also work on SQLite.

# B: Verify
# Inspect the schema (PRAGMA table_info(...) / PRAGMA foreign_key_list(...) in SQLite) to confirm the FK and indexes exist.

### Full flow: update models → autogenerate → adjust migration for SQLite batch mode → ensure data compatibility → alembic upgrade head → verify.
```

#### Another Solution

```bash
Quickest (if you can lose data):
    Delete the SQLite file and rerun:
        rm local.db (or whatever DB file you're using)
        alembic upgrade head

If you need to keep the DB contents:
    Drop the stray temp table, then rerun:
        sqlite3 local.db 'DROP TABLE IF EXISTS _alembic_tmp_comments;'
        alembic downgrade f6fa61e85818
        alembic upgrade head
```

### Logging Module

**Logger** --one or more--> **Handler** --one--> **Formatter**

- **Logger**: Schedules log information for output
- **Handler**: Sends the log information to a destination; Console handler / File handler
- **Formatter**: Defines how the log will be displayed; Display current time + log message

#### Logging Levels

- **CRITICAL**: Errors that cause application failure, such as a crucial database being unavailable
- **ERROR**: Handling errors that affect the application's operation, such as an HTTP 500 error, but allow the application to continue working
- **WARNING**: Requires attention
- **INFO**: informative messages, such as user authentication message
- **DEBUG**: debugging messages, provides extra information for developers during development or testing

#### Sample Code

```python
import logging

# Get logger and set level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler("file.log")

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(name)s:%(lineno)d %(message)s"
)

# Add formatter to handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Use the logger
logger.debug("debug message")
logger.info("info message")
logger.warning("warning")
logger.error("error message")
logger.critical("critical message")

# %(levelname)s:%(name)s:%(message)s
# Ex: DEBUG:myLogger:debug message
```

### Pytest Example Output

```bash
$ pytest app/tests/ -v -q
Cannot read termcap database;
using dumb terminal settings.
=============================================================================================== test session starts ===============================================================================================
platform linux -- Python 3.12.0, pytest-9.0.1, pluggy-1.6.0
rootdir: ...my_fastapi
configfile: pyproject.toml
plugins: asyncio-1.3.0, anyio-4.12.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 8 items

app/tests/routers/test_post.py ........
```

### LogTail Setup

https://betterstack.com/docs/logs/python/#logging-from-python

```bash
$ uv pip install logtail-python

# https://betterstack.com/docs/logs/collector/?collector=55052&source=1620699

export COLLECTOR_SECRET=LeyThJyDskkCUSpMQPHvaSbyZhtxu7qn

echo $COLLECTOR_SECRET

curl -sSL https://raw.githubusercontent.com/BetterStackHQ/collector/main/install.sh | \
  COLLECTOR_SECRET="$COLLECTOR_SECRET" bash

docker run --rm --privileged alpine:latest sh -c "apk add --no-cache bash wget -q && \
  wget -qO- https://telemetry.betterstack.com/api/collector/public/ebpf.sh | bash"
```

### HTTP Status Codes

FastAPI exposes **HTTP status code constants** from **Starlette**, all defined in `starlette.status`.

```python
from starlette.status import *

# or

from fastapi import status
```

#### Complete List of HTTP Status Code Constants

**Informational (1xx)**
```python
HTTP_100_CONTINUE
HTTP_101_SWITCHING_PROTOCOLS
HTTP_102_PROCESSING
HTTP_103_EARLY_HINTS
```

**Success (2xx)**
```python
HTTP_200_OK
HTTP_201_CREATED
HTTP_202_ACCEPTED
HTTP_203_NON_AUTHORITATIVE_INFORMATION
HTTP_204_NO_CONTENT
HTTP_205_RESET_CONTENT
HTTP_206_PARTIAL_CONTENT
HTTP_207_MULTI_STATUS
HTTP_208_ALREADY_REPORTED
HTTP_226_IM_USED
```

**Redirection (3xx)**
```python
HTTP_300_MULTIPLE_CHOICES
HTTP_301_MOVED_PERMANENTLY
HTTP_302_FOUND
HTTP_303_SEE_OTHER
HTTP_304_NOT_MODIFIED
HTTP_305_USE_PROXY
HTTP_306_RESERVED
HTTP_307_TEMPORARY_REDIRECT
HTTP_308_PERMANENT_REDIRECT
```

**Client Error (4xx)**
```python
HTTP_400_BAD_REQUEST
HTTP_401_UNAUTHORIZED
HTTP_402_PAYMENT_REQUIRED
HTTP_403_FORBIDDEN
HTTP_404_NOT_FOUND
HTTP_405_METHOD_NOT_ALLOWED
HTTP_406_NOT_ACCEPTABLE
HTTP_407_PROXY_AUTHENTICATION_REQUIRED
HTTP_408_REQUEST_TIMEOUT
HTTP_409_CONFLICT
HTTP_410_GONE
HTTP_411_LENGTH_REQUIRED
HTTP_412_PRECONDITION_FAILED
HTTP_413_REQUEST_ENTITY_TOO_LARGE
HTTP_414_REQUEST_URI_TOO_LONG
HTTP_415_UNSUPPORTED_MEDIA_TYPE
HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
HTTP_417_EXPECTATION_FAILED
HTTP_418_IM_A_TEAPOT
HTTP_421_MISDIRECTED_REQUEST
HTTP_422_UNPROCESSABLE_ENTITY --> HTTP_422_UNPROCESSABLE_CONTENT
HTTP_423_LOCKED
HTTP_424_FAILED_DEPENDENCY
HTTP_425_TOO_EARLY
HTTP_426_UPGRADE_REQUIRED
HTTP_428_PRECONDITION_REQUIRED
HTTP_429_TOO_MANY_REQUESTS
HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE
HTTP_451_UNAVAILABLE_FOR_LEGAL_REASONS
```

**Server Error (5xx)**
```python
HTTP_500_INTERNAL_SERVER_ERROR
HTTP_501_NOT_IMPLEMENTED
HTTP_502_BAD_GATEWAY
HTTP_503_SERVICE_UNAVAILABLE
HTTP_504_GATEWAY_TIMEOUT
HTTP_505_HTTP_VERSION_NOT_SUPPORTED
HTTP_506_VARIANT_ALSO_NEGOTIATES
HTTP_507_INSUFFICIENT_STORAGE
HTTP_508_LOOP_DETECTED
HTTP_510_NOT_EXTENDED
HTTP_511_NETWORK_AUTHENTICATION_REQUIRED
```

#### Quick Example

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

@app.get("/item/{id}")
def get_item(id: int):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Item not found"
    )
```

### OAuth2PasswordRequestForm

```python
from fastapi.security import OAuth2PasswordRequestForm

form: OAuth2PasswordRequestForm = Depends()
vs
form: Annotated[OAuth2PasswordRequestForm, Depends()]
```

Both mean:
- "Inject an instance of OAuth2PasswordRequestForm using Depends()"
- The request must be `application/x-www-form-urlencoded`
- FastAPI will parse fields: `username`, `password`, `scope`, `client_id`, `client_secret`

#### grant_type -- Why might a token endpoint not work properly in an OAuth2 implementation?

In OAuth2, the token endpoint requires the `grant_type` to know which flow you're using (password, authorization_code, client_credentials, refresh_token, etc.).
If it's missing or incorrect, the token endpoint will typically fail or return an `invalid_request` error.

**Why it matters**

The `grant_type` tells the authorization server which OAuth2 flow is being used.
If it's missing, the server won't know how to process the request and the token endpoint will fail.

### Docker Command - Test Alembic

```bash
cd fastapi-mastering && docker run --rm --network fastapi-mastering_backend -v "$(pwd):/app" -w /app -e ENV_STATE=dev -e DEV_POSTGRESQL_USERNAME=admin -e DEV_POSTGRESQL_PASSWORD="Admin123!" -e DEV_POSTGRESQL_SERVER=pg -e DEV_POSTGRESQL_PORT=5432 -e DEV_POSTGRESQL_DATABASE=quiz_db python:3.12 bash -c "pip install -q -r requirements.txt && python -m alembic upgrade head" 2>&1
```

### MailGun Setup

https://documentation.mailgun.com/docs/mailgun/quickstart

#### Add Authorized Recipient

```bash
curl -X POST \
  "https://api.mailgun.net/v5/sandbox/auth_recipients?email=your-email@example.com" \
  --user 'api:YOUR_API_KEY'
```

#### Send Your First Email

```bash
curl --user 'api:f14d458ed13199343b7b4b825538e002-04af4ed8-xxx' \
  https://api.mailgun.net/v3/xxx.mailgun.org/messages \
  -F from='Test <postmaster@xxx.mailgun.org>' \
  -F to='my-email.dev@gmail.com' \
  -F subject='Hello!' \
  -F text='Test message'
```

## 📝 License

This project is part of a learning exercise and demonstration of FastAPI best practices.

## 🤝 Contributing

This is a learning project. Feel free to fork and adapt for your own use.

---

**Built with ❤️ using FastAPI, SQLAlchemy 2.0, and modern Python practices**
