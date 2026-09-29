# CleanMyMac 竞品矩阵 — 产品经理视角分析报告

> **分析对象**：CleanMyMac 5（基准产品）及其全部主要竞品（Mac 清理 / 优化 / 可视化 / 安全套件，共 11 个可辨识主体 + 6 个免费层）
> **分析视角**：产品经理（功能点 → 价值锚点 → 付费理由 → 商业化路径）
> **数据截至**：2026-09-28（今日实测）
> **汇率口径**：USD/CNY = 6.7195，EUR/CNY = 7.6501，HKD/CNY = 0.8566（er-api.com，2026-09-28 00:02 UTC）
> **买断摊销口径**：一次性授权统一按 **5 年**摊为年化 ARPU（与既有「重复文件查找赛道」「备份×克隆赛道」报告保持一致）
> **承接**：本报告是《CleanMyMac-产品分析报告（PM视角·功能点与营收点拆解）》的竞品篇

---

## 〇、结论先行（TL;DR）

**1. 竞品之间真正的分水岭不是「功能多少」，而是「价值锚在哪个焦虑上」。**
11 个付费主体里 **9 个的功能是同一个模子**——垃圾清理 + 应用卸载 + 大文件 + 重复文件，四项全占。功能层面已无差异化空间。差异 100% 来自价值锚点，而价值锚点直接决定定价：**同赛道年化 ARPU 从 ¥0 跨到 ¥1,209，约 90 倍断层**，与功能数量完全无关。

**2. 「清理」这个价值正在被三股力量同时清零——这是本次分析最硬的判断。**
① **macOS 自愈**：Apple 官方不鼓励 cleaner apps，DaisyDisk 官网直接把 "cleaner app" 做成对照表（自查恢复 1–5GB / 缓存可再生 / 可能损坏系统 vs DaisyDisk 10–100GB+ / 永久删除 / 安全挡板），并标注 "Recommended by Apple: Yes"。
② **免费 + 本地化**：腾讯柠檬清理以「完全免费 + GitHub 开源 + 微信/QQ/Xcode/Sketch 逐一定制扫描」把中国区中间层价格直接打到 0。
③ **缓存可再生**：清理是重复需求，但用户没有重复付费的理由。
→ 这是「被操作系统内置 = 品类死亡判决」规律的**第六次验证，且形态升级**：不是被 OS 直接内置杀死，而是被「免费 + 本地化」杀死在中间层。

**3. 能收费的那一层已经迁移到三件事：安全感、可视化、持续成本项。**
实证：竞品所有加档/涨价动作都落在这三处——安全（MacKeeper 的 VPN + ID 监控、MacBooster 的杀毒、Intego/Trend Micro 的 AV+FW 套件）、可视化（DaisyDisk 靠一张圆环图活 20 年，CleanMyMac 把 Space Lens 放进 Plus 档）、云盘（CleanMyMac Plus 的 Cloud Cleanup、Cleaner One 的云清理）。**「省空间」这个卖点只能换来免费用户。**

**4. 付费墙位置是本赛道最好用的分类器，全赛道只有三档，且墙位越靠后口碑越差。**
用量墙（BuhoCleaner 免费版限清 3GB、CleanMyMac 免费版单文件 500MB 上限、MacKeeper 每工具免费修 1 次）→ 功能墙（CCleaner Free 无自动化、Cleaner One 免费版不能删应用）→ **纯订阅无免费可用层**（MacKeeper、MacBooster 免费版只能扫不能修）。
口碑排序与墙位排序完全一致：**BuhoCleaner 4.8 > CleanMyMac 4.7 = DaisyDisk 4.7 > MacKeeper 4.3 > Cleaner One 3.5**。

**5. 最赚钱的公司不靠清理赚钱。**
- **Gen Digital**（CCleaner 母公司）FY2026 营收 **$50.0 亿**，CCleaner 估占仅 **≈5%**（≈¥14 亿）——它是安全订阅与金融身份服务的获客钩子，Mac 版的 CleanMyMac 竞品策略甚至被评测界判为"2026 年没有理由选它"。
- **趋势科技 / Intego** 把清理当作安全套件里的一个 SKU（Cleaner One Pro / SmartClean）。
- **名科国际（08100.HK，持 IObit / MacBooster）** 2025 全年营收 **HK$8,895.7 万（≈¥7,620 万）**，其中软件业务 **HK$8,157.7 万（≈¥6,988 万，占 91.7%）**，分部溢利 **HK$1,871 万**，由盈转亏（净亏 HK$74.1 万）——**一家上市公司接近全部收入来自"清理+杀毒"工具，年收入不到 7,000 万人民币，这就是本赛道单点工具的天花板锚点。**

**6. 中国区是全场最特殊的一格：免费产品是事实标准，而 CleanMyMac 被迫做了美区没有的动作。**
CleanMyMac 在中国区把付费墙切成 **Basic ¥199/年 / Plus ¥388/年**（美区只按 1/2/5 台设备分档，不做功能分档）。同一个产品在不同市场的付费墙位置不同，恰恰说明它在中文市场承受着免费替代的结构性压力——**而腾讯柠檬清理提供了中文区唯一的"全功能免费 + 原生本地化"选项。**

**7. 最清晰的空位：没有一个竞品把「清理」做成「可验证的清理」。**
全部 11 个主体都只回答「删了多少 GB」，**没有一个回答三个更重要的问题**：删了会不会坏？能不能回滚？清理前后系统是否真的变快？这与备份赛道「恢复验证」是结构同构的空位（92% 有备份但 31% 恢复失败 → 恢复验证成为新付费层）。

---

## 一、竞品地图：按「价值锚点 + 距系统内核距离」分五层

**分层原则**：不按功能分类（会导致混层分析错误），而按「谁在付钱 + 价值锚在什么焦虑上」分层。

| 层 | 定位 | 价格区间（年化） | 代表产品 | 价值锚点 | 付费主体 |
|---|---|---|---|---|---|
| **L0** | 系统内置 | ¥0 | macOS 存储管理 / XProtect / 快照 / Time Machine | 零成本、零学习 | Apple（不收费） |
| **L1** | 免费 / 开源单点 | **¥0** | **腾讯柠檬清理**、OnyX、AppCleaner、GrandPerspective、Pearcleaner、OmniDiskSweeper | 零成本 + 掌控感 + 纯粹 | 无（donation / 生态导流） |
| **L2** | 买断制极简单点 | ¥4–116 | DaisyDisk（$9.99）、Sensei 买断（$59）、Nektony 单品（$19.90）、GrandPerspective MAS（$2.99）、BuhoCleaner 终身（¥78） | **可视化 + 一次交付** | 个人用户（厌恶订阅） |
| **L3** | 订阅制一站式套件 | ¥68–1,209 | **CleanMyMac 5**、MacBooster 8、MacCleaner Pro、BuhoCleaner 订阅、Cleaner One Pro、CCleaner for Mac | **认知卸载 + 一站式** | 个人 / 家庭 / 小企业 |
| **L4** | 安全厂商把清理当钩子 | ¥262–497 | **MacKeeper**（Clario）、Intego ONE、AVG TuneUp、Avast Cleanup | **安全感（AV + VPN + ID）** | 个人（安全预算） |
| **L5** | 套装分销 | ¥1,209 | **Setapp**（270+ 应用，$14.99/月起） | 多应用打包 | 个人 / 自由职业 |

**读法**：本赛道没有"垂直细分"的竞品。所有付费产品都在回答同一个问题——**"除了删文件，我还能给你什么？"** 答案分成三类：更多功能（L3）、更安全（L4）、更好看（L2）。**没有一家提供"更可信"。**

---

## 二、竞品全功能点枚举

### 2.1 一览表（11 个付费主体 + 6 个免费层）

| # | 产品 | 开发方 / 归属 | 最新版本 | 计费 | 标价（1 台 Mac） | 折年 ¥ | 墙型 |
|---|---|---|---|---|---|---|---|
| 1 | **CleanMyMac 5**（基准） | MacPaw（UA/US） | 5.6.0 / 2026-08-21 | 订阅 + 买断 | **$39.95/年**；$119.95 买断；中国 Basic ¥199 / Plus ¥388 | **268** | 用量墙（单文件 500MB 上限） |
| 2 | **MacBooster 8** | IObit / 名科国际 08100.HK | 8.3.0 / 2026-05 | 订阅（无终身） | **$29.95/年** Standard（1 台）；$49.95/年 Premium（3 台）；$79.95 Lite 终身（3 台） | **201** | 无免费可用层（免费版只能扫） |
| 3 | **MacKeeper** | Clario Tech FZCO（迪拜） | 7.8 / 2026-09 | **纯订阅** | **$38.99–$107.99/年**；常见档 $71.40/年（1 台）、$89.40/年（3 台）；$10.95/月 | **262–480** | 无免费层（每工具免费修 1 次） |
| 4 | **BuhoCleaner** | Dr.Buho Inc. 布霍科技（中国，2020） | 1.16.1 / 2026-05-18 | **买断为主** + 订阅 | 中国 **¥78 终身**（1 台）/ ¥198（3 台）/ ¥68 年；海外 $25.99 终身（原 $67.99） | **16**（终身摊 5 年） | 用量墙（免费版限清 3GB） |
| 5 | **MacCleaner Pro** | Nektony（UA） | — | 订阅 + 买断 | **$14.95/月**；$39.95/年（1 台）、$53.28（2 台）、$93.24（5 台）；买断 $85.95 / $129.95 / $199.95 | **116–268** | 试用制（未见免费层） |
| 6 | **Cleaner One Pro** | **趋势科技 Trend Micro（中国台湾）** | — | 订阅 | **$19.99/年**（1 台）；$29.99/年（5 台）；欧区 €16.99/年（原 €24.99） | **134** | 功能墙（免费版不能删应用） |
| 7 | **CCleaner for Mac** | Piriform / **Gen Digital** | — | 订阅 | 免费 / Professional / Professional Plus；**€44.95/年** Pro、€64.95/年 Pro Plus（3 设备）、€64.95 Premium Bundle（5 设备） | **344–497** | 功能墙（Free 无自动化） |
| 8 | **Sensei** | Cindori（SE） | — | 买断 + 订阅 | **$59 买断**（3 台）/ **$29 年**（3 台） | **79–195** | 试用制 |
| 9 | **DaisyDisk** | Software Ambience（UA） | 4.34.2 / 2026-07-10 | **纯买断** | **$9.99 一次性**（5 台 Mac，终身） | **13** | 功能墙（免费版只能扫不能删） |
| 10 | **Intego ONE** | Intego（US，25 年） | — | 纯订阅 | Essential $56.24/2 年；**Advanced（含 SmartClean）$90.99/2 年**；Complete $97.49/2 年 | **306**（Advanced） | 功能墙 |
| 11 | **Setapp** | MacPaw（UA/US） | — | 订阅 | **$14.99/月**（1 Mac）/ $18.99（Mac+iOS）/ $22.99（4 Mac+4 iOS） | **1,209** | 无（纯订阅打包） |
| — | **腾讯柠檬清理** | 腾讯（中国） | 5.3.3 / 2026-06-01 | **完全免费** | **¥0** | **0** | 无墙 |
| — | OnyX | Titanium Software（FR，2003–） | 5.1.0 / 2026-09-15 | **免费** | ¥0（donation） | 0 | 无墙 |
| — | AppCleaner | FreeMacSoft | — | **免费** | ¥0（donation） | 0 | 无墙 |
| — | GrandPerspective | 开源（GPL） | 3.8.1 / 2026-09-13 | **免费 / $2.99 MAS** | ¥0 / $2.99 | 0–4 | 无墙 |
| — | OmniDiskSweeper | The Omni Group | — | **免费** | ¥0 | 0 | 无墙 |
| — | Pearcleaner | 开源（Apache-2.0 + Commons Clause） | v5.1.1 / 2025-09-30 | **免费** | ¥0 | 0 | 无墙；**⚠️ 项目状态 On Hold** |

### 2.2 逐产品功能点拆解

#### ① CleanMyMac 5（基准，MacPaw）
| 模块 | 子功能 |
|---|---|
| Smart Care | 5 项核心动作一键执行（清理 / 保护 / 提速 / 应用 / 文件） |
| Cleanup | System Junk、Mail Attachments、Trash Bins、Large & Old Files、Universal Binaries、**Cloud Cleanup（Plus 档）** |
| Protection | **Malware Removal（Moonlock 引擎，宣称检出 99%）**、Privacy（浏览痕迹、应用权限）、**Safety Database** |
| Speed | Optimization（登录项 / 后台项）、Maintenance Scripts（含 Spotlight/Mail 重建） |
| Applications | Uninstaller（含残留）、**Updater（App Store + 第三方）**、Extensions 管理 |
| Files | **Space Lens（Plus 档）**、Duplicates、Similar Images、**Shredder** |
| 其他 | 菜单栏健康监控、Mac 健康指数、GPU/CPU/电池详情、Apple 公证、iF Design Award |

**官方宣称数据**：29,000,000 次下载；4.7 分（3,333 条评价）；18 年 Mac 经验（2008–2026）；月均清理 35M GB、移除 328K 威胁、9.8M 次提速。

#### ② MacBooster 8（IObit / 名科国际 08100.HK）
| 模块 | 子功能 |
|---|---|
| 深度系统清理 | **System Junk（20+ 类垃圾）**、Large & Old Files、Duplicate Finder、Photo Sweeper（相似/隐藏副本） |
| 性能提升 | **Turbo Boost（磁盘权限修复 + 存储优化）**、Memory Clean、Startup Optimization |
| 安全保护 | **Virus Scan、Malware Removal、Real-time Protection、Privacy Protection（恶意 cookie）**、实时防火墙监控（8.3.0 新增） |
| 监控 | 实时 CPU / RAM / 磁盘监控 |

**关键差异**：五款清洁工具 + 内置杀毒是 MacBooster 唯一甩开免费替代的地方；但商业模式是**纯订阅、无终身**（8.3.0 依旧报 "Subscription only — no lifetime license"），且 MacUpdate 口碑偏混（第三方转载站记 3.8/5，**来源不可作为一手依据**）。

#### ③ MacKeeper（Clario Tech FZCO，迪拜）
| 模块 | 子功能 |
|---|---|
| Cleaning | Junk files、**Duplicate Finder**、Smart Uninstaller |
| Performance | Memory Cleaner、App Updates、Startup Items |
| Security | **Real-time Antivirus（AV-TEST 6/6，检出率 99.7%）**、Adware Cleaner |
| Privacy | **VPN Private Connect（无限流量）**、**StopAd 广告拦截**、**ID Theft Guard（24/7 监控邮箱/SSN/信用卡泄露）** |
| 服务 | **24/7 内置人工技术聊天**、MacKeeper Premium Services（人工远程支持，价格面议） |

**关键背景**：Zeobit → Kromtech → **Clario（2019 年末接手）** 三次易主；2014 年 Zeobit 因欺诈广告向 FTC 缴纳 **$200 万**和解金；当前 Apple 公证 + ISO 27001 + AppEsteem。宣称 **60,000,000+ 下载、150+ 国家**。

#### ④ BuhoCleaner（Dr.Buho Inc. / 布霍科技，中国，2020）
| 模块 | 子功能 |
|---|---|
| Flash Clean | 一键清 application / browser / system junk + **purgeable space（可清除空间）** |
| Disk Space Analyzer | 可视化磁盘占用 + 大文件一键删 |
| App Uninstall | 彻底卸载 + **孤儿残留**、批量（同开发者）卸载、Microsoft 365 专用流程 |
| Duplicates | 重复文件 + **相似照片** |
| Speed Boost | 释放 RAM、停用失效/隐藏登录项、Flush DNS、Reindex Spotlight、Reindex Mail |
| 工具集 | **File Shredder（不可恢复删除）**、**Xcode 缓存/模拟器清理**、菜单栏监控（CPU/温度/风扇/WiFi/磁盘） |
| 商业 | 免费版限清 **3GB**；中国区 ¥78 终身（1 台）；海外 $25.99 终身（原 $67.99）；**10 台商务终身 ¥288/598** |

**宣称数据**：1,000,000+ 下载；100,000+ 满意用户；180+ 国家；380+ 媒体推荐；**Trustpilot 4.8/5**（同类最高）；App Store 4.8/5。团队 1–10 人（BeginDot），CEO Andy Est。2026 年才正式进入国内市场。

#### ⑤ Nektony MacCleaner Pro（6 件套）
| 组成 | 子功能 |
|---|---|
| App Cleaner & Uninstaller | 彻底卸载、重置应用设置、清残留、启动项与扩展管理、应用更新 |
| Duplicate File Finder | 重复文件/文件夹、相似照片、文件夹合并、指定文件比对 |
| Disk Space Analyzer | 磁盘占用分析、最大文件/文件夹、旧文件、隐藏大文件 |
| Cleanup / Speed 组件 | 系统与缓存清理、Mail 附件、截图、本地化文件、压缩包；RAM 释放、重载 Mail/Spotlight、浏览器扩展 |
| 渠道 | 官网 + **Setapp** + Mac App Store；**支持订阅与一次性买断双轨** |

**宣称**：最多释放 50GB、提速最高 30%；装机 **11,800,000+**、16 款 App、15 年（官网自述）。Nektony 单品 App Cleaner & Uninstaller 单独卖 **$19.90 买断**，且被趋势科技官方博客列为"App 卸载单项最优"。

#### ⑥ Cleaner One Pro（趋势科技 Trend Micro，中国台湾）
| 模块 | 子功能 |
|---|---|
| Smart Scan | 存储 / 系统健康 / 未使用应用三合一总览 |
| Toolbar | 菜单栏实时 CPU / 网络 / 内存 + 一键清垃圾 |
| Cleaning | 垃圾、**隐藏残留**、重复文件、**相似照片（按内容而非文件名比对）**、大文件 |
| Disk Map | 可视化磁盘占用 |
| 应用管理 | 批量卸载应用 + 残留 |
| 工具 | **File Shredder**、启动项管理、RAM 释放、**漏洞扫描与软件更新** |
| 渠道 | Windows / Mac / iOS 三端；**免费版可扫不可删应用** |

#### ⑦ CCleaner for Mac（Piriform / Gen Digital）— 本组最弱
| 模块 | 子功能 |
|---|---|
| Clean Clutter | 系统垃圾 + 下载文件 |
| Browser Cleaner | 浏览历史 + 自动填充密码等敏感数据 + 定时自动清 |
| Find Duplicates | 重复文件 |
| Analyze Photos | **模糊/欠曝/相似照片**（Professional 独有） |
| Uninstall Apps / Manage Startup | 卸载冗余应用、启动项管理 |
| 云端与更新 | **Cloud cleaning（Google Drive / OneDrive）**、Driver Updater、Performance Optimizer（以上均为跨平台版能力） |

**关键判断**：Mac 版功能明显薄于竞品——**无应用卸载的独立性、界面投资不足、免费版带广告**。第三方评测原话：*"2026 年 Mac 上没有任何理由选 CCleaner"*、"大多数 Mac 高阶用户在 2017 年后就悄悄换掉了"。它的价值不在产品，在 Gen Digital 的分发与品牌。

#### ⑧ Sensei（Cindori）
| 模块 | 子功能 |
|---|---|
| Monitor | 菜单栏实时 CPU / GPU / 电池健康 / 存储；**可自定义监控仪表盘与编辑器** |
| Cleanup | 系统垃圾、旧缓存、系统日志、大下载、残留安装包；**App Uninstaller（含残留）** |
| Hardware | **S.M.A.R.T. 硬盘健康报告**、电池循环/容量、温度传感器与风扇转速、**磁盘读写基准测试**、**SSD Trim 开关** |

**定位**：唯一把"硬件健康监控"当主价值的竞品。$59 买断 / $29 年，均 3 台 Mac。

#### ⑨ DaisyDisk（Software Ambience）— 单点极致样本
| 模块 | 子功能 |
|---|---|
| 可视化 | 圆环式磁盘占用图（交互式下钻） |
| 准确计价 | **精确空间计算（排除克隆与硬链接）、以管理员身份扫描** |
| 破案能力 | **拆解 "Other" 与 "System Data"**、**管理并清除 macOS 快照（snapshots）** |
| 云盘 | 远程扫描 Dropbox / Google Drive / OneDrive / Box |
| 体验 | 空格键即时预览、多磁盘（内置/外置/RAID/网络/虚拟）、扫描速度 15 秒 vs Finder 3–6 分钟 |
| 商业 | **$9.99 一次性 / 5 台 / 终身**，30 天退款，**无订阅** |

**Apple 背书（本组唯一）**：App Store **"Editors' Choice"**、三次"年度最佳 App"；**26,200 名 Apple 与 Pixar 员工在使用**；638 篇媒体评测；App Store 4.7 分（3,691 条评分）。

#### ⑩ Intego ONE（美国，25 年）
| 模块 | 子功能 |
|---|---|
| Antivirus | 实时防护、Safe List、快速扫描、定时扫描、病毒库自动更新（AV-TEST / AV Comparatives / VB100 认证） |
| Firewall | Smart Firewall、连接监控、自定义规则 |
| **SmartClean** | 垃圾/缓存/残留清理、完整卸载（含隐藏文件）、日志清理、存储分析、**内存与 CPU 优化** |
| VPN | 全球服务器、Lightway 协议、无日志政策 |

**定价**：Essential $56.24/2 年、**Advanced（含 SmartClean）$90.99/2 年**、Complete $97.49/2 年；续费按 $129.99–149.99/年。

#### ⑪ Setapp（MacPaw，L5 分销层）
270+ Mac/iOS 应用一价全包；$14.99/月（1 Mac）、$18.99（1 Mac + 4 iOS）、$22.99（4 Mac + 4 iOS）；7 天免费试用。**新增双轨分成**：Single App 85/15（可含一次性买断）vs Membership 70/30（按用量分成）。地理分布：北美 33% / 欧洲 43.7% / 拉美 6.4% / 其他 16.5%。

**为什么列它**：它是本赛道**唯一能让清理工具获得高 ARPU 的结构**——CleanMyMac、MacCleaner Pro、Gemini 2 都在里面，用户为"打包"付 $180/年，但**没有一分钱是"为清理付的"**。

#### 免费层（L1）——必须逐项过，否则会把已免费的能力误判为差异化

| 产品 | 定位 | 能力边界 | 可持续性信号 |
|---|---|---|---|
| **腾讯柠檬清理** | **中国区事实标准** | 系统/应用垃圾、大文件、重复文件、相似照片、浏览器隐私、应用卸载、磁盘可视化、状态栏监控（CPU/风扇/温度）、**摄像头麦克风调用提示**、**一键搬家**、**微信/QQ/企业微信/Xcode/Sketch 逐一 Zoo 定制清理**、文档时光机 | 🟢 活跃（5.3.3 / 2026-06-01）；已并入「腾讯电脑管家 for Mac」（增病毒查杀）；**GitHub 仓库为只读开源** |
| OnyX（Titanium Software） | 面向技术用户 | 验证系统文件结构、清理与维护、卸载、**配置 Finder/Dock/Safari 参数**、删缓存、重建数据库与索引；**每个 macOS 大版本一个专用版本** | 🟢 活跃（5.1.0 / 2026-09-15，支持 macOS 27 "Golden Gate"）；2003 年至今，**单开发者 + donation** |
| AppCleaner（FreeMacSoft） | 只做卸载 | 彻底卸载 + 残留清理、SmartDelete、保护应用、Widget | 🟢 长期稳定；donation |
| GrandPerspective | 只做可视化 | **Treemap 磁盘占用图**、30+ 颜色映射方案、高级过滤测试、**硬链接分析（可分析 Time Machine 备份）**、云文件分析、导出图片/文本 | 🟢 活跃（3.8.1 / 2026-09-13）；**GPL，2025-09 刚满 20 周年**；SourceForge 免费 vs MAS $2.99 同款 |
| OmniDiskSweeper | 只做可视化 | 按大小列出文件/文件夹 | 🟢 The Omni Group 免费赠品 |
| Pearcleaner | 只做卸载 + 极客向 | App Uninstall、**孤儿文件搜索**、开发环境管理、Homebrew 管理、App Lipo（剥离多余架构）、PKG/插件/服务管理、**Sentinel Monitor（入废纸篓自动清，占用 ~2MB RAM）**、Steam 游戏支持、CLI | 🔴 **项目状态 On Hold**；Apache-2.0 + Commons Clause（**明确禁止任何形式的商业化**） |

---

## 三、功能点 × 竞品覆盖矩阵

行 = 功能模块；列 = 主要竞品；✅ 完整 / ⚠️ 部分或弱 / ❌ 无

| 功能模块 | CleanMyMac | MacBooster | MacKeeper | BuhoCleaner | MacCleaner Pro | Cleaner One | CCleaner Mac | Sensei | DaisyDisk | 柠檬清理 | OnyX | AppCleaner | Pearcleaner |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 系统垃圾清理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| 应用卸载 + 残留 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 大文件 / 旧文件 | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ✅ | ✅ | ❌ | ❌ | ⚠️ |
| 重复文件 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 相似照片 | ✅ | ✅ | ⚠️ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **磁盘可视化** | ✅（Plus） | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅✅ | ✅ | ❌ | ❌ | ❌ |
| 内存清理 | ⚠️ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 启动项管理 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ⚠️ |
| 应用更新 | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ✅ |
| 文件粉碎机 | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 浏览器隐私清理 | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅✅ | ❌ | ❌ | ✅ | ⚠️ | ❌ | ❌ |
| **云盘清理** | ✅（Plus） | ❌ | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **恶意软件防护** | ⚠️ | ✅ | ✅✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️（管家版） | ❌ | ❌ | ❌ |
| **VPN / ID 监控** | ❌ | ❌ | ✅✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **硬件健康监控** | ⚠️ | ✅ | ⚠️ | ✅ | ❌ | ⚠️ | ❌ | ✅✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| 系统参数 / 维护脚本 | ⚠️ | ⚠️ | ❌ | ⚠️ | ✅ | ❌ | ❌ | ⚠️ | ❌ | ⚠️ | ✅✅ | ❌ | ❌ |
| 开发者专项（Xcode/Docker） | ⚠️（Xcode 缓存） | ❌ | ❌ | ✅（Xcode） | ❌ | ❌ | ❌ | ❌ | ❌ | ✅✅（Xcode） | ❌ | ❌ | ✅ |
| 中文 IM 定制清理 | ❌ | ❌ | ❌ | ⚠️ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅✅ | ❌ | ❌ | ❌ |
| CLI | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| **可回滚 / 可验证清理** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**矩阵的三个读法**：

1. **前六行（垃圾/卸载/大文件/重复/相似照片/内存）几乎全绿** → 功能同质化已到极致，**不是差异化空间所在**。
2. **最下面的「可回滚 / 可验证清理」整行全红** → 全赛道唯一的结构性空位（详见第八章）。
3. **「中文 IM 定制清理」只有腾讯柠檬一家全占，且是✅✅** → 这是被严重低估的护城河：**唯一让免费产品在中文区打败付费产品的机制，不是价格，是"能清微信"。**

---

## 四、核心价值拆解（本报告要回答的核心问题）

### 4.1 五类价值锚点

竞品们卖的东西，剥到底只有五类：

| # | 价值锚点 | 用户真实诉求 | 谁把它做到极致 | 商业可提取性 | 对应收入形态 |
|---|---|---|---|---|---|
| **V1** | **认知卸载** | "我该删什么？" → "点一下" | CleanMyMac Smart Care、柠檬清理一键、BuhoCleaner Flash Clean、MacKeeper 状态圆环 | **中** | 订阅（套件） |
| **V2** | **可视化** | "空间去哪了？" → 看见就能处理 | **DaisyDisk**、GrandPerspective、Space Lens、Disk Map | 中（**但撑不起订阅**） | 一次性买断 |
| **V3** | **安全感** | "删了会不会坏？" + "有没有病毒？" | **MacKeeper / Intego / MacBooster**（AV + VPN + ID）、CleanMyMac（Safety Database + Moonlock） | **强**（有持续成本项） | 高价订阅 |
| **V4** | **可量化的省空间** | "给我一个 GB 数字" | 所有产品的宣传页 | **弱**（缓存可再生，无持续理由） | 免费 / 极低价 |
| **V5** | **掌控感 / 身份** | "我要自己决定，不要你替我做" | **OnyX**、CLI 工具、Pearcleaner | 弱（但换忠诚度） | donation / 免费 |

**判别法（可直接复用）**：
> **同一款产品里，价值锚点越靠 V1/V2/V3，ARPU 越高；越靠 V4，越接近免费。功能数量与 ARPU 无关。**
>
> 极端实证：DaisyDisk 只有 **1 个功能**，ARPU ¥13；CleanMyMac 有 **25+ 个功能**，ARPU ¥268（20 倍）。但 DaisyDisk 的 1 个功能属于 **V2（可视化）**，CleanMyMac 的 25 个里有 20 个属于 **V4（省空间）** —— CleanMyMac 的溢价来自它把 V1/V2/V3 打包进了一个按钮。

### 4.2 价值锚点 × 产品定位象限

```
        高商业可提取性
              ↑
              │   V3 安全感                 V1 认知卸载
              │   MacKeeper(¥480)          CleanMyMac(¥268)
              │   Intego(¥306)             MacCleaner Pro(¥268)
              │   MacBooster(¥201)         BuhoCleaner订阅(¥68)
              │        ┌─────── Setapp(¥1,209) ───────┐
              │        │  （打包，非工具本身价值）    │
              │
   ───────────┼──────────────────────────────────────→  用户价值感知
              │
              │   V5 掌控感                 V2 可视化
              │   OnyX(¥0)                  DaisyDisk(¥13)
              │   Pearcleaner(¥0)           Sensei(¥79)
              │   AppCleaner(¥0)            GrandPerspective(¥0–4)
              │   V4 省空间
              │   柠檬清理(¥0)
              │   CCleaner Free(¥0)
              ↓
        低商业可提取性
```

**象限解读**：
- **右上（V1 认知卸载）** = 本赛道唯一能规模化收订阅的位置 → 但竞争者最多、功能最容易同质化。
- **左上（V3 安全感）** = **ARPU 最高的位置（Setapp 之下）**，因为它是唯一"有持续交付成本"的锚点（病毒库、VPN 带宽、ID 监控数据源）→ 所以 MacKeeper/Intego/Gen Digital 能收 ¥300–500 而不被骂。
- **右下（V2 可视化）** = 口碑最好但收不到订阅 → 只能买断，天花板明确。
- **左下（V4/V5）** = 免费区，**柠檬清理和 OnyX 就住在这里，而且住得很舒服**。

### 4.3 因果链：为什么「清理」本身不值钱

这是本报告最需要讲清楚的一条。**三家独立主体从三个方向给出同一个结论**：

| 力量 | 证据 | 对定价的影响 |
|---|---|---|
| **① macOS 自愈** | DaisyDisk 官网把 "cleaner app" 做成对照表：通常只恢复 **1–5GB**、删的是缓存（**体积不见得大**）、瞄准的是**预定义文件**、**缓存很快会重新出现**、**可能损坏系统**、"Recommended by Apple: **No**"。反观 DaisyDisk：**10–100GB+**、删的是真占地方的文件、**永久删除**、**Apple 推荐: Yes** | 大厂用"官方背书"把"一键清理"打成伪需求 |
| **② 免费 + 本地化** | 腾讯柠檬清理：完全免费 + 微信/QQ/Xcode/Sketch 定制 + 内存清理 + 状态栏监控 + **文档时光机**。中文区用户实测口径："**用了一段时间后，我果断卸载了 CleanMyMac，把省下的 300 块钱拿去买了杯咖啡**" | 中文区中间层价格 → **¥0** |
| **③ 缓存可再生** | 所有竞品的宣传数字都是"本次释放 X GB"——**这是一次性收益，不是持续交付** | 用户无重复付费理由 → 续订率天然低 |

**合成结论（本赛道的定价铁律）**：
> **只做「清理」的产品，定价天花板 = ¥0。**
> 要越过 ¥0，必须在清理之外**至少迁移到一个有持续成本或强感知的锚点**：安全（V3）、可视化（V2）、云盘、多设备、或开发工具专项。

**验证**：11 个付费主体里，**没有一个的付费理由是"清理得更干净"**。MacKeeper 卖 VPN + AV + ID 监控；Intego 卖 AV + FW；MacBooster 卖杀毒；Cleaner One 卖 Disk Map + 相似照片；Sensei 卖硬盘健康；DaisyDisk 卖可视化；BuhoCleaner 卖"买断不订阅"；CCleaner 卖品牌与跨平台捆绑；Setapp 卖打包。**CleanMyMac 是唯一还敢把"清理"本身写进付费墙的（Plus 档的 Cloud Cleanup），而它为此付出了中国区被迫做功能分档的代价。**

---

## 五、定价与商业化对标 + ARPU 断层

### 5.1 折年 ARPU 断层（¥0 → ¥1,209，约 90 倍）

| 产品 | 计费结构 | 折年 ARPU | 相对断层 |
|---|---|---|---|
| 腾讯柠檬清理 / OnyX / AppCleaner / Pearcleaner / OmniDiskSweeper | 免费 | **¥0** | 基准 |
| GrandPerspective（SourceForge 免费 / MAS $2.99） | 免费 / 买断摊 5 年 | **¥0–4** | 1.0× |
| DaisyDisk | 买断 $9.99 / 5 台摊 5 年 | **¥13** | 3.3× |
| **BuhoCleaner 终身** | 买断 ¥78 / 1 台摊 5 年 | **¥16** | 4.0× |
| BuhoCleaner 年订阅 | ¥68/年 | **¥68** | 17× |
| Sensei 买断 | $59 / 3 台摊 5 年 | **¥79** | 20× |
| MacCleaner Pro 买断 | $85.95 摊 5 年 | **¥116** | 29× |
| Cleaner One Pro | $19.99/年 | **¥134** | 34× |
| Sensei 订阅 | $29/年 3 台 | **¥195** | 49× |
| **CleanMyMac 中国 Basic** | ¥199/年 | **¥199** | 50× |
| MacBooster Standard | $29.95/年 | **¥201** | 50× |
| MacKeeper 促销档 | $38.99/年 | **¥262** | 66× |
| **CleanMyMac 美区** | $39.95/年 | **¥268** | 67× |
| MacCleaner Pro 订阅 | $39.95/年 | **¥268** | 67× |
| **CleanMyMac 中国 Plus** | ¥388/年 | **¥388** | 97× |
| Intego ONE Advanced | $90.99/2 年 | **¥306** | 77× |
| CCleaner Mac Pro | €44.95/年 | **¥344** | 86× |
| MacKeeper 常规档 | $71.40/年 | **¥480** | 120× |
| CCleaner Pro Plus（3 设备） | €64.95/年 | **¥497** | 124× |
| **Setapp Mac 会员** | $14.99/月 | **¥1,209** | **302×** |

> **断层由「付费理由强度 × 计费结构 × 人群净值 × 计价货币」四项决定，与功能数量无关。**
> 最强单点对照：**BuhoCleaner 终身 ¥16 vs CleanMyMac 订阅 ¥268（17 倍），两者功能重合度约 85%。** 差值 100% 来自计费结构（买断 vs 订阅）+ 品牌溢价。

### 5.2 商业化程度分级（L0–L5）

| 级别 | 定义 | 产品 | 收入证据硬度 |
|---|---|---|---|
| **L5 套装生态** | 工具被打包进更大的订阅体系 | **Setapp**（¥1,209，270+ 应用） | 软（无单独披露） |
| **L4 大厂钩子** | 清理只是安全/身份业务的获客入口 | **CCleaner**（Gen Digital FY26 $50.0 亿，CCleaner ≈5%）、**MacKeeper**（Clario 未披露）、**Intego**（未披露）、**Cleaner One**（趋势科技未拆分） | 硬（Gen）/ 缺口（其余） |
| **L3 独立订阅套件** | 自有品牌订阅，有真实续费 | **CleanMyMac**（MacPaw FY24 $90.2M，CleanMyMac ≈80%）、**MacBooster**（名科国际软件业务 HK$8,158 万）、**MacCleaner Pro**（Nektony 未披露） | **硬**（MacPaw 审计）/ 硬（名科上市年报） |
| **L2 买断制** | 一次性授权，无续费 | **DaisyDisk**、**Sensei**、**BuhoCleaner 终身**、Nektony 单品 | 缺口（全部未披露） |
| **L1 免费 / donation** | 无商业化 | **OnyX**、**AppCleaner**、**GrandPerspective**、**Pearcleaner** | 硬（donation 页） |
| **L0 生态导流** | 不靠工具收入，靠流量/装机/生态 | **腾讯柠檬清理** | 缺口（并入管家体系） |

### 5.3 公司层财务锚点（唯一经审计的三家）

| 主体 | 归属产品 | FY/年度 | 收入 | 利润 | 与清理业务的关系 |
|---|---|---|---|---|---|
| **Gen Digital（GEN）** | CCleaner | FY2026 | **$50.0 亿**（+27%） | 净利 $9.73 亿 | **CCleaner 估占 ≈5%（≈¥14 亿）**；主体是 Cyber Safety（61% 营业利润率）+ Trust-Based（LifeLock / MoneyLion） |
| **MacPaw Family Ltd** | CleanMyMac / Setapp / Gemini 2 | FY2024（审计） | **$90,211,688（≈¥6.06 亿）** | **净亏 $13,147,167**（首亏） | **CleanMyMac ≈80%（≈$7,217 万 ≈ ¥4.85 亿）**；Setapp ≈15% |
| **名科国际 08100.HK** | MacBooster（IObit） | 2025 | **HK$8,895.7 万（≈¥7,620 万）**，-14.7% | 净亏 HK$74.1 万（由盈转亏） | **软件业务 HK$8,157.7 万（≈¥6,988 万，占 91.7%）**，分部溢利 HK$1,871 万；企业管理/IT 合约服务 HK$738 万（-65.4%，亏 HK$557 万）；净资产 HK$2.02 亿 |
| **Clario Tech FZCO** | MacKeeper | — | 未披露 | 未披露 | 仅知 60M+ 下载、150+ 国家 |
| **趋势科技** | Cleaner One Pro | — | 未拆分 | — | 清理是安全套件的一个 SKU |
| **Dr.Buho Inc.** | BuhoCleaner | 2020– | 未披露 | 未披露 | 1M+ 下载、10 万+ 用户；1–10 人团队 |
| **Nektony** | MacCleaner Pro | — | 未披露 | — | 11.8M+ 装机（自述）、16 款 App |
| **Software Ambience** | DaisyDisk | — | 未披露 | — | 单产品公司 |
| **Titanium Software** | OnyX | 2003– | 0（donation） | — | 单开发者 |
| **FreeMacSoft** | AppCleaner | — | 0（donation） | — | 单开发者 |

**三条公司层读数**：
1. **清理工具单独存在时，天花板是 HK$8,158 万（≈¥6,988 万）年收入**——名科国际用一个上市公司的体量、5 亿次累计下载，把它做到了这个数，还亏了钱。
2. **一旦挂到安全业务上，同样的清理功能可以撑起 $50 亿营收**（Gen Digital）——但清理本身贡献只占 5%。
3. **MacPaw 的 ~80% 集中度是风险也是样本**：它证明了"单 SKU 撑一家公司"在清理赛道**是可能的，但要用设计 + 生态（Setapp）+ 18 年品牌来换**，且 AI 转型一年就让它首亏 $1,314 万。

### 5.4 计费结构对照（本赛道最值得记的一张表）

| 结构 | 代表 | 优点 | 缺点 | 实证 |
|---|---|---|---|---|
| **纯买断** | DaisyDisk $9.99、BuhoCleaner ¥78、Sensei $59 | 口碑最好；转化摩擦最低 | **永久封印续费收入** | DaisyDisk 被 Apple 收录、26,200 名 Apple 员工在用，但公司只靠这一款 $9.99 产品 |
| **纯订阅** | MacKeeper $38.99–107.99、MacBooster $29.95、CCleaner €44.95 | 现金流可预测；能摊持续成本（AV/VPN） | 口碑最差；**必须靠持续成本项自证合理** | MacKeeper Trustpilot 4.3（最低档）；被指"最贵" |
| **买断 + 订阅双轨** | CleanMyMac（$39.95/年 vs $119.95 买断）、Nektony（$39.95/年 vs $85.95 买断）、BuhoCleaner（¥68/年 vs ¥78 终身） | 覆盖两种心态 | **自我矛盾**：BuhoCleaner 终身 ¥78 vs 年费 ¥68 → **1.15 年回本**，理性用户必选买断；CleanMyMac $119.95 vs $39.95 → **3.0 年回本** | 已在 CleanMyMac 报告中作为"定价自我矛盾"记录 |
| **免费 + 生态** | 腾讯柠檬清理 | 心智占领最快 | 不产生直接收入 | 中文区事实标准 |

> **衍生规则（第三次验证）**：**买断回本周期 < 3 年时，年费 SKU 纯属价格锚点道具，且永久封印续费收入。** BuhoCleaner 的 ¥78 终身 / ¥68 年 = 1.15 年回本，是本赛道最激进的一档——它用"极端买断"换来了 Trustpilot 4.8 的全场最高口碑，代价是几乎没有续费收入。

---

## 六、用户数据与真实口碑实测

### 6.1 规模数据（含口径标注）

| 产品 | 宣称用户/下载 | 第三方/可验证 | 评分（来源） |
|---|---|---|---|
| CleanMyMac | **29,000,000 次下载** | 官网自述 | **4.7 / 5**（3,333 条评价，官网）；MacUpdate 3.3/5（427 条，专业用户） |
| MacBooster | 5 亿次累计下载（IObit 全线）；名科国际新用户 **3,300 万/年**（2024: 3,600 万） | 上市年报 | MacUpdate 口碑"偏混"（第三方转载站记 3.8/5，**不可作一手依据**） |
| MacKeeper | **60,000,000+ 下载**、150+ 国家 | 官网自述 | **4.3 / 5**（Trustpilot）；MacKeeper 官方回复"几乎所有评论，无论好坏" |
| BuhoCleaner | **1,000,000+ 下载**、100,000+ 满意用户、180+ 国家、380+ 媒体推荐 | 官网自述 | **4.8 / 5**（Trustpilot，**全场最高**）；App Store 4.8/5 |
| MacCleaner Pro（Nektony） | **11,800,000+ 装机**、16 款 App、15 年 | 官网自述 | Trustpilot 有大量正面评价（官网引 10 条，其 Support 团队被点名） |
| Cleaner One Pro | 趋势科技全线（未拆） | — | **3.5 / 5**（MacUpdate，经竞品转引，**二手口径**） |
| DaisyDisk | **26,200 名 Apple 与 Pixar 员工在用**；638 篇媒体评测；3 次"年度最佳 App" | Apple 官方故事页 | **4.7 / 5**（App Store，3,691 条评分 / 2,912 条评论） |
| 腾讯柠檬清理 | 未披露 | 官网 + GitHub 开源 | App Store 版受限（**完整版才有应用卸载**） |
| OnyX | 2003 年至今，未披露 | — | 无商业化，无评分压力 |
| Pearcleaner | — | GitHub | **⚠️ 项目状态 On Hold** |

### 6.2 口碑断层（本次最重要的发现之一）

**评分排序与"付费墙位置 + 是否强制订阅"完全一致**：

```
口碑最好 ────────────────────────────────────────→ 口碑最差
BuhoCleaner 4.8   CleanMyMac 4.7   DaisyDisk 4.7   MacKeeper 4.3   Cleaner One 3.5
  （买断）        （用量墙）        （买断）        （无免费层）    （功能墙）
```

**规律**：
> **口碑与"功能多少"无关，与"墙位靠不靠后"和"是否强制订阅"强相关。**
> 买断制 / 宽免费层的产品口碑最好（BuhoCleaner 4.8、DaisyDisk 4.7、AppCleaner / OnyX 在极客圈近乎零差评）；纯订阅 + 激进弹窗的产品口碑最差（MacKeeper 4.3 且被反复提"最贵"、Cleaner One 3.5）。

**竞品对彼此的评价（原话，含明确攻击点）**：
- 评测界对 CCleaner Mac：*"2026 年 Mac 上没有任何理由选 CCleaner"*、*"大多数 Mac 高阶用户在 2017 年后就悄悄换掉了"*、*"没有应用卸载、界面基础、免费版带广告"*。
- 对 MacKeeper：*"品牌信任赤字仍在，不是因为当前应用不好，而是信任重建很慢"*、*"通知和购买弹窗频繁"*、*"订阅制且昂贵"*、*"重复文件查找器有时无法完成扫描"*。
- 对 CleanMyMac：*"比部分竞品更贵"*、*"占用存储空间较大"*、*"免费版限制用户删除大于 500MB 的文件"*。
- 对 Cleaner One Pro：*"无恶意软件防护、无 purgeable 空间清理、无文件恢复"*。
- 对 MacBooster：*"订阅制、无终身授权"*、*"MacUpdate 社区评价偏混"*。
- **对免费产品的原声（中文区）**：*"CleanMyMac X 的优势在于更多高级功能（如病毒扫描、系统维护脚本），但这些功能要么可以通过其他免费工具替代，要么普通用户根本用不上。"*

### 6.3 中文区用户决策路径（实测推荐矩阵）

中文区已有稳定共识，且**与厂商投入方向明显错位**：

| 用户诉求 | 中文区共识推荐 | 该产品的商业状态 |
|---|---|---|
| 功能最全、体验最好 | CleanMyMac X | 订阅 ¥199–388/年 |
| **完全免费、国产简单** | **腾讯柠檬清理** | **免费，无收入** |
| 中文无广告、全能稳定、高性价比 | BuhoCleaner | 买断 ¥78 |
| 开源干净、极客工具 | Pearcleaner | 免费，**已 On Hold** |
| 极简免费、只卸载 | AppCleaner | 免费 |

---

## 七、PM 视角：五类打法与可迁移结论

### 7.1 五类打法

| 打法 | 代表 | 获客机制 | 变现机制 | 结构性风险 |
|---|---|---|---|---|
| **A. 品牌 + 一站式 + 订阅** | CleanMyMac | 设计奖 + 18 年口碑 + Setapp 生态 + 内容营销 | 订阅 ¥199–388/年（+买断） | 功能同质化；AI 转型成本；单 SKU 80% 集中度 |
| **B. 安全钩子 + 高 ARPU** | MacKeeper、Intego、Cleaner One、CCleaner | 品牌 + 渠道预装 + 免费试用 | AV/VPN/ID 高价订阅 ¥262–497 | 口碑赤字；清理部分做不深（"扫描卡住"） |
| **C. 性价比 + 买断 + 口碑** | BuhoCleaner、DaisyDisk、Sensei | 媒体测评 + 口碑传播 + App Store 推荐 | 买断 ¥13–79 | 无续费收入；增长依赖新品 |
| **D. 免费 + 本地化 + 生态** | 腾讯柠檬清理、IObit | 免费 + 原生本地化（微信/QQ/Xcode） | 不靠工具收入；导流到管家/广告/装机 | 商业化动机缺失；一旦收钱即失去立身之本 |
| **E. 单点极简 + 开源** | OnyX、AppCleaner、GrandPerspective、Pearcleaner | 极客社区 + SourceForge/GitHub | donation ≈ 0 | **可持续性最差（Pearcleaner 已 On Hold）** |

### 7.2 可迁移结论（六条，可直接复用）

**① 功能同质化赛道的唯一差异化维度是「价值锚点」，不是功能清单。**
> 11 个主体 9 个功能重合 85%+，ARPU 差 90 倍。做竞品分析时**先问"它把价值锚在哪个焦虑上"，再数功能**。

**② 中间层（纯清理）已被三方夹击归零，不要在中间层定价。**
> OS 内置（零成本）+ 免费本地化（零成本）+ 缓存可再生（无持续理由）= 定价天花板 ¥0。

**③ 收订阅的唯一正当理由 = 有一层真实的持续交付成本。**
> 本赛道能收 ¥300–500 的三家（MacKeeper / Intego / Gen Digital）全都靠 **病毒库 + VPN 带宽 + ID 监控数据源**。反过来，纯本地工具（DaisyDisk / BuhoCleaner / Sensei）全部只能买断。**这不是营销选择，是成本结构决定的。**

**④ 口碑与"是否强制订阅"负相关；买断是口碑最优解，但封印续费。**
> 最激进买断的 BuhoCleaner 拿到 4.8，最纯订阅的 MacKeeper 拿到 4.3。**要口碑就别订阅，要现金流就接受差评——除非你能自证持续成本。**

**⑤ 本地化定制（中文 IM / 开发工具 / 设计工具）是被严重低估的护城河。**
> 唯一让免费产品在中文区打败付费产品的机制，不是价格，是**"它能清微信，CleanMyMac 不能"**。同理，开发者的 **Xcode 缓存 / 模拟器 / Docker 镜像 / node_modules** 是本赛道 ARPU 最高的清洗对象（单个 Docker 镜像可达 50GB），而目前只有腾讯柠檬与 BuhoCleaner 做到了"部分"，**没有一个产品把它做成专业线**。

**⑥ 安全厂商做清理 SKU 有天然优势：既有品牌信任（用来降低"删错"焦虑），又有持续成本项（病毒库）可以用来正当收订阅。** 这解释了为什么 L4 层能收最高价却产品最差——**用户付的不是清理能力的钱，是安全品牌的保险费。**

### 7.3 反向样本（负样本比正样本更有说服力）

| 负样本 | 事实 | 教训 |
|---|---|---|
| **CCleaner for Mac** | 母公司年入 $50 亿，Mac 版被评测界判"2026 年无理由选择" | **大厂品牌 + 渠道能给收入，但给不了 Mac 端产品力** |
| **Pearcleaner** | 功能比 AppCleaner 强得多（孤儿搜索 / Homebrew / Lipo / Sentinel），许可含 Commons Clause 明令禁止商业化 | **"功能更强 + 禁止变现" = 项目 On Hold**；开源单点工具做不到可持续 |
| **腾讯柠檬清理** | 全功能免费，但被独立评测直指"功能相对基础、个性化设置少、无付费版提供高级功能" | **免费不是终点**；缺付费层意味着缺演进动力，长期被 OS 与竞品双向挤压 |
| **MacBooster** | 唯一做杀毒的清理软件，却仍被标注"订阅制、无终身"，母公司由盈转亏 | **即便抓到 V3（安全感）锚点，也需要规模才能摊平成本；1 人公司做不到** |
| **Setapp Mobile** | 2026-02-16 关闭，运营 17 个月 | **打包模式在移动端不成立**，桌面端才是正解 |

---

## 八、产品空位与改进建议

### 8.1 三个可进场位置（按优先级）

**P0 — 可验证清理（本赛道唯一整行全红的空位）**
> 全行业都只回答"删了多少 GB"，**没有一个回答"删了会不会坏 / 能不能回滚 / 清理前后系统是否真的变快"**。
> 最小可行形态：清理前自动生成**可回滚快照**（或符号链接回收站）+ 清理后自动跑**前后性能基准对比**（启动时间 / 空闲磁盘 / 内存压力）+ 一份可分享的"清理报告"。
> 为什么成立：与备份赛道「恢复验证」结构同构（92% 有备份但 31% 恢复失败 → 恢复验证成为新付费层）。清理赛道的对应事实是——**所有产品的差评里最一致的一条就是"怕删错"，而 CleanMyMac 的 Safety Database / BuhoCleaner 的确认窗口都只是"缓解"而不是"消除"。**

**P0 — 免费层做透 + 只在"有持续成本的层"收费**
> 参照 Hasleo 分层模板：免费版只砍"企业才需要的那刀"，不砍普通用户核心体验；订阅只挂在**云盘清理 + 恶意库 + 多设备 + 同步**上。
> 反向教材：MacKeeper（无免费可用层 → 4.3 分）、CleanMyMac 免费版单文件 500MB 上限（= 隐性用量墙，被竞品当作攻击点）。

**P1 — 开发者专项清理（ARPU 最高的清洗对象，无人专业化）**
> 清洗对象：Xcode 缓存/模拟器/Archives、Docker 镜像与层、node_modules、Python venv、Gradle/Maven 缓存、Homebrew 旧版本、iOS DeviceSupport、构建产物。
> 现状：腾讯柠檬与 BuhoCleaner 各有"Xcode 一项"，CleanMyMac 只认 Xcode 缓存，**没有一个产品把"开发者磁盘"当成独立产品线**。
> 付费理由强度：单个 Docker 镜像体积可达 50GB 级，开发者时间成本高、付费能力高、且**持续产生**（有真实持续交付价值）。

**P1 — 中文 IM 深度清理商用化**
> 微信/QQ/企业微信/钉钉/飞书的聊天图片视频、缓存、备份路径是企业级痛点（已有中文区专门的"小而美备份站"需求）。腾讯柠檬做了，但**没有一家把它做成可收费产品**——因为做的人免费，付钱的人不做。

**P2 — 家庭/多设备打包**
> CleanMyMac 2 台 $63.95、5 台 $127.95；BuhoCleaner 10 台商务终身 ¥288；MacKeeper Family（3 台+1）$71.64。**多设备是本赛道最自然的加价维度**，但需要账号体系（P2 优先级低于前三条，因为它不解决价值锚点问题）。

### 8.2 应当回避的方向

| 回避项 | 原因 |
|---|---|
| **又一个"一键清理"** | 功能墙已被 6 个免费产品填满（柠檬、OnyX、AppCleaner、GrandPerspective、OmniDiskSweeper、Pearcleaner），且被 Apple 官方贬为伪需求 |
| **纯本地工具挂年费** | 没有持续交付成本 → 用户会算账 → 被免费替代吃掉（MacBooster 的困境） |
| **与安全厂商拼 AV/VPN/ID 监控** | 病毒库、VPN 带宽、ID 监控数据源都是重资产，1–10 人团队无法摊平 |
| **只做磁盘可视化** | DaisyDisk 用 $9.99 买断 + Apple 背书 + 20 年口碑把这条路走到头了，后来者只能更便宜 |
| **依赖"设计好看"做溢价** | CleanMyMac 有 iF Design Award + 18 年品牌 + Setapp 生态，才有 20 倍溢价空间；这不可复制 |

---

## 附：数据来源与口径说明

### A. 一手来源（今日实测）

| # | 数据 | 来源 |
|---|---|---|
| 1 | MacBooster 功能与定价（$29.95 / $49.95 / $79.95） | macbooster.net 官方站与官方购买页（搜索结果直引官方页文案） |
| 2 | CCleaner for Mac 功能与版本分档（FREE / PROFESSIONAL / PROFESSIONAL PLUS，1/1/3 设备） | ccleaner.com/ccleaner-mac |
| 3 | CCleaner 全平台定价（Pro €44.95、Pro Plus €64.95、Premium Bundle €64.95） | ccleaner.com/ccleaner/plans |
| 4 | MacKeeper 功能与定位 | mackeeper.com 首页、mackeeper.com/duplicate-finder |
| 5 | MacKeeper 定价与公司（$38.99–107.99/年、$10.95/月、Clario Tech FZCO 迪拜） | mackeeper.com/duplicate-finder 官方页脚 + 独立评测交叉验证 |
| 6 | BuhoCleaner 中国区定价（¥68 年 / ¥78 终身 / ¥198 三台 / ¥288·598 商务） | drbuho.com/zh-cn/store、drbuho.com/zh-tw/store |
| 7 | BuhoCleaner 海外定价（$17.99 / $25.99 / $67.99） | drbuho.com/buhontfs/buy（同站价格表） |
| 8 | BuhoCleaner 功能、规模宣称、公司背景（2020、1–10 人、CEO Andy Est） | drbuho.com 首页、drbuho.com/zh-cn/about、begindot 产品档案 |
| 9 | Nektony MacCleaner Pro 功能与定价（$14.95/月、$39.95/年、$85.95 买断） | nektony.com/mac-cleaner-pro、nektony.com/mac-cleaner-pro/buy |
| 10 | Sensei 功能与定价（$59 买断 / $29 年，3 台） | sensei.app、sensei.app/pricing |
| 11 | DaisyDisk 功能、定价（$9.99 / 5 台 / 终身）、Apple 背书、26,200 员工、4.7 分（3,691 评分） | daisydiskapp.com 首页与 support/pricing |
| 12 | Cleaner One Pro 定价（$19.99 / $29.99；€16.99 / €25.99）与功能 | trendmicro.com 产品页、shop.trendmicro.com、cleanerone.trendmicro.com |
| 13 | Intego ONE 功能与定价（Essential $56.24 / Advanced $90.99 / Complete $97.49，均 2 年） | intego.com 首页 |
| 14 | Setapp 应用数（270+）与定价（$14.99 / $18.99 / $22.99）+ 85/15 与 70/30 分成 | macpaw.com/setapp |
| 15 | CleanMyMac 5 定价（$39.95 / $63.95 / $127.95）与版本 5.6.0 | macpaw.com/store/cleanmymac、cleanmymac.com |
| 16 | 腾讯柠檬清理功能、版本 5.3.3（2026-06-01）、开源 | lemon.qq.com 官网 |
| 17 | OnyX 功能、免费、5.1.0（2026-09-15）、2003 年至今、donation | titanium-software.fr/en/onyx.html |
| 18 | AppCleaner（FreeMacSoft，免费 + donation） | freemacsoft.net/appcleaner |
| 19 | GrandPerspective 功能、GPL、3.8.1（2026-09-13）、20 周年、免费 / $2.99 MAS | grandperspectiv.sourceforge.net |
| 20 | Pearcleaner 功能、许可（Apache-2.0 + Commons Clause）、**项目 On Hold** | github.com/alienator88/Pearcleaner |
| 21 | 名科国际 2025 年报（营收 HK$8,895.7 万、软件业务 HK$8,157.7 万 91.7%、净亏 HK$74.1 万、净资产 HK$2.02 亿） | 08100.HK 年报摘要与业绩公告（etnet / 证券之星 / 老虎社区交叉验证，与年报 PDF 一致） |
| 22 | 汇率 | open.er-api.com（2026-09-28 00:02 UTC） |

### B. 二手来源（已标注，不作一手依据）

| 数据 | 来源 | 使用方式 |
|---|---|---|
| MacBooster MacUpdate 3.8/5 | 第三方软件转载站（repackmac.com） | **仅作"口碑偏混"的定性旁证，不作数字引用** |
| Cleaner One Pro MacUpdate 3.5/5 | nektony.com 评测文（竞品视角） | 标注为二手口径 |
| BuhoCleaner "$39.99/年 或 $96.99 买断" | nektony.com 评测文 | 与官网 $39.99 年 / $67.99 终身列表价交叉，取官网口径 |
| MacKeeper "$71.40/年 / $89.40/年" | 第三方评测（bestguide、worldoftech） | 与官网 $38.99–107.99 区间交叉，标注为"常见档" |
| CleanMyMac 免费版单文件 500MB 上限 | cleanerone.trendmicro.com 博客（竞品视角） | 标注为竞品口径 |
| CleanMyMac 中国区 Basic ¥199 / Plus ¥388 | 上一份报告的官方中国区定价页实测 | 沿用 |

### C. 数据缺口（诚实标注，共 8 项）

1. **Clario Tech（MacKeeper）收入完全未披露**——仅有 60M+ 下载与 150+ 国家，无法反推 ARPU。
2. **Nektony / Cindori / Software Ambience / Titanium Software / FreeMacSoft 全部无公开财务**——L2 买断层与 L1 免费层的商业化程度只能从定价结构推断。
3. **趋势科技未拆分 Cleaner One Pro 收入**——清理只是其安全产品线的一个 SKU。
4. **Dr.Buho（布霍科技）收入未披露**——仅知 1M+ 下载、10 万+ 用户、1–10 人团队；**其"100,000+ 满意用户"与"1,000,000+ 下载"两个口径的差异未解释**。
5. **名科国际年报未拆分 MacBooster 单品收入**——只有软件业务合计 HK$8,157.7 万（含 IObit 全线：Advanced SystemCare、Driver Booster、Smart Defrag 等）。
6. **全部竞品的续订率 / 流失率缺失**——本赛道无一家披露，这是评估订阅制健康度的最大黑洞。
7. **中国区 CleanMyMac 的实际成交价与销量未知**——中国区有折扣券体系，¥199/¥388 是标价而非成交均价。
8. **腾讯柠檬清理的商业贡献无法量化**——已并入「腾讯电脑管家 for Mac」，收入混入腾讯互联网增值服务，无独立口径。

### D. 口径提醒（引用本报告时请注意）

- **买断一律按 5 年摊销**，因此 DaisyDisk（¥13）、BuhoCleaner 终身（¥16）的年化 ARPU 会显得极低。若按 3 年摊销，DaisyDisk 升至 ¥22、BuhoCleaner 升至 ¥26，**断层结论不变**。
- **"下载量"≠"用户数"≠"活跃"≠"付费"**。本赛道所有"用户数"宣称均为厂商自述的累计装机口径，且多款产品按 SKU 加总（如 IObit 5 亿次为全线累计）。
- **跨币种价格不完全可比**：BuhoCleaner 中国区（¥68/¥78）比海外直营价（$17.99/$25.99）低 **30–40%**，属本地化定价，不是折扣。
- **评分来源不同不可直接横比**：Trustpilot（MacKeeper 4.3、BuhoCleaner 4.8）↔ App Store（DaisyDisk 4.7）↔ MacUpdate（专业用户，普遍更低）三者样本结构不同，本报告只在"同一来源内"做排序判断。
