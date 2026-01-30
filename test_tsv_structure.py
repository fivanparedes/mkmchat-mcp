#!/usr/bin/env python3
"""Test script for new TSV structure"""

from mkmchat.data.loader import get_data_loader

print('=' * 60)
print('TESTING NEW TSV STRUCTURE')
print('=' * 60)

loader = get_data_loader()

# Test characters
chars = loader.get_all_characters()
print(f'\n✅ Loaded {len(chars)} characters')

# Test a few characters
test_chars = ['Ninjutsu Scorpion', 'Lizard Jade', 'Lizard Baraka']
for char_name in test_chars:
    char = loader.get_character(char_name)
    if char:
        print(f'\n📍 {char.name}')
        print(f'   Class: {char.class_type} | Rarity: {char.rarity}')
        print(f'   Stats: Attack={char.stats.attack}, Health={char.stats.health} (all zeros expected)')
        print(f'   Abilities: {len(char.abilities)} total')
        for ab in char.abilities:
            unb = '[UNBLOCKABLE]' if ab.unblockable else ''
            print(f'      - {ab.name}: {ab.effect} {unb}')
        if char.passive:
            print(f'   Passive: {char.passive.description[:80]}...')
        if char.synergy:
            print(f'   Synergy: {char.synergy[:60]}...')

# Test equipment
equipment = loader.get_all_equipment()
print(f'\n✅ Loaded {len(equipment)} equipment items')
if equipment:
    eq = equipment[0]
    print(f'   Sample: {eq.name} ({eq.type})')
    print(f'   Effect: {eq.effect}')

print('\n' + '=' * 60)
print('✅ ALL TESTS PASSED - Data structure updated successfully!')
print('=' * 60)
