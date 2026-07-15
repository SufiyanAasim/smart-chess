FROM python:3.11-slim

# Install system dependencies, X11/Tkinter libraries, Stockfish engine, and audio libraries
RUN apt-get update && apt-get install -y \
    libx11-6 \
    libxext-6 \
    libxrender-dev \
    libxft2 \
    libtk8.6 \
    x11-apps \
    stockfish \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and resources
COPY src/ ./src/
COPY main.py .

# Create writable data directories for SQLite database and PGN exports
RUN mkdir -p /app/data /app/data/pgn && chmod -R 777 /app/data

CMD ["python", "main.py"]
