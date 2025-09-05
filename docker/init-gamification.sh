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
    
    # Get LMS app - try local first, then remote
    echo "📦 Getting LMS app..."
    if [ -d "/workspace/lms" ]; then
        echo "Using local LMS app..."
        bench get-app --resolve-deps lms /workspace
    else
        echo "Downloading LMS app from GitHub..."
        bench get-app lms
    fi
    
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
    
    bench start
fi