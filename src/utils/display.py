"""Display utilities using Rich library for beautiful CLI output."""

from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()


def create_table(
    title: str,
    columns: List[tuple],
    rows: List[List[Any]],
    show_lines: bool = False,
) -> Table:
    """
    Create a Rich table with specified columns and rows.

    Args:
        title: Table title.
        columns: List of (column_name, column_style) tuples.
        rows: List of row data.
        show_lines: Whether to show lines between rows.

    Returns:
        Rich Table object.
    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        show_lines=show_lines,
    )

    # Add columns
    for col_name, col_style in columns:
        table.add_column(col_name, style=col_style)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table


def display_documents(
    documents: List[Dict[str, Any]],
    title: str = "Documents",
    show_vector: bool = False,
    max_text_length: int = 50,
) -> None:
    """
    Display documents in a formatted table.

    Args:
        documents: List of document dictionaries.
        title: Table title.
        show_vector: Whether to show vector data.
        max_text_length: Maximum length for text fields before truncation.
    """
    if not documents:
        console.print("[yellow]No documents found.[/yellow]")
        return

    # Define columns
    columns = [
        ("ID", "cyan"),
        ("Question", "green"),
        ("Answer", "blue"),
        ("Category", "magenta"),
        ("Source", "yellow"),
    ]

    if show_vector:
        columns.append(("Vector Dim", "red"))

    rows = []
    for doc in documents:
        question = doc.get("question", "")
        answer = doc.get("answer", "")
        
        # Truncate long text
        if len(question) > max_text_length:
            question = question[:max_text_length] + "..."
        if len(answer) > max_text_length:
            answer = answer[:max_text_length] + "..."

        row = [
            doc.get("_id", "N/A"),
            question,
            answer,
            doc.get("category", "N/A"),
            doc.get("source_file", "N/A"),
        ]

        if show_vector:
            vector = doc.get("$vector", [])
            row.append(len(vector) if vector else 0)

        rows.append(row)

    table = create_table(title, columns, rows, show_lines=True)
    console.print(table)


def display_document_detail(document: Dict[str, Any]) -> None:
    """
    Display a single document with all details.

    Args:
        document: Document dictionary.
    """
    if not document:
        console.print("[yellow]Document not found.[/yellow]")
        return

    # Create a panel with document details
    details = []
    
    # Core fields
    details.append(f"[bold cyan]ID:[/bold cyan] {document.get('_id', 'N/A')}")
    details.append(f"[bold green]Question:[/bold green]\n{document.get('question', 'N/A')}")
    details.append(f"[bold blue]Answer:[/bold blue]\n{document.get('answer', 'N/A')}")
    
    # Metadata
    details.append(f"\n[bold yellow]Metadata:[/bold yellow]")
    details.append(f"  Category: {document.get('category', 'N/A')}")
    details.append(f"  Source: {document.get('source_file', 'N/A')}")
    details.append(f"  Sheet: {document.get('sheet_name', 'N/A')}")
    details.append(f"  Version: {document.get('version', 'N/A')}")
    details.append(f"  Document Date: {document.get('document_date', 'N/A')}")
    details.append(f"  Upload Time: {document.get('upload_timestamp', 'N/A')}")
    
    # Vector info
    vector = document.get("$vector", [])
    if vector:
        details.append(f"\n[bold red]Vector:[/bold red] {len(vector)} dimensions")

    panel = Panel(
        "\n".join(details),
        title="Document Details",
        border_style="cyan",
    )
    console.print(panel)


def display_search_results(results: List[Dict[str, Any]], search_type: str = 'general', show_full: bool = False) -> None:
    """
    Display search results in a formatted table or detailed panels.
    
    Args:
        results: List of search result documents
        search_type: Type of search ('keyword', 'similarity', 'category', 'source')
        show_full: Whether to show full text without truncation
    """
    from rich.table import Table
    from rich.panel import Panel
    from rich.columns import Columns
    
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    
    # If showing full details, use panel format for better readability
    if show_full:
        console.print(f"\n[bold cyan]Search Results ({len(results)} found)[/bold cyan]\n")
        
        for idx, doc in enumerate(results, 1):
            doc_id = str(doc.get('_id', 'N/A'))
            question = doc.get('question', 'N/A')
            answer = doc.get('answer', 'N/A')
            category = doc.get('category', 'N/A')
            source = doc.get('source_file', 'N/A')
            
            # Build the content
            content_lines = []
            content_lines.append(f"[bold cyan]ID:[/bold cyan] {doc_id}")
            content_lines.append(f"\n[bold green]Question:[/bold green]\n{question}")
            content_lines.append(f"\n[bold white]Answer:[/bold white]\n{answer}")
            content_lines.append(f"\n[bold yellow]Category:[/bold yellow] {category}")
            content_lines.append(f"[bold magenta]Source:[/bold magenta] {source}")
            
            # Add score if available
            if search_type == 'keyword' and 'relevance_score' in doc:
                score = f"{doc['relevance_score']:.1f}"
                content_lines.append(f"\n[bold green]Relevance Score:[/bold green] {score}")
            elif search_type == 'similarity':
                # Show detailed similarity scores if available
                if 'question_similarity' in doc and 'answer_similarity' in doc:
                    content_lines.append(f"\n[bold green]Similarity Scores:[/bold green]")
                    content_lines.append(f"  Overall: {doc.get('overall_similarity', 0):.3f}")
                    content_lines.append(f"  Question: {doc.get('question_similarity', 0):.3f}")
                    content_lines.append(f"  Answer: {doc.get('answer_similarity', 0):.3f}")
                elif 'similarity_score' in doc:
                    score = f"{doc['similarity_score']:.3f}"
                    content_lines.append(f"\n[bold green]Similarity Score:[/bold green] {score}")
            
            content = "\n".join(content_lines)
            panel = Panel(content, title=f"Result #{idx}", border_style="cyan")
            console.print(panel)
            console.print()  # Add spacing between results
        
        return
    
    # Otherwise use compact table format
    id_width = 20
    text_width = 50
    cat_width = 15
    source_width = 25
    
    table = Table(
        title=f"Search Results ({len(results)} found)",
        show_header=True,
        header_style="bold cyan",
        show_lines=True
    )
    
    # Add columns based on search type
    table.add_column("#", style="dim", width=3)
    table.add_column("ID", style="cyan", width=id_width, no_wrap=True)
    table.add_column("Question", style="green", width=text_width)
    table.add_column("Answer", style="white", width=text_width)
    table.add_column("Category", style="yellow", width=cat_width)
    table.add_column("Source", style="magenta", width=source_width)
    
    if search_type == 'keyword':
        table.add_column("Score", style="bold green", width=8)
    elif search_type == 'similarity':
        # Check if we have detailed similarity scores
        has_detailed = any('question_similarity' in doc for doc in results)
        if has_detailed:
            table.add_column("Overall", style="bold green", width=8)
            table.add_column("Q-Sim", style="bold cyan", width=8)
            table.add_column("A-Sim", style="bold yellow", width=8)
        else:
            table.add_column("Similarity", style="bold green", width=10)
    
    # Add rows
    for idx, doc in enumerate(results, 1):
        doc_id = str(doc.get('_id', 'N/A'))
        question = doc.get('question', 'N/A')
        answer = doc.get('answer', 'N/A')
        category = doc.get('category', 'N/A')
        source = doc.get('source_file', 'N/A')
        
        # Truncate for compact display
        if len(doc_id) > id_width:
            doc_id = doc_id[:id_width-3] + "..."
        if len(question) > text_width:
            question = question[:text_width-3] + "..."
        if len(answer) > text_width:
            answer = answer[:text_width-3] + "..."
        if len(category) > cat_width:
            category = category[:cat_width-3] + "..."
        if len(source) > source_width:
            source = source[:source_width-3] + "..."
        
        row = [str(idx), doc_id, question, answer, category, source]
        
        if search_type == 'keyword' and 'relevance_score' in doc:
            score = f"{doc['relevance_score']:.1f}"
            row.append(score)
        elif search_type == 'similarity':
            if 'question_similarity' in doc and 'answer_similarity' in doc:
                # Show detailed scores
                row.append(f"{doc.get('overall_similarity', 0):.3f}")
                row.append(f"{doc.get('question_similarity', 0):.3f}")
                row.append(f"{doc.get('answer_similarity', 0):.3f}")
            elif 'similarity_score' in doc:
                score = f"{doc['similarity_score']:.3f}"
                row.append(score)
        
        table.add_row(*row)
    
    console.print(table)
    
    # Show helpful tip
    if not show_full and results:
        console.print("\n[dim]💡 Tip: Use --full flag to see complete text[/dim]")


def display_stats(stats: Dict[str, Any]) -> None:
    """
    Display collection statistics.

    Args:
        stats: Statistics dictionary.
    """
    # Create statistics panel
    stats_text = []
    stats_text.append(f"[bold cyan]Total Documents:[/bold cyan] {stats.get('total_documents', 0)}")
    stats_text.append(f"[bold green]Unique Categories:[/bold green] {stats.get('unique_categories', 0)}")
    stats_text.append(f"[bold yellow]Unique Sources:[/bold yellow] {stats.get('unique_sources', 0)}")
    
    # Quality metrics
    empty_q = stats.get('empty_questions', 0)
    empty_a = stats.get('empty_answers', 0)
    
    # Handle both integer and string values (e.g., "Unknown" for large collections)
    has_quality_issues = False
    if isinstance(empty_q, int) and empty_q > 0:
        has_quality_issues = True
    if isinstance(empty_a, int) and empty_a > 0:
        has_quality_issues = True
    
    if has_quality_issues or empty_q == "Unknown" or empty_a == "Unknown":
        stats_text.append(f"\n[bold red]Quality Issues:[/bold red]")
        if isinstance(empty_q, int) and empty_q > 0:
            stats_text.append(f"  Empty Questions: {empty_q}")
        elif empty_q == "Unknown":
            stats_text.append(f"  Empty Questions: Unknown (large collection)")
        if isinstance(empty_a, int) and empty_a > 0:
            stats_text.append(f"  Empty Answers: {empty_a}")
        elif empty_a == "Unknown":
            stats_text.append(f"  Empty Answers: Unknown (large collection)")

    panel = Panel(
        "\n".join(stats_text),
        title="Collection Statistics",
        border_style="cyan",
    )
    console.print(panel)

    # Display categories if available
    categories = stats.get('categories', [])
    if categories:
        console.print("\n[bold]Categories:[/bold]")
        for cat in categories:
            console.print(f"  • {cat}")

    # Display sources if available
    sources = stats.get('sources', [])
    if sources and len(sources) <= 20:  # Only show if not too many
        console.print("\n[bold]Sources:[/bold]")
        for src in sources:
            console.print(f"  • {src}")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def display_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def display_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[bold yellow]⚠[/bold yellow] {message}")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[bold cyan]ℹ[/bold cyan] {message}")


def display_duplicate_group(
    group_id: int,
    documents: List[Dict[str, Any]],
    similarity_scores: Optional[List[float]] = None,
) -> None:
    """
    Display a group of duplicate documents.

    Args:
        group_id: Group identifier.
        documents: List of duplicate documents.
        similarity_scores: Optional similarity scores for each document.
    """
    console.print(f"\n[bold cyan]Group {group_id}:[/bold cyan]")
    
    columns = [
        ("#", "cyan"),
        ("ID", "yellow"),
        ("Question", "green"),
        ("Answer", "blue"),
        ("Source", "magenta"),
    ]
    
    if similarity_scores:
        columns.append(("Similarity", "red"))

    rows = []
    for idx, doc in enumerate(documents, 1):
        question = doc.get("question", "")[:50]
        answer = doc.get("answer", "")[:50]
        
        row = [
            idx,
            doc.get("_id", "N/A")[:12],
            question + ("..." if len(doc.get("question", "")) > 50 else ""),
            answer + ("..." if len(doc.get("answer", "")) > 50 else ""),
            doc.get("source_file", "N/A"),
        ]
        
        if similarity_scores and idx - 1 < len(similarity_scores):
            row.append(f"{similarity_scores[idx - 1]:.2%}")
        
        rows.append(row)

    table = create_table(f"Duplicate Group {group_id}", columns, rows, show_lines=True)
    console.print(table)


def display_progress(message: str) -> None:
    """Display a progress message."""
    console.print(f"[dim]{message}...[/dim]")
