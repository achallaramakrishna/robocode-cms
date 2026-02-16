import cv2
import pytesseract
import os
import re
import numpy as np


class StrictPageRectangleDetector:

    def __init__(self, debug=False):
        self.debug = debug

    def detect_page(self, page_path, output_dir, page_number):

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        image = cv2.imread(page_path)
        if image is None:
            print("Failed to read image.")
            return []

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = image.shape[:2]

        # --------------------------------------------------
        # 1️⃣ Better Visual Block Detection
        # --------------------------------------------------
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            25,
            10
        )

        # 🔹 Smaller kernel (avoid merging full column text)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        contours, _ = cv2.findContours(
            dilated,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Sort top-to-bottom
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])

        results = []
        fig_count = 0

        for cnt in contours:

            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            print("Contour found:", x, y, w, h, "Area:", area)

            # ----------------------------
            # Basic filtering
            # ----------------------------
            if area < 10000:
                continue

            if area > 0.75 * (width * height):
                continue

            ratio = w / float(h)
            if ratio < 0.25 or ratio > 4.0:
                continue

            # ----------------------------
            # Caption detection below block
            # ----------------------------
            cap_top = y + h
            cap_bottom = min(cap_top + 200, height)

            caption_region = gray[
                y + h:y + h + 150,
                max(x - 40, 0):min(x + w + 40, width)
            ]

           

            if caption_region.size == 0:
                continue

            text = pytesseract.image_to_string(
                caption_region,
                config="--psm 6"
            ).strip()

            # Must contain Fig pattern
            match = re.search(r"Fig\.?\s*\d+\.\d+", text)
            if not match:
                continue

            # Reject inline references
            if ", Fig" in text or " in Fig" in text:
                continue

            fig_count += 1

            # ----------------------------
            # Crop image + caption
            # ----------------------------
            crop_bottom = min(cap_top + 80, height)
            # Expand bounding box slightly
            # Expand bounding box slightly
            expand_top = 20
            expand_bottom = 170
            expand_left = 40
            expand_right = 90   # extra space on right

            new_x = max(x - expand_left, 0)
            new_y = max(y - expand_top, 0)

            new_w = min(w + expand_left + expand_right, width - new_x)
            new_h = min(h + expand_bottom, height - new_y)

            cropped = image[new_y:new_y + new_h, new_x:new_x + new_w]


            # ----------------------------
            # Trim left/right whitespace
            # ----------------------------
            crop_gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            _, thresh_crop = cv2.threshold(crop_gray, 245, 255, cv2.THRESH_BINARY_INV)

            coords = cv2.findNonZero(thresh_crop)

            if coords is not None:
                x_vals = coords[:, 0, 0]
                min_x = max(np.min(x_vals) - 10, 0)
                max_x = min(np.max(x_vals) + 40, cropped.shape[1])  # leave extra right margin
                cropped = cropped[:, min_x:max_x]

            file_name = f"page_{page_number}_fig_{fig_count}.png"
            file_path = os.path.join(output_dir, file_name)

            cv2.imwrite(file_path, cropped)

            results.append({
                "file_name": file_name,
                "caption": match.group()
            })

            if self.debug:
                print(f"Detected Figure: {file_name}")
                print("Caption:", match.group())

        return results
