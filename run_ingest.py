import json
import argparse
from pathlib import Path
import traceback
import uuid
import hashlib

from ingest.pdf_to_images import PDFToImages
from ingest.figure_extractor_v2 import extract_figures


# -------------------------------------------------
# Main Ingest Runner
# -------------------------------------------------
def run_ingest_from_json(json_path: Path, force=False):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    course_id = ctx.get("course_id")
    input_pdf_path = ctx.get("input_pdf_path")
    # "textbook"   → only save figures with a Fig. caption (default)
    # "no_caption" → save all qualifying embedded images (e.g. NEET books)
    mode = ctx.get("figure_detection_mode", "textbook")

    if not course_id:
        raise ValueError("❌ 'course_id' missing in JSON.")

    if not input_pdf_path:
        raise ValueError("❌ 'input_pdf_path' missing in JSON.")

    pdf_folder = Path(input_pdf_path)

    if not pdf_folder.exists():
        raise FileNotFoundError(f"❌ PDF folder not found: {pdf_folder}")

    print("\n===========================================")
    print("STARTING INGEST PROCESS")
    print(f"Course ID: {course_id}")
    print(f"Figure mode: {mode}")
    print("===========================================\n")

    pdf_files = sorted(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found.")
        return

    pdf_to_images = PDFToImages()

    for pdf_idx, pdf in enumerate(pdf_files, start=1):

        try:
            print(f"\n[{pdf_idx}/{len(pdf_files)}] Processing: {pdf.name}")

            # -------------------------------------
            # Generate stable chapter UUID from PDF name
            # -------------------------------------
            chapter_name = pdf.stem

            chapter_uuid = str(uuid.UUID(
                hashlib.md5(chapter_name.encode()).hexdigest()
            ))

            print(f"  Chapter UUID: {chapter_uuid}")

            # -------------------------------------
            # Prepare workspace
            # -------------------------------------
            chapter_dir = Path(f"workspace/courses/{course_id}/chapters/{chapter_uuid}")
            pages_dir = chapter_dir / "pages"
            figures_dir = chapter_dir / "assets/figures"

            pages_dir.mkdir(parents=True, exist_ok=True)
            figures_dir.mkdir(parents=True, exist_ok=True)

            # -------------------------------------
            # Convert PDF → Page images (for OCR later)
            # Skip if pages already exist and --force not set
            # -------------------------------------
            existing_pages = list(pages_dir.glob("page_*.png"))
            if existing_pages and not force:
                print(f"  Pages already rendered ({len(existing_pages)} pages), skipping render step.")
                page_images = sorted(str(p) for p in existing_pages)
            else:
                print("  Rendering PDF to page images...")
                page_images = pdf_to_images.convert(str(pdf), str(pages_dir))

            if not page_images:
                print("  No images generated.")
                continue

            # -------------------------------------
            # Figure extraction (PyMuPDF-based)
            # Works for both "textbook" (needs Fig caption)
            # and "no_caption" (NEET / all embedded images)
            # Skip if image_metadata.json already exists and --force not set
            # -------------------------------------
            meta_file = figures_dir / "image_metadata.json"
            if meta_file.exists() and not force:
                import json as _json
                with open(meta_file) as _f:
                    metadata = _json.load(_f)
                total_figures = len(metadata.get("figures", []))
                print(f"  Figures already extracted ({total_figures} figures), skipping.")
            else:
                print(f"  Extracting figures (mode={mode})...")
                metadata = extract_figures(
                    pdf_path=str(pdf),
                    output_dir=str(figures_dir),
                    mode=mode,
                    debug=False,
                )
                total_figures = len(metadata.get("figures", []))

            print(f"  Figures: {total_figures}  |  Done: {pdf.name}")

        except Exception as e:

            print(f"\nERROR processing: {pdf.name}")
            print(f"Reason: {str(e)}")
            traceback.print_exc()
            print("Continuing to next PDF...\n")


# -------------------------------------------------
# CLI Entry
# -------------------------------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Path to course JSON file")
    parser.add_argument("--force", action="store_true")

    args = parser.parse_args()

    run_ingest_from_json(
        Path(args.json_file),
        force=args.force
    )
