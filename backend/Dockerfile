FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copy source code
COPY . .

# Create directory for static cards
RUN mkdir -p static/cards

# Expose port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
