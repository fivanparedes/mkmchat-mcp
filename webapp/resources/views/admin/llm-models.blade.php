<x-app-layout>
    <x-slot name="header">
        <h2 class="font-semibold text-xl text-mk-text leading-tight uppercase tracking-wide">
            &#9881;&#65039; {{ __('Admin — LLM Models') }}
        </h2>
    </x-slot>

    <div class="py-8">
        <div class="max-w-7xl mx-auto sm:px-6 lg:px-8">
            <livewire:admin.llm-models />
        </div>
    </div>
</x-app-layout>
