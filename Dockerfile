# Multi-stage build for optimized image size
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching - this layer changes only when requirements change
COPY requirements.txt .

# Install Python dependencies with pip cache
RUN pip install --user --upgrade pip setuptools wheel && \
    pip install --user --no-warn-script-location -r requirements.txt

# Final stage - optimized for faster startup
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install runtime dependencies (cached layer)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python dependencies from builder (cached if requirements unchanged)
COPY --from=builder /root/.local /root/.local

# Make sure the PATH includes local Python packages
ENV PATH=/root/.local/bin:$PATH

# Create directory for SQLite database (fallback)
RUN mkdir -p app/db

# Copy startup and migration scripts (changes less frequently than app code)
COPY start.sh migration_manager.sh ./
RUN chmod +x start.sh migration_manager.sh

# Copy alembic config and migrations (changes less frequently)
COPY alembic.ini .
COPY alembic/ ./alembic/

# Copy application code last (most frequently changed)
COPY app/ ./app/

# Expose port
EXPOSE 8000

# Optimized health check with faster endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application via start script
CMD ["./start.sh"]
