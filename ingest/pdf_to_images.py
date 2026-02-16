# ingest/pdf_to_images.py

import os
from pdf2image import convert_from_path


class PDFToImages:

    def __init__(self, dpi=180):
        self.dpi = dpi

    def convert(self, pdf_path, output_dir):

        os.makedirs(output_dir, exist_ok=True)

        pages = convert_from_path(pdf_path, dpi=self.dpi)

        image_paths = []

        for i, page in enumerate(pages):
            path = os.path.join(output_dir, f"page_{i+1}.png")
            page.save(path, "PNG")
            image_paths.append(path)

        return image_paths
