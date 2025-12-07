# Add your FastAPI backend container
#FROM python:3.12
#WORKDIR /app
#COPY . .
#RUN pip install -r requirements.txt
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# Dockerfile for Alembic (or backend)
FROM python:3.12

# Create a non-root user
RUN useradd -ms /bin/bash alembicuser

# Set working directory
WORKDIR /app

# Copy project files and give ownership to the new user
COPY --chown=alembicuser:alembicuser . /app

# Switch to the new user
USER alembicuser



