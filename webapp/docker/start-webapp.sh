#!/bin/sh
set -e

cd /var/www/html

if [ ! -f .env ]; then
  cp .env.example .env
fi

if [ -n "${APP_KEY:-}" ]; then
  if grep -q '^APP_KEY=' .env; then
    sed -i "s|^APP_KEY=.*|APP_KEY=${APP_KEY}|" .env
  else
    echo "APP_KEY=${APP_KEY}" >> .env
  fi
fi

if [ -n "${MKM_API_URL:-}" ]; then
  if grep -q '^MKM_API_URL=' .env; then
    sed -i "s|^MKM_API_URL=.*|MKM_API_URL=${MKM_API_URL}|" .env
  else
    echo "MKM_API_URL=${MKM_API_URL}" >> .env
  fi
fi

if [ -n "${MKM_DAILY_LIMIT:-}" ]; then
  if grep -q '^MKM_DAILY_LIMIT=' .env; then
    sed -i "s|^MKM_DAILY_LIMIT=.*|MKM_DAILY_LIMIT=${MKM_DAILY_LIMIT}|" .env
  else
    echo "MKM_DAILY_LIMIT=${MKM_DAILY_LIMIT}" >> .env
  fi
fi

if [ -n "${MKM_API_KEY:-}" ]; then
  if grep -q '^MKM_API_KEY=' .env; then
    sed -i "s|^MKM_API_KEY=.*|MKM_API_KEY=${MKM_API_KEY}|" .env
  else
    echo "MKM_API_KEY=${MKM_API_KEY}" >> .env
  fi
fi

if [ -n "${MKM_API_KEY_HEADER:-}" ]; then
  if grep -q '^MKM_API_KEY_HEADER=' .env; then
    sed -i "s|^MKM_API_KEY_HEADER=.*|MKM_API_KEY_HEADER=${MKM_API_KEY_HEADER}|" .env
  else
    echo "MKM_API_KEY_HEADER=${MKM_API_KEY_HEADER}" >> .env
  fi
fi

if [ -n "${MKM_WEB_RATE_LIMIT_PER_MINUTE:-}" ]; then
  if grep -q '^MKM_WEB_RATE_LIMIT_PER_MINUTE=' .env; then
    sed -i "s|^MKM_WEB_RATE_LIMIT_PER_MINUTE=.*|MKM_WEB_RATE_LIMIT_PER_MINUTE=${MKM_WEB_RATE_LIMIT_PER_MINUTE}|" .env
  else
    echo "MKM_WEB_RATE_LIMIT_PER_MINUTE=${MKM_WEB_RATE_LIMIT_PER_MINUTE}" >> .env
  fi
fi

php artisan config:clear --ansi || true
php artisan cache:clear --ansi || true

if ! grep -q '^APP_KEY=base64:' .env; then
  php artisan key:generate --force
fi

php artisan package:discover --ansi

touch database/database.sqlite
php artisan migrate --force

exec php artisan serve --host=0.0.0.0 --port=8000
