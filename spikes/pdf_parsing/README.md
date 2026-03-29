## Goal

Evaluate PDF parsing tools for 10-Q documents to select the most suitable parser for the enterprise RAG ingestion pipeline.

## Test Setup

The spike will mainly test the below three aspects:

1.	Whether tables are extracted
2.	Whether header or footer is detected as text
3.	Whether section heading is labeled as Title

Pages to be tested:

- Page 6 contains balance sheet
- Page 9 contains pure text
- Page 17 is a combination of heading, paragraph, and table

## Results
- Table: The results does not have table elements.

- Header/Footer is detected as Title.

    This introduces data pollution, as repeated headers/footers are treated as meaningful content.

	It can degrade retrieval quality in RAG by surfacing irrelevant or duplicated context.

- Section heading is labeled as Title.

Therefore, unstructured (fast) does not satisfy the requirements.

## Decision
- Choose Docling

Docling uses a structure-aware pipeline for document understanding.
For table extraction, it leverages models such as TableFormer (Vision Transformer-based) to explicitly model row/column relationships and cell structure.


In contrast, unstructured (hi_res) relies on detectron2-based layout detection, which performs region detection (e.g., identifying table areas) but does not model table structure itself.

As a result:
- Docling → structure-aware (can reconstruct table schema)
- Unstructured hi_res → region detection (requires heuristic post-processing)

Docling is therefore better suited for financial documents with:
- multi-column layouts
- merged cells
- complex table structures

## Risks
Parsing speed:

Docling introduces heavier models (layout + table structure), which may increase processing latency compared to lightweight parsing approaches.

This is considered a Week 9/10 infrastructure problem (optimization, batching, GPU usage), not a blocker for initial correctness validation.

## Next Step
Run Docling on the same three pages (6, 9, 17).

Evaluate:

- Table structure reconstruction quality
- Handling of mixed layouts (heading + paragraph + table)
- Consistency of element classification
