import os
import re
import cv2
import pytesseract
from pathlib import Path


class StrictFigureDetector:

    FIG_PATTERN = re.compile(r'\bFig\.\s*\d+\.\d+\b', re.IGNORECASE)

    def __init__(self, debug=False):
        self.debug = debug
        self.extracted_figures = set()

    def detect(self, page_images, output_dir):

        os.makedirs(output_dir, exist_ok=True)

        total = 0

        print("\n==============================")
        print("STRICT FIGURE DETECTION MODE")
        print("==============================\n")

        for page_path in page_images:

            print(f"\n📄 Processing page: {page_path}")

            image = cv2.imread(page_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            data = pytesseract.image_to_data(
                gray,
                output_type=pytesseract.Output.DICT,
                config="--oem 3 --psm 6"
            )

            n_boxes = len(data["text"])

            for i in range(n_boxes):

                word = data["text"][i].strip()

                if not word:
                    continue

                if self.FIG_PATTERN.match(word):

                    fig_label = word.replace(" ", "")

                    if fig_label in self.extracted_figures:
                        print(f"⚠ Duplicate skipped: {fig_label}")
                        continue

                    self.extracted_figures.add(fig_label)

                    x = data["left"][i]
                    y = data["top"][i]
                    w = data["width"][i]
                    h = data["height"][i]

                    print(f"✅ Valid caption detected: {fig_label}")

                    cropped = self._crop_figure(image, y)

                    save_path = os.path.join(
                        output_dir,
                        f"{fig_label.replace('.', '_')}.png"
                    )

                    cv2.imwrite(save_path, cropped)

                    print(f"💾 Saved: {save_path}")

                    total += 1

        print(f"\n🎯 Total figures extracted: {total}")
        return total

    def _crop_figure(self, image, caption_y):

        # Crop region ABOVE caption
        top_crop = 0
        bottom_crop = max(0, caption_y - 10)

        region = image[top_crop:bottom_crop, :]

        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

        # Remove white margins
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

        coords = cv2.findNonZero(thresh)

        if coords is None:
            return region

        x, y, w, h = cv2.boundingRect(coords)

        cropped = region[y:y+h, x:x+w]

        return cropped
