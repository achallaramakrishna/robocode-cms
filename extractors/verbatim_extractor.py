import base64
import json
import requests
from pathlib import Path


class VerbatimExtractor:

    def __init__(self, api_key: str, model="gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.openai.com/v1/responses"

        self.prompt = """
CRITICAL MODE: VERBATIM EXTRACTION

If page contains:
EXERCISE
NUMERICALS
MULTIPLE CHOICE
SHORT ANSWER
LONG ANSWER

Extract ALL questions EXACTLY as printed.

STRICT RULES:
- Preserve numbering exactly
- Preserve subparts (a), (b), (i), (ii)
- Preserve nuclear notation exactly
- Preserve reaction arrows
- Preserve units
- Preserve MCQ options
- Preserve given answers
- DO NOT rewrite
- DO NOT solve

Return JSON:

{
  "exercise_sections": [
    {
      "section_title": "",
      "questions": [
        {
          "number": "",
          "question_text": "",
          "sub_parts": [],
          "options": [],
          "given_answer": ""
        }
      ]
    }
  ]
}
"""

    def _encode_image(self, image_path: Path):
        b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    def extract(self, image_path: Path):

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

        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()

        output = response.json()

        text = ""
        for item in output.get("output", []):
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")

        return json.loads(text.strip())
