<section>
    <header>
        <h2 class="text-lg font-medium text-mk-text">{{ __('Theme Preferences') }}</h2>
        <p class="mt-1 text-sm text-mk-muted">{{ __('Select your preferred theme for the MKMChat application.') }}</p>
    </header>

    <form wire:submit="updateTheme" class="mt-6 space-y-6">
        <div>
            <x-input-label :value="__('Application Theme')" />
            <div class="mt-2 space-y-4">
                <label class="flex items-center">
                    <input type="radio" wire:model="theme" value="scorpion" class="text-mk-fire focus:ring-mk-fire border-mk-border bg-mk-surface">
                    <span class="ml-2 text-mk-text">{{ __('Scorpion (Dark with gold accents)') }}</span>
                </label>

                <label class="flex items-center">
                    <input type="radio" wire:model="theme" value="sub-zero" class="text-mk-fire focus:ring-mk-fire border-mk-border bg-mk-surface">
                    <span class="ml-2 text-mk-text">{{ __('Sub Zero (Light with blue accents)') }}</span>
                </label>
            </div>
            <x-input-error :messages="$errors->get('theme')" class="mt-2" />
        </div>

        <div class="flex items-center gap-4">
            <x-primary-button>{{ __('Save Theme') }}</x-primary-button>
            <x-action-message class="me-3" on="theme-updated">{{ __('Saved.') }}</x-action-message>
        </div>
    </form>
</section>
