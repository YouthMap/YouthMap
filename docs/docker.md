# Running with Docker

As an alternative to installing Python and dependencies directly on the host, you can run Youth Map inside a Docker
container. This page explains the steps. It assumes Docker is already installed on your server.

### Check out the repository

You will still need to check out the code itself, as in the main sysadmin documentation.

```bash
git clone git@github.com:YouthMap/YouthMap.git youthmap
cd youthmap
git checkout ##tagname##
```

### Build the image

Create the following `Dockerfile` in the root of the repository:

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "youthmap.py"]
```

From the root of the Youth Map repository, build a Docker image:

```bash
docker build -t youthmap .
```

### Create a persistent data volume

The `data/` directory holds the SQLite database and any uploaded files. To ensure this survives container restarts and
image updates, create a named Docker volume for it:

```bash
docker volume create youthmap-data
```

### Run the container

Run the Docker container, mounting the persistent data partition and forwarding port 8080 through to the container.

Replace the string `##your-secret-here##` to a long random string (e.g. the output of `openssl rand -hex 32`).

```bash
docker run -d \
  --name youthmap \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v youthmap-data:/app/data \
  -e COOKIE_SECRET=##your-secret-here## \
  youthmap
```

### Updating the container

To deploy a new version, rebuild the image and recreate the container. The data volume is unaffected, and will still contain your uploaded icons and database:

```bash
docker build -t youthmap .
docker stop youthmap && docker rm youthmap
docker run -d \
  --name youthmap \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  -v youthmap-data:/app/data \
  -e COOKIE_SECRET=##your-secret-here## \
  youthmap
```

### Docker Compose

You can use `docker compose` to avoid having to supply the runtime arguments every time. To do this, create a file called `docker-compose.yml` in the root of the repository with the following contents, replacing `##your-secret-here##` as above.

```yaml
services:
  youthmap:
    build: .
    restart: unless-stopped
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - youthmap-data:/app/data
    environment:
      - COOKIE_SECRET=##your-secret-here##

volumes:
  youthmap-data:
```

To build the image and start the container:

```bash
docker compose up -d
```

To deploy an updated version, pull or check out the new code and then run:

```bash
docker compose up -d --build
```

This rebuilds the image and recreates the container if anything has changed.