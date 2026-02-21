{{--
    Ask Question result partial.
    Variables: $result (array), $strategy (string)
--}}
<div class="mk-card p-4 sm:p-8">
    <h3 class="text-base font-semibold text-mk-fire mb-4">&#128172; Answer</h3>
    <div class="mk-prose">
        {!! Str::markdown($result['text'] ?? '') !!}
    </div>
</div>