"""Apply paragraph edits to a manuscript and write a revision log.

usage: python apply.py paper.(docx|md|txt|tex) edits.json [-o OUT] [--author NAME] [--inplace] [--log LOG]

.docx  -> <name>_revised.docx with real Word tracked changes (w:ins / w:del)
text   -> <name>_revised.<ext> (clean)  +  <name>_revised.review.md (CriticMarkup redline)
          --inplace overwrites the original instead (a .bak copy is kept)
both   -> <name>_revised_修订说明.md (one entry per edit: type, reason, before, after, redline)

edits.json:
{"author": "Claude",
 "edits": [{"para": 12,                         # idx from extract.py
            "old": "<exact current text>",      # recommended safety check
            "new": "<full new text>",           # or:
            "replacements": [{"find": "...", "replace": "..."}],   # each find must be unique
            "type": "D2", "reason": "...",
            "allow_drop": false}]}              # text formats: allow dropping a citation with its sentence
Exit code 1 if any edit failed (successful edits are still written).
"""
import argparse
import json
import os
import shutil
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textdiff import EditError, apply_replacements, criticmarkup  # noqa: E402

TEXT_EXT = {".md", ".markdown", ".txt", ".tex", ".rmd", ".qmd"}


def resolve_new(edit, old):
    if edit.get("old") is not None and edit["old"] != old:
        raise EditError("old 与当前段落文本不一致（请从 paragraphs.json 原样复制）")
    new = edit["new"] if "new" in edit else apply_replacements(old, edit.get("replacements", []))
    if new == old:
        raise EditError("新旧文本相同")
    return new


def run_docx(path, edits, author, out):
    import zipfile
    from docx_core import Para, RevisionWriter, apply_edit, iter_paragraphs, read_document, write_document
    root = read_document(path)
    paras = dict(enumerate(iter_paragraphs(root)))
    rw = RevisionWriter(root, author)
    done, failed = [], []
    for e in edits:
        try:
            if e["para"] not in paras:
                raise EditError("段落编号不存在")
            para = Para(paras[e["para"]])
            if not para.editable:
                raise EditError("段落被锁定：" + "; ".join(sorted(set(para.problems))))
            old = para.display
            new = resolve_new(e, old)
            apply_edit(para, new, rw)
            done.append((e, para.expand(old), para.expand(new)))
        except EditError as err:
            failed.append((e, str(err)))
    out = out or os.path.splitext(path)[0] + "_revised.docx"
    write_document(path, out, root)
    with zipfile.ZipFile(out) as z:
        assert z.testzip() is None
    read_document(out)
    return done, failed, [out]


def run_text(path, edits, out, inplace):
    from text_core import TextDoc
    doc = TextDoc(path)
    with open(path, "rb") as f:
        original = f.read()
    if (b"\xef\xbb\xbf" if doc.bom else b"") + doc.render({}).encode("utf-8") != original:
        raise SystemExit("内部错误：文件无法无损往返，停止以免破坏原文")
    clean, review, done, failed = {}, {}, [], []
    for e in edits:
        try:
            if not 0 <= e["para"] < len(doc.blocks):
                raise EditError("段落编号不存在")
            b = doc.blocks[e["para"]]
            if not b.editable:
                raise EditError(f"{b.kind} 块被锁定")
            new = resolve_new(e, b.text)
            doc.check_protected(b.text, new, e)
            clean[e["para"]] = new
            review[e["para"]] = criticmarkup(b.text, new, f"{e.get('type', '')}: {e.get('reason', '')}")
            done.append((e, b.text, new))
        except EditError as err:
            failed.append((e, str(err)))
    base, ext = os.path.splitext(path)
    if inplace:
        shutil.copy2(path, path + ".bak")
        out = path
    else:
        out = out or base + "_revised" + ext
    doc.write(out, doc.render(clean))
    review_path = os.path.splitext(out)[0] + ("_revised" if inplace else "") + ".review.md"
    doc.write(review_path, doc.render(review))
    outs = [out, review_path] + ([path + ".bak"] if inplace else [])
    return done, failed, outs


def write_log(log_path, src, outs, author, done, failed):
    types = Counter(e.get("type", "?") for e, _, _ in done)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"# 修订说明\n\n- 源文件：{os.path.basename(src)}\n"
                f"- 输出：{', '.join(os.path.basename(o) for o in outs)}\n- 修订者：{author}\n"
                f"- 已修改段落：{len(done)}；未能应用：{len(failed)}\n"
                f"- 类型统计：{', '.join(f'{k}×{v}' for k, v in sorted(types.items()))}\n\n")
        for e, old, new in done:
            f.write(f"## P{e['para']} · {e.get('type', '')}\n\n{e.get('reason', '')}\n\n"
                    f"**修订痕迹**\n\n> {criticmarkup(old, new)}\n\n"
                    f"**修订后**\n\n> {new if new else '（整段删除）'}\n\n")
        if failed:
            f.write("## 未能应用的修改\n\n")
            for e, err in failed:
                f.write(f"- P{e['para']}: {err}\n")


def main():
    for s_ in (sys.stdout, sys.stderr):
        try:
            s_.reconfigure(encoding="utf-8")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("edits")
    ap.add_argument("-o", "--out")
    ap.add_argument("--author")
    ap.add_argument("--inplace", action="store_true", help="text formats only")
    ap.add_argument("--log")
    args = ap.parse_args()

    with open(args.edits, encoding="utf-8") as f:
        spec = json.load(f)
    edits = spec["edits"] if isinstance(spec, dict) else spec
    author = args.author or (spec.get("author") if isinstance(spec, dict) else None) or "Claude"
    dup = [k for k, v in Counter(e["para"] for e in edits).items() if v > 1]
    if dup:
        sys.exit(f"同一段落出现多条 edit，请合并：{dup}")
    edits = sorted(edits, key=lambda e: e["para"])

    ext = os.path.splitext(args.path)[1].lower()
    if ext == ".docx":
        done, failed, outs = run_docx(args.path, edits, author, args.out)
    elif ext in TEXT_EXT:
        done, failed, outs = run_text(args.path, edits, args.out, args.inplace)
    else:
        sys.exit(f"不支持的格式 {ext}")

    base = os.path.splitext(args.path)[0]
    log_path = args.log or base + "_revised_修订说明.md"
    write_log(log_path, args.path, outs, author, done, failed)
    print(f"applied {len(done)} edits, failed {len(failed)}")
    for o in outs + [log_path]:
        print(f"wrote {o}")
    for e, err in failed:
        print(f"FAILED P{e['para']}: {err}", file=sys.stderr)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
