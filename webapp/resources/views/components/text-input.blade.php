@props(['disabled' => false])

<input @disabled($disabled) {{ $attributes->merge(['class' => 'bg-mk-surface border-mk-border text-mk-text rounded-md shadow-sm focus:border-mk-fire focus:ring-mk-fire placeholder:text-mk-muted disabled:opacity-50']) }}>