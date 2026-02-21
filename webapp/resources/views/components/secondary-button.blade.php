<button {{ $attributes->merge(['type' => 'button', 'class' => 'mk-btn-secondary']) }}>
    {{ $slot }}
</button>