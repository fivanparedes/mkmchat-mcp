<?php

namespace App\Livewire;

use App\Models\QueryHistory;
use Illuminate\Support\Facades\Auth;
use Livewire\Component;
use Livewire\WithPagination;

class QueryHistoryList extends Component
{
    use WithPagination;

    public ?int $viewingId = null;
    public ?array $viewingResult = null;
    public ?string $viewingStrategy = null;
    public ?string $viewingQueryType = null;
    public ?string $viewingModelSlug = null;

    public function viewEntry(int $id): void
    {
        $history = QueryHistory::where('user_id', Auth::id())
            ->where('id', $id)
            ->firstOrFail();

        $this->viewingId        = $history->id;
        $this->viewingResult    = $history->response;
        $this->viewingStrategy  = $history->strategy;
        $this->viewingQueryType = $history->query_type ?? 'team_suggest';
        $this->viewingModelSlug = $history->model_slug ?? 'mistral-nemo:12b';
    }

    public function closeEntry(): void
    {
        $this->viewingId        = null;
        $this->viewingResult    = null;
        $this->viewingStrategy  = null;
        $this->viewingQueryType = null;
        $this->viewingModelSlug = null;
        $this->resetPage();
    }

    /**
     * Return the blade partial name for the current query type.
     * Add a new match arm here when new query types are introduced.
     */
    public function resultPartial(): string
    {
        return match($this->viewingQueryType) {
            'ask_question' => 'livewire.partials.result-ask-question',
            default        => 'livewire.partials.result-team-suggest',
        };
    }

    public function render()
    {
        $histories = QueryHistory::where('user_id', Auth::id())
            ->latest()
            ->paginate(10);

        return view('livewire.query-history', compact('histories'));
    }
}
