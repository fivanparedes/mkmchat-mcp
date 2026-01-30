"""Team composition data models"""

from typing import List
from pydantic import BaseModel


class TeamSynergy(BaseModel):
    """Team synergy bonus"""
    description: str
    bonus_type: str  # e.g., "damage", "health", "special"
    magnitude: str  # e.g., "20% attack boost"


class Team(BaseModel):
    """Team composition"""
    name: str
    characters: List[str]  # Character names
    strategy: str
    synergies: List[TeamSynergy]
    strengths: List[str]
    weaknesses: List[str]
    recommended_equipment: List[str] = []
