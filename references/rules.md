# 防御性表达判断规则

## 总检验

对每一句限定、免责、否认、"仍需谨慎"类表达，依次问：

1. **删掉它，读者会不会被实质性误导？** 会 → 信息必须保留（可改写表达）；不会 → 进入第 2 问。
2. **它有没有增加新的科学信息？**（对象、条件、数值、未测量的指标、设计限制、具体的替代解释）有 → 把这部分信息留下，去掉包装；没有 → 删除。
3. **同一信息是否已在别处说过？** 是 → 只在最合适的位置保留一次（通常是 Discussion 的 limitations 段），其他位置删除。

原则：有扎实的文献和数据支持，就给出相应解释；没有足够依据，就不继续延伸；真实局限直接写清楚，写完就停。

---

## D 类：删除（不增加科学信息）

| 代码 | 模式 | 英文常见形态 | 中文常见形态 |
|---|---|---|---|
| D1 | **稻草人否认**：否认正文从未提出的结论 | should not be taken to imply that all/every…; this does not mean that… | 这并不代表所有…；不能据此认为…（而正文并未这样说） |
| D2 | **空泛谨慎尾句**：没有具体理由的"谨慎解读" | should be interpreted with caution; caution is warranted | 仍需谨慎解释；结论需审慎看待 |
| D3 | **重复局限**：同一局限在多处复述 | as mentioned, given the small sample… (第 N 次) | 如前所述，受样本量限制… |
| D4 | **二次对冲**：已用 may/might/可能 标明推测，又补一句"这只是推测" | however, this remains speculative; this hypothesis requires confirmation | 但这仍是推测，有待证实 |
| D5 | **预设质疑式自辩**：替想象中的审稿人辩护、解释为什么没做 | this may be unavoidable given the nature of…; due to budgetary limitations we were unable to… | 受客观条件所限，难以避免…；由于经费原因… |
| D6 | **空泛展望**：没有说明要做什么研究 | further studies are needed (句末孤立出现) | 有待进一步研究证实 |
| D7 | **范围免责**：声明"本研究不主张 X"，但没人主张 X | this study does not claim to establish… | 本研究并非旨在… |
| D8 | **元话语铺垫**：只起过渡作用、给后文"打预防针" | it should be noted that; it is important to acknowledge that; despite the novelty of the current study | 需要指出的是；值得注意的是；尽管本研究具有一定创新性 |

D8 常与有用信息同句出现：删铺垫，留信息。

## R 类：改写（有信息，但包装过度）

| 代码 | 做法 | 例 |
|---|---|---|
| R1 | **局限去辩解**：保留事实，删去原因铺陈与自我开脱 | "owing to funding constraints we were regrettably unable to measure serum 25(OH)D, which would certainly have strengthened our conclusions" → "Serum 25(OH)D was not measured." |
| R2 | **分散局限合并**：多处零散局限并成一句 / 一段 | "…the cohort was relatively modest in size. … Another potential concern is that follow-up may have been somewhat short…" → "Limitations include the small cohort and the 6-month follow-up." |
| R3 | **叠加对冲降为一个** | "may possibly suggest a potential role" → "may play a role" / "suggests a role"（看证据强度） |
| R4 | **双重否定改正说** | "was not without effect" → "had an effect on…"（仅当数据支持） |
| R5 | **边界条件并入主张**：把"仅限于某人群"之类的有效限定写进主句 | "X improved Y. However, this was only observed in ICU patients." → "In ICU patients, X improved Y." |
| R6 | **"无法完成"改为测量事实** | "we were not able to obtain reliable adherence data, as this would have required pill counts that were impractical in our setting" → "Adherence was not measured." |

## K 类：必须保留（不是防御性写作）

- **K1 阴性结果与统计量**：未达显著性、置信区间跨 1、效应量小——这是结果本身。
- **K2 单次、恰当的推测标记**：机制解释中的 may / might / could / 可能，区分推测与已证实机制。
- **K3 影响解释的具体局限**：样本量、观察性设计（不能推断因果）、未测量 / 缺失的变量、选择偏倚、未校正混杂、随访短、单中心、外推人群。
- **K4 因果措辞护栏**：观察性研究中的 associated with / 相关，而非 caused / 导致。
- **K5 分析层级区分**：组内 vs 组间差异、主要 vs 次要终点、预设 vs 事后 / 探索性亚组、多重比较未校正。
- **K6 报告规范要求的内容**：CONSORT / STROBE / PRISMA 要求的局限性、方案偏离、缺失数据处理——至少保留一次。
- **K7 伦理、利益冲突、资金、预注册**相关声明。
- **K8 期刊或作者明确要求**的表述。

## 反向护栏（修订后必须自查）

防御性修订最常见的失败不是删得不够，而是删过头：

1. **不得升级主张强度**：may → does、associated → caused、trend → significant、suggest → demonstrate，一律禁止。删掉"这只是推测"时，推测本身的 may 必须保留。
2. **不得删除有依据的解释**：有数据或引文支持的机制、比较、解释，留着。
3. **不得改动数据**：数字、P 值、置信区间、单位、样本量、引用标记、图表编号。
4. **换说法 ≠ 删除**：把 "should be interpreted with caution" 改成 "warrants careful interpretation" 不算处理。检查每条 D 类修改是真的删掉了。
5. **局限不能消失**：每条 K3 局限在全文至少还剩一处。
6. **不新增证据**：不加引用、不补数据、不编造原文没有的局限或解释。
7. **不顺手润色**：与防御性表达无关的语法、用词、风格不动——那是另一项任务，混在一起会让作者无法逐条审核。

## 识别线索（只是线索，不能据此批量删除）

英文：nevertheless, should be interpreted with caution, should not be taken to imply, does not necessarily, cannot be ruled out, remains to be determined, warrants further investigation, further studies are needed, it should be noted, it is important to acknowledge, to some extent, potentially, possibly, may…(叠用), not without, only, merely, limited to, preliminary。

中文：需要指出的是、值得注意的是、仍需谨慎、尚不能说明、不能据此认为、不代表、并不意味着、尚未排除、仅限于、在一定程度上、有待进一步研究、可能…或许…（叠用）、受…所限。

出现这些词 ≠ 防御性写作。逐句按"总检验"判断。

## 背景

- 新版 GPT 类模型在润色论文时会收窄、撤回作者主张，并添加材料不支持的限定；提到"审稿"或做一轮自审后更严重。AI 审稿人给这类稿件更高分，人类读者觉得更难读、作者更不自信（Liao, *Writing for the Reviewer: Defensive Writing in GPT Models*, arXiv:2610.11355）。
- 因此本技能本身也要警惕同样的倾向：**不要在修订中新增任何限定句。**
