<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-mk-text leading-tight uppercase tracking-wide">
            &#9881;&#65039; {{ __('Explain a Mechanic') }}
        </h2>
    </x-slot>

    <div class="py-8">
        <div class="max-w-4xl mx-auto sm:px-6 lg:px-8 space-y-6">
            <x-app-quick-nav current="mechanic" />
            <livewire:explain-mechanic />
        </div>
    </div>
</x-app-layout>
