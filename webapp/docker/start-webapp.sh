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

if ! grep -q '^APP_KEY=base64:' .env; then
  php artisan key:generate --force
fi

php artisan package:discover --ansi

touch database/database.sqlite
php artisan migrate --force

exec php artisan serve --host=0.0.0.0 --port=8000
