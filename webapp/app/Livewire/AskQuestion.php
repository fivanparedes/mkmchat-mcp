<?php

namespace App\Livewire;

use App\Models\LlmModel;
use App\Models\QueryHistory;
use App\Models\User;
use App\Services\MkmApiService;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Gate;
use Illuminate\Support\Facades\RateLimiter;
use Livewire\Attributes\Computed;
use Livewire\Component;
use RuntimeException;

class AskQuestion extends Component
{
    public string $question = '';
    public string $modelSlug = '';
    public bool $loading = false;
    public ?string $errorMessage = null;
    public ?string $result = null;
    public ?int $historyId = null;

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

    public function mount(): void
    {
        $default = LlmModel::active()
            ->where('slug', 'llama3.2:3b')
            ->first() ?? LlmModel::active()->first();
        $this->modelSlug = $default?->slug ?? '';
    }

    public function submit(MkmApiService $apiService): void
    {
        Gate::authorize('ask-question');

        $this->validate([
            'question'  => ['required', 'string', 'min:3', 'max:2000'],
            'modelSlug' => ['required', 'string'],
        ]);

        if ($this->limitReached) {
            $this->errorMessage = "You have reached your daily limit of {$this->dailyLimit} queries.";
            return;
        }

        $this->loading = true;
        $this->errorMessage = null;
        $this->result = null;

        /** @var \App\Models\User $user */
        $user = Auth::user();

        $maxAttempts = max(1, (int) config('mkm.web_rate_limit_per_minute', 10));
        $rateLimitKey = $this->rateLimitKey($user);
        if (RateLimiter::tooManyAttempts($rateLimitKey, $maxAttempts)) {
            $remainingSeconds = RateLimiter::availableIn($rateLimitKey);
            $this->errorMessage = "Too many requests. Try again in {$remainingSeconds} seconds.";
            return;
        }
        RateLimiter::hit($rateLimitKey, 60);

        $history = QueryHistory::create([
            'user_id'    => $user->id,
            'query_type' => 'ask_question',
            'strategy'   => $this->question,
            'model_slug' => $this->modelSlug,
            'status'     => 'pending',
        ]);

        try {
            $text = $apiService->askQuestion($this->question, $this->modelSlug);
            $history->update(['response' => ['text' => $text], 'status' => 'success']);
            $this->result    = $text;
            $this->historyId = $history->id;
        } catch (RuntimeException $e) {
            $history->update(['status' => 'error', 'error_message' => $e->getMessage()]);
            $this->errorMessage = $e->getMessage();
            $this->historyId    = $history->id;
        } finally {
            $this->loading = false;
        }
    }

    public function render()
    {
        return view('livewire.ask-question');
    }

    private function rateLimitKey(User $user): string
    {
        $ip = request()->ip() ?? 'unknown';
        return "ask-question:{$user->id}:{$ip}";
    }
}
