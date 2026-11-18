"""Dump a manuscript into numbered paragraphs for reading and editing.

usage: python extract.py paper.(docx|md|markdown|txt|tex) [-o out_prefix]
writes <prefix>.paragraphs.json  (idx, style/kind, text, editable, markers)
       <prefix>.read.md          (reading view: [P<idx>] blocks)
Default prefix: <system temp>/revise-defensive/<file name>, so nothing lands next to the paper.
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TEXT_EXT = {".md", ".markdown", ".txt", ".tex", ".rmd", ".qmd"}


def rows_docx(path):
    from docx_core import Para, iter_paragraphs, plain_text, read_document, style_of
    root = read_document(path)
    for idx, p in enumerate(iter_paragraphs(root)):
        para = Para(p)
        text = para.display if para.editable else plain_text([p])
        if not text.strip():
            continue
        row = {"idx": idx, "style": style_of(p), "text": text, "editable": para.editable}
        if para.opaques:
            row["markers"] = para.legend()
        if para.problems:
            row["problems"] = sorted(set(para.problems))
        yield row


def rows_text(path):
    from text_core import TextDoc
    doc = TextDoc(path)
    for idx, b in enumerate(doc.blocks):
        row = {"idx": idx, "style": b.kind, "text": b.text, "editable": b.editable,
               "lines": f"{b.start + 1}-{b.end}"}
        if not b.editable:
            row["problems"] = [f"{b.kind} 块不修改"]
        yield row


def main():
    for s_ in (sys.stdout, sys.stderr):
        try:
            s_.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("-o", "--out", help="output prefix")
    args = ap.parse_args()

    ext = os.path.splitext(args.path)[1].lower()
    if ext == ".docx":
        rows = list(rows_docx(args.path))
    elif ext in TEXT_EXT:
        rows = list(rows_text(args.path))
    else:
        sys.exit(f"不支持的格式 {ext}：请提供 .docx / .md / .txt / .tex（.doc 请先另存为 .docx）")

    if args.out:
        prefix = args.out
    else:
        d = os.path.join(tempfile.gettempdir(), "revise-defensive")
        os.makedirs(d, exist_ok=True)
        prefix = os.path.join(d, os.path.basename(args.path))

    lines = []
    for r in rows:
        flag = "" if r["editable"] else "  [LOCKED: " + "; ".join(r["problems"]) + "]"
        style = f" ({r['style']})" if r["style"] else ""
        text = r["text"]
        if not r["editable"] and text.count("\n") > 3:
            text = "\n".join(text.split("\n")[:3]) + "\n…"
        lines.append(f"[P{r['idx']}]{style}{flag}\n{text}\n")
        if r.get("markers"):
            legend = "; ".join(f"⟦{k}⟧={v['type'].split(':')[0]}:{v['text'][:40]!r}" for k, v in r["markers"].items())
            lines.append(f"    markers: {legend}\n")

    with open(prefix + ".paragraphs.json", "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    with open(prefix + ".read.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    locked = sum(not r["editable"] for r in rows)
    print(f"format: {ext}; paragraphs: {len(rows)}; locked: {locked}")
    print(f"wrote {prefix}.paragraphs.json\nwrote {prefix}.read.md")


if __name__ == "__main__":
    main()
