FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libx11-6 \
    libxext-6 \
    libxrender-dev \
    libxft2 \
    libtk8.6 \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and resources
COPY src/ ./src/
COPY main.py .

CMD ["python", "main.py"]
