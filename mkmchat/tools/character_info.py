"""Character information tool"""

from mkmchat.data.loader import get_data_loader


async def get_character_info(character_name: str) -> dict:
    """
    Get detailed information about a character
    
    Args:
        character_name: Name of the character to look up
        
    Returns:
        MCP response with character information
    """
    loader = get_data_loader()
    
    # Try exact match first
    character = loader.get_character(character_name)
    
    # If not found, try fuzzy search
    if not character:
        matches = loader.search_characters_fuzzy(character_name)
        if not matches:
            # Provide helpful suggestions
            all_chars = loader.get_all_characters()
            suggestions = [c.name for c in all_chars if character_name.lower().split()[0] in c.name.lower()][:5]
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"\n\nDid you mean: {', '.join(suggestions)}?"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Character '{character_name}' not found. Please check the spelling.{suggestion_text}"
                    }
                ]
            }
        character = matches[0]
        
    # Format character information
    abilities_text = "\n".join([
        f"- **{ability.name}** ({ability.type}): "
        f"{ability.effect or 'N/A'} - {'Unblockable' if ability.unblockable else 'Blockable'}"
        for ability in character.abilities
    ])
    
    # Handle passive (can be single object, list, or None)
    passive_text = "None"
    if character.passive:
        if isinstance(character.passive, list):
            passive_text = "\n".join([
                f"- **{p.name}**: {p.description}\n  Tags: {', '.join(p.tags)}"
                for p in character.passive
            ])
        else:
            passive_text = f"**{character.passive.name}**: {character.passive.description}\nTags: {', '.join(character.passive.tags)}"
    
    synergy_text = character.synergy or "None"
    
    response_text = f"""# {character.name}

**Class**: {character.class_type}
**Rarity**: {character.rarity}
**Tier**: {character.tier} (Practical Usefulness)

## Stats
- Attack: {character.stats.attack}
- Health: {character.stats.health}
- Toughness: {character.stats.toughness}
- Recovery: {character.stats.recovery}

## Abilities
{abilities_text}

## Passive
{passive_text}

## Synergy
{synergy_text}
"""
    
    return {
        "content": [
            {
                "type": "text",
                "text": response_text
            }
        ]
    }
