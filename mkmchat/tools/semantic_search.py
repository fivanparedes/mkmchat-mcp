"""Semantic search tool for intelligent data retrieval"""

import logging
import json
from typing import Dict, Any, Optional, List

from mkmchat.data.rag import RAGSystem
from mkmchat.data.loader import get_data_loader

logger = logging.getLogger(__name__)

# Global RAG system instance
_rag_system: Optional[RAGSystem] = None


def get_rag_system() -> RAGSystem:
    """Get or initialize the RAG system singleton"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
        if _rag_system.enabled:
            _rag_system.index_data()
    return _rag_system


async def semantic_search(
    query: str,
    top_k: int = 5,
    doc_type: Optional[str] = None,
    min_similarity: float = 0.3
) -> Dict[str, Any]:
    """
    Perform semantic search across all game data
    
    Args:
        query: Natural language search query
        top_k: Number of results to return (default: 5)
        doc_type: Filter by type ('character', 'equipment', 'gameplay', 'glossary')
        min_similarity: Minimum similarity score 0-1 (default: 0.3)
    
    Returns:
        MCP response with search results
    """
    rag = get_rag_system()
    
    if not rag.enabled:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "RAG system not available. Install dependencies: pip install sentence-transformers"
                }
            ]
        }
    
    try:
        results = rag.search(
            query=query,
            top_k=top_k,
            doc_type=doc_type,
            min_similarity=min_similarity
        )
        
        if not results:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No results found for query: {query}\n\nTry adjusting your search terms or lowering min_similarity."
                    }
                ]
            }
        
        # Format results as text
        result_text = f"# Search Results for: {query}\n\n"
        result_text += f"Found {len(results)} results:\n\n"
        
        for i, (doc, score) in enumerate(results, 1):
            result_text += f"## Result {i} (Score: {score:.3f})\n"
            result_text += f"**Type:** {doc.doc_type}\n"
            if doc.metadata:
                result_text += f"**Metadata:** {json.dumps(doc.metadata)}\n"
            result_text += f"\n{doc.content}\n\n"
            result_text += "---\n\n"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Search failed: {str(e)}"
                }
            ]
        }


async def search_characters_advanced(
    rarity: Optional[str] = None,
    char_class: Optional[str] = None,
    tier: Optional[str] = None,
    keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search characters by attributes and keywords
    
    Args:
        rarity: Filter by rarity (Diamond, Gold, Silver, Bronze)
        char_class: Filter by class (Martial Artist, Spec Ops, Outworld, Netherrealm, Elder God)
        tier: Filter by tier (S+, S, A, B, C, D)
        keyword: Search keyword in passive/abilities (e.g., 'fire', 'stun', 'bleed')
    
    Returns:
        MCP response with matching characters
    """
    loader = get_data_loader()
    
    try:
        results = loader.search_characters_by_attribute(
            rarity=rarity,
            char_class=char_class,
            tier=tier,
            keyword=keyword
        )
        
        if not results:
            filters_used = []
            if rarity:
                filters_used.append(f"rarity={rarity}")
            if char_class:
                filters_used.append(f"class={char_class}")
            if tier:
                filters_used.append(f"tier={tier}")
            if keyword:
                filters_used.append(f"keyword={keyword}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No characters found matching filters: {', '.join(filters_used)}\n\nTry relaxing your search criteria."
                    }
                ]
            }
        
        # Format results
        result_text = f"# Character Search Results\n\n"
        result_text += f"Found **{len(results)}** characters\n\n"
        
        # Group by rarity for readability
        for char in results[:20]:  # Limit to 20 results
            passive_preview = ""
            if char.passive:
                desc = char.passive.description if not isinstance(char.passive, list) else char.passive[0].description
                passive_preview = f" - {desc[:80]}..." if len(desc) > 80 else f" - {desc}"
            
            result_text += f"- **{char.name}** ({char.class_type}, {char.rarity}, Tier {char.tier}){passive_preview}\n"
        
        if len(results) > 20:
            result_text += f"\n... and {len(results) - 20} more characters"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in character search: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Character search failed: {str(e)}"
                }
            ]
        }


async def search_equipment_advanced(
    rarity: Optional[str] = None,
    equip_type: Optional[str] = None,
    tier: Optional[str] = None,
    keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search equipment by attributes and keywords
    
    Args:
        rarity: Filter by rarity (Epic, Rare, Uncommon, Common)
        equip_type: Filter by type (Weapon, Armor, Accessory)
        tier: Filter by tier (S+, S, A, B, C, D)
        keyword: Search keyword in effects (e.g., 'fire', 'critical', 'power')
    
    Returns:
        MCP response with matching equipment
    """
    loader = get_data_loader()
    
    try:
        results = loader.search_equipment_by_attribute(
            rarity=rarity,
            equip_type=equip_type,
            tier=tier,
            keyword=keyword
        )
        
        if not results:
            filters_used = []
            if rarity:
                filters_used.append(f"rarity={rarity}")
            if equip_type:
                filters_used.append(f"type={equip_type}")
            if tier:
                filters_used.append(f"tier={tier}")
            if keyword:
                filters_used.append(f"keyword={keyword}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"No equipment found matching filters: {', '.join(filters_used)}\n\nTry relaxing your search criteria."
                    }
                ]
            }
        
        # Format results
        result_text = f"# Equipment Search Results\n\n"
        result_text += f"Found **{len(results)}** equipment items\n\n"
        
        for equip in results[:20]:  # Limit to 20 results
            effect_preview = equip.effect[:80] + "..." if len(equip.effect) > 80 else equip.effect
            result_text += f"- **{equip.name}** ({equip.type}, {equip.rarity}, Tier {equip.tier})\n"
            result_text += f"  Effect: {effect_preview}\n"
        
        if len(results) > 20:
            result_text += f"\n... and {len(results) - 20} more items"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in equipment search: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Equipment search failed: {str(e)}"
                }
            ]
        }
