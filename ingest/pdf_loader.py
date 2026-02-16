from pathlib import Path
import uuid
import shutil


class PDFLoader:

    def __init__(self, base_upload_dir: str):
        self.base_upload_dir = Path(base_upload_dir)

    def load_chapter_pdf(self, source_pdf_path: str):

        source_pdf_path = Path(source_pdf_path)

        chapter_uuid = str(uuid.uuid4())

        chapter_dir = self.base_upload_dir / chapter_uuid
        chapter_dir.mkdir(parents=True, exist_ok=True)

        dest_pdf_path = chapter_dir / source_pdf_path.name
        shutil.copy(source_pdf_path, dest_pdf_path)

        return {
            "chapter_id": chapter_uuid,
            "chapter_dir": str(chapter_dir),
            "pdf_path": str(dest_pdf_path)
        }
