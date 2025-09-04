# Frappe LMS Gamification - Docker Deployment Guide

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Deployment](#detailed-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Database Migration](#database-migration)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Production Configuration](#production-configuration)
9. [Troubleshooting](#troubleshooting)
10. [Rollback Procedures](#rollback-procedures)
11. [Maintenance](#maintenance)
12. [Performance Optimization](#performance-optimization)

## 🎯 Overview

This guide provides comprehensive instructions for deploying Frappe LMS with the new gamification features using Docker. The gamification system includes points management, leaderboards, challenges, streak tracking, and social features.

### What's New in Gamification v2.0.0
- **Points System**: Comprehensive point earning and spending
- **Leaderboards**: Global and course-specific rankings
- **Challenges**: Time-based competitive learning
- **Streaks**: Daily learning habit tracking
- **Social Features**: Achievement sharing and community interaction

## 🔧 Prerequisites

### System Requirements
- **Docker**: Version 20.10+ 
- **Docker Compose**: Version 2.0+
- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 10GB free space (20GB recommended)
- **CPU**: 2+ cores recommended

### Network Requirements
- **Ports**: 8000 (web), 9000 (socketio), 3306 (database), 6379 (redis)
- **Internet Access**: Required for initial setup and updates

### Verify Prerequisites
```bash
# Check Docker version
docker --version
docker-compose --version

# Check available resources
docker system info

# Check port availability
netstat -tuln | grep -E ':(8000|9000|3306|6379)'
```

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/frappe/lms.git
cd lms
```

### 2. Start Services
```bash
cd docker
docker-compose up -d
```

### 3. Access Application
- **Web Interface**: http://localhost:8000
- **Default Credentials**: admin / admin
- **Site**: lms.localhost

## 🔨 Detailed Deployment

### Step 1: Environment Preparation

#### 1.1 Create Project Directory
```bash
mkdir frappe-lms-gamification
cd frappe-lms-gamification
```

#### 1.2 Clone Repository
```bash
git clone https://github.com/frappe/lms.git .
```

#### 1.3 Verify Gamification Files
```bash
# Check for gamification components
ls -la lms/lms/doctype/ | grep -E '(points|challenge|leaderboard|streak|social)'
ls -la lms/lms/ | grep gamification
```

### Step 2: Docker Configuration

#### 2.1 Review Docker Compose Configuration
```bash
cat docker/docker-compose.yml
```

#### 2.2 Enhanced Docker Compose (Optional)
Create an enhanced version with Redis optimization:

```yaml
# docker/docker-compose.enhanced.yml
version: "3.7"
name: lms-gamification
services:
  mariadb:
    image: mariadb:10.8
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --skip-character-set-client-handshake
      - --skip-innodb-read-only-compressed
      - --innodb-buffer-pool-size=1G
      - --max-connections=200
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-123}
      MYSQL_DATABASE: lms
    volumes:
      - mariadb-data:/var/lib/mysql
      - ./mariadb.cnf:/etc/mysql/conf.d/mariadb.cnf
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 20s
      retries: 5

  frappe:
    image: frappe/bench:latest
    command: bash /workspace/init.sh
    environment:
      - SHELL=/bin/bash
      - REDIS_CACHE_URL=redis://redis:6379/0
      - REDIS_QUEUE_URL=redis://redis:6379/1
      - REDIS_SOCKETIO_URL=redis://redis:6379/2
    working_dir: /home/frappe
    volumes:
      - .:/workspace
      - frappe-data:/home/frappe/frappe-bench
    ports:
      - "${WEB_PORT:-8000}:8000"
      - "${SOCKETIO_PORT:-9000}:9000"
    depends_on:
      mariadb:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  mariadb-data:
  redis-data:
  frappe-data:
```

### Step 3: Environment Variables

#### 3.1 Create Environment File
```bash
# Create .env file in docker directory
cat > docker/.env << EOF
# Database Configuration
DB_ROOT_PASSWORD=secure_password_123
DB_NAME=lms

# Application Configuration
WEB_PORT=8000
SOCKETIO_PORT=9000
SITE_NAME=lms.localhost
ADMIN_PASSWORD=admin123

# Gamification Configuration
ENABLE_GAMIFICATION=1
POINTS_MULTIPLIER=1.0
STREAK_BONUS_POINTS=5
DAILY_CHALLENGE_POINTS=25

# Redis Configuration
REDIS_CACHE_URL=redis://redis:6379/0
REDIS_QUEUE_URL=redis://redis:6379/1
REDIS_SOCKETIO_URL=redis://redis:6379/2

# Performance Settings
WORKER_PROCESSES=2
MAX_CONNECTIONS=200
EOF
```

### Step 4: Enhanced Initialization Script

#### 4.1 Create Enhanced Init Script
```bash
cat > docker/init-gamification.sh << 'EOF'
#!/bin/bash
set -e

echo "🎮 Starting Frappe LMS with Gamification Features..."

# Check if bench already exists
if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "📁 Bench already exists, starting services..."
    cd frappe-bench
    
    # Update gamification features
    echo "🔄 Updating gamification features..."
    bench --site ${SITE_NAME:-lms.localhost} migrate
    bench --site ${SITE_NAME:-lms.localhost} clear-cache
    
    bench start
else
    echo "🏗️ Creating new bench with gamification support..."
    
    export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"
    
    # Initialize bench
    bench init --skip-redis-config-generation frappe-bench
    cd frappe-bench
    
    # Configure services
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379/0
    bench set-redis-queue-host redis://redis:6379/1
    bench set-redis-socketio-host redis://redis:6379/2
    
    # Remove conflicting services from Procfile
    sed -i '/redis/d' ./Procfile
    sed -i '/watch/d' ./Procfile
    
    # Get LMS app
    bench get-app lms
    
    # Create site with gamification
    echo "🌐 Creating site with gamification features..."
    bench new-site ${SITE_NAME:-lms.localhost} \
        --force \
        --mariadb-root-password ${DB_ROOT_PASSWORD:-123} \
        --admin-password ${ADMIN_PASSWORD:-admin} \
        --no-mariadb-socket
    
    # Install LMS app
    bench --site ${SITE_NAME:-lms.localhost} install-app lms
    
    # Configure development mode
    bench --site ${SITE_NAME:-lms.localhost} set-config developer_mode 1
    
    # Enable gamification features
    echo "🎯 Enabling gamification features..."
    bench --site ${SITE_NAME:-lms.localhost} set-config enable_gamification 1
    bench --site ${SITE_NAME:-lms.localhost} set-config points_multiplier ${POINTS_MULTIPLIER:-1.0}
    
    # Run gamification migrations
    echo "📊 Running gamification database migrations..."
    bench --site ${SITE_NAME:-lms.localhost} migrate
    
    # Setup gamification data
    echo "🎮 Setting up gamification data..."
    bench --site ${SITE_NAME:-lms.localhost} execute "lms.lms.gamification.setup_gamification_data"
    
    # Clear cache
    bench --site ${SITE_NAME:-lms.localhost} clear-cache
    
    # Set default site
    bench use ${SITE_NAME:-lms.localhost}
    
    echo "✅ Gamification setup completed!"
    
    # Start services
    bench start
fi
EOF

chmod +x docker/init-gamification.sh
```

### Step 5: Database Configuration

#### 5.1 Create MariaDB Configuration
```bash
cat > docker/mariadb.cnf << EOF
[mysqld]
# Gamification Optimizations
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
innodb_flush_log_at_trx_commit = 2
innodb_flush_method = O_DIRECT

# Connection Settings
max_connections = 200
max_connect_errors = 1000000

# Query Cache (for leaderboards)
query_cache_type = 1
query_cache_size = 128M
query_cache_limit = 2M

# Temporary Tables (for analytics)
tmp_table_size = 64M
max_heap_table_size = 64M

# Character Set
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# Logging
log_error = /var/log/mysql/error.log
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2
EOF
```

## 🚀 Deployment Execution

### Method 1: Standard Deployment
```bash
cd docker
docker-compose up -d
```

### Method 2: Enhanced Deployment
```bash
cd docker
docker-compose -f docker-compose.enhanced.yml up -d
```

### Method 3: Production Deployment
```bash
cd docker
docker-compose -f docker-compose.enhanced.yml --env-file .env up -d
```

## 🔍 Database Migration

### Automatic Migration (Recommended)
The enhanced init script handles migrations automatically. Monitor the logs:

```bash
docker-compose logs -f frappe
```

### Manual Migration (If Needed)
```bash
# Access the container
docker-compose exec frappe bash

# Navigate to bench directory
cd frappe-bench

# Run migrations
bench --site lms.localhost migrate

# Verify gamification tables
bench --site lms.localhost execute "frappe.db.sql('SHOW TABLES LIKE \"%lms%gamification%\"')"
```

### Verify Gamification Tables
```bash
# Check if gamification tables exist
docker-compose exec frappe bash -c "cd frappe-bench && bench --site lms.localhost execute \"print([t for t in frappe.db.get_tables() if 'lms' in t.lower()])\""
```

## ✅ Post-Deployment Verification

### 1. Service Health Check
```bash
# Check all services are running
docker-compose ps

# Check service logs
docker-compose logs mariadb
docker-compose logs redis
docker-compose logs frappe
```

### 2. Application Access
```bash
# Test web interface
curl -I http://localhost:8000

# Test API endpoints
curl -X GET "http://localhost:8000/api/method/lms.gamification.api.get_user_points" \
  -H "Authorization: token [your-api-key]:[your-api-secret]"
```

### 3. Gamification Features Test
```bash
# Access the container and test gamification
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
from lms.lms.gamification import award_points

# Test point awarding
result = award_points(
    user="Administrator",
    points=10,
    activity_type="test",
    description="Deployment test"
)
print(f"Points awarded: {result}")
'"
```

### 4. Database Verification
```bash
# Check gamification tables
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
tables = frappe.db.sql(\"SHOW TABLES LIKE \\\"%lms%\\\"\", as_dict=True)
print(\"LMS Tables:\", [t.values() for t in tables])
'"
```

### 5. Frontend Verification
1. Open http://localhost:8000 in browser
2. Login with admin credentials
3. Navigate to:
   - `/leaderboard` - Global leaderboard
   - `/points` - Points dashboard
   - `/challenges` - Challenge hub
   - `/streaks` - Streak tracker

## 🏭 Production Configuration

### 1. Security Configuration

#### 1.1 Environment Variables for Production
```bash
cat > docker/.env.production << EOF
# Security
DB_ROOT_PASSWORD=your_secure_db_password_here
ADMIN_PASSWORD=your_secure_admin_password_here
SECRET_KEY=your_secret_key_here

# SSL Configuration
SSL_ENABLED=1
SSL_CERT_PATH=/certs/cert.pem
SSL_KEY_PATH=/certs/key.pem

# Performance
WORKER_PROCESSES=4
MAX_CONNECTIONS=500
REDIS_MAXMEMORY=2gb

# Monitoring
ENABLE_MONITORING=1
LOG_LEVEL=INFO

# Backup
BACKUP_ENABLED=1
BACKUP_SCHEDULE="0 2 * * *"
EOF
```

#### 1.2 Production Docker Compose
```yaml
# docker/docker-compose.production.yml
version: "3.7"
name: lms-gamification-prod
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - frappe
    restart: unless-stopped

  mariadb:
    image: mariadb:10.8
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --innodb-buffer-pool-size=2G
      - --max-connections=500
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
      MYSQL_DATABASE: lms
    volumes:
      - mariadb-data:/var/lib/mysql
      - ./mariadb-prod.cnf:/etc/mysql/conf.d/mariadb.cnf
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      timeout: 20s
      retries: 10

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 2gb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      timeout: 20s
      retries: 5

  frappe:
    image: frappe/bench:latest
    command: bash /workspace/init-production.sh
    environment:
      - SHELL=/bin/bash
      - FRAPPE_ENV=production
      - WORKER_PROCESSES=${WORKER_PROCESSES:-4}
    working_dir: /home/frappe
    volumes:
      - .:/workspace
      - frappe-data:/home/frappe/frappe-bench
      - ./logs:/home/frappe/frappe-bench/logs
    depends_on:
      mariadb:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  worker:
    image: frappe/bench:latest
    command: bash -c "cd frappe-bench && bench worker --queue default,long,short"
    environment:
      - SHELL=/bin/bash
    working_dir: /home/frappe
    volumes:
      - .:/workspace
      - frappe-data:/home/frappe/frappe-bench
    depends_on:
      - frappe
    restart: unless-stopped

  scheduler:
    image: frappe/bench:latest
    command: bash -c "cd frappe-bench && bench schedule"
    environment:
      - SHELL=/bin/bash
    working_dir: /home/frappe
    volumes:
      - .:/workspace
      - frappe-data:/home/frappe/frappe-bench
    depends_on:
      - frappe
    restart: unless-stopped

volumes:
  mariadb-data:
  redis-data:
  frappe-data:
```

### 2. Nginx Configuration
```nginx
# docker/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream frappe {
        server frappe:8000;
    }
    
    upstream socketio {
        server frappe:9000;
    }
    
    # Rate limiting for gamification APIs
    limit_req_zone $binary_remote_addr zone=gamification:10m rate=10r/s;
    
    server {
        listen 80;
        server_name your-domain.com;
        
        # Redirect to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name your-domain.com;
        
        ssl_certificate /etc/nginx/certs/cert.pem;
        ssl_certificate_key /etc/nginx/certs/key.pem;
        
        # Gamification API rate limiting
        location /api/method/lms.gamification {
            limit_req zone=gamification burst=20 nodelay;
            proxy_pass http://frappe;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location / {
            proxy_pass http://frappe;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /socket.io {
            proxy_pass http://socketio;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. Services Not Starting

**Problem**: Docker services fail to start
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs [service-name]
```

**Solutions**:
```bash
# Restart services
docker-compose restart

# Rebuild containers
docker-compose down
docker-compose up --build -d

# Check port conflicts
netstat -tuln | grep -E ':(8000|9000|3306|6379)'
```

#### 2. Database Connection Issues

**Problem**: Cannot connect to MariaDB
```bash
# Test database connection
docker-compose exec mariadb mysql -u root -p123 -e "SHOW DATABASES;"
```

**Solutions**:
```bash
# Reset database
docker-compose down
docker volume rm docker_mariadb-data
docker-compose up -d

# Check database logs
docker-compose logs mariadb
```

#### 3. Gamification Features Not Working

**Problem**: Points not being awarded or leaderboards empty

**Diagnostic Steps**:
```bash
# Check gamification tables
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
print(\"Points Transactions:\", frappe.db.count(\"LMS Points Transaction\"))
print(\"Challenges:\", frappe.db.count(\"LMS Challenge\"))
print(\"Leaderboard Entries:\", frappe.db.count(\"LMS Leaderboard Entry\"))
'"

# Check scheduled jobs
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
from frappe.utils.scheduler import get_scheduled_jobs
print(\"Scheduled Jobs:\", get_scheduled_jobs())
'"
```

**Solutions**:
```bash
# Manually run gamification setup
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute 'lms.lms.gamification.setup_gamification_data()'
"

# Restart scheduler
docker-compose restart scheduler

# Clear cache
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost clear-cache
"
```

#### 4. Performance Issues

**Problem**: Slow leaderboard loading or high memory usage

**Diagnostic Steps**:
```bash
# Check Redis memory usage
docker-compose exec redis redis-cli info memory

# Check database performance
docker-compose exec mariadb mysql -u root -p123 -e "SHOW PROCESSLIST;"

# Check container resources
docker stats
```

**Solutions**:
```bash
# Optimize Redis
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru

# Rebuild leaderboard cache
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute 'lms.lms.gamification.rebuild_leaderboard_cache()'
"

# Increase container resources
# Edit docker-compose.yml to add:
# deploy:
#   resources:
#     limits:
#       memory: 2G
#       cpus: '1.0'
```

#### 5. Frontend Issues

**Problem**: Gamification pages not loading or showing errors

**Solutions**:
```bash
# Rebuild frontend
docker-compose exec frappe bash -c "
cd frappe-bench
bench build
"

# Check frontend logs
docker-compose logs frappe | grep -i error

# Clear browser cache and reload
```

### Log Analysis

#### Enable Debug Logging
```bash
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost set-config developer_mode 1
bench --site lms.localhost set-config log_level DEBUG
"
```

#### View Gamification Logs
```bash
# Application logs
docker-compose logs frappe | grep -i gamification

# Database logs
docker-compose logs mariadb | grep -i error

# Redis logs
docker-compose logs redis
```

## 🔄 Rollback Procedures

### 1. Quick Rollback (Disable Gamification)

```bash
# Disable gamification features
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost set-config enable_gamification 0
bench --site lms.localhost clear-cache
"

# Restart services
docker-compose restart frappe
```

### 2. Database Rollback

#### 2.1 Create Backup Before Rollback
```bash
# Create database backup
docker-compose exec mariadb mysqldump -u root -p123 lms > backup_before_rollback.sql
```

#### 2.2 Remove Gamification Tables
```bash
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe

# List gamification tables
gamification_tables = [
    \"tabLMS Points Transaction\",
    \"tabLMS Challenge\",
    \"tabLMS Challenge Participation\",
    \"tabLMS Leaderboard Entry\",
    \"tabLMS Streak Record\",
    \"tabLMS Social Activity\"
]

for table in gamification_tables:
    try:
        frappe.db.sql(f\"DROP TABLE IF EXISTS `{table}`\")
        print(f\"Dropped table: {table}\")
    except Exception as e:
        print(f\"Error dropping {table}: {e}\")

frappe.db.commit()
'"
```

#### 2.3 Remove User Gamification Fields
```bash
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe

# Remove gamification fields from User
gamification_fields = [
    \"total_points\",
    \"available_points\",
    \"current_streak\",
    \"longest_streak\",
    \"gamification_level\",
    \"last_activity_date\"
]

for field in gamification_fields:
    try:
        frappe.db.sql(f\"ALTER TABLE `tabUser` DROP COLUMN IF EXISTS `{field}`\")
        print(f\"Removed field: {field}\")
    except Exception as e:
        print(f\"Error removing {field}: {e}\")

frappe.db.commit()
'"
```

### 3. Complete System Rollback

#### 3.1 Stop Services
```bash
docker-compose down
```

#### 3.2 Restore from Backup
```bash
# If you have a pre-gamification backup
docker volume rm docker_mariadb-data
docker-compose up -d mariadb

# Wait for MariaDB to start
sleep 30

# Restore backup
docker-compose exec -T mariadb mysql -u root -p123 lms < your_backup.sql
```

#### 3.3 Use Previous Version
```bash
# Checkout previous version
git checkout [previous-version-tag]

# Rebuild and start
docker-compose up --build -d
```

### 4. Partial Rollback (Keep Data)

```bash
# Disable gamification without removing data
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe

# Disable gamification in site config
frappe.db.set_value(\"System Settings\", None, \"enable_gamification\", 0)

# Clear cache
frappe.clear_cache()

print(\"Gamification disabled but data preserved\")
'"
```

## 🔧 Maintenance

### Daily Maintenance

#### 1. Health Check Script
```bash
#!/bin/bash
# daily-health-check.sh

echo "🏥 Daily Health Check - $(date)"

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Check disk usage
echo "💾 Disk Usage:"
df -h

# Check database size
echo "🗄️ Database Size:"
docker-compose exec mariadb mysql -u root -p123 -e "
    SELECT 
        table_schema AS 'Database',
        ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
    FROM information_schema.tables 
    WHERE table_schema = 'lms'
    GROUP BY table_schema;
"

# Check gamification metrics
echo "🎮 Gamification Metrics:"
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
print(f\"Active Users: {frappe.db.count(\"User\", {\"enabled\": 1})}\")
print(f\"Points Transactions: {frappe.db.count(\"LMS Points Transaction\")}\")
print(f\"Active Challenges: {frappe.db.count(\"LMS Challenge\", {\"status\": \"Active\"})}\")
print(f\"Leaderboard Entries: {frappe.db.count(\"LMS Leaderboard Entry\")}\")
'"

echo "✅ Health check completed"
```

#### 2. Backup Script
```bash
#!/bin/bash
# backup-gamification.sh

BACKUP_DIR="/backups/$(date +%Y-%m-%d)"
mkdir -p $BACKUP_DIR

echo "💾 Creating backup - $(date)"

# Database backup
docker-compose exec mariadb mysqldump -u root -p123 --single-transaction lms > "$BACKUP_DIR/lms-database.sql"

# Files backup
docker-compose exec frappe tar -czf - /home/frappe/frappe-bench/sites > "$BACKUP_DIR/lms-files.tar.gz"

# Compress backup
tar -czf "$BACKUP_DIR.tar.gz" -C /backups "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"
```

### Weekly Maintenance

#### 1. Performance Optimization
```bash
#!/bin/bash
# weekly-optimization.sh

echo "⚡ Weekly Optimization - $(date)"

# Optimize database
docker-compose exec mariadb mysql -u root -p123 -e "
    USE lms;
    OPTIMIZE TABLE 
        \`tabLMS Points Transaction\`,
        \`tabLMS Challenge\`,
        \`tabLMS Leaderboard Entry\`,
        \`tabLMS Streak Record\`;
"

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHDB

# Rebuild leaderboard cache
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute 'lms.lms.gamification.rebuild_leaderboard_cache()'
"

# Clear application cache
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost clear-cache
"

echo "✅ Optimization completed"
```

### Monthly Maintenance

#### 1. Data Archival
```bash
#!/bin/bash
# monthly-archival.sh

echo "📦 Monthly Data Archival - $(date)"

# Archive old points transactions (older than 1 year)
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost execute '
import frappe
from frappe.utils import add_years, now

# Archive old transactions
old_date = add_years(now(), -1)
old_transactions = frappe.db.sql(f\"
    SELECT name FROM \`tabLMS Points Transaction\` 
    WHERE transaction_date < \"{old_date}\"
\", as_dict=True)

print(f\"Found {len(old_transactions)} old transactions to archive\")

# Move to archive table (implement as needed)
# frappe.db.sql(\"CREATE TABLE IF NOT EXISTS \`tabLMS Points Transaction Archive\` LIKE \`tabLMS Points Transaction\`\")
# ... archival logic
'"

echo "✅ Archival completed"
```

## 📈 Performance Optimization

### 1. Database Optimization

#### Index Creation
```sql
-- Run these in MariaDB for better performance
CREATE INDEX idx_points_user_date ON `tabLMS Points Transaction` (user, transaction_date);
CREATE INDEX idx_leaderboard_period ON `tabLMS Leaderboard Entry` (period, score DESC);
CREATE INDEX idx_challenge_status ON `tabLMS Challenge` (status, start_date);
CREATE INDEX idx_streak_user_date ON `tabLMS Streak Record` (user, date);
```

#### Query Optimization
```bash
# Enable slow query log
docker-compose exec mariadb mysql -u root -p123 -e "
    SET GLOBAL slow_query_log = 'ON';
    SET GLOBAL long_query_time = 2;
    SET GLOBAL log_queries_not_using_indexes = 'ON';
"
```

### 2. Redis Optimization

```bash
# Optimize Redis for gamification
docker-compose exec redis redis-cli config set maxmemory-policy allkeys-lru
docker-compose exec redis redis-cli config set maxmemory 1gb
docker-compose exec redis redis-cli config set save "900 1 300 10 60 10000"
```

### 3. Application Optimization

```bash
# Enable production optimizations
docker-compose exec frappe bash -c "
cd frappe-bench
bench --site lms.localhost set-config enable_gamification_cache 1
bench --site lms.localhost set-config leaderboard_cache_timeout 300
bench --site lms.localhost set-config points_calculation_batch_size 100
"
```

## 📞 Support and Resources

### Getting Help
- **Documentation**: Check the implementation guide and API documentation
- **GitHub Issues**: Report bugs with the 'gamification' label
- **Community Forum**: Join discussions about gamification features
- **Discord/Slack**: Real-time support from the community

### Useful Commands Reference

```bash
# Quick status check
docker-compose ps && docker-compose logs --tail=50 frappe

# Restart gamification services
docker-compose restart frappe worker scheduler

# Clear all caches
docker-compose exec frappe bash -c "cd frappe-bench && bench --site lms.localhost clear-cache"
docker-compose exec redis redis-cli FLUSHALL

# Check gamification health
docker-compose exec frappe bash -c "cd frappe-bench && bench --site lms.localhost execute 'lms.lms.gamification.health_check()'"

# View recent logs
docker-compose logs --tail=100 -f frappe | grep -i gamification
```

---

**🎮 Congratulations!** You have successfully deployed Frappe LMS with comprehensive gamification features. Your learning platform now includes points, leaderboards, challenges, streaks, and social features to enhance user engagement.

For additional support or advanced configurations, refer to the [implementation guide](./frappe-lms-gamification-implementation-guide.md) or contact the development team.

**Happy Learning! 🚀**