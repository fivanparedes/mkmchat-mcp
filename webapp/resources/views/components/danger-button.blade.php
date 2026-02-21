<button {{ $attributes->merge(['type' => 'button', 'class' => 'mk-btn-danger']) }}>
    {{ $slot }}
</button>