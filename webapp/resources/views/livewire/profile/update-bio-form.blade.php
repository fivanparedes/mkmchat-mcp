<section>
    <header>
        <h2 class="text-lg font-medium text-mk-text">{{ __('Bio & Avatar') }}</h2>
        <p class="mt-1 text-sm text-mk-muted">{{ __('Personalize your profile with a short bio and avatar URL.') }}</p>
    </header>

    <form wire:submit="updateBio" class="mt-6 space-y-6">
        <div>
            <x-input-label for="bio" :value="__('Bio')" />
            <textarea
                id="bio"
                wire:model="bio"
                rows="3"
                maxlength="500"
                class="mt-1 block w-full rounded-md bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire placeholder:text-mk-muted"
                placeholder="Tell others a little about yourself…"
            ></textarea>
            <p class="mt-1 text-xs text-mk-muted">{{ strlen($bio) }} / 500</p>
            <x-input-error :messages="$errors->get('bio')" class="mt-2" />
        </div>

        <div>
            <x-input-label for="avatarUrl" :value="__('Avatar URL')" />
            <div class="mt-1 flex items-center gap-4">
                @if($avatarUrl)
                    <img src="{{ $avatarUrl }}" alt="Avatar preview" class="w-12 h-12 rounded-full border border-mk-border object-cover" />
                @else
                    <img src="{{ asset('images/fighter-placeholder.svg') }}" alt="Default avatar" class="w-12 h-12 rounded-full border border-mk-border object-cover" />
                @endif
                <x-text-input
                    id="avatarUrl"
                    wire:model.live.debounce.500ms="avatarUrl"
                    type="url"
                    class="block flex-1"
                    placeholder="https://example.com/your-avatar.jpg"
                />
            </div>
            <x-input-error :messages="$errors->get('avatarUrl')" class="mt-2" />
        </div>

        <div class="flex items-center gap-4">
            <x-primary-button>{{ __('Save') }}</x-primary-button>
            <x-action-message class="me-3" on="bio-updated">{{ __('Saved.') }}</x-action-message>
        </div>
    </form>
</section>
