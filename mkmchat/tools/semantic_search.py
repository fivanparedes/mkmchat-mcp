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


async def search_by_strategy(strategy: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search for characters and equipment matching a gameplay strategy
    
    Args:
        strategy: Strategy description (e.g., "high damage dealer", "tank", "support")
        top_k: Number of results per category
    
    Returns:
        MCP response with strategy search results
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
        # Search characters
        char_results = rag.search_characters(strategy, top_k=top_k)
        
        # Search equipment
        equip_results = rag.search_equipment(strategy, top_k=top_k)
        
        # Format as text
        result_text = f"# Strategy Search: {strategy}\n\n"
        
        result_text += f"## Top {len(char_results)} Characters\n\n"
        for i, (doc, score) in enumerate(char_results, 1):
            name = doc.metadata.get("name", "Unknown")
            char_class = doc.metadata.get("class", "Unknown")
            rarity = doc.metadata.get("rarity", "Unknown")
            result_text += f"{i}. **{name}** ({char_class} - {rarity}) - Score: {score:.3f}\n"
            result_text += f"   {doc.content[:150]}...\n\n"
        
        result_text += f"\n## Top {len(equip_results)} Equipment\n\n"
        for i, (doc, score) in enumerate(equip_results, 1):
            name = doc.metadata.get("name", "Unknown")
            equip_type = doc.metadata.get("type", "Unknown")
            result_text += f"{i}. **{name}** ({equip_type}) - Score: {score:.3f}\n"
            result_text += f"   {doc.content[:150]}...\n\n"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error in strategy search: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Strategy search failed: {str(e)}"
                }
            ]
        }


async def explain_mechanic(mechanic_query: str) -> Dict[str, Any]:
    """
    Explain game mechanics or terminology
    
    Args:
        mechanic_query: Question about game mechanics or terms
    
    Returns:
        MCP response with mechanic explanations
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
        # Search gameplay mechanics
        gameplay_results = rag.search_gameplay(mechanic_query, top_k=3)
        
        # Search glossary
        glossary_results = rag.search_glossary(mechanic_query, top_k=3)
        
        # Format as text
        result_text = f"# Mechanic Explanation: {mechanic_query}\n\n"
        
        if gameplay_results:
            result_text += "## Gameplay Mechanics\n\n"
            for i, (doc, score) in enumerate(gameplay_results, 1):
                result_text += f"### Result {i} (Score: {score:.3f})\n"
                result_text += f"{doc.content}\n\n"
        
        if glossary_results:
            result_text += "## Glossary Terms\n\n"
            for i, (doc, score) in enumerate(glossary_results, 1):
                result_text += f"### Result {i} (Score: {score:.3f})\n"
                result_text += f"{doc.content}\n\n"
        
        if not gameplay_results and not glossary_results:
            result_text += "No relevant information found. Try rephrasing your question."
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": result_text
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error explaining mechanic: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Mechanic explanation failed: {str(e)}"
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


async def search_glossary_term(term: str) -> Dict[str, Any]:
    """
    Search for specific glossary terms
    
    Args:
        term: Term or concept to look up (e.g., 'bleed', 'stun', 'power drain')
    
    Returns:
        MCP response with term definitions
    """
    loader = get_data_loader()
    
    try:
        result = loader.search_glossary(term)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Glossary: {term}\n\n{result}"
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error searching glossary: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Glossary search failed: {str(e)}"
                }
            ]
        }


async def search_gameplay(query: str) -> Dict[str, Any]:
    """
    Search for specific gameplay mechanics
    
    Args:
        query: Gameplay mechanic to search for (e.g., 'tag-in', 'special attacks', 'equipment')
    
    Returns:
        MCP response with gameplay information
    """
    loader = get_data_loader()
    
    try:
        result = loader.search_gameplay(query)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"# Gameplay: {query}\n\n{result}"
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error searching gameplay: {e}")
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Gameplay search failed: {str(e)}"
                }
            ]
        }
