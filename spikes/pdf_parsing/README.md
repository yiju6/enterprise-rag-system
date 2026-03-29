## Goal

Evaluate PDF parsing solutions for 10-Q documents and select a parser that meets the requirements for an enterprise RAG ingestion pipeline.

The evaluation focuses on:

* Structural correctness (especially tables)

* Signal-to-noise ratio (header/footer handling)

* Semantic labeling (section boundaries)

## Test Setup

We evaluate parsing quality across representative page types in a 10-Q document:

* Page 6: Balance sheet (dense table, multi-level headers)
* Page 9: Pure narrative text
* Page 17: Mixed layout (heading + paragraph + table)

Evaluation criteria:

1. Table extraction quality (structure, completeness)
2. Header/Footer handling (noise vs content)
3. Section heading classification (semantic correctness)


## Baseline: Unstructured (fast)

### Findings

* Table extraction
   * No table elements detected on balance sheet page
   * Fails to capture structured financial data

* Header/Footer handling → 
   * Misclassified as Title
   * Introduces repeated, non-informative content

* Heading classification
   * Section headings labeled as Title (not ideal but usable)

### Impact

* Table extraction failure is a blocking issue for financial documents
* Header/footer misclassification leads to:

   * Data pollution in embeddings
   * Degraded retrieval relevance

### Conclusion

Unstructured (fast) is insufficient for structured financial documents and cannot be used in the ingestion pipeline.


## Decision

### Selected: Docling

Docling adopts a structure-aware document understanding pipeline, including:

* Layout detection (document-level segmentation)
* Table structure modeling via Transformer-based models (e.g., TableFormer)


In contrast, Unstructured (hi_res):

* Uses detectron2 for region detection only
* Does not model table structure explicitly

### Key Difference

* Docling: Structure-aware (table = grid with semantics)
* Unstructured: Region detection (table = bounding box + heuristics)


### Rationale

Docling is better aligned with requirements for financial documents:

* Accurate table reconstruction (including multi-level headers)
* Consistent handling of mixed layouts
* Cleaner semantic signals for downstream chunking

## Risks

Parsing latency

* Docling introduces heavier models (layout + table structure)
* Expected to be slower than lightweight parsers

This is treated as a Week 9/10 infrastructure concern:

   * batching
   * parallelization
   * GPU acceleration

Not a blocker for correctness validation.


## Validation: Docling Results

Docling was evaluated on the same three pages.

### Table Extraction
* Balance sheet fully detected
* Row/column structure correctly reconstructed
* Multi-level headers preserved

Conclusion: Meets requirements for structured financial data ingestion.

### Header/Footer Handling 

* Header and footer content is included in output

Impact:

* Adds noise to embeddings and retrieval

Mitigation:

* Can be handled via post-processing:

   * position-based filtering (bbox / page margin)
   * frequency-based filtering (repeated text across pages)

Conclusion: Acceptable with downstream filtering.

### Heading Classification

* Section headings correctly labeled as section_header

Impact:
* Enables reliable section-based chunking
* Improves retrieval precision and context grouping

## Final Assessment

Docling satisfies all core correctness requirements for 10-Q ingestion:

* Accurate table extraction (critical path)
* Acceptable noise profile (manageable via post-processing)
* Reliable semantic labeling (improves downstream RAG quality)

It is the appropriate choice for the current pipeline.

## Next Steps

* Implement post-processing layer:

   * header/footer filtering
   * table normalization (DataFrame → schema mapping)

* Benchmark performance:

   * per-page latency
   * scalability under batch ingestion

* Integrate into RAG pipeline:

   * section-aware chunking
   * table-aware retrieval strategy