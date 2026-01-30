# Equipment System Migration

## Summary
Successfully migrated equipment data from JSON format to TSV format and integrated equipment recommendations into team suggestions.

## Changes Made

### 1. Data Format Migration
- **Deprecated**: `data/equipment.json` (old nested structure with stats, passive_effects, fusion_level, required_character)
- **New**: `data/equipment_common.tsv` (simplified flat structure)
  - Columns: name, type, effect, max_fusion_effect
  - Types: Weapon, Armor, Accessory
  - Easier to edit and consistent with character data format

### 2. Model Simplification
**Old Equipment Model** (nested):
```python
class EquipmentStats:
    attack_boost, health_boost, toughness_boost, recovery_boost

class PassiveEffect:
    description, condition

class Equipment:
    name, type, rarity, stats, passive_effects, fusion_level, required_character
```

**New Equipment Model** (flat):
```python
class Equipment:
    name: str
    type: str  # Weapon, Armor, Accessory
    effect: str
    max_fusion_effect: Optional[str]
```

### 3. Data Loader Updates
- Updated `DataLoader.load_equipment()` to prioritize TSV format
- Added `_load_equipment_from_tsv()` method
- Maintains JSON fallback for backward compatibility

### 4. Tool Updates

#### `get_equipment_info` Tool
- Simplified output format
- Shows: name, type, effect, max_fusion_effect
- Removed: stats breakdown, passive effects list, fusion level, required character

#### `suggest_team` Tool (Enhanced)
- **New Feature**: Includes equipment recommendations for each team member
- Equipment selection based on strategy:
  - **High Damage/Attack/Offensive**: Prioritizes Weapons and Armor
  - **Tank/Defensive/Survivability**: Prioritizes Armor and Accessories
  - **Boss Battles**: Balanced Weapon and Accessory mix
  - **Default**: Distributes different equipment types
- Each character in the team now gets 1-2 equipment recommendations

### 5. Test Updates
- Updated `test_load_equipment` to use "Amulet" instead of "Wrath Hammer"
- Updated `test_get_equipment_info` to use "Shuriken" instead of "Wrath Hammer"
- Updated `test_suggest_team_with_required_character` to use "Ninjutsu Scorpion" (full name)
- Added check for "Equipment" in team suggestion output

## Current Equipment Data
The TSV file contains 3 example items:
1. **Amulet** (Accessory): 20-30% RESISTANCE to slow and stun
2. **Bracers** (Armor): 10-20% TOUGHNESS boost
3. **Shuriken** (Weapon): 15-25% Basic attacks UNBLOCKABLE chance

## Testing

### Manual Testing
```bash
# Test equipment loading
python -c "from mkmchat.data.loader import get_data_loader; loader = get_data_loader(); equipment = loader.get_all_equipment(); print(f'Loaded {len(equipment)} equipment items'); [print(f'{e.name} ({e.type}): {e.effect}') for e in equipment]"

# Test team suggestion with equipment
python -c "
import asyncio
from mkmchat.tools.team_suggest import suggest_team

async def test():
    result = await suggest_team('high damage')
    print(result['content'][0]['text'])
    
asyncio.run(test())
"
```

### Automated Tests
```bash
pytest tests/ -v
# All 9 tests pass ✅
```

## Example Output

### Team Suggestion (with equipment)
```
# Team Suggestion for 'high damage'

## Team Composition (3 characters)

### 🥊 Starter (Position 1)
**Strike Force Cassie Cage** - Spec Ops (Diamond)
- Attack: 1350 | Health: 1250
- Toughness: 980 | Recovery: 950
- Role: Enters battle first

**Recommended Equipment**:
  - **Shuriken** (Weapon): 15-25% Basic attacks UNBLOCKABLE chance
  - **Bracers** (Armor): 10-20% TOUGHNESS boost

### Position 2
**Dragon Breath Bo' Rai Cho** - Martial Artist (Gold)
- Attack: 1300 | Health: 1100
- Toughness: 970 | Recovery: 890

**Recommended Equipment**:
  - **Shuriken** (Weapon): 15-25% Basic attacks UNBLOCKABLE chance
  - **Bracers** (Armor): 10-20% TOUGHNESS boost

[... continues for Position 3]
```

## Documentation Updates
- Updated `.github/copilot-instructions.md`:
  - Data Format section: documented new equipment TSV format
  - Key Files section: updated equipment file reference
  - Common Tasks section: added "Adding a New Equipment Item" guide

## Benefits
1. **Consistency**: All game data now in TSV format (characters, abilities, passives, equipment)
2. **Simplicity**: Flat equipment structure easier to understand and maintain
3. **Enhanced Functionality**: Team suggestions now include equipment recommendations
4. **Easy Editing**: TSV format allows quick edits in text editors or spreadsheet apps
5. **Backward Compatible**: Falls back to JSON if TSV not found

## Next Steps (Optional)
1. Add more equipment items to `equipment_common.tsv`
2. Enhance equipment selection algorithm with more sophisticated logic:
   - Match equipment to character class
   - Consider character abilities when selecting equipment
   - Support equipment synergies
3. Add equipment fusion level support if needed
4. Consider adding character-specific equipment restrictions
