"""Data loader for MK Mobile game data"""

import json
import csv
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Optional

from mkmchat.models import Character, Equipment, Team, CharacterStats, Ability, Passive


class DataLoader:
    """Loads and manages MK Mobile game data"""
    
    def __init__(self, data_dir: Optional[Path] = None):
        if data_dir is None:
            # Default to data/ directory at project root
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
            
        self._characters: Dict[str, Character] = {}
        self._equipment: Dict[str, Equipment] = {}
        self._teams: List[Team] = []
        self._glossary: str = ""
        self._glossary_terms: Dict[str, str] = {}  # Indexed glossary terms
        self._gameplay: str = ""
        self._gameplay_sections: Dict[str, str] = {}  # Indexed gameplay sections
        
    def load_all(self):
        """Load all game data"""
        self.load_characters()
        self.load_equipment()
        self.load_teams()
        self.load_glossary()
        self.load_gameplay()
        
    def load_characters(self):
        """Load character data from TSV or JSON"""
        # Try TSV format first (optimized)
        characters_tsv = self.data_dir / "characters.tsv"
        abilities_tsv = self.data_dir / "abilities.tsv"
        passives_tsv = self.data_dir / "passives.tsv"
        
        if characters_tsv.exists() and abilities_tsv.exists() and passives_tsv.exists():
            self._load_characters_from_tsv(characters_tsv, abilities_tsv, passives_tsv)
            return
        
        # Fallback to JSON format
        characters_file = self.data_dir / "chars_gold.json"
        if not characters_file.exists():
            characters_file = self.data_dir / "characters.json"
            
        if not characters_file.exists():
            return
            
        with open(characters_file, 'r') as f:
            data = json.load(f)
            for char_data in data.get("characters", []):
                char = Character(**char_data)
                self._characters[char.name.lower()] = char
    
    def _load_characters_from_tsv(self, chars_file: Path, abilities_file: Path, passives_file: Path):
        """Load characters from TSV files"""
        # Load abilities first (new optimized structure: character, sp1, sp2, sp3, xray)
        abilities_dict: Dict[str, List[Ability]] = {}
        with open(abilities_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                char_name = row['character']
                abilities_list = []
                
                # Special Attack 1
                if row.get('sp1') and row['sp1'].strip():
                    abilities_list.append(Ability(
                        name='Special Attack 1',
                        type='Special Attack 1',
                        effect=row['sp1'],
                        unblockable=False
                    ))
                
                # Special Attack 2
                if row.get('sp2') and row['sp2'].strip():
                    abilities_list.append(Ability(
                        name='Special Attack 2',
                        type='Special Attack 2',
                        effect=row['sp2'],
                        unblockable=False
                    ))
                
                # Special Attack 3 (optional)
                if row.get('sp3') and row['sp3'].strip():
                    abilities_list.append(Ability(
                        name='Special Attack 3',
                        type='Special Attack 3',
                        effect=row['sp3'],
                        unblockable=False
                    ))
                
                # X-Ray/Fatal Blow Attack (optional)
                if row.get('xray') and row['xray'].strip():
                    # Determine if it's X-Ray or Fatal Blow based on character
                    attack_type = 'Fatal Blow Attack' if 'Ghostface' in char_name or 'Noob Saibot' in char_name or 'Jade' in char_name else 'X-Ray Attack'
                    abilities_list.append(Ability(
                        name=attack_type,
                        type=attack_type,
                        effect=row['xray'],
                        unblockable=True  # X-Ray and Fatal Blow are typically unblockable
                    ))
                
                abilities_dict[char_name] = abilities_list
        
        # Load passives
        passives_dict: Dict[str, Passive] = {}
        with open(passives_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                char_name = row['character']
                passive = Passive(
                    name=char_name,  # Use character name as passive name
                    description=row['description'],
                    tags=[]  # No tags in new structure
                )
                passives_dict[char_name] = passive
        
        # Load main character data
        with open(chars_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                char_name = row['name']
                
                # Get abilities and passives for this character
                abilities = abilities_dict.get(char_name, [])
                passive = passives_dict.get(char_name, None)
                
                char = Character(
                    name=char_name,
                    **{"class": row['class']},  # Use alias
                    rarity=row['rarity'],
                    tier=row['tier'],
                    stats=CharacterStats(
                        attack=0,  # No stats in new structure
                        health=0,
                        toughness=0,
                        recovery=0
                    ),
                    abilities=abilities,
                    passive=passive,
                    synergy=row.get('synergy', '') if row.get('synergy') else None
                )
                self._characters[char.name.lower()] = char
                
    def load_equipment(self):
        """Load equipment data from TSV or JSON"""
        # Try TSV format first (optimized)
        equipment_basic = self.data_dir / "equipment_basic.tsv"
        equipment_krypt = self.data_dir / "equipment_krypt.tsv"
        equipment_towers = self.data_dir / "equipment_towers.tsv"
        
        # Load all equipment files if they exist
        if equipment_basic.exists():
            self._load_equipment_from_tsv(equipment_basic)
        
        if equipment_krypt.exists():
            self._load_equipment_from_tsv(equipment_krypt)
        
        if equipment_towers.exists():
            self._load_equipment_from_tsv(equipment_towers)
        
        # If we loaded equipment, return
        if self._equipment:
            return
        
        # Fallback to old filename for backward compatibility
        equipment_tsv_old = self.data_dir / "equipment_common.tsv"
        if equipment_tsv_old.exists():
            self._load_equipment_from_tsv(equipment_tsv_old)
            return
        
        # Fallback to JSON format
        equipment_file = self.data_dir / "equipment.json"
        if not equipment_file.exists():
            return
            
        with open(equipment_file, 'r') as f:
            data = json.load(f)
            for equip_data in data.get("equipment", []):
                equip = Equipment(**equip_data)
                self._equipment[equip.name.lower()] = equip
    
    def _load_equipment_from_tsv(self, equipment_file: Path):
        """Load equipment from TSV file"""
        with open(equipment_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                equipment = Equipment(
                    name=row['name'],
                    rarity=row['rarity'],
                    type=row['type'],
                    effect=row['effect'],
                    max_fusion_effect=row.get('max_fusion_effect') if row.get('max_fusion_effect') else None,
                    tier=row['tier']
                )
                self._equipment[equipment.name.lower()] = equipment
                
    def load_teams(self):
        """Load pre-built team compositions (optional)"""
        teams_file = self.data_dir / "teams.json"
        if not teams_file.exists():
            # Teams file is optional, skip if not present
            return
            
        with open(teams_file, 'r') as f:
            data = json.load(f)
            for team_data in data.get("teams", []):
                team = Team(**team_data)
                self._teams.append(team)
    
    def load_glossary(self):
        """Load game terminology glossary with term indexing"""
        glossary_file = self.data_dir / "glossary.txt"
        if not glossary_file.exists():
            # Glossary is optional
            return
        
        with open(glossary_file, 'r', encoding='utf-8') as f:
            self._glossary = f.read()
        
        # Parse glossary into searchable terms
        current_section = ""
        for line in self._glossary.split('\n'):
            line = line.strip()
            if line.startswith('== ') and line.endswith(' =='):
                # Section header like "== BUFFS =="
                current_section = line[3:-3].strip()
            elif ':' in line and line[0].isalpha():
                # Term definition like "Regen: Causes the character to heal over time."
                parts = line.split(':', 1)
                if len(parts) == 2:
                    term = parts[0].strip().lower()
                    definition = parts[1].strip()
                    self._glossary_terms[term] = f"[{current_section}] {definition}"
    
    def load_gameplay(self):
        """Load gameplay mechanics documentation with section indexing"""
        gameplay_file = self.data_dir / "gameplay.txt"
        if not gameplay_file.exists():
            # Gameplay is optional
            return
        
        with open(gameplay_file, 'r', encoding='utf-8') as f:
            self._gameplay = f.read()
        
        # Parse gameplay into indexed sections by topic
        # Since gameplay.txt doesn't have == sections ==, we'll index by keywords
        lines = self._gameplay.split('\n')
        
        # Index key topics for quick lookup
        topic_keywords = {
            'team': ['team', 'composed', '3 characters', '3 vs 3'],
            'tag': ['tag-in', 'tag-out', 'tagging'],
            'starter': ['starter', 'first appears', 'left'],
            'special attacks': ['special attack', 'sp1', 'sp2', 'sp3', 'power bar'],
            'xray': ['x-ray', 'fatal blow', 'unblockable', 'extreme damage'],
            'equipment': ['equipment', 'slots', 'weapon', 'armor', 'accessory'],
            'rarity': ['bronze', 'silver', 'gold', 'diamond', 'challenge'],
            'tier': ['tier', 'ranked', 'useless', 'good', 'game changer'],
            'brutality': ['brutality', 'friendship', 'finalizer', 'resurrection'],
            'game modes': ['faction wars', 'realm klash', 'tower'],
            'character effects': ['[', ']', 'exclusive', 'character']
        }
        
        for topic, keywords in topic_keywords.items():
            matching_lines = []
            for line in lines:
                line_lower = line.lower()
                if any(kw in line_lower for kw in keywords):
                    matching_lines.append(line)
            if matching_lines:
                self._gameplay_sections[topic] = '\n'.join(matching_lines)
                
    def get_character(self, name: str) -> Optional[Character]:
        """Get character by name (case-insensitive)"""
        return self._characters.get(name.lower())
    
    def get_equipment(self, name: str) -> Optional[Equipment]:
        """Get equipment by name (case-insensitive)"""
        return self._equipment.get(name.lower())
    
    def search_characters(self, query: str) -> List[Character]:
        """Search characters by partial name match"""
        query_lower = query.lower()
        return [
            char for name, char in self._characters.items()
            if query_lower in name
        ]
    
    def search_characters_fuzzy(self, query: str, threshold: float = 0.6) -> List[Character]:
        """Search characters with fuzzy name matching
        
        Args:
            query: Character name to search for
            threshold: Minimum similarity score (0-1, default: 0.6)
            
        Returns:
            List of matching characters, prioritizing exact matches
        """
        query_lower = query.lower()
        
        # Exact/partial match first
        exact_matches = [
            char for name, char in self._characters.items()
            if query_lower in name
        ]
        if exact_matches:
            return exact_matches
        
        # Fuzzy match fallback
        all_names = list(self._characters.keys())
        close_matches = get_close_matches(query_lower, all_names, n=5, cutoff=threshold)
        return [self._characters[name] for name in close_matches]
    
    def search_characters_by_attribute(
        self, 
        rarity: Optional[str] = None,
        char_class: Optional[str] = None,
        tier: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[Character]:
        """Search characters by attributes and passive/ability keywords
        
        Args:
            rarity: Filter by rarity (e.g., 'Diamond', 'Gold')
            char_class: Filter by class (e.g., 'Martial Artist', 'Spec Ops')
            tier: Filter by tier (e.g., 'S+', 'A')
            keyword: Search keyword in passive/abilities (e.g., 'fire', 'stun')
            
        Returns:
            List of characters matching all specified criteria
        """
        results = []
        for char in self._characters.values():
            # Filter by rarity
            if rarity and char.rarity.lower() != rarity.lower():
                continue
            # Filter by class
            if char_class and char.class_type.lower() != char_class.lower():
                continue
            # Filter by tier
            if tier and char.tier.lower() != tier.lower():
                continue
            
            # Filter by keyword in passive/abilities
            if keyword:
                keyword_lower = keyword.lower()
                found = False
                
                # Check passive
                if char.passive:
                    if isinstance(char.passive, list):
                        for p in char.passive:
                            if keyword_lower in p.description.lower():
                                found = True
                                break
                    elif keyword_lower in char.passive.description.lower():
                        found = True
                
                # Check abilities
                if not found:
                    for ability in char.abilities:
                        if ability.effect and keyword_lower in ability.effect.lower():
                            found = True
                            break
                
                # Check character name
                if not found and keyword_lower in char.name.lower():
                    found = True
                
                if not found:
                    continue
            
            results.append(char)
        return results
    
    def search_equipment_fuzzy(self, query: str, threshold: float = 0.6) -> List[Equipment]:
        """Search equipment with fuzzy name matching
        
        Args:
            query: Equipment name to search for
            threshold: Minimum similarity score (0-1, default: 0.6)
            
        Returns:
            List of matching equipment, prioritizing exact matches
        """
        query_lower = query.lower()
        
        # Exact/partial match first
        exact_matches = [
            equip for name, equip in self._equipment.items()
            if query_lower in name
        ]
        if exact_matches:
            return exact_matches
        
        # Fuzzy match fallback
        all_names = list(self._equipment.keys())
        close_matches = get_close_matches(query_lower, all_names, n=5, cutoff=threshold)
        return [self._equipment[name] for name in close_matches]
    
    def search_equipment_by_attribute(
        self,
        rarity: Optional[str] = None,
        equip_type: Optional[str] = None,
        tier: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> List[Equipment]:
        """Search equipment by attributes and effect keywords
        
        Args:
            rarity: Filter by rarity (e.g., 'Epic', 'Rare')
            equip_type: Filter by type (e.g., 'Weapon', 'Armor', 'Accessory')
            tier: Filter by tier (e.g., 'S+', 'A')
            keyword: Search keyword in effects (e.g., 'fire', 'critical')
            
        Returns:
            List of equipment matching all specified criteria
        """
        results = []
        for equip in self._equipment.values():
            # Filter by rarity
            if rarity and equip.rarity.lower() != rarity.lower():
                continue
            # Filter by type
            if equip_type and equip.type.lower() != equip_type.lower():
                continue
            # Filter by tier
            if tier and equip.tier.lower() != tier.lower():
                continue
            
            # Filter by keyword in effects
            if keyword:
                keyword_lower = keyword.lower()
                found = False
                
                if equip.effect and keyword_lower in equip.effect.lower():
                    found = True
                if equip.max_fusion_effect and keyword_lower in equip.max_fusion_effect.lower():
                    found = True
                if keyword_lower in equip.name.lower():
                    found = True
                
                if not found:
                    continue
            
            results.append(equip)
        return results
    
    def get_teams(self) -> List[Team]:
        """Get all pre-built teams"""
        return self._teams
    
    def get_all_characters(self) -> List[Character]:
        """Get all characters"""
        return list(self._characters.values())
    
    def get_all_equipment(self) -> List[Equipment]:
        """Get all equipment"""
        return list(self._equipment.values())
    
    def get_glossary(self) -> str:
        """Get game terminology glossary"""
        return self._glossary
    
    def search_glossary(self, query: str) -> str:
        """Search for specific glossary terms
        
        Args:
            query: Search query for glossary terms
            
        Returns:
            Matching glossary terms or full glossary if no matches
        """
        query_lower = query.lower()
        matches = []
        
        # Search for matching terms
        for term, definition in self._glossary_terms.items():
            if query_lower in term or term in query_lower:
                matches.append(f"**{term.title()}**: {definition}")
            elif query_lower in definition.lower():
                matches.append(f"**{term.title()}**: {definition}")
        
        if matches:
            return '\n\n'.join(matches)
        
        # Fuzzy match fallback
        close_terms = get_close_matches(query_lower, list(self._glossary_terms.keys()), n=3, cutoff=0.5)
        if close_terms:
            matches = [f"**{term.title()}**: {self._glossary_terms[term]}" for term in close_terms]
            return '\n\n'.join(matches)
        
        return self._glossary  # Fallback to full glossary
    
    def get_glossary_terms(self) -> Dict[str, str]:
        """Get indexed glossary terms"""
        return self._glossary_terms
    
    def get_gameplay(self) -> str:
        """Get gameplay mechanics documentation"""
        return self._gameplay
    
    def search_gameplay(self, query: str) -> str:
        """Search for specific gameplay mechanics
        
        Args:
            query: Search query for gameplay mechanics
            
        Returns:
            Matching gameplay sections or full gameplay if no matches
        """
        query_lower = query.lower()
        matches = []
        
        # Search indexed sections first
        for topic, content in self._gameplay_sections.items():
            if query_lower in topic or any(word in topic for word in query_lower.split()):
                matches.append(f"## {topic.title()}\n{content}")
        
        # Also search the full content for the query
        if not matches:
            for line in self._gameplay.split('\n'):
                if query_lower in line.lower():
                    matches.append(line)
        
        if matches:
            return '\n\n'.join(matches[:5])  # Limit to 5 sections/matches
        
        return self._gameplay  # Fallback to full gameplay
    
    def get_gameplay_sections(self) -> Dict[str, str]:
        """Get indexed gameplay sections"""
        return self._gameplay_sections


# Global data loader instance
_data_loader = DataLoader()
_data_loader.load_all()


def get_data_loader() -> DataLoader:
    """Get the global data loader instance"""
    return _data_loader
