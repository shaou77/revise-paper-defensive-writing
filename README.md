# revise-paper-defensive-writing

**Version 0.1** · A Claude Code skill that finds and revises **over-defensive writing** in academic manuscripts.

Papers polished by AI often add a hedge after every finding: "these results should be interpreted with caution", "this does not imply that all outcomes improved", "further studies are needed to confirm this". Such sentences look rigorous but often add no scientific information, and they make the authors sound unsure of their own work. This skill reads the whole manuscript and removes these sentences. It states each real limitation plainly, keeps it in one place, and preserves every result, qualifier and limitation the reader needs.

> The test: **keep a qualifier only if deleting it would materially mislead the reader.**

## What it does

| Action | Examples |
|---|---|
| Delete hedges that add no information | Denying a conclusion the paper never drew; "interpret with caution" with no stated reason; "this remains speculative" right after a claim already marked with *may* |
| Rewrite sentences that carry information but over-package it | "Owing to funding constraints we were regrettably unable to measure X, which would certainly have strengthened our conclusions" → "X was not measured." |
| Merge repeated limitations | The same limitation scattered across sections is kept once, in the most suitable place |
| **Keep** | Null results and their statistics, a single appropriate hedge on speculation, specific limitations that affect interpretation, causal-language safeguards, post hoc labels, items required by reporting guidelines |

The full rules are in [`references/rules.md`](references/rules.md) (written in Chinese, with English example phrases). They cover D1–D8 (delete), R1–R6 (rewrite) and K1–K8 (keep), plus reverse guardrails against over-correction.

## Supported formats

| Input | Output |
|---|---|
| `.docx` | A copy with **real Word tracked changes** (`w:ins`/`w:del`) that the author can accept or reject one by one. Italics, superscripts, EndNote/Zotero citation fields, hyperlinks, bookmarks and footnote references are preserved |
| `.md` `.txt` `.tex` `.qmd` `.rmd` | A clean revised copy plus a [CriticMarkup](https://github.com/CriticMarkup/CriticMarkup-toolkit) review copy (`{--deleted--}{++added++}{>>reason<<}`). With `--inplace`, the original is edited directly and a `.bak` backup is kept |
| Both | A revision log listing each edit's type, reason, redline and final text |

Safety checks:

- **Word:** after writing, the script verifies that accepting all changes gives the new text and rejecting all gives the original.
- **Text formats:** an edit that drops or adds a citation (`[@key]`, `[12]`, `\cite{}`), formula or link is rejected.
- **Untouched:** code blocks, display math, front matter and Word paragraphs that already contain tracked changes are never modified.

## Installation

```bash
git clone https://github.com/shaou77/revise-paper-defensive-writing ~/.claude/skills/revise-paper-defensive-writing
```

Requirements: Python 3. `.docx` files also need `lxml` (`pip install lxml`).

## Usage

In Claude Code:

```
Check this manuscript for defensive writing: paper.docx
```

You can also name the skill `revise-paper-defensive-writing` directly. It is triggered by phrases such as "defensive writing", "over-hedging", "too many disclaimers" or "the limitations section is too wordy", and by their Chinese equivalents.

The scripts can also be run on their own:

```bash
python scripts/extract.py paper.docx              # numbered paragraphs, written to a temp folder
python scripts/apply.py paper.docx edits.json     # build the revised copy from edits.json
```

## Design choices

- **No keyword-based bulk deletion.** Words like "not measured", "limitation" or "may" do not by themselves mean a sentence is defensive. Each sentence is judged on its own.
- **No unrelated polishing.** Only defensive expressions are changed, so the author can review every edit.
- **No new qualifiers.** Newer GPT-style models add unsupported qualifiers and narrow the authors' claims when polishing papers, and do so more when reviewers are mentioned (Liao, *Writing for the Reviewer: Defensive Writing in GPT Models*, arXiv:2610.11355). The revision itself must not repeat that mistake.

## Acknowledgements

The idea was inspired by an article on a Chinese WeChat public account. The rules, examples and code in this repository were written independently.

## License

MIT
