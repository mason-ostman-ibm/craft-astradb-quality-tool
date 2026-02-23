# AstraDB Quality Check Tool - Implementation Plan

## Project Overview

A Python CLI tool for cleaning and refining an AstraDB vector database containing question-answer pairs. The tool will support similarity search, keyword search, duplicate detection/removal, Q&A correction, and comprehensive data management features.

## Technical Stack

- **Language**: Python 3.9+
- **CLI Framework**: Click (for command-line interface)
- **Database**: AstraDB (DataStax)
- **Vector Search**: AstraDB native vector search
- **Embeddings**: IBM Sentence Transformer 30M (pre-existing vectors)
- **Additional Libraries**:
  - `astrapy` - AstraDB Python SDK
  - `python-dotenv` - Environment variable management
  - `pandas` - Data export/import and manipulation
  - `rich` - Beautiful CLI output and tables
  - `questionary` - Interactive prompts
  - `sentence-transformers` - For generating embeddings if needed

## Database Schema

```
Collection Fields:
- _id: Document identifier
- question: Question text
- answer: Answer text
- source_file: Origin file name
- category: Content category
- document_date: Date of document
- upload_timestamp: When uploaded
- version: Version number
- sheet_name: Excel sheet name (if applicable)
- $vector: Vector embeddings (IBM sentence transformer 30M)
```

## Architecture

```
astradb-quality-check-tool/
├── src/
│   ├── __init__.py
│   ├── cli.py                 # Main CLI entry point
│   ├── config.py              # Configuration and env management
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py      # AstraDB connection handler
│   │   └── operations.py      # CRUD operations
│   ├── search/
│   │   ├── __init__.py
│   │   ├── similarity.py      # Vector similarity search
│   │   └── keyword.py         # Text-based keyword search
│   ├── cleanup/
│   │   ├── __init__.py
│   │   ├── duplicates.py      # Duplicate detection and removal
│   │   ├── merge.py           # Merge similar entries
│   │   └── quality.py         # Quality scoring and validation
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── update.py          # Update Q&A pairs
│   │   ├── delete.py          # Delete operations
│   │   └── batch.py           # Batch operations
│   ├── export_import/
│   │   ├── __init__.py
│   │   ├── exporter.py        # Export to JSON/CSV
│   │   └── importer.py        # Import with validation
│   ├── audit/
│   │   ├── __init__.py
│   │   └── logger.py          # Audit logging system
│   └── utils/
│       ├── __init__.py
│       ├── display.py         # Rich table formatting
│       └── validators.py      # Input validation
├── tests/
│   ├── __init__.py
│   ├── test_search.py
│   ├── test_duplicates.py
│   └── test_operations.py
├── docs/
│   ├── USER_GUIDE.md
│   └── API_REFERENCE.md
├── .env.example
├── requirements.txt
├── setup.py
└── README.md
```

## Core Features & CLI Commands

### 1. Search Operations

```bash
# Similarity search
astra-clean search similar "What is governance?" --threshold 0.85 --limit 10

# Keyword search
astra-clean search keyword "governance" --fields question,answer --limit 20

# Advanced search with filters
astra-clean search similar "policy question" --category "HR" --source "handbook.xlsx"
```

### 2. Duplicate Management

```bash
# Find duplicates (exact match)
astra-clean duplicates find --method exact

# Find duplicates (semantic similarity)
astra-clean duplicates find --method semantic --threshold 0.90

# Interactive duplicate review
astra-clean duplicates review --threshold 0.90

# Auto-remove exact duplicates (keep first)
astra-clean duplicates remove --method exact --keep first --preview
```

### 3. Q&A Correction

```bash
# Update a specific entry
astra-clean update --id <doc_id> --question "New question" --answer "New answer"

# Batch update from CSV
astra-clean update --from-file corrections.csv --preview

# Interactive correction mode
astra-clean correct --interactive
```

### 4. Quality Management

```bash
# Run quality check
astra-clean quality check --report

# Find entries with issues
astra-clean quality find --empty-answers --short-questions

# Fix quality issues interactively
astra-clean quality fix --interactive
```

### 5. Merge Operations

```bash
# Find similar questions with different answers
astra-clean merge find --threshold 0.92

# Interactive merge (choose best answer)
astra-clean merge review --threshold 0.92

# Auto-merge with strategy
astra-clean merge auto --strategy longest-answer --preview
```

### 6. Export/Import

```bash
# Export entire collection
astra-clean export --format json --output backup.json

# Export with filters
astra-clean export --format csv --category "HR" --output hr_data.csv

# Import with duplicate checking
astra-clean import --file data.json --check-duplicates --preview

# Import and merge
astra-clean import --file data.csv --merge-strategy update
```

### 7. Statistics & Reporting

```bash
# Collection statistics
astra-clean stats --detailed

# Duplicate report
astra-clean stats duplicates --threshold 0.90

# Quality report
astra-clean stats quality --export report.html
```

### 8. Audit & Undo

```bash
# View audit log
astra-clean audit log --last 50

# Undo last operation
astra-clean audit undo --last

# Undo specific operation
astra-clean audit undo --operation-id <id>
```

## Key Implementation Details

### 1. Configuration Management

```python
# .env file structure
ASTRA_DB_ENDPOINT=https://xxx.apps.astra.datastax.com
ASTRA_DB_TOKEN=AstraCS:xxx
ASTRA_DB_KEYSPACE=default_keyspace
ASTRA_DB_COLLECTION=qa_collection
SIMILARITY_THRESHOLD=0.85
AUDIT_LOG_PATH=./audit_logs
```

### 2. Duplicate Detection Strategy

**Exact Match:**
- Compare normalized question text (lowercase, stripped whitespace)
- Group by identical questions
- Show all answers for review

**Semantic Similarity:**
- Use AstraDB vector search with configurable threshold
- For each question, find similar questions (>threshold)
- Present clusters of similar questions for review
- Allow user to select which to keep or merge

### 3. Interactive Review Interface

```
Found 3 duplicate groups:

Group 1: "What is the policy?" (3 duplicates)
┌────┬─────────────────────────┬──────────────────────┬─────────────┬──────────┐
│ ID │ Question                │ Answer               │ Source      │ Date     │
├────┼─────────────────────────┼──────────────────────┼─────────────┼──────────┤
│ 1  │ What is the policy?     │ The policy is...     │ handbook.pdf│ 2024-01  │
│ 2  │ What is the policy?     │ Policy states...     │ guide.xlsx  │ 2024-02  │
│ 3  │ What's the policy?      │ According to...      │ manual.docx │ 2024-03  │
└────┴─────────────────────────┴──────────────────────┴─────────────┴──────────┘

Actions:
[1] Keep entry 1, delete others
[2] Keep entry 2, delete others
[3] Keep entry 3, delete others
[4] Merge all (choose best answer)
[5] Skip this group
[6] Delete all
```

### 4. Quality Scoring System

Quality checks:
- Empty or null fields (question/answer)
- Very short questions (<10 chars)
- Very short answers (<20 chars)
- Missing metadata (source_file, category)
- Duplicate questions with identical answers
- Questions without question marks (optional)
- Answers that are just URLs or references

Score: 0-100 based on weighted criteria

### 5. Audit Logging

```json
{
  "operation_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "operation_type": "delete",
  "user": "system",
  "affected_documents": [
    {
      "id": "doc_id",
      "before": {...},
      "after": null
    }
  ],
  "metadata": {
    "reason": "duplicate removal",
    "threshold": 0.90
  }
}
```

### 6. Preview Mode

All destructive operations support `--preview` flag:
- Shows what will be changed
- Displays before/after states
- Requires confirmation before execution
- Can save preview to file

## Additional Features to Consider

### Advanced Cleanup Ideas:

1. **Answer Consolidation**: Merge multiple answers for the same question into a comprehensive single answer

2. **Category Auto-Tagging**: Use embeddings to suggest categories for uncategorized entries

3. **Source Validation**: Check if source files still exist, flag orphaned entries

4. **Version Management**: Compare different versions of Q&A pairs, track changes over time

5. **Conflict Resolution**: When merging, use strategies like:
   - Keep most recent
   - Keep longest answer
   - Keep from preferred source
   - Manual selection

6. **Bulk Reprocessing**: Re-generate embeddings for entries (if model changes)

7. **Data Validation Rules**: Custom rules for your domain (e.g., all HR questions must have category="HR")

8. **Similarity Clustering**: Group all similar questions together for batch review

9. **Answer Quality Scoring**: Use LLM to score answer quality and completeness

10. **Cross-Reference Detection**: Find questions that reference other questions

## Development Phases

### Phase 1: Core Infrastructure (Week 1)
- Project setup and dependencies
- AstraDB connection and configuration
- Basic CLI structure with Click
- Environment management

### Phase 2: Search & Discovery (Week 1-2)
- Similarity search implementation
- Keyword search implementation
- Result display with Rich tables
- Filtering capabilities

### Phase 3: Duplicate Management (Week 2)
- Exact duplicate detection
- Semantic duplicate detection
- Interactive review interface
- Deletion operations with preview

### Phase 4: Data Operations (Week 2-3)
- Update operations
- Batch operations
- Merge functionality
- Quality scoring

### Phase 5: Import/Export (Week 3)
- JSON export/import
- CSV export/import
- Validation on import
- Backup functionality

### Phase 6: Audit & Safety (Week 3-4)
- Audit logging system
- Undo functionality
- Preview mode for all operations
- Operation history

### Phase 7: Polish & Documentation (Week 4)
- Comprehensive testing
- User documentation
- Error handling improvements
- Performance optimization

## Testing Strategy

1. **Unit Tests**: Test individual functions and modules
2. **Integration Tests**: Test AstraDB operations
3. **CLI Tests**: Test command-line interface
4. **Mock Data**: Create test collection with known duplicates
5. **Edge Cases**: Empty fields, special characters, large datasets

## Success Criteria

- ✅ Successfully connect to AstraDB
- ✅ Search by similarity with configurable threshold
- ✅ Search by keywords across fields
- ✅ Detect and remove exact duplicates
- ✅ Detect and review semantic duplicates
- ✅ Update Q&A pairs individually and in batch
- ✅ Export/import data with validation
- ✅ Audit log all changes
- ✅ Preview mode for destructive operations
- ✅ Quality scoring and reporting
- ✅ Comprehensive CLI with help documentation
- ✅ User-friendly interactive interfaces

## Next Steps

1. Review this plan and provide feedback
2. Confirm any additional features you'd like
3. Switch to 'code' mode to begin implementation
4. Start with Phase 1: Core Infrastructure

Would you like to proceed with this plan, or would you like to adjust any features or priorities?
