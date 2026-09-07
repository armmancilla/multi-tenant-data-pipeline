FROM python:3.13-slim

# Setting environment variables for determinism
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/src

# App directory
WORKDIR /src

# Installing Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copying application code inside the directory
COPY ./src ./src
COPY ./scripts ./scripts
COPY ./migrations ./migrations

# Creating a non-root user for security
RUN addgroup --gid 10001 pipeuser && \
    adduser --disabled-password --gecos "" --uid 10001 --gid 10001 pipeuser \
    && chown -R pipeuser /src
USER 10001