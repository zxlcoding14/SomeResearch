# Readest 产品分析报告（PM 视角）

> 调研日期：2026-09-18 | 对象：Readest（readest.com）
> 数据来源：官网及定价页、GitHub 生态数据（reporank，2026-09）、Uptodown、Cossmology 企业档案、第三方评测（大眼仔、BookShelves 对比、Make Tech Easier、Arabian Post）
> 说明：收入无官方披露，推断处均显式标注

---

## 一、结论先行

1. **Readest 是 2024 年成立的开源电子书阅读器**（AGPL-3.0，Bilingify LLC，德国），由 Foliate 核心的现代重写（Tauri v2 + Next.js）+ KOReader 联合创始人的社区号召力构成，GitHub **24,278 stars**（2026-09），是开源阅读器赛道近两年增长最快的项目。
2. **商业模式 = 开源客户端 + 订阅 SaaS（open-core）**：Free $0 → Plus $4.99/月 → Pro $9.99/月，另有 $9.99~$49.99 存储买断和 $19.99 全部自定义买断。**收费的从来不是"阅读"，而是云同步存储 + AI 翻译/朗读配额**——这是典型的"边际成本项货币化"设计。
3. **核心差异化**：七端覆盖（macOS/Win/Linux/Android/iOS/Web/KOReader 墨水屏）+ 阅读器生态集成（Readwise/Notion/Obsidian/Calibre/OPDS）+ 分屏对照阅读（Parallel Read）——占位是"知识工作者 & 极客的最后一款阅读器"，而非大众书店型 App。
4. **主要风险**：pre-1.0（v0.12.x）、PDF 仍是实验性、六平台全做导致单端体验折衷（无 iCloud/原生多窗口）、开源阅读社区对订阅制有天然抵触、专有云同步 = 数据锁定争议。

---

## 二、产品概览

| 项目 | 内容 |
|---|---|
| 定位 | "免费开源的 EPUB/PDF 阅读器，为深度沉浸式阅读打造"；口号 Read, Digest, Get Insight |
| 主体 | Bilingify LLC（德国注册，2024；创始人 Huang Xin，KOReader 联合创造者） |
| 技术栈 | Foliate 现代重写；Tauri v2 + Next.js + Rust；支持 Docker 私有化部署 Web 端 |
| 格式 | EPUB、MOBI、KF8(AZW3)、FB2、CBZ、TXT、Markdown；**PDF 实验性** |
| 平台 | macOS、Windows、Linux、Android、iOS、Web、KOReader 插件（即墨水屏设备） |
| 开源数据 | GitHub 24.3k stars / 1.57k forks（2026-09，90 天净增约 +376）；AGPL-3.0 |
| 融资 | 无公开融资记录 |

## 三、功能分层（用户价值拆解）

| 层级 | 功能 | 说明 |
|---|---|---|
| 阅读基础 | 高亮/笔记/书签/全文搜索、双模式翻页（分页+滚动）、主题/字体/行距深度自定义 | 全免费 |
| 差异功能 | **Parallel Read 分屏对照**（同步滚动，最多 4 本书）、DeepL 翻译、Wikipedia/词典查询 | 免费+配额 |
| 多端同步 | 书库/进度/标注云同步、KOReader 同步、OPDS/Calibre-Web 接入 | 500MB 免费 |
| AI 层 | AI 朗读（TTS 有声书化）、AI 翻译（Google/Azure/DeepL/Yandex） | 配额货币化核心 |
| 工作流集成 | Readwise、Notion、Obsidian 导出、Audiobookshelf、Hardcover/BookOrbit、LocalSend 传书 | 面向知识工作者 |

**PM 解读**：功能设计刻意避开"书店/内容"赛道，全部押注"已有书的人怎么读得更好"——与微信读书、Kindle 的内容生态玩法完全正交。

## 四、商业化分析

### 1. 定价漏斗（真实数据）

| 档位 | 价格 | 核心权益 |
|---|---|---|
| Free | $0 | 全部基础功能 + 500MB 云同步 + 1 万字符/天 AI 翻译 + AI 朗读 |
| Plus | $4.99/月 | 5GB 存储、10 万字符/天翻译（DeepL Pro 10 万字）、无限朗读、解锁全部自定义、优先支持 |
| Pro | $9.99/月 | 20GB 存储、50 万字符/天翻译、新功能抢先、高级 AI 工具 |
| Lifetime（按需买断） | 存储增量 $9.99~$49.99；全部自定义 $19.99 | 一次性付款，账号绑定全平台 |

### 2. 定价结构点评

- **配额即价格锚点**：免费版给 1 万字/天翻译是精心设计的"够用但会撞墙"线（重度用户一天读 2 万字外文书即触发升级）；AI 翻译/朗读是真实 API 成本项（DeepL Pro 按 char 计费），配额制把变动成本转嫁给付费者，免费用户成本封顶；
- **存储 = 锁定器**：500MB 免费额度恰好容纳小书库，书架越大越难迁出（取消订阅后旧书仍可下载但无法上传新书、第三方云同步被停）——续费动力来自沉没的书库资产；
- **买断并行订阅**是少见设计：照顾开源社区"反订阅"情绪，给"我只想要全自定义"的用户一次性出口（$19.99）；
- 收入无披露。推断量级：24k stars 对应的可触达极客用户约数十万安装量级，若付费转化 1~2%，**ARR 粗略在十万美元级（纯推断，无披露）**。

### 3. 增长引擎

- **开源 + GitHub 社区**（stars 90 天 +376，持续自然增长）；
- **KOReader 联动**直击墨水屏存量用户（创始人即 KOReader 联合作者，冷启动信任成本≈0）；
- **媒体口碑**：Make Tech Easier"可能是你唯一需要的电子书阅读器"（2025-10）、Yahoo Tech Kobo 主题报道（2026-05）；
- 应用商店/Uptodown 等分发（Uptodown Windows 下载约 2k，量级尚小，主要增长在社区渠道）。

## 五、竞争格局

| 竞品 | 类型 | 与 Readest 关系 |
|---|---|---|
| Foliate / KOReader | 开源（Linux 桌面/墨水屏） | 前身与盟友；Readest 补齐其移动+云同步短板 |
| Koodo Reader | 开源跨平台阅读器 | 最直接开源对手；Readest 胜在 iOS/Web/墨水屏覆盖与活跃度 |
| Calibre | 开源书库管理 | 互补（Readest 做其阅读端） |
| Readwise Reader | 订阅制 $9.99/月（read-later） | 争夺知识工作者钱包；Readest 胜在开源+自管书文件，败在无内容发现 |
| Kindle / Apple Books / 微信读书 | 生态绑定型 | 不同赛道（内容 vs 工具）；Readest 服务"书的来源不依赖商店"的用户 |

## 六、风险

1. **pre-1.0 工程债**：PDF 实验性、TTS 章节续播 bug、大书库内存占用高（社区实测）；
2. **六平台折衷**：不用 iCloud、无 macOS 原生多窗口/Shortcuts——被对比评测反复点名；
3. **反订阅情绪**：开源阅读社区对 reader 收订阅费有结构性抵触，评分中已见反弹；
4. **专有云同步的单点依赖**：服务关闭则同步/升级失效（AGPL 保证客户端可用，但云端不在开源范围）。

## 七、PM 启示

1. **"开源客户端 + 云配额 SaaS"是工具类开源项目的标准变现答案**，Readest 的配额设计（AI 成本项配额化 + 存储锁定）值得同类产品抄作业；
2. **创始人社区资产（KOReader） = 冷启动最大杠杆**——开源产品选赛道时，"作者在目标社区已有信任"比功能规划更重要；
3. **七端同做的代价**：覆盖广度是传播亮点（"最后一款阅读器"叙事成立），但单端深度被牺牲，长期需要平台优先级取舍（墨水屏/桌面 vs 移动）；
4. 与本系列调研对照：Readest 验证了"不卖软件卖服务配额"路线在开源工具上的可行性——与白描（买断）、案记索图（免费+定制）构成工具变现的三种范式。

---

### 附：关键链接
- 官网：https://readest.com/zh | 定价：https://readest.com/pricing | Web 版：https://web.readest.com
- GitHub：https://github.com/readest/readest（AGPL-3.0）
- 企业档案：https://cossmology.com/organizations/readest
- 对比评测：https://getbookshelves.app/alternatives/readest/ | https://www.dayanzai.me/readest.html
