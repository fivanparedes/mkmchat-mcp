@php
    $definition = is_array($result) ? ($result['definition'] ?? '') : '';
    $recommendations = is_array($result) ? ($result['recommendations'] ?? '') : '';
@endphp

<div class="space-y-6">
    <div class="mk-card p-4 sm:p-6">
        <h4 class="text-sm font-semibold text-mk-fire mb-3">Definition</h4>
        <div class="mk-prose text-sm">
            {!! Str::markdown($definition) !!}
        </div>
    </div>
    <div class="mk-card p-4 sm:p-6">
        <h4 class="text-sm font-semibold text-mk-fire mb-3">Recommendations</h4>
        <div class="mk-prose text-sm">
            {!! Str::markdown($recommendations) !!}
        </div>
    </div>
</div>
