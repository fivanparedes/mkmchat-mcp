@props([
    'current' => null, // team | history | ask | mechanic
])

<nav {{ $attributes->merge(['class' => 'flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-mk-muted border border-mk-border rounded-lg px-4 py-3 bg-mk-card/50']) }} aria-label="{{ __('App sections') }}">
    <span class="text-xs font-semibold uppercase tracking-wider text-mk-muted shrink-0">{{ __('Jump to') }}</span>
    <a href="{{ route('dashboard') }}" wire:navigate @class(['text-mk-fire font-medium' => $current === 'team', 'hover:text-mk-fire transition' => $current !== 'team'])>{{ __('Team') }}</a>
    <span class="text-mk-border" aria-hidden="true">|</span>
    <a href="{{ route('history') }}" wire:navigate @class(['text-mk-fire font-medium' => $current === 'history', 'hover:text-mk-fire transition' => $current !== 'history'])>{{ __('History') }}</a>
    <span class="text-mk-border" aria-hidden="true">|</span>
    <a href="{{ route('ask') }}" wire:navigate @class(['text-mk-fire font-medium' => $current === 'ask', 'hover:text-mk-fire transition' => $current !== 'ask'])>{{ __('Ask') }}</a>
    <span class="text-mk-border" aria-hidden="true">|</span>
    <a href="{{ route('mechanic') }}" wire:navigate @class(['text-mk-fire font-medium' => $current === 'mechanic', 'hover:text-mk-fire transition' => $current !== 'mechanic'])>{{ __('Explain mechanic') }}</a>
</nav>
