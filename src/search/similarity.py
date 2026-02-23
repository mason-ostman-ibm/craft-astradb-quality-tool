"""Similarity search using vector embeddings in AstraDB."""

import logging
import os
import warnings
from typing import List, Dict, Any, Optional
from ..db.connection import AstraDBConnection

# Suppress transformers progress bars and warnings
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_PROGRESS_BARS'] = '1'

# Suppress warnings
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


class SimilaritySearch:
    """Handles vector similarity search for finding similar Q&A pairs."""
    
    def __init__(self, connection: AstraDBConnection):
        """
        Initialize similarity search.
        
        Args:
            connection: Active AstraDB connection
        """
        self.connection = connection
        self._embedding_model = None
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading IBM Granite embedding model...")
                # Load model with progress bars disabled
                self._embedding_model = SentenceTransformer(
                    'ibm-granite/granite-embedding-30m-english',
                    device='cpu'  # Explicitly set device to avoid warnings
                )
                logger.info("Embedding model loaded successfully")
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise ImportError(
                    "sentence-transformers is required for text-based similarity search. "
                    "Install it with: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
        return self._embedding_model
    
    def search_by_text(
        self,
        query_text: str,
        threshold: float = 0.85,
        limit: int = 10,
        category: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar Q&A pairs using text query.
        Generates embeddings using IBM Granite 30M model.
        
        Args:
            query_text: Text to search for
            threshold: Similarity threshold (0-1)
            limit: Maximum results
            category: Filter by category
            source: Filter by source file
            
        Returns:
            List of similar documents with similarity scores (including question and answer similarities)
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Generating embedding for query: '{query_text[:50]}...'")
            
            # Generate embedding using the same model used for the collection
            query_embedding = self.embedding_model.encode(
                query_text,
                show_progress_bar=False,
                convert_to_numpy=True
            ).tolist()
            
            logger.info(f"Embedding generated, searching with threshold {threshold}")
            
            # Use the vector search with the generated embedding
            results = self.search_by_vector(
                query_vector=query_embedding,
                threshold=threshold,
                limit=limit * 3,  # Get more results for post-processing
                category=category,
                source=source
            )
            
            # Calculate separate similarity scores for questions and answers
            logger.info("Calculating separate question and answer similarity scores...")
            enhanced_results = []
            
            for doc in results:
                question = doc.get('question', '')
                answer = doc.get('answer', '')
                
                # Generate embeddings for question and answer
                if question and question != 'N/A':
                    question_embedding = self.embedding_model.encode(
                        question,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    ).tolist()
                    question_similarity = self._cosine_similarity(query_embedding, question_embedding)
                else:
                    question_similarity = 0.0
                
                if answer and answer not in ['N/A', 'unanswered', '']:
                    answer_embedding = self.embedding_model.encode(
                        answer,
                        show_progress_bar=False,
                        convert_to_numpy=True
                    ).tolist()
                    answer_similarity = self._cosine_similarity(query_embedding, answer_embedding)
                else:
                    answer_similarity = 0.0
                
                # Add the detailed similarity scores
                doc['question_similarity'] = question_similarity
                doc['answer_similarity'] = answer_similarity
                doc['overall_similarity'] = doc.get('similarity_score', 0.0)
                
                enhanced_results.append(doc)
            
            # Sort by overall similarity and return top results
            enhanced_results.sort(key=lambda x: x.get('overall_similarity', 0), reverse=True)
            return enhanced_results[:limit]
            
        except Exception as e:
            logger.error(f"Text-based similarity search failed: {e}")
            raise
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        import math
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        return dot_product / (magnitude1 * magnitude2)
    
    def search_by_vector(
        self,
        query_vector: List[float],
        threshold: float = 0.85,
        limit: int = 10,
        category: Optional[str] = None,
        source: Optional[str] = None,
        exclude_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar Q&A pairs using a vector.
        
        Args:
            query_vector: Vector embedding to search with
            threshold: Similarity threshold (0-1)
            limit: Maximum results
            category: Filter by category
            source: Filter by source file
            exclude_id: Exclude a specific document ID (useful for finding duplicates)
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Searching for similar vectors with threshold {threshold}")
            
            # Build filter
            filter_dict = {}
            if category:
                filter_dict["category"] = category
            if source:
                filter_dict["source_file"] = source
            if exclude_id:
                filter_dict["_id"] = {"$ne": exclude_id}
            
            # Perform vector search
            results = self.connection.collection.find(
                filter=filter_dict if filter_dict else None,
                sort={"$vector": query_vector},
                limit=limit,
                projection={
                    "_id": 1,
                    "question": 1,
                    "answer": 1,
                    "category": 1,
                    "source_file": 1,
                    "document_date": 1
                },
                include_similarity=True
            )
            
            # Filter by threshold
            filtered_results = []
            for doc in results:
                similarity = doc.get('$similarity', 0)
                if similarity >= threshold:
                    doc['similarity_score'] = similarity
                    filtered_results.append(doc)
            
            logger.info(f"Found {len(filtered_results)} results above threshold {threshold}")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Vector similarity search failed: {e}")
            raise
    
    def find_similar_to_document(
        self,
        document_id: str,
        threshold: float = 0.85,
        limit: int = 10,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to a specific document.
        
        Args:
            document_id: ID of the document to find similar items for
            threshold: Similarity threshold (0-1)
            limit: Maximum results
            category: Filter by category
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Finding documents similar to {document_id}")
            
            # Get the source document
            source_doc = self.connection.collection.find_one(
                filter={"_id": document_id},
                projection={"$vector": 1}
            )
            
            if not source_doc:
                raise ValueError(f"Document {document_id} not found")
            
            if "$vector" not in source_doc:
                raise ValueError(f"Document {document_id} has no vector embedding")
            
            # Search using the document's vector
            return self.search_by_vector(
                query_vector=source_doc["$vector"],
                threshold=threshold,
                limit=limit,
                category=category,
                exclude_id=document_id  # Don't include the source document
            )
            
        except Exception as e:
            logger.error(f"Failed to find similar documents: {e}")
            raise
    
    def find_potential_duplicates(
        self,
        threshold: float = 0.90,
        limit_per_query: int = 5,
        sample_size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Find potential duplicate Q&A pairs based on high similarity.
        
        This scans the collection and finds groups of highly similar questions.
        
        Args:
            threshold: Similarity threshold for duplicates (default 0.90)
            limit_per_query: Max similar items to find per document
            sample_size: Optional limit on documents to check (for large collections)
            
        Returns:
            List of duplicate groups with similarity scores
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            logger.info(f"Scanning for potential duplicates with threshold {threshold}")
            
            # Get all documents (or sample)
            if sample_size:
                cursor = self.connection.collection.find(
                    limit=sample_size,
                    projection={"_id": 1, "question": 1, "$vector": 1}
                )
            else:
                cursor = self.connection.collection.find(
                    projection={"_id": 1, "question": 1, "$vector": 1}
                )
            
            documents = list(cursor)
            logger.info(f"Checking {len(documents)} documents for duplicates")
            
            # Track which documents we've already grouped
            processed_ids = set()
            duplicate_groups = []
            
            for doc in documents:
                doc_id = str(doc["_id"])
                
                # Skip if already in a group
                if doc_id in processed_ids:
                    continue
                
                # Find similar documents
                similar = self.find_similar_to_document(
                    document_id=doc_id,
                    threshold=threshold,
                    limit=limit_per_query
                )
                
                if similar:
                    # Create a group
                    group = {
                        "primary": {
                            "_id": doc_id,
                            "question": doc.get("question", "")
                        },
                        "duplicates": similar,
                        "count": len(similar) + 1
                    }
                    duplicate_groups.append(group)
                    
                    # Mark all as processed
                    processed_ids.add(doc_id)
                    for sim_doc in similar:
                        processed_ids.add(str(sim_doc["_id"]))
            
            logger.info(f"Found {len(duplicate_groups)} potential duplicate groups")
            return duplicate_groups
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            raise
    
    def compare_questions(
        self,
        question1_id: str,
        question2_id: str
    ) -> Dict[str, Any]:
        """
        Compare two specific questions and return their similarity.
        
        Args:
            question1_id: First question document ID
            question2_id: Second question document ID
            
        Returns:
            Comparison result with similarity score
        """
        if not self.connection.is_connected:
            raise RuntimeError("Not connected to AstraDB")
        
        try:
            # Get both documents
            doc1 = self.connection.collection.find_one(
                filter={"_id": question1_id},
                projection={"_id": 1, "question": 1, "answer": 1, "$vector": 1}
            )
            
            doc2 = self.connection.collection.find_one(
                filter={"_id": question2_id},
                projection={"_id": 1, "question": 1, "answer": 1, "$vector": 1}
            )
            
            if not doc1 or not doc2:
                raise ValueError("One or both documents not found")
            
            if "$vector" not in doc1 or "$vector" not in doc2:
                raise ValueError("One or both documents missing vector embeddings")
            
            # Calculate similarity using vector search
            similar = self.search_by_vector(
                query_vector=doc1["$vector"],
                threshold=0.0,  # Get all results
                limit=1,
                exclude_id=question1_id
            )
            
            # Find doc2 in results
            similarity_score = 0.0
            for result in similar:
                if str(result["_id"]) == question2_id:
                    similarity_score = result.get("similarity_score", 0.0)
                    break
            
            return {
                "document1": {
                    "_id": question1_id,
                    "question": doc1.get("question", ""),
                    "answer": doc1.get("answer", "")
                },
                "document2": {
                    "_id": question2_id,
                    "question": doc2.get("question", ""),
                    "answer": doc2.get("answer", "")
                },
                "similarity_score": similarity_score,
                "is_likely_duplicate": similarity_score >= 0.90
            }
            
        except Exception as e:
            logger.error(f"Question comparison failed: {e}")
            raise
