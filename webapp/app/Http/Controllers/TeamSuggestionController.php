<?php

namespace App\Http\Controllers;

use App\Models\QueryHistory;
use App\Services\MkmApiService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use RuntimeException;

class TeamSuggestionController extends Controller
{
    public function __construct(private MkmApiService $apiService) {}

    /**
     * Submit a team suggestion request.
     * Called by the Livewire component via action.
     */
    public function suggest(Request $request): array
    {
        $validated = $request->validate([
            'strategy'         => ['required', 'string', 'min:3', 'max:2000'],
            'owned_characters' => ['nullable', 'string', 'max:1000'],
        ]);

        /** @var \App\Models\User $user */
        $user = Auth::user();

        // Enforce daily limit if configured.
        $limit = (int) config('mkm.daily_limit', 0);
        if ($limit > 0 && $user->todayQueryCount() >= $limit) {
            abort(429, "You have reached your daily limit of {$limit} queries.");
        }

        // Parse optional owned characters from comma-separated string.
        $ownedCharacters = [];
        if (!empty($validated['owned_characters'])) {
            $ownedCharacters = array_filter(
                array_map('trim', explode(',', $validated['owned_characters']))
            );
        }

        // Persist as a pending record first.
        $history = QueryHistory::create([
            'user_id'          => $user->id,
            'strategy'         => $validated['strategy'],
            'owned_characters' => array_values($ownedCharacters),
            'status'           => 'pending',
        ]);

        try {
            $response = $this->apiService->suggestTeam($validated['strategy'], array_values($ownedCharacters));

            $history->update([
                'response' => $response,
                'status'   => 'success',
            ]);

            return ['status' => 'success', 'historyId' => $history->id, 'response' => $response];
        } catch (RuntimeException $e) {
            $history->update([
                'status'        => 'error',
                'error_message' => $e->getMessage(),
            ]);

            return ['status' => 'error', 'message' => $e->getMessage(), 'historyId' => $history->id];
        }
    }
}
