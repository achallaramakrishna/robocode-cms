import base64
import json
import re
from pathlib import Path
import requests


class OpenAIVisionOCR:
    """
    Vision OCR engine for RoboDynamics LMS.
    Designed for learning-optimized structured extraction.
    """

    def __init__(
        self,
        api_key: str,
        prompt_file: Path,
        model: str = "gpt-4o-mini"
    ):
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")

        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        self.api_key = api_key
        self.model = model
        self.prompt = prompt_file.read_text(encoding="utf-8")
        self.url = "https://api.openai.com/v1/responses"

    # -------------------------------------------------
    # Utilities
    # -------------------------------------------------

    def _encode_image(self, image_path: Path) -> str:
        b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def _clean_json_text(self, text: str) -> str:
        text = re.sub(r"^```json", "", text, flags=re.IGNORECASE).strip()
        text = re.sub(r"^```", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
        text = text.replace("\u2026", "...").replace("\u00b0", "°")
        text = re.sub(r"[\x00-\x1F\x7F]", "", text)
        return text

    def _default_structure(self):
        return {
            "definitions": [],
            "laws": [],
            "formulas": [],
            "differences": [],
            "unit_mappings": [],
            "conceptual_facts": [],
            "derivations": [],
            "examples": [],
            "exercise_sections": [],
            "mcq_sections": [],
            "numerical_sections": [],
            "short_long_sections": [],
            "diagrams": [],
            "tables": []
        }

    def _extract_structured_json(self, response_json: dict) -> dict:
        texts = []

        for item in response_json.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texts.append(content.get("text", ""))

        combined = self._clean_json_text("\n".join(texts))

        try:
            parsed = json.loads(combined)

            # Ensure all required keys exist
            default = self._default_structure()
            for key in default:
                if key not in parsed:
                    parsed[key] = []

            return parsed

        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed. Using fallback structure.")
            fallback = self._default_structure()
            fallback["_raw_text_fallback"] = combined
            return fallback

    # -------------------------------------------------
    # OCR Runner
    # -------------------------------------------------

    def ocr_page(self, image_path: Path) -> dict:
        page_number = int(image_path.stem.split("_")[1])

        payload = {
            "model": self.model,
            "input": [{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": self.prompt},
                    {"type": "input_image", "image_url": self._encode_image(image_path)}
                ]
            }]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        structured = self._extract_structured_json(response.json())

        return {
            "page_number": page_number,
            "image": image_path.name,
            "structured_content": structured,
            "meta": {
                "model": self.model,
                "learning_schema": True
            }
        }
