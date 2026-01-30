"""Equipment data models"""

from typing import Optional
from pydantic import BaseModel


class Equipment(BaseModel):
    """Mortal Kombat Mobile equipment/gear"""
    name: str
    rarity: str  # Epic, Rare, Uncommon, Common
    type: str  # Weapon, Armor, Accessory
    effect: str  # Effect description
    max_fusion_effect: Optional[str] = None  # Max fusion level effect (optional)
    tier: str  # S+, S, A, B, C, D (practical usefulness rating)
