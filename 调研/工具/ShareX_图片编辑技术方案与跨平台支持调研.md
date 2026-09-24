# ShareX 图片编辑技术方案与跨平台支持调研

**调研日期：** 2026-09-20  
**资料范围：** ShareX 官网、官方 GitHub `develop` 分支及公开工程文件

## 一、结论摘要

ShareX 的图片编辑不是独立的通用图像处理软件，而是围绕“截图/录屏 → 标注与脱敏 → 保存、复制或上传”的桌面工作流设计。

- 稳定产品定位和交付仍以 **Windows** 为主。
- 图片编辑支持形状、箭头、文字、步骤、气泡、裁剪、模糊、马赛克、智能橡皮擦、背景和图像效果。
- 当前 `develop` 分支已将编辑器公共能力拆分为 **Avalonia + SkiaSharp** 架构，具备跨平台技术基础。
- 主应用、屏幕捕获、全局快捷键、Direct3D、Windows Forms 等仍深度依赖 Windows，不能据此宣称稳定版已经支持 macOS/Linux。
- 推荐表述：**Windows 正式支持 + 编辑器跨平台重构进行中/具备技术准备**。

## 二、图片编辑技术方案

### 2.1 工作流与产品边界

编辑器可由 After capture tasks、Tools → Image editor、快捷键、历史记录和资源管理器右键等入口打开。用户在同一窗口完成标注、敏感信息遮挡、背景整理和效果处理，然后继续执行复制、保存、上传、打印或固定到屏幕等动作。

这说明编辑器被设计为截图工作流中的中间处理阶段，而不是带工程文件管理的专业图像编辑器。

### 2.2 编辑能力分层

#### 标注层

Rectangle、Ellipse、Line、Arrow、Freehand、Text、Speech Balloon、Step、Image、Emoji、Cursor。

标注在扁平化前保持可编辑，可选择、移动、缩放、改色、修改粗细、复制、删除和调整层级。

#### 脱敏层

- **Blur**：模糊敏感区域。
- **Pixelate**：马赛克遮挡。
- **Smart Eraser**：使用邻近颜色快速覆盖细节。
- **Crop / Cut Out**：裁剪或移除中间无关区域。

官网建议，对高敏感信息优先裁掉，而不是只做视觉覆盖。

#### 聚焦层

Highlight、Magnify、Spotlight 用于突出局部，同时保留原图上下文。

#### 画布与背景层

支持边距、填充、智能填充、圆角、阴影、宽高比，以及纯色、渐变、图片或壁纸背景。

#### 效果层

`ShareX.ImageEffectsLib` 按以下目录组织效果：

- `Manipulations`
- `Adjustments`
- `Filters`
- `Drawings`

公开源码还包含 `ImageEffect`、`ImageEffectPreset` 等类型，体现可组合、可序列化和可复用预设的设计方向。

## 三、技术架构分析

| 层次 | 技术判断 | 公开证据/含义 |
|---|---|---|
| 产品定位 | 桌面端截图、录屏、图像编辑与上传自动化 | 官网与 README 均明确描述为 Windows 应用；编辑器嵌入截图后处理工作流 |
| 编辑器 UI | Avalonia + Fluent Theme + MVVM | `ShareX.ImageEditor.csproj` 引用 Avalonia、Fluent Theme、CommunityToolkit.Mvvm |
| 图像渲染 | SkiaSharp 作为 2D 图像/绘制抽象 | 编辑器与 Avalonia 公共项目引用 SkiaSharp |
| Windows UI 集成 | Windows Forms 绑定 | 主应用引用 `SkiaSharp.Views.WindowsForms`，并启用 `UseWindowsForms` |
| 效果系统 | 独立 ImageEffectsLib | 按 Manipulations、Adjustments、Filters、Drawings 分组 |
| 捕获/硬件 | Windows API 与 Direct3D 路线 | ScreenCaptureLib 为 `net10.0-windows`，引用 Windows Forms 和 `Vortice.Direct3D11` |
| 工程分层 | Core / Presentation / Integration / Localization | ImageEditor 源码目录按模型、呈现、宿主集成和本地化拆分 |

综合来看，渲染路线可概括为：

```text
Avalonia 控件/窗口层
        ↓
ShareX.Avalonia.Imaging 抽象
        ↓
SkiaSharp 图像与绘制
        ↓
平台宿主（Windows Forms / Direct3D / 系统剪贴板等）
```

## 四、跨平台支持分析

### 4.1 已经做到的支持

1. `ShareX.ImageEditor` 和 `ShareX.Avalonia` 的目标框架为 `net10.0`，未限定 Windows。
2. UI 使用 Avalonia.Desktop、Fluent Theme 和 Inter 字体，具备跨平台桌面 UI 基础。
3. 图像能力以 SkiaSharp 为核心，便于复用像素绘制与导出逻辑。
4. 编辑器项目声明 `x64;ARM64`，已考虑多架构构建。
5. 本地化资源采用 `resx/Localization` 组织；官网列出简体中文、繁体中文等多语言支持。

> 多语言支持属于本地化能力，不等同于跨操作系统支持。

### 4.2 尚未完成或受限的部分

1. 主应用 `ShareX.csproj` 明确目标为 `net10.0-windows10.0.22621.0`，并启用 Windows Forms。
2. `ScreenCaptureLib` 目标为 `net10.0-windows`，使用 Windows Forms 和 `Vortice.Direct3D11`。
3. 屏幕捕获、窗口枚举、全局热键、系统托盘、资源管理器集成等能力无法直接平移到 macOS/Linux。
4. 官网、README 和下载渠道（Setup、Portable、Microsoft Store、Steam）仍以 Windows 生态为中心。

因此，Linux/macOS 更适合被视为源码层面的潜在目标或开发中方向，不能视为官方稳定发行版支持。

## 五、如果继续推进跨平台，建议的工程路径

1. 保持 `ShareX.ImageEditor/Core`、`ImageEffectsLib`、`ShareX.Avalonia.Imaging` 为平台无关层。
2. 将截图、剪贴板、全局快捷键、托盘、文件选择器、上传认证等能力抽象为 `IPlatformServices`。
3. 将 WinForms、Direct3D、Shell integration 隔离到 `ShareX.Platform.Windows`；再新增 macOS/Linux 实现。
4. 优先实现“打开图片 → 编辑 → 导出”，再迁移全部屏幕捕获能力。
5. 使用 SkiaSharp 统一像素绘制和导出，并针对各平台测试输入法、字体、DPI、色彩管理、剪贴板和窗口行为。
6. 在 CI 中加入 `win-x64`、`win-arm64`、`linux-x64`、`osx-arm64` 等 RID 构建矩阵和编辑器回归测试。

## 六、对产品/项目的启示

- **适合借鉴：** 编辑器与上传自动化紧耦合；标注对象在最终导出前保持可编辑；效果库独立化。
- **需要警惕：** 跨平台 UI 框架不自动带来跨平台系统能力；截图工具的真正难点在捕获、热键、窗口、剪贴板和 GPU/编码器适配。
- **复刻建议：** 先实现“平台无关图片编辑 SDK + 平台适配壳”，再接入各平台截图能力。

## 七、资料与证据链接

- [ShareX 官网](https://getsharex.com/)
- [ShareX Image Editor 文档](https://getsharex.com/docs/image-editor)
- [ShareX 官方 GitHub README](https://github.com/ShareX/ShareX/blob/develop/README.md)
- [主应用 ShareX.csproj](https://raw.githubusercontent.com/ShareX/ShareX/develop/ShareX/ShareX.csproj)
- [图像编辑器 ShareX.ImageEditor.csproj](https://raw.githubusercontent.com/ShareX/ShareX/develop/ShareX.ImageEditor/ShareX.ImageEditor.csproj)
- [Avalonia 公共项目 ShareX.Avalonia.csproj](https://raw.githubusercontent.com/ShareX/ShareX/develop/ShareX.Avalonia/ShareX.Avalonia.csproj)
- [屏幕捕获库 ShareX.ScreenCaptureLib.csproj](https://raw.githubusercontent.com/ShareX/ShareX/develop/ShareX.ScreenCaptureLib/ShareX.ScreenCaptureLib.csproj)

> 注：本报告基于 2026-09-20 可访问的公开页面与 `develop` 分支工程文件；`develop` 分支可能变化，跨平台结论应以官方发布说明和实际构建产物为准。
