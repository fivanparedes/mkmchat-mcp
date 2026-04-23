<div class="space-y-6">
    @if($this->dailyLimit > 0)
        <div class="mk-card p-4 sm:p-6">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-mk-muted">Daily Queries Used</span>
                <span class="text-sm text-mk-muted">{{ $this->todayCount }} / {{ $this->dailyLimit }}</span>
            </div>
            <div class="w-full bg-mk-border rounded-full h-2">
                <div class="h-2 rounded-full {{ $this->limitReached ? 'bg-mk-danger' : 'bg-mk-fire' }}"
                     style="width: {{ min(100, $this->dailyLimit > 0 ? ($this->todayCount / $this->dailyLimit) * 100 : 0) }}%">
                </div>
            </div>
            @if($this->limitReached)
                <p class="mt-2 text-sm text-mk-danger">You have reached your daily query limit.</p>
            @endif
        </div>
    @endif

    <div class="mk-card p-4 sm:p-8">
        <h3 class="text-lg font-semibold text-mk-text uppercase tracking-wide mb-5">&#9881;&#65039; Explain a Mechanic</h3>

        <form wire:submit="submit" class="space-y-4">
            <div>
                <x-input-label for="mechanic" value="Mechanic" />
                <textarea
                    id="mechanic"
                    wire:model="mechanic"
                    rows="4"
                    class="mt-1 block w-full rounded-md bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire placeholder:text-mk-muted"
                    placeholder="e.g. Power drain, Brutality, Stun, Fusion"
                    @disabled($this->limitReached)
                ></textarea>
                <x-input-error :messages="$errors->get('mechanic')" class="mt-2" />
            </div>

            <div>
                <x-input-label for="modelSlug" value="LLM Model" />
                <select
                    id="modelSlug"
                    wire:model="modelSlug"
                    class="mt-1 block w-full rounded-md bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire"
                    @disabled($this->limitReached)
                >
                    @foreach($this->availableModels as $m)
                        <option value="{{ $m->slug }}">{{ $m->name }} ({{ $m->parameter_size ?? $m->slug }})</option>
                    @endforeach
                </select>
                <x-input-error :messages="$errors->get('modelSlug')" class="mt-2" />
            </div>

            @if($errorMessage)
                <div class="rounded-md bg-mk-tag-error-bg border border-mk-tag-error-text p-4">
                    <p class="text-sm text-mk-tag-error-text">{{ $errorMessage }}</p>
                </div>
            @endif

            <div class="flex items-center gap-4">
                <x-primary-button type="submit" wire:loading.attr="disabled" :disabled="$this->limitReached">
                    <span wire:loading.remove wire:target="submit">Explain</span>
                    <span wire:loading wire:target="submit" class="flex items-center gap-2">
                        <svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                        </svg>
                        Thinking&hellip;
                    </span>
                </x-primary-button>
            </div>
        </form>
    </div>

    @if($result)
        <div class="space-y-6">
            <div class="mk-card p-4 sm:p-8">
                <h3 class="text-base font-semibold text-mk-fire mb-4">Definition</h3>
                <div class="mk-prose">
                    {!! \App\Support\SafeMarkdown::render($result['definition'] ?? '') !!}
                </div>
            </div>
            <div class="mk-card p-4 sm:p-8">
                <h3 class="text-base font-semibold text-mk-fire mb-4">Recommendations</h3>
                <div class="mk-prose">
                    {!! \App\Support\SafeMarkdown::render($result['recommendations'] ?? '') !!}
                </div>
            </div>
        </div>
    @endif
</div>
