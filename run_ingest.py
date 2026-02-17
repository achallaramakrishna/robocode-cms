import json
import argparse
from pathlib import Path
import traceback
import uuid
import hashlib

from ingest.pdf_to_images import PDFToImages


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
    mode = ctx.get("figure_detection_mode", "textbook")

    if not course_id:
        raise ValueError("❌ 'course_id' missing in JSON.")

    if not input_pdf_path:
        raise ValueError("❌ 'input_pdf_path' missing in JSON.")

    pdf_folder = Path(input_pdf_path)

    if not pdf_folder.exists():
        raise FileNotFoundError(f"❌ PDF folder not found: {pdf_folder}")

    print("\n===========================================")
    print("🚀 STARTING INGEST PROCESS")
    print(f"📚 Course ID: {course_id}")
    print(f"📘 Mode: {mode}")
    print("===========================================\n")

    pdf_files = list(pdf_folder.glob("*.pdf"))

    if not pdf_files:
        print("⚠ No PDF files found.")
        return

    pdf_to_images = PDFToImages()

    for pdf in pdf_files:

        try:
            print(f"\n📄 Processing: {pdf.name}")

            # -------------------------------------
            # Generate stable chapter UUID from PDF name
            # -------------------------------------
            chapter_name = pdf.stem

            chapter_uuid = str(uuid.UUID(
                hashlib.md5(chapter_name.encode()).hexdigest()
            ))

            print(f"📘 Chapter UUID: {chapter_uuid}")

            # -------------------------------------
            # Prepare workspace
            # -------------------------------------
            chapter_dir = Path(f"workspace/courses/{course_id}/{chapter_uuid}")
            pages_dir = chapter_dir / "pages"
            figures_dir = chapter_dir / "assets/figures"

            pages_dir.mkdir(parents=True, exist_ok=True)
            figures_dir.mkdir(parents=True, exist_ok=True)

            # -------------------------------------
            # Convert PDF → Images
            # -------------------------------------
            print("🖼 Rendering PDF to images...\n")

            page_images = pdf_to_images.convert(
                str(pdf),
                str(pages_dir)
            )

            if not page_images:
                print("⚠ No images generated.")
                continue

            # -------------------------------------
            # Strict Rectangular Figure Detection
            # -------------------------------------
            if mode == "textbook":

                print("🔎 Running RECTANGULAR figure detection...\n")

                from ingest.strict_page_rectangle_detector import StrictPageRectangleDetector

                detector = StrictPageRectangleDetector(debug=False)

                all_results = []
                page_number = 1

                for page_path in page_images:
                    results = detector.detect_page(
                        page_path=page_path,
                        output_dir=str(figures_dir),
                        page_number=page_number
                    )
                    all_results.extend(results)
                    page_number += 1

                total_figures = len(all_results)

                print("\n----------------------------------")
                print(f"TOTAL EXTRACTED FIGURES: {total_figures}")
                print("----------------------------------\n")

                print(f"✅ Extracted {total_figures} figures.")

            else:
                print(f"⚠ Unsupported mode: {mode}")

        except Exception as e:

            print(f"\n❌ ERROR processing: {pdf.name}")
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
