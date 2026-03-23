<div class="h-[calc(100dvh-15rem)] min-h-[34rem] max-h-[calc(100dvh-15rem)] flex flex-col gap-6 min-h-0" x-data="{ draftMessage: $wire.entangle('message') }">
    @if($this->dailyLimit > 0)
        <div class="mk-card p-4 sm:p-6">
            <div class="flex items-center justify-between mb-2">
                <span class="text-sm font-medium text-mk-muted">Daily Queries Used</span>
                <span class="text-sm text-mk-muted">{{ $this->todayCount }} / {{ $this->dailyLimit }}</span>
            </div>
            <div class="w-full bg-mk-border rounded-full h-2">
                <div class="h-2 rounded-full {{ $this->limitReached ? 'bg-red-600' : 'bg-mk-fire' }}"
                     style="width: {{ min(100, $this->dailyLimit > 0 ? ($this->todayCount / $this->dailyLimit) * 100 : 0) }}%"></div>
            </div>
            @if($this->limitReached)
                <p class="mt-2 text-sm text-red-400">You have reached your daily query limit.</p>
            @endif
        </div>
    @endif

    <div class="mk-card p-0 overflow-hidden flex-1 min-h-0">
        <div class="grid grid-cols-1 lg:grid-cols-12 h-full overflow-hidden">
            <aside class="lg:col-span-4 border-b lg:border-b-0 lg:border-r border-mk-border bg-mk-surface/70 p-4 sm:p-5 space-y-4 flex flex-col min-h-0">
                <div class="flex items-center justify-between gap-3">
                    <h3 class="text-sm font-semibold tracking-wide uppercase text-mk-muted">Conversations</h3>
                    <x-primary-button wire:click="startConversation" type="button">New chat</x-primary-button>
                </div>

                <div class="space-y-2 overflow-y-auto pr-1 flex-1 min-h-0">
                    @forelse($this->conversations as $conversation)
                        <div class="rounded-lg border {{ $activeConversationId === $conversation->id ? 'border-mk-fire bg-mk-card' : 'border-mk-border bg-mk-surface' }} p-3">
                            @if($renameConversationId === $conversation->id)
                                <div class="space-y-2">
                                    <x-text-input wire:model="renameTitle" type="text" class="block w-full" maxlength="160" />
                                    <div class="flex gap-2">
                                        <x-primary-button wire:click="saveRename" type="button">Save</x-primary-button>
                                        <button wire:click="cancelRename" type="button" class="text-sm text-mk-muted hover:text-mk-fire transition">Cancel</button>
                                    </div>
                                    <x-input-error :messages="$errors->get('renameTitle')" />
                                </div>
                            @else
                                <div class="flex items-start justify-between gap-2">
                                    <button
                                        wire:click="selectConversation({{ $conversation->id }})"
                                        type="button"
                                        class="text-left text-sm font-medium text-mk-text hover:text-mk-fire transition line-clamp-2"
                                    >
                                        {{ $conversation->title }}
                                    </button>
                                    <div class="flex items-center gap-2">
                                        <button wire:click="beginRename({{ $conversation->id }})" type="button" class="text-xs text-mk-muted hover:text-mk-fire transition">Rename</button>
                                        <button
                                            wire:click="deleteConversation({{ $conversation->id }})"
                                            onclick="return confirm('Delete this chat conversation?');"
                                            type="button"
                                            class="text-xs text-red-400 hover:text-red-300 transition"
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                                <p class="mt-2 text-xs text-mk-muted">{{ optional($conversation->last_message_at)->diffForHumans() ?? 'No messages yet' }}</p>
                            @endif
                        </div>
                    @empty
                        <p class="text-sm text-mk-muted">No conversations yet. Start a new chat to begin.</p>
                    @endforelse
                </div>
            </aside>

            <section class="lg:col-span-8 flex flex-col bg-mk-card/40 min-h-0 overflow-hidden">
                <div class="px-4 py-3 sm:px-6 sm:py-4 border-b border-mk-border">
                    <h3 class="text-base sm:text-lg font-semibold text-mk-text leading-tight">
                        {{ $activeConversationId ? optional($this->conversations->firstWhere('id', $activeConversationId))->title : 'New chat' }}
                    </h3>
                </div>

                <div class="flex-1 overflow-y-scroll p-4 sm:p-6 space-y-4 min-h-0">
                    @if($activeConversationId)
                        @forelse($this->activeMessages as $msg)
                            <div class="flex {{ $msg->role === 'assistant' ? 'justify-start' : 'justify-end' }}">
                                <article class="max-w-[90%] sm:max-w-[80%] rounded-2xl px-4 py-3 border {{ $msg->role === 'assistant' ? 'bg-mk-surface border-mk-border text-mk-text' : 'bg-mk-fire/15 border-mk-fire/60 text-orange-100' }}">
                                    <p class="text-xs uppercase tracking-wide mb-2 {{ $msg->role === 'assistant' ? 'text-mk-muted' : 'text-orange-300' }}">{{ $msg->role === 'assistant' ? 'Assistant' : 'You' }}</p>
                                    <div class="mk-prose text-sm leading-relaxed">
                                        {!! \App\Support\SafeMarkdown::render($msg->content) !!}
                                    </div>
                                    @if($msg->role === 'assistant')
                                        <p class="mt-3 text-[10px] text-mk-muted/80">
                                            Model: {{ $msg->model_slug ?: 'N/A' }}
                                        </p>
                                    @endif
                                </article>
                            </div>
                        @empty
                            <div class="h-full flex items-center justify-center">
                                <p class="text-sm text-mk-muted">Send a message to start this conversation.</p>
                            </div>
                        @endforelse
                    @else
                        <div class="h-full flex items-center justify-center">
                            <p class="text-sm text-mk-muted">Create a new chat to start asking questions.</p>
                        </div>
                    @endif

                    @if($loading)
                        <div class="flex justify-end" x-show="draftMessage && draftMessage.trim().length > 0">
                            <article class="max-w-[90%] sm:max-w-[80%] rounded-2xl px-4 py-3 border bg-mk-fire/15 border-mk-fire/60 text-orange-100">
                                <p class="text-xs uppercase tracking-wide mb-2 text-orange-300">You</p>
                                <p class="text-sm leading-relaxed" x-text="draftMessage"></p>
                            </article>
                        </div>

                        <div class="flex justify-start">
                            <div class="max-w-[80%] rounded-2xl px-4 py-3 border bg-mk-surface border-mk-border text-mk-text">
                                <p class="text-xs uppercase tracking-wide mb-2 text-mk-muted">Assistant</p>
                                <p class="text-sm text-mk-muted flex items-center gap-2">
                                    <svg class="animate-spin h-4 w-4 text-mk-fire" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                                    </svg>
                                    Thinking...
                                </p>
                            </div>
                        </div>
                    @endif
                </div>

                <div class="p-4 sm:p-6 border-t border-mk-border bg-mk-surface/50 shrink-0">
                    @if($errorMessage)
                        <div class="rounded-md bg-red-950 border border-red-800 p-3 mb-3">
                            <p class="text-sm text-red-400">{{ $errorMessage }}</p>
                        </div>
                    @endif

                    <form wire:submit="send" class="space-y-3">
                        <textarea
                            id="chatMessage"
                            wire:model="message"
                            rows="3"
                            class="block w-full rounded-xl bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire placeholder:text-mk-muted"
                            placeholder="Ask about strategy, mechanics, teams, or equipment..."
                            @disabled($loading || $this->limitReached)
                        ></textarea>
                        <x-input-error :messages="$errors->get('message')" class="mt-2" />

                        <div class="flex items-end justify-between gap-3">
                            <div class="w-full sm:w-72">
                                <x-input-label for="chatModelSlugBottom" value="LLM Model" />
                                <select
                                    id="chatModelSlugBottom"
                                    wire:model="modelSlug"
                                    class="mt-1 block w-full rounded-md bg-mk-surface border-mk-border text-mk-text shadow-sm focus:border-mk-fire focus:ring-mk-fire"
                                    @disabled($loading || $this->limitReached)
                                >
                                    @foreach($this->availableModels as $m)
                                        <option value="{{ $m->slug }}">{{ $m->name }} ({{ $m->parameter_size ?? $m->slug }})</option>
                                    @endforeach
                                </select>
                                <x-input-error :messages="$errors->get('modelSlug')" class="mt-2" />
                            </div>

                            <div class="shrink-0">
                                <x-primary-button type="submit" class="h-11 px-6 min-w-[7.5rem] justify-center" wire:loading.attr="disabled" :disabled="$loading || $this->limitReached">
                                    <span wire:loading.remove wire:target="send">Send</span>
                                    <span wire:loading wire:target="send">Sending...</span>
                                </x-primary-button>
                            </div>
                        </div>
                    </form>
                </div>
            </section>
        </div>
    </div>
</div>
