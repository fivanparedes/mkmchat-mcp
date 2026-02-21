<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>MKMChat &mdash; Your Mortal Kombat Mobile Assistant</title>
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=figtree:400,500,600,700&display=swap" rel="stylesheet" />
        @vite(['resources/css/app.css', 'resources/js/app.js'])
    </head>
    <body class="font-sans antialiased bg-mk-bg text-mk-text">

        {{--  HERO  --}}
        <div class="relative min-h-screen flex flex-col"
             style="background: radial-gradient(ellipse at 50% -5%, #2d0d00 0%, #0a0a0a 65%);">

            <div class="w-full h-0.5 bg-gradient-to-r from-transparent via-mk-fire to-transparent"></div>

            {{-- Top nav --}}
            <nav class="relative z-10 max-w-7xl mx-auto w-full px-6 py-5 flex items-center justify-between">
                <span class="text-xl font-black tracking-widest text-mk-fire uppercase"
                      style="font-family: 'Cinzel', serif;">MKMChat</span>

                @if (Route::has('login'))
                    <div class="flex items-center gap-3">
                        @auth
                            <a href="{{ route('dashboard') }}" wire:navigate
                               class="inline-flex items-center px-5 py-2 bg-mk-fire text-white text-xs font-bold uppercase tracking-widest rounded-md hover:bg-mk-fire-light transition">
                                Dashboard
                            </a>
                        @else
                            <a href="{{ route('login') }}"
                               class="text-sm text-mk-muted hover:text-mk-text transition">Sign In</a>
                            @if (Route::has('register'))
                                <a href="{{ route('register') }}"
                                   class="inline-flex items-center px-5 py-2 bg-mk-fire text-white text-xs font-bold uppercase tracking-widest rounded-md hover:bg-mk-fire-light transition">
                                    Get Started
                                </a>
                            @endif
                        @endauth
                    </div>
                @endif
            </nav>

            {{-- Hero content --}}
            <div class="flex-1 flex flex-col items-center justify-center text-center px-6 pb-20 pt-8">
                <div class="flex items-center gap-4 mb-10">
                    <div class="h-px w-20 bg-gradient-to-r from-transparent to-mk-fire opacity-60"></div>
                    <span class="text-mk-fire text-2xl select-none">&#9876;</span>
                    <div class="h-px w-20 bg-gradient-to-l from-transparent to-mk-fire opacity-60"></div>
                </div>

                <h1 class="text-5xl sm:text-7xl font-black uppercase tracking-widest text-white mb-4"
                    style="font-family: 'Cinzel', serif; text-shadow: 0 0 60px rgba(232,66,10,0.4), 0 2px 4px rgba(0,0,0,0.9);">
                    MKMChat
                </h1>

                <p class="text-lg sm:text-2xl font-semibold text-mk-fire-light tracking-wide mb-5 uppercase">
                    Your Mortal Kombat Mobile Assistant
                </p>

                <p class="max-w-lg text-mk-muted text-base leading-relaxed mb-10">
                    Powered by local AI and a rich knowledge base of fighters, equipment, and game mechanics.
                    Build the perfect team, master every tower, and crush every opponent.
                </p>

                @if (Route::has('login'))
                    <div class="flex flex-col sm:flex-row gap-4 items-center">
                        @auth
                            <a href="{{ route('dashboard') }}"
                               class="inline-flex items-center px-10 py-3 bg-mk-fire text-white text-sm font-bold uppercase tracking-widest rounded-md hover:bg-mk-fire-light transition shadow-lg">
                                &#9876; Go to Dashboard
                            </a>
                        @else
                            @if (Route::has('register'))
                                <a href="{{ route('register') }}"
                                   class="inline-flex items-center px-10 py-3 bg-mk-fire text-white text-sm font-bold uppercase tracking-widest rounded-md hover:bg-mk-fire-light transition shadow-lg">
                                    &#9876; Get Started &mdash; Free
                                </a>
                            @endif
                            <a href="{{ route('login') }}"
                               class="inline-flex items-center px-10 py-3 border border-mk-border text-mk-muted text-sm font-semibold uppercase tracking-widest rounded-md hover:border-mk-fire hover:text-mk-fire transition">
                                Sign In
                            </a>
                        @endauth
                    </div>
                @endif

                <div class="mt-16 text-mk-muted text-xs uppercase tracking-widest animate-bounce select-none">
                    &#8595; Discover Features
                </div>
            </div>
        </div>

        {{--  FEATURES  --}}
        <section class="bg-mk-surface border-t border-mk-border py-20 px-6">
            <div class="max-w-6xl mx-auto">
                <div class="text-center mb-14">
                    <h2 class="text-3xl font-black text-white uppercase tracking-widest mb-4"
                        style="font-family: 'Cinzel', serif;">What Can I Do?</h2>
                    <div class="flex items-center justify-center gap-3">
                        <div class="h-px w-12 bg-mk-fire opacity-60"></div>
                        <span class="text-mk-fire text-xs uppercase tracking-widest font-semibold">Features</span>
                        <div class="h-px w-12 bg-mk-fire opacity-60"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                    <div class="mk-card p-6 hover:border-mk-fire transition-colors group">
                        <div class="text-3xl mb-4">&#9876;&#65039;</div>
                        <h3 class="font-bold text-white text-sm uppercase tracking-wide mb-2 group-hover:text-mk-fire transition-colors">Team Builder</h3>
                        <p class="text-mk-muted text-sm leading-relaxed">
                            AI-powered 3-character team suggestions with full equipment loadouts, tailored to your strategy and owned fighters.
                        </p>
                    </div>

                    <div class="mk-card p-6 hover:border-mk-fire transition-colors group">
                        <div class="text-3xl mb-4">&#128172;</div>
                        <h3 class="font-bold text-white text-sm uppercase tracking-wide mb-2 group-hover:text-mk-fire transition-colors">Ask the Oracle</h3>
                        <p class="text-mk-muted text-sm leading-relaxed">
                            Ask anything about MK Mobile &mdash; mechanics, tower strategies, character synergies, and resource spending.
                        </p>
                    </div>

                    <div class="mk-card p-6 hover:border-mk-fire transition-colors group">
                        <div class="text-3xl mb-4">&#129504;</div>
                        <h3 class="font-bold text-white text-sm uppercase tracking-wide mb-2 group-hover:text-mk-fire transition-colors">RAG-Powered</h3>
                        <p class="text-mk-muted text-sm leading-relaxed">
                            Backed by a rich knowledge base of characters, equipment, passives, glossary and gameplay guides.
                        </p>
                    </div>

                    <div class="mk-card p-6 hover:border-mk-fire transition-colors group">
                        <div class="text-3xl mb-4">&#128220;</div>
                        <h3 class="font-bold text-white text-sm uppercase tracking-wide mb-2 group-hover:text-mk-fire transition-colors">Query History</h3>
                        <p class="text-mk-muted text-sm leading-relaxed">
                            Every team build and question is saved. Review past answers, revisit strategies, and track daily usage.
                        </p>
                    </div>
                </div>
            </div>
        </section>

        {{--  HOW IT WORKS  --}}
        <section class="bg-mk-bg border-t border-mk-border py-20 px-6">
            <div class="max-w-4xl mx-auto">
                <div class="text-center mb-14">
                    <h2 class="text-3xl font-black text-white uppercase tracking-widest mb-4"
                        style="font-family: 'Cinzel', serif;">How It Works</h2>
                    <div class="flex items-center justify-center gap-3">
                        <div class="h-px w-12 bg-mk-fire opacity-60"></div>
                        <span class="text-mk-fire text-xs uppercase tracking-widest font-semibold">Local AI</span>
                        <div class="h-px w-12 bg-mk-fire opacity-60"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-3 gap-10 text-center">
                    <div>
                        <div class="text-4xl font-black text-mk-fire mb-3" style="font-family: 'Cinzel', serif;">01</div>
                        <h4 class="font-bold text-white text-sm uppercase tracking-wide mb-2">Describe Your Goal</h4>
                        <p class="text-mk-muted text-sm leading-relaxed">Tell the assistant your strategy &mdash; rush, defense, tower challenge &mdash; in plain language.</p>
                    </div>
                    <div>
                        <div class="text-4xl font-black text-mk-fire mb-3" style="font-family: 'Cinzel', serif;">02</div>
                        <h4 class="font-bold text-white text-sm uppercase tracking-wide mb-2">AI Searches the Knowledge Base</h4>
                        <p class="text-mk-muted text-sm leading-relaxed">The system retrieves the most relevant characters, equipment, and mechanics using semantic search.</p>
                    </div>
                    <div>
                        <div class="text-4xl font-black text-mk-fire mb-3" style="font-family: 'Cinzel', serif;">03</div>
                        <h4 class="font-bold text-white text-sm uppercase tracking-wide mb-2">Get Your Answer</h4>
                        <p class="text-mk-muted text-sm leading-relaxed">A local LLM synthesizes the context and delivers detailed team builds or expert answers. All on your device.</p>
                    </div>
                </div>
            </div>
        </section>

        {{--  FOOTER  --}}
        <footer class="bg-mk-surface border-t border-mk-border">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-3">
                <p class="text-xs text-mk-muted">
                    &copy; {{ date('Y') }} MKMChat &mdash; Not affiliated with Warner Bros. or NetherRealm Studios.
                    Released under the <a href="https://opensource.org/licenses/MIT" target="_blank" class="text-mk-fire hover:underline">MIT License</a>.
                </p>
                <p class="text-xs text-mk-muted">
                    Made by <a href="https://x.com/hacheipe399" target="_blank" class="text-mk-fire font-semibold hover:underline">@hacheipe399</a>
                </p>
            </div>
        </footer>

    </body>
</html>