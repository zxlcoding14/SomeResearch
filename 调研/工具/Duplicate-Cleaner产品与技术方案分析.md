# Duplicate Cleaner 产品、竞品与技术方案分析

**文档类型**：PM 调研与技术预研  
**调研对象**：Duplicate Cleaner（https://www.duplicatecleaner.com/）  
**调研日期**：2026-09-24  
**结论性质**：基于公开资料的产品判断，不替代真实用户访谈、性能压测或法律许可审查。

## 1. 执行摘要

Duplicate Cleaner 是一款 Windows 桌面端重复文件发现与清理工具，核心价值不是简单“删除同名文件”，而是以较高的可控性处理文档、照片、音乐、视频、压缩包和文件夹中的冗余数据。

从 PM 角度看，它的优势是检测维度深、媒体场景完整、安全控制充分；主要问题是功能复杂、首次使用门槛较高、官网和价值呈现偏传统、使用频率天然偏低。产品更适合定位为“专业文件整理工具”，而不是泛化的 PC 一键加速软件。

建议优先投入：

1. 场景化首次运行向导；
2. 基于质量、路径和时间的智能保留推荐；
3. 删除前后的可恢复与风险解释；
4. 扫描结果的空间收益和质量收益可视化；
5. 将核心检测能力抽象为可复用引擎，支持 GUI、CLI、NAS/Web 等入口。

## 2. 产品现状与目标用户

### 2.1 产品定位

官网的核心表达是 “Find & Remove Duplicate Files”。产品支持 Free 与 Pro，Pro 采用版本永久授权并提供 7 天完整功能试用；购买页还提供单地点 Site License。Pro 5 面向 Windows 10/11。

### 2.2 目标用户

| 用户群 | 典型场景 | 关键诉求 |
|---|---|---|
| 家庭用户 | 下载目录、微信/手机导入、备份副本 | 快速释放空间，不误删 |
| 摄影用户 | RAW、导出图、裁剪图、不同分辨率图片 | 识别相似图，保留最佳版本 |
| 视频/内容创作者 | 不同编码、剪辑中间文件、素材副本 | 找到重复和近似片段 |
| 音乐收藏者 | 不同格式、码率或标签的同一歌曲 | 按音质和标签整理 |
| IT/高级用户 | 磁盘、网络盘、归档盘对比 | 批量、可脚本化、可回溯 |
| 小企业/机构 | 单地点多机部署 | 简单授权和集中采购 |

### 2.3 用户任务链

发现磁盘空间不足 → 选择扫描范围 → 定义“重复”规则 → 扫描与预览 → 决定保留项 → 移动/回收站/删除 → 验证空间收益 → 后续定期复查。

其中最关键的产品风险点是“决定保留哪个文件”，而不是“找出候选文件”。

## 3. 功能与体验评估

### 3.1 功能优势

- 精确查重：内容哈希、字节级比较、大小、文件名、扩展名、日期等。
- 相似媒体：图片旋转/翻转/重采样、音频内容与标签、视频帧和音轨。
- 文件治理：重复文件夹、唯一文件、压缩包内部扫描、虚拟文件夹、批处理与命令行。
- 操作安全：保护目录、忽略系统文件、回收站、移动/复制、图片/视频/音频预览。
- 可复用性：可保存扫描设置和结果，适合重复执行相同任务。

完整功能矩阵： https://www.digitalvolcano.co.uk/dcfeatures.html

### 3.2 UX 优点

1. **安全感较强**：用户可以预览、筛选、移动到回收站，而不是强制永久删除。
2. **高级能力完整**：可以表达“某个主目录优先保留，其他目录只作为重复来源”的复杂策略。
3. **本地处理**：适合不希望上传照片、视频或企业文件的用户。

### 3.3 UX 问题

1. 入口按功能而非按任务组织，普通用户不清楚应使用 Regular、Image、Audio 还是 Video 模式。
2. 高级条件太多，首次扫描容易产生配置疲劳。
3. 扫描前缺少“预计可释放多少空间”和“风险范围”的即时反馈。
4. 查到重复之后，选择保留项仍需要用户承担较多认知负担。
5. 官网更像传统工具站，案例、前后对比、动态演示和按人群的价值文案不足。

## 4. 竞品与开源方案

### 4.1 竞品分层

| 方案 | 类型 | 强项 | 弱项/机会 |
|---|---|---|---|
| dupeGuru | 免费开源 GUI | Windows/macOS/Linux、图片/音乐模式、安全选择 | 技术栈较老，产品商业化弱 |
| Czkawka/Krokiet | 免费开源、多平台 | Rust、速度、缓存、重复/空目录/大文件/相似图像和视频 | Czkawka GTK 12 是旧前端的最后版本，新用户转向 Krokiet；需持续维护多端 |
| Video Duplicate Finder | 开源垂直工具 | 视频/图片相似度、局部片段、AI 本地匹配、CLI/Web/Docker | 领域较窄，依赖 FFmpeg 和模型资源 |
| fclones | 高性能 CLI | Rust、并行扫描、JSON、dry-run、硬/软链接、缓存 | 对普通用户缺少 GUI 和媒体语义 |
| rdfind/rmlint | 高性能 CLI | 哈希分阶段、低资源、脚本化、Linux 生态 | Windows 和消费级体验弱 |
| Gemini 2 | Mac 商业软件 | 简单、漂亮、智能选择、相似文件、监控 | 主要服务 macOS，订阅价格和平台限制是机会 |

### 4.2 值得重点研究的开源项目

#### Czkawka / Krokiet

- GitHub：https://github.com/qarmin/czkawka
- MIT（部分前端按 GPL-3.0-only 许可），Rust 实现，支持 Windows、Linux、macOS 等。
- 能力包括重复文件、空文件夹、大文件、临时文件、相似图片、相似视频、音乐、损坏文件、EXIF 清理等。
- 有缓存、CLI、GUI、核心库和 Android 前端；强调本地运行和不收集用户信息。
- **可借鉴**：核心库与多前端分离、缓存模型、多工具工作台、跨平台路线。
- **注意**：引入代码前必须逐项核查仓库当前许可证、依赖许可证和动态链接方式。

#### dupeGuru

- GitHub：https://github.com/arsenetar/dupeguru
- 官网：https://dupeguru.voltaicideas.net/
- 主要使用 Python 3 与 Qt，支持 Windows、macOS、Linux；提供文件名模糊匹配、图片/音乐模式、参考目录、安全分组和移动/复制操作。
- **可借鉴**：参考目录、分组式结果和安全删除交互。
- **注意**：Python/Qt 打包、性能和维护状态需要单独评估，适合借鉴交互和模型，不一定适合作为高性能核心。

#### fclones

- GitHub：https://github.com/pkolaczk/fclones
- Rust CLI，强调大规模文件集的并行处理、低内存路径表示、持久化缓存、JSON/CSV 输出和 dry-run。
- 支持按路径、名称、创建/修改时间、文件数量等策略选择保留或删除，并可生成硬链接/软链接。
- **可借鉴**：扫描阶段拆分、机器可读报告、动作与发现分离、性能工程。
- **限制**：其最佳性能偏 Linux；Windows 上的链接、文件系统和 Copy-on-Write 能力不同。

#### Video Duplicate Finder

- GitHub：https://github.com/0x90d/videoduplicatefinder
- 支持视频/图片相似度、局部片段、音频指纹、可选本地 AI embedding，并提供 GUI、CLI、Web UI 和 Docker。
- **可借鉴**：把昂贵的 AI 匹配放到可选阶段；缓存 embedding；统一桌面、无头和 Web 入口。
- **限制**：FFmpeg、模型下载和硬件性能会影响安装体验、包体积与运行成本。

#### rdfind / rmlint

- rdfind：https://github.com/pauldreik/rdfind
- rmlint：https://github.com/sahib/rmlint
- 典型特点是先按大小筛选，再比较前后字节，最后计算哈希；适用于大规模、低交互的冗余发现。
- **可借鉴**：分阶段候选收敛、结果文件、可重复执行、硬链接/软链接动作。
- **限制**：CLI 优先，交互、媒体相似度和 Windows 桌面集成较弱。

### 4.3 竞品结论

Duplicate Cleaner 的防守优势是“Windows + 深度媒体匹配 + 丰富安全动作 + 商业支持”。

其进攻机会是吸收开源方案的三项能力：

1. Rust/原生核心带来的扫描性能和低内存；
2. CLI/JSON/Web/NAS 多入口；
3. 缓存、可重复扫描和机器可读结果。

## 5. 可行技术方案

### 5.1 方案 A：Windows 原生商业产品

**适合**：先验证 PMF、保持 Windows 体验和商业授权。

建议架构：

```text
Windows GUI (WinUI 3/WPF)
        |
Application Service / Scan Job Manager
        |
Duplicate Engine (Rust/C++ DLL)
  |        |         |
File Index  Hash     Media Similarity
            |        (pHash/音频指纹/视频采样)
        SQLite/Cache/Result Store
        |
Safe Action Layer (Recycle/Move/Copy/Link/Undo)
```

建议技术点：

- 文件发现：Windows API + 异步目录遍历；排除系统目录、junction、符号链接循环。
- 候选收敛：路径过滤 → 文件大小 → 文件头/尾采样 → xxHash/BLAKE3 → 必要时 SHA-256 或字节比较。
- 图片：缩略图、EXIF、pHash/dHash；相似度阈值必须可解释。
- 音频：标签读取、时长/码率比较；需要时再做声学指纹。
- 视频：先采样关键帧，再进入 FFmpeg 或可选 embedding 阶段。
- 数据层：SQLite 保存扫描任务、文件元数据、哈希缓存、结果快照和动作日志。
- 安全动作：默认回收站/移动；永久删除需要二次确认；所有动作可生成恢复清单。

### 5.2 方案 B：Rust Core + 多前端

**适合**：同时支持 GUI、CLI、Web/NAS、未来跨平台。

核心 crate 提供：

- 扫描器和取消/暂停机制；
- 哈希与缓存；
- 重复组和相似度结果模型；
- 策略选择器（保留规则）；
- dry-run 与动作计划；
- JSON/CSV/SQLite 输出。

前端可以是：

- Windows：Tauri/WinUI；
- CLI：用于脚本和企业批处理；
- Web：本地绑定 `127.0.0.1`，默认密码或本机认证；
- NAS：Docker 部署，但必须增加路径白名单、CSRF、认证和不暴露公网的安全限制。

这是长期最值得投入的路线，但初期需要处理跨平台文件权限、路径语义、打包、签名、FFmpeg 和模型分发等问题。

### 5.3 方案 C：在现有产品上增量增强

**适合**：已有成熟 Windows 引擎和用户基础，不希望大规模重写。

第一阶段不替换核心，只增加：

1. 新手向导层；
2. 推荐保留策略；
3. 扫描结果价值摘要；
4. 缓存和结果快照；
5. CLI/JSON 导出；
6. 可选的 AI 相似照片/视频模块。

该路线 PM 风险最低，优先推荐用于商业产品迭代。

## 6. 推荐的 MVP 范围

### MVP-1：精确重复清理

- Windows 10/11；
- 目录选择、排除和保护；
- 大小分组 + 快速哈希 + 最终校验；
- 结果分组、预览、按规则自动标记；
- 回收站/移动到隔离目录；
- dry-run、撤销清单、空间收益统计；
- JSON/CSV 导出。

### MVP-2：媒体相似度

- 图片 pHash/dHash 与旋转/缩放容错；
- 音乐标签与基础声学相似度；
- 视频关键帧相似度；
- 质量评分和保留建议；
- 所有 AI/重计算能力默认关闭，按需启用。

### MVP-3：平台化

- CLI 和计划任务；
- 本地 Web/NAS；
- 多设备/家庭授权；
- 企业审计日志和集中策略。

## 7. 关键产品策略

### 7.1 智能保留策略

默认给出可解释排序，而不是直接删除：

```text
保留分数 = 路径可信度
         + 分辨率/码率质量
         + 元数据完整度
         + 文件更新时间
         + 用户历史选择
```

建议默认动作是“标记建议”，而不是“自动删除”。

### 7.2 安全策略

- 默认只处理 100% 精确重复；
- 相似文件必须显式打开并展示阈值；
- 默认进回收站或隔离目录；
- 操作前输出影响摘要：文件数、预计释放空间、受影响目录；
- 支持动作日志和撤销；
- 系统目录、程序目录、同步目录默认为保护或强提醒。

### 7.3 指标体系

| 层级 | 指标 |
|---|---|
| 获客 | 官网→下载、下载→安装 |
| 激活 | 首次扫描完成率、首次发现重复率、首次释放空间 |
| 转化 | 7 天试用启动率、试用→Pro、Pro 功能触发→购买 |
| 信任 | 误删投诉率、恢复/撤销率、扫描失败率 |
| 留存 | 30/90 天复扫率、保存扫描配置比例、定期任务使用率 |
| 性能 | 每百万文件扫描耗时、峰值内存、缓存命中率 |

## 8. 风险与验证计划

### 主要风险

1. 相似度阈值过低导致误报；
2. junction、硬链接、云同步占位文件导致错误处理；
3. 长时间扫描阻塞 UI 或耗尽内存；
4. AI 模型下载增加包体积和隐私疑虑；
5. 不同文件系统对链接、回收站和权限的行为不一致；
6. 引入 GPL/AGPL 等开源组件产生商业分发约束。

### 验证步骤

1. 准备包含精确重复、重命名、压缩、旋转图片、转码视频和硬链接的基准数据集；
2. 用 1 万、10 万、100 万文件做扫描、内存和恢复测试；
3. 对 20 名用户做首次任务可用性测试；
4. 对“推荐保留”做人工标注集，评估 precision/recall；
5. 用静态许可证扫描和 SBOM 审查所有开源依赖；
6. 对删除动作做故障注入，验证中断、权限不足、磁盘满和进程崩溃后的可恢复性。

## 9. 最终建议

如果目标是做一个比 Duplicate Cleaner 更有竞争力的产品，不建议从“增加更多匹配条件”开始，而应优先构建以下闭环：

> **快速发现 → 可解释推荐 → 安全确认 → 可撤销执行 → 空间和质量收益反馈 → 定期复查**

推荐路线：

- 短期：保留现有 Windows 引擎，重做首次体验、安全动作和智能标记；
- 中期：抽象 Rust/C++ 核心，增加 CLI、JSON 和本地 Web；
- 长期：扩展 NAS/云盘、多设备授权、企业策略和本地 AI 媒体匹配。

## 10. 参考来源

1. Duplicate Cleaner 官网：https://www.duplicatecleaner.com/
2. Duplicate Cleaner 功能矩阵：https://www.digitalvolcano.co.uk/dcfeatures.html
3. Duplicate Cleaner 购买页：https://www.digitalvolcano.co.uk/dcpurchase.html
4. DigitalVolcano 支持中心：https://digvolsoft.freshdesk.com/support/home
5. Czkawka/Krokiet：https://github.com/qarmin/czkawka
6. dupeGuru：https://github.com/arsenetar/dupeguru
7. dupeGuru 官网：https://dupeguru.voltaicideas.net/
8. fclones：https://github.com/pkolaczk/fclones
9. rdfind：https://github.com/pauldreik/rdfind
10. rmlint：https://github.com/sahib/rmlint
11. Video Duplicate Finder：https://github.com/0x90d/videoduplicatefinder
12. Gemini 2：https://macpaw.com/gemini

