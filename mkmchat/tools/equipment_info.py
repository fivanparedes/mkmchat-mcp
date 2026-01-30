"""Equipment information tool"""

from mkmchat.data.loader import get_data_loader


async def get_equipment_info(equipment_name: str) -> dict:
    """
    Get detailed information about equipment
    
    Args:
        equipment_name: Name of the equipment to look up
        
    Returns:
        MCP response with equipment information
    """
    loader = get_data_loader()
    
    # Try exact match first
    equipment = loader.get_equipment(equipment_name)
    
    # If not found, try fuzzy search
    if not equipment:
        matches = loader.search_equipment_fuzzy(equipment_name)
        if not matches:
            # Provide helpful suggestions
            all_equip = loader.get_all_equipment()
            first_word = equipment_name.lower().split()[0] if equipment_name.split() else equipment_name.lower()
            suggestions = [e.name for e in all_equip if first_word in e.name.lower()][:5]
            suggestion_text = ""
            if suggestions:
                suggestion_text = f"\n\nDid you mean: {', '.join(suggestions)}?"
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Equipment '{equipment_name}' not found. Please check the spelling.{suggestion_text}"
                    }
                ]
            }
        equipment = matches[0]
    
    # Format equipment information
    max_fusion_text = f"\n**Max Fusion Effect**: {equipment.max_fusion_effect}" if equipment.max_fusion_effect else ""
    
    response_text = f"""# {equipment.name}

**Type**: {equipment.type}
**Rarity**: {equipment.rarity}
**Tier**: {equipment.tier} (Practical Usefulness)

## Effect
{equipment.effect}{max_fusion_text}
"""
    
    return {
        "content": [
            {
                "type": "text",
                "text": response_text
            }
        ]
    }
