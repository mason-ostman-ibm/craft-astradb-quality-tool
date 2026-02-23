"""Keyword search functionality for AstraDB collection."""

import logging
from typing import List, Dict, Any, Optional
from ..db.connection import AstraDBConnection

logger = logging.getLogger(__name__)


class KeywordSearch:
    """Handles keyword-based text search across Q&A pairs."""
    
    def __init__(self, connection: AstraDBConnection):
        """
        Initialize keyword search.
        
        Args:
            connection: Active AstraDB connection
        """
        self.connection = connection
    
    def search(
        self,
        keyword: str,
        fields: Optional[List[str]] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 20,
        case_sensitive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search for keyword across specified fields.
        
        Note: AstraDB Data API doesn't support $regex, so we fetch documents
        and filter in Python. For large collections, this may be slow.
        
        Args:
            keyword: Search term
            fields: Fields to search in (default: ['question', 'answer'])
            category: Filter by category
            source: Filter by source file
            limit: Maximum results to return
            case_sensitive: Whether search is case-sensitive
            
        Returns:
            List of matching documents with relevance scores
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        fields = fields or ['question', 'answer']
        
        # Build base filter for category/source
        base_filter = {}
        if category:
            base_filter["category"] = category
        if source:
            base_filter["source_file"] = source
        
        try:
            logger.info(f"Searching for keyword '{keyword}' in fields {fields}")
            
            # Fetch documents with base filter
            # Note: For large collections, we fetch more than needed and filter client-side
            fetch_limit = min(limit * 10, 1000)  # Fetch 10x limit or max 1000
            
            cursor = self.connection.collection.find(
                filter=base_filter if base_filter else None,
                limit=fetch_limit,
                projection={
                    "_id": 1,
                    "question": 1,
                    "answer": 1,
                    "category": 1,
                    "source_file": 1,
                    "document_date": 1,
                    "upload_timestamp": 1
                }
            )
            
            all_docs = list(cursor)
            logger.info(f"Fetched {len(all_docs)} documents for filtering")
            
            # Filter documents client-side
            keyword_lower = keyword if case_sensitive else keyword.lower()
            matching_docs = []
            
            for doc in all_docs:
                matches = False
                for field in fields:
                    if field in doc and doc[field]:
                        text = str(doc[field])
                        text_compare = text if case_sensitive else text.lower()
                        if keyword_lower in text_compare:
                            matches = True
                            break
                
                if matches:
                    # Calculate relevance score
                    score = self._calculate_relevance(doc, keyword, fields, case_sensitive)
                    doc['relevance_score'] = score
                    matching_docs.append(doc)
            
            # Sort by relevance score (highest first)
            matching_docs.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            # Limit results
            results = matching_docs[:limit]
            
            logger.info(f"Found {len(results)} matching results")
            return results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            raise
    
    def _calculate_relevance(
        self,
        doc: Dict[str, Any],
        keyword: str,
        fields: List[str],
        case_sensitive: bool
    ) -> float:
        """
        Calculate relevance score for a document.
        
        Score is based on:
        - Number of keyword occurrences
        - Field where keyword appears (question > answer)
        - Position of keyword (earlier = higher score)
        
        Args:
            doc: Document to score
            keyword: Search keyword
            fields: Fields that were searched
            case_sensitive: Whether search was case-sensitive
            
        Returns:
            Relevance score (0-100)
        """
        score = 0.0
        keyword_lower = keyword if case_sensitive else keyword.lower()
        
        # Question matches are worth more
        field_weights = {
            'question': 2.0,
            'answer': 1.0,
            'category': 0.5,
            'source_file': 0.3
        }
        
        for field in fields:
            if field not in doc or not doc[field]:
                continue
            
            text = str(doc[field])
            text_lower = text if case_sensitive else text.lower()
            
            # Count occurrences
            occurrences = text_lower.count(keyword_lower)
            if occurrences > 0:
                weight = field_weights.get(field, 1.0)
                
                # Base score from occurrences
                occurrence_score = min(occurrences * 10, 50)  # Cap at 50
                
                # Position bonus (earlier = better)
                position = text_lower.find(keyword_lower)
                position_score = max(0, 20 - (position / len(text) * 20))
                
                # Exact word match bonus
                words = text_lower.split()
                if keyword_lower in words:
                    exact_match_bonus = 15
                else:
                    exact_match_bonus = 0
                
                field_score = (occurrence_score + position_score + exact_match_bonus) * weight
                score += field_score
        
        return min(score, 100.0)  # Cap at 100
    
    def search_by_category(
        self,
        category: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all Q&A pairs in a specific category.
        
        Args:
            category: Category to filter by
            limit: Maximum results
            
        Returns:
            List of documents in category
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Fetching all entries in category '{category}'")
            
            cursor = self.connection.collection.find(
                filter={"category": category},
                limit=limit,
                projection={
                    "_id": 1,
                    "question": 1,
                    "answer": 1,
                    "category": 1,
                    "source_file": 1,
                    "document_date": 1
                }
            )
            
            results = list(cursor)
            logger.info(f"Found {len(results)} entries in category '{category}'")
            return results
            
        except Exception as e:
            logger.error(f"Category search failed: {e}")
            raise
    
    def search_by_source(
        self,
        source_file: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all Q&A pairs from a specific source file.
        
        Args:
            source_file: Source file name to filter by
            limit: Maximum results
            
        Returns:
            List of documents from source
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Fetching all entries from source '{source_file}'")
            
            cursor = self.connection.collection.find(
                filter={"source_file": source_file},
                limit=limit,
                projection={
                    "_id": 1,
                    "question": 1,
                    "answer": 1,
                    "category": 1,
                    "source_file": 1,
                    "document_date": 1
                }
            )
            
            results = list(cursor)
            logger.info(f"Found {len(results)} entries from source '{source_file}'")
            return results
            
        except Exception as e:
            logger.error(f"Source search failed: {e}")
            raise
    
    def advanced_search(
        self,
        query: Dict[str, Any],
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Perform advanced search with custom MongoDB-style query.
        
        Args:
            query: MongoDB-style filter query
            limit: Maximum results
            
        Returns:
            List of matching documents
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Executing advanced search with query: {query}")
            
            cursor = self.connection.collection.find(
                filter=query,
                limit=limit
            )
            
            results = list(cursor)
            logger.info(f"Advanced search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Advanced search failed: {e}")
            raise
