FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install docker CLI so we can spawn/remove containers via the mounted socket
RUN apt-get update && apt-get install -y \
      curl apt-transport-https ca-certificates gnupg lsb-release \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
         | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
         https://download.docker.com/linux/debian $(lsb_release -cs) stable" \
         | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y docker-ce-cli \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our load-balancer code + consistent hash implementation
COPY app.py .
COPY consistent_hash.py .

EXPOSE 5000
CMD ["python", "app.py"]
