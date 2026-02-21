@php
    $rarityColors = [
        'Diamond' => ['border' => 'border-cyan-500',   'badge' => 'bg-cyan-950 text-cyan-300',    'header' => 'bg-cyan-950/40'],
        'Gold'    => ['border' => 'border-yellow-500', 'badge' => 'bg-yellow-950 text-yellow-300', 'header' => 'bg-yellow-950/40'],
        'Silver'  => ['border' => 'border-gray-500',   'badge' => 'bg-gray-800 text-gray-300',     'header' => 'bg-gray-900'],
        'Bronze'  => ['border' => 'border-orange-500', 'badge' => 'bg-orange-950 text-orange-300', 'header' => 'bg-orange-950/40'],
    ];
    $rarity = $char['rarity'] ?? 'Silver';
    $colors = $rarityColors[$rarity] ?? $rarityColors['Silver'];

    $slotIcons = [
        'weapon'    => '&#9876;&#65039;',
        'armor'     => '&#128737;&#65039;',
        'accessory' => '&#128142;',
    ];
@endphp

<div class="bg-mk-card border-2 {{ $colors['border'] }} rounded-lg overflow-hidden flex flex-col shadow-lg">
    {{-- Character header --}}
    <div class="{{ $colors['header'] }} p-4 flex items-center gap-4">
        <img src="{{ asset('images/fighter-placeholder.svg') }}"
             alt="Fighter"
             class="w-16 h-16 rounded-full border-2 {{ $colors['border'] }} object-cover flex-shrink-0" />
        <div class="min-w-0">
            <h4 class="text-base font-bold text-white truncate">{{ $char['name'] }}</h4>
            <span class="inline-block mt-1 px-2 py-0.5 rounded text-xs font-semibold {{ $colors['badge'] }}">
                {{ $rarity }}
            </span>
        </div>
    </div>

    {{-- Passive --}}
    @if(!empty($char['passive']))
        <div class="px-4 py-3 border-b border-mk-border">
            <p class="text-xs font-semibold text-mk-muted uppercase tracking-wide mb-1">Passive</p>
            <p class="text-sm text-mk-text leading-snug">{{ $char['passive'] }}</p>
        </div>
    @endif

    {{-- Equipment --}}
    @if(!empty($char['equipment']))
        <div class="px-4 py-3 flex-1">
            <p class="text-xs font-semibold text-mk-muted uppercase tracking-wide mb-2">Equipment</p>
            <div class="space-y-3">
                @foreach($char['equipment'] as $equip)
                    <div class="flex gap-3 items-start">
                        <img src="{{ asset('images/equipment-placeholder.svg') }}"
                             alt="{{ $equip['slot'] ?? 'Equipment' }}"
                             class="w-10 h-10 rounded border border-mk-border flex-shrink-0 object-cover" />
                        <div class="min-w-0">
                            <div class="flex items-center gap-1">
                                <span class="text-sm">{!! $slotIcons[$equip['slot'] ?? ''] ?? '&#128295;' !!}</span>
                                <span class="text-sm font-medium text-mk-text truncate">{{ $equip['name'] }}</span>
                            </div>
                            <p class="text-xs text-mk-muted mt-0.5 leading-snug">{{ $equip['effect'] }}</p>
                        </div>
                    </div>
                @endforeach
            </div>
        </div>
    @endif
</div>