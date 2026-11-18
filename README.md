# revise-paper-defensive-writing

**版本 0.1** · 一个 Claude Code Skill：检查并修改学术论文中的**过度防御性写作**。

AI 润色过的论文常在每个发现后补一句"这些结果应谨慎解读""这并不代表所有指标都改善""仍需进一步研究证实"。这类句子看起来严谨，实际上常常不增加任何科学信息，还会让作者显得不自信。本技能通读全文，删掉这类句子，把真实局限写清楚并只保留一次，同时不丢失任何结果、限定和局限。

> 判断标准：**一个限定是否需要保留，只看删掉它以后，读者会不会被实质性误导。**

## 它做什么

| 处理 | 例 |
|---|---|
| 删除不增加信息的尾句 | 否认正文从未提出的结论；没有具体理由的"需谨慎解读"；已用 *may* 标明推测后再补"但这仍是推测" |
| 改写有信息但包装过度的句子 | "由于经费限制，我们遗憾地未能测定 X，这本可以加强结论" → "X 未测定。" |
| 合并重复局限 | 散落在多处的同一局限，只在最合适的位置保留一次 |
| **保留** | 阴性结果与统计量、单次的推测标记、影响解释的具体局限、因果措辞护栏、事后分析标注、报告规范要求的内容 |

规则全文见 [`references/rules.md`](references/rules.md)（D1–D8 删除 / R1–R6 改写 / K1–K8 保留 + 反向护栏）。

## 支持的格式

| 输入 | 输出 |
|---|---|
| `.docx` | 带**真实 Word 修订痕迹**（`w:ins`/`w:del`）的文档，作者可逐条接受/拒绝；斜体、上标、EndNote/Zotero 引文域、超链接、书签、脚注引用不受影响 |
| `.md` `.txt` `.tex` `.qmd` `.rmd` | 干净修订稿 + [CriticMarkup](https://github.com/CriticMarkup/CriticMarkup-toolkit) 审阅稿（`{--删--}{++增++}{>>理由<<}`）；`--inplace` 直接改原文件并保留 `.bak` |
| 两者 | 逐条修订说明（类型、理由、修订痕迹、修订后文本） |

安全检查：

- Word：自动核对"全部接受 = 新稿、全部拒绝 = 原稿"。
- 文本格式：误删或新增引用（`[@key]`、`[12]`、`\cite{}`）、公式、链接会被拦下。
- 代码块、公式块、front matter、已有修订的 Word 段落一律不改。

## 安装

```bash
git clone https://github.com/shaou77/revise-paper-defensive-writing ~/.claude/skills/revise-paper-defensive-writing
```

依赖：Python 3；处理 `.docx` 需要 `lxml`（`pip install lxml`）。

## 使用

在 Claude Code 中：

```
检查这篇论文的防御性写作：paper.docx
```

或点名使用 `revise-paper-defensive-writing`。触发词包括：防御性写作、过度谨慎、免责声明太多、hedging、defensive writing 等。

脚本也可单独运行：

```bash
python scripts/extract.py paper.docx              # 编号段落 → 临时目录
python scripts/apply.py paper.docx edits.json     # 按 edits.json 生成修订稿
```

## 设计取舍

- **不靠关键词批量删除。** "未测量""局限""may"出现不等于防御性写作，必须逐句判断。
- **不顺手润色。** 只改防御性表达，作者才能逐条审核。
- **不新增任何限定。** 新版 GPT 类模型在润色时会添加材料不支持的限定、收窄作者主张，提到"审稿"时更甚（Liao, *Writing for the Reviewer: Defensive Writing in GPT Models*, arXiv:2610.11355）。修订本身不能重蹈覆辙。

## 致谢

思路受一篇中文公众号文章启发。本仓库的规则、示例和代码均为独立编写。

## 许可

MIT
