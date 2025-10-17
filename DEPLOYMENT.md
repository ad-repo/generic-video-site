# Video Site Deployment Guide

## Deploy with Cache Clear

For a complete deployment with aggressive cache clearing and verification:
```bash
./deploy-with-cache-clear.sh
```

## Manual Deploy

If you prefer to run commands manually:
```bash
# Stop containers
sudo docker-compose -f docker-compose.yml down

# Remove old image
sudo docker rmi nas3/generic-video-site:local

# Clean up
sudo docker system prune -f

# Rebuild with no cache
sudo docker-compose -f docker-compose.yml build --no-cache

# Start containers
sudo docker-compose -f docker-compose.yml up -d
```

## Verification

After deployment, check:
1. **Browser**: Visit your site URL
2. **Sidebar**: Should see course navigation on the left
3. **Version**: Look for "DEPLOYED VERSION 2.0" in header
4. **Star ratings**: Should be able to rate and clear courses
5. **Console**: Open browser dev tools (F12) for any errors

## Troubleshooting

### Container not starting
```bash
sudo docker-compose logs
```

### Files not updating
```bash
# Check if files are in container
sudo docker exec generic-video-site ls -la /app/static/

# Check HTML content
sudo docker exec generic-video-site cat /app/static/index.html | head -10
```

### Force complete rebuild
```bash
sudo docker system prune -a
./deploy-with-cache-clear.sh
```

## Useful Commands

- **View logs**: `sudo docker-compose logs -f`
- **Stop service**: `sudo docker-compose down`
- **Restart**: `sudo docker-compose restart`
- **Check status**: `sudo docker-compose ps`
- **Shell access**: `sudo docker exec -it generic-video-site /bin/bash`
