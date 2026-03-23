<?php

namespace App\Livewire;

use App\Models\Conversation;
use App\Models\ConversationMessage;
use App\Models\LlmModel;
use App\Models\User;
use App\Services\MkmApiService;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\Facades\RateLimiter;
use Livewire\Attributes\Computed;
use Livewire\Component;
use RuntimeException;

class Chat extends Component
{
    public ?int $activeConversationId = null;
    public string $message = '';
    public string $modelSlug = '';
    public bool $loading = false;
    public ?string $errorMessage = null;

    public ?int $renameConversationId = null;
    public string $renameTitle = '';

    #[Computed]
    public function dailyLimit(): int
    {
        return (int) config('mkm.daily_limit', 0);
    }

    #[Computed]
    public function todayCount(): int
    {
        return Auth::user()->todayQueryCount();
    }

    #[Computed]
    public function limitReached(): bool
    {
        return $this->dailyLimit > 0 && $this->todayCount >= $this->dailyLimit;
    }

    #[Computed]
    public function availableModels()
    {
        return LlmModel::active()->orderBy('name')->get();
    }

    /**
     * @return Collection<int, Conversation>
     */
    #[Computed]
    public function conversations(): Collection
    {
        return Conversation::query()
            ->where('user_id', Auth::id())
            ->orderByDesc('last_message_at')
            ->orderByDesc('updated_at')
            ->get();
    }

    /**
     * @return Collection<int, ConversationMessage>
     */
    #[Computed]
    public function activeMessages(): Collection
    {
        if (!$this->activeConversationId) {
            return new Collection();
        }

        $conversation = $this->loadConversationOrFail($this->activeConversationId);

        return $conversation->messages()
            ->orderBy('id')
            ->get();
    }

    public function mount(): void
    {
        $default = LlmModel::active()
            ->where('slug', 'llama3.2:3b')
            ->first() ?? LlmModel::active()->first();
        $this->modelSlug = $default?->slug ?? '';

        $latestConversation = Conversation::query()
            ->where('user_id', Auth::id())
            ->orderByDesc('last_message_at')
            ->orderByDesc('updated_at')
            ->first();

        if ($latestConversation) {
            $this->activeConversationId = $latestConversation->id;
        }
    }

    public function startConversation(): void
    {
        Gate::authorize('chat');

        /** @var User $user */
        $user = Auth::user();

        $conversation = Conversation::create([
            'user_id' => $user->id,
            'title' => 'New chat',
        ]);

        $this->activeConversationId = $conversation->id;
        $this->renameConversationId = null;
        $this->renameTitle = '';
        $this->errorMessage = null;
    }

    public function selectConversation(int $conversationId): void
    {
        Gate::authorize('chat');

        $conversation = $this->loadConversationOrFail($conversationId);

        $this->activeConversationId = $conversation->id;
        $this->errorMessage = null;
        $this->renameConversationId = null;
        $this->renameTitle = '';
    }

    public function beginRename(int $conversationId): void
    {
        $conversation = $this->loadConversationOrFail($conversationId);

        $this->renameConversationId = $conversation->id;
        $this->renameTitle = $conversation->title;
    }

    public function cancelRename(): void
    {
        $this->renameConversationId = null;
        $this->renameTitle = '';
    }

    public function deleteConversation(int $conversationId): void
    {
        Gate::authorize('chat');

        $conversation = $this->loadConversationOrFail($conversationId);
        $wasActive = $this->activeConversationId === $conversation->id;

        $conversation->delete();

        if ($wasActive) {
            $nextConversation = Conversation::query()
                ->where('user_id', Auth::id())
                ->orderByDesc('last_message_at')
                ->orderByDesc('updated_at')
                ->first();

            $this->activeConversationId = $nextConversation?->id;
        }

        if ($this->renameConversationId === $conversationId) {
            $this->renameConversationId = null;
            $this->renameTitle = '';
        }

        $this->errorMessage = null;
    }

    public function saveRename(): void
    {
        Gate::authorize('chat');

        $this->validate([
            'renameTitle' => ['required', 'string', 'min:2', 'max:160'],
        ]);

        if (!$this->renameConversationId) {
            return;
        }

        $conversation = $this->loadConversationOrFail($this->renameConversationId);
        $conversation->update([
            'title' => trim($this->renameTitle),
        ]);

        $this->renameConversationId = null;
        $this->renameTitle = '';
    }

    public function send(MkmApiService $apiService): void
    {
        Gate::authorize('chat');

        $this->validate([
            'message' => ['required', 'string', 'min:1', 'max:4000'],
            'modelSlug' => ['required', 'string'],
        ]);

        if ($this->limitReached) {
            $this->errorMessage = "You have reached your daily limit of {$this->dailyLimit} queries.";
            return;
        }

        /** @var User $user */
        $user = Auth::user();

        $maxAttempts = max(1, (int) config('mkm.web_rate_limit_per_minute', 10));
        $rateLimitKey = $this->rateLimitKey($user);

        if (RateLimiter::tooManyAttempts($rateLimitKey, $maxAttempts)) {
            $remainingSeconds = RateLimiter::availableIn($rateLimitKey);
            $this->errorMessage = "Too many requests. Try again in {$remainingSeconds} seconds.";
            return;
        }

        RateLimiter::hit($rateLimitKey, 60);

        $this->loading = true;
        $this->errorMessage = null;

        $conversation = $this->activeConversationId
            ? $this->loadConversationOrFail($this->activeConversationId)
            : Conversation::create([
                'user_id' => $user->id,
                'title' => $this->generateConversationTitle($this->message),
            ]);

        if (!$this->activeConversationId) {
            $this->activeConversationId = $conversation->id;
        }

        $prompt = trim($this->message);

        ConversationMessage::create([
            'conversation_id' => $conversation->id,
            'role' => 'user',
            'content' => $prompt,
            'model_slug' => $this->modelSlug,
        ]);

        $conversation->update([
            'last_message_at' => now(),
            'title' => $conversation->title === 'New chat'
                ? $this->generateConversationTitle($prompt)
                : $conversation->title,
        ]);

        try {
            $summaryMessageCount = (int) $conversation->summary_message_count;

            $allMessages = $conversation->messages()
                ->orderBy('id')
                ->get(['role', 'content']);

            $messages = $allMessages
                ->slice($summaryMessageCount)
                ->values()
                ->map(fn (ConversationMessage $message) => [
                    'role' => $message->role,
                    'content' => $message->content,
                ])
                ->all();

            $response = $apiService->chat(
                $prompt,
                $messages,
                $conversation->summary_text,
                $summaryMessageCount,
                $this->modelSlug,
            );

            ConversationMessage::create([
                'conversation_id' => $conversation->id,
                'role' => 'assistant',
                'content' => $response['text'],
                'model_slug' => $this->modelSlug,
            ]);

            $conversation->update([
                'summary_text' => $response['summary_text'] ?: $conversation->summary_text,
                'summary_message_count' => $response['summary_message_count'],
                'last_message_at' => now(),
            ]);

            $this->message = '';
        } catch (RuntimeException $e) {
            $conversation->update([
                'last_message_at' => now(),
            ]);
            $this->errorMessage = $e->getMessage();
        } finally {
            $this->loading = false;
        }
    }

    public function render()
    {
        return view('livewire.chat');
    }

    private function loadConversationOrFail(int $conversationId): Conversation
    {
        return Conversation::query()
            ->where('user_id', Auth::id())
            ->where('id', $conversationId)
            ->firstOrFail();
    }

    private function generateConversationTitle(string $rawMessage): string
    {
        $title = trim(preg_replace('/\s+/', ' ', $rawMessage) ?? '');
        if ($title === '') {
            return 'New chat';
        }

        return mb_substr($title, 0, 80);
    }

    private function rateLimitKey(User $user): string
    {
        $ip = request()->ip() ?? 'unknown';
        return "chat:{$user->id}:{$ip}";
    }
}
