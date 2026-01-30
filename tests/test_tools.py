"""Tests for MCP tools"""

import pytest

from mkmchat.tools.character_info import get_character_info
from mkmchat.tools.equipment_info import get_equipment_info
from mkmchat.tools.team_suggest import suggest_team


@pytest.mark.asyncio
async def test_get_character_info():
    """Test character info tool"""
    result = await get_character_info("Ninjutsu Scorpion")
    
    assert "content" in result
    assert len(result["content"]) > 0
    assert "Ninjutsu Scorpion" in result["content"][0]["text"]
    assert "Martial Artist" in result["content"][0]["text"]
    
    # Check for new format fields
    assert "Unblockable" in result["content"][0]["text"] or "Blockable" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_get_character_info_not_found():
    """Test character info with non-existent character"""
    result = await get_character_info("NonExistentCharacter123")
    
    assert "content" in result
    assert "not found" in result["content"][0]["text"].lower()


@pytest.mark.asyncio
async def test_get_equipment_info():
    """Test equipment info tool"""
    result = await get_equipment_info("Shuriken")
    
    assert "content" in result
    assert "Shuriken" in result["content"][0]["text"]
    assert "Weapon" in result["content"][0]["text"]


@pytest.mark.asyncio
async def test_suggest_team():
    """Test team suggestion tool"""
    result = await suggest_team(strategy="high damage")
    
    assert "content" in result
    assert len(result["content"]) > 0
    text = result["content"][0]["text"]
    assert "Team" in text
    assert "Equipment" in text  # Check that equipment recommendations are included
    

@pytest.mark.asyncio
async def test_suggest_team_with_required_character():
    """Test team suggestion with required character"""
    result = await suggest_team(
        strategy="high damage",
        required_character="Ninjutsu Scorpion"
    )
    
    assert "content" in result
    text = result["content"][0]["text"]
    assert "Scorpion" in text
