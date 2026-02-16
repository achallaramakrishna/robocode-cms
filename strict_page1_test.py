from ingest.strict_page_rectangle_detector import StrictPageRectangleDetector
from ingest.pdf_to_images import PDFToImages
from pathlib import Path

pdf = r"input_pdfs/physics/class10/cbse_10_1/selina-class-10-physics-chapter-1-force.pdf"

print("Rendering PDF...")
converter = PDFToImages()
pages = converter.convert(pdf, "temp_pages")

if not pages:
    print("No pages rendered.")
    exit()

print(f"Total pages rendered: {len(pages)}")

print("Running detector on page 1...")
detector = StrictPageRectangleDetector(debug=True)  # <-- enable debug mode

result = detector.detect_page(
    page_path=pages[0],
    output_dir="temp_figures",
    page_number=1
)

print("\nRESULTS:")
print(result)

if result:
    print(f"\nFigures detected: {len(result)}")
    for r in result:
        print(f"Figure file: {r.get('file_name')}")
        print(f"Caption: {r.get('caption')}")
else:
    print("No figures detected.")
