<?php

namespace App\Livewire;

use App\Models\QueryHistory;
use App\Services\MkmApiService;
use Illuminate\Support\Facades\Auth;
use Livewire\Attributes\Computed;
use Livewire\Component;
use RuntimeException;

class TeamSuggestion extends Component
{
    // Form fields
    public string $strategy = '';
    public string $ownedCharacters = '';

    // UI state
    public bool $loading = false;
    public ?string $errorMessage = null;

    // Result
    public ?array $result = null;
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

    public function submit(MkmApiService $apiService): void
    {
        $this->validate([
            'strategy'        => ['required', 'string', 'min:3', 'max:2000'],
            'ownedCharacters' => ['nullable', 'string', 'max:1000'],
        ]);

        if ($this->limitReached) {
            $this->errorMessage = "You have reached your daily limit of {$this->dailyLimit} queries.";
            return;
        }

        $this->loading = true;
        $this->errorMessage = null;
        $this->result = null;

        // Parse comma-separated owned characters.
        $owned = [];
        if (!empty(trim($this->ownedCharacters))) {
            $owned = array_values(array_filter(
                array_map('trim', explode(',', $this->ownedCharacters))
            ));
        }

        /** @var \App\Models\User $user */
        $user = Auth::user();

        $history = QueryHistory::create([
            'user_id'          => $user->id,
            'query_type'       => 'team_suggest',
            'strategy'         => $this->strategy,
            'owned_characters' => $owned,
            'status'           => 'pending',
        ]);

        try {
            $response = $apiService->suggestTeam($this->strategy, $owned);

            $history->update([
                'response' => $response,
                'status'   => 'success',
            ]);

            $this->result    = $response;
            $this->historyId = $history->id;
        } catch (RuntimeException $e) {
            $history->update([
                'status'        => 'error',
                'error_message' => $e->getMessage(),
            ]);

            $this->errorMessage = $e->getMessage();
            $this->historyId    = $history->id;
        } finally {
            $this->loading = false;
        }
    }

    public function render()
    {
        return view('livewire.team-suggestion');
    }
}
