FROM python:3.13-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy pyproject.toml and other config files
COPY pyproject.toml uv.lock* ./

# Install dependencies using uv with --system flag
RUN uv pip install --system -e .

# Copy the project files
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]