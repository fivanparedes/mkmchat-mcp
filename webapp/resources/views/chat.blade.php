<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-mk-text leading-tight uppercase tracking-wide">
            &#128172; {{ __('Chat') }}
        </h2>
    </x-slot>

    <div class="py-6">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 flex flex-col gap-6 min-h-0">
            <x-app-quick-nav current="chat" />
            <div class="min-h-0">
                <livewire:chat />
            </div>
        </div>
    </div>
</x-app-layout>
