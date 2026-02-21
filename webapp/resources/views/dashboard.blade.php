<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-mk-text leading-tight uppercase tracking-wide">
            &#9876;&#65039; {{ __('Team Suggestion') }}
        </h2>
    </x-slot>

    <div class="py-8">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8 space-y-6">
            <livewire:team-suggestion />
        </div>
    </div>
</x-app-layout>