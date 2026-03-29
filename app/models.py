from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Block:
    content: str
    content_type: str        # "text"/"table"/"figure"
    metadata: dict = field(default_factory=dict) # {"section": "Part I > Item 2", "page_number": 3, ...}

@dataclass
class Document:
    source_file: str          # "2022 Q3 AAPL.pdf"
    doc_type: str             # "pdf"/"markdown"/"html"
    blocks: list[Block]
    metadata: dict = field(default_factory=dict) # {"company": "AAPL", "quarter": "Q3 2022", ...}

@dataclass
class Chunk:
    content: str
    content_type: str          # "text"/"table"
    source_file: str          # "2022 Q3 AAPL.pdf"
    doc_type: str             # "pdf"/"markdown"/"html"
    chunk_index: int
    tenant_id: str | None     # Week 7 placeholder
    access_level: str | None  # Week 7 placeholder
    metadata: dict = field(default_factory=dict) # metadata: page_number, section, company, quarter