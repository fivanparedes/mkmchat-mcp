<?php

return [
    /*
    |--------------------------------------------------------------------------
    | MK Mobile Assistant API
    |--------------------------------------------------------------------------
    |
    | Base URL of the Python HTTP server (mkmchat).
    |
    */
    'api_url' => env('MKM_API_URL', 'http://localhost:8080'),

    /*
    |--------------------------------------------------------------------------
    | Python API Authentication
    |--------------------------------------------------------------------------
    */
    'api_key' => env('MKM_API_KEY'),
    'api_key_header' => env('MKM_API_KEY_HEADER', 'X-API-Key'),

    /*
    |--------------------------------------------------------------------------
    | Daily query limit per user (0 = unlimited)
    |--------------------------------------------------------------------------
    */
    'daily_limit' => (int) env('MKM_DAILY_LIMIT', 0),

    /*
    |--------------------------------------------------------------------------
    | Per-minute action rate limit (authenticated user, fallback by IP)
    |--------------------------------------------------------------------------
    */
    'web_rate_limit_per_minute' => (int) env('MKM_WEB_RATE_LIMIT_PER_MINUTE', 10),
];
