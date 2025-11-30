FROM kalilinux/kali-rolling:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    nmap \
    ufw \
    systemd \
    sudo \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -s /bin/bash autoshield && \
    echo "autoshield ALL=(ALL) NOPASSWD: /usr/sbin/ufw, /usr/bin/systemctl" >> /etc/sudoers

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R autoshield:autoshield /app

# Switch to non-root user
USER autoshield

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the server
CMD ["python3", "server.py"]
