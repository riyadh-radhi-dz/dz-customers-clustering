FROM python:3.13-slim

# Install system deps for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONUNBUFFERED=1

# Metadata
LABEL name="dz-clustering"
LABEL description="DZ Customers Clustering API"
LABEL version="0.1.0"

# Install uv
RUN pip install uv

# Copy pyproject.toml and other config files
COPY pyproject.toml uv.lock* ./
COPY requirements.txt /app/requirements.txt

# Install dependencies using uv with --system flag
RUN uv pip install --system -e .
RUN uv pip install --system -r requirements.txt

# Copy the project files
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI application
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Use environment variable to control worker count
ENV WORKERS=1
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers $WORKERS --loop auto"]
