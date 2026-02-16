import re
import json
import cv2
import numpy as np
import pytesseract
from pathlib import Path
from pdf2image import convert_from_path


# ---------------------------------------------
# CONFIG
# ---------------------------------------------
FIG_REGEX = r"Fig\.?\s*\d+\.\d+"   # Fig. 1.2 OR Fig 1.2


# ---------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------
def extract_figures_from_pdf(pdf_path: str, chapter_dir: str):

    chapter_dir = Path(chapter_dir)
    figures_dir = chapter_dir / "assets" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "figures": []
    }

    # Convert PDF pages to images (high DPI improves OCR)
    pages = convert_from_path(pdf_path, dpi=350, thread_count=2)

    figure_count = 0

    for page_index, page in enumerate(pages):

        page_number = page_index + 1

        # Convert PIL to OpenCV
        open_cv_image = np.array(page)
        image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # OCR data
        data = pytesseract.image_to_data(
            gray,
            output_type=pytesseract.Output.DICT,
            config="--oem 3 --psm 4"
        )

        n_boxes = len(data["text"])

        for i in range(n_boxes):

            word = data["text"][i].strip()

            if not word:
                continue

            if re.search(FIG_REGEX, word):

                # Extract full caption line
                caption_words = []
                y = data["top"][i]

                for j in range(i, min(i + 15, n_boxes)):
                    if abs(data["top"][j] - y) < 20:
                        caption_words.append(data["text"][j])
                    else:
                        break

                caption_text = " ".join(caption_words).strip()

                # Extract figure number
                match = re.search(r"\d+\.\d+", caption_text)
                if not match:
                    continue

                fig_number = match.group()
                fig_filename = f"fig_{fig_number.replace('.', '_')}.png"

                # Crop region ABOVE caption
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]

                crop_top = max(0, y - 500)
                crop_bottom = y + h + 20
                crop_left = 0
                crop_right = image.shape[1]

                crop = image[crop_top:crop_bottom, crop_left:crop_right]

                # Add white padding
                crop = cv2.copyMakeBorder(
                    crop,
                    20, 20, 20, 20,
                    cv2.BORDER_CONSTANT,
                    value=[255, 255, 255]
                )

                save_path = figures_dir / fig_filename
                cv2.imwrite(str(save_path), crop)

                metadata["figures"].append({
                    "figure_number": fig_number,
                    "page_number": page_number,
                    "image_file": fig_filename,
                    "caption": caption_text,
                    "chapter_uuid": chapter_dir.name,
                    "asset_type": None,
                    "linked_asset_id": None
                })

                figure_count += 1

    # Remove duplicates
    unique = {}
    for fig in metadata["figures"]:
        unique[fig["figure_number"]] = fig

    metadata["figures"] = list(unique.values())

    # Save metadata
    metadata_path = figures_dir / "image_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata saved: {metadata_path}")

    return metadata
