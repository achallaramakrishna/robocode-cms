import cv2
import os
import numpy as np


class SimpleFigureExtractor:

    def __init__(self, min_area=40000, padding=20):
        self.min_area = min_area
        self.padding = padding

    def extract(self, pages, output_dir):

        os.makedirs(output_dir, exist_ok=True)

        total = 0

        for page_path in pages:

            img = cv2.imread(page_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Threshold for diagrams
            _, thresh = cv2.threshold(
                gray, 200, 255, cv2.THRESH_BINARY_INV
            )

            contours, _ = cv2.findContours(
                thresh,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            page_no = page_path.split("_")[-1].split(".")[0]

            for i, cnt in enumerate(contours):

                area = cv2.contourArea(cnt)

                if area < self.min_area:
                    continue

                x, y, w, h = cv2.boundingRect(cnt)

                # Add white padding
                x1 = max(0, x - self.padding)
                y1 = max(0, y - self.padding)
                x2 = min(img.shape[1], x + w + self.padding)
                y2 = min(img.shape[0], y + h + self.padding)

                crop = img[y1:y2, x1:x2]

                save_path = os.path.join(
                    output_dir,
                    f"page_{page_no}_fig_{i+1}.png"
                )

                cv2.imwrite(save_path, crop)
                total += 1

        return total
