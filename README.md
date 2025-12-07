# github

…or create a new repository on the command line

```bash
echo "# fastapi-mastering" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/tien-le/fastapi-mastering.git
git push -u origin main
```

…or push an existing repository from the command line
```bash
git remote add origin https://github.com/tien-le/fastapi-mastering.git
git branch -M main
git push -u origin main
```


# Run fastapi
```bash
my-fastapi$ uvicorn main:app --reload
```

# Tool ruff

## requirements-dev.txt
```bash
ruff
```

## Extension VS Code
https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff

## VS Code - User Settings
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

# pytest
```bash
pytest --fixtures-per-test
pytest --fixtures
pytest -v
```

# alembic
Note: alembic folder is the same level of app

## init alembic
```bash
$ alembic init alembic
```

## update env.py
```python
from app.models.models import Post, Comment
from app.core.config_loader import settings

config = context.config  # existed line

# Set the DB URL
config.set_main_option("sqlalchemy.url", str(settings.SQLALCHEMY_DATABASE_URI))

from app.core.database import Base
target_metadata = Base.metadata
```

## Create tables - Generate the migration
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

## Apply
```bash
$ alembic current
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.

$ alembic upgrade head
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 0b446e005cff, Create table Post, Comment


$ alembic upgrade head
```

# Note: TL;DR Cheatsheet of alembic
```bash
$ alembic init alembic
$ alembic revision --autogenerate -m "your message"
$ alembic upgrade head
```

## Mark the migration as applied (simpler)
```bash
# mark the database as being up-to-date without actually running migrations.
# after the DB already exists
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

# Logging module

Logger --one or more--> Handler --one--> Formatter

+ Logger: Schedules log information for output
+ Handler: Sends the log information to a destination; Console handler / File handler
+ Formatter: Defines how the log will be displayed; Display current time + log message

## Logging levels
+ CRITICAL: Errors that cause application failure, such as a crucial database being unavailable
+ ERROR: Handling errors that affect the application's operation, such as an HTTP 500 error, but allow the application to continue working
+ WARNING: Requires attention
+ INFO: informative messages, such as user authentication message
+ DEBUG: debugging messages, provides extra information for developers during development or testing

## Sample code
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

# pytest
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