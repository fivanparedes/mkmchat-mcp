{{--
    Team Suggest result partial.
    Variables: $result (array), $strategy (string)
--}}
@if(!empty($result['strategy']))
    <div class="mk-card border-l-4 border-mk-fire p-4 sm:p-6">
        <h3 class="text-base font-semibold text-mk-fire mb-2">&#9876;&#65039; Team Strategy</h3>
        <p class="text-mk-text leading-relaxed">{{ $result['strategy'] }}</p>
    </div>
@endif

<div class="grid grid-cols-1 gap-6 sm:grid-cols-3">
    @foreach(['char1', 'char2', 'char3'] as $charKey)
        @if(isset($result[$charKey]))
            @include('livewire.partials.character-card', ['char' => $result[$charKey]])
        @endif
    @endforeach
</div>