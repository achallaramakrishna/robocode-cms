import cv2
from pathlib import Path
from strict_page_rectangle_detector import StrictPageRectangleDetector

# ----------------------------------------
# CONFIG
# ----------------------------------------
PAGE_IMAGE = r"C:\robocode\workspace\courses\55\07af590b-f79b-46a3-9427-ed2c64c0e843\pages\page_1.png"
OUTPUT_DIR = r"C:\robocode\workspace\test_output"

# ----------------------------------------
# RUN
# ----------------------------------------
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

detector = StrictPageRectangleDetector()

result = detector.extract_diagrams_from_page(
    PAGE_IMAGE,
    OUTPUT_DIR
)

print("\n==============================")
print("EXTRACTION RESULT")
print("==============================")
print(f"Total Figures Found: {result['total_figures']}")

for item in result["metadata"]:
    print(f"Saved: {item['file']}")
