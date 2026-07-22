# ============================================================
# Dockerfile
# Builds the Docker image for the Banking App.
#
# Docker packages the app and all its dependencies into a
# portable container that runs the same everywhere.
#
# Build:  docker build -t banking-app .
# Run:    docker run -p 5000:5000 banking-app
# ============================================================

# Use the official slim Python 3.11 image as the base.
# "slim" means it's a smaller image without unnecessary tools.
FROM python:3.11-slim

# Set the working directory inside the container.
# All subsequent commands run from this directory.
WORKDIR /app

# ── Create a non-root user for security ──
# Running as root inside a container is a security risk.
# We create a dedicated user "appuser" to run the application.
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# ── Install dependencies ──
# Copy requirements.txt first (before the rest of the code).
# Docker caches this layer — if requirements don't change,
# it won't re-install packages on every build (faster builds).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy application code ──
COPY . .

# Give the non-root user ownership of the app directory
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Expose port 5000 so Docker knows the app listens on this port
EXPOSE 5000

# ── Start the app with Gunicorn ──
# Gunicorn is a production-grade WSGI server (better than Flask's built-in server).
# "app:app" means: from app.py, use the variable named `app`.
# --workers 2 : run 2 worker processes to handle concurrent requests
# --bind 0.0.0.0:5000 : listen on all network interfaces on port 5000
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "app:app"]
