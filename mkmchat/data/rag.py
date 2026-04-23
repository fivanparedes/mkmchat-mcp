"""RAG (Retrieval-Augmented Generation) system for intelligent data search"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pickle
import hashlib

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    np = None

logger = logging.getLogger(__name__)

# Tier ranking for sorting (higher = better)
TIER_RANK = {"D": 0, "C": 1, "B": 2, "A": 3, "S": 4, "S+": 5}
TIER_BOOST = 0.1  # Score boost per tier level


def get_tier_rank(tier: str) -> int:
    """Get numeric rank for a tier string."""
    if tier:
        return TIER_RANK.get(tier.strip(), 0)
    return 0


class Document:
    """A document chunk with metadata"""
    
    def __init__(self, content: str, metadata: Dict, doc_type: str):
        self.content = content
        self.metadata = metadata
        self.doc_type = doc_type  # 'character', 'equipment', 'gameplay', 'glossary'
        self.embedding: Optional[np.ndarray] = None
    
    def __repr__(self):
        return f"Document(type={self.doc_type}, metadata={self.metadata})"


class RAGSystem:
    """Retrieval-Augmented Generation system for MK Mobile data"""
    
    def __init__(self, data_dir: Optional[Path] = None, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG system
        
        Args:
            data_dir: Directory containing game data files
            model_name: Name of the sentence transformer model to use
        """
        if not EMBEDDINGS_AVAILABLE:
            logger.warning("sentence-transformers not available. Install with: pip install sentence-transformers")
            self.enabled = False
            return
            
        self.enabled = True
        
        if data_dir is None:
            self.data_dir = Path(__file__).resolve().parent
        else:
            self.data_dir = Path(data_dir)
        
        self.cache_dir = self.data_dir / ".rag_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        self.documents: List[Document] = []
        self.embeddings: Optional[np.ndarray] = None
        self._last_data_hash: Optional[str] = None  # tracks hash after last index
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better embedding consistency."""
        if not text:
            return ""
        # Replace curly quotes with straight ones
        text = text.replace('’', "'").replace('‘', "'").replace('“', '"').replace('”', '"')
        return text.strip()

    def _apply_keyword_boost(self, query: str, results: List[Tuple[Document, float]]) -> List[Tuple[Document, float]]:
        """Apply a boost to results that contain keywords from the query."""
        if not query or not results:
            return results
            
        # Clean query: remove possessives and common punctuation
        clean_query = query.lower().replace("'s", "").replace("s'", "").replace("’s", "")
        for char in ".,!?;:()[]{}":
            clean_query = clean_query.replace(char, " ")
            
        # Extract keywords (words > 3 chars or common MK terms)
        words = clean_query.split()
        keywords = [w for w in words if len(w) > 3]
        
        # Add important small terms if they appear
        important_terms = ['set', 'gear', 'kard', 'tier']
        for term in important_terms:
            if term in words and term not in keywords:
                keywords.append(term)
                
        # Character names and set types are crucial
        set_types = ['brutality', 'friendship']
        for stype in set_types:
            if stype in clean_query and stype not in keywords:
                keywords.append(stype)
        
        if not keywords:
            return results
            
        boosted_results = []
        for doc, score in results:
            content_lower = doc.content.lower()
            name_lower = doc.metadata.get('name', '').lower()
            
            boost = 0
            for kw in keywords:
                # Big boost for direct name match
                if kw in name_lower:
                    boost += 0.15
                # Medium boost for content match (tags, character names in desc)
                elif kw in content_lower:
                    boost += 0.05
            
            boosted_results.append((doc, score + boost))
            
        # Re-sort by boosted score
        boosted_results.sort(key=lambda x: x[1], reverse=True)
        return boosted_results

    def _get_cache_hash(self) -> str:
        """Generate hash of data files for cache validation"""
        hasher = hashlib.md5()
        for file in sorted(self.data_dir.glob("*.tsv")):
            hasher.update(file.read_bytes())
        for file in sorted(self.data_dir.glob("*.txt")):
            hasher.update(file.read_bytes())
        return hasher.hexdigest()
    
    def _load_cache(self) -> bool:
        """Load cached embeddings if available and valid"""
        cache_file = self.cache_dir / "embeddings.pkl"
        hash_file = self.cache_dir / "data_hash.txt"
        
        if not cache_file.exists() or not hash_file.exists():
            return False
        
        # Check if data has changed
        current_hash = self._get_cache_hash()
        cached_hash = hash_file.read_text().strip()
        
        if current_hash != cached_hash:
            logger.info("Data files changed, rebuilding embeddings")
            return False
        
        # Load cached embeddings
        try:
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
                self.documents = cache_data['documents']
                self.embeddings = cache_data['embeddings']
            logger.info(f"Loaded {len(self.documents)} documents from cache")
            return True
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False
    
    def _save_cache(self):
        """Save embeddings to cache"""
        try:
            cache_file = self.cache_dir / "embeddings.pkl"
            hash_file = self.cache_dir / "data_hash.txt"
            
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'documents': self.documents,
                    'embeddings': self.embeddings
                }, f)
            
            hash_file.write_text(self._get_cache_hash())
            logger.info("Saved embeddings to cache")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def index_data(self, force_rebuild: bool = False):
        """Index all data files for semantic search"""
        if not self.enabled:
            return
        
        # Try loading from cache
        if not force_rebuild and self._load_cache():
            return
        
        logger.info("Building document index...")
        self.documents = []
        
        # Index characters from TSV
        self._index_characters()
        
        # Index equipment
        self._index_equipment()
        
        # Index gameplay mechanics
        self._index_gameplay()
        
        # Index glossary
        self._index_glossary()
        
        # Generate embeddings
        if self.documents:
            logger.info(f"Generating embeddings for {len(self.documents)} documents...")
            contents = [doc.content for doc in self.documents]
            self.embeddings = self.model.encode(contents, show_progress_bar=True)
            logger.info("Embeddings generated successfully")
            
            # Save to cache
            self._save_cache()
        
        # Remember the hash of the data we just indexed
        self._last_data_hash = self._get_cache_hash()
        
        if not self.documents:
            logger.warning("No documents found to index")
    
    def _index_characters(self):
        """Index character data"""
        import csv
        
        chars_file = self.data_dir / "characters.tsv"
        abilities_file = self.data_dir / "abilities.tsv"
        passives_file = self.data_dir / "passives.tsv"
        
        if not all([chars_file.exists(), abilities_file.exists(), passives_file.exists()]):
            logger.warning("Character TSV files not found, skipping character indexing")
            return
        
        # Load character base info
        chars_data = {}
        with open(chars_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                chars_data[row['name']] = row
        
        # Load abilities
        abilities_data = {}
        with open(abilities_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                abilities_data[row['character']] = row
        
        # Load passives
        passives_data = {}
        with open(passives_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                passives_data[row['character']] = row
        
        # Create comprehensive documents for each character
        for char_name, char_info in chars_data.items():
            # Base character info document
            content_parts = [
                f"Character: {char_name}",
                f"Class: {char_info.get('class', 'Unknown')}",
                f"Rarity: {char_info.get('rarity', 'Unknown')}"
            ]

            # Always include synergy so the embedding reflects team-comp context
            synergy_val = char_info.get('synergy') or 'None'
            content_parts.append(f"Synergy: {synergy_val}")
            
            # Add abilities
            if char_name in abilities_data:
                abilities = abilities_data[char_name]
                if abilities.get('sp1'):
                    content_parts.append(f"Special Attack 1: {abilities['sp1']}")
                if abilities.get('sp2'):
                    content_parts.append(f"Special Attack 2: {abilities['sp2']}")
                if abilities.get('sp3'):
                    content_parts.append(f"Special Attack 3: {abilities['sp3']}")
                if abilities.get('xray'):
                    content_parts.append(f"X-Ray/Fatal Blow: {abilities['xray']}")
            
            # Add passive
            if char_name in passives_data:
                passive = passives_data[char_name]
                if passive.get('description'):
                    content_parts.append(f"Passive: {passive['description']}")
            
            content = "\n".join(content_parts)
            
            doc = Document(
                content=content,
                metadata={
                    'name': char_name,
                    'class': char_info.get('class'),
                    'rarity': char_info.get('rarity'),
                    'synergy': char_info.get('synergy'),
                    'tier': char_info.get('tier', '')
                },
                doc_type='character'
            )
            self.documents.append(doc)
        
        logger.info(f"Indexed {len(chars_data)} characters")
    
    def _index_equipment(self):
        """Index equipment data from basic, krypt and towers files"""
        import csv
        
        equipment_files = [
            self.data_dir / "equipment_basic.tsv",
            self.data_dir / "equipment_krypt.tsv",
            self.data_dir / "equipment_towers.tsv"
        ]
        
        # Pattern to detect character sets: [CHARACTER] {{SetType}}
        set_pattern = re.compile(r'\[(.*?)\]\s+{{(Friendship|Brutality)}}')
        
        # First pass: map sets to item names
        equipment_sets = {}  # (char, type) -> [item_names]
        all_rows = []        # list of (row, source_name, file_name)
        
        for equipment_file in equipment_files:
            if not equipment_file.exists():
                logger.debug(f"{equipment_file.name} not found, skipping")
                continue
            
            source = "Tower Equipment" if "towers" in equipment_file.name else \
                     "Krypt Equipment" if "krypt" in equipment_file.name else "Basic Equipment"
            
            with open(equipment_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                for row in reader:
                    all_rows.append((row, source, equipment_file.name))
                    
                    # Check for set tags
                    effect_text = row.get('effect', '')
                    match = set_pattern.search(effect_text)
                    if match:
                        char, stype = match.group(1), match.group(2)
                        equipment_sets.setdefault((char, stype), []).append(row['name'])
        
        # Second pass: index items with cross-references
        equipment_count = 0
        for row, source, file_name in all_rows:
            name = self._normalize_text(row['name'])
            effect = self._normalize_text(row['effect'])
            
            content_parts = [
                f"Equipment: {name}",
                f"Type: {row['type']}",
                f"Rarity: {row.get('rarity', 'Unknown')}",
                f"Effect: {effect}"
            ]
            
            if row.get('max_fusion_effect'):
                content_parts.append(f"Max Fusion Effect: {self._normalize_text(row['max_fusion_effect'])}")
            
            # Add set information if applicable
            match = set_pattern.search(effect)
            if match:
                char, stype = match.group(1), match.group(2)
                others = [self._normalize_text(n) for n in equipment_sets.get((char, stype), []) if n != row['name']]
                if others:
                    content_parts.append(f"Related Set Items: {', '.join(others)}")
            
            content_parts.append(f"Source: {source}")
            content = "\n".join(content_parts)
            
            doc = Document(
                content=content,
                metadata={
                    'name': row['name'],
                    'type': row['type'],
                    'rarity': row.get('rarity'),
                    'tier': row.get('tier', ''),
                    'source': source,
                    'file': file_name
                },
                doc_type='equipment'
            )
            self.documents.append(doc)
            equipment_count += 1
        
        if equipment_count > 0:
            logger.info(f"Indexed {equipment_count} equipment items with set cross-references")
        else:
            logger.warning("No equipment files found, skipping equipment indexing")
    
    def _index_gameplay(self):
        """Index gameplay mechanics — one Document per line for precise retrieval."""
        gameplay_file = self.data_dir / "gameplay.txt"
        if not gameplay_file.exists():
            return

        content = gameplay_file.read_text(encoding='utf-8')

        # Simple keyword → topic mapping for metadata annotation.
        TOPIC_KEYWORDS = {
            'team': ['team', 'composed', '3 characters', '3 vs 3', 'starter'],
            'tag': ['tag-in', 'tag-out', 'tagging'],
            'special attacks': ['special attack', 'sp1', 'sp2', 'sp3', 'power bar'],
            'xray': ['x-ray', 'fatal blow', 'unblockable', 'extreme damage'],
            'equipment': ['equipment', 'slots', 'weapon', 'armor', 'accessory'],
            'rarity': ['bronze', 'silver', 'gold', 'diamond', 'challenge'],
            'tier': ['tier', 'ranked', 'useless', 'good', 'game changer', 's+'],
            'brutality': ['brutality', 'friendship', 'finalizer', 'resurrection'],
            'game modes': ['faction wars', 'realm klash', 'tower'],
        }

        def _detect_topic(line_lower: str) -> str:
            for topic, kws in TOPIC_KEYWORDS.items():
                if any(kw in line_lower for kw in kws):
                    return topic
            return 'general'

        count = 0
        for i, line in enumerate(content.split('\n')):
            text = line.strip()
            if not text:
                continue
            topic = _detect_topic(text.lower())
            doc = Document(
                content=text,
                metadata={'line': i, 'topic': topic},
                doc_type='gameplay'
            )
            self.documents.append(doc)
            count += 1

        logger.info(f"Indexed {count} gameplay lines")
    
    def _index_glossary(self):
        """Index glossary terms — one Document per term for precise retrieval."""
        glossary_file = self.data_dir / "glossary.txt"
        if not glossary_file.exists():
            return

        content = glossary_file.read_text(encoding='utf-8')
        current_category = 'general'
        count = 0

        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped:
                continue

            # Section header like "== DEBUFFS =="
            if stripped.startswith('== ') and stripped.endswith(' =='):
                current_category = stripped[3:-3].strip().lower()
                continue

            # Term definition like "Snare: Prevents the character..."
            if ':' in stripped and stripped[0].isalpha():
                parts = stripped.split(':', 1)
                term = parts[0].strip()
                definition = parts[1].strip()
                full_text = f"{term}: {definition}"
                doc = Document(
                    content=full_text,
                    metadata={'term': term.lower(), 'category': current_category},
                    doc_type='glossary'
                )
                self.documents.append(doc)
                count += 1
            else:
                # Non-term line — index as-is under current category
                doc = Document(
                    content=stripped,
                    metadata={'category': current_category},
                    doc_type='glossary'
                )
                self.documents.append(doc)
                count += 1

        logger.info(f"Indexed {count} glossary entries")
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        min_similarity: float = 0.3
    ) -> List[Tuple[Document, float]]:
        """
        Search for relevant documents using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            doc_type: Filter by document type ('character', 'equipment', 'gameplay', 'glossary')
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of (document, similarity_score) tuples
        """
        if not self.enabled:
            return []
        
        if not self.documents or self.embeddings is None:
            logger.warning("No indexed documents. Call index_data() first.")
            return []
        
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        # Calculate similarities
        similarities = np.dot(self.embeddings, query_embedding)
        
        # Filter by document type if specified
        if doc_type:
            filtered_indices = [i for i, doc in enumerate(self.documents) if doc.doc_type == doc_type]
            filtered_similarities = similarities[filtered_indices]
            filtered_docs = [self.documents[i] for i in filtered_indices]
        else:
            filtered_similarities = similarities
            filtered_docs = self.documents
        
        # Get top-k results
        top_indices = np.argsort(filtered_similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            score = float(filtered_similarities[idx])
            if score >= min_similarity:
                results.append((filtered_docs[idx], score))
        
        return results
    
    def search_characters(
        self,
        query: str,
        top_k: int = 10,
        prioritize_tier: bool = True
    ) -> List[Tuple[Document, float]]:
        """
        Search for characters matching the query with optional tier prioritization.
        
        Args:
            query: Search query
            top_k: Number of results to return
            prioritize_tier: If True, boost scores based on tier (S+ > S > A > B > C > D)
            
        Returns:
            List of (Document, score) tuples sorted by adjusted score
        """
        # Fetch more results to allow tier reranking
        fetch_k = top_k * 3 if prioritize_tier else top_k
        base_results = self.search(query, top_k=fetch_k, doc_type='character')
        
        if not prioritize_tier:
            return base_results[:top_k]
        
        # Apply tier boost to scores
        adjusted_results = []
        for doc, score in base_results:
            tier = doc.metadata.get('tier', '')
            tier_rank = get_tier_rank(tier)
            # Boost: S+ gets +0.5, S gets +0.4, A gets +0.3, etc.
            tier_bonus = tier_rank * TIER_BOOST
            adjusted_score = score + tier_bonus
            adjusted_results.append((doc, adjusted_score))
        
        # Sort by adjusted score (highest first) and limit to top_k
        adjusted_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply keyword boost for direct relevance
        final_results = self._apply_keyword_boost(query, adjusted_results)
        
        return final_results[:top_k]
    
    def search_equipment(
        self,
        query: str,
        top_k: int = 20,
        prioritize_tier: bool = True
    ) -> List[Tuple[Document, float]]:
        """
        Search for equipment matching the query with optional tier prioritization.
        
        Args:
            query: Search query
            top_k: Number of results to return
            prioritize_tier: If True, boost scores based on tier (S+ > S > A > B > C > D)
            
        Returns:
            List of (Document, score) tuples sorted by adjusted score
        """
        # Fetch more results to allow tier reranking
        fetch_k = top_k * 3 if prioritize_tier else top_k
        base_results = self.search(query, top_k=fetch_k, doc_type='equipment')
        
        if not prioritize_tier:
            return base_results[:top_k]
        
        # Apply tier boost to scores
        adjusted_results = []
        for doc, score in base_results:
            tier = doc.metadata.get('tier', '')
            tier_rank = get_tier_rank(tier)
            # Boost: S+ gets +0.5, S gets +0.4, A gets +0.3, etc.
            tier_bonus = tier_rank * TIER_BOOST
            adjusted_score = score + tier_bonus
            adjusted_results.append((doc, adjusted_score))
        
        # Sort by adjusted score (highest first) and limit to top_k
        adjusted_results.sort(key=lambda x: x[1], reverse=True)
        
        # Apply keyword boost for direct relevance
        final_results = self._apply_keyword_boost(query, adjusted_results)
        
        return final_results[:top_k]
    
    def search_gameplay(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Search for gameplay mechanics matching the query"""
        return self.search(query, top_k=top_k, doc_type='gameplay')
    
    def search_glossary(self, query: str, top_k: int = 3) -> List[Tuple[Document, float]]:
        """Search for glossary terms matching the query"""
        return self.search(query, top_k=top_k, doc_type='glossary')

    # ------------------------------------------------------------------
    # Runtime cache-invalidation helpers
    # ------------------------------------------------------------------

    def is_stale(self) -> bool:
        """Return True if the data files have changed since the last index."""
        if not self.enabled or self._last_data_hash is None:
            return False
        return self._get_cache_hash() != self._last_data_hash

    def check_and_reindex(self) -> bool:
        """Re-index data if the underlying files changed.  Returns True if a rebuild happened."""
        if self.is_stale():
            logger.info("Data files changed since last index — rebuilding…")
            self.index_data(force_rebuild=True)
            return True
        return False

    def get_status(self) -> Dict:
        """Return a status dict useful for health / observability endpoints."""
        import datetime

        cache_file = self.cache_dir / "embeddings.pkl" if self.enabled else None
        cache_age = None
        if cache_file and cache_file.exists():
            mtime = cache_file.stat().st_mtime
            cache_age = str(datetime.datetime.fromtimestamp(mtime))

        return {
            "enabled": self.enabled,
            "document_count": len(self.documents) if self.enabled else 0,
            "cache_dir": str(self.cache_dir) if self.enabled else None,
            "cache_last_built": cache_age,
            "data_stale": self.is_stale() if self.enabled else False,
        }
