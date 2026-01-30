# TSV Structure Update Summary

## Changes Made

### 1. Data File Structure Updates

#### characters.tsv
**Before:**
```
name	class	rarity	attack	health	toughness	recovery	synergy
```

**After:**
```
name	class	rarity	synergy
```
- ✅ Removed all stats columns (attack, health, toughness, recovery)
- ✅ Synergy is now optional (empty if not applicable)

#### abilities.tsv
**Before:**
```
character	ability_name	ability_type	effect	unblockable
```

**After:**
```
character	ability_type	effect	unblockable
```
- ✅ Removed `ability_name` column (ability_type is used as name)

#### passives.tsv
**Before:**
```
character	passive_name	description	tags
```

**After:**
```
character	description
```
- ✅ Removed `passive_name` column (character name is used)
- ✅ Removed `tags` column (simplified structure)

### 2. Code Updates

#### mkmchat/data/loader.py
- ✅ Updated `_load_characters_from_tsv()` to:
  - Use `ability_type` as ability name
  - Use character name as passive name
  - Set empty tags list for passives
  - Set stats to 0 (attack, health, toughness, recovery)
  - Handle optional synergy field with `.get()`

#### mkmchat/tools/llm_team_suggest.py
- ✅ Updated Ollama prompt to remove stats line
- ✅ Updated Gemini prompt to remove stats line
- ✅ Updated `_build_game_data_context()` to not display stats
- ✅ Changed instructions from "Consider character stats, abilities..." to "Consider character abilities, passives..."

#### mkmchat/tools/team_suggest.py
- ✅ Updated sorting logic to use ability counts instead of stats:
  - Tank strategy: sort by unblockable abilities
  - Balanced strategy: sort by ability count
  - Boss strategy: sort by ability count
  - Stats-based sorting removed

#### .github/copilot-instructions.md
- ✅ Updated Data Format section with new TSV structure
- ✅ Documented removal of stats columns
- ✅ Updated abilities and passives column descriptions

### 3. Testing

Created `test_tsv_structure.py` to verify:
- ✅ Characters load correctly with 0 stats
- ✅ Abilities use ability_type as name
- ✅ Passives load with character name
- ✅ Synergy field works (present in some chars, absent in others)
- ✅ Equipment loads correctly

**Test Results:**
```
✅ Loaded 16 characters
✅ Loaded 3 equipment items
✅ ALL TESTS PASSED
```

### 4. MCP Server Compatibility

- ✅ Server starts without errors
- ✅ All 4 tools still functional:
  - `get_character_info`
  - `get_equipment_info`
  - `suggest_team`
  - `suggest_team_with_llm`

## Breaking Changes

### Stats are now always 0
- Character stats (attack, health, toughness, recovery) are no longer loaded from data
- All characters have `CharacterStats(attack=0, health=0, toughness=0, recovery=0)`
- Team suggestion logic now uses ability counts and types instead of stats

### Passive structure simplified
- No more passive names - character name is used
- No more tags - empty list always returned
- Always single passive per character (no lists)

### Ability naming simplified
- ability_type is used as the ability name
- No separate name column needed

## Migration Notes

If you have code that:
1. **Relies on character stats** → Update to use abilities, passives, or class synergies
2. **Uses passive.tags** → This is now always an empty list
3. **Uses separate ability names** → Use ability.type instead (they're identical now)
4. **Expects stat-based sorting** → Update to use ability-based logic

## Files Modified

1. `mkmchat/data/loader.py` - Data loading logic
2. `mkmchat/tools/llm_team_suggest.py` - LLM prompts and context
3. `mkmchat/tools/team_suggest.py` - Team building algorithm
4. `.github/copilot-instructions.md` - Documentation
5. `test_tsv_structure.py` - New test file

## Verification

Run these commands to verify everything works:
```bash
# Test data loading
python test_tsv_structure.py

# Start MCP server
python -m mkmchat.server

# Test with MCP Inspector
npx @modelcontextprotocol/inspector python -m mkmchat.server
```

All systems operational! ✅
