"""AstraDB connection handler."""

import logging
from typing import Optional
from astrapy import DataAPIClient
from astrapy.exceptions import DataAPIException

from ..config import config

logger = logging.getLogger(__name__)


class AstraDBConnection:
    """Manages connection to AstraDB and provides access to collections."""

    def __init__(self):
        """Initialize AstraDB connection."""
        self._client: Optional[DataAPIClient] = None
        self._database = None
        self._collection = None
        self._connected = False

    def connect(self) -> bool:
        """
        Establish connection to AstraDB.

        Returns:
            bool: True if connection successful, False otherwise.

        Raises:
            ValueError: If configuration is invalid.
            DataAPIException: If connection fails.
        """
        try:
            if not config.is_configured:
                raise ValueError(
                    "AstraDB configuration is incomplete. "
                    "Please check your .env file."
                )

            logger.info("Connecting to AstraDB...")

            # Initialize the client
            self._client = DataAPIClient(config.astra_db_token)

            # Get database reference
            self._database = self._client.get_database(
                config.astra_db_endpoint,
                keyspace=config.astra_db_keyspace
            )

            # Get collection reference
            self._collection = self._database.get_collection(
                config.astra_db_collection
            )

            # Test connection by getting collection info
            _ = self._collection.options()

            self._connected = True
            logger.info(
                f"Successfully connected to collection '{config.astra_db_collection}' "
                f"in keyspace '{config.astra_db_keyspace}'"
            )
            return True

        except DataAPIException as e:
            logger.error(f"Failed to connect to AstraDB: {e}")
            self._connected = False
            raise
        except Exception as e:
            logger.error(f"Unexpected error during connection: {e}")
            self._connected = False
            raise

    def disconnect(self):
        """Close the AstraDB connection."""
        if self._client:
            # Note: astrapy doesn't require explicit disconnection
            # but we'll reset our references
            self._client = None
            self._database = None
            self._collection = None
            self._connected = False
            logger.info("Disconnected from AstraDB")

    @property
    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._connected

    @property
    def collection(self):
        """
        Get the collection object.

        Returns:
            Collection: The AstraDB collection object.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._connected or not self._collection:
            raise RuntimeError(
                "Not connected to AstraDB. Call connect() first."
            )
        return self._collection

    @property
    def database(self):
        """
        Get the database object.

        Returns:
            Database: The AstraDB database object.

        Raises:
            RuntimeError: If not connected.
        """
        if not self._connected or not self._database:
            raise RuntimeError(
                "Not connected to AstraDB. Call connect() first."
            )
        return self._database

    def get_collection_info(self) -> dict:
        """
        Get information about the collection.

        Returns:
            dict: Collection metadata and statistics.
        """
        if not self.is_connected:
            raise RuntimeError("Not connected to AstraDB")

        try:
            options = self._collection.options()
            
            # Try to get document count, but handle large collections
            try:
                count_result = self._collection.count_documents({}, upper_bound=1000)
            except Exception as count_error:
                logger.warning(f"Could not get exact count: {count_error}")
                count_result = "1000+ (large collection)"
            
            return {
                "name": config.astra_db_collection,
                "keyspace": config.astra_db_keyspace,
                "options": options,
                "approximate_count": count_result,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return (
            f"AstraDBConnection("
            f"collection={config.astra_db_collection}, "
            f"status={status})"
        )
