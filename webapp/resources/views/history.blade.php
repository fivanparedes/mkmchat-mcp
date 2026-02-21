<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-mk-text leading-tight uppercase tracking-wide">
            &#128220; {{ __('Query History') }}
        </h2>
    </x-slot>

    <div class="py-8">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <livewire:query-history-list />
        </div>
    </div>
</x-app-layout>