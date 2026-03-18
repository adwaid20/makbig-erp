# Start from Python base image
FROM python:3.14

# Set working directory inside container
WORKDIR /app

# Copy requirements first (for faster builds)
COPY requirements.txt .

# Install all dependencies
RUN pip install -r requirements.txt

# Copy your entire project
COPY . .