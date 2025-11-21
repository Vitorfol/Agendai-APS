
FROM python:3.12-slim

# Do not create .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required to build some Python packages
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   build-essential \
	   gcc \
	   libssl-dev \
	   libffi-dev \
	   ca-certificates \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install first to leverage Docker layer cache
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip \
	&& pip install --no-cache-dir -r /app/requirements.txt

# Copy project
COPY . /app

# Use a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser \
	&& chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Default command; expects the FastAPI app to be at src.main:app
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
