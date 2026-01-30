"""Tests for data loader"""

import pytest
from pathlib import Path

from mkmchat.data.loader import DataLoader


@pytest.fixture
def loader():
    """Create a data loader for testing"""
    loader = DataLoader()
    loader.load_all()
    return loader


def test_load_characters(loader):
    """Test loading character data"""
    characters = loader.get_all_characters()
    assert len(characters) > 0
    
    # Check if Ninjutsu Scorpion exists (new format)
    scorpion = loader.get_character("Ninjutsu Scorpion")
    assert scorpion is not None
    assert scorpion.name == "Ninjutsu Scorpion"
    assert scorpion.class_type == "Martial Artist"
    
    # Check abilities format
    assert len(scorpion.abilities) > 0
    first_ability = scorpion.abilities[0]
    assert hasattr(first_ability, 'type')
    assert hasattr(first_ability, 'effect')
    assert hasattr(first_ability, 'unblockable')


def test_load_equipment(loader):
    """Test loading equipment data"""
    equipment = loader.get_all_equipment()
    assert len(equipment) > 0
    
    # Check if Amulet exists (from new TSV format)
    amulet = loader.get_equipment("Amulet")
    assert amulet is not None
    assert amulet.type == "Accessory"
    assert "RESISTANCE" in amulet.effect


def test_search_characters(loader):
    """Test character search"""
    results = loader.search_characters("scor")
    assert len(results) > 0
    assert any("scorpion" in char.name.lower() for char in results)


def test_case_insensitive_lookup(loader):
    """Test case-insensitive character lookup"""
    char1 = loader.get_character("Ninjutsu Scorpion")
    char2 = loader.get_character("ninjutsu scorpion")
    char3 = loader.get_character("NINJUTSU SCORPION")
    
    assert char1 == char2 == char3
