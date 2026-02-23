# AstraDB Quality Check Tool - Agent Architecture

## Overview

The AstraDB Quality Check Tool is a modular Python CLI application designed to manage, clean, and refine question-answer pairs stored in an AstraDB vector database. The system follows an agent-based architecture where each module acts as a specialized agent responsible for specific operations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface (cli.py)                   │
│                    Command Router & Orchestrator                 │
└────────────┬────────────────────────────────────────────────────┘
             │
             ├──────────────────────────────────────────────────────┐
             │                                                      │
    ┌────────▼────────┐                                   ┌────────▼────────┐
    │  Configuration  │                                   │   Display       │
    │     Agent       │                                   │    Agent        │
    │  (config.py)    │                                   │ (display.py)    │
    └────────┬────────┘                                   └─────────────────┘
             │
    ┌────────▼────────────────────────────────────────────────────┐
    │              Database Connection Agent                       │
    │                  (db/connection.py)                          │
    │         Manages AstraDB connections & lifecycle              │
    └────────┬────────────────────────────────────────────────────┘
             │
             ├─────────────────┬─────────────────┬─────────────────┐
             │                 │                 │                 │
    ┌────────▼────────┐ ┌─────▼──────┐ ┌───────▼────────┐ ┌──────▼──────┐
    │   Operations    │ │   Search   │ │    Cleanup     │ │   Export/   │
    │     Agent       │ │   Agents   │ │    Agents      │ │   Import    │
    │ (operations.py) │ │            │ │                │ │   Agents    │
    └─────────────────┘ └────────────┘ └────────────────┘ └─────────────┘
```

## Agent Descriptions

### 1. CLI Agent (`src/cli.py`)

**Role:** Command Router & User Interface Orchestrator

**Responsibilities:**
- Parse and route CLI commands
- Coordinate between different agents
- Handle user input validation
- Manage command-line options and arguments
- Provide help documentation
- Handle errors and user feedback

**Key Commands:**
- `test-connection` - Verify AstraDB connectivity
- `stats` - Display collection statistics
- `show <doc_id>` - Show document details
- `update <doc_id>` - Update document fields
- `delete <doc_id>` - Delete a document
- `search keyword` - Keyword-based search
- `search similar` - Vector similarity search
- `search category` - Category-based filtering
- `search source` - Source file filtering

**Status:** ✅ Core functionality complete, Phase 2 in progress

---

### 2. Configuration Agent (`src/config.py`)

**Role:** Environment & Settings Manager

**Responsibilities:**
- Load and validate environment variables
- Manage application settings
- Provide configuration access to other agents
- Validate required credentials
- Handle default values

**Configuration Domains:**
- **AstraDB Settings:** Endpoint, token, keyspace, collection
- **Search Settings:** Similarity thresholds, result limits
- **Audit Settings:** Log paths, enable/disable flags
- **Quality Settings:** Minimum lengths, quality thresholds

**Status:** ✅ Complete

---

### 3. Database Connection Agent (`src/db/connection.py`)

**Role:** AstraDB Connection Lifecycle Manager

**Responsibilities:**
- Establish and maintain AstraDB connections
- Provide connection context management
- Handle connection errors and retries
- Expose collection interface to other agents
- Manage connection pooling and cleanup

**Key Features:**
- Context manager support (`with` statement)
- Automatic connection cleanup
- Collection metadata retrieval
- Error handling and logging

**Status:** ✅ Complete with large collection handling

---

### 4. Database Operations Agent (`src/db/operations.py`)

**Role:** CRUD Operations Executor

**Responsibilities:**
- Execute Create, Read, Update, Delete operations
- Batch operations on multiple documents
- Collection statistics gathering
- Document counting with large collection support
- Metadata extraction (categories, sources)

**Key Methods:**
- `get_document_by_id()` - Retrieve single document
- `get_documents()` - Retrieve multiple with filtering
- `update_document()` - Update single document
- `update_many()` - Batch updates
- `delete_document()` - Delete single document
- `delete_many()` - Batch deletions
- `insert_document()` - Create new document
- `get_collection_stats()` - Statistics aggregation

**Status:** ✅ Complete

---

### 5. Search Agents (`src/search/`)

#### 5.1 Keyword Search Agent (`src/search/keyword.py`)

**Role:** Text-Based Search Executor

**Responsibilities:**
- Perform keyword searches across text fields
- Client-side filtering (AstraDB Data API limitation)
- Relevance scoring based on:
  - Keyword occurrence frequency
  - Field weights (question > answer)
  - Position in text
  - Exact word matches
- Category and source filtering

**Key Methods:**
- `search()` - Main keyword search with relevance scoring
- `search_by_category()` - Category-based retrieval
- `search_by_source()` - Source file-based retrieval
- `advanced_search()` - Custom MongoDB-style queries

**Limitations:**
- No native regex support in AstraDB Data API
- Fetches documents client-side for filtering
- Limited to 1000 documents per fetch

**Status:** ✅ Complete and tested

#### 5.2 Similarity Search Agent (`src/search/similarity.py`)

**Role:** Vector-Based Semantic Search Executor

**Responsibilities:**
- Perform vector similarity searches
- Find semantically similar Q&A pairs
- Detect potential duplicates based on similarity
- Compare specific documents
- Support threshold-based filtering

**Key Methods:**
- `search_by_vector()` - Search using pre-computed embeddings
- `find_similar_to_document()` - Find similar items to a specific doc
- `find_potential_duplicates()` - Scan for high-similarity pairs
- `compare_questions()` - Direct comparison of two documents
- `search_by_text()` - ⚠️ Not implemented (requires embedding generation)

**Current Limitations:**
- Text-based search requires sentence-transformers integration
- Works with existing vectors only
- No embedding generation capability yet

**Status:** ✅ Vector search complete, ⚠️ Text embedding pending

---

### 6. Display Agent (`src/utils/display.py`)

**Role:** User Interface Formatter

**Responsibilities:**
- Format data for terminal display using Rich library
- Create tables, panels, and formatted output
- Display search results with proper styling
- Show document details
- Present statistics and metrics
- Provide success/error/warning messages

**Key Functions:**
- `display_documents()` - Tabular document display
- `display_document_detail()` - Single document panel
- `display_search_results()` - Search results table
- `display_stats()` - Statistics panel
- `display_duplicate_group()` - Duplicate clusters
- `display_success/error/warning/info()` - Status messages

**Status:** ✅ Complete

---

### 7. Validation Agent (`src/utils/validators.py`)

**Role:** Input Validation & Sanitization

**Responsibilities:**
- Validate user inputs
- Sanitize file names
- Check threshold ranges
- Validate document IDs
- Verify export formats
- Validate merge strategies

**Key Functions:**
- `validate_similarity_threshold()` - 0.0-1.0 range check
- `validate_file_path()` - Path validation
- `validate_document_id()` - ID format check
- `validate_export_format()` - Format type check
- `sanitize_filename()` - Remove invalid characters

**Status:** ✅ Complete

---

## Future Agents (Not Yet Implemented)

### 8. Cleanup Agents (`src/cleanup/`)

**Planned Modules:**

#### 8.1 Duplicate Detection Agent (`duplicates.py`)
- Detect exact duplicates (text matching)
- Detect semantic duplicates (vector similarity)
- Group duplicate clusters
- Interactive duplicate review
- Duplicate removal strategies

#### 8.2 Merge Agent (`merge.py`)
- Merge similar questions with different answers
- Answer consolidation strategies:
  - Keep longest answer
  - Keep most recent
  - Keep from preferred source
  - Manual selection
- Conflict resolution

#### 8.3 Quality Scoring Agent (`quality.py`)
- Score Q&A pair quality (0-100)
- Detect quality issues:
  - Empty/null fields
  - Very short questions/answers
  - Missing metadata
  - Malformed content
- Generate quality reports
- Suggest improvements

**Status:** 📋 Planned for Phase 3

---

### 9. Export/Import Agents (`src/export_import/`)

**Planned Modules:**

#### 9.1 Export Agent (`exporter.py`)
- Export to JSON format
- Export to CSV format
- Filtered exports (category, source, date range)
- Backup entire collection
- Include/exclude vector data

#### 9.2 Import Agent (`importer.py`)
- Import from JSON
- Import from CSV
- Validation on import
- Duplicate checking during import
- Merge strategies for conflicts
- Preview mode before import

**Status:** 📋 Planned for Phase 5

---

### 10. Audit Agent (`src/audit/`)

**Planned Module:** `logger.py`

**Responsibilities:**
- Log all data modifications
- Track operation history
- Enable undo functionality
- Generate audit reports
- Compliance tracking

**Audit Log Structure:**
```json
{
  "operation_id": "uuid",
  "timestamp": "ISO-8601",
  "operation_type": "update|delete|merge",
  "user": "system",
  "affected_documents": [
    {
      "id": "doc_id",
      "before": {...},
      "after": {...}
    }
  ],
  "metadata": {
    "reason": "duplicate removal",
    "threshold": 0.90
  }
}
```

**Status:** 📋 Planned for Phase 6

---

### 11. Batch Operations Agent (`src/operations/`)

**Planned Modules:**
- `batch.py` - Batch update/delete operations
- `update.py` - Advanced update strategies
- `delete.py` - Safe deletion with preview

**Status:** 📋 Planned for Phase 4

---

## Data Flow Diagrams

### Search Operation Flow

```
User Command
    │
    ├─→ CLI Agent (parse command)
    │       │
    │       ├─→ Configuration Agent (get settings)
    │       │
    │       ├─→ Connection Agent (establish connection)
    │       │       │
    │       │       └─→ AstraDB
    │       │
    │       ├─→ Search Agent (execute search)
    │       │       │
    │       │       ├─→ Keyword Search (text-based)
    │       │       │   └─→ Relevance Scoring
    │       │       │
    │       │       └─→ Similarity Search (vector-based)
    │       │           └─→ Threshold Filtering
    │       │
    │       └─→ Display Agent (format results)
    │               │
    │               └─→ Rich Tables/Panels
    │
    └─→ User Output
```

### Update Operation Flow

```
User Command
    │
    ├─→ CLI Agent (parse & validate)
    │       │
    │       ├─→ Validation Agent (check inputs)
    │       │
    │       ├─→ Connection Agent (connect)
    │       │
    │       ├─→ Operations Agent (execute update)
    │       │       │
    │       │       └─→ AstraDB (update document)
    │       │
    │       ├─→ [Future] Audit Agent (log change)
    │       │
    │       └─→ Display Agent (show success)
    │
    └─→ User Confirmation
```

## Agent Communication Patterns

### 1. Direct Invocation
Most agents are invoked directly by the CLI agent:
```python
with AstraDBConnection() as conn:
    ops = DatabaseOperations(conn)
    result = ops.get_document_by_id(doc_id)
```

### 2. Dependency Injection
Agents receive dependencies through constructors:
```python
class KeywordSearch:
    def __init__(self, connection: AstraDBConnection):
        self.connection = connection
```

### 3. Context Management
Connection agent uses context manager pattern:
```python
with AstraDBConnection() as conn:
    # Connection automatically managed
    pass
```

### 4. Configuration Access
Global configuration instance:
```python
from .config import config
threshold = config.similarity_threshold
```

## Technology Stack

### Core Technologies
- **Python 3.9+** - Primary language
- **Click** - CLI framework
- **AstraPy** - AstraDB Python SDK
- **Rich** - Terminal formatting
- **python-dotenv** - Environment management

### Database
- **AstraDB** - Vector database (DataStax)
- **Vector Search** - Native AstraDB vector similarity
- **IBM Sentence Transformer 30M** - Pre-existing embeddings

### Future Integrations
- **sentence-transformers** - Embedding generation
- **pandas** - Data manipulation for export/import
- **questionary** - Interactive prompts

## Development Phases

### ✅ Phase 1: Core Infrastructure (Complete)
- Project setup
- AstraDB connection
- Basic CLI structure
- Configuration management
- CRUD operations

### 🔄 Phase 2: Search & Discovery (In Progress)
- ✅ Keyword search
- ✅ Category/source filtering
- ✅ Vector similarity search (by document ID)
- ⚠️ Text-based similarity search (pending embeddings)
- ✅ Result display formatting

### 📋 Phase 3: Duplicate Management (Planned)
- Exact duplicate detection
- Semantic duplicate detection
- Interactive review interface
- Deletion operations with preview

### 📋 Phase 4: Data Operations (Planned)
- Batch updates
- Merge functionality
- Quality scoring
- Advanced filtering

### 📋 Phase 5: Import/Export (Planned)
- JSON export/import
- CSV export/import
- Validation
- Backup functionality

### 📋 Phase 6: Audit & Safety (Planned)
- Audit logging system
- Undo functionality
- Preview mode for all operations
- Operation history

## Current Implementation Status

### Working Features ✅
1. **Connection Management**
   - Connect to AstraDB
   - Handle large collections (>1000 docs)
   - Connection lifecycle management

2. **Basic Operations**
   - Show document details
   - Update documents
   - Delete documents
   - Collection statistics

3. **Keyword Search**
   - Search across question/answer fields
   - Relevance scoring
   - Category/source filtering
   - Case-sensitive option

4. **Vector Search**
   - Find similar documents by ID
   - Threshold-based filtering
   - Similarity scoring

5. **Display**
   - Rich formatted tables
   - Document detail panels
   - Statistics display
   - Search results formatting

### In Development 🔄
1. **Text-Based Similarity Search**
   - Requires embedding generation
   - Needs sentence-transformers integration

### Planned Features 📋
1. **Duplicate Management**
2. **Quality Scoring**
3. **Batch Operations**
4. **Export/Import**
5. **Audit Logging**
6. **Merge Operations**

## Agent Extension Guidelines

### Adding a New Agent

1. **Create Module File**
   ```python
   # src/new_module/agent.py
   import logging
   from ..db.connection import AstraDBConnection
   
   logger = logging.getLogger(__name__)
   
   class NewAgent:
       def __init__(self, connection: AstraDBConnection):
           self.connection = connection
   ```

2. **Add CLI Commands**
   ```python
   # src/cli.py
   @cli.group()
   def new_command():
       """New command group."""
       pass
   
   @new_command.command('action')
   def new_action():
       """Execute new action."""
       with AstraDBConnection() as conn:
           agent = NewAgent(conn)
           result = agent.execute()
   ```

3. **Add Display Functions**
   ```python
   # src/utils/display.py
   def display_new_results(results):
       """Display new agent results."""
       # Format and display
   ```

4. **Add Validation**
   ```python
   # src/utils/validators.py
   def validate_new_input(value):
       """Validate new agent input."""
       # Validation logic
   ```

5. **Update Documentation**
   - Add to this agents.md file
   - Update README.md
   - Add to IMPLEMENTATION_PLAN.md

## Error Handling Strategy

### Agent-Level Error Handling
Each agent handles its own errors:
```python
try:
    result = agent.execute()
except SpecificError as e:
    logger.error(f"Agent failed: {e}")
    raise
```

### CLI-Level Error Handling
CLI catches and displays user-friendly errors:
```python
try:
    result = execute_command()
except Exception as e:
    display_error(f"Operation failed: {e}")
    sys.exit(1)
```

### Logging Strategy
- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Operation failures
- **DEBUG**: Detailed troubleshooting

## Performance Considerations

### Large Collection Handling
- Document counting limited to 1000 (AstraDB restriction)
- Pagination for large result sets
- Client-side filtering for keyword search
- Batch operations for efficiency

### Vector Search Optimization
- Use existing embeddings (no generation overhead)
- Threshold filtering to reduce results
- Limit parameter to control result size
- Exclude source document from similarity results

### Memory Management
- Stream large result sets
- Use cursors for iteration
- Limit fetch sizes
- Clean up connections properly

## Security Considerations

### Credential Management
- Environment variables for sensitive data
- No credentials in code
- Token validation on startup
- Secure connection handling

### Data Validation
- Input sanitization
- Document ID validation
- File path validation
- Threshold range checking

### Audit Trail
- Log all modifications (future)
- Track user actions (future)
- Enable undo operations (future)

## Testing Strategy

### Unit Tests
- Test individual agent methods
- Mock AstraDB connections
- Validate input/output

### Integration Tests
- Test agent interactions
- Test with real AstraDB (test collection)
- Validate end-to-end flows

### CLI Tests
- Test command parsing
- Test error handling
- Test user interactions

## Conclusion

The AstraDB Quality Check Tool follows a modular, agent-based architecture where each component has clear responsibilities and well-defined interfaces. This design enables:

- **Maintainability**: Easy to update individual agents
- **Extensibility**: Simple to add new agents
- **Testability**: Agents can be tested independently
- **Scalability**: Agents can be optimized individually
- **Clarity**: Clear separation of concerns

As development progresses through the planned phases, new agents will be added following the established patterns and guidelines documented here.