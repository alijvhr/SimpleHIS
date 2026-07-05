# Docker Setup for Hospital Information System

This directory contains Docker configuration files to run the HIS application in a container.

## Files

- `Dockerfile` - Docker image definition
- `docker-compose.yml` - Docker Compose configuration for easy deployment
- `.dockerignore` - Files to exclude from Docker build context

## Running the Application

### Using Docker Compose (Recommended)

1. Make sure Docker and Docker Compose are installed
2. From the HIS project root directory, run:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

3. The application will be available at http://localhost:8000

### Using Docker directly

1. Build the image:
   ```bash
   docker build -f docker/Dockerfile -t his-app .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/hospital.db:/app/hospital.db -v $(pwd)/uploads:/app/uploads his-app
   ```

## Database and Uploads

- The SQLite database (`hospital.db`) is persisted using Docker volumes
- Uploaded files are stored in the `uploads` directory and also persisted

## Initial Admin User

After the first run, you'll need to create the initial admin user. You can do this by:

1. Running the container with interactive mode:
   ```bash
   docker run -it -v $(pwd)/hospital.db:/app/hospital.db his-app python initial_admin.py
   ```

2. Or connect to the running container and run the script inside.

## Notes

- The application runs on port 8000 inside the container
- Database is initialized automatically on startup
- Static files and templates are included in the image
