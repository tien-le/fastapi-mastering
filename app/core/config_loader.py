# import os
# from pathlib import Path

from app.core.config import get_settings

# Find the .env file by going up to the backend directory
# backend_dir = Path(__file__).resolve().parent.parent.parent
# print(f"backend_dir: {backend_dir}")
# env_file = os.path.join(backend_dir, ".env")
# settings = Settings(_env_file=env_file)

settings = get_settings()
