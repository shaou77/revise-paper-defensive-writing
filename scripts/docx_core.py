"""Shared helpers: parse Word paragraphs into atoms, rebuild them with tracked changes.

A paragraph is flattened into a "display text" the model can edit:
  - ordinary characters appear as-is (tab -> \t, line break -> \n)
  - things that must not be split (citation fields, hyperlinks, footnote refs,
    equations, images ...) appear as an opaque marker  ⟦n⟧
  - zero-width things (bookmarks, comment ranges) are invisible and kept in place.
"""
import copy
import os
import re
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone

from lxml import etree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textdiff import EditError, diff_ops, tokenize  # noqa: E402,F401

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
NS = {"w": W}


def w(tag):
    return f"{{{W}}}{tag}"


MARK_RE = re.compile(r"⟦(\d+)⟧")
ZERO_WIDTH = {w(t) for t in (
    "bookmarkStart", "bookmarkEnd", "commentRangeStart", "commentRangeEnd",
    "permStart", "permEnd", "customXmlInsRangeStart", "customXmlInsRangeEnd",
    "customXmlDelRangeStart", "customXmlDelRangeEnd")}
DROP = {w("proofErr"), w("lastRenderedPageBreak")}
REVISIONS = {w(t) for t in ("ins", "del", "moveFrom", "moveTo", "moveFromRangeStart",
                            "moveFromRangeEnd", "moveToRangeStart", "moveToRangeEnd")}


# ---------------------------------------------------------------- io
def read_document(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml")
    return etree.fromstring(xml)


def write_document(src, dst, root):
    data = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            buf = data if item.filename == "word/document.xml" else zin.read(item.filename)
            zout.writestr(item, buf)


def iter_paragraphs(root):
    """Body paragraphs (incl. tables) in document order, skipping text boxes."""
    body = root.find(w("body"))
    for p in body.iter(w("p")):
        if any(a.tag == w("txbxContent") for a in p.iterancestors()):
            continue
        yield p


def style_of(p):
    ps = p.find(f"{w('pPr')}/{w('pStyle')}")
    return ps.get(w("val")) if ps is not None else ""


# ---------------------------------------------------------------- text views
def plain_text(elements, view="accept"):
    """Visible text of elements. view='accept' (final) or 'reject' (original)."""
    out = []
    for el in elements:
        for node in el.iter():
            tag = node.tag
            if not isinstance(tag, str):
                continue
            anc = {a.tag for a in node.iterancestors()}
            if view == "accept" and w("del") in anc:
                continue
            if view == "reject" and w("ins") in anc:
                continue
            if tag == w("t") or (tag == w("delText") and view == "reject"):
                out.append(node.text or "")
            elif tag == w("tab") and node.getparent() is not None and node.getparent().tag == w("r"):
                out.append("\t")
            elif tag in (w("br"), w("cr")):
                out.append("\n")
    return "".join(out)


# ---------------------------------------------------------------- parsing
class Para:
    def __init__(self, p):
        self.p = p
        self.ppr = None
        self.units = []                 # list of dict(kind=char|opaque, ...)
        self.zw_before = defaultdict(list)
        self.problems = []
        self.opaques = {}               # id -> atom
        self._parse()

    # -- helpers
    def _opaque(self, els, label, deletable):
        oid = len(self.opaques) + 1
        atom = {"kind": "opaque", "id": oid, "els": els, "label": label,
                "deletable": deletable, "text": plain_text(els)}
        self.opaques[oid] = atom
        self.units.append(atom)

    def _run(self, r):
        rpr = r.find(w("rPr"))
        for c in r:
            tag = c.tag
            if not isinstance(tag, str) or tag == w("rPr") or tag in DROP:
                continue
            if tag == w("t"):
                for ch in c.text or "":
                    if ch in "⟦⟧":
                        self.problems.append("正文含 ⟦ ⟧ 字符")
                    self.units.append({"kind": "char", "ch": ch, "rpr": rpr, "el": None})
            elif tag == w("tab"):
                self.units.append({"kind": "char", "ch": "\t", "rpr": rpr, "el": c})
            elif tag in (w("br"), w("cr")) and c.get(w("type")) in (None, "textWrapping"):
                self.units.append({"kind": "char", "ch": "\n", "rpr": rpr, "el": c})
            else:
                nr = etree.Element(w("r"))
                if rpr is not None:
                    nr.append(copy.deepcopy(rpr))
                nr.append(copy.deepcopy(c))
                name = etree.QName(tag).localname
                self._opaque([nr], name, deletable=name in ("sym", "noBreakHyphen", "softHyphen"))

    def _parse(self):
        field, depth = None, 0
        for child in self.p:
            tag = child.tag
            if not isinstance(tag, str):
                continue
            if tag == w("pPr"):
                self.ppr = child
                continue
            if field is not None:
                field.append(child)
                for fc in child.iter(w("fldChar")):
                    t = fc.get(w("fldCharType"))
                    depth += 1 if t == "begin" else -1 if t == "end" else 0
                if depth == 0:
                    self._finish_field(field)
                    field = None
                continue
            if tag == w("r") and child.find(w("fldChar")) is not None:
                fc = child.find(w("fldChar"))
                if fc.get(w("fldCharType")) == "begin":
                    field, depth = [child], 1
                    continue
            if tag in REVISIONS:
                self.problems.append("段落已有修订痕迹（请先接受/拒绝原有修订）")
                continue
            if tag in DROP:
                continue
            if tag in ZERO_WIDTH:
                self.zw_before[len(self.units)].append(child)
            elif tag == w("r"):
                self._run(child)
            else:
                name = etree.QName(tag).localname
                self._opaque([child], name, deletable=False)
        if field is not None:
            self.problems.append("域代码未闭合")
            self._finish_field(field)

    def _finish_field(self, els):
        instr = "".join(t.text or "" for e in els for t in e.iter(w("instrText"))).strip()
        kind = "citation" if re.search(r"ADDIN|CITATION|ZOTERO|EN\.CITE|Mendeley|NOTEREF|REF ", instr, re.I) else "field"
        self._opaque(els, f"{kind}: {instr[:60]}", deletable=True)

    # -- views
    def marker(self, atom):
        return f"⟦{atom['id']}⟧"

    @property
    def display(self):
        return "".join(u["ch"] if u["kind"] == "char" else self.marker(u) for u in self.units)

    def expand(self, display_text):
        return MARK_RE.sub(lambda m: self.opaques[int(m.group(1))]["text"], display_text)

    @property
    def editable(self):
        return not self.problems

    def legend(self):
        return {str(k): {"type": a["label"], "text": a["text"], "deletable": a["deletable"]}
                for k, a in self.opaques.items()}


# ---------------------------------------------------------------- diff
class RevisionWriter:
    def __init__(self, root, author):
        ids = [int(v) for v in root.xpath("//@w:id", namespaces=NS) if str(v).lstrip("-").isdigit()]
        self.next_id = max(ids + [0]) + 1000
        self.author = author
        self.date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def wrapper(self, kind):
        el = etree.Element(w(kind))
        el.set(w("id"), str(self.next_id))
        el.set(w("author"), self.author)
        el.set(w("date"), self.date)
        self.next_id += 1
        return el


def _make_run(rpr, chars, deleted):
    """chars: list of (ch, original_el)."""
    r = etree.Element(w("r"))
    if rpr is not None:
        r.append(copy.deepcopy(rpr))
    buf = []

    def flush():
        if buf:
            t = etree.SubElement(r, w("delText" if deleted else "t"))
            t.text = "".join(buf)
            t.set(XML_SPACE, "preserve")
            buf.clear()

    for ch, el in chars:
        if ch == "\t":
            flush()
            r.append(copy.deepcopy(el) if el is not None else etree.Element(w("tab")))
        elif ch == "\n":
            flush()
            r.append(copy.deepcopy(el) if el is not None else etree.Element(w("br")))
        else:
            buf.append(ch)
    flush()
    return r


def _to_deleted(el):
    el = copy.deepcopy(el)
    for node in el.iter():
        if node.tag == w("t"):
            node.tag = w("delText")
        elif node.tag == w("instrText"):
            node.tag = w("delInstrText")
    return el


def _is_script(rpr):
    if rpr is None:
        return False
    va = rpr.find(w("vertAlign"))
    return va is not None and va.get(w("val")) in ("superscript", "subscript")


def apply_edit(para, new_display, rw):
    """Rewrite para.p so that accept-all == new_display and reject-all == original."""
    old_display = para.display
    # ---- validate markers
    old_marks = [int(m) for m in MARK_RE.findall(old_display)]
    new_marks = [int(m) for m in MARK_RE.findall(new_display)]
    if len(set(new_marks)) != len(new_marks) or not set(new_marks) <= set(old_marks):
        raise EditError("新文本中的 ⟦n⟧ 标记重复或不存在")
    if new_marks != [m for m in old_marks if m in new_marks]:
        raise EditError("⟦n⟧ 标记的先后顺序被改变")
    for m in set(old_marks) - set(new_marks):
        if not para.opaques[m]["deletable"]:
            raise EditError(f"标记 ⟦{m}⟧（{para.opaques[m]['label']}）不可删除，请保留")
    if "⟦" in MARK_RE.sub("", new_display) or "⟧" in MARK_RE.sub("", new_display):
        raise EditError("新文本含残缺的 ⟦ ⟧ 标记")

    # ---- char -> unit map for old display
    char2unit = []
    for ui, u in enumerate(para.units):
        n = 1 if u["kind"] == "char" else len(para.marker(u))
        char2unit.extend([ui] * n)
    a = tokenize(old_display)
    b = tokenize(new_display)
    merged = diff_ops(a, b)

    def tok_units(i1, i2):
        if i1 == i2:
            pos = a[i1][1] if i1 < len(a) else len(old_display)
            u = char2unit[pos] if pos < len(char2unit) else len(para.units)
            return u, u
        return char2unit[a[i1][1]], char2unit[a[i2 - 1][2] - 1] + 1

    out = []

    def emit_old(u1, u2, deleted):
        group, rpr = [], None

        def flush():
            nonlocal group
            if group:
                run = _make_run(rpr, group, deleted)
                if deleted:
                    d = rw.wrapper("del")
                    d.append(run)
                    out.append(d)
                else:
                    out.append(run)
                group = []

        for ui in range(u1, u2):
            if ui in para.zw_before:
                flush()
                out.extend(para.zw_before.pop(ui))
            u = para.units[ui]
            if u["kind"] == "char":
                if group and u["rpr"] is not rpr:
                    flush()
                rpr = u["rpr"]
                group.append((u["ch"], u["el"]))
            else:
                flush()
                if deleted:
                    d = rw.wrapper("del")
                    for el in u["els"]:
                        d.append(_to_deleted(el))
                    out.append(d)
                else:
                    out.extend(u["els"])
        flush()

    def pick_rpr(u1, u2):
        cands = []
        if u2 > u1:
            cands.append(u1)
        cands += [u1 - 1, u2]
        chars = [para.units[i] for i in cands if 0 <= i < len(para.units) and para.units[i]["kind"] == "char"]
        for c in chars:
            if not _is_script(c["rpr"]):
                return c["rpr"]
        return chars[0]["rpr"] if chars else None

    for tag, i1, i2, j1, j2 in merged:
        u1, u2 = tok_units(i1, i2)
        if tag == "equal":
            emit_old(u1, u2, deleted=False)
            continue
        ins_text = "".join(t[0] for t in b[j1:j2])
        if MARK_RE.search(ins_text):
            raise EditError("标记 ⟦n⟧ 周围改动过大无法对齐：请保持标记两侧原文不动或分两步修改")
        rpr = pick_rpr(u1, u2)
        if u2 > u1:
            emit_old(u1, u2, deleted=True)
        if ins_text:
            ins = rw.wrapper("ins")
            ins.append(_make_run(rpr, [(c, None) for c in ins_text], deleted=False))
            out.append(ins)
    # trailing zero-width elements
    for ui in sorted(para.zw_before):
        out.extend(para.zw_before[ui])

    for child in list(para.p):
        if child is not para.ppr:
            para.p.remove(child)
    for el in out:
        para.p.append(el)

    # ---- self check
    exp_new, exp_old = para.expand(new_display), para.expand(old_display)
    got_new, got_old = plain_text([para.p], "accept"), plain_text([para.p], "reject")
    if got_new != exp_new or got_old != exp_old:
        raise EditError(f"自检失败：\n接受后={got_new!r}\n期望={exp_new!r}\n拒绝后={got_old!r}\n期望={exp_old!r}")
