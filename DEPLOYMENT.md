# SVA-Chatbot Deployment Guide

This guide provides comprehensive instructions for deploying the SVA-Chatbot system in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Production Deployment](#production-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

### Required Software

- **Docker** (20.10+) and **Docker Compose** (2.0+)
- **Node.js** (18+) for frontend development
- **Python** (3.11+) for backend development
- **MongoDB** (7.0+) or MongoDB Atlas account

### Required Accounts

- **Groq API** account with API key
- **MongoDB Atlas** account (for production)
- **Domain name** (for production deployment)
- **SSL certificate** (for HTTPS)

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/sva-chatbot.git
cd sva-chatbot
```

### 2. Configure Environment

**Backend:**

```bash
cd backend
cp .env.example .env
# Edit .env and add your Groq API key and JWT secret
```

**Frontend:**

```bash
cd frontend
cp .env.example .env
# Edit .env if needed (defaults should work for local development)
```

### 3. Start with Docker Compose

```bash
# From project root
docker-compose up -d
```

This will start:

- MongoDB on port 27017
- Backend API on port 8000
- Frontend on port 3000

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Check frontend
open http://localhost:3000
```

### 5. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 6. Stop Services

```bash
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v
```

## Production Deployment

### 1. Prepare Environment

**Backend Production Environment:**

```bash
cd backend
cp .env.production.example .env.production
```

Edit `.env.production` and set:

- `MONGODB_URL`: Your MongoDB Atlas connection string
- `GROQ_API_KEY`: Your production Groq API key
- `JWT_SECRET_KEY`: Generate a strong secret (see below)
- `CORS_ORIGINS`: Your production frontend URL
- `ENVIRONMENT=production`
- `DEBUG=false`

**Generate JWT Secret:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Frontend Production Environment:**

```bash
cd frontend
cp .env.production.example .env.production
```

Edit `.env.production` and set:

- `VITE_API_URL`: Your production backend URL
- `VITE_WS_URL`: Your production WebSocket URL

### 2. MongoDB Atlas Setup

1. Create a MongoDB Atlas cluster
2. Create a database user
3. Whitelist your server IP or use 0.0.0.0/0 (not recommended)
4. Get connection string and update `MONGODB_URL`

### 3. Build Production Images

```bash
# Build backend
docker build -t sva-chatbot-backend:latest ./backend

# Build frontend
docker build -t sva-chatbot-frontend:latest ./frontend
```

### 4. Deploy with Docker Compose

```bash
# Set MongoDB credentials
export MONGO_ROOT_USERNAME=admin
export MONGO_ROOT_PASSWORD=your_secure_password

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

### 5. Configure Nginx (Optional but Recommended)

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Backend API
        location /api {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # WebSocket
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
        }
    }
}
```

## Cloud Deployment

### Railway Deployment

1. **Create Railway Account**: https://railway.app

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository

3. **Add MongoDB**:
   - Click "New" → "Database" → "MongoDB"
   - Copy connection string

4. **Configure Backend Service**:
   - Add service from repo
   - Set root directory: `/backend`
   - Add environment variables from `.env.production`
   - Set `MONGODB_URL` to Railway MongoDB connection string

5. **Configure Frontend Service**:
   - Add service from repo
   - Set root directory: `/frontend`
   - Add environment variables from `.env.production`
   - Set `VITE_API_URL` to backend service URL

6. **Deploy**:
   - Railway will automatically build and deploy
   - Get public URLs for both services

### Render Deployment

1. **Create Render Account**: https://render.com

2. **Create Web Service for Backend**:
   - New → Web Service
   - Connect repository
   - Name: `sva-chatbot-backend`
   - Root Directory: `backend`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4`
   - Add environment variables

3. **Create Web Service for Frontend**:
   - New → Web Service
   - Connect repository
   - Name: `sva-chatbot-frontend`
   - Root Directory: `frontend`
   - Build Command: `npm install && npm run build`
   - Start Command: `npm install -g serve && serve -s dist -l $PORT`
   - Add environment variables

4. **Create MongoDB**:
   - Use MongoDB Atlas or Render's MongoDB add-on

### Vercel Deployment (Frontend Only)

1. **Install Vercel CLI**:

```bash
npm install -g vercel
```

2. **Deploy Frontend**:

```bash
cd frontend
vercel --prod
```

3. **Configure Environment**:
   - Add environment variables in Vercel dashboard
   - Set `VITE_API_URL` to your backend URL

### AWS Deployment

See separate AWS deployment guide for:

- ECS/Fargate deployment
- EC2 deployment
- Elastic Beanstalk deployment

## Environment Configuration

### Backend Environment Variables

| Variable          | Description                          | Required | Default                 |
| ----------------- | ------------------------------------ | -------- | ----------------------- |
| `MONGODB_URL`     | MongoDB connection string            | Yes      | -                       |
| `MONGODB_DB_NAME` | Database name                        | Yes      | `sva_chatbot`           |
| `GROQ_API_KEY`    | Groq API key                         | Yes      | -                       |
| `JWT_SECRET_KEY`  | JWT signing secret                   | Yes      | -                       |
| `ENVIRONMENT`     | Environment (development/production) | No       | `development`           |
| `DEBUG`           | Enable debug mode                    | No       | `true`                  |
| `CORS_ORIGINS`    | Allowed CORS origins                 | No       | `http://localhost:3000` |
| `LOG_LEVEL`       | Logging level                        | No       | `INFO`                  |
| `WORKERS`         | Number of Uvicorn workers            | No       | `4`                     |

### Frontend Environment Variables

| Variable                | Description      | Required | Default                 |
| ----------------------- | ---------------- | -------- | ----------------------- |
| `VITE_API_URL`          | Backend API URL  | Yes      | `http://localhost:8000` |
| `VITE_WS_URL`           | WebSocket URL    | Yes      | `ws://localhost:8000`   |
| `VITE_APP_NAME`         | Application name | No       | `SVA-Chatbot`           |
| `VITE_ENABLE_ANALYTICS` | Enable analytics | No       | `false`                 |

## Monitoring and Maintenance

### Health Checks

```bash
# Comprehensive health check
curl https://your-domain.com/health

# Liveness probe
curl https://your-domain.com/health/live

# Readiness probe
curl https://your-domain.com/health/ready
```

### Metrics

```bash
# Performance metrics
curl https://your-domain.com/metrics

# Cache statistics
curl https://your-domain.com/cache/stats
```

### Logs

**Docker Compose:**

```bash
# View logs
docker-compose logs -f backend

# Export logs
docker-compose logs backend > backend.log
```

**Production:**

- Configure log aggregation (ELK, Splunk, CloudWatch)
- Set up log rotation
- Monitor error rates

### Backups

**MongoDB:**

```bash
# Backup
mongodump --uri="mongodb://..." --out=/backup/$(date +%Y%m%d)

# Restore
mongorestore --uri="mongodb://..." /backup/20260116
```

**Automated Backups:**

- Configure MongoDB Atlas automated backups
- Set up daily backup cron jobs
- Store backups in S3 or similar

### Updates

**Rolling Update:**

```bash
# Pull latest images
docker-compose pull

# Restart services one by one
docker-compose up -d --no-deps backend
docker-compose up -d --no-deps frontend
```

**Zero-Downtime Update:**

- Use blue-green deployment
- Use Kubernetes rolling updates
- Use load balancer health checks

### Scaling

**Horizontal Scaling:**

```bash
# Scale backend
docker-compose up -d --scale backend=3

# Scale with load balancer
# Configure nginx upstream with multiple backend instances
```

**Vertical Scaling:**

- Increase container resources in docker-compose.prod.yml
- Adjust `WORKERS` environment variable
- Increase MongoDB instance size

## Troubleshooting

### Common Issues

**Backend won't start:**

- Check MongoDB connection
- Verify Groq API key
- Check logs: `docker-compose logs backend`

**Frontend can't connect to backend:**

- Verify `VITE_API_URL` is correct
- Check CORS configuration
- Verify backend is running

**Database connection errors:**

- Check MongoDB is running
- Verify connection string
- Check network connectivity
- Whitelist IP in MongoDB Atlas

**High memory usage:**

- Reduce number of workers
- Adjust cache TTLs
- Increase container memory limits

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Backend
DEBUG=true docker-compose up backend

# View detailed logs
docker-compose logs -f --tail=100 backend
```

## Security Checklist

- [ ] Change default JWT secret
- [ ] Use strong MongoDB passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up rate limiting
- [ ] Enable CORS restrictions
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] API key rotation
- [ ] Monitor access logs

## Support

For issues and questions:

- GitHub Issues: https://github.com/your-org/sva-chatbot/issues
- Documentation: https://docs.your-domain.com
- Email: support@your-domain.com
