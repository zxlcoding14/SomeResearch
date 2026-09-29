# NAPS2（Not Another PDF Scanner）项目技术方案分析

> 分析对象：`https://github.com/cyanfish/naps2`（源码仓库，当前浅克隆版本提交 `876e8ca`）

## 1. 项目定位与主要功能

NAPS2 是一个桌面文档扫描应用，同时提供可复用的 .NET 扫描 SDK。核心目标是把不同操作系统、不同扫描驱动统一成一致的扫描体验，并完成“扫描→图像处理→OCR→文档导出”。

主要功能：

- 扫描设备发现、能力查询和单页/多页扫描。
- 支持平板、自动进纸器（ADF）、双面、纸张尺寸、DPI、位深、色彩模式等参数。
- 页面排序、旋转、裁剪、纠偏、增强、去背景等后处理。
- 导入/导出 PDF、TIFF、JPEG、PNG；PDF 合并、分页和元数据处理。
- 基于 Tesseract 的 OCR，可生成可检索 PDF，并缓存识别结果。
- 条码检测、批量扫描、配置文件（Profile）和命令行自动化。
- Windows、macOS、Linux 桌面客户端；SDK 可嵌入第三方 .NET 应用。
- 通过 eSCL（AirScan）协议共享扫描仪，使局域网客户端或浏览器能够访问扫描服务。

README 明确列出驱动：Windows 的 WIA/TWAIN，macOS 的 Apple ImageCaptureCore/TWAIN，Linux 的 SANE，以及跨平台网络 eSCL。

## 2. 总体技术架构

```text
桌面 UI（WinForms / GTK / macOS）
        │
        ▼
NAPS2.Lib（业务编排、Profile、导入导出、命令行、操作管理）
        │
        ▼
NAPS2.Sdk（跨平台扫描抽象、图像模型、OCR、PDF、序列化）
        │
 ┌──────┼───────────────┬───────────┐
 ▼      ▼               ▼           ▼
WIA   TWAIN            SANE        eSCL/Apple
        │
        ▼
Worker/Remoting（可选隔离进程、gRPC/Named Pipes）
        │
        ▼
设备原生 API / 网络扫描仪
```

仓库按职责拆分为多个 .NET 项目：

- **NAPS2.Sdk**：公共扫描 API 与核心领域模型。
- **NAPS2.Images.[平台]**：GDI、WPF、GTK、macOS、ImageSharp 等图像适配层。
- **NAPS2.Lib**：桌面应用共享业务层（Eto.Forms UI 逻辑、配置、操作、导入导出）。
- **NAPS2.App.WinForms/Gtk/Mac/Console**：平台入口和 UI 壳。
- **NAPS2.App.Worker / NAPS2.Sdk.Worker.[平台]**：扫描隔离进程。
- **NAPS2.Escl、NAPS2.Escl.Server、NAPS2.Escl.Usb**：eSCL 协议客户端、服务端和 USB 发现支持。
- **NAPS2.Images、NAPS2.Internals**：图像基础设施和共享底层工具。

SDK 目标框架包含 `net8`、`net10.0`、`net462`，macOS 额外编译 `net10.0-macos`，说明项目通过多目标编译和条件编译适配平台差异。

## 3. 扫描原理与执行流程

### 3.1 统一入口

`ScanController` 是 SDK 的主入口：

1. `ScanOptionsValidator` 校验设备、驱动和参数。
2. `ScanBridgeFactory` 决定进程内桥接（`InProcScanBridge`）还是 Worker 桥接（`WorkerScanBridge`）。
3. Bridge 调用 `ScanDriverFactory` 创建具体驱动。
4. 驱动把原生设备事件转换为统一的 `ScanEvents`，并按页异步产出 `ProcessedImage`。
5. `LocalPostProcessor` 对每页执行 OCR 排队等后处理。
6. 通过 `IAsyncEnumerable<ProcessedImage>` 流式返回，调用方可以边扫描边显示/保存。

这种设计避免一次性把整本文件加载进内存，也能在 ADF 场景中持续报告页进度和错误。

### 3.2 驱动适配

`ScanDriverFactory` 使用 `Driver` 枚举选择实现：

- **WIA**：Windows Image Acquisition，使用 Windows 原生 COM/API。
- **TWAIN**：通过 NTwain 等封装访问厂商 TWAIN DSM；部分设备要求 32 位进程。
- **SANE**：Linux/macOS 常用的开源扫描栈，通过 native interop 调用 `libsane`。
- **Apple**：macOS ImageCaptureCore。
- **eSCL**：基于 HTTP 的 AirScan 标准，适合网络扫描仪，也可用于 USB eSCL 设备。

默认驱动按平台选择：Windows=WIA、macOS=Apple、Linux=SANE；用户也可以显式指定驱动。

### 3.3 Worker 隔离与容错

`ScanningContext.WorkerFactory` 可将原生扫描调用放入独立进程。当前实现对 Apple 和 SANE 默认倾向 Worker；TWAIN 在 Windows 64 位进程中通常通过 32 位 Worker 解决架构限制。

Worker 层使用 protobuf/gRPC 协议和 Named Pipes，传输设备列表、扫描选项、页面数据和错误。收益是：

- 原生驱动崩溃不会直接拖垮主 UI。
- 解决 32/64 位不兼容。
- 降低 libusb、厂商驱动、COM 消息泵对主进程的影响。

代价是跨进程序列化、生命周期和调试复杂度增加。

### 3.4 图像与内存模型

`ScanningContext` 统一管理图像上下文、临时目录、日志、OCR 引擎和生命周期。

- `ImageContext` 以适配器方式屏蔽 GDI/WPF/GTK/NSImage/ImageSharp 的差异。
- `ProcessedImage` 同时保存图像存储、元数据和变换状态，变换尽量延迟到 `Render()`。
- 可选 `FileStorageManager` 将大图落盘，避免大量页面长期占用内存。
- Context 释放时统一回收其创建的 `ProcessedImage` 和文件存储。

## 4. OCR 原理

OCR 由 `IOcrEngine` 抽象，默认实现 `TesseractOcrEngine`：

1. 扫描页先保存到临时图片文件。
2. `OcrController` 把请求放入 `OcrRequestQueue`，支持优先级、取消、事件和结果缓存。
3. 通过无窗口子进程启动 Tesseract，设置 `TESSDATA_PREFIX` 和语言模型。
4. 请求 Tesseract 输出 hOCR（包含文字、词框、行框和角度信息）。
5. 解析 hOCR 为 `OcrResult`/`OcrResultElement`，供 PDF 导出时叠加透明文字层。

支持系统 Tesseract、NAPS2 内置二进制和自定义可执行文件；语言数据可区分 `fast`/`best` 模式。OCR 运行在后台，具备超时、取消和错误日志，避免阻塞 UI。

## 5. PDF 与文件导出

SDK 提供 `PdfExporter`/Pdfium 相关实现：

- 将每个 `ProcessedImage` 渲染为页面图像并写入 PDF。
- 保留无变换 PDF 页时可走“直接复用”路径，减少重新编码（代码中已有对应设计）。
- 支持 PDF 兼容级别、PDF/A 辅助处理、JPEG/PNG 选择、加密参数和元数据模型。
- OCR 导出逻辑以“图像页 + 透明文字层”为核心，使扫描 PDF 可搜索。

除 PDF 外，图像导出使用统一的 `ImageExportFormat` 和 `ImageExportHelper`，支持 JPEG/PNG/TIFF 等格式及质量/无损参数。

## 6. eSCL 网络共享原理

`NAPS2.Escl.Server` 实现 Mopria eSCL HTTP 服务：发布设备能力、创建扫描 Job、轮询 Job 状态并下载扫描图像；`MdnsAdvertiser` 用于局域网发现。由于 eSCL 是标准 HTTP 协议，浏览器或 TypeScript 客户端无需安装本地驱动即可访问共享扫描仪（仓库另有 `naps2-webscan` 示例项目）。

## 7. 关键工程设计取舍

**优点**

- 驱动策略模式 + Bridge/Worker 分层，跨平台和厂商兼容性较强。
- `IAsyncEnumerable` 流式扫描，适合 ADF、大批量文档。
- 图像上下文、存储后端和 OCR 引擎均可替换，SDK 可嵌入。
- 原生能力通过独立项目和条件编译隔离，桌面 UI 可复用大量业务逻辑。
- 完整测试项目覆盖 SDK、应用、eSCL 和扫描器场景。

**代价/风险**

- 原生驱动差异巨大，错误处理、设备 ID 变化和消息泵逻辑复杂。
- 多目标框架、平台图像库和原生二进制使发布矩阵较大。
- Worker、gRPC、临时文件和 OCR 子进程增加部署与诊断成本。
- PDF/OCR 对大分辨率图像的 CPU、磁盘和内存压力较高，需要合理的文件存储和队列策略。
- GPL-2.0-or-later 主程序许可证对二次分发有约束；SDK/图像/eSCL 子项目主要为 LGPL，集成时需分别核对许可证。

## 8. 可借鉴的实现要点

若构建类似系统，建议复用以下思想：

1. 先定义与设备无关的 `ScanOptions`、`ScanDevice`、`ScanCaps` 和分页事件协议。
2. 每种驱动只负责“设备控制与原始图像获取”，旋转/裁剪/OCR/PDF 放在公共后处理管线。
3. 采用异步流逐页输出，错误应能定位到具体页，并支持取消。
4. 对不稳定或位数不匹配的 native API 使用 Worker 隔离。
5. 图像对象支持内存/文件两种存储策略，并通过引用计数或 Context 统一释放。
6. OCR 采用异步队列和结果缓存，导出时再合成文字层。
7. 网络扫描优先考虑标准 eSCL/AirScan，降低客户端安装驱动的成本。

## 9. 结论

NAPS2 的核心不是单一的“扫描界面”，而是一套以 `NAPS2.Sdk` 为中心的跨平台扫描平台：底层通过 WIA/TWAIN/SANE/Apple/eSCL 适配硬件，中间层用 Bridge、Worker 和统一图像模型隔离平台差异，上层由 NAPS2.Lib 和多个 UI 壳实现桌面产品，OCR 与 PDF 则作为可插拔的异步后处理能力。该架构适合需要长期维护多厂商扫描设备、批量文档处理和 SDK 集成的场景。

## 10. 主要源码依据

- `README.md`：产品能力、平台、驱动和许可证。
- `NAPS2.Sdk/README.md`：SDK 包结构、示例和驱动矩阵。
- `NAPS2.Sdk/Scan/ScanController.cs`：扫描主流程、事件和异步流。
- `NAPS2.Sdk/Scan/Internal/ScanDriverFactory.cs`：驱动选择。
- `NAPS2.Sdk/Scan/Internal/ScanBridgeFactory.cs`：进程内/Worker 桥接策略。
- `NAPS2.Sdk/Scan/ScanningContext.cs`：图像、文件存储、OCR、Worker 和资源生命周期。
- `NAPS2.Sdk/Ocr/OcrController.cs`、`TesseractOcrEngine.cs`：OCR 队列和 hOCR 解析。
- `NAPS2.Sdk/Pdf/PdfiumPdfExporter.cs`：PDF 页面构建与 OCR 导出设计。
- 各 `NAPS2.App.*`、`NAPS2.Lib.*`、`NAPS2.Escl.*` 项目文件：平台壳、业务层和网络扫描服务划分。
