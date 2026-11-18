"""Format-independent word-level diff used by both the .docx and the text backends."""
import difflib
import re

TOKEN_RE = re.compile(
    r"⟦\d+⟧"                                                         # docx opaque marker
    r"|[A-Za-z0-9À-ɏ]+(?:['’\-][A-Za-z0-9À-ɏ]+)*"  # latin word / number
    r"|\s+"                                                          # whitespace
    r"|.", re.S)                                                     # single char (CJK, punctuation)


class EditError(Exception):
    pass


def tokenize(s):
    """[(token, start, end), ...]"""
    return [(m.group(0), m.start(), m.end()) for m in TOKEN_RE.finditer(s)]


def diff_ops(a, b):
    """Opcodes over token lists a, b; whitespace-only 'equal' gaps between two changes are
    folded into one replace so redlines read as phrases, not word confetti."""
    ops = difflib.SequenceMatcher(None, [t[0] for t in a], [t[0] for t in b], autojunk=False).get_opcodes()
    merged = []
    for op in ops:
        tag = op[0]
        if tag != "equal" and len(merged) >= 2 and merged[-1][0] == "equal" and merged[-2][0] != "equal" \
                and all(t[0].isspace() for t in a[merged[-1][1]:merged[-1][2]]):
            merged.pop()
            p = merged.pop()
            merged.append(("replace", p[1], op[2], p[3], op[4]))
        elif tag != "equal" and merged and merged[-1][0] != "equal":
            p = merged.pop()
            merged.append(("replace", p[1], op[2], p[3], op[4]))
        else:
            merged.append(op)
    return merged


def apply_replacements(text, replacements):
    for r in replacements:
        n = text.count(r["find"])
        if n != 1:
            raise EditError(f"find 片段出现 {n} 次（需恰好 1 次）：{r['find'][:60]!r}")
        text = text.replace(r["find"], r["replace"])
    return text


def criticmarkup(old, new, comment=None):
    """CriticMarkup review string: {--del--} {++ins++} {~~old~>new~~} {>>comment<<}."""
    a, b = tokenize(old), tokenize(new)
    out = []
    for tag, i1, i2, j1, j2 in diff_ops(a, b):
        x = "".join(t[0] for t in a[i1:i2])
        y = "".join(t[0] for t in b[j1:j2])
        if tag == "equal":
            out.append(x)
        elif tag == "delete":
            out.append("{--" + x + "--}")
        elif tag == "insert":
            out.append("{++" + y + "++}")
        else:
            out.append("{~~" + x + "~>" + y + "~~}")
    if comment:
        out.append("{>>" + comment.replace("<<", "‹‹") + "<<}")
    return "".join(out)
