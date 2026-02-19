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
FIG_REGEX      = re.compile(r"Fig[.,]?\s*\d+[\.\-]\d+", re.IGNORECASE)
MIN_FIG_H      = 40     # min figure height in pixels
MIN_FIG_W      = 40     # min figure width in pixels
WHITE_THRESH   = 240    # luminance above which a pixel is "white"
PAD            = 12     # padding around tight crop (px)
CAPTION_PAD    = 10     # extra px below caption baseline to include
COL_MARGIN     = 60     # horizontal margin around caption column
# ─────────────────────────────────────────────────────────────────────────────


def _norm_label(label: str) -> str:
    """Normalise a Fig label to canonical form 'Fig. X.Y' for deduplication.

    Handles OCR variants: 'Fig 1.2', 'Fig.1.2', 'Fig 1-2', etc.
    """
    m = re.search(r"(\d+)[\.\-](\d+)", label)
    if m:
        return f"Fig. {m.group(1)}.{m.group(2)}"
    return label


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


def _find_captions(img_rgb: np.ndarray, return_ocr_data: bool = False):
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
        is_caption  = bool(re.match(r"Fig[.,]?$",words[0], re.IGNORECASE))
        fig_tok_pos = 0  # position of "Fig." in words list

        # ── Rule 2: "Fig." in second half, followed by Title-Case words ───────
        if not is_caption:
            pos = next(
                (p for p, w in enumerate(words)
                 if re.match(r"Fig[.,]?$",w, re.IGNORECASE)),
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

        # ── Reject false positives ────────────────────────────────────────────
        # 1. Range references: "Fig. 1.3 to Fig. 1.8" is a range, not a caption
        if re.search(r"Fig[.,]?\s*\d+[\.\-]\d+\s+to\s+Fig", line_text, re.IGNORECASE):
            continue

        # 2. Sentence continuation: after "Fig. X.Y", text reads like a sentence
        #    For Rule 1 (standalone caption line, fig_tok_pos==0): only reject
        #    on strong sentence-starters ("the", "it", "this", etc.).
        #    For Rule 2 (mid-line "Fig." in two-column layout): also reject
        #    if the first word after the label is lowercase (more aggressive),
        #    since real two-column captions have Title-Case descriptions.
        _SENTENCE_STARTERS = {
            "the", "this", "it", "its", "such", "that", "these",
            "those", "there", "here", "when", "where", "which", "who", "is",
            "are", "was", "were", "has", "have", "had", "to", "as", "so",
            # Verbs that indicate a forward-reference sentence like
            # "Fig. 1.32 shows a uniform..." (not a standalone caption)
            "shows", "show", "illustrates", "illustrate", "depicts", "depict",
            "represents", "represent", "gives", "give",
        }
        after_label = line_text[match.end():].strip().lstrip(".,")
        first_after_words = after_label.split()
        first_after = first_after_words[0] if first_after_words else ""
        if first_after and first_after.lower() in _SENTENCE_STARTERS:
            continue
        # Only reject lowercase-first-word for Rule 2 (mid-line) captures;
        # Rule 1 standalone captions like "Fig. 1.32 shows a uniform..." are valid.
        if fig_tok_pos > 0 and first_after and first_after[0].islower():
            continue

        # 3. Rule 2 false positives: the "second half" detection may fire on
        #    exercise question lines like "8. Explain ... Fig. 1.40 ..."
        #    Reject if the line text contains question-number pattern at start
        #    and the Fig reference is buried in question body text
        if fig_tok_pos > 0:
            # For Rule 2 captures, verify the words after Fig.X.Y are a clean
            # description (all Title-Case, no lowercase sentence words like
            # "of", "in", "the" as the second word after the label)
            after_fig = [words[j] for j in range(fig_tok_pos + 2, len(words)) if words[j]]
            if len(after_fig) >= 2 and after_fig[1][:1].islower():
                continue
        # ─────────────────────────────────────────────────────────────────────

        norm = _norm_label(label)
        if norm in seen_labels:
            continue
        seen_labels.add(norm)

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

        # ── Handle merged caption lines ───────────────────────────────────────
        # OCR sometimes merges two side-by-side captions into one line, e.g.:
        # "Fig. 1.10 Turning a Fig. 1.11 Tightening"
        # Find any additional Fig. labels after the first one.
        remainder = line_text[match.end():]
        extra_matches = list(FIG_REGEX.finditer(remainder))
        for em in extra_matches:
            extra_label = em.group()
            extra_norm  = _norm_label(extra_label)
            if extra_norm in seen_labels:
                continue
            # Check it's followed by a caption-like word (not inline ref)
            after_extra = remainder[em.end():].strip().lstrip(".,")
            after_extra_words = after_extra.split()
            first_extra_after = after_extra_words[0] if after_extra_words else ""
            # Accept if the next word is Title-Case or empty (label only)
            if first_extra_after and first_extra_after[0].islower():
                continue
            if first_extra_after and first_extra_after.lower() in _SENTENCE_STARTERS:
                continue
            seen_labels.add(extra_norm)
            # Find word index of this extra label in the token list
            extra_tok_pos = next(
                (p for p, w in enumerate(words)
                 if re.match(r"Fig[.,]?$",w, re.IGNORECASE)
                 and p > fig_tok_pos),
                None,
            )
            if extra_tok_pos is not None:
                ex_indices = indices[extra_tok_pos:]
            else:
                ex_indices = cap_indices  # fallback: reuse first caption bbox
            ex_tops    = [data["top"][i]                     for i in ex_indices]
            ex_bottoms = [data["top"][i] + data["height"][i] for i in ex_indices]
            ex_lefts   = [data["left"][i]                    for i in ex_indices]
            ex_rights  = [data["left"][i] + data["width"][i] for i in ex_indices]
            found.append({
                "label":   extra_label,
                "caption": extra_label + " " + after_extra[:60],
                "top":     min(ex_tops),
                "bottom":  max(ex_bottoms),
                "left":    min(ex_lefts),
                "right":   max(ex_rights),
            })

    found.sort(key=lambda c: c["top"])
    if return_ocr_data:
        return found, data
    return found


def _find_exercise_figures(img_rgb: np.ndarray,
                            already_found: list,
                            data: dict) -> list:
    """
    Second-pass: find exercise figures whose labels appear inline in
    question text (e.g. "shown in Fig. 1.27" or "as shown in Fig. 1.29").

    Strategy
    --------
    1. Collect every Fig. X.Y label referenced anywhere on the page.
    2. Remove labels already captured by the main caption pass.
    3. For each uncaptured label, find its Y position from the OCR data.
    4. Scan UPWARD from that Y position to find the nearest non-text
       visual block (the figure drawing) by looking for a row that has
       high pixel density (content) but is isolated (whitespace above it).
    5. Tight-crop that block and synthesise a caption-like entry.

    Returns a list of additional caption dicts in the same format as
    _find_captions, with is_exercise=True so the caller can label them
    differently (e.g. "Fig. 1.27 (exercise)").
    """
    n = len(data["text"])

    # Verbs that indicate a cross-reference sentence rather than an exercise
    # figure: "Fig. 1.32 shows a uniform metre rule..." → skip, it's pointing
    # to a figure on another page.
    _CROSS_REF_VERBS = {
        "shows", "show", "illustrates", "illustrate", "depicts", "depict",
        "represents", "represent", "gives", "give",
    }

    # Build (label → list of Y positions where it is referenced)
    label_refs = defaultdict(list)
    for i in range(n):
        word = (data["text"][i] or "").strip()
        if not word:
            continue
        # Gather up to 3 consecutive tokens to form "Fig. 1.27"
        joined_parts = []
        for j in range(i, min(i + 3, n)):
            w = (data["text"][j] or "").strip()
            if w:
                joined_parts.append(w)
        joined = " ".join(joined_parts)
        m = FIG_REGEX.match(joined)
        if m:
            label = m.group()
            top   = data["top"][i]
            left  = data["left"][i]
            # Skip cross-reference lines: "Fig. 1.32 shows a uniform..."
            # Look at the word after the label match in the token stream.
            match_end_len = len(m.group().split())  # approx tokens consumed
            next_tok_idx  = i + match_end_len
            while next_tok_idx < n and not (data["text"][next_tok_idx] or "").strip():
                next_tok_idx += 1
            next_tok = (data["text"][next_tok_idx] or "").strip().lower() if next_tok_idx < n else ""
            if next_tok in _CROSS_REF_VERBS:
                continue
            label_refs[label].append({"top": top, "left": left})

    # Use normalised labels to avoid duplicates due to OCR variants (e.g.
    # "Fig 1.36" vs "Fig. 1.36" should not produce two entries).
    captured = {_norm_label(c["label"]) for c in already_found}
    extra = []

    img_h, img_w = img_rgb.shape[:2]

    for label, refs in label_refs.items():
        if _norm_label(label) in captured:
            continue

        # Use the topmost reference location as the anchor
        refs.sort(key=lambda r: r["top"])
        ref_top  = refs[0]["top"]
        ref_left = refs[0]["left"]

        # Determine column: left or right half
        if ref_left < img_w / 2:
            col_l, col_r = 0, img_w // 2 + 60
        else:
            col_l, col_r = img_w // 2 - 60, img_w

        # Scan upward from ref_top to find a non-text visual block.
        # A visual block is a region with rows having content pixels
        # separated by whitespace from the surrounding text.
        search_top = max(ref_top - 600, 0)
        col_slice  = img_rgb[search_top:ref_top, col_l:col_r]
        if col_slice.shape[0] < 10:
            continue

        non_white = np.any(col_slice < WHITE_THRESH, axis=2)
        density   = non_white.mean(axis=1)

        # Find the nearest non-text visual block ABOVE the reference,
        # working bottom-to-top within the search window.
        CONTENT_THRESH = 0.03   # row is "content" if >3% pixels are non-white
        GAP_THRESH     = 0.005  # row is "gap" if <0.5% pixels are non-white
        MIN_BLOCK_H    = 15     # minimum figure height in pixels

        rows = len(density)
        block_bottom = None
        block_top    = None
        in_content   = False

        for r in range(rows - 1, -1, -1):
            d = density[r]
            if d >= CONTENT_THRESH and not in_content:
                block_bottom = r
                in_content   = True
            elif d < GAP_THRESH and in_content:
                block_top    = r + 1
                break

        if block_bottom is None:
            continue
        if block_top is None:
            block_top = 0

        if block_bottom - block_top < MIN_BLOCK_H:
            continue

        abs_top    = search_top + block_top
        abs_bottom = search_top + block_bottom

        # Tight-crop horizontally within the column
        band = img_rgb[abs_top:abs_bottom, col_l:col_r]
        mask = np.any(band < WHITE_THRESH, axis=2)
        cols = np.any(mask, axis=0)
        if not cols.any():
            continue
        c0 = int(np.where(cols)[0][0])
        c1 = int(np.where(cols)[0][-1])

        extra.append({
            "label":       label,
            "caption":     label,        # label only — no separate caption line
            "top":         abs_top,
            "bottom":      abs_bottom,
            "left":        col_l + c0,
            "right":       col_l + c1,
            "is_exercise": True,
        })
        captured.add(_norm_label(label))

    extra.sort(key=lambda c: c["top"])
    return extra


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
    # Global set of normalised labels already extracted (across all pages).
    # Used to avoid duplicate exercise entries for cross-page references.
    global_captured: set = set()

    for page_num, page in enumerate(doc, start=1):
        img_rgb = _get_page_image(page)
        h, w    = img_rgb.shape[:2]

        if debug:
            print(f"  Page {page_num}: {w}x{h} px")

        if mode == "no_caption":
            _no_caption_blobs(img_rgb, page_num, output_dir, figures, counter)
            continue

        # Pass 1: standard caption-anchored detection
        captions, ocr_data = _find_captions(img_rgb, return_ocr_data=True)

        # Pass 2: exercise figures whose labels appear inline in question text.
        # Pass global_captured so cross-page refs (e.g. "Fig. 1.35" referenced
        # on page 12 but captioned on page 13) are not extracted twice.
        page_captured = {_norm_label(c["label"]) for c in captions} | global_captured
        exercise_caps = _find_exercise_figures(
            img_rgb,
            [{"label": lbl} for lbl in page_captured],   # synthetic list for compat
            ocr_data,
        )

        # Merge and sort by Y position
        all_caps = sorted(captions + exercise_caps, key=lambda c: c["top"])

        if debug:
            for c in all_caps:
                tag = "[ex]" if c.get("is_exercise") else "    "
                print(f"  {tag} {c['label']:12s} top={c['top']:4d} "
                      f"left={c['left']:4d}  {c['caption'][:50]}")

        if not all_caps:
            continue

        # Track prev_bottom separately per column so that a left-column caption
        # does not restrict the search band for a subsequent right-column caption.
        prev_bottom_left  = 0   # bottom of last processed left-column caption
        prev_bottom_right = 0   # bottom of last processed right-column caption
        # Also track the band_top used for the last crop in each column so
        # merged same-row captions (e.g. "Fig.1.10 ... Fig.1.11 ...") can
        # share the same vertical search band.
        last_band_top_left  = 0
        last_band_top_right = 0

        for cap in all_caps:
            # ── Exercise figures: bounding box already computed ──────────────
            if cap.get("is_exercise"):
                fig_top    = cap["top"]
                fig_bottom = cap["bottom"]
                fig_left   = cap["left"]
                fig_right  = cap["right"]

                # Use a smaller minimum for exercise figures (thin diagrams)
                MIN_EX_H = 20
                if (fig_right - fig_left) < MIN_FIG_W or (fig_bottom - fig_top) < MIN_EX_H:
                    continue

                counter[0] += 1
                label    = cap["label"]
                fig_name = re.sub(r"[^a-zA-Z0-9]", "_", label).strip("_")
                fname    = f"page_{page_num}_{fig_name}_ex.png"

                # Save without caption strip (no standalone caption line)
                hh, ww = img_rgb.shape[:2]
                t = max(fig_top   - PAD, 0)
                b = min(fig_bottom + PAD, hh)
                l = max(fig_left  - PAD, 0)
                r = min(fig_right + PAD, ww)
                Image.fromarray(img_rgb[t:b, l:r]).save(str(output_dir / fname), "PNG")

                figures.append({
                    "figure_label": label,
                    "page_number":  page_num,
                    "image_file":   fname,
                    "caption":      cap["caption"],
                    "bbox":         [fig_left, fig_top, fig_right, fig_bottom],
                    "source":       "exercise",
                })
                global_captured.add(_norm_label(label))
                continue

            # ── Determine figure's column ────────────────────────────────────
            cap_mid  = (cap["left"] + cap["right"]) / 2
            page_mid = w / 2

            if cap_mid < page_mid:
                col_l    = 0
                col_r    = min(cap["right"] + COL_MARGIN, w)
                band_top = prev_bottom_left
                last_band_top = last_band_top_left
            else:
                col_l    = max(cap["left"] - COL_MARGIN, 0)
                col_r    = w
                band_top = prev_bottom_right
                last_band_top = last_band_top_right

            band_bottom = cap["top"]

            # Merged same-row caption: band would be zero or negative because
            # prev_bottom was already advanced past this caption's top.
            # Reuse the previous band_top for this column (same figure row).
            if band_bottom <= band_top:
                band_top = last_band_top

            if band_bottom - band_top < MIN_FIG_H:
                if cap_mid < page_mid:
                    prev_bottom_left  = cap["bottom"]
                else:
                    prev_bottom_right = cap["bottom"]
                continue

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
                if cap_mid < page_mid:
                    last_band_top_left  = band_top
                    prev_bottom_left    = cap["bottom"]
                else:
                    last_band_top_right = band_top
                    prev_bottom_right   = cap["bottom"]
                continue

            fig_top, fig_bottom, fig_left, fig_right = bbox
            if (fig_right - fig_left) < MIN_FIG_W or (fig_bottom - fig_top) < MIN_FIG_H:
                if cap_mid < page_mid:
                    last_band_top_left  = band_top
                    prev_bottom_left    = cap["bottom"]
                else:
                    last_band_top_right = band_top
                    prev_bottom_right   = cap["bottom"]
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
                "source":       "theory",
            })
            global_captured.add(_norm_label(label))

            if debug:
                print(f"    saved {fname}  col=[{col_l},{col_r}]  "
                      f"content={fig_left},{fig_top}..{fig_right},{fig_bottom}")

            if cap_mid < page_mid:
                last_band_top_left  = band_top
                prev_bottom_left    = cap["bottom"]
            else:
                last_band_top_right = band_top
                prev_bottom_right   = cap["bottom"]

    doc.close()

    # ── Post-processing: deduplicate across pages ─────────────────────────────
    # A cross-page exercise reference (e.g. "see Fig. 1.35" on page 12 when
    # the figure is captioned on page 13) may produce two entries for the same
    # label.  Keep the theory entry; remove the exercise duplicate.
    seen_norm: dict = {}  # norm_label → index in figures
    deduped: list = []
    for fig in figures:
        norm = _norm_label(fig["figure_label"])
        if norm not in seen_norm:
            seen_norm[norm] = len(deduped)
            deduped.append(fig)
        else:
            existing = deduped[seen_norm[norm]]
            # Prefer theory over exercise; prefer earlier page if both same source
            if existing.get("source") == "exercise" and fig.get("source") == "theory":
                # Delete the stale exercise image file if it was saved
                stale_path = output_dir / existing["image_file"]
                if stale_path.exists():
                    stale_path.unlink()
                deduped[seen_norm[norm]] = fig
    figures = deduped
    # ─────────────────────────────────────────────────────────────────────────

    metadata  = {"figures": figures}
    meta_path = output_dir / "image_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"  [{len(figures)} figure(s) -> {output_dir}]")
    return metadata
