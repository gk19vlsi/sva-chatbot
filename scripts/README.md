# Deployment Scripts

This directory contains deployment scripts for the SVA-Chatbot system.

## Available Scripts

### `deploy-local.sh`

Deploys the application locally using Docker Compose for development.

**Usage:**

```bash
./scripts/deploy-local.sh
```

**What it does:**

- Checks for Docker and Docker Compose
- Creates .env files from examples if needed
- Stops any running containers
- Builds and starts all services
- Performs health checks
- Displays service URLs

**Requirements:**

- Docker
- Docker Compose
- .env files configured

### `deploy-production.sh`

Deploys the application to production using Docker Compose.

**Usage:**

```bash
sudo MONGO_ROOT_USERNAME=admin MONGO_ROOT_PASSWORD=secret ./scripts/deploy-production.sh
```

**What it does:**

- Validates production environment
- Creates backup of current deployment
- Pulls latest code from Git
- Builds production images
- Performs zero-downtime deployment
- Runs health checks
- Rolls back on failure

**Requirements:**

- Docker
- Docker Compose
- Production .env files
- MongoDB credentials set
- Root/sudo access

### `deploy-railway.sh`

Helps deploy the application to Railway.

**Usage:**

```bash
./scripts/deploy-railway.sh
```

**What it does:**

- Checks for Railway CLI
- Logs in to Railway
- Creates/uses Railway project
- Sets environment variables
- Deploys backend and frontend

**Requirements:**

- Railway CLI (`npm install -g @railway/cli`)
- Railway account
- Git repository

### `deploy-render.sh`

Provides instructions for deploying to Render.

**Usage:**

```bash
./scripts/deploy-render.sh
```

**What it does:**

- Displays step-by-step deployment guide
- Optionally creates render.yaml configuration
- Provides environment variable templates

**Requirements:**

- Render account
- Git repository

## Quick Start

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-org/sva-chatbot.git
cd sva-chatbot

# 2. Configure environment
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit .env files with your configuration

# 3. Deploy
./scripts/deploy-local.sh
```

### Production Deployment

```bash
# 1. Prepare production environment
cp backend/.env.production.example backend/.env.production
cp frontend/.env.production.example frontend/.env.production
# Edit .env.production files with production configuration

# 2. Set MongoDB credentials
export MONGO_ROOT_USERNAME=admin
export MONGO_ROOT_PASSWORD=your_secure_password

# 3. Deploy
sudo -E ./scripts/deploy-production.sh
```

### Railway Deployment

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Deploy
./scripts/deploy-railway.sh
```

### Render Deployment

```bash
# Follow the guide
./scripts/deploy-render.sh
```

## CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. **Tests**: Runs backend and frontend tests on every push/PR
2. **Build**: Builds Docker images on main branch
3. **Deploy**: Optionally deploys to production

### Setting up CI/CD

1. **Add GitHub Secrets:**
   - `DOCKER_USERNAME`: Docker Hub username
   - `DOCKER_PASSWORD`: Docker Hub password
   - `DEPLOY_HOST`: Production server hostname
   - `DEPLOY_USER`: SSH username
   - `DEPLOY_KEY`: SSH private key
   - `DEPLOY_URL`: Production URL for health checks

2. **Enable GitHub Actions:**
   - Go to repository Settings → Actions
   - Enable workflows

3. **Push to main:**
   ```bash
   git push origin main
   ```

## Troubleshooting

### Script Permission Denied

```bash
chmod +x scripts/*.sh
```

### Docker Not Found

Install Docker:

- macOS: https://docs.docker.com/desktop/mac/install/
- Linux: https://docs.docker.com/engine/install/
- Windows: https://docs.docker.com/desktop/windows/install/

### MongoDB Connection Failed

- Check MongoDB is running
- Verify connection string in .env
- Check network connectivity
- Whitelist IP in MongoDB Atlas

### Health Check Failed

- Check service logs: `docker-compose logs backend`
- Verify environment variables
- Check port availability
- Wait longer for services to start

### Deployment Rollback

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Restore from backup
cd backups/YYYYMMDD_HHMMSS
docker-compose -f docker-compose.prod.yml up -d
```

## Best Practices

1. **Always test locally first**

   ```bash
   ./scripts/deploy-local.sh
   ```

2. **Use production environment files**
   - Never commit .env files
   - Use strong secrets in production
   - Rotate secrets regularly

3. **Monitor deployments**
   - Check logs after deployment
   - Verify health endpoints
   - Monitor error rates

4. **Backup before production deployment**
   - Automatic backups in deploy-production.sh
   - Manual backups: `mongodump`

5. **Use CI/CD for production**
   - Automated testing
   - Consistent deployments
   - Easy rollbacks

## Support

For issues with deployment scripts:

- Check logs: `docker-compose logs -f`
- Review DEPLOYMENT.md
- Open GitHub issue
- Contact support

## Contributing

When adding new deployment scripts:

1. Follow existing naming convention
2. Add error handling
3. Include health checks
4. Update this README
5. Test thoroughly
