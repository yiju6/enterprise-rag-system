from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Chunk:
    content: str
    source_file: str          # "2022 Q3 AAPL.pdf"
    doc_type: str             # "pdf"/"markdown"/"html"
    chunk_index: int
    tenant_id: str | None     # Week 7 placeholder
    access_level: str | None  # Week 7 placeholder
    metadata: dict = field(default_factory=dict) # metadata: page_number, section, company, quarter