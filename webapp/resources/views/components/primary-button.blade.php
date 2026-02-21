<button {{ $attributes->merge(['type' => 'submit', 'class' => 'mk-btn-fire']) }}>
    {{ $slot }}
</button>