"""
generate_session_html.py
=========================
Generates clean, professional HTML files from session notes JSON.
Creates one HTML file per topic/section, stored at:
  /opt/robodynamics/session_materials/{course_id}/

File naming: session{day}_{topic_slug}.html
Example: session1_jvm_jdk_jre.html, session1_primitive_data_types.html

Features:
  - Simple, unbranded, professional layout
  - Syntax-highlighted Java code blocks
  - Image support with fallback placeholder
  - Download as PDF button (browser print dialog)

Usage:
    python generate_session_html.py --notes notes_day_01.json --course-id 162 --session-day 1
"""

import sys
import json
import re
import argparse
from pathlib import Path


def slugify(text: str) -> str:
    """Convert text to snake_case slug."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', '_', text.strip())
    return text[:40]


def html_escape(text: str) -> str:
    """Escape HTML special characters."""
    return (text.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))


def generate_styles() -> str:
    """Return clean, unbranded CSS for all pages."""
    return """
    <style>
        :root {
            --primary: #2c3e50;
            --accent: #3498db;
            --code-bg: #1e2430;
            --code-text: #abb2bf;
            --code-keyword: #c678dd;
            --code-string: #98c379;
            --code-comment: #5c6370;
            --code-number: #d19a66;
            --green-output: #27ae60;
            --warn-red: #e74c3c;
            --note-yellow: #f39c12;
        }

        * { box-sizing: border-box; }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.75;
            margin: 0;
            padding: 24px 16px;
            background: #f4f6f8;
            color: #2c3e50;
            font-size: 15px;
        }

        .container {
            max-width: 880px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            overflow: hidden;
        }

        /* ── Top bar with Download button ── */
        .top-bar {
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
            padding: 10px 28px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .top-bar .breadcrumb {
            font-size: 0.82em;
            color: #6c757d;
        }
        .btn-pdf {
            background: var(--accent);
            color: white;
            border: none;
            border-radius: 5px;
            padding: 7px 18px;
            font-size: 0.85em;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            text-decoration: none;
        }
        .btn-pdf:hover { background: #2980b9; }

        /* ── Page header ── */
        .page-header {
            background: var(--primary);
            color: white;
            padding: 28px 36px;
        }
        .page-header .label {
            font-size: 0.78em;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            opacity: 0.7;
            margin-bottom: 6px;
        }
        .page-header h1 {
            font-size: 1.55em;
            font-weight: 700;
            margin: 0 0 6px 0;
        }
        .page-header .subtitle {
            font-size: 0.9em;
            opacity: 0.8;
        }

        /* ── Content ── */
        .content {
            padding: 32px 36px 40px;
        }

        /* ── Learning outcomes ── */
        .outcomes-box {
            background: #eaf4fb;
            border-left: 4px solid var(--accent);
            border-radius: 4px;
            padding: 16px 20px;
            margin-bottom: 28px;
        }
        .outcomes-box h3 {
            margin: 0 0 10px 0;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            color: var(--accent);
        }
        .outcomes-box ul {
            margin: 0;
            padding: 0 0 0 18px;
        }
        .outcomes-box li {
            margin-bottom: 4px;
            font-size: 0.93em;
            color: #34495e;
        }

        /* ── Section heading ── */
        h2.section-heading {
            font-size: 1.25em;
            font-weight: 700;
            color: var(--primary);
            border-bottom: 2px solid var(--accent);
            padding-bottom: 8px;
            margin: 0 0 18px 0;
        }

        p { margin: 0 0 14px 0; }

        ol, ul {
            padding-left: 22px;
            margin: 0 0 14px 0;
        }
        li { margin-bottom: 5px; }

        /* ── Code blocks ── */
        .code-wrap {
            background: var(--code-bg);
            border-radius: 6px;
            margin: 14px 0;
            overflow: hidden;
        }
        .code-header {
            background: rgba(255,255,255,0.07);
            padding: 5px 14px;
            font-size: 0.75em;
            color: #888;
            font-family: monospace;
            border-bottom: 1px solid rgba(255,255,255,0.06);
            display: flex;
            justify-content: space-between;
        }
        pre {
            margin: 0;
            padding: 16px 18px;
            color: var(--code-text);
            font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
            font-size: 0.88em;
            line-height: 1.65;
            white-space: pre-wrap;
            word-break: break-word;
            overflow-x: auto;
        }

        /* Syntax highlighting */
        .kw  { color: var(--code-keyword); font-weight: 600; }
        .str { color: var(--code-string); }
        .cmt { color: var(--code-comment); font-style: italic; }
        .num { color: var(--code-number); }

        /* ── Output block ── */
        .output-wrap {
            background: #f8fff8;
            border: 1px solid #c3e6cb;
            border-left: 4px solid var(--green-output);
            border-radius: 4px;
            padding: 12px 16px;
            margin: 4px 0 16px;
        }
        .output-wrap .output-label {
            font-size: 0.76em;
            font-weight: 700;
            color: var(--green-output);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }
        .output-wrap pre {
            color: #155724;
            background: none;
            padding: 0;
            font-size: 0.87em;
        }

        /* ── Example box ── */
        .example-box {
            border: 1px solid #e9ecef;
            border-radius: 6px;
            margin: 18px 0;
            overflow: hidden;
        }
        .example-box .ex-title {
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 0.9em;
            color: #495057;
        }
        .example-box .ex-desc {
            padding: 10px 16px 0;
            font-size: 0.88em;
            color: #6c757d;
            font-style: italic;
        }
        .example-box .code-wrap { border-radius: 0; margin: 0; }
        .example-box .output-wrap { margin: 0 16px 14px; }

        /* ── Key points ── */
        .key-points {
            background: #fffbf0;
            border: 1px solid #ffc107;
            border-left: 4px solid #ffc107;
            border-radius: 4px;
            padding: 14px 18px;
            margin: 16px 0;
        }
        .key-points .kp-title {
            font-weight: 700;
            font-size: 0.88em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #856404;
            margin-bottom: 8px;
        }
        .key-points ul { margin: 0; }
        .key-points li { color: #5d4a00; font-size: 0.93em; }

        /* ── Common mistakes ── */
        .mistakes-box {
            background: #fff5f5;
            border: 1px solid #f5c6cb;
            border-left: 4px solid var(--warn-red);
            border-radius: 4px;
            padding: 14px 18px;
            margin: 16px 0;
        }
        .mistakes-box .mb-title {
            font-weight: 700;
            font-size: 0.88em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--warn-red);
            margin-bottom: 8px;
        }
        .mistakes-box ul { margin: 0; }
        .mistakes-box li { color: #7b1a1a; font-size: 0.93em; }

        /* ── Images ── */
        .img-wrap { text-align: center; margin: 18px 0; }
        .img-wrap img {
            max-width: 100%;
            border-radius: 6px;
            border: 1px solid #e9ecef;
        }
        .img-placeholder {
            background: #f0f4ff;
            border: 2px dashed #adb5bd;
            border-radius: 6px;
            padding: 24px;
            color: #6c757d;
            font-size: 0.88em;
        }
        .img-caption {
            font-size: 0.82em;
            color: #6c757d;
            font-style: italic;
            margin-top: 6px;
        }

        /* ── Assignment box ── */
        .assignment-box {
            background: #f0fff4;
            border: 1px solid #c3e6cb;
            border-left: 4px solid #28a745;
            border-radius: 4px;
            padding: 18px 22px;
            margin-top: 32px;
        }
        .assignment-box .asgn-title {
            font-weight: 700;
            color: #1e7e34;
            margin-bottom: 10px;
        }
        .assignment-box .hint-list li { color: #155724; font-size: 0.92em; }

        /* ── Footer ── */
        .page-footer {
            border-top: 1px solid #e9ecef;
            padding: 14px 36px;
            font-size: 0.8em;
            color: #adb5bd;
            text-align: center;
        }

        /* ── Print / PDF ── */
        @media print {
            body { background: white; padding: 0; }
            .container { box-shadow: none; border-radius: 0; }
            .top-bar { display: none; }
        }
    </style>

    <script>
        function downloadPDF() {
            window.print();
        }
    </script>
"""


def simple_java_highlight(code: str) -> str:
    """Apply basic Java syntax highlighting."""
    keywords = [
        'public', 'private', 'protected', 'static', 'final', 'class', 'interface',
        'extends', 'implements', 'new', 'return', 'void', 'int', 'long', 'double',
        'float', 'boolean', 'char', 'byte', 'short', 'true', 'false', 'null',
        'if', 'else', 'for', 'while', 'do', 'switch', 'case', 'break', 'continue',
        'default', 'try', 'catch', 'finally', 'throw', 'throws', 'import', 'package',
        'this', 'super', 'instanceof', 'String', 'System', 'out', 'println'
    ]

    lines = []
    for line in code.split('\n'):
        escaped = html_escape(line)

        if '//' in escaped:
            idx = escaped.find('//')
            code_part = escaped[:idx]
            comment_part = escaped[idx:]
            for kw in keywords:
                code_part = re.sub(r'\b' + re.escape(kw) + r'\b',
                                   f'<span class="kw">{kw}</span>', code_part)
            code_part = re.sub(r'&quot;([^&quot;]*)&quot;',
                               r'<span class="str">&quot;\1&quot;</span>', code_part)
            code_part = re.sub(r'\b(\d[\d_]*[LlfFdD]?)\b',
                               r'<span class="num">\1</span>', code_part)
            escaped = code_part + f'<span class="cmt">{comment_part}</span>'
        else:
            for kw in keywords:
                escaped = re.sub(r'\b' + re.escape(kw) + r'\b',
                                 f'<span class="kw">{kw}</span>', escaped)
            escaped = re.sub(r'&quot;([^&quot;]*)&quot;',
                             r'<span class="str">&quot;\1&quot;</span>', escaped)
            escaped = re.sub(r'\b(\d[\d_]*[LlfFdD]?)\b',
                             r'<span class="num">\1</span>', escaped)

        lines.append(escaped)
    return '\n'.join(lines)


def build_content_paragraphs(content: str) -> str:
    """Convert content text to HTML paragraphs/lists."""
    html = ''
    for para in content.split('\n\n'):
        para = para.strip()
        if not para:
            continue
        lines = para.split('\n')
        first = lines[0].strip()
        # Numbered list
        if re.match(r'^\d+\.', first):
            html += '<ol>\n'
            for line in lines:
                clean = re.sub(r'^\d+\.\s*', '', line.strip())
                if clean:
                    html += f'  <li>{html_escape(clean)}</li>\n'
            html += '</ol>\n'
        # Bullet list
        elif first.startswith(('•', '-', '*')) and len(lines) > 1:
            html += '<ul>\n'
            for line in lines:
                clean = line.strip().lstrip('•-* ')
                if clean:
                    html += f'  <li>{html_escape(clean)}</li>\n'
            html += '</ul>\n'
        else:
            html += f'<p>{html_escape(para)}</p>\n'
    return html


def generate_topic_html(session_day: int, section: dict, meta: dict,
                        overview: dict, assignment: dict) -> str:
    """Generate a complete HTML page for a single topic/section."""
    section_title  = section.get("title", "")
    section_id     = section.get("section_id", "S1")
    section_num    = section_id.replace("S", "")
    session_title  = meta.get("session_title", f"Day {session_day}")
    phase          = meta.get("phase", "")
    date_str       = meta.get("date", "")
    num_sections   = meta.get("total_sections", "")

    breadcrumb_parts = [f"Day {session_day}", session_title]
    if phase:
        breadcrumb_parts.insert(1, phase)
    breadcrumb = " › ".join(breadcrumb_parts)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Day {session_day} – Topic {section_num}: {html_escape(section_title)}</title>
    {generate_styles()}
</head>
<body>
<div class="container">

    <!-- top bar -->
    <div class="top-bar">
        <div class="breadcrumb">{html_escape(breadcrumb)} › Topic {section_num}</div>
        <button class="btn-pdf" onclick="downloadPDF()">⬇ Download PDF</button>
    </div>

    <!-- page header -->
    <div class="page-header">
        <div class="label">Java Full Stack Training &nbsp;·&nbsp; Day {session_day}{(' &nbsp;·&nbsp; ' + html_escape(date_str)) if date_str else ''}</div>
        <h1>Topic {section_num}: {html_escape(section_title)}</h1>
        <div class="subtitle">{html_escape(session_title)}</div>
    </div>

    <!-- content -->
    <div class="content">
"""

    # Learning outcomes
    outcomes = overview.get("learning_outcomes", [])
    if outcomes:
        html += '    <div class="outcomes-box">\n'
        html += '        <h3>Session Learning Outcomes</h3>\n'
        html += '        <ul>\n'
        for o in outcomes:
            html += f'            <li>{html_escape(o)}</li>\n'
        html += '        </ul>\n    </div>\n\n'

    # Section heading
    html += f'    <h2 class="section-heading">{html_escape(section_title)}</h2>\n'

    # Images
    for img in section.get("images", []):
        url = img.get("url", "")
        caption = img.get("caption", "")
        alt = img.get("alt", caption)
        placeholder = img.get("placeholder", False)

        html += '    <div class="img-wrap">\n'
        if url and not placeholder:
            html += f'        <img src="{url}" alt="{html_escape(alt)}" loading="lazy">\n'
        elif url:
            html += f'''        <img src="{url}" alt="{html_escape(alt)}" loading="lazy"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
        <div class="img-placeholder" style="display:none">
            <div>&#128443; {html_escape(caption or alt)}</div>
        </div>\n'''
        else:
            html += f'        <div class="img-placeholder">&#128443; {html_escape(caption or alt)}</div>\n'

        if caption:
            html += f'        <div class="img-caption">{html_escape(caption)}</div>\n'
        html += '    </div>\n'

    # Main content
    content = section.get("content", "")
    if content:
        html += build_content_paragraphs(content)

    # Syntax box
    syntax = section.get("syntax_box")
    if syntax:
        code = syntax.get("code", "")
        desc = syntax.get("description", "")
        highlighted = simple_java_highlight(code)
        html += '    <div class="code-wrap">\n'
        html += f'        <div class="code-header"><span>Syntax</span><span>Java</span></div>\n'
        if desc:
            html += f'        <div style="padding:8px 18px 0; color:#aaa; font-size:0.82em; font-family:monospace;">{html_escape(desc)}</div>\n'
        html += f'        <pre>{highlighted}</pre>\n    </div>\n'

    # Examples
    for ex in section.get("examples", []):
        title_ex = ex.get("title", "")
        desc_ex  = ex.get("description", "")
        code_ex  = ex.get("code", "")
        output   = ex.get("output", "")
        highlighted = simple_java_highlight(code_ex)

        html += '    <div class="example-box">\n'
        html += f'        <div class="ex-title">{html_escape(title_ex)}</div>\n'
        if desc_ex:
            html += f'        <div class="ex-desc">{html_escape(desc_ex)}</div>\n'
        html += '        <div class="code-wrap">\n'
        html += '            <div class="code-header"><span>Java</span></div>\n'
        html += f'            <pre>{highlighted}</pre>\n        </div>\n'
        if output:
            html += '        <div class="output-wrap">\n'
            html += '            <div class="output-label">Expected Output</div>\n'
            html += f'            <pre>{html_escape(output)}</pre>\n        </div>\n'
        html += '    </div>\n'

    # Key points
    key_points = section.get("key_points", [])
    if key_points:
        html += '    <div class="key-points">\n'
        html += '        <div class="kp-title">Key Points to Remember</div>\n'
        html += '        <ul>\n'
        for pt in key_points:
            html += f'            <li>{html_escape(pt)}</li>\n'
        html += '        </ul>\n    </div>\n'

    # Common mistakes
    mistakes = section.get("common_mistakes", [])
    if mistakes:
        html += '    <div class="mistakes-box">\n'
        html += '        <div class="mb-title">Common Mistakes to Avoid</div>\n'
        html += '        <ul>\n'
        for m in mistakes:
            html += f'            <li>{html_escape(m)}</li>\n'
        html += '        </ul>\n    </div>\n'

    # Assignment (last section only)
    if assignment:
        html += '    <div class="assignment-box">\n'
        html += f'        <div class="asgn-title">Home Assignment: {html_escape(assignment.get("title", ""))}</div>\n'
        desc_a = assignment.get("description", "")
        if desc_a:
            html += f'        <p>{html_escape(desc_a)}</p>\n'
        hints = assignment.get("hints", [])
        if hints:
            html += '        <ul class="hint-list">\n'
            for h in hints:
                html += f'            <li>{html_escape(h)}</li>\n'
            html += '        </ul>\n'
        sub = assignment.get("submission", "")
        if sub:
            html += f'        <p style="margin-top:10px; font-size:0.9em; color:#155724;"><strong>Submission:</strong> {html_escape(sub)}</p>\n'
        html += '    </div>\n'

    # Close
    html += """    </div><!-- /content -->

    <div class="page-footer">
        Java Full Stack Training &nbsp;·&nbsp; Day """ + str(session_day) + """ &nbsp;·&nbsp; Topic """ + section_num + """: """ + html_escape(section_title) + """
    </div>

</div><!-- /container -->
</body>
</html>"""

    return html


def generate_all_topics(notes_json_path: Path, output_dir: Path, session_day: int):
    """Generate one HTML file per topic section from a notes JSON."""
    print(f"Loading: {notes_json_path}")
    with open(notes_json_path, encoding='utf-8') as f:
        data = json.load(f)

    meta       = data.get("meta", {})
    overview   = data.get("overview", {})
    sections   = data.get("sections", [])
    assignment = data.get("home_assignment", {})

    # Embed total_sections in meta for convenience
    meta["total_sections"] = len(sections)

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files = []

    for i, section in enumerate(sections):
        title    = section.get("title", f"Topic {i+1}")
        slug     = slugify(title)
        filename = f"session{session_day}_{slug}.html"
        out_path = output_dir / filename

        # Only append assignment to the last section
        sec_assignment = assignment if i == len(sections) - 1 else {}

        html_content = generate_topic_html(
            session_day, section, meta, overview, sec_assignment
        )

        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        size_kb = out_path.stat().st_size / 1024
        print(f"  OK  {filename}  ({size_kb:.1f} KB)")
        generated_files.append(out_path)

    return generated_files


def main():
    parser = argparse.ArgumentParser(description="Generate HTML topic files from Notes JSON")
    parser.add_argument("--notes",       required=True,      help="Path to notes JSON file")
    parser.add_argument("--course-id",   required=True, type=int, help="Course ID (e.g. 162)")
    parser.add_argument("--session-day", required=True, type=int, help="Session day number (e.g. 1)")
    parser.add_argument("--output-dir",  default=None,       help="Override output directory")
    args = parser.parse_args()

    notes_path = Path(args.notes)
    if not notes_path.exists():
        print(f"Error: Notes file not found: {notes_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir) if args.output_dir else \
                 Path(f"/opt/robodynamics/session_materials/{args.course_id}")

    print(f"\nGenerating HTML topic files...")
    print(f"  Input : {notes_path}")
    print(f"  Output: {output_dir}")
    print(f"  Day   : {args.session_day}\n")

    files = generate_all_topics(notes_path, output_dir, args.session_day)

    print(f"\nDone — {len(files)} files created in {output_dir}")
    for f in files:
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
