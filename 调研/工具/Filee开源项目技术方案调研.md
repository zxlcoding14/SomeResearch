# Filee 开源项目技术方案调研

> 调研对象：<https://github.com/KnifeLemon/Filee>
>
> 源码快照：commit `380092e9e9cf89c6fc9ab964a936f7deef0b346e`（2026-10-08）

## 1. 项目定位与总体架构

Filee 是面向 Windows（同时预览 macOS/Linux）的本地文件转换器。核心卖点是“拖拽即转换、结果不上传、转换能力由多个引擎组合而成”。源码按职责拆分为：

- `Filee.App`：Avalonia UI、光标处 donut 菜单、托盘、设置和进度提示。
- `Filee.Core`：格式注册、预设、转换路由、队列、输出命名和监听文件夹；不依赖 UI/操作系统 API。
- `Filee.Engines`：每个转换后端实现一个 `IConverter`，并注册到 `EngineRegistry`。
- `Filee.Platform.Windows/MacOS/Linux`：资源管理器/Finder/文件管理器集成、全局输入和自启动。
- `Filee.Cli`：复用同一套 Core/Engines 的命令行与 watch 模式。

转换主链路为：

```text
输入文件 → FormatRegistry 识别格式 → ConverterCatalog 过滤可用引擎
         → RoutePlanner(Dijkstra) 规划路径 → JobQueue 并行执行步骤
         → 临时目录中转 → OutputPathResolver 分配最终路径 → 进度/历史
```

## 2. 转换抽象：IConverter + 加权转换图

`IConverter` 只声明四类信息：稳定 ID、支持的直接边 `ConversionEdge(From, To, Cost)`、并发上限、状态探测和 `ConvertAsync`。因此引擎只需声明“我能做哪些一步转换”，无需知道其他引擎。

格式是图节点，直接转换是有向边。例如：

```text
HWPX --rhwp--> PDF --PDFium--> PNG
DOCX --DocxReader/HWPX writer--> HWPX --rhwp--> PDF
EPUB --EbookReader--> HWPX --rhwp--> PDF
```

`RoutePlanner` 对可用引擎的边运行 Dijkstra，最多 3 跳；边权是转换成本加引擎优先级惩罚（0~9），优先级只用于同等路径的选优，不会为了偏好某引擎而选择更长路径。源格式与目标格式相同也必须存在显式自环边，支持“重新编码/压缩/改质量”等操作。

这带来两个扩展特征：新增一个 `IConverter` 并在 `EngineRegistry.CreateAll` 注册后，会自动解锁所有可达的多步路径；引擎缺失时从图中剔除，UI 可据此解释“需要安装某引擎”。

## 3. JobQueue 的执行模型

`JobQueue` 将一个拖拽动作封装为 `ConversionJob`，为每个任务创建独立临时目录，并按文件粒度并行执行。每个引擎通过 `SemaphoreSlim` 限制并发（`MaxParallelism=0` 表示 CPU 核数；FFmpeg=2，rhwp=2）。

单文件多步转换中：

1. 第一步读取源文件并写入临时输出；
2. 后续步骤读取上一步结果；
3. 仅最后一步使用最终输出分配器，避免中间文件污染用户目录；
4. 取消、超时或异常时删除部分输出，单文件失败不会中止其他文件。

队列对三种聚合操作走专门路径：

- **合并 PDF**：各文件先转 PDF，再由 `IPdfMerger`（PDFsharp）按原顺序合并。
- **多页 TIFF**：各文件先得到 TIFF 页，再由 `ITiffMerger` 合成一份 TIFF。
- **One ZIP/压缩为一个归档**：源文件原样交给 `IFileCombiner`，不先转换。

输出名由预设中的目录、文件名模板、冲突策略和“保留原日期”规则决定；并发任务通过保留集合避免重名竞争。

## 4. 文档转换的关键技术：统一中间模型

项目最有价值的设计是 `HDocument` 文档模型和双向读写器：

```text
DOCX/XLSX/PPTX/PDF/HTML/EPUB/Markdown/TXT/HWPX...
                 ↓ reader
              HDocument
                 ↓ writer
        HWPX(OWPML) 或 DOCX(WordprocessingML)
```

### 4.1 输入读取

`DocumentReaders` 集中维护“格式 ID → reader”映射，新增 reader 一行即可同时让 HWPX writer、DOCX writer 及所有路由生效。内置 reader 包括：

- DOCX/OOXML：直接解析 ZIP/XML，保留页、节、页眉页脚、表格、图片、文本框等布局信息。
- XLSX/XLS/ODS/CSV/TSV：读取为工作簿/单元格模型，保留显示文本、类型、数字格式、合并、隐藏行列、冻结行等。
- PPTX：每页幻灯片转为文档 section，保留浮动对象和文本样式。
- PDF：PdfPig 按字位置重建行、段落、列阅读顺序；图片保留或由 PDFium 渲染，扫描页不做 OCR，只保留为图片。
- HTML：AngleSharp + 简化 CSS 解析；脚本、表单、导航等主动跳过，远程图片不下载。
- Markdown：Markdig 解析标题、列表、表格、脚注、数学等。
- EPUB/MOBI/FB2/漫画：先解包容器，再复用 HTML/文档模型。
- ODT/RTF/LaTeX/reStructuredText：可选 Pandoc 输出 JSON AST，再转为模型。

### 4.2 HWPX writer：无需 Hancom Office

`HwpxWriter` 从内置 `blank.hwpx` 模板复制 OWPML 包结构，生成 `header.xml`、各 section XML、清单和媒体文件；图片统一写入 `BinData`，不支持的图片格式先用 ImageMagick 转 PNG。输出先写 `.tmp`，完成后原子替换。

因此“DOCX/XLSX/PPTX/PDF → PDF”默认不是调用 Microsoft Office：

```text
源文件 → 内置 reader → HDocument → HWPX → rhwp export-pdf → PDF
```

该路径可在无 Office/Hancom 的机器上运行，并且通过 `PdfPenalty` 让保留结构的路径优先于“先 PDF 再识别”。

### 4.3 DOCX writer

DOCX writer 从同一个 `HDocument` 手写 WordprocessingML，生成关系、内容类型、节、编号、页眉页脚、图片、脚注、书签和形状等。测试会用 Open XML SDK 校验结构，再用自身 reader 和 LibreOffice 交叉读取，降低“能写不能打开”的风险。

## 5. 各类能力的实现原理

| 类型 | 主要技术 | 关键限制/取舍 |
|---|---|---|
| 图片/RAW | Magick.NET、LibRaw；动画帧、EXIF 方向、PSD/XCF 合成 | RAW 转码依赖解码器；部分格式会栅格化 |
| SVG/矢量/CAD | Svg.Skia/SkiaSharp；ACadSharp 读写 DWG/DXF，自研 Skia 渲染到 PDF/SVG/位图 | CAD 仅支持建模范围内实体，复杂 ACIS/OLE 等跳过并记录 |
| PDF | PDFsharp 写入/合并，PDFium 栅格化，PdfPig 文本与布局读取 | 无 OCR；表格通常退化为按阅读顺序的段落 |
| 视频/音频 | FFmpeg/ffprobe 外部进程；根据媒体信息生成编码参数，多 pass GIF 调色板 | 有损编码；FFmpeg 最多并发 2，取消会杀进程树并清理半成品 |
| 电子书 | EPUB/MOBI/FB2 自研容器解析，统一到 HDocument；calibre 补充冷门格式 | DRM、KFX/Topaz 等拒绝处理 |
| 压缩包 | ZIP/TAR 部分进程内实现，7-Zip 处理 7Z/RAR/CAB/ISO 等 | 先列目录，拒绝路径穿越、符号链接、加密和超大条目 |
| 字体 | 直接解析 SFNT 表；WOFF zlib、WOFF2 Brotli；CFF → TrueType 曲线近似 | 丢弃 DSIG；不写字体集合和部分 CFF2 变量字体 |
| 邮件 | MimeKitLite 解析 MIME、quoted-printable/base64、编码头；EML→HTML/TXT/附件 ZIP | HTML 去脚本，内嵌 `cid:` 图片转 data URI |
| HWP/HWPX | rhwp 负责 HWP↔HWPX/HWPX→PDF；Filee 自研 HWPX 读写器负责结构转换 | 不依赖 Hancom Office，复杂对象有明确跳过项 |

## 6. 外部引擎与可复现性

`EngineEnvironment` 的查找顺序是：用户指定副本 → Filee 安装目录/下载目录 → 系统 PATH 或标准安装目录（仅可选引擎）。内置引擎不调用系统 Office/Hancom。引擎下载信息在 `engines.json` 中固定 URL、SHA-256 和大小，安装时先 staging、校验成功后替换，避免半安装。

外部程序统一经 `ProcessRunner` 启动：不经 shell、参数使用 `ArgumentList`、隐藏窗口、捕获 stdout/stderr、支持超时和取消时杀整个进程树。

> 注意：README 中“Filee never uses software installed on the system”的表述比当前源码严格；当前 `EngineEnvironment.SearchSystem=true`，FFmpeg、Pandoc、Ghostscript、calibre、LibreOffice 等可选引擎确实会回退到系统副本。内置转换器仍不依赖系统 Office/Hancom。

## 7. 质量、安全与工程化观察

**优点**

1. 转换图与统一文档模型使能力组合性很强，新增格式的边际成本低。
2. 中间文件隔离、输出保留、并发闸门、失败隔离和可取消设计适合批处理。
3. 对归档路径穿越、符号链接、加密文件、临时文件和外部进程超时有防护。
4. 测试覆盖路由、文档读写、字体、归档和 UI headless 渲染，并使用独立软件交叉验证。

**局限**

1. “最多 3 跳”避免路径爆炸，但对少数复杂格式可能找不到可行链路。
2. `HDocument` 是有损抽象：Word 图表、SmartArt、公式、批注/修订、部分 CAD 对象无法完整保留。
3. PDF 逆向排版依赖几何启发式，复杂表格、扫描件和矢量标注不可完全还原。
4. 可选外部引擎版本、许可证和系统字体会影响结果；虽然引擎版本可固定，但系统副本回退降低了完全可复现性。

## 8. 可借鉴的实现模式

- 用“格式节点 + 引擎边 + 成本”替代大量 `if/else` 转换矩阵。
- 对复杂文档采用“多格式 reader → 一个中间模型 → 多格式 writer”，避免 N×M 适配器爆炸。
- 将聚合转换（合并、打包、多页输出）从普通单文件转换中抽出专用接口。
- 外部 CLI 统一封装超时、取消、输出捕获和临时目录，所有输出完成后再原子落盘。
- 用可解释的引擎状态和缺失依赖信息驱动 UI，而不是在转换失败后才提示。

## 9. 参考源码

- `docs/ARCHITECTURE.md`
- `docs/ENGINES.md`
- `src/Filee.Core/Conversion/IConverter.cs`
- `src/Filee.Core/Conversion/RoutePlanner.cs`
- `src/Filee.Core/Conversion/JobQueue.cs`
- `src/Filee.Engines/Hwp/Hwpx/DocumentReaders.cs`
- `src/Filee.Engines/Hwp/Hwpx/HwpxWriter.cs`
- `src/Filee.Engines/Hwp/RhwpConverter.cs`
- `src/Filee.Engines/Infrastructure/EngineEnvironment.cs`
- `src/Filee.Engines/Infrastructure/ProcessRunner.cs`
- `src/Filee.Engines/Media/FfmpegConverter.cs`

