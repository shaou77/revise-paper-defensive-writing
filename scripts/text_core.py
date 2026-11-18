"""Markdown / plain text / LaTeX backend.

The file is split into blocks (paragraphs separated by blank lines). Front matter, fenced
code, $$ math $$, HTML comments and LaTeX float/equation environments are locked.
Edits replace whole blocks; everything else in the file is preserved byte-for-byte.
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textdiff import EditError  # noqa: E402

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
TEX_ENV_RE = re.compile(r"^\s*\\begin\{(equation|align|gather|multline|eqnarray|figure|table|tabular|"
                        r"tikzpicture|lstlisting|verbatim|minted|algorithm)\*?\}")

# inline things a prose edit must never silently drop or invent
PROTECT_RE = re.compile(
    r"\[@[^\]]+\]"                              # pandoc citation [@key; @key2]
    r"|\[\^[^\]]+\]"                            # footnote ref [^1]
    r"|\[\d+(?:\s*[-–,]\s*\d+)*\]"              # numeric citation [12], [3-5]
    r"|\^\d+(?:[-–,]\d+)*\^"                    # superscript citation ^12^
    r"|`[^`\n]+`"                               # inline code
    r"|\$[^$\n]+\$"                             # inline math
    r"|\]\([^)\s]+(?:\s+\"[^\"]*\")?\)"         # link / image target
    r"|\\(?:cite[a-z]*|ref|eqref|autoref|cref|Cref|label|footnote)\*?(?:\[[^\]]*\])*\{[^}]+\}"  # LaTeX
)


class Block:
    def __init__(self, start, end, kind, text):
        self.start, self.end, self.kind, self.text = start, end, kind, text

    @property
    def editable(self):
        return self.kind in ("text", "heading", "list", "quote", "table")


class TextDoc:
    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        self.bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        self.nl = "\r\n" if "\r\n" in text else "\n"
        self.trailing_nl = text.endswith(("\n", "\r\n"))
        self.lines = text.replace("\r\n", "\n").split("\n")
        if self.trailing_nl:
            self.lines.pop()
        self.blocks = self._parse()

    def _find(self, i, pred):
        for j in range(i, len(self.lines)):
            if pred(self.lines[j]):
                return j
        return len(self.lines) - 1

    def _parse(self):
        L, blocks, i, n = self.lines, [], 0, len(self.lines)

        def add(s, e, kind):
            blocks.append(Block(s, e, kind, "\n".join(L[s:e])))

        if n and L[0].strip() in ("---", "+++"):
            j = self._find(1, lambda x: x.strip() == L[0].strip())
            add(0, j + 1, "frontmatter")
            i = j + 1
        while i < n:
            line = L[i]
            s = line.strip()
            if not s:
                i += 1
                continue
            m = FENCE_RE.match(line)
            if m:
                fence = m.group(1)[0] * 3
                j = self._find(i + 1, lambda x: x.strip().startswith(fence))
                add(i, j + 1, "code"); i = j + 1; continue
            if s.startswith("$$") or s.startswith("\\["):
                close = "$$" if s.startswith("$$") else "\\]"
                j = i if (len(s) > 2 and s.endswith(close)) else self._find(i + 1, lambda x: close in x)
                add(i, j + 1, "math"); i = j + 1; continue
            if s.startswith("<!--"):
                j = self._find(i, lambda x: "-->" in x)
                add(i, j + 1, "comment"); i = j + 1; continue
            m = TEX_ENV_RE.match(line)
            if m:
                env = m.group(1)
                j = self._find(i, lambda x: re.search(r"\\end\{" + env + r"\*?\}", x))
                add(i, j + 1, "latex-env"); i = j + 1; continue
            if s.startswith("%"):
                j = i
                while j + 1 < n and L[j + 1].strip().startswith("%"):
                    j += 1
                add(i, j + 1, "comment"); i = j + 1; continue
            j = i
            while j + 1 < n and L[j + 1].strip() and not FENCE_RE.match(L[j + 1]) \
                    and not L[j + 1].strip().startswith(("$$", "<!--")) and not TEX_ENV_RE.match(L[j + 1]):
                j += 1
            seg = L[i:j + 1]
            if s.startswith("#"):
                kind = "heading"
            elif all(x.strip().startswith("|") for x in seg):
                kind = "table"
            elif re.match(r"\s*([-*+]|\d+[.)])\s", line):
                kind = "list"
            elif s.startswith(">"):
                kind = "quote"
            else:
                kind = "text"
            add(i, j + 1, kind)
            i = j + 1
        return blocks

    # ------------------------------------------------------------------ edits
    def check_protected(self, old, new, edit):
        lost = Counter(PROTECT_RE.findall(old)) - Counter(PROTECT_RE.findall(new))
        added = Counter(PROTECT_RE.findall(new)) - Counter(PROTECT_RE.findall(old))
        if lost and not edit.get("allow_drop"):
            raise EditError(f"删除了受保护元素 {sorted(lost)}；若确属随句删除，在该 edit 中加 \"allow_drop\": true")
        if added and not edit.get("allow_add"):
            raise EditError(f"新增了引用/公式/链接 {sorted(added)}；防御性修订不应新增证据")

    def render(self, replaced):
        """replaced: {block_index: new_text}"""
        out, prev = [], 0
        for bi in sorted(replaced, key=lambda k: self.blocks[k].start):
            b = self.blocks[bi]
            out += self.lines[prev:b.start]
            new = replaced[bi]
            if new != "":
                out += new.split("\n")
            elif out and b.end < len(self.lines) and not self.lines[b.end].strip() and (not out[-1].strip()):
                prev = b.end + 1            # drop the now-double blank line
                continue
            prev = b.end
        out += self.lines[prev:]
        text = self.nl.join(out) + (self.nl if self.trailing_nl else "")
        return text

    def write(self, path, text):
        with open(path, "wb") as f:
            f.write((b"\xef\xbb\xbf" if self.bom else b"") + text.encode("utf-8"))
