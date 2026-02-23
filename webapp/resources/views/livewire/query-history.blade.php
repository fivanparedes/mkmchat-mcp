<div>
    @if($viewingId !== null)
        {{-- Result detail view --}}
        <div class="space-y-6 mb-8">
            <div class="flex items-center justify-between mb-2">
                <h3 class="text-lg font-medium text-mk-text">
                    @if($viewingQueryType === 'ask_question')
                        <span class="text-mk-fire">&#128172;</span>
                        <em class="text-mk-fire-light">{{ $viewingStrategy }}</em>
                    @else
                        <span class="text-mk-fire">&#9876;&#65039;</span>
                        Team for: <em class="text-mk-fire-light">{{ $viewingStrategy }}</em>
                    @endif
                </h3>
                <button type="button" wire:click="closeEntry" class="text-sm text-mk-muted hover:text-mk-fire underline transition">
                    &larr; Back to list
                </button>
            </div>

            @if($viewingModelSlug)
                <div class="text-xs text-mk-muted">
                    Model: <span class="font-mono text-mk-text">{{ $viewingModelSlug }}</span>
                </div>
            @endif

            @if($viewingResult)
                @php $partial = $this->resultPartial(); @endphp
                @include($partial, ['result' => $viewingResult, 'strategy' => $viewingStrategy])
            @else
                <div class="mk-card border border-yellow-800 p-4 text-sm text-yellow-400">
                    No result available for this entry.
                </div>
            @endif
        </div>
    @else
        {{-- History list --}}
        <div class="mk-card overflow-hidden">
            @if($histories->isEmpty())
                <div class="p-8 text-center text-mk-muted">
                    <p class="text-lg">No queries yet.</p>
                    <p class="mt-1 text-sm">
                        <a href="{{ route('dashboard') }}" wire:navigate class="text-mk-fire hover:underline">Make your first team suggestion &rarr;</a>
                        &nbsp;or&nbsp;
                        <a href="{{ route('ask') }}" wire:navigate class="text-mk-fire hover:underline">Ask a question &rarr;</a>
                    </p>
                </div>
            @else
                <table class="min-w-full divide-y divide-mk-border">
                    <thead class="bg-mk-surface">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Date</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Type</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Query</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Model</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Status</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-mk-muted uppercase tracking-wider">Action</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-mk-border">
                        @foreach($histories as $history)
                            <tr class="hover:bg-mk-surface transition-colors">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-mk-muted">
                                    {{ $history->created_at->format('M d, Y H:i') }}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    @if(($history->query_type ?? 'team_suggest') === 'ask_question')
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-purple-950 text-purple-300">&#128172; Ask</span>
                                    @else
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-blue-950 text-blue-300">&#9876;&#65039; Team</span>
                                    @endif
                                </td>
                                <td class="px-6 py-4 text-sm text-mk-text max-w-xs">
                                    <span class="line-clamp-2">{{ Str::limit($history->strategy, 100) }}</span>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-xs font-mono text-mk-muted">
                                    {{ $history->model_slug ?? '—' }}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    @if($history->status === 'success')
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-950 text-green-300">Success</span>
                                    @elseif($history->status === 'error')
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-950 text-red-400" title="{{ $history->error_message }}">Error</span>
                                    @else
                                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-950 text-yellow-300">Pending</span>
                                    @endif
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm">
                                    @if($history->status === 'success')
                                        <button wire:click="viewEntry({{ $history->id }})" class="text-mk-fire hover:text-mk-fire-light font-medium transition">
                                            View
                                        </button>
                                    @else
                                        <span class="text-mk-muted">&mdash;</span>
                                    @endif
                                </td>
                            </tr>
                        @endforeach
                    </tbody>
                </table>
                <div class="px-6 py-4 border-t border-mk-border">
                    {{ $histories->links() }}
                </div>
            @endif
        </div>
    @endif
</div>