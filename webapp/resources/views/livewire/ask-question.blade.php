<div class="space-y-6">
    {{-- Daily usage meter --}}
    @if($this->dailyLimit > 0)
        <div class="mk-card p-4 sm:p-6">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-mk-muted">Daily Queries Used</span>
                <span class="text-sm text-mk-muted">{{ $this->todayCount }} / {{ $this->dailyLimit }}</span>
            </div>
            <div class="w-full bg-mk-border rounded-full h-2">
                <div class="h-2 rounded-full {{ $this->limitReached ? 'bg-red-600' : 'bg-mk-fire' }}"
                     style="width: {{ min(100, $this->dailyLimit > 0 ? ($this->todayCount / $this->dailyLimit) * 100 : 0) }}%">
                </div>
            </div>
            @if($this->limitReached)
                <p class="mt-2 text-sm text-red-400">You have reached your daily query limit.</p>
            @endif
        </div>
    @endif

    {{-- Query form --}}
    <div class="mk-card p-4 sm:p-8">
        <h3 class="text-lg font-semibold text-mk-text uppercase tracking-wide mb-5">&#128172; Ask a Question</h3>

        <form wire:submit="submit" class="space-y-4">
            <div>
                <x-input-label for="question" value="Your Question" />
                <textarea
                    id="question"
                    wire:model="question"
                    rows="4"
                    class="mt-1 block w-full rounded-md bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire placeholder:text-mk-muted"
                    placeholder="e.g. What is the best strategy for Tower of Power? How does X-Ray work?"
                    @disabled($this->limitReached)
                ></textarea>
                <x-input-error :messages="$errors->get('question')" class="mt-2" />
            </div>

            @if($errorMessage)
                <div class="rounded-md bg-red-950 border border-red-800 p-4">
                    <p class="text-sm text-red-400">{{ $errorMessage }}</p>
                </div>
            @endif

            <div class="flex items-center gap-4">
                <x-primary-button type="submit" wire:loading.attr="disabled" :disabled="$this->limitReached">
                    <span wire:loading.remove wire:target="submit">Ask</span>
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

    {{-- Answer --}}
    @if($result)
        <div class="mk-card p-4 sm:p-8">
            <h3 class="text-base font-semibold text-mk-fire mb-4 flex items-center gap-2">
                &#128172; Answer
            </h3>
            <div class="mk-prose">
                {!! Str::markdown($result) !!}
            </div>
        </div>
    @endif
</div>