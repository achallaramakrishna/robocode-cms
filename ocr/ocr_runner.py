import json
from pathlib import Path
from ocr.openai_vision_ocr import OpenAIVisionOCR


def run_ocr_for_chapter(
    chapter_dir: Path,
    api_key: str,
    prompt_file: Path,
    force_reprocess: bool = False
):
    pages_dir = chapter_dir / "pages"
    ocr_dir = chapter_dir / "ocr_openai"

    ocr_dir.mkdir(exist_ok=True)

    ocr_engine = OpenAIVisionOCR(
        api_key=api_key,
        prompt_file=prompt_file
    )

    page_images = sorted(pages_dir.glob("page_*.png"))

    if not page_images:
        print(f"⚠️ No pages found in {pages_dir}")
        return

    for image in page_images:
        page_num = image.stem.split("_")[1]
        output_file = ocr_dir / f"page_{page_num}.json"

        if output_file.exists() and not force_reprocess:
            print(f"⏭️ Skipping page {page_num} (already processed)")
            continue

        print(f"🧠 OCR Processing: {image.name}")

        try:
            result = ocr_engine.ocr_page(image)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"❌ Failed OCR for {image.name}: {e}")

    print(f"✅ OCR completed for chapter: {chapter_dir.name}")
