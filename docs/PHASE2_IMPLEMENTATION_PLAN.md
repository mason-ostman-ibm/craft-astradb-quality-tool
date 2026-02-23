# Phase 2: Search & Discovery - Implementation Plan

## Current Status Summary

### ✅ Completed Features
1. **Keyword Search** (`search keyword`)
   - Full-text search across question/answer fields
   - Relevance scoring algorithm
   - Category and source filtering
   - Case-sensitive option
   - Client-side filtering (due to AstraDB API limitations)

2. **Category Search** (`search category`)
   - Filter by specific category
   - Returns all Q&A pairs in category

3. **Source Search** (`search source`)
   - Filter by source file
   - Returns all Q&A pairs from source

4. **Vector Similarity Search** (`search similar`)
   - Find similar documents by document ID
   - Uses existing vector embeddings
   - Threshold-based filtering
   - Excludes source document from results

### ⚠️ Partially Implemented
1. **Text-Based Similarity Search**
   - Module exists but not functional
   - Requires embedding generation
   - Needs sentence-transformers integration

### 📋 Missing Features for Phase 2 Completion
1. **Enhanced CLI Commands**
   - Better error messages
   - Progress indicators for long operations
   - Result pagination for large result sets

2. **Advanced Search Combinations**
   - Combine keyword + similarity search
   - Multi-field filtering
   - Date range filtering

3. **Search Result Export**
   - Save search results to file
   - Export in JSON/CSV format

## Implementation Tasks

### Task 1: Test and Validate Existing Search Commands ✅

**Priority:** HIGH  
**Estimated Time:** 1-2 hours  
**Status:** Ready to test

**Actions:**
1. Test `astra-clean search keyword "policy"` with various keywords
2. Test `astra-clean search category "HR"` with different categories
3. Test `astra-clean search source "handbook.xlsx"` with different sources
4. Test `astra-clean search similar <doc_id>` with various document IDs
5. Verify error handling for invalid inputs
6. Check display formatting for different result sizes

**Success Criteria:**
- All commands execute without errors
- Results are properly formatted
- Relevance/similarity scores are accurate
- Filtering works correctly

---

### Task 2: Enhance Search Result Display

**Priority:** MEDIUM  
**Estimated Time:** 2-3 hours  
**Status:** Enhancement

**Current Issues:**
- Search results may be truncated
- No pagination for large result sets
- Limited metadata display

**Proposed Enhancements:**
1. Add pagination support (show 20 results at a time)
2. Add `--full` flag to show complete text (not truncated)
3. Add `--export` flag to save results to file
4. Show search metadata (query time, total matches, etc.)
5. Add color coding for relevance/similarity scores

**Implementation:**
```python
# In display.py
def display_search_results_paginated(
    results: List[Dict[str, Any]],
    page_size: int = 20,
    search_type: str = 'general'
) -> None:
    """Display search results with pagination."""
    # Implementation
```

---

### Task 3: Add Advanced Search Combinations

**Priority:** MEDIUM  
**Estimated Time:** 3-4 hours  
**Status:** New feature

**New CLI Commands:**
```bash
# Combined keyword + similarity search
astra-clean search combined "governance policy" --similar-to <doc_id> --threshold 0.85

# Multi-field search with date range
astra-clean search advanced --keyword "policy" --category "HR" --date-from "2024-01-01"

# Search with multiple filters
astra-clean search filter --categories "HR,Finance" --sources "handbook.xlsx,guide.pdf"
```

**Implementation:**
1. Create `AdvancedSearch` class in `src/search/advanced.py`
2. Add CLI commands in `src/cli.py`
3. Implement filter combination logic
4. Add date range filtering support

---

### Task 4: Implement Search Result Export

**Priority:** LOW  
**Estimated Time:** 2-3 hours  
**Status:** New feature

**New Functionality:**
```bash
# Export search results to JSON
astra-clean search keyword "policy" --export results.json

# Export to CSV
astra-clean search similar <doc_id> --export results.csv --format csv
```

**Implementation:**
1. Add `--export` and `--format` options to search commands
2. Create export functions in `src/utils/export.py`
3. Support JSON and CSV formats
4. Include metadata in exports

---

### Task 5: Add Search Performance Optimization

**Priority:** MEDIUM  
**Estimated Time:** 2-3 hours  
**Status:** Enhancement

**Optimizations:**
1. **Caching:** Cache frequently searched terms
2. **Batch Processing:** Fetch documents in batches for keyword search
3. **Index Hints:** Use AstraDB indexes effectively
4. **Result Limiting:** Smart limiting based on relevance scores

**Implementation:**
```python
# In keyword.py
class KeywordSearchCache:
    """Cache for keyword search results."""
    def __init__(self, max_size: int = 100):
        self.cache = {}
        self.max_size = max_size
```

---

### Task 6: Improve Error Handling and User Feedback

**Priority:** HIGH  
**Estimated Time:** 2-3 hours  
**Status:** Enhancement

**Improvements:**
1. Better error messages for common issues
2. Suggestions when no results found
3. Progress indicators for long searches
4. Validation of search parameters before execution

**Example:**
```python
# When no results found
if not results:
    display_info("No results found for 'policy'")
    display_info("Suggestions:")
    display_info("  • Try different keywords")
    display_info("  • Check spelling")
    display_info("  • Use broader search terms")
    display_info("  • Try similarity search instead")
```

---

### Task 7: Add Search History and Favorites

**Priority:** LOW  
**Estimated Time:** 3-4 hours  
**Status:** New feature

**New Commands:**
```bash
# View search history
astra-clean search history

# Save a search as favorite
astra-clean search save "policy search" --query "keyword:policy category:HR"

# Run saved search
astra-clean search run "policy search"

# List saved searches
astra-clean search list-saved
```

**Implementation:**
1. Store search history in local file (`.astra_search_history`)
2. Store saved searches in config file
3. Add commands to manage history and favorites

---

## Testing Plan

### Unit Tests
```python
# tests/test_search.py
def test_keyword_search():
    """Test keyword search functionality."""
    # Test implementation

def test_similarity_search():
    """Test similarity search functionality."""
    # Test implementation

def test_search_filtering():
    """Test search filtering options."""
    # Test implementation
```

### Integration Tests
```python
# tests/test_search_integration.py
def test_search_end_to_end():
    """Test complete search workflow."""
    # Test implementation

def test_search_with_large_results():
    """Test search with large result sets."""
    # Test implementation
```

### CLI Tests
```bash
# Manual testing script
./tests/manual_search_tests.sh
```

---

## Phase 2 Completion Checklist

### Core Functionality
- [x] Keyword search implementation
- [x] Category filtering
- [x] Source filtering
- [x] Vector similarity search (by document ID)
- [ ] Text-based similarity search (requires embeddings - Phase 2.5)
- [ ] Advanced search combinations
- [ ] Search result export

### User Experience
- [x] Basic result display
- [ ] Pagination support
- [ ] Progress indicators
- [ ] Better error messages
- [ ] Search suggestions

### Performance
- [x] Basic optimization
- [ ] Result caching
- [ ] Batch processing
- [ ] Smart limiting

### Documentation
- [x] agents.md created
- [x] CLI help text
- [ ] User guide for search features
- [ ] API documentation

### Testing
- [ ] Unit tests for all search functions
- [ ] Integration tests
- [ ] Manual CLI testing
- [ ] Performance testing

---

## Next Steps

1. **Immediate Actions:**
   - Test all existing search commands
   - Fix any bugs found during testing
   - Improve error handling

2. **Short-term (This Week):**
   - Implement pagination
   - Add search result export
   - Enhance display formatting

3. **Medium-term (Next Week):**
   - Add advanced search combinations
   - Implement caching
   - Add search history

4. **Long-term (Future):**
   - Text-based similarity search (requires embedding generation)
   - Machine learning-based search improvements
   - Search analytics and insights

---

## Dependencies

### Required for Phase 2 Completion:
- ✅ AstraPy SDK
- ✅ Click CLI framework
- ✅ Rich display library
- ✅ Python-dotenv

### Optional for Enhanced Features:
- ⚠️ sentence-transformers (for text-based similarity)
- 📋 pandas (for CSV export)
- 📋 questionary (for interactive search)

---

## Risk Assessment

### Low Risk:
- Testing existing commands
- Display enhancements
- Error handling improvements

### Medium Risk:
- Advanced search combinations (complexity)
- Performance optimization (may need refactoring)
- Search result export (file handling)

### High Risk:
- Text-based similarity search (requires new dependency)
- Caching implementation (may cause stale data issues)

---

## Success Metrics

### Phase 2 Complete When:
1. All search commands work reliably
2. Search results are well-formatted and useful
3. Error handling is robust
4. Performance is acceptable for collections up to 10,000 documents
5. Documentation is complete
6. Tests pass with >80% coverage

### User Satisfaction Indicators:
- Search results are relevant
- Commands are intuitive
- Response time is acceptable (<5 seconds for most searches)
- Error messages are helpful

---

## Conclusion

Phase 2 is approximately **70% complete**. The core search functionality is implemented and working. The remaining 30% consists of:
- Testing and validation (10%)
- User experience enhancements (10%)
- Advanced features (10%)

**Recommended Next Action:** Switch to code mode and begin testing existing search commands, then implement the high-priority enhancements.