# Deployment Guide - Simple Hospital Information System

## Quick Start (Development)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create initial admin user
python initial_admin.py

# 3. Run the application
python main.py
# OR
uvicorn main:app --reload

# 4. Access the system
# Open browser: http://localhost:8000
# Login with admin credentials
```

## Production Deployment

### Option 1: Using Uvicorn with Systemd (Recommended for Linux)

1. **Create a systemd service file:**

```bash
sudo nano /etc/systemd/system/hospital-his.service
```

Add the following content:

```ini
[Unit]
Description=Hospital Information System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/SimpleHIS
Environment="PATH=/var/www/SimpleHIS/venv/bin"
ExecStart=/var/www/SimpleHIS/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

[Install]
WantedBy=multi-user.target
```

2. **Enable and start the service:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable hospital-his
sudo systemctl start hospital-his
sudo systemctl status hospital-his
```

### Option 2: Using Gunicorn with Uvicorn Workers

1. **Install Gunicorn:**

```bash
pip install gunicorn
```

2. **Run with Gunicorn:**

```bash
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Option 3: Using Docker

1. **Create Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create initial admin user
RUN echo -e "admin\nمدیر سیستم\nadmin123" | python initial_admin.py

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. **Build and run:**

```bash
docker build -t hospital-his .
docker run -d -p 8000:8000 -v $(pwd)/hospital.db:/app/hospital.db hospital-his
```

### Option 4: Using Docker Compose

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./hospital.db:/app/hospital.db
      - ./uploads:/app/uploads
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

## Nginx Reverse Proxy Configuration

For production, use Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-hospital-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/SimpleHIS/static;
        expires 30d;
    }

    location /uploads {
        alias /var/www/SimpleHIS/uploads;
        internal;  # Only accessible via application
    }
}
```

## SSL/HTTPS Configuration (Let's Encrypt)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-hospital-domain.com

# Auto-renewal is configured automatically
```

## Security Checklist for Production

### 1. Change Secret Key

Edit `auth.py` and change the `SECRET_KEY`:

```python
SECRET_KEY = "your-very-secret-random-key-here-generate-with-openssl"
```

Generate a secure key:

```bash
openssl rand -hex 32
```

### 2. Environment Variables

Create a `.env` file:

```bash
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./hospital.db
ALLOWED_HOSTS=your-domain.com
```

Update code to use environment variables:

```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")
```

### 3. Secure Database

```bash
# Set proper permissions
chmod 600 hospital.db

# Regular backups
0 2 * * * /usr/bin/sqlite3 /var/www/SimpleHIS/hospital.db ".backup '/backup/hospital-$(date +\%Y\%m\%d).db'"
```

### 4. Firewall Configuration

```bash
# Allow only HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5. File Upload Security

- Already implemented: Secure file naming with UUID
- Set upload size limit in Nginx (already configured above)
- Validate file types on upload

## Performance Optimization

### 1. Database Indexing

Already implemented in models:
- Patient national_id indexed
- User username indexed

### 2. Static File Caching

Configure Nginx to cache static files (already in config above)

### 3. Application Caching

Consider adding Redis for session storage in high-traffic scenarios

### 4. Multiple Workers

Use multiple workers for better performance:

```bash
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Monitoring and Logging

### 1. Application Logs

```bash
# Create log directory
mkdir -p /var/log/hospital-his

# Run with logging
uvicorn main:app --log-level info --access-log --log-config logging.conf
```

### 2. System Monitoring

Install monitoring tools:

```bash
sudo apt install htop iotop netstat
```

### 3. Application Monitoring

Consider using:
- Sentry for error tracking
- Prometheus + Grafana for metrics
- ELK stack for log aggregation

## Backup Strategy

### 1. Database Backup

**Daily automated backup script:**

```bash
#!/bin/bash
BACKUP_DIR="/backup/database"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 /var/www/SimpleHIS/hospital.db ".backup '$BACKUP_DIR/hospital_$DATE.db'"

# Keep only last 30 days
find $BACKUP_DIR -name "hospital_*.db" -mtime +30 -delete
```

### 2. File Upload Backup

```bash
# Backup uploads directory
rsync -av /var/www/SimpleHIS/uploads/ /backup/uploads/
```

### 3. Configuration Backup

```bash
# Backup entire application directory
tar -czf /backup/app/hospital-his_$(date +%Y%m%d).tar.gz /var/www/SimpleHIS
```

## Updating the Application

```bash
# 1. Backup database
cp hospital.db hospital.db.backup

# 2. Pull latest code
git pull

# 3. Install new dependencies
pip install -r requirements.txt

# 4. Restart service
sudo systemctl restart hospital-his
```

## Troubleshooting

### Database Locked Error

```bash
# Check for other connections
lsof hospital.db

# Restart application
sudo systemctl restart hospital-his
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R www-data:www-data /var/www/SimpleHIS
sudo chmod -R 755 /var/www/SimpleHIS
sudo chmod 600 /var/www/SimpleHIS/hospital.db
```

## Scaling Considerations

### For High Traffic:

1. **Database**: Migrate to PostgreSQL
2. **Caching**: Add Redis for session management
3. **Load Balancing**: Use multiple application servers behind a load balancer
4. **CDN**: Serve static files from a CDN
5. **Separate File Storage**: Use object storage (S3, MinIO) for uploads

## Support and Maintenance

### Regular Maintenance Tasks:

1. **Weekly**: Check logs for errors
2. **Monthly**: Review user accounts and permissions
3. **Quarterly**: Update dependencies and security patches
4. **Yearly**: Review and update secret keys

### Health Check Endpoint

Add to `routers/common.py`:

```python
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

Monitor with:

```bash
curl http://localhost:8000/health
```

## Conclusion

The Hospital Information System is production-ready and can be deployed using any of the methods above. For most use cases, the systemd service with Nginx reverse proxy is recommended.

For any issues or questions, refer to the main README.md or create an issue in the repository.
