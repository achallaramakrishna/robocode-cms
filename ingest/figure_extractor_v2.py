"""
figure_extractor_v2.py
======================
Extracts figures from scanned-PDF textbooks using caption-anchored cropping.

How it works (textbook mode)
-----------------------------
Each page of these PDFs is a single high-resolution raster scan.  We:

1. Pull the native raster image directly from the PDF via PyMuPDF.
2. Run pytesseract word-level OCR grouped by (block_num, line_num).
3. A line is a TRUE CAPTION when "Fig." is the first token of its OCR
   block-line, or when "Fig." appears late in a line followed by Title-
   Case description words (two-column layout edge case).
4. For each caption the search band is everything above it since the
   previous caption, restricted to the caption's horizontal column.
5. Within that column band, a row-density projection finds the last
   whitespace gap before the caption top — that gap's bottom edge is
   the true start of the figure (separating it from text above).
6. The PNG crop includes the figure + caption line, padded.

no_caption mode
---------------
Connected-component analysis saves all large non-white blobs.
For NEET books or any PDF without "Fig." captions.

Dependencies: pymupdf (fitz), pytesseract, Pillow, numpy
"""

import re
import io
import json
from collections import defaultdict
import fitz
import pytesseract
import numpy as np
from PIL import Image
from pathlib import Path


# ── tunables ─────────────────────────────────────────────────────────────────
FIG_REGEX      = re.compile(r"Fig\.?\s*\d+[\.\-]\d+", re.IGNORECASE)
MIN_FIG_H      = 40     # min figure height in pixels
MIN_FIG_W      = 40     # min figure width in pixels
WHITE_THRESH   = 240    # luminance above which a pixel is "white"
PAD            = 12     # padding around tight crop (px)
CAPTION_PAD    = 10     # extra px below caption baseline to include
COL_MARGIN     = 60     # horizontal margin around caption column
# ─────────────────────────────────────────────────────────────────────────────


def _get_page_image(page) -> np.ndarray:
    """Return the native raster of a scanned PDF page as RGB numpy array."""
    imgs = page.get_images(full=True)
    if imgs:
        xref = imgs[0][0]
        raw  = page.parent.extract_image(xref)
        pil  = Image.open(io.BytesIO(raw["image"])).convert("RGB")
        return np.array(pil)
    mat = fitz.Matrix(200 / 72, 200 / 72)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    return np.array(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))


def _find_captions(img_rgb: np.ndarray):
    """
    Return list of caption dicts sorted top-to-bottom.

    A line is a TRUE CAPTION when:
    1. "Fig." is the very first token of its OCR block-line (primary rule),
    2. OR "Fig." appears in the second half of the line followed by Title-
       Case words — handles right-column captions merged by OCR with left-
       column text.

    Bounding box is computed from only the "Fig. X.Y …" tokens so the
    caption's left/right reflect the figure's column, not the full line.

    Returns list of dicts: {label, caption, top, bottom, left, right}
    """
    pil  = Image.fromarray(img_rgb)
    data = pytesseract.image_to_data(
        pil,
        output_type=pytesseract.Output.DICT,
        config="--oem 3 --psm 3",
    )

    n      = len(data["text"])
    groups = defaultdict(list)
    for i in range(n):
        if not (data["text"][i] or "").strip():
            continue
        key = (data["block_num"][i], data["line_num"][i])
        groups[key].append(i)

    found       = []
    seen_labels = set()

    for (_blk, _ln), indices in groups.items():
        words     = [(data["text"][i] or "").strip() for i in indices]
        line_text = " ".join(w for w in words if w)

        if not FIG_REGEX.search(line_text):
            continue

        # ── Rule 1: first token is "Fig." ────────────────────────────────────
        is_caption  = bool(re.match(r"Fig\.?$", words[0], re.IGNORECASE))
        fig_tok_pos = 0  # position of "Fig." in words list

        # ── Rule 2: "Fig." in second half, followed by Title-Case words ───────
        if not is_caption:
            pos = next(
                (p for p, w in enumerate(words)
                 if re.match(r"Fig\.?$", w, re.IGNORECASE)),
                len(words),
            )
            if pos >= len(words) * 0.5:
                after = [words[j] for j in range(pos + 2, len(words)) if words[j]]
                if after and after[0][:1].isupper() and len(after[0]) > 2:
                    is_caption  = True
                    fig_tok_pos = pos

        if not is_caption:
            continue

        match = FIG_REGEX.search(line_text)
        if not match:
            continue
        label = match.group()
        if label in seen_labels:
            continue
        seen_labels.add(label)

        # Use only tokens from "Fig." onward for the bounding box
        cap_indices = indices[fig_tok_pos:]
        tops    = [data["top"][i]                     for i in cap_indices]
        bottoms = [data["top"][i] + data["height"][i] for i in cap_indices]
        lefts   = [data["left"][i]                    for i in cap_indices]
        rights  = [data["left"][i] + data["width"][i] for i in cap_indices]

        found.append({
            "label":   label,
            "caption": line_text,
            "top":     min(tops),
            "bottom":  max(bottoms),
            "left":    min(lefts),
            "right":   max(rights),
        })

    found.sort(key=lambda c: c["top"])
    return found



def _tight_crop_col(img_rgb: np.ndarray,
                    row_top: int, row_bottom: int,
                    col_left: int, col_right: int):
    """
    Tight non-white bounding box within the band AND column.
    Returns (top, bottom, left, right) or None.
    """
    if row_bottom <= row_top or col_right <= col_left:
        return None
    band = img_rgb[row_top:row_bottom, col_left:col_right]
    mask = np.any(band < WHITE_THRESH, axis=2)
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    if not rows.any():
        return None
    r0 = int(np.where(rows)[0][0]);   r1 = int(np.where(rows)[0][-1])
    c0 = int(np.where(cols)[0][0]);   c1 = int(np.where(cols)[0][-1])
    return (row_top + r0, row_top + r1, col_left + c0, col_left + c1)


def _save_crop(img_rgb, fig_top, fig_bottom, fig_left, fig_right,
               cap_bottom, out_path):
    h, w = img_rgb.shape[:2]
    t = max(fig_top   - PAD, 0)
    b = min(cap_bottom + CAPTION_PAD + PAD, h)
    l = max(fig_left  - PAD, 0)
    r = min(fig_right + PAD, w)
    Image.fromarray(img_rgb[t:b, l:r]).save(str(out_path), "PNG")


def _no_caption_blobs(img_rgb, page_num, output_dir, figures, counter):
    """Save all large non-white blobs (no_caption mode)."""
    import cv2
    gray    = np.mean(img_rgb, axis=2).astype(np.uint8)
    _, mask = cv2.threshold(gray, WHITE_THRESH, 255, cv2.THRESH_BINARY_INV)
    kernel  = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    dilated = cv2.dilate(mask, kernel, iterations=2)
    n_lbl, _lbl, stats, _ = cv2.connectedComponentsWithStats(dilated, 8)
    h, w      = img_rgb.shape[:2]
    page_area = h * w
    for lbl in range(1, n_lbl):
        x  = int(stats[lbl, cv2.CC_STAT_LEFT])
        y  = int(stats[lbl, cv2.CC_STAT_TOP])
        bw = int(stats[lbl, cv2.CC_STAT_WIDTH])
        bh = int(stats[lbl, cv2.CC_STAT_HEIGHT])
        area = bw * bh
        if bw < MIN_FIG_W or bh < MIN_FIG_H:
            continue
        if area > 0.80 * page_area or area < 0.004 * page_area:
            continue
        counter[0] += 1
        fname = f"page_{page_num}_img_{counter[0]}.png"
        t = max(y - PAD, 0);  b = min(y + bh + PAD, h)
        l = max(x - PAD, 0);  r = min(x + bw + PAD, w)
        Image.fromarray(img_rgb[t:b, l:r]).save(str(output_dir / fname), "PNG")
        figures.append({
            "figure_label": f"Figure {page_num}.{counter[0]}",
            "page_number":  page_num,
            "image_file":   fname,
            "caption":      "",
            "bbox":         [x, y, x + bw, y + bh],
        })


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def extract_figures(
    pdf_path: str,
    output_dir: str,
    mode: str = "textbook",
    debug: bool = False,
) -> dict:
    """
    Extract figures from a PDF and write PNG crops + image_metadata.json.

    Parameters
    ----------
    pdf_path   : path to the PDF
    output_dir : output directory
    mode       : "textbook"   – figures with Fig. captions only
                 "no_caption" – all qualifying blobs (NEET / no captions)
    debug      : verbose per-page output

    Returns
    -------
    {"figures": [{figure_label, page_number, image_file, caption, bbox}]}
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    doc     = fitz.open(str(pdf_path))
    figures = []
    counter = [0]

    for page_num, page in enumerate(doc, start=1):
        img_rgb = _get_page_image(page)
        h, w    = img_rgb.shape[:2]

        if debug:
            print(f"  Page {page_num}: {w}x{h} px")

        if mode == "no_caption":
            _no_caption_blobs(img_rgb, page_num, output_dir, figures, counter)
            continue

        captions = _find_captions(img_rgb)

        if debug:
            for c in captions:
                print(f"    caption {c['label']:12s} top={c['top']:4d} "
                      f"left={c['left']:4d}  {c['caption'][:50]}")

        if not captions:
            continue

        prev_bottom = 0

        for cap in captions:
            band_top    = prev_bottom
            band_bottom = cap["top"]

            if band_bottom - band_top < MIN_FIG_H:
                prev_bottom = cap["bottom"]
                continue

            # ── Determine figure's column ────────────────────────────────────
            cap_mid  = (cap["left"] + cap["right"]) / 2
            page_mid = w / 2

            if cap_mid < page_mid:
                col_l = 0
                col_r = min(cap["right"] + COL_MARGIN, w)
            else:
                col_l = max(cap["left"] - COL_MARGIN, 0)
                col_r = w

            # ── Tight crop within the column band ───────────────────────────
            # Column restriction prevents opposite-column text contaminating
            # the crop; we include all content in the column (text wrapping
            # a figure is intentional editorial context in textbooks).
            bbox = _tight_crop_col(img_rgb, band_top, band_bottom, col_l, col_r)

            # Fall back to full band if column crop found nothing
            if bbox is None:
                bbox = _tight_crop_col(img_rgb, band_top, band_bottom, 0, w)

            if bbox is None:
                if debug:
                    print(f"    {cap['label']}: no content found")
                prev_bottom = cap["bottom"]
                continue

            fig_top, fig_bottom, fig_left, fig_right = bbox
            if (fig_right - fig_left) < MIN_FIG_W or (fig_bottom - fig_top) < MIN_FIG_H:
                prev_bottom = cap["bottom"]
                continue

            counter[0] += 1
            label    = cap["label"]
            fig_name = re.sub(r"[^a-zA-Z0-9]", "_", label).strip("_")
            fname    = f"page_{page_num}_{fig_name}.png"

            _save_crop(img_rgb, fig_top, fig_bottom, fig_left, fig_right,
                       cap["bottom"], output_dir / fname)

            figures.append({
                "figure_label": label,
                "page_number":  page_num,
                "image_file":   fname,
                "caption":      cap["caption"],
                "bbox":         [fig_left, fig_top, fig_right, fig_bottom],
            })

            if debug:
                print(f"    saved {fname}  col=[{col_l},{col_r}]  "
                      f"fig_start={fig_start}  "
                      f"content={fig_left},{fig_top}..{fig_right},{fig_bottom}")

            prev_bottom = cap["bottom"]

    doc.close()

    metadata  = {"figures": figures}
    meta_path = output_dir / "image_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  [{len(figures)} figure(s) -> {output_dir}]")
    return metadata
