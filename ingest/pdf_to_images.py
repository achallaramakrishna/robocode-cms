from pathlib import Path
from pdf2image import convert_from_path
import cv2
import numpy as np


class PDFToImages:
    def __init__(self, dpi=150):
        self.dpi = dpi

    def convert(self, pdf_path: str, output_dir: str):
        pdf_path = str(pdf_path)
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        pages = convert_from_path(pdf_path, dpi=self.dpi)

        page_paths = []
        for i, pil_img in enumerate(pages, start=1):
            path = out / f"page_{i}.png"

            # PIL -> OpenCV (stable write on Windows)
            arr = np.array(pil_img)
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(path), bgr)

            page_paths.append(str(path))

        return page_paths
