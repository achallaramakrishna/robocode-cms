from pathlib import Path
from ingest.pdf_to_images import PDFToImages

chapter_dir = Path("workspace/chapters/ac9d5e08-b333-490f-80d0-164413a9ee04")
pdf_path = chapter_dir / "chapter.pdf"
pages_dir = chapter_dir / "pages"

if not pdf_path.exists():
    raise FileNotFoundError("chapter.pdf not found")

converter = PDFToImages(dpi=300)
pages = converter.convert(
    pdf_path=str(pdf_path),
    output_dir=str(pages_dir)
)

print(f"✅ Generated {len(pages)} pages for {chapter_dir.name}")
