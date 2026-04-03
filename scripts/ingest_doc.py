from pathlib import Path
from app.ingestor import ingest

files = [
    Path("data/uploads/pdf/2023 Q3 AAPL.pdf"),
    Path("data/uploads/pdf/2023 Q3 NVDA.pdf"),
    Path("data/uploads/pdf/2023 Q3 MSFT.pdf"),
]

for file in files:
    print(f"Ingesting {file.name}...")
    ingest(file)
    print(f"Done: {file.name}")