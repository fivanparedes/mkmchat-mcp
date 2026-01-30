"""Character data models"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class CharacterStats(BaseModel):
    """Character base stats"""
    attack: int
    health: int
    toughness: int
    recovery: int
    
    
class Ability(BaseModel):
    """Character ability/special move"""
    name: str
    type: str  # e.g., "Special Attack 1", "Special Attack 2", "X-Ray Attack", "Fatal Blow Attack"
    effect: Optional[str] = None  # e.g., "Stun", "Freeze", "Curse", "Shield"
    unblockable: bool = False


class Passive(BaseModel):
    """Character passive ability"""
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)  # e.g., ["Attack Boost", "Health Boost"]
    

class Character(BaseModel):
    """Mortal Kombat Mobile character"""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str
    class_type: str = Field(alias="class")
    rarity: str  # Diamond, Gold, Silver, Bronze
    tier: str  # S+, S, A, B, C, D (practical usefulness rating)
    stats: CharacterStats
    abilities: List[Ability]
    passive: Optional[Union[Passive, List[Passive]]] = None  # Can be single passive, list, or null
    synergy: Optional[str] = None  # Changed from synergies (plural)
