from pathlib import Path

from extractors.page_classifier import PageClassifier
from extractors.smart_router import SmartRouter


def run_extraction_for_chapter(chapter_dir: Path):

    ocr_dir = chapter_dir / "ocr_openai"

    if not ocr_dir.exists():
        print("⚠️ No OCR data found")
        return

    page_files = sorted(ocr_dir.glob("page_*.json"))

    if not page_files:
        print("⚠️ No pages found")
        return

    assets_dir = chapter_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    print(f"\n📘 Running Smart Extraction for {chapter_dir.name}")

    # STEP 1: Classify pages
    classifier = PageClassifier(page_files)
    classified_pages = classifier.classify()

    # STEP 2: Route to correct extractors
    router = SmartRouter(classified_pages, assets_dir)
    router.route()

    print(f"✅ Extraction completed for {chapter_dir.name}")
