import cv2
import pytesseract
import os
import re
import json


class StrictFigureDetector:

    def __init__(self):
        self.caption_pattern = re.compile(r'Fig\.?\s*\d+\.\d+', re.IGNORECASE)

    def detect(self, page_images, output_dir):

        print("\n==============================")
        print("TEXTBOOK MODE – CAPTION ANCHOR EXTRACTION")
        print("==============================\n")

        os.makedirs(output_dir, exist_ok=True)

        total_figures = 0
        metadata = []

        for page_path in page_images:

            print(f"\nProcessing {page_path}")

            image = cv2.imread(page_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            data = pytesseract.image_to_data(
                gray,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6"
            )

            n_boxes = len(data['text'])
            captions = []

            for i in range(n_boxes):
                text = data['text'][i].strip()

                if self.caption_pattern.search(text):
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]

                    captions.append((x, y, w, h, text))

            print(f"Captions detected: {len(captions)}")

            for cap in captions:

                x, y, w, h, text = cap

                # Expand crop upward to include image
                crop_top = max(0, y - 350)
                crop_bottom = min(image.shape[0], y + h + 20)

                crop = image[crop_top:crop_bottom, :]

                filename = f"page_{total_figures+1}.png"
                save_path = os.path.join(output_dir, filename)

                cv2.imwrite(save_path, crop)

                metadata.append({
                    "file": filename,
                    "caption": text,
                    "page": page_path
                })

                total_figures += 1

        metadata_path = os.path.join(output_dir, "image_metadata.json")

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4)

        return {
            "total_figures": total_figures
        }
