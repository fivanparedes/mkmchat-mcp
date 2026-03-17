FROM node:20-alpine AS assets

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY resources ./resources
COPY vite.config.js postcss.config.js tailwind.config.js ./
RUN npm run build

FROM php:8.4-cli-bookworm

WORKDIR /var/www/html

ENV APP_ENV=local \
    APP_DEBUG=true \
    APP_URL=http://localhost:8000 \
    DB_CONNECTION=sqlite \
    MKM_API_URL=http://python-api:8080 \
    MKM_DAILY_LIMIT=0

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        unzip \
        libsqlite3-dev \
        libonig-dev \
        libxml2-dev \
        libcurl4-openssl-dev \
        libzip-dev \
        libicu-dev \
    && docker-php-ext-install \
        pdo_sqlite \
        mbstring \
        xml \
        curl \
        bcmath \
        zip \
        intl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

COPY . .
RUN composer install --no-interaction --prefer-dist --optimize-autoloader --no-dev --no-scripts

COPY --from=assets /app/public/build ./public/build
COPY docker/start-webapp.sh /usr/local/bin/start-webapp

RUN chmod +x /usr/local/bin/start-webapp \
    && mkdir -p storage/framework/cache storage/framework/sessions storage/framework/views bootstrap/cache database

EXPOSE 8000

CMD ["start-webapp"]
