"""Team suggestion tool"""

from typing import List, Optional
from mkmchat.data.loader import get_data_loader


# Tier and rarity ordering for prioritization
TIER_ORDER = {"S+": 6, "S": 5, "A": 4, "B": 3, "C": 2, "D": 1}
CHARACTER_RARITY_ORDER = {"Diamond": 4, "Gold": 3, "Silver": 2, "Bronze": 1}
EQUIPMENT_RARITY_ORDER = {"Epic": 4, "Rare": 3, "Uncommon": 2, "Common": 1}


async def suggest_team(
    strategy: str,
    owned_characters: Optional[List[str]] = None,
    required_character: Optional[str] = None
) -> dict:
    """
    Suggest optimal team compositions by assembling a custom 3-character team
    
    Prioritization logic:
    1. Analyze passive abilities for synergies
    2. Filter by tier (S+ > S > A > B > C > D)
    3. Then by rarity (Diamond > Gold > Silver > Bronze)
    
    Args:
        strategy: Desired strategy (e.g., 'high damage', 'boss battles')
        owned_characters: List of characters the player owns (optional)
        required_character: A character that must be in the team (optional)
        
    Returns:
        MCP response with team suggestions
    """
    loader = get_data_loader()
    
    # Get available characters
    all_characters = loader.get_all_characters()
    
    # Filter by owned characters if specified
    if owned_characters:
        owned_lower = [c.lower() for c in owned_characters]
        available_chars = [char for char in all_characters if char.name.lower() in owned_lower]
    else:
        available_chars = all_characters
    
    if len(available_chars) < 3:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Not enough characters available. Need at least 3 characters to form a team. Found: {len(available_chars)}"
                }
            ]
        }
    
    # Build team based on strategy with tier/rarity prioritization
    team = _build_team_by_strategy(strategy, available_chars, required_character)
    
    if not team:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Could not build a team for strategy '{strategy}' with the available characters."
                }
            ]
        }
    
    # Get equipment recommendations
    equipment = loader.get_all_equipment()
    equipment_suggestions = _suggest_equipment_for_team(team, strategy, equipment)
    
    # Format the team suggestion
    response_text = _format_team_response(team, strategy, equipment_suggestions)
    
    return {
        "content": [
            {
                "type": "text",
                "text": response_text
            }
        ]
    }


def _get_character_score(char) -> tuple:
    """
    Calculate priority score for a character based on tier and rarity.
    Returns tuple for sorting: (tier_score, rarity_score)
    Higher scores = better priority
    """
    tier_score = TIER_ORDER.get(char.tier, 0)
    rarity_score = CHARACTER_RARITY_ORDER.get(char.rarity, 0)
    return (tier_score, rarity_score)


def _analyze_passive_synergies(characters: list) -> dict:
    """
    Analyze passive abilities to find potential synergies.
    Returns dict mapping character names to synergy keywords found in their passives.
    """
    synergy_map = {}
    
    # Keywords that indicate synergies
    synergy_keywords = [
        'team', 'ally', 'allies', 'teammate', 'teammates',
        'outworld', 'martial artist', 'spec ops', 'netherrealm', 
        'elder god', 'ronin', 'strike force', 'nomad',
        'damage boost', 'attack boost', 'health boost', 'power generation',
        'cripple', 'weaken', 'snare', 'stun', 'blind', 'curse',
        'resurrection', 'regeneration', 'shield', 'immunity'
    ]
    
    for char in characters:
        if not char.passive:
            continue
            
        synergies = []
        
        # Handle single passive or list of passives
        passives = char.passive if isinstance(char.passive, list) else [char.passive]
        
        for passive in passives:
            description_lower = passive.description.lower()
            
            # Find matching synergy keywords
            for keyword in synergy_keywords:
                if keyword in description_lower:
                    synergies.append(keyword)
        
        if synergies:
            synergy_map[char.name] = synergies
    
    return synergy_map


def _find_synergistic_characters(base_char, available_chars: list, synergy_map: dict) -> list:
    """
    Find characters that synergize well with the base character.
    Returns sorted list of characters by synergy potential.
    """
    if base_char.name not in synergy_map:
        return []
    
    base_synergies = synergy_map[base_char.name]
    synergistic_chars = []
    
    for char in available_chars:
        if char.name == base_char.name:
            continue
            
        synergy_score = 0
        
        # Check class synergies
        if base_char.class_type.lower() in [s.lower() for s in base_synergies]:
            if char.class_type == base_char.class_type:
                synergy_score += 3
        
        # Check passive keyword matches
        if char.name in synergy_map:
            char_synergies = synergy_map[char.name]
            common_keywords = set(base_synergies) & set(char_synergies)
            synergy_score += len(common_keywords)
        
        if synergy_score > 0:
            synergistic_chars.append((char, synergy_score))
    
    # Sort by synergy score, then by tier/rarity
    synergistic_chars.sort(key=lambda x: (x[1], _get_character_score(x[0])), reverse=True)
    
    return [char for char, score in synergistic_chars]


def _build_team_by_strategy(strategy: str, available_chars: list, required_character: Optional[str]) -> Optional[list]:
    """
    Build a 3-character team based on strategy.
    
    Priority order:
    1. Passive synergies (characters that complement each other)
    2. Tier (S+ > S > A > B > C > D)
    3. Rarity (Diamond > Gold > Silver > Bronze)
    """
    strategy_lower = strategy.lower()
    
    # Start with required character if specified
    team = []
    remaining_chars = available_chars.copy()
    
    if required_character:
        required_char = next((c for c in available_chars if c.name.lower() == required_character.lower()), None)
        if required_char:
            team.append(required_char)
            remaining_chars = [c for c in remaining_chars if c.name.lower() != required_character.lower()]
    
    # Step 1: Analyze passive synergies across all available characters
    synergy_map = _analyze_passive_synergies(available_chars)
    
    # Step 2: If we have a base character (required or first pick), find synergistic teammates
    if team:
        # Find characters that synergize with the required character
        synergistic = _find_synergistic_characters(team[0], remaining_chars, synergy_map)
        
        # Separate synergistic from non-synergistic
        synergistic_names = {c.name for c in synergistic}
        non_synergistic = [c for c in remaining_chars if c.name not in synergistic_names]
        
        # Prioritize synergistic characters, then fall back to tier/rarity
        remaining_chars = synergistic + non_synergistic
    else:
        # No required character - sort by tier/rarity first, then check synergies
        remaining_chars.sort(key=_get_character_score, reverse=True)
    
    # Step 3: Apply strategy-specific filtering/sorting on top of synergy analysis
    if "damage" in strategy_lower or "attack" in strategy_lower or "offensive" in strategy_lower:
        # For damage strategies, look for offensive passives
        offensive_chars = []
        other_chars = []
        
        for char in remaining_chars:
            if char.name in synergy_map:
                synergies = synergy_map[char.name]
                if any(keyword in synergies for keyword in ['damage boost', 'attack boost', 'cripple', 'weaken']):
                    offensive_chars.append(char)
                    continue
            other_chars.append(char)
        
        # Offensive chars first, then others (both maintaining tier/rarity order)
        offensive_chars.sort(key=_get_character_score, reverse=True)
        other_chars.sort(key=_get_character_score, reverse=True)
        remaining_chars = offensive_chars + other_chars
        
    elif "tank" in strategy_lower or "defensive" in strategy_lower or "survivability" in strategy_lower:
        # For tank strategies, look for defensive/healing passives
        defensive_chars = []
        other_chars = []
        
        for char in remaining_chars:
            if char.name in synergy_map:
                synergies = synergy_map[char.name]
                if any(keyword in synergies for keyword in ['health boost', 'regeneration', 'shield', 'immunity', 'resurrection']):
                    defensive_chars.append(char)
                    continue
            other_chars.append(char)
        
        defensive_chars.sort(key=_get_character_score, reverse=True)
        other_chars.sort(key=_get_character_score, reverse=True)
        remaining_chars = defensive_chars + other_chars
        
    elif "boss" in strategy_lower:
        # For boss battles, prioritize high-tier characters with powerful abilities
        remaining_chars.sort(key=lambda c: (
            _get_character_score(c),
            len([a for a in c.abilities if a.unblockable])
        ), reverse=True)
        
    elif "class" in strategy_lower or "synergy" in strategy_lower:
        # Group by class for class-specific synergies
        if team:
            primary_class = team[0].class_type
            same_class = [c for c in remaining_chars if c.class_type == primary_class]
            other_class = [c for c in remaining_chars if c.class_type != primary_class]
            
            # Sort both groups by tier/rarity
            same_class.sort(key=_get_character_score, reverse=True)
            other_class.sort(key=_get_character_score, reverse=True)
            remaining_chars = same_class + other_class
    else:
        # Default: sort by tier/rarity (already done if no required character)
        if team:
            remaining_chars.sort(key=_get_character_score, reverse=True)
    
    # Fill remaining slots (need 3 total)
    slots_needed = 3 - len(team)
    team.extend(remaining_chars[:slots_needed])
    
    return team if len(team) == 3 else None


def _get_equipment_score(equipment) -> tuple:
    """
    Calculate priority score for equipment based on tier and rarity.
    Returns tuple for sorting: (tier_score, rarity_score)
    Higher scores = better priority
    """
    tier_score = TIER_ORDER.get(equipment.tier, 0)
    rarity_score = EQUIPMENT_RARITY_ORDER.get(equipment.rarity, 0)
    return (tier_score, rarity_score)


def _suggest_equipment_for_team(team: list, strategy: str, all_equipment: list) -> dict:
    """
    Suggest equipment for each team member based on strategy.
    Prioritizes by tier (S+ > S > A > B > C > D) then rarity (Epic > Rare > Uncommon > Common)
    """
    suggestions = {}
    strategy_lower = strategy.lower()
    
    # Sort all equipment by tier/rarity first
    sorted_equipment = sorted(all_equipment, key=_get_equipment_score, reverse=True)
    
    # Categorize equipment by type (maintaining tier/rarity order)
    weapons = [e for e in sorted_equipment if e.type.lower() == "weapon"]
    armor = [e for e in sorted_equipment if e.type.lower() == "armor"]
    accessories = [e for e in sorted_equipment if e.type.lower() == "accessory"]
    
    for char in team:
        char_equipment = []
        
        # Strategy-based equipment selection (prioritizing highest tier/rarity within category)
        if "damage" in strategy_lower or "attack" in strategy_lower or "offensive" in strategy_lower:
            # Prioritize weapons and attack-boosting items
            if weapons:
                char_equipment.append(weapons[0])
            if accessories:
                # Look for offensive accessories
                char_equipment.append(accessories[0])
                
        elif "tank" in strategy_lower or "defensive" in strategy_lower or "survivability" in strategy_lower:
            # Prioritize armor and defensive items
            if armor:
                char_equipment.append(armor[0])
            if accessories:
                char_equipment.append(accessories[0])
                
        elif "boss" in strategy_lower:
            # Balanced equipment for boss battles - best weapon and best accessory
            if weapons:
                char_equipment.append(weapons[0])
            if accessories:
                char_equipment.append(accessories[0])
        else:
            # Default: give best weapon and best armor
            if weapons:
                char_equipment.append(weapons[0])
            if armor:
                char_equipment.append(armor[0])
        
        suggestions[char.name] = char_equipment
    
    return suggestions


def _format_team_response(team: list, strategy: str, equipment_suggestions: dict) -> str:
    """Format the team suggestion response"""
    
    # Determine starter (first character in team)
    starter = team[0]
    
    response = f"""# Team Suggestion for '{strategy}'

## Team Composition (3 characters)

### 🥊 Starter (Position 1)
**{starter.name}** - {starter.class_type} ({starter.rarity})
- **Tier**: {starter.tier} (Practical Usefulness)
- Attack: {starter.stats.attack} | Health: {starter.stats.health}
- Toughness: {starter.stats.toughness} | Recovery: {starter.stats.recovery}
- Role: Enters battle first
"""
    
    # Add recommended equipment for starter
    if starter.name in equipment_suggestions:
        response += f"\n**Recommended Equipment**:\n"
        for equip in equipment_suggestions[starter.name]:
            response += f"  - **{equip.name}** ({equip.type}, {equip.rarity}, Tier {equip.tier}): {equip.effect}\n"
    
    response += "\n"
    
    # Add other team members
    for i, char in enumerate(team[1:], 2):
        response += f"""### Position {i}
**{char.name}** - {char.class_type} ({char.rarity})
- **Tier**: {char.tier} (Practical Usefulness)
- Attack: {char.stats.attack} | Health: {char.stats.health}
- Toughness: {char.stats.toughness} | Recovery: {char.stats.recovery}
"""
        
        # Add recommended equipment
        if char.name in equipment_suggestions:
            response += f"\n**Recommended Equipment**:\n"
            for equip in equipment_suggestions[char.name]:
                response += f"  - **{equip.name}** ({equip.type}, {equip.rarity}, Tier {equip.tier}): {equip.effect}\n"
        
        response += "\n"
    
    # Add team analysis
    total_attack = sum(c.stats.attack for c in team)
    total_health = sum(c.stats.health for c in team)
    avg_toughness = sum(c.stats.toughness for c in team) / 3
    
    # Calculate average tier score
    tier_scores = [TIER_ORDER.get(c.tier, 0) for c in team]
    avg_tier_score = sum(tier_scores) / len(tier_scores)
    tier_rating = "Excellent" if avg_tier_score >= 5 else "Great" if avg_tier_score >= 4 else "Good" if avg_tier_score >= 3 else "Decent"
    
    # Check for class synergies
    classes = [c.class_type for c in team]
    class_counts = {}
    for cls in classes:
        class_counts[cls] = class_counts.get(cls, 0) + 1
    
    synergy_note = ""
    for cls, count in class_counts.items():
        if count >= 2:
            synergy_note += f"\n- ⚡ **{cls} Synergy**: {count} characters share this class for potential passive bonuses"
    
    response += f"""## Team Stats Summary
- **Team Tier Rating**: {tier_rating} (Avg: {avg_tier_score:.1f})
- **Total Attack Power**: {total_attack}
- **Total Health Pool**: {total_health}
- **Average Toughness**: {avg_toughness:.0f}
- **Team Diversity**: {len(class_counts)} different class(es)

## Strategy Notes
{synergy_note if synergy_note else "- Mixed classes: Consider equipment to boost team cohesion"}

## Passive Synergies
"""
    
    # Add passive information
    for char in team:
        if char.passive:
            passives = char.passive if isinstance(char.passive, list) else [char.passive]
            response += f"\n**{char.name}**:\n"
            for passive in passives:
                response += f"  - {passive.description}\n"
    
    response += "\n## Abilities Overview\n"
    
    for char in team:
        response += f"\n**{char.name}**:\n"
        for ability in char.abilities:
            response += f"  - {ability.name} ({ability.type})"
            if ability.effect:
                response += f" - {ability.effect}"
            if ability.unblockable:
                response += " [Unblockable]"
            response += "\n"
    
    response += """
## Fight Tips
- The **Starter** character enters battle first
- Use **Tag-in** to switch characters strategically
- Characters can **Tag-out** when another is called in
- Each fight is 3v3, plan your rotation accordingly
- **Tier ratings** indicate practical usefulness: S+ and S tier characters are most effective
"""
    
    return response
