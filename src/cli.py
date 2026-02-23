"""Main CLI entry point for AstraDB Quality Check Tool."""

import logging
import sys
import click
from rich.console import Console

from .config import config
from .db.connection import AstraDBConnection
from .db.operations import DatabaseOperations
from .utils.display import (
    display_success,
    display_error,
    display_info,
    display_stats,
    console,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('astra_clean.log')
    ]
)

# Suppress verbose logging from third-party libraries
logging.getLogger('astrapy').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('huggingface_hub').setLevel(logging.WARNING)
logging.getLogger('transformers').setLevel(logging.WARNING)

# Only show errors and warnings in console for our own loggers
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Get our logger
logger = logging.getLogger(__name__)
logger.addHandler(console_handler)


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def cli(ctx):
    """
    AstraDB Quality Check Tool - Clean and refine your vector database.
    
    A comprehensive CLI tool for managing, cleaning, and optimizing
    question-answer pairs in AstraDB vector collections.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Validate configuration
    try:
        if not config.is_configured:
            display_error(
                "Configuration incomplete. Please set up your .env file with "
                "ASTRA_DB_ENDPOINT and ASTRA_DB_TOKEN."
            )
            sys.exit(1)
    except ValueError as e:
        display_error(str(e))
        sys.exit(1)


@cli.command()
@click.pass_context
def test_connection(ctx):
    """Test connection to AstraDB."""
    display_info("Testing connection to AstraDB...")
    
    try:
        with AstraDBConnection() as conn:
            info = conn.get_collection_info()
            display_success("Successfully connected to AstraDB!")
            console.print(f"\n[bold]Collection:[/bold] {info['name']}")
            console.print(f"[bold]Keyspace:[/bold] {info['keyspace']}")
            console.print(f"[bold]Approximate Documents:[/bold] {info['approximate_count']}")
            
    except Exception as e:
        display_error(f"Connection failed: {e}")
        logger.error(f"Connection test failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--detailed',
    is_flag=True,
    help='Show detailed statistics including categories and sources.'
)
@click.pass_context
def stats(ctx, detailed):
    """Display collection statistics and health metrics."""
    display_info("Gathering collection statistics...")
    
    try:
        with AstraDBConnection() as conn:
            ops = DatabaseOperations(conn)
            stats_data = ops.get_collection_stats()
            display_stats(stats_data)
            
            if detailed:
                # Additional detailed information
                console.print("\n[bold cyan]Detailed Information:[/bold cyan]")
                console.print(f"Configuration: {config}")
                
    except Exception as e:
        display_error(f"Failed to get statistics: {e}")
        logger.error(f"Stats command failed: {e}", exc_info=True)
        sys.exit(1)


@cli.group()
def search():
    """Search operations for finding documents."""
    pass


@search.command('keyword')
@click.argument('keyword')
@click.option('--fields', multiple=True, default=['question', 'answer'], help='Fields to search (can specify multiple)')
@click.option('--category', help='Filter by category')
@click.option('--source', help='Filter by source file')
@click.option('--limit', default=20, help='Maximum results to return')
@click.option('--case-sensitive', is_flag=True, help='Case-sensitive search')
@click.option('--full', is_flag=True, help='Show full text without truncation')
@click.pass_context
def search_keyword(ctx, keyword, fields, category, source, limit, case_sensitive, full):
    """Search for keyword across question/answer fields."""
    from .search.keyword import KeywordSearch
    from .utils.display import display_search_results
    
    display_info(f"Searching for '{keyword}' in {', '.join(fields)}...")
    
    try:
        with AstraDBConnection() as conn:
            searcher = KeywordSearch(conn)
            results = searcher.search(
                keyword=keyword,
                fields=list(fields),
                category=category,
                source=source,
                limit=limit,
                case_sensitive=case_sensitive
            )
            
            if results:
                display_success(f"Found {len(results)} matching Q&A pairs!")
                display_search_results(results, search_type='keyword', show_full=full)
            else:
                display_info("No results found.")
                
    except Exception as e:
        display_error(f"Search failed: {e}")
        logger.error(f"Keyword search failed: {e}", exc_info=True)
        sys.exit(1)


@search.command('similar')
@click.argument('query')
@click.option('--by-id', is_flag=True, help='Search by document ID instead of text')
@click.option('--threshold', default=0.85, type=float, help='Similarity threshold (0-1)')
@click.option('--limit', default=10, help='Maximum results to return')
@click.option('--category', help='Filter by category')
@click.option('--full', is_flag=True, help='Show full text without truncation')
@click.pass_context
def search_similar(ctx, query, by_id, threshold, limit, category, full):
    """
    Find Q&A pairs similar to a query.
    
    By default, searches by text using IBM Granite embeddings.
    Use --by-id flag to search by document ID instead.
    
    Examples:
      astra-clean search similar "What is governance?"
      astra-clean search similar <doc_id> --by-id
    """
    from .search.similarity import SimilaritySearch
    from .utils.display import display_search_results
    
    try:
        with AstraDBConnection() as conn:
            searcher = SimilaritySearch(conn)
            
            if by_id:
                # Search by document ID
                display_info(f"Finding Q&A pairs similar to document {query}...")
                results = searcher.find_similar_to_document(
                    document_id=query,
                    threshold=threshold,
                    limit=limit,
                    category=category
                )
            else:
                # Search by text (generate embedding)
                display_info(f"Finding Q&A pairs similar to: '{query[:50]}...'")
                display_info("Generating embedding using IBM Granite 30M model...")
                results = searcher.search_by_text(
                    query_text=query,
                    threshold=threshold,
                    limit=limit,
                    category=category
                )
            
            if results:
                display_success(f"Found {len(results)} similar Q&A pairs!")
                display_search_results(results, search_type='similarity', show_full=full)
            else:
                display_info(f"No similar Q&A pairs found above threshold {threshold}.")
                display_info("Try:")
                display_info("  • Lowering the threshold (e.g., --threshold 0.75)")
                display_info("  • Using different search terms")
                display_info("  • Using keyword search instead")
                
    except ImportError as e:
        display_error("Text-based similarity search requires sentence-transformers.")
        display_info("Install it with: pip install sentence-transformers")
        sys.exit(1)
    except Exception as e:
        display_error(f"Similarity search failed: {e}")
        logger.error(f"Similarity search failed: {e}", exc_info=True)
        sys.exit(1)


@search.command('category')
@click.argument('category')
@click.option('--limit', default=50, help='Maximum results to return')
@click.option('--full', is_flag=True, help='Show full text without truncation')
@click.pass_context
def search_category(ctx, category, limit, full):
    """Get all Q&A pairs in a specific category."""
    from .search.keyword import KeywordSearch
    from .utils.display import display_search_results
    
    display_info(f"Fetching all Q&A pairs in category '{category}'...")
    
    try:
        with AstraDBConnection() as conn:
            searcher = KeywordSearch(conn)
            results = searcher.search_by_category(
                category=category,
                limit=limit
            )
            
            if results:
                display_success(f"Found {len(results)} Q&A pairs in category '{category}'!")
                display_search_results(results, search_type='category', show_full=full)
            else:
                display_info(f"No Q&A pairs found in category '{category}'.")
                
    except Exception as e:
        display_error(f"Category search failed: {e}")
        logger.error(f"Category search failed: {e}", exc_info=True)
        sys.exit(1)


@search.command('source')
@click.argument('source_file')
@click.option('--limit', default=100, help='Maximum results to return')
@click.option('--full', is_flag=True, help='Show full text without truncation')
@click.pass_context
def search_source(ctx, source_file, limit, full):
    """Get all Q&A pairs from a specific source file."""
    from .search.keyword import KeywordSearch
    from .utils.display import display_search_results
    
    display_info(f"Fetching all Q&A pairs from source '{source_file}'...")
    
    try:
        with AstraDBConnection() as conn:
            searcher = KeywordSearch(conn)
            results = searcher.search_by_source(
                source_file=source_file,
                limit=limit
            )
            
            if results:
                display_success(f"Found {len(results)} Q&A pairs from source '{source_file}'!")
                display_search_results(results, search_type='source', show_full=full)
            else:
                display_info(f"No Q&A pairs found from source '{source_file}'.")
                
    except Exception as e:
        display_error(f"Source search failed: {e}")
        logger.error(f"Source search failed: {e}", exc_info=True)
        sys.exit(1)


@cli.group()
def duplicates():
    """Duplicate detection and management."""
    pass


@cli.group()
def quality():
    """Quality checking and validation."""
    pass


@cli.group()
def export():
    """Export data to various formats."""
    pass


@cli.group()
def import_cmd():
    """Import data from files."""
    pass


@cli.group()
def audit():
    """Audit log and undo operations."""
    pass


@cli.command()
@click.argument('doc_id')
@click.option('--question', help='New question text')
@click.option('--answer', help='New answer text')
@click.option('--category', help='New category')
@click.option('--source', help='New source file')
@click.option('--no-vector', is_flag=True, help='Skip vector regeneration (faster but less accurate for search)')
@click.pass_context
def update(ctx, doc_id, question, answer, category, source, no_vector):
    """
    Update a document by ID.
    
    By default, when updating question or answer, the vector embedding is automatically
    regenerated from the combined question + answer text for optimal search accuracy.
    Use --no-vector to skip this step for faster updates.
    """
    if not any([question, answer, category, source]):
        display_error("At least one field must be specified for update.")
        sys.exit(1)
    
    display_info(f"Updating document {doc_id}...")
    
    try:
        with AstraDBConnection() as conn:
            ops = DatabaseOperations(conn)
            
            # Build update dictionary
            update_data = {}
            if question:
                update_data['question'] = question
            if answer:
                update_data['answer'] = answer
            if category:
                update_data['category'] = category
            if source:
                update_data['source_file'] = source
            
            # Determine if we should regenerate vector
            regenerate = not no_vector and (question or answer)
            
            if regenerate:
                display_info("Regenerating vector embedding from question + answer...")
            
            # Perform update with optional vector regeneration
            success = ops.update_document(doc_id, update_data, regenerate_vector=regenerate)
            
            if success:
                if regenerate:
                    display_success(f"Document {doc_id} updated with new vector embedding!")
                else:
                    display_success(f"Document {doc_id} updated successfully!")
            else:
                display_error(f"Document {doc_id} not found or update failed.")
                sys.exit(1)
                
    except Exception as e:
        display_error(f"Update failed: {e}")
        logger.error(f"Update command failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('doc_id')
@click.confirmation_option(prompt='Are you sure you want to delete this document?')
@click.pass_context
def delete(ctx, doc_id):
    """Delete a document by ID."""
    display_info(f"Deleting document {doc_id}...")
    
    try:
        with AstraDBConnection() as conn:
            ops = DatabaseOperations(conn)
            success = ops.delete_document(doc_id)
            
            if success:
                display_success(f"Document {doc_id} deleted successfully!")
            else:
                display_error(f"Document {doc_id} not found.")
                sys.exit(1)
                
    except Exception as e:
        display_error(f"Delete failed: {e}")
        logger.error(f"Delete command failed: {e}", exc_info=True)
        sys.exit(1)

@cli.command('delete-unanswered')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
@click.confirmation_option(prompt='Are you sure you want to delete ALL unanswered documents?')
@click.pass_context
def delete_unanswered(ctx, dry_run):
    """Delete all documents with 'unanswered' as the answer."""
    display_info("Searching for unanswered documents...")
    
    try:
        with AstraDBConnection() as conn:
            ops = DatabaseOperations(conn)
            
            # Find all unanswered documents (fetch in batches due to AstraDB limits)
            unanswered_docs = []
            batch_size = 1000
            has_more = True
            
            while has_more:
                batch = ops.get_documents(
                    filter_dict={"answer": "unanswered"},
                    limit=batch_size
                )
                
                if not batch:
                    has_more = False
                else:
                    unanswered_docs.extend(batch)
                    # If we got less than batch_size, we've reached the end
                    if len(batch) < batch_size:
                        has_more = False
            
            if not unanswered_docs:
                display_info("No unanswered documents found.")
                return
            
            display_info(f"Found {len(unanswered_docs)} unanswered documents.")
            
            if dry_run:
                display_info("DRY RUN - No documents will be deleted. Here's what would be deleted:")
                from .utils.display import display_search_results
                display_search_results(unanswered_docs[:20], search_type='general')
                if len(unanswered_docs) > 20:
                    display_info(f"... and {len(unanswered_docs) - 20} more documents")
                return
            
            # Delete all unanswered documents
            display_info(f"Deleting {len(unanswered_docs)} documents...")
            deleted_count = 0
            
            for doc in unanswered_docs:
                doc_id = doc.get('_id')
                if doc_id and ops.delete_document(doc_id):
                    deleted_count += 1
            
            display_success(f"Successfully deleted {deleted_count} out of {len(unanswered_docs)} unanswered documents!")
                
    except Exception as e:
        display_error(f"Bulk delete failed: {e}")
        logger.error(f"Bulk delete command failed: {e}", exc_info=True)
        sys.exit(1)



@cli.command()
@click.argument('doc_id')
@click.pass_context
def show(ctx, doc_id):
    """Show detailed information about a document."""
    display_info(f"Retrieving document {doc_id}...")
    
    try:
        with AstraDBConnection() as conn:
            ops = DatabaseOperations(conn)
            doc = ops.get_document_by_id(doc_id)
            
            if doc:
                from .utils.display import display_document_detail
                display_document_detail(doc)
            else:
                display_error(f"Document {doc_id} not found.")
                sys.exit(1)
                
    except Exception as e:
        display_error(f"Failed to retrieve document: {e}")
        logger.error(f"Show command failed: {e}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        cli(obj={})
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        logger.error(f"Unexpected error in main: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
