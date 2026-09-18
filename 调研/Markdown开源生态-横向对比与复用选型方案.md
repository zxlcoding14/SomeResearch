# Markdown 开源生态 — 技术方案 × 用户量 × 商业化 × 复用复杂度 × 跨平台 全景调研

> **分析对象**：Markdown 相关开源项目（解析内核 / 编辑器组件 / 端应用 / 发布工具）共 60+ 个仓库
> **分析视角**：产品经理视角 —— 回答"能不能直接复用、复用成本多高、谁已经验证过商业化、跨平台怎么落地"
> **数据截至**：2026-09-17（GitHub API / npm registry / 各官网定价页 实测）
> **承接文档**：本文是《Markdown编辑器需求调研.md》的**供给侧配套**。前者已确认需求空缺 ——「Typora 的免费平替：跨平台、启动快、内存小、中文友好、所见即所得、数据绝对安全」；本文回答"用什么开源零部件最快拼出来"。
> **一句话定位**：Markdown 是**基础设施级开源品类** —— 内核层几乎零成本、零风险（全 MIT）；但**变现能力与许可证开放度呈严格负相关**，且变现点 100% 不在编辑器功能上。

---

## 〇、结论先行（TL;DR）

1. **做产品不需要从零写内核，也不需要碰 AGPL。** 解析内核层（marked / markdown-it / micromark）全是 MIT/BSD，月下载量在 1 亿–2.7 亿量级，是**零成本、零法务风险**的成熟零件；真正该自己投入的是"写作体验层"。

2. **"Typora 免费平替"这件事，开源区已有现成零部件，且被严重低估：`Vditor`（MIT / 仅 1 个依赖 / 70KB gzip / 内置「即时渲染 IR」模式 / 中文原生）是最短路径。** 它 npm 月下载仅 16.1 万，远低于其能力位 —— 说明"可用但未被大规模验证"，对后来者既是风险也是差异化窗口。

3. **开源 Markdown 的商业化差距可达 ~270 倍，且与代码质量无关。** Obsidian（零融资、7 人、估 ARR $25M、MAU 150 万+）vs Logseq（开源、44.9k★、8 年累计募资 **$744,861**）—— 同赛道、同为本地优先、同为 Markdown 内核，年化收入差约 **268 倍**。差别不在开源，在于**是否把「同步 + 发布 + 协作」做成了付费刚需**。

4. **变现点 100% 落在编辑器之外的三件事上：同步 / 发布 / 协作。** 60+ 个项目的付费项无一例外 —— Obsidian（Sync/Publish）、Joplin（Cloud）、思源（S3-WebDAV 买断 + 云同步年订阅）、HackMD（协作席位）、Outline（团队权限）、AppFlowy / AFFiNE（Cloud）。**编辑器本身在开源世界的定价是 0，不要试图卖编辑器。**

5. **许可证开放度与商业化成反比，这是本报告最强的结构性发现。** 76.8k★ 的 AppFlowy、72.7k★ 的 AFFiNE、46.4k★ 的思源、44.9k★ 的 Logseq —— **全部 AGPL-3.0**；而被全行业白嫖复用的内核（marked / markdown-it / micromark / goldmark）**全部 MIT**。选 AGPL 是"防白嫖换维护者收入"，选 MIT 是"换生态位但放弃直接变现"。

6. **对 `mini-tool` 的落地结论（承接需求文档）**：MVP 走 **markdown-it（渲染）+ CodeMirror 6（编辑）+ 自研中文体验层**，或直接用 **Vditor** 抢时间窗；**P0 红线是「绝不丢内容」**（MarkText 正因丢内容被社区否决）。商业化不要卖编辑器，卖"AI 写作 + 同步/发布"。

---

# 第一层：全景分层框架（漏斗收敛起点）

Markdown 不是"一个品类"，而是**五层堆叠的产业链**。混在一起看会得出错误结论（例如"markdown-it 有 2.19 万星但 npm 月下载 1.12 亿"，两个数字说的不是同一件事）。

| 层级 | 角色 | 典型项目 | 谁在用 | 变现能力 |
|---|---|---|---|---|
| **L0 解析内核** | 文本 → Token/AST | markdown-it、marked、micromark、goldmark、comrak、pandoc | 所有下游 | ❌ 几乎为零 |
| **L1 编辑器组件** | 可嵌入的编辑 UI | Vditor、Cherry Markdown、Tiptap、Milkdown、CodeMirror、ProseMirror | 产品开发者 | ❌ 开源部分免费 |
| **L2 渲染增强链** | 公式/高亮/图表/安全 | KaTeX、Shiki、highlight.js、DOMPurify、remark-gfm | 所有下游 | ❌ 生态公共品 |
| **L3 端应用** | 用户可直接用的产品 | Obsidian、Joplin、思源、Logseq、AppFlowy、AFFiNE | 终端用户 | ✅ **唯一真金白银层** |
| **L4 发布/文档站** | 内容 → 站点 | Docusaurus、VitePress、HedgeDoc、Outline、MkDocs | 团队/企业 | ✅ 团队席位制 |

> **漏斗第一刀**：如果你的目标是做「Typora 免费平替」，你的**竞品在 L3**，你的**零件在 L0+L1+L2**，你的**付费墙参考在 L3+L4**。三者不能混谈。

---

# 第二层：技术方案（分五层枚举）

## 2.1 L0 解析内核：两大架构路线

| 架构路线 | 原理 | 代表 | 优势 | 代价 |
|---|---|---|---|---|
| **Tokenizer + Renderer** | 逐行扫锚 → token → 直接输出 HTML | markdown-it、marked、goldmark、comrak、pulldown-cmark | 快、体积小、易上手 | 只能"渲染"，做复杂变换要改 renderer |
| **AST 驱动（unified）** | 文本 → mdast → 插件链 → HTML/MDX | remark / micromark / unified / MDX / markdown-it-py | 可编程、可变换、支持 MDX | 依赖树庞大、包体膨胀、学习曲线陡 |

**关键洞察：AI 时代把 AST 路线推上了牌桌。** 原因不是渲染，而是 **AI 需要"结构化的 Markdown"** —— 要把 LLM 输出裁切、重排、插入组件、做引用标注，只有 AST 能做。`streamdown`（Vercel 的 LLM 流式渲染器）月下载 **2,247 万**，是 2025–2026 冒出的新物种，说明"为 AI 输出优化的 Markdown 渲染"已独立成层。

### 各语言内核实测（GitHub API，2026-09-17）

| 项目 | 语言 | ★ | Fork | 许可证 | 创建 | 最后提交 | 状态 |
|---|---|---|---|---|---|---|---|
| jgm/pandoc | Haskell | 46,304 | 4,003 | GPL-2.0 | 2010-03 | 2026-09-17 | 🟢 最全转换器 |
| markedjs/marked | JS | 37,151 | 3,717 | MIT 系 | 2011-07 | 2026-09-15 | 🟢 最快 |
| markdown-it/markdown-it | TS | 21,912 | 1,847 | MIT | 2014-12 | 2026-09-12 | 🟢 生态最广 |
| mdx-js/mdx | JS | 19,788 | 1,176 | MIT | 2017-12 | 2026-09-11 | 🟢 组件化 |
| erusev/parsedown | PHP | 15,059 | 1,135 | MIT | 2013-07 | 2026-02-18 | 🟢 |
| evilstreak/markdown-js | JS | 7,672 | 835 | — | 2009-12 | 2020-03-27 | 🔴 停更 6 年 |
| jonschlinkert/remarkable | JS | 5,842 | 375 | MIT | 2014-09 | 2024-05-17 | 🟡 半停 |
| yuin/goldmark | Go | 5,021 | 315 | MIT | 2019-04 | 2026-09-15 | 🟢 **主打 CJK 友好** |
| vmg/redcarpet | C | 5,078 | 534 | MIT | 2011-03 | 2025-03-06 | 🟡 |
| swiftlang/swift-markdown | Swift | 3,412 | 301 | Apache-2.0 | 2021-07 | 2026-09-16 | 🟢 |
| lepture/mistune | Python | 3,076 | 302 | BSD-3 | 2014-02 | 2026-08-21 | 🟢 |
| thephpleague/commonmark | PHP | 2,976 | 216 | BSD-3 | 2014-09 | 2026-09-17 | 🟢 |
| pulldown-cmark | Rust | 2,718 | 304 | MIT | 2015-06 | 2026-09-11 | 🟢 |
| commonmark/commonmark-java | Java | 2,689 | 336 | BSD-2 | 2015-07 | 2026-08-07 | 🟢 |
| vsch/flexmark-java | Java | 2,641 | 301 | BSD-2 | 2016-01 | 2025-04-16 | 🟡 |
| developit/snarkdown | JS | 2,401 | 115 | MIT | 2014-11 | 2022-11-29 | 🔴 停更 |
| micromark/micromark | JS | 2,220 | 89 | MIT | 2018-11 | 2026-09-11 | 🟢 CommonMark 100% |
| kivikakk/comrak | Rust | 1,701 | 193 | — | 2016-11 | 2026-09-14 | 🟢 |
| rsms/markdown-wasm | C/WASM | 1,672 | 69 | MIT | 2019-12 | 2022-11-22 | 🔴 停更 |
| wooorm/markdown-rs | Rust | 1,570 | 93 | MIT | 2022-06 | 2025-04-23 | 🟡 |
| mity/md4c | C | 1,447 | 215 | MIT | 2016-10 | 2026-09-16 | 🟢 |
| executablebooks/markdown-it-py | Python | 1,363 | 122 | MIT | 2020-03 | 2026-09-14 | 🟢 |
| miyuchina/mistletoe | Python | 1,063 | 139 | MIT | 2017-07 | 2026-09-16 | 🟢 |
| JetBrains/markdown | Kotlin | 959 | 104 | Apache-2.0 | 2014-12 | 2026-09-16 | 🟢 |

**新增变量（2025–2026 新项目，值得盯）**：`serkodev/markdown-exit`（1,363★，2025-08 建，markdown-it 的 drop-in 替代、原生 TS）、`comarkdown/comark`（1,031★，2026-01 建）。两者都在"重写 markdown-it"——说明 **markdown-it 的 API 已成事实标准，但实现被认为有更新空间**。

### 性能实测（公开基准，口径不同，仅作量级参考）

| 基准来源 | 结论 |
|---|---|
| MeasureThat 2026（marked 17 vs markdown-it 14，Chrome 143） | markdown-it **32,524 ops/s** vs marked **15,581 ops/s**（markdown-it 约 2.1×） |
| GitCode 实测（Node 16 / i7-10700K，10KB 文档） | marked **8ms** / markdown-it **18ms** / commonmark.js 22ms / showdown 35ms |
| BenchmarkLab（另一轮） | CommonMark 96,997 / Marked 96,997 / markdown-it 70,922 / Remarkable 78,288 |

> ⚠️ **口径警告**：三个基准互相矛盾（rank 反转）。结论应该是：**在 10KB–100KB 文档量级上，主流内核的性能差异对"写作场景"完全不可感知**（都是毫秒级）。不要在选型时拿性能当决策依据 —— 该拿**体积、依赖数、插件生态、维护活跃度**当依据。

## 2.2 L1 可嵌入编辑器组件（真正的"复用"战场）

| 项目 | ★ | 语言 | 许可证 | 核心技术 | 交互模式 | 最后提交 | 状态 |
|---|---|---|---|---|---|---|---|
| ueberdosis/tiptap | 38,414 | TS | MIT | ProseMirror | Headless 富文本 | 2026-09-16 | 🟢 open core |
| benweet/stackedit | 23,100 | JS | Apache-2.0 | — | 在线协同 | 2023-07-04 | 🔴 停更 |
| nhn/tui.editor | 18,020 | TS | MIT | ToastMark(自研) | WYSIWYG + 双栏 | 2024-08-01 | 🔴 **GitHub 已 archive** |
| pandao/editor.md | 14,317 | JS | MIT | CodeMirror | 双栏 | 2024-04-26 | 🔴 事实停更 |
| doocs/md | 13,335 | TS | WTFPL | — | 双栏（公众号排版） | 2026-09-16 | 🟢 中文场景 |
| Milkdown/milkdown | 11,919 | TS | MIT | ProseMirror + remark | **Markdown-first WYSIWYG** | 2026-09-16 | 🟢 |
| Vanessa219/vditor | 11,328 | TS | MIT | 自研 | **WYSIWYG / 即时渲染IR / 分屏 三模式** | 2026-09-15 | 🟢 中文原生 |
| sparksuite/simplemde | 10,145 | JS | MIT | CodeMirror | 双栏 | 2024-06-11 | 🔴 停更 |
| hinesboy/mavonEditor | 6,575 | Vue | MIT | CodeMirror | 双栏 | 2025-03-05 | 🟡 |
| Tencent/cherry-markdown | 4,872 | JS | Other(腾讯) | 自研 | 双栏 + 所见即所得 | 2026-09-16 | 🟢 但 152 open issues |
| pd4d10/bytemd | 1,370 | TS | MIT | remark/rehype | 双栏 + 插件化 | 2025-02-12 | 🟡 已转个人维护 |
| outline/rich-markdown-editor | 2,935 | TS | BSD-3 | ProseMirror | WYSIWYG | 2022-01-17 | 🔴 停更 |

### 三条技术路线的取舍（针对"Typora 式所见即所得"）

| 路线 | 代表 | 做到 Typora 体验的难度 | 适合谁 |
|---|---|---|---|
| **自研双栏**（左源码 + 右预览） | 大量产品 | ⭐ 容易，但**不是 Typora 体验**（Typora 无模式切换） | 快速验证 / 技术向用户 |
| **富文本引擎伪装 Markdown** | Tiptap、ProseMirror、Lexical | ⭐⭐⭐ 难在 **Markdown ↔ 富文本双向序列化会丢格式** | 需要深度排版、表格、协同 |
| **Markdown-first WYSIWYG** | **Vditor(IR 模式)、Milkdown** | ⭐⭐ 中等，但这才是 Typora 的真路线 | ⭐ **推荐** |

> **PM 结论**：要打"Typora 免费平替"，**必须选第三条路**。Vditor 的「即时渲染（IR）」模式和 Milkdown 是开源区唯一两个"天生就是这个形态"的零件。

## 2.3 L2 渲染增强链（npm 月下载量实测，2026-08-13 ~ 09-11）

| 能力 | 包 | 月下载量 | 说明 |
|---|---|---|---|
| 安全净化 | dompurify | 227,361,003 | **Markdown 渲染必配**，不做 XSS 净化是产品级事故 |
| 代码高亮 | highlight.js | 123,794,519 | 经典，体积大 |
| 代码高亮 | shiki | 86,007,371 | 现代，VS Code 同款主题，构建期重 |
| 数学公式 | katex | 91,983,392 | 公式渲染事实标准 |
| GFM 扩展 | remark-gfm | 138,600,977 | 表格/删除线/任务列表 |
| React 渲染 | react-markdown | 125,866,760 | Web 场景主流 |
| React 渲染 | markdown-to-jsx | 17,492,908 | 更轻 |
| **LLM 流式渲染** | streamdown | 22,471,668 | ⭐ Vercel 出品，**2025+ 新物种** |
| 反向转换 | turndown | 33,138,167 | HTML → Markdown（AI 抓网页必备） |
| 标题锚点 | markdown-it-anchor | 13,420,167 | |
| 校验 | markdownlint | 11,652,620 | |
| 参考 | prettier | 491,845,255 | 全品类第一，Markdown 格式化的实际承载者 |

## 2.4 技术选型决策树

```
要做「Typora 免费平替」
│
├─ 决定交互形态
│   ├─ 必须无模式切换（所见即所得）→ Vditor(IR) / Milkdown
│   └─ 可接受双栏 → markdown-it + CodeMirror 6
│
├─ 决定平台
│   ├─ Win/Mac/Linux 桌面 → Electron / Tauri
│   └─ 要求「启动快 + 内存小」（需求文档硬条件）→ Tauri 或原生壳
│
└─ 决定 AI 层（差异化所在）
    ├─ 流式输出渲染 → streamdown 思路
    ├─ 网页剪藏 → turndown
    └─ 本地模型 → 自研，无成熟开源件
```

---

# 第三层：用户量（真实数据）

## 3.1 内核层：npm 月下载量是比 Star 硬得多的指标

| 包 | 月下载量 | Star | 下载/Star 比 | 解读 |
|---|---:|---:|---:|---|
| marked | **271,994,342** | 37,151 | 7,321 | 传播最广 |
| micromark | 213,264,257 | 2,220 | 96,065 | **Star 严重低估**（被 remark 系带量） |
| mdast-util-from-markdown | 208,948,479 | — | — | remark 生态底座 |
| unified | 205,211,747 | — | — | AST 生态总入口 |
| remark-parse | 180,603,864 | — | — | |
| remark-gfm | 138,600,977 | — | — | |
| **markdown-it** | **112,044,306** | 21,912 | 5,113 | 被 VS Code 采用（含传递依赖） |
| remark | 21,037,454 | — | — | |
| showdown | 5,217,778 | — | — | 老牌，衰退中 |
| **vditor** | **161,176** | 11,328 | **14** | ⚠️ **下载/Star 比极低** |
| **cherry-markdown** | **23,702** | 4,872 | **5** | ⚠️ 极低 |
| bytemd | 27,169 | 1,370 | 20 | 低 |
| editor.md | 2,408 | 14,317 | **0.17** | 🔴 名存实亡 |

> **这是本报告最有复用的一个指标 —— "下载/Star 比"能识别"高星但没人真用"的组件。**
> - 比率 > 5,000：真实基础设施（marked、markdown-it）
> - 比率 < 50：**组件被大量 Star 但极少被真正集成**（vditor 14、cherry-markdown 5）
> - 后者恰恰是"机会区"：代码质量不差、社区声量不足、**没有被大厂占位**。
> - 例外说明：Cherry/Vditor 主要通过 CDN 分发（不走 npm），该比率会低估其真实使用量 —— 但仍显著低于同等星级的其他组件。

## 3.2 端应用层（L3）用户量实测

| 产品 | ★ | Fork | 许可证 | 平台 | 真实用户量（口径标注） |
|---|---|---|---|---|---|
| AppFlowy | 76,773 | 6,021 | **AGPL-3.0** | Win/Mac/Linux/iOS/Android/Web | 无官方披露；Discord 3,500+ 成员（2023） |
| AFFiNE | 72,692 | 5,284 | 腾讯式 NOASSERTION | 全平台 + 自托管 | 无官方披露 |
| memos | 63,119 | 4,764 | **MIT** | Docker/Web | 无官方披露 |
| MarkText | 61,511 | 4,551 | MIT | Win/Mac/Linux | 单版本下载量 1–2.4 万次（v0.20.0-rc 系列） |
| Joplin | 56,397 | 6,294 | NOASSERTION | 全平台 | **桌面端累计下载 12,801,252**（官网 stats 实测：Win 8,715,279 / Mac 2,175,543 / Linux 1,910,430） |
| 思源 SiYuan | 46,400 | 3,010 | **AGPL-3.0** | 全平台 + Docker | 无官方披露 |
| Logseq | 44,947 | 2,812 | **AGPL-3.0** | 全平台 + Web | 官网实时在线 1,774 人；150+ 插件 / 30+ 主题 |
| Outline | 40,570 | 3,560 | NOASSERTION | Web/自托管 | 无官方披露 |
| Trilium | 37,871 | 2,542 | **AGPL-3.0** | 全平台 + Docker | 无官方披露 |
| Wiki.js | 28,934 | 3,315 | AGPL-3.0 | Node 自托管 | — |
| notable | 23,496 | 1,182 | — | 桌面 | 🔴 2024-06 停更 |
| BookStack | 19,047 | 2,423 | MIT | PHP 自托管 | — |
| Zettlr | 13,525 | 840 | GPL-3.0 | 桌面 | — |
| VNote | 12,962 | 1,296 | LGPL-3.0 | 桌面（C++/Qt） | — |
| HedgeDoc | 7,425 | 596 | AGPL-3.0 | Docker Web | — |
| **Obsidian（闭源参照）** | — | — | 闭源 | 全平台 | **MAU 口径分歧**：①「1.5M+ 用户」（benchquill / setupai）②「552.66 万 MAU（2026-03）」（IMA 知识库）。取可信区间 **150 万–550 万** |

### 竞品生态杠杆（Obsidian 的"以社区代团队"模型）

| 指标 | 数值 | 口径 |
|---|---|---|
| 团队规模 | **7 名全职** | 第三方报道 |
| 社区插件数 | 2,700+（2026-03）／1,800+（另一来源） | 口径不一 |
| 每周新插件 | 5–12 个，70+ 个更新 | 第三方报道 |
| 单个插件峰值下载 | Excalidraw 插件 **500 万+** | 第三方报道 |
| 用户/员工比 | 约 **21.4 万 : 1** | 派生计算 |

## 3.3 中文生态专项

| 项目 | 归属 | ★ | 许可证 | 定位 | 商业化 |
|---|---|---|---|---|---|
| Cherry Markdown | 腾讯 | 4,872 | 腾讯自有 | 企业级 Markdown 编辑器 | 免费（内部基建外溢） |
| Vditor | Vanessa219（个人） | 11,328 | MIT | 通用编辑器三模式 | 免费 |
| ByteMD | 原字节 → 个人(pd4d10) | 1,370 | MIT | 插件化编辑器 | 免费 |
| mavonEditor | 个人 | 6,575 | MIT | Vue 双栏 | 免费 |
| doocs/md | 社区 | 13,335 | WTFPL | **微信公众号排版** | 免费 + 打赏 |
| 思源 SiYuan | 个人（中国） | 46,400 | AGPL-3.0 | 全功能笔记 | ✅ ¥80 买断 / ¥96 年订阅 |
| 语雀 / 飞书文档 | 阿里/字节 | — | 闭源 | SaaS | 订阅 |

> **洞察**：中文生态里**没有一个开源项目在卖编辑器**。腾讯/字节的投入是"内部基建 + 人才品牌"，个人项目靠打赏或同步服务。**思源是唯一走通人民币定价的开源 Markdown 笔记**。

---

# 第四层：商业化（漏斗形收敛）

## 4.1 第一层：六种变现模式枚举（穷举）

| # | 模式 | 案例 | 真实定价 |
|---|---|---|---|
| 1 | **付费同步服务** | Obsidian Sync / Joplin Cloud / 思源云 | Obsidian $4/mo；Joplin €2.99–9.99/mo；思源 ¥96/yr |
| 2 | **付费发布/托管** | Obsidian Publish / HackMD 公开笔记 | $8/mo |
| 3 | **一次性买断（桌面软件）** | Typora / 思源功能买断 / AFFiNE Believer | Typora **$14.99**；思源 **¥80**；AFFiNE **$499.99 终身** |
| 4 | **团队席位制** | HackMD / Outline / Joplin Teams | HackMD $5/seat/mo；Outline $10/月(1–10人)/$79/月(11–100)/$249/月(101–200)；Joplin €6.69/seat/mo |
| 5 | **云服务 + AI 加值** | AppFlowy Cloud / AFFiNE Pro | AppFlowy $10/user/mo；AFFiNE $6.75–$10/seat/mo |
| 6 | **开放核心（Open Core）** | Tiptap（MIT 内核 + 商业 Pro/Cloud） | 企业报价 |
| 7 | **捐赠/赞助（不构成商业模式）** | Logseq（Open Collective）、Joplin 打赏 | Logseq **累计 $744,861**（8 年） |

## 4.2 第二层：同赛道收入规模对比（**本报告的核心表**）

| 产品 | 许可证 | 团队 | 融资 | 年收入（口径） | ARPU（推算） | 人均产出 | ROI 判读 |
|---|---|---|---|---|---|---|---|
| **Obsidian** | 闭源（Markdown 内核） | **7 人** | **$0** | **~$25M ARR**（第三方估算，2026-03） | $4.5–16.7/年（按 MAU 150万–550万） | **$3.57M/人/年**（≈¥2,570 万） | ⭐⭐⭐ 极高 |
| **Logseq** | AGPL-3.0 | 4 名维护者 | $4.1M seed（2023，个人投资人） | **累计募资 $744,861 / 8 年 ≈ $93k/年** | ≈ $0（同步为 backer 门槛） | — | ⭐ 极低 |
| **Joplin** | NOASSERTION（MIT 系） | 小团队 | 无（Cloud 收入 + 捐赠） | 未披露；**12.8M 累计下载可作分母** | — | — | ⭐⭐ 中 |
| **思源 SiYuan** | AGPL-3.0 | 个人/小团队（中国） | 无 | 未披露；**¥80 买断 + ¥96 年订阅** | 低于 Obsidian | — | ⭐⭐ 中（本地市场） |
| **AppFlowy** | AGPL-3.0 | 50–100 人 | **$6.4M seed**（OSS Capital 领投） | Cloud $10/user/mo（起步免费） | — | — | ⭐⭐ 待验证 |
| **AFFiNE** | 编辑器 MIT / 整体受限 | 中等 | 未完全披露 | Pro $6.75/mo + Team $10/seat | — | — | ⭐⭐ 待验证 |
| **HackMD** | 部分开源 | — | — | 官网称 **100 万+ 用户 / 30k 团队 / 170 国 / 7.7M 笔记** | $5/seat/mo | — | ⭐⭐⭐ |
| **Outline** | NOASSERTION | — | 有融资 | $10–249/月 分档 | 高（团队制） | — | ⭐⭐⭐ |
| 参照：Notion（闭源） | 闭源 | ~800 人 | 多轮 VC | 百亿估值级 | $10–20/user/mo | — | ⭐⭐⭐ |

### 最有信息量的两个派生指标

**① ARPU 断层 ≠ 功能数量差**
- Obsidian ARPU ≈ **$4.5–16.7/年**（本地优先 + 极低基础设施成本）
- Joplin Cloud Basic ≈ **€28.69/年**（≈$31）
- 思源 ≈ **¥96/年**（≈$13.5）
- AppFlowy / AFFiNE / Outline ≈ **$81–120/年**（团队制）
> **决定性因素是「计费结构」（个人订阅 vs 团队席位）和「计价货币」（美元 vs 人民币），不是功能清单。**

**② 人均产出揭示模式效率**
- Obsidian：**$3.57M/人/年** —— 极端值，靠"7 人团队 + 2,700 插件社区"的杠杆
- 但**不可复制性极高**：它需要"本地文件 + 增量同步"这个架构前提，才能让用户增长**不带来基础设施成本**。云端产品做不到。

## 4.3 第三层：为什么大多数开源 Markdown 项目"不能"变现

| 障碍 | 机理 | 实证 |
|---|---|---|
| **编辑器功能的边际价值为 0** | 开源替代品免费且质量高，付费编辑器无法定价 | Typora 只能定 $14.99 买断；思源只能定 ¥80 |
| **同步是唯一的"物理性"付费点** | 用户愿意为"数据在自己设备之外存在"付费 | 所有产品付费墙都卡在同步/发布/协作 |
| **AGPL 阻断了 SaaS 白嫖，也阻断了生态** | 云厂商不敢用 AGPL，个人开发者不愿承担传染性 | 4 个最成功的 AGPL 产品都靠"卖云服务"变现，不靠生态 |
| **国内定价天花板 ≈ ¥50–100/年** | 比价压力 + 免费替代品充足 | 思源 ¥80 买断 / ¥96 年订阅已顶到上限；Quicker 参照 ¥57.6/年 |
| **捐赠不是商业模式** | 稀缺性好心人 vs 持续成本 | Logseq 8 年累计 $74.5 万，年化 $9.3 万 |

## 4.4 第四层：唯一被验证的可行路径（对 mini-tool 的启示）

```
开源 Markdown 项目能否变现？
│
├─ 卖编辑器本身 → ❌ 已证伪（Typora/思源 顶到 $15/¥80）
│
├─ 卖本地功能 → ❌ 已证伪（免费替代品太多，且社区反感"功能阉割"）
│
└─ 卖"编辑器之外的三件事" → ✅ 唯一被反复验证的路径
    ├─ 同步（Obsidian $4 / Joplin €2.99 / 思源 ¥96 年）
    ├─ 发布（Obsidian $8 / HackMD 公开笔记）
    ├─ 协作（HackMD $5/seat / Outline $10+ / Joplin Teams €6.69）
    └─ 【新增】AI 写作（尚无开源项目跑通 → 你的机会窗口）
```

> **关键机会判断**：Obsidian 明确"AI 不内置，靠插件"；思源要用户自备 API Key；Joplin 的 `Joplin Cloud AI` 还在 beta。**"开箱即用的 AI 写作 + AI 流式渲染 + 本地优先 Markdown"这个组合，在开源区目前没有占位者。** 这与你的 mini-tool 方向完全重合。

---

# 第五层：复用复杂度（可量化选型指标）

## 5.1 许可证风险矩阵 —— **这是复用决策的第一优先级**

| 许可证 | 传染性 | 能否闭源商用 | 代表项目 | 复用建议 |
|---|---|---|---|---|
| **MIT / BSD / Apache-2.0** | 无 | ✅ | marked、markdown-it、micromark、goldmark、KaTeX、Shiki、DOMPurify、Tiptap、Vditor、Milkdown、memos | ✅ **放心复用** |
| **MPL-2.0** | 文件级 | ✅（改动的文件需开源） | AFFiNE Blocksuite、Laverna | 🟡 可复用，勿改原文件 |
| **LGPL-3.0** | 库级（动态链接豁免） | 🟡 有条件 | VNote | 🟡 动态链接可，静态链接慎 |
| **GPL-2.0/3.0** | 强 | ❌ | Pandoc、Zettlr、glamour | ❌ 顶多当独立 CLI 调用 |
| **AGPL-3.0** | 最强（含网络服务） | ❌ | **AppFlowy、AFFiNE(部分)、思源、Logseq、Trilium、Wiki.js、HedgeDoc** | ❌ **绝对不能代码级复用** |
| **Other / NOASSERTION** | 需逐个读 | ⚠️ | Joplin、cherry-markdown、Outline | ⚠️ **必须人工核验 LICENSE 原文** |

> 🚨 **最容易踩的坑**：`AppFlowy / 思源 / Logseq / Trilium` 四个"看起来最像 Typora 平替"的项目，**全是 AGPL-3.0**。代码可以读、思路可以学，**一行都不能抄进闭源产品**。
> ⚠️ 第二个坑：`NOASSERTION` 不代表没有许可证 —— GitHub 只是无法自动识别。Joplin 实际是 MIT（多许可证混合），Cherry Markdown 是腾讯自有条款，Outline 是 BSL 系。**商用前必须读 LICENSE 全文。**

## 5.2 体积与依赖实测（Bundlephobia 实测）

| 组件 | 版本 | 原始体积 | gzip 后 | 直接依赖数 | 评价 |
|---|---|---:|---:|---:|---|
| **markdown-it** | 15.0.2 | 97,584 B | **40,507 B** | **6** | ⭐ 极优（entities 占 75KB 是大头） |
| **vditor** | 4.0.0 | 291,813 B | **70,297 B** | **1** | ⭐⭐ 功能/体积比最优 |
| **cherry-markdown** | 0.11.10 | **4,885,461 B** | **1,392,816 B** | **12** | ❌ 4.88MB / gzip 1.39MB，是 vditor 的 20 倍 |

> **对"轻量"定位的直接结论**：如果你的卖点是"启动快、内存小"（需求文档硬条件），
> **Cherry Markdown 直接出局**（4.88MB 主包 + 12 依赖，与轻量定位根本冲突）；
> **Vditor（70KB gzip / 1 依赖）和 markdown-it（40KB gzip / 6 依赖）是仅有的两个合格选项。**

## 5.3 维护活跃度与"弃坑"风险

| 风险等级 | 项目 | 信号 |
|---|---|---|
| 🟢 **活跃** | markdown-it、marked、micromark、goldmark、Vditor、Milkdown、Tiptap、Cherry、doocs/md、memos | 2026-09 仍高频提交 |
| 🟡 **半停滞** | bytemd（2025-02）、mavonEditor（2025-03）、flexmark-java（2025-04）、markdown-rs（2025-04）、remarkable（2024-05） | 半年到 1 年无提交 |
| 🔴 **停更/归档** | **tui.editor（GitHub 已 archive）**、editor.md（2024-04）、simplemde（2024-06）、stackedit（2023-07）、macdown（2023-07）、rich-markdown-editor（2022-01）、markdown-js（2020）、snarkdown（2022）、markdown-wasm（2022）、Laverna（2021）、notable（2024-06） | **11 个项目已死** |
| ⚠️ **需重新核实** | **MarkText** | GitHub 未 archive、2026-09-16 仍有提交、**v0.20.0-rc.3 于 2026-09-15 发布**（rc.1 单资产下载 24,301 次）—— 与《Markdown编辑器需求调研》中"已停更"的判断**已出现背离，建议更新结论** |

## 5.4 复用复杂度综合评分（5 维，⭐ 越多越易复用）

| 项目 | 许可证友好 | 体积/依赖 | 维护活跃 | 集成成本 | 功能完备 | **总分** | 适用定位 |
|---|---|:---:|:---:|:---:|:---:|:---:|---|
| **markdown-it** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐（纯渲染） | **14/15** | 自研双栏内核 |
| **Vditor** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐（三模式） | **15/15** | ⭐ **Typora 平替首选** |
| **Milkdown** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **13/15** | Markdown-first WYSIWYG |
| **Tiptap** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **13/15** | 深度排版/协同 |
| **marked** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | **14/15** | 极简渲染 |
| **micromark/remark** | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | **11/15** | AI/AST 变换 |
| Cherry Markdown | ⭐⭐ | ❌ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | **10/15** | 企业后台富编辑器 |
| bytemd | ⭐⭐⭐ | ⭐⭐ | ⭐ | ⭐⭐ | ⭐⭐ | **10/15** | 不推荐新项目 |
| tui.editor | ⭐⭐⭐ | ⭐⭐ | ❌ | ⭐⭐ | ⭐⭐⭐ | **10/15** | ❌ 已归档 |
| 思源 / AppFlowy / Logseq | ❌ AGPL | — | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ | **不可复用** | 仅作产品参考 |

---

# 第六层：跨平台

## 6.1 技术栈 → 平台矩阵

| 技术路线 | 代表产品 | Win | Mac | Linux | iOS | Android | Web | 冷启动/内存 |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Electron** | MarkText、Joplin、Logseq、思源、AFFiNE、Trilium、Zettlr、Obsidian | ✅ | ✅ | ✅ | 独立 RN | 独立 RN | ✅ | ❌ 重（需求文档主要痛点） |
| **Flutter + Rust** | AppFlowy | ✅ | ✅ | ✅ | ✅ | ✅ | 弱 | 🟡 中 |
| **C++ / Qt** | VNote | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ 轻 |
| **Go 内核 + Electron 壳** | 思源（内核 Go / 壳 Electron） | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | 🟡 中 |
| **Tauri（Rust + 系统 WebView）** | 少量新项目 | ✅ | ✅ | ✅ | 部分 | 部分 | ❌ | ✅ 较轻 |
| **纯 Web（自托管）** | HedgeDoc、Outline、Wiki.js、memos | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ 但非"本地编辑器"（需求文档已排除） |

## 6.2 跨平台路线的真实取舍

| 路线 | 优点 | 代价 | 适合 |
|---|---|---|---|
| Electron | 生态最成熟、渲染一致（自带 Chromium） | **内存 200–500MB、启动慢** —— 与"Typora 平替"定位直接冲突 | 功能优先 |
| Tauri | 复用系统 WebView → 包体小 5–10 倍 | 不同系统 WebView 版本差异 → **渲染不一致**（写作产品致命） | 体积优先 |
| Qt / 原生 | 内存最小、启动最快 | 开发慢、Markdown 渲染要自己造（无成熟浏览器级排版） | 极致轻量 |
| Flutter + Rust | 真正一套代码全平台 | Dart 生态对 Markdown 不友好；AppFlowy 的移动端仍显著滞后 | 全平台优先 |

> **承接需求文档的社区共识**："轻量 Markdown 渲染很难绕开浏览器内核"——但选择了浏览器内核就等于接受 Electron/Tauri 的取舍。**这是该品类无法回避的根本矛盾，也是唯一的差异化空间所在。**

## 6.3 跨平台一致性中最容易被忽视的坑：CJK（中文）

| 问题 | 表现 | 证据 |
|---|---|---|
| **中英混排的换行/断词** | 中文无空格，按空格断词会错行 | goldmark 明确把 **"CJK-friendly"** 写进 README 作为卖点 —— 说明这是真实需求 |
| 中文字体的行高/字重**渲染不一致** | 同一文档在 Win/Mac 排版差异明显 | — |
| **输入法（IME）与编辑器冲突** | 拼音输入过程中触发 Markdown 语法 | 需求文档中 MarkText「光标错位」、Zettlr「疑似中文 bug」均为该类问题 |
| **中文标点语法误判** | 全角符号被识别为语法符号 | — |

> ⭐ **这是《Markdown编辑器需求调研》里"中文友好"痛点的技术归因。** 而 Vditor（中文原生开发）、goldmark（CJK-friendly）、doocs/md（公众号场景）三个项目恰好都在这个点上天然占位。**"中文友好"不是营销词，是 4 个具体技术点的工程投入。**

---

# 第七层：选型建议（针对「Typora 免费平替」目标）

## 7.1 三套可执行组合方案

### 方案 A：全 MIT 自研双栏（**风险最低，最快验证**）
| 层 | 选型 | 许可证 | 体积 |
|---|---|---|---|
| 编辑 | CodeMirror 6 | MIT | 轻 |
| 渲染 | **markdown-it** | MIT | 40.5KB gzip / 6 依赖 |
| 高亮 | Shiki 或 highlight.js | MIT | — |
| 公式 | KaTeX | MIT | — |
| 净化 | DOMPurify | Apache-2.0/MIT | — |
| AI 流 | 参考 streamdown 思路自研 | — | — |
**工期**：最短 ｜ **代价**：不是 Typora 体验（双栏有模式切换）

### 方案 B：Vditor 抢时间窗（**最贴近目标形态，⭐ 推荐**）
| 优势 | 数据支撑 |
|---|---|
| 内置三种模式（WYSIWYG / **即时渲染IR** / 分屏），IR 模式 ≈ Typora 体验 | 官方能力 |
| 体积/依赖最优 | 291KB / **70KB gzip** / **1 个依赖** |
| 中文原生开发，CJK 问题最少 | 中文团队 |
| MIT 可闭源商用 | LICENSE 明确 |
| **未被大厂占位，npm 月下载仅 16.1 万** | 差异化窗口 |
**工期**：最短 ｜ **风险**：单人维护，需评估长期可持续性（建议 fork 后内部维护）

### 方案 C：Milkdown / Tiptap + remark AST（**体验最好，最贵**）
适用：需要**复杂排版、表格、协同、AI 结构化改写**。代价：ProseMirror 学习曲线 + Markdown 双向序列化丢格式的风险。

## 7.2 优先级表

| 优先级 | 事项 | 理由 |
|---|---|---|
| **P0** | **数据可靠性：原子写入 + 崩溃恢复 + 自动备份** | 「绝不丢内容」是社区红线（MarkText 因此被否） |
| **P0** | **中文体验：IME 兼容、中英混排断行、全角标点** | 需求文档中的高频痛点，且竞品普遍不解决 |
| **P0** | **许可证合规：全链 MIT，禁用 AGPL 系代码** | 一次污染，全部返工 |
| **P1** | 启动速度 / 内存（选 Tauri 或原生壳 vs Electron 的取舍） | 需求文档硬条件 |
| **P1** | 无模式切换的所见即所得（选 Vditor IR 或 Milkdown） | 目标形态核心 |
| **P1** | **AI 写作层（流式渲染 + 本地模型可选 + BYOK）** | 开源区无占位者，是唯一增量卖点 |
| **P2** | 同步 / 发布（**这是唯一被验证的付费墙**） | 但 P2 不影响 MVP 验证 |
| **P2** | 插件机制 | 需求文档中为"锦上添花" |

## 7.3 风险清单

| 风险 | 等级 | 缓解 |
|---|---|---|
| 选了 AGPL 系代码（思源/AppFlowy/Logseq） | 🔴 致命 | 只读思路，不抄代码；依赖清单做 license 扫描 |
| `NOASSERTION` 项目未核验 LICENSE 原文 | 🟠 高 | Joplin / Cherry / Outline 商用前人工读 LICENSE |
| 依赖 Vditor 单人维护 | 🟠 高 | fork + 内部维护，或方案 A 兜底 |
| 做了编辑器功能却无法变现 | 🟠 高 | 变现锚点从一开始就设计在"同步/发布/AI" |
| 电子/内存与"轻量"定位冲突 | 🟡 中 | 早期明确 Tauri vs Electron，避免后期重写 |

---

## 附：数据来源与口径说明

| 数据类别 | 采集方式 | 采集时间 | 口径说明 |
|---|---|---|---|
| GitHub Star / Fork / License / 提交时间 | GitHub REST API `api.github.com/repos/*`、`/search/repositories` | 2026-09-17 | 精确值，非估算 |
| npm 月下载量 | `api.npmjs.org/downloads/point/last-month/*` | 2026-09-17（统计区间 2026-08-13 ~ 09-11） | 含 CI 与传递依赖，**不等于终端用户数** |
| 包体积 / 依赖数 | Bundlephobia API | 2026-09-17 | 主入口 bundle，未 tree-shake |
| Release 下载量 | GitHub Releases API 资产 download_count 求和 | 2026-09-17 | 仅统计 GitHub 直链，不含国内镜像分发 |
| Joplin 累计下载 | joplinapp.org/stats 官方页面 | 2026-09-17 | 官方自报，按平台分列 |
| 各产品定价 | 官网定价页直读（Obsidian/Lypora/Joplin/SiYuan/HackMD/Outline/AFFiNE/AppFlowy） | 2026-09-17 | 官方定价页为准 |
| 思源调价记录 | 什么值得买 / 官方社区公告 | 2026-03-02 生效 | 72→80 元，仅影响新购用户 |
| Logseq 财务 | Open Collective 公开账本 | 2026-09 实测 | **全透明账本**，可信度高；累计募得 $744,861.50 |
| Obsidian ARR / MAU / 团队 | 第三方报道与估算（biggo、setupai、IMA 知识库） | 2026-03 前后 | ⚠️ **估算，非官方披露**；MAU 存在 150 万 / 552 万两个口径 |
| AppFlowy 融资 | 官方 blog + TechCrunch 系转载 | 2023-11 | $6.4M seed，OSS Capital 领投 |
| 性能基准 | MeasureThat / GitCode / BenchmarkLab | 2026（部分口径较旧） | ⚠️ **三个基准互相矛盾，仅作量级参考** |
| 已停更判断 | 以"最后提交时间 + 是否 archive"为准 | 2026-09-17 | 与《Markdown编辑器需求调研》中 MarkText 结论存在背离，建议更新 |

> **本报告未能取得的数据（如需可继续深挖）**：思源/AppFlowy/AFFiNE/Joplin 的确切付费用户数与年收入（均未公开）；Obsidian 官方 MAU；PyPI 侧下载量（pypistats 接口限流，Python 生态 mistune 3,076★ / markdown-it-py 1,363★ 仅有 GitHub 指标）。
