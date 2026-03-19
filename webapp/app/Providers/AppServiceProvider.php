<?php

namespace App\Providers;

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        Gate::define('ask-question', fn ($user) => (bool) $user);
        Gate::define('suggest-team', fn ($user) => (bool) $user);
        Gate::define('manage-llm-models', fn ($user) => $user?->isAdmin() === true);

        RateLimiter::for('ai-actions', function (Request $request) {
            $maxAttempts = max(1, (int) config('mkm.web_rate_limit_per_minute', 10));
            $userKey = $request->user()?->id;
            $ip = $request->ip() ?? 'unknown';

            return Limit::perMinute($maxAttempts)->by($userKey ? "user:{$userKey}" : "ip:{$ip}");
        });
    }
}
