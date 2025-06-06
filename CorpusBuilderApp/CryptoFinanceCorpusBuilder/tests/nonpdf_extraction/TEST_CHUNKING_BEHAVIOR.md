# Non-PDF Chunking Behavior Test Plan

## Overview
This document outlines the test plan for verifying chunking behavior with large files in the non-PDF extractor pipeline.

## Test Cases

### 1. Large Python Files
- **Test File**: Large ML model implementation (>10k lines)
- **Expected Behavior**:
  - Chunk at logical boundaries (class/method definitions)
  - Preserve code structure and imports
  - Maintain context between chunks
- **Validation**:
  - Check for broken syntax
  - Verify import statements are preserved
  - Ensure class/method definitions are complete

### 2. Large Jupyter Notebooks
- **Test File**: Research notebook with multiple cells and outputs
- **Expected Behavior**:
  - Chunk at cell boundaries
  - Preserve markdown and code cell separation
  - Maintain cell execution order
- **Validation**:
  - Verify cell types are preserved
  - Check output consistency
  - Ensure markdown formatting is intact

### 3. Large JSON Files
- **Test File**: Large dataset or API response
- **Expected Behavior**:
  - Chunk at object boundaries
  - Preserve JSON structure
  - Maintain data relationships
- **Validation**:
  - Verify JSON syntax
  - Check object completeness
  - Ensure data integrity

### 4. Large CSV Files
- **Test File**: Large financial dataset
- **Expected Behavior**:
  - Chunk at row boundaries
  - Preserve header information
  - Maintain column relationships
- **Validation**:
  - Verify header presence
  - Check data type consistency
  - Ensure no data loss

## Quality Metrics

### 1. Context Preservation
- **Overlap Score**: Measure semantic overlap between chunks
- **Context Continuity**: Verify no context loss between chunks
- **Reference Integrity**: Check cross-references are maintained

### 2. Structure Integrity
- **Syntax Validation**: Verify code/formatting is preserved
- **Structure Completeness**: Check for broken structures
- **Relationship Preservation**: Validate data relationships

### 3. Performance Metrics
- **Chunking Time**: Measure processing time per file
- **Memory Usage**: Monitor memory consumption
- **Chunk Distribution**: Track chunk size statistics

## Test Implementation

```python
def test_chunking_behavior():
    # Test large Python file
    test_python_file = "path/to/large_model.py"
    chunks = extract_text_from_file(test_python_file)
    assert_chunk_quality(chunks)
    
    # Test large Jupyter notebook
    test_notebook = "path/to/large_research.ipynb"
    chunks = extract_text_from_file(test_notebook)
    assert_notebook_chunk_quality(chunks)
    
    # Test large JSON file
    test_json = "path/to/large_dataset.json"
    chunks = extract_text_from_file(test_json)
    assert_json_chunk_quality(chunks)
    
    # Test large CSV file
    test_csv = "path/to/large_financial_data.csv"
    chunks = extract_text_from_file(test_csv)
    assert_csv_chunk_quality(chunks)

def assert_chunk_quality(chunks):
    # Verify chunk size
    for chunk in chunks:
        assert len(chunk.split()) <= CHUNK_TOKEN_THRESHOLD
        
    # Verify context preservation
    for i in range(len(chunks)-1):
        assert has_context_overlap(chunks[i], chunks[i+1])
        
    # Verify structure integrity
    for chunk in chunks:
        assert is_valid_structure(chunk)
```

## Success Criteria

1. **Semantic Coherence**
   - All chunks maintain semantic meaning
   - No information loss between chunks
   - Context is preserved

2. **Structural Integrity**
   - Code/formatting is preserved
   - No broken syntax
   - Data relationships maintained

3. **Performance**
   - Chunking time < 5 seconds per MB
   - Memory usage < 1GB for 100MB file
   - Stable chunk size distribution

4. **Quality**
   - No data corruption
   - No format loss
   - No context breaks

## Documentation Requirements

1. **Chunking Behavior**
   - Document behavior for each file type
   - Note any limitations
   - Record edge cases

2. **Performance Metrics**
   - Record processing times
   - Document memory usage
   - Track chunk statistics

3. **Quality Control**
   - Update quality guidelines
   - Document validation rules
   - Note any exceptions

## Next Steps

1. Create test files for each category
2. Implement test cases
3. Run performance benchmarks
4. Document results
5. Update quality control guidelines 