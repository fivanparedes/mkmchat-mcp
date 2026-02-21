@props(['value'])

<label {{ $attributes->merge(['class' => 'block font-medium text-sm text-mk-muted']) }}>
    {{ $value ?? $slot }}
</label>