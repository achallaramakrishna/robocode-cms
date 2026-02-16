import json
import argparse
from pathlib import Path

from ingest.pdf_loader import PDFLoader
from ingest.figure_extractor import extract_figures_from_pdf


def run_ingest_from_json(json_path: Path):

    if not json_path.exists():
        raise FileNotFoundError(f"JSON not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        ctx = json.load(f)

    if "course_id" not in ctx:
        raise ValueError("course_id missing. Run Phase A first.")

    if "input_pdf_path" not in ctx:
        raise ValueError("input_pdf_path missing in JSON.")

    course_id = ctx["course_id"]
    source_dir = Path(ctx["input_pdf_path"])

    if not source_dir.exists():
        raise FileNotFoundError(f"Source folder not found: {source_dir}")

    pdf_files = sorted(source_dir.glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError(f"No PDF files found in {source_dir}")

    base_upload_dir = Path(f"workspace/courses/{course_id}/chapters")
    base_upload_dir.mkdir(parents=True, exist_ok=True)

    pdf_loader = PDFLoader(base_upload_dir=str(base_upload_dir))

    print("\nPHASE C – STRICT FIGURE EXTRACTION\n")

    for pdf in pdf_files:

        print(f"Processing: {pdf.name}")

        # 1️⃣ Create chapter folder + UUID
        chapter_info = pdf_loader.load_chapter_pdf(
            source_pdf_path=str(pdf)
        )

        chapter_dir = Path(chapter_info["chapter_dir"])
        chapter_uuid = chapter_dir.name

        print(f"Chapter UUID: {chapter_uuid}")

        # 2️⃣ Extract figures
        metadata = extract_figures_from_pdf(
            pdf_path=str(pdf),
            chapter_dir=str(chapter_dir)
        )

        print(f"Extracted Figures: {len(metadata.get('figures', []))}\n")

    print("INGEST COMPLETED\n")


# CLI
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Robo Dynamics Figure Ingest Runner"
    )

    parser.add_argument(
        "json_file",
        help="Path to course JSON file"
    )

    args = parser.parse_args()

    run_ingest_from_json(Path(args.json_file))
