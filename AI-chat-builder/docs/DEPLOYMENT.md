# Deployment Guide

## Production Deployment

### Prerequisites

- VPS or cloud server (AWS, DigitalOcean, etc.)
- Domain name
- SSL certificate (Let's Encrypt recommended)
- Docker and Docker Compose installed

### Step 1: Server Setup

1. **Update system**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

3. **Install Docker Compose**
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Step 2: Application Setup

1. **Clone repository**
```bash
git clone <your-repo-url>
cd ChatBuilder
```

2. **Configure environment**
```bash
cp .env.example .env
nano .env
```

Set production values:
- Strong `SECRET_KEY` (generate with `openssl rand -hex 32`)
- Strong `ENCRYPTION_KEY` (generate with Python Fernet)
- Production database credentials
- Your domain in `ALLOWED_ORIGINS`

3. **Update docker-compose for production**

Edit `docker-compose.yml`:
- Remove `--reload` from backend command
- Set proper resource limits
- Configure restart policies

### Step 3: SSL/TLS Setup

1. **Install Certbot**
```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. **Get SSL certificate**
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

3. **Configure Nginx**

Create `/etc/nginx/sites-available/chatbuilder`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/chatbuilder /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: Deploy Application

1. **Build and start services**
```bash
docker-compose up -d --build
```

2. **Run database migrations**
```bash
docker-compose exec backend alembic upgrade head
```

3. **Verify deployment**
```bash
docker-compose ps
docker-compose logs -f
```

### Step 5: Monitoring & Maintenance

1. **Set up log rotation**
```bash
docker-compose logs --tail=1000 -f > /var/log/chatbuilder.log
```

2. **Configure backups**

Create backup script `/usr/local/bin/backup-chatbuilder.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/backups/chatbuilder"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T postgres pg_dump -U chatbuilder chatbuilder > "$BACKUP_DIR/db_$DATE.sql"

# Backup uploads
tar -czf "$BACKUP_DIR/uploads_$DATE.tar.gz" ./uploads

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-chatbuilder.sh
```

3. **Monitor resources**
```bash
docker stats
```

## Scaling Strategies

### Horizontal Scaling

1. **Load Balancer Setup**
- Use Nginx or HAProxy
- Distribute traffic across multiple backend instances

2. **Database Scaling**
- Use managed PostgreSQL (AWS RDS, DigitalOcean Managed DB)
- Configure read replicas for analytics queries

3. **Redis Cluster**
- Set up Redis Sentinel for high availability
- Use Redis Cluster for distributed caching

### Vertical Scaling

1. **Increase container resources**

Edit `docker-compose.yml`:
```yaml
backend:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 4G
      reservations:
        cpus: '1'
        memory: 2G
```

2. **Optimize database**
- Increase shared_buffers
- Configure connection pooling
- Add appropriate indexes

## CI/CD Pipeline

### GitHub Actions Example

`.github/workflows/deploy.yml`:
```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /path/to/ChatBuilder
            git pull
            docker-compose up -d --build
            docker-compose exec backend alembic upgrade head
```

## Security Checklist

- [ ] Change default passwords
- [ ] Use strong SECRET_KEY and ENCRYPTION_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall (UFW)
- [ ] Set up fail2ban
- [ ] Regular security updates
- [ ] Database backups automated
- [ ] Monitor logs for suspicious activity
- [ ] Rate limiting configured
- [ ] CORS properly configured

## Troubleshooting

### Service won't start
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Database connection issues
```bash
docker-compose exec postgres psql -U chatbuilder -d chatbuilder
```

### Clear and rebuild
```bash
docker-compose down -v
docker-compose up -d --build
```
