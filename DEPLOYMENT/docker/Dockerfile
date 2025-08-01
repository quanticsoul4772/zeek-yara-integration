# Zeek-YARA Integration Educational Platform
# Multi-stage Docker build for educational environment

# Base stage with system dependencies
FROM python:3.9-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build tools
    build-essential \
    git \
    curl \
    # Security tools
    yara \
    # Network tools
    tcpdump \
    wget \
    # Development tools
    vim \
    nano \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Install Zeek from source (latest stable)
RUN apt-get update && apt-get install -y \
    cmake \
    make \
    gcc \
    g++ \
    flex \
    bison \
    libpcap-dev \
    libssl-dev \
    python3-dev \
    swig \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Download and build Zeek
RUN cd /tmp && \
    wget https://download.zeek.org/zeek-5.0.0.tar.gz && \
    tar -xzf zeek-5.0.0.tar.gz && \
    cd zeek-5.0.0 && \
    ./configure --prefix=/opt/zeek && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/zeek-5.0.0*

# Add Zeek to PATH
ENV PATH="/opt/zeek/bin:${PATH}"

# Install Suricata
RUN apt-get update && apt-get install -y \
    suricata \
    && rm -rf /var/lib/apt/lists/*

# Development stage
FROM base as development

# Install development tools
RUN apt-get update && apt-get install -y \
    # Development dependencies
    python3-pip \
    python3-venv \
    # Debugging tools
    gdb \
    strace \
    # Documentation tools
    pandoc \
    # Testing tools
    valgrind \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt test-requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r test-requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p \
    DATA/runtime/logs \
    DATA/runtime/extracted-files \
    DATA/runtime/alerts \
    DATA/runtime/correlation \
    DATA/persistent/databases \
    DATA/persistent/configurations \
    DATA/persistent/cache \
    DATA/samples/benign \
    DATA/samples/simulated \
    DATA/samples/pcaps \
    DATA/samples/scenarios

# Set up permissions
RUN chmod +x TOOLS/cli/zyi && \
    chmod +x TOOLS/scripts/setup/*.sh && \
    chmod +x TOOLS/scripts/testing/*.sh

# Expose ports
EXPOSE 8000 8080

# Educational stage
FROM base as education

# Install only runtime dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    click \
    pydantic \
    sqlalchemy \
    yara-python \
    requests

# Set working directory
WORKDIR /app

# Copy only necessary files for educational use
COPY PLATFORM/ ./PLATFORM/
COPY TOOLS/cli/ ./TOOLS/cli/
COPY EDUCATION/ ./EDUCATION/
COPY CONFIGURATION/defaults/ ./CONFIGURATION/defaults/
COPY RULES/ ./RULES/
COPY requirements.txt ./

# Create educational user
RUN useradd -m -s /bin/bash student && \
    chown -R student:student /app

# Create necessary directories
RUN mkdir -p \
    DATA/runtime/logs \
    DATA/runtime/extracted-files \
    DATA/runtime/alerts \
    DATA/samples/benign \
    && chown -R student:student DATA/

# Set up permissions
RUN chmod +x TOOLS/cli/zyi

# Switch to student user for educational safety
USER student

# Set environment variables for educational mode
ENV ZYI_ENV=education \
    ZYI_SAFE_MODE=true \
    ZYI_DEMO_MODE=true

# Default command for educational environment
CMD ["./TOOLS/cli/zyi", "info"]

# Production stage
FROM base as production

# Install only production dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    gunicorn \
    click \
    pydantic \
    sqlalchemy \
    psycopg2-binary \
    redis \
    yara-python \
    requests

# Set working directory
WORKDIR /app

# Copy production files
COPY PLATFORM/ ./PLATFORM/
COPY TOOLS/cli/ ./TOOLS/cli/
COPY CONFIGURATION/defaults/production.json ./CONFIGURATION/defaults/
COPY RULES/yara/production/ ./RULES/yara/production/
COPY RULES/suricata/production/ ./RULES/suricata/production/
COPY requirements.txt ./

# Create production user
RUN useradd -m -s /bin/bash -u 1000 zyi && \
    chown -R zyi:zyi /app

# Create production directories
RUN mkdir -p \
    DATA/runtime/logs \
    DATA/runtime/extracted-files \
    DATA/runtime/alerts \
    DATA/runtime/correlation \
    DATA/persistent/databases \
    && chown -R zyi:zyi DATA/

# Set up permissions
RUN chmod +x TOOLS/cli/zyi

# Switch to production user
USER zyi

# Set environment variables for production
ENV ZYI_ENV=production \
    ZYI_SAFE_MODE=false \
    ZYI_DEMO_MODE=false \
    WORKERS=4

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["./TOOLS/cli/zyi", "api", "start", "--host", "0.0.0.0", "--port", "8000"]