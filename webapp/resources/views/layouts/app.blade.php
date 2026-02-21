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
        <div class="min-h-screen flex flex-col">
            <livewire:layout.navigation />

            @if (isset($header))
                <header class="bg-mk-surface border-b border-mk-border">
                    <div class="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
                        {{ $header }}
                    </div>
                </header>
            @endif

            <main class="flex-1">
                {{ $slot }}
            </main>

            <footer class="bg-mk-surface border-t border-mk-border mt-auto">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-3">
                    <p class="text-xs text-mk-muted">
                        &copy; {{ date('Y') }} MKMChat &mdash; Not affiliated with Warner Bros. or NetherRealm Studios.
                        Released under the <a href="https://opensource.org/licenses/MIT" target="_blank" class="text-mk-fire hover:underline">MIT License</a>.
                    </p>
                    <p class="text-xs text-mk-muted">
                        Made by <a href="https://x.com/hacheipe399" target="_blank" class="text-mk-fire font-semibold hover:underline">@hacheipe399</a>
                    </p>
                </div>
            </footer>
        </div>
    </body>
</html>