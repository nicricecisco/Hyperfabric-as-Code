# Base image: browser-based VS Code
FROM codercom/code-server:latest

# Install Python and pip 
USER root
RUN apt-get update && apt-get install -y \
    python3 python3-venv python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Create a Python virtual environment and upgrade pip
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip

# Add virtual environment to PATH so python and pip default to it
ENV PATH="/opt/venv/bin:$PATH"

# Copy runtime files into /tmp for later copying into /workspace
COPY requirements.txt /tmp/
COPY extensions.txt /tmp/
COPY settings.json /tmp/settings.json
COPY clonerepo.sh /clonerepo.sh

# Make sure clone script is executable
RUN chmod +x /clonerepo.sh

# Install Python dependencies from /tmp (not yet in /workspace)
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt

# Install VS Code extensions from /tmp
RUN while read extension; do \
      code-server --install-extension "$extension"; \
    done < /tmp/extensions.txt

# Create .env file template in /tmp (will be copied to workspace at runtime)
RUN echo '#Put your API key for Hyperfabric inside the quotations below\n' >> /tmp/.env
RUN echo 'HYPERFABRIC_TOKEN=""' >> /tmp/.env

# Change permissions so non-root user can write to everything
RUN chown -R coder:coder /workspace /clonerepo.sh /tmp

# Switch to non-root user (security best practice)
USER coder

# Expose code-server port
EXPOSE 8080

# Set entrypoint to cloning script
ENTRYPOINT ["/clonerepo.sh"]

# Default command starts code-server
CMD ["code-server", "--bind-addr", "0.0.0.0:8080", "--auth", "none", "/workspace"]
