<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="csrf-token" content="{{ csrf_token() }}">
        <title>{{ config('app.name', 'MKMChat') }}</title>
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=figtree:400,500,600&display=swap" rel="stylesheet" />
        @vite(['resources/css/app.css', 'resources/js/app.js'])
    </head>
    <body class="font-sans antialiased bg-mk-bg text-mk-text">
        <div class="min-h-screen flex flex-col items-center bg-mk-bg">
            <div class="w-full h-0.5 bg-gradient-to-r from-transparent via-mk-fire to-transparent"></div>

            <div class="w-full sm:max-w-md mt-10 px-6 py-8 flex flex-col items-center">
                <a href="/" wire:navigate class="mb-8">
                    <span class="text-3xl font-black tracking-widest text-mk-fire uppercase"
                          style="font-family: 'Cinzel', serif;">MKMChat</span>
                </a>

                <div class="w-full mk-card shadow-2xl p-8">
                    {{ $slot }}
                </div>
            </div>

            <footer class="mt-auto w-full border-t border-mk-border py-4 px-6">
                <div class="max-w-md mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
                    <p class="text-xs text-mk-muted">
                        &copy; {{ date('Y') }} MKMChat &mdash;
                        <a href="https://opensource.org/licenses/MIT" target="_blank" class="text-mk-fire hover:underline">MIT License</a>
                    </p>
                    <p class="text-xs text-mk-muted">
                        Made by <a href="https://x.com/hacheipe399" target="_blank" class="text-mk-fire font-semibold hover:underline">@hacheipe399</a>
                    </p>
                </div>
            </footer>
        </div>
    </body>
</html>