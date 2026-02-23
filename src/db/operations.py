"""Database operations for AstraDB collection."""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .connection import AstraDBConnection

logger = logging.getLogger(__name__)


class DatabaseOperations:
    """Handles CRUD operations on the AstraDB collection."""

    def __init__(self, connection: AstraDBConnection):
        """
        Initialize database operations.

        Args:
            connection: Active AstraDB connection.
        """
        self.connection = connection

    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a document by its ID.

        Args:
            doc_id: The document ID.

        Returns:
            Document data or None if not found.
        """
        try:
            result = self.connection.collection.find_one({"_id": doc_id})
            return result
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            raise

    def get_documents(
        self,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        skip: int = 0,
        projection: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve multiple documents with optional filtering.

        Args:
            filter_dict: MongoDB-style filter dictionary.
            limit: Maximum number of documents to return.
            skip: Number of documents to skip.
            projection: Fields to include/exclude.

        Returns:
            List of documents.
        """
        try:
            filter_dict = filter_dict or {}
            
            # Build find parameters - skip is not allowed without sort in AstraDB
            find_params = {
                "filter": filter_dict,
                "limit": limit,
            }
            
            if projection:
                find_params["projection"] = projection
            
            # Only add skip if it's non-zero AND we have a sort (AstraDB requirement)
            # For now, we don't use skip to avoid the error
            if skip > 0:
                logger.warning(f"Skip parameter ({skip}) ignored - AstraDB requires sort clause with skip")
            
            cursor = self.connection.collection.find(**find_params)
            
            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            raise

    def count_documents(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.

        Args:
            filter_dict: MongoDB-style filter dictionary.

        Returns:
            Number of matching documents or -1 if count exceeds limit.
        """
        try:
            filter_dict = filter_dict or {}
            return self.connection.collection.count_documents(
                filter=filter_dict,
                upper_bound=1000
            )
        except Exception as e:
            # For large collections, return -1 to indicate unknown count
            logger.warning(f"Could not count documents: {e}")
            return -1

    def update_document(
        self,
        doc_id: str,
        update_data: Dict[str, Any],
        upsert: bool = False,
        regenerate_vector: bool = False,
    ) -> bool:
        """
        Update a document by ID.

        Args:
            doc_id: The document ID.
            update_data: Fields to update.
            upsert: Create document if it doesn't exist.
            regenerate_vector: If True, regenerate the vector embedding when question or answer changes.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Add update timestamp
            update_data["last_modified"] = datetime.utcnow().isoformat()
            
            # If regenerating vector and question/answer changed, generate new embedding
            if regenerate_vector and ('question' in update_data or 'answer' in update_data):
                # Get current document to merge with updates
                current_doc = self.get_document_by_id(doc_id)
                if current_doc:
                    # Merge current and new data
                    question = update_data.get('question', current_doc.get('question', ''))
                    answer = update_data.get('answer', current_doc.get('answer', ''))
                    
                    # Generate new vector from combined question + answer
                    if question and answer and answer not in ['unanswered', 'N/A', '']:
                        combined_text = f"{question} {answer}"
                    else:
                        combined_text = question
                    
                    # Generate embedding
                    try:
                        from sentence_transformers import SentenceTransformer
                        logger.info("Generating new vector embedding...")
                        model = SentenceTransformer('ibm-granite/granite-embedding-30m-english', device='cpu')
                        new_vector = model.encode(
                            combined_text,
                            show_progress_bar=False,
                            convert_to_numpy=True
                        ).tolist()
                        update_data['$vector'] = new_vector
                        logger.info("Vector embedding generated successfully")
                    except Exception as e:
                        logger.warning(f"Failed to generate vector embedding: {e}")
                        # Continue with update even if vector generation fails
            
            result = self.connection.collection.update_one(
                filter={"_id": doc_id},
                update={"$set": update_data},
                upsert=upsert,
            )
            
            # AstraDB returns update_info dict with fields: n, updatedExisting, ok, nModified
            if hasattr(result, 'update_info'):
                # n: number of documents matched
                # updatedExisting: True if existing doc was updated, False if new doc created
                # ok: operation success status (1.0 = success)
                matched = result.update_info.get('n', 0) > 0
                ok_status = result.update_info.get('ok', 0) == 1.0
                
                logger.info(f"Update result - matched: {matched}, ok: {ok_status}")
                logger.info(f"Full update_info: {result.update_info}")
                
                # Success if document was found (n > 0) AND operation succeeded (ok = 1.0)
                return matched and ok_status
            
            # Fallback: if update_one succeeded without error, consider it successful
            logger.info("No update_info attribute, assuming success")
            return True
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise

    def update_many(
        self,
        filter_dict: Dict[str, Any],
        update_data: Dict[str, Any],
    ) -> int:
        """
        Update multiple documents matching the filter.

        Args:
            filter_dict: MongoDB-style filter dictionary.
            update_data: Fields to update.

        Returns:
            Number of documents updated.
        """
        try:
            # Add update timestamp
            update_data["last_modified"] = datetime.utcnow().isoformat()
            
            result = self.connection.collection.update_many(
                filter=filter_dict,
                update={"$set": update_data},
            )
            
            # AstraDB returns update_info dict with nModified field
            if hasattr(result, 'update_info'):
                return result.update_info.get('nModified', 0)
            return 0
        except Exception as e:
            logger.error(f"Error updating multiple documents: {e}")
            raise

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document by ID.

        Args:
            doc_id: The document ID.

        Returns:
            True if deleted, False if not found.
        """
        try:
            result = self.connection.collection.delete_one({"_id": doc_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise

    def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """
        Delete multiple documents matching the filter.

        Args:
            filter_dict: MongoDB-style filter dictionary.

        Returns:
            Number of documents deleted.
        """
        try:
            result = self.connection.collection.delete_many(filter=filter_dict)
            return result.deleted_count
        except Exception as e:
            logger.error(f"Error deleting multiple documents: {e}")
            raise

    def insert_document(self, document: Dict[str, Any]) -> str:
        """
        Insert a new document.

        Args:
            document: Document data to insert.

        Returns:
            The inserted document ID.
        """
        try:
            # Add creation timestamp
            document["created_at"] = datetime.utcnow().isoformat()
            
            result = self.connection.collection.insert_one(document)
            return result.inserted_id
        except Exception as e:
            logger.error(f"Error inserting document: {e}")
            raise

    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Insert multiple documents.

        Args:
            documents: List of documents to insert.

        Returns:
            List of inserted document IDs.
        """
        try:
            # Add creation timestamp to all documents
            timestamp = datetime.utcnow().isoformat()
            for doc in documents:
                doc["created_at"] = timestamp
            
            result = self.connection.collection.insert_many(documents)
            return result.inserted_ids
        except Exception as e:
            logger.error(f"Error inserting multiple documents: {e}")
            raise

    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories from the collection.

        Returns:
            List of unique category values.
        """
        try:
            # Use distinct to get unique values
            categories = self.connection.collection.distinct("category")
            return [cat for cat in categories if cat]  # Filter out None/empty
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            raise

    def get_all_sources(self) -> List[str]:
        """
        Get all unique source files from the collection.

        Returns:
            List of unique source_file values.
        """
        try:
            sources = self.connection.collection.distinct("source_file")
            return [src for src in sources if src]  # Filter out None/empty
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection.

        Returns:
            Dictionary with collection statistics.
        """
        try:
            total_docs = self.count_documents()
            categories = self.get_all_categories()
            sources = self.get_all_sources()
            
            # Count documents with empty fields (only if we can count)
            if total_docs >= 0:
                empty_questions = self.count_documents(
                    {"$or": [{"question": ""}, {"question": None}]}
                )
                empty_answers = self.count_documents(
                    {"$or": [{"answer": ""}, {"answer": None}]}
                )
            else:
                empty_questions = -1
                empty_answers = -1
            
            # Format total_docs for display
            total_docs_display = "1000+" if total_docs == -1 else total_docs
            
            return {
                "total_documents": total_docs_display,
                "unique_categories": len(categories),
                "unique_sources": len(sources),
                "categories": categories,
                "sources": sources,
                "empty_questions": empty_questions if empty_questions >= 0 else "Unknown",
                "empty_answers": empty_answers if empty_answers >= 0 else "Unknown",
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
