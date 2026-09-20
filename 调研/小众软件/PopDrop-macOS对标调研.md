# PopDrop 的 macOS 对标调研：场景是否存在、实现差异在哪

> 调研对象：Windows 项目 [hiforrest/PopDrop](https://github.com/hiforrest/PopDrop) 所覆盖的使用场景，在 macOS 上是否有对等场景与产品
> 配套文档：[PopDrop-功能点与技术方案分析.md](PopDrop-功能点与技术方案分析.md)（功能与技术方案）、[PopDrop-功能点清单-简化版.md](PopDrop-功能点清单-简化版.md)（功能速览）
> 姊妹文档：[PopDrop-Linux对标调研.md](PopDrop-Linux对标调研.md)（Linux 侧，含三平台横向对比）
> 调研方式：**公开资料检索 + API 语义比对**。macOS 侧结论来自各产品官网/商店页、Apple 官方文档与公开技术讨论；未在 macOS 上安装或实测任何产品，也未编写代码验证。
> 证据等级标注：✅ = 有公开资料直接印证；🔶 = 基于 API 语义与公开资料的推断，未直接验证。

---

## 1. 结论速览

### 1.1 三句话结论

1. **场景存在，而且相当成熟** —— PopDrop 覆盖的每一类使用场景在 macOS 上都能找到对应产品，其中"拖放中转站"在 macOS 上是一个**比 Windows 更成熟、产品更多的品类**（Yoink、Dropover、Unclutter、FilePane、Dropzone…）。
2. **但没有一个产品和 PopDrop 形态相同** —— macOS 把这些场景**拆散**到了多个单一职能的产品 + 系统自带能力里，没有"面板 + 来源分栏 + 固定项 + 文本块 + 投送到前台应用"整合在一起的东西。
3. **实现路径差异极大，且差异不在"能不能做"，而在"用什么机制做、以及允许你做到什么程度"** —— 最关键的一条：**PopDrop 大量依赖"用窗口消息跨进程操纵别人的窗口"，macOS 没有对应的通用机制**，只能改用辅助功能（Accessibility）API，而这条路径受 TCC 权限与沙盒限制，直接决定了产品能不能上架 Mac App Store。

### 1.2 能力对照表

| PopDrop 能力（完整版章节） | macOS 是否存在同场景 | 代表产品 / 系统能力 | 实现路径差异 |
| --- | --- | --- | --- |
| 呼出面板取用文件（2.1） | ✅ 存在 | FilePane、Folder Slice、HighTop、Raycast、Alfred | 中：热键机制不同，面板本身不难 |
| 拖放中转站（2.1 / 2.7.4） | ✅ **成熟品类** | Yoink、Dropover、Unclutter、Dropzone、Notchy、Dockside | 中：拖放模型不同但都是原生一等公民 |
| 来源分栏 + 固定项（2.3 / 2.5） | 🔶 无直接对标 | 无 | 高：需要自己实现整套数据模型，但无系统级障碍 |
| 文本块工作区（2.4） | ✅ 存在（形态不同） | Raycast Snippets、Alfred Snippets、Espanso、Refrain | 中：取用形态不同，投送机制差异大 |
| Windows 终端兼容发送（2.4.1） | ✅ 存在 | iTerm2 / Terminal.app 的 AppleScript 接口 | **低**：macOS 更简单（见 §5.1） |
| Launcher 模式（2.6） | ✅ 存在 | Launchpad、Raycast、Alfred、Dropzone | 低 |
| 外部内容投放 / 下载（2.7.3 / 2.12） | ✅ 存在 | Dropover、Dropzone、浏览器拖拽 + File Promise | 中：用 `NSFilePromiseProvider` 而非异步 HDROP |
| 内置文件预览（2.8.1） | ⚠️ **系统已提供** | **Quick Look**（系统级）、`QLPreviewPanel` | **低**：macOS 把这件事做成了系统能力 |
| 外部空格键预览 Seer/QuickLook（2.8.2） | ⚠️ 不需要 | Finder 里空格预览是**系统自带** | **低**：PopDrop 要接第三方才有，macOS 原生就有 |
| 选择窗口定位到此（2.9） | ✅ 存在（唯一对标） | **Default Folder X** | **高**：机制完全不同，且受限 |
| 右键菜单与文件操作（2.10） | ✅ 存在 | Finder 自身 + Finder Sync 扩展 / 快速操作 / 服务 | 中高：扩展受沙盒约束 |
| 打开方式与工具动作（2.11） | ✅ 存在 | `open -a`、`NSWorkspace.open`、快捷指令 | 低 |
| 文件管理器适配（2.13） | ✅ 存在（生态小得多） | ForkLift、Path Finder、Transmit | 中：Finder 主导，没有 7 家可适配 |
| 缓存、刷新、变更监听（2.16） | ✅ 存在 | FSEvents、`NSMetadataQuery`（Spotlight） | 中：语义不同（见 §4.6） |
| 最近文件侧边栏（2.3） | ✅ 存在 | Finder「最近使用」、`sfl3` 文件 | 中：数据源格式不同 |

---

## 2. 场景层：macOS 上有什么

### 2.1 拖放中转站（shelf）—— macOS 的成熟品类

这是与 PopDrop **重叠度最高**的一类，也是 macOS 上明显比 Windows 繁荣的品类。共同心智模型是：**拖起来 → 先放这儿 → 切到目标 → 再拖出去**，正是 PopDrop "不切换当前窗口"要解决的问题。

| 产品 | 形态 | 备注 |
| --- | --- | --- |
| **Yoink** | 屏幕边缘滑出的临时货架，跨 App、跨空间（Spaces）、跨全屏保留内容 | 该品类的经典产品，Mac App Store 分发 |
| **Dropover** | 拖拽货架，支持多货架、文件动作、分享、快捷指令 | 功能最接近"中转站 + 动作中心" |
| **Unclutter** | 菜单栏面板，含文件暂存 / 剪贴板 / 笔记三个分区 | 三合一形态 |
| **FilePane** | 拖拽时在光标附近浮出 "Drop Here" 面板，提供复制/移动/压缩/转换/缩放/分享 | **与 PopDrop 的"顶部拖拽识别区"最像** |
| **Dropzone 4** | 浮动 Drop Bar，可放文件、上传、执行动作 | 偏向动作面板 |
| **Notchy** | 用 MacBook 刘海区域做投放货架，重启后仍保留 | 新形态，免费 |
| **Dockside** | Dock 旁的货架，可放文件、文件夹、图片、URL、文本 | — |

**关键差异**：这些产品几乎全是"**自己的容器**"——你先把东西放进它的货架，它再负责送出去。而 PopDrop 是"**你自己的文件夹**"——它索引你已有的目录，面板只是这些目录的一个快速视图。这是**产品定位差异**，不是技术限制：macOS 上做"索引已有目录的面板"同样可行，只是没人这么做，因为 Finder + Spotlight / Raycast 已经覆盖了"找文件"这一半。

### 2.2 不切换窗口的快速取用面板

| 产品 | 与 PopDrop 的关系 |
| --- | --- |
| **FilePane** | 最接近：拖拽时浮出面板，提供文件动作 |
| **Folder Slice** | 定位就是"快速取用文件并直接拖进应用"（要求 macOS 15.2+） |
| **HighTop** | 菜单栏的快速取用工具 |
| **Recent File Picker** | 只做"最近文件"，菜单栏形式 |
| **Raycast / Alfred** | 走"键盘唤起 + 搜索"路线，取代的是"翻目录"而不是"分栏浏览" |

**形态差异**：macOS 这一类的默认形态是**菜单栏（menu bar）常驻 + 点击展开**，而 PopDrop 是**全局热键唤起 + 失焦自动隐藏的独立面板**。菜单栏形态在 macOS 上更受青睐，因为它天然不抢焦点、不需要"自动隐藏保护"那一整套机制。

### 2.3 文本块 / Snippet / Prompt 管理

PopDrop 的文本块工作区（递归平铺 `.md`/`.txt` 为卡片）在 macOS 上对应的是一个**已经很拥挤**的品类，但形态是"**关键字展开**"而不是"卡片浏览 + 手动发送"：

| 产品 | 形态 |
| --- | --- |
| **Raycast Snippets** | 系统级关键字展开、标签、动态占位符、可从 TextExpander/aText/Espanso/PhraseExpress 导入 |
| **Alfred Snippets** | Powerpack 功能，任意 App 内自动展开、动态占位符、光标定位、排除规则 |
| **Espanso** | 开源（Rust）跨平台文本扩展器，YAML 配置 |
| **Refrain** | 专门面向 prompt / snippet 管理，Markdown 工作流（要求 macOS 14+） |
| **macOS 系统文本替换** | 系统设置 → 键盘 → 文本替换，随 Apple ID 同步 |

- 差异在于**触发方式**：macOS 主流是"**打缩写自动替换**"，PopDrop 是"**打开面板 → 找到卡片 → 发送**"。
- PopDrop 的"前置发送（投送到原输入内容最前方）"在 macOS 上没有现成对标——snippet 类工具是**替换触发词**，语义上不完全是同一件事，但解决的痛点高度重叠。
- 🔶 Snippet 类工具往目标 App 注入文本用的正是 **`CGEventPost` 模拟 ⌘V + 剪贴板**，或对原生文本控件直接走 **Accessibility API 写值**——与 PopDrop 在 Windows 上"写剪贴板 + 模拟 Ctrl+V"是同一套思路，见 §4.11。

### 2.4 预览 —— macOS 把它做成了系统能力

这是**最不需要对标的**一块。

| 场景 | Windows / PopDrop | macOS |
| --- | --- | --- |
| 空格键快速预览 | 需要**外接 Seer / QuickLook** 才能有（2.8.2，默认 `Off`） | **系统自带**：Finder 里选中文件按空格即预览 |
| 应用内嵌预览 | 自建预览子系统 + 原生 Helper + PDFium / IFilter | `QLPreviewPanel` / QuickLook 扩展，系统统一提供 |
| 缩略图 | Shell 缩略图 + WIC 自建管线 | QuickLook 缩略图扩展 |

也就是说：**PopDrop 里一整个 §5.4 预览子系统（含 PDFium 动态加载、DOCX IFilter、WIC 缩放、12 秒硬超时、分类负缓存）在 macOS 上基本是系统白送的**。第三方 macOS 面板只要调 `QLPreviewPanel` 就能得到与 Finder 一致的预览体验。🔶

### 2.5 选择窗口定位到此 —— 唯一有成熟对标、但机制完全不同的一项

**Default Folder X** 是 macOS 上唯一成熟的对应产品：在标准打开/保存对话框里增强导航、收藏夹、最近文件夹、Finder 窗口定位等功能。

关键差异在于**它怎么做到的**：

- macOS 的 `NSOpenPanel` / `NSSavePanel` 是 **AppKit 对象**，没有可供外部进程发消息的窗口句柄语义。
- **自 macOS 10.15 起，保存面板即使对非沙盒应用也在独立系统进程中显示** ✅，进程边界更加明确。
- 公开资料**没有**证实它使用 APE 注入或 OSAX 脚本附加（那是更老 macOS 时代的可行手段）；有用户/开发者讨论指出 **Default Folder X 5 重写后依赖 macOS 辅助功能（Accessibility）子系统**——通过 AX 通知侦测对话框出现，再操作其可访问元素 ✅（该来源为社区讨论，非官方架构文档，**属证据而非定论**）。
- 现代 macOS 的 SIP、Hardened Runtime、代码签名与库校验，让任意代码注入**变得非常困难** ✅。

**结论**：同一场景在 macOS 上存在，但**实现难度显著更高**，且必须走 Accessibility 这条"窄路"，见 §4.2。

### 2.6 右键菜单与文件操作

macOS 的机制与 Windows 完全不同，且**不是"在别人的窗口里弹自己的菜单"**：

| 手段 | 能力 | 限制 |
| --- | --- | --- |
| **Finder Sync 扩展**（`FIFinderSync`） | 向 Finder 右键菜单添加上下文项，可拿到 `selectedItemURLs()` 与 `targetedURL` | **扩展自身是沙盒的**，能力受限 ✅ |
| **快速操作 / 服务（Services）** | 处理 Finder 选择项 | 一般**没有受支持的方式**把任意动作提升为 Finder 顶层右键项 ✅ |
| **AppleScript / `NSWorkspace`** | 由自己的 App 发起 Finder 操作 | 反过来（往 Finder 塞菜单）不行 |

- 一个实际会踩的坑：**Finder 选择项传进来的 URL 并不自动构成沙盒资源**，沙盒应用要持久访问需要用户经 `NSOpenPanel` 授权、创建 **security-scoped bookmark**（`withSecurityScope`）、持久化、解析后 `startAccessingSecurityScopedResource()`，用完 `stopAccessingSecurityScopedResource()` ✅。
- 也就是说，PopDrop 在 Windows 上"拖进来就拿到真实路径、随便读写"这件事，在 **macOS 沙盒应用里可能直接读不了**——除非用户显式授权过该目录。这是**功能性**差异，不只是实现差异。

### 2.7 文件管理器适配

PopDrop 支持 7 家第三方文件管理器（`[FileManager] Provider`）。macOS 侧生态小得多：

- **Finder 是绝对主导**，且系统提供了标准能力：`NSWorkspace.activateFileViewerSelecting(_:)`（Reveal in Finder）、`NSWorkspace.selectFile(_:inFileViewerRootedAtPath:)`、命令行 `open -R` ✅。
- 第三方替代品主要是 **ForkLift** 与 **Path Finder**；Path Finder 附带 **Reveal** 辅助程序用于"从 Finder 转到 Path Finder" ✅。切换默认文件查看器有 `NSFileViewer` 偏好设置的社区做法，但**非官方文档支持** 🔶。
- `open -R` 对多选**只可靠处理一个文件**，多选建议用 AppleScript `reveal` 或 `NSWorkspace.activateFileViewerSelecting` ✅。

**结论**：适配面从"7 家"降到"1 家主 + 2 家可选"，但系统给了统一 API，整体比 Windows 简单。

### 2.8 终端发送

macOS 上**更简单**，因为两个主流终端都提供官方脚本接口：

- **iTerm2**（`com.googlecode.iterm2`）：AppleScript `write text "..."`，且有 `newline NO` 形式可只发文本不发回车 ✅ —— **正好对应 PopDrop 2.4.1 的"只投送正文、不额外发送回车"**。
- **Terminal.app**（`com.apple.Terminal`）：`do script "..." in front window` ✅。
- 判断前台应用：`NSWorkspace.frontmostApplication`，或 `System Events` 取 `bundle identifier of first application process whose frontmost is true` ✅。

**这是 macOS 唯一一处明显"比 Windows 省事"的场景**：PopDrop 需要靠"顶层窗口类 + 拥有者进程"识别宿主（因为 Windows 终端没有脚本接口），macOS 直接按 bundle identifier 分发即可。

---

## 3. 实现层差异总览

| 维度 | Windows（PopDrop 的做法） | macOS（对等机制） | 差异性质 |
| --- | --- | --- | --- |
| 主程序语言 | AutoHotkey v2 + Ahk2Exe | Swift / Objective-C（AppKit） | 完全不同 |
| 跨进程窗口控制 | `WM_*` / `CDM_*` / `BFFM_*` 消息发往任意 HWND | **无对应机制**，只能走 Accessibility API | ⚠️ **根本差异** |
| 全局热键 | `RegisterHotKey` | Carbon `RegisterEventHotKey`（不需辅助功能权限） | 低 |
| 权限模型 | UIPI（完整性级别） | TCC + App Sandbox（辅助功能 / 输入监控 / 完全磁盘访问） | ⚠️ **根本差异** |
| 拖放数据模型 | OLE `IDataObject` + `CF_*` 剪贴板格式 | `NSPasteboard` + UTI + `NSDraggingSource/Session` | 中 |
| 虚拟文件 / 异步文件 | `FileGroupDescriptorW` + `FileContents` TYMED | `NSFilePromiseProvider` / `NSFilePromiseReceiver` | 中（语义相近） |
| 文件操作 | `IFileOperation` + 进度接收器 | `NSFileManager` / `NSFileCoordinator` | 中 |
| 删除到回收站 | `SHFileOperation` 走回收站 | `NSFileManager.trashItem(at:resultingItemURL:)` | 低 |
| 文件变更监听 | `ReadDirectoryChangesW`（重叠 I/O） | **FSEvents**（等价物）；`NSMetadataQuery` 走 Spotlight | 中（语义不同） |
| 元数据 / 全文检索 | Windows Search / IFilter | **Spotlight**（`NSMetadataQuery`） | ⚠️ macOS 强得多 |
| 文档解析预览 | PDFium、WIC、DOCX IFilter 自建 | **Quick Look 系统提供** | macOS 明显更省 |
| 缩略图 | Shell 缩略图 + WIC 管线 | Quick Look 缩略图扩展 | macOS 更省 |
| 最近文件 | `%APPDATA%\...\Recent` 快捷方式目录 | `sfl3` 文件（`~/Library/Application Support/com.apple.sharedfilelist/`） | 中 |
| 配置与缓存 | INI（UTF-16LE）+ SQLite（`winsqlite3.dll`） | plist / JSON + SQLite（`libsqlite3`）/ GRDB | 低 |
| 界面实现 | 原生 Win32 控件 + 少量 Owner Draw | AppKit / SwiftUI 原生控件 | 低（都倾向原生） |
| 分发 | 单 exe + Ahk2Exe | **`.app` bundle + 代码签名 + 公证**；上架 MAS 需沙盒 | ⚠️ **根本差异** |
| 多语言 | 无（全简中） | 系统要求本地化 | 低 |

---

## 4. 逐项深入：差异到底在哪

### 4.1 进程模型与 IPC —— 差异不大，但 macOS 更倾向单进程

- PopDrop 的进程结构是：AHK 主进程 + 两个常驻/一次性 C++ Helper（`PopDropPreview.exe` / `PopDropTransfer.exe`），通过**共享内存 + 文件系统 IPC**（`request-<generation>.ini` / `ready-<generation>\source-NNNN.ini` + `complete.ini` 哨兵，75 ms 轮询）通信。
- macOS 侧有更顺手的替代：**XPC**（`NSXPCConnection`）、**辅助进程 `NSTask`**、或干脆用 Swift 单进程 + 后台队列。
- 🔶 用文件系统做 IPC（PopDrop 那套"写入中间文件 + 原子改名 + 代际匹配"）在 macOS 上**技术上同样可行**，但属于"把 Windows 限制带过去"的做法——macOS 上 XPC 是标准答案，没必要自己造轮子。

**真正的差异**：PopDrop 之所以拆出 Helper，一个重要原因是 **AHK 无法直接做原生 C++ 能做的事**（PDF 渲染、COM vtable、OLE 拖放）。macOS 上主程序本身就是 Swift/ObjC，**这些能力都在同一个进程里**，Helper 的必要性大幅下降。**只有一个例外**：预览与文档解析仍建议隔离（对应 Quick Look 扩展或 XPC 服务），因为第三方解析器可能崩溃或被挂起，这与 Windows 侧"预览跑在可终止 Helper 里"的动机一致。

### 4.2 跨进程窗口控制 —— **最大的根本差异**

这是整份调研里最关键的一条。

**Windows 的做法**：HWND 是系统级全局对象，任何进程都能 `SendMessage` 过去（受 UIPI 限制）。PopDrop 的"选择窗口定位到此"整个功能就建立在这个能力上：

```ahk
; 概念示意（完整版 §2.9 / §5.5.8）
; Explorer 风格窗口：用地址栏快捷入口，再以 CDM_GETFOLDERPATH 核验
; 旧式树形选择器：SendMessageW(hwnd, BFFM_SETSELECTIONW, TRUE, path)
```

它**不需要注入，不需要目标程序配合**，只要拿到 HWND 就能操作。

**macOS 的做法**：没有 HWND 的等价物，也没有通用跨进程消息。

| 概念 | Windows | macOS |
| --- | --- | --- |
| 目标标识 | `HWND`（系统级） | 无；只能靠 PID / bundle id 定位进程 |
| 通用控制通道 | `SendMessage` / `PostMessage` | **不存在** |
| 语义化控制 | UI Automation / MSAA（较新推荐） | **Accessibility API（`AXUIElement`）** |
| 授权 | UIPI（完整性级别） | 用户显式授予**辅助功能权限**（TCC） |
| 失败模式 | 消息不被支持、UIPI 拦截、指针跨地址空间问题 | 目标未实现可访问性、权限被拒、`kAXErrorNotImplemented` |

公开资料明确指出：**与 macOS `AXUIElement` 最接近的对照物是 Windows 的 UI Automation，而不是 `SendMessage`** ✅。`SendMessage` 更接近"低层跨进程控制通道"。

**对 PopDrop 场景的直接影响**：

| PopDrop 依赖消息的功能 | macOS 上怎么办 | 难度变化 |
| --- | --- | --- |
| 选择窗口定位到此（2.9） | AX 侦测对话框 → 操作其可访问元素（Default Folder X 路线） | **显著变难** |
| 向终端投送文本（2.4.1） | AppleScript / AX，或 `CGEventPost` 模拟 | **变简单** |
| 前置发送到原窗口（2.4） | 剪贴板 + `CGEventPost` ⌘V；原生控件可走 AX 写值 | 持平 |
| 自动隐藏守卫（2.1） | `NSWindow` 的 `windowDidResignKey` / `NSApplication` 激活通知 | **变简单**（进程内即可） |
| 原生控件"手写 COM vtable"（5.1.3） | **不存在这个问题**——AppKit 是正常的 OO API，没机会也没有必要手写 vtable | **变简单** |

反过来说，PopDrop 在 Windows 上为了"在别人的窗口里完成一件事"付出的那些代价——手写 `IDropTarget`/`IDropSource`/`IDataObject` 的 COM vtable、`NumPut` 手搓 `LVGROUP` 结构、按 `A_PtrSize` 分支 x86/x64 布局、原生 `SetTimer` + `WinEvent` 守卫自动隐藏——**在 macOS 上大都不存在**，因为 AppKit 本来就是给进程内用的正常 API。

### 4.3 权限模型 —— 第二个根本差异

| 维度 | Windows | macOS |
| --- | --- | --- |
| 保护机制 | **UIPI**：低完整性进程不能向高完整性进程发受限消息 | **TCC**：辅助功能、输入监控、完全磁盘访问、自动化，逐项用户授权 |
| 何时需要提权 | 只有极少数操作（写系统目录等） | 跨 App 控制、全局键盘监听、访问受保护目录**都要授权** |
| 用户感受 | 一次 UAC，之后基本无感 | 多轮授权弹窗，且**系统设置里可以随时撤销** |
| 沙盒 | 无系统级强制沙盒 | **App Sandbox** 可选但上架 MAS 必需 |
| 失败表现 | 拖放/消息静默失败 | API 调用返回错误，功能整块不可用 |

- PopDrop 在 Windows 上遇到的权限问题是 **UIPI 阻断跨权限拖放**，文档明确"不绕过这项系统安全限制"，要求来源程序与 PopDrop 同权限级别。
- macOS 上对应的是：**没拿到辅助功能授权，几乎一半的功能直接不可用**；没拿到完全磁盘访问，**索引用户目录都做不到**。
- **沙盒是决定性的**：研究显示沙盒应用**可能无法进行不受限的跨进程 AX 操作** ✅。这直接推出 §4.4 的结论。

### 4.4 沙盒决定了产品形态 —— 一条可以直接观察到的规律

把 §2.1 那些产品的分发方式摆在一起看，规律很清楚：

| 产品 | 分发 | 是否沙盒 | 能力边界 |
| --- | --- | --- | --- |
| Yoink | Mac App Store | 是 | 只做**自己的货架**，不操纵别人窗口 |
| Dropover | 官网 + MAS | 官网版更宽 | 货架 + 动作 |
| Unclutter / FilePane / Dropzone | MAS | 是 | 自己的容器 |
| **Default Folder X** | **仅官网直发** | **否** | **唯一能操作别人的打开/保存对话框的产品** |

🔶 **规律**：在 macOS 上，**"跨应用控制别人窗口"与"上架 Mac App Store"基本互斥**。想做 Default Folder X 那样的事，就必须走官网直发 + Developer ID 签名 + 公证 + 引导用户授权辅助功能。

这对 PopDrop 移植的含义很直接：**PopDrop 里最有价值、最难替代的那几项（选择窗口定位、跨应用投送、终端发送）恰好全在"不能上 MAS"的那一侧。**

### 4.5 全局热键 —— 差异不大，但有一个坑

- macOS 上做简单的全局快捷键，**首选 Carbon 的 `RegisterEventHotKey`**：公开资料称它**不需要辅助功能权限，且可以在沙盒应用里使用** ✅。这是 macOS 上一个"老 API 反而更合适"的特例（Carbon 事件管理器虽老但仍在用）。
- **`CGEventTap` / `NSEvent.addGlobalMonitorForEventsMatchingMask`** 更强大（可以看按键内容、做输入拦截），但**需要辅助功能或输入监控授权** ✅。
- 已知坑：`RegisterEventHotKey` 在 **macOS Sequoia 上对某些 Option/Shift 组合回报错误 `-9868`** ✅。

**对 PopDrop 的含义**：PopDrop 的"主快捷键 F2 + 双击直达文本区（400 ms 判定）+ 每工作区独立快捷键"用 `RegisterEventHotKey` 做前两项没问题；**但"双击主快捷键"需要自己维护时间窗**（同 Windows 侧的做法），`RegisterEventHotKey` 只给单次按下事件——这一点两边是一样的。

### 4.6 文件变更监听 —— 语义不同，不只是 API 不同

| | `ReadDirectoryChangesW`（Windows） | **FSEvents**（macOS） |
| --- | --- | --- |
| 粒度 | 默认文件/目录级动作 | 默认**目录树级**，加 `kFSEventStreamCreateFlagFileEvents` 才有文件级 |
| 合并 | 不合并，但内核缓冲区会溢出 | **会合并事件**，官方明确"不是每个操作的完整描述" |
| 历史 | 无 | 可查询历史变更（带上时间点回放） |
| 递归 | 需自行处理 | 天然面向目录树 |

- 公开对比结论：**`ReadDirectoryChangesW` 在 macOS 上最接近的等价物是 FSEvents，而不是 `NSMetadataQuery`** ✅。
- `NSMetadataQuery` / Spotlight 适合"**找出并跟踪符合元数据条件的文件**"，适合做"内容更新于"这类语义，但**依赖 Spotlight 索引**且不保证实时 ✅。

**对 PopDrop 的含义**：PopDrop 的"50–120 ms 事件合并后重扫受影响来源"这套自建去抖逻辑，在 macOS 上**FSEvents 已经帮你做了一部分**；但反过来，PopDrop 精心设计的"网络路径不在刷新关键路径做同步存在性检查""监听溢出后只重建该来源句柄"这些坑，macOS 上依然存在（FSEvents 同样会丢事件、网络卷同样慢）。**§5.2 那一整套扫描缓存方案的动机在 macOS 上大部分仍然成立**，只是实现手段换成 FSEvents + 自建快照。

### 4.7 拖放数据模型 —— 概念映射相当整齐

| Windows / PopDrop | macOS |
| --- | --- |
| `IDataObject` / `IDropTarget` / `IDropSource` | `NSPasteboard` + `NSDraggingSource` / `NSDraggingDestination` / `NSDraggingSession` |
| `CF_HDROP` | `.fileURL`（UTI: `public.file-url`） |
| `CF_UNICODETEXT` / `CF_TEXT` | `.string` / `NSStringPboardType` |
| `FileGroupDescriptorW` + `FileContents`（虚拟文件） | **`NSFilePromiseProvider` / `NSFilePromiseReceiver`** |
| 异步 HDROP（延迟下载） | File Promise 的"延迟生成"语义 |
| `DROPFILES` 结构体 | 无对应物（不需要） |
| `RegisterDragDrop` / `DoDragDrop` | 由 `NSView` 的拖放协议自动接管 |
| `DRAGDROP_S_*` 返回码 | 无对应物，用协议方法返回值表达 |

- `NSFilePromiseProvider` 是**惰性生产者**，`NSFilePromiseReceiver` 是**延迟消费者**；实际文件在**投放时**才生成或下载 ✅。这与 PopDrop 处理"浏览器拖出的图片其实还没下载完"的异步 HDROP 场景**是同一类问题的同一种解法**，只是 macOS 把它标准化了：接收方 `registerForDraggedTypes(NSFilePromiseReceiver.readableDraggedTypes)`，然后**在普通 file URL 之前先处理 promise** ✅。
- **最大简化**：macOS 不需要"手写 COM vtable"。PopDrop 在 Windows 上为 `IDropTarget`/`IDropSource`/`IDataObject` 手搓虚表（用 `CallbackCreate(..., "Fast", N)` + `NumPut` 往 `Buffer` 里填函数指针，还要按 `A_PtrSize` 分 x86/x64 布局）；macOS 侧直接实现协议方法即可。
- **最大新增**：**沙盒下的 URL 访问权问题**（§2.6）——拿到 URL ≠ 有权限读写。

### 4.8 文件操作

| 操作 | Windows / PopDrop | macOS |
| --- | --- | --- |
| 复制/移动（带进度、冲突处理） | `IFileOperation` + `IFileOperationProgressSink` | `NSFileManager` / `NSFileCoordinator`；批量可走 `NSWorkspace` |
| 删除到回收站 | `SHFileOperation` → 回收站 | `NSFileManager.trashItem(at:resultingItemURL:)` → 废纸篓 |
| 永久删除 | `Shift+Delete` 确认后永久 | 直接 `removeItem`（**废纸篓不可用这个坑 macOS 不存在**） |
| 重命名 | 由 Windows Shell 执行 | `FileManager.moveItem` |

**对 PopDrop 的含义**：PopDrop 在 Windows 上刻意"把重名、合并、权限提升、进度、占用、取消与部分完成都交给 Shell 处理"（避免自己用"复制后删除"模拟移动）——这个**设计判断在 macOS 上完全适用**，只是"交给 Shell"变成"交给 `NSFileManager` / `NSFileCoordinator`"。🔶

### 4.9 最近文件

- PopDrop 读 `%APPDATA%\Microsoft\Windows\Recent` 目录下的快捷方式（2.3）。
- macOS 的最近文件在 `~/Library/Application Support/com.apple.sharedfilelist/`：
  - 全局：`com.apple.LSSharedFileList.RecentDocuments.sfl2`（旧）/ **`.sfl3`**（较新）
  - 按应用：`.../com.apple.LSSharedFileList.ApplicationRecentDocuments/com.apple.<bundle-id>.sfl3`
- **`.sfl` 不是普通 plist**，是 Apple 私有的 SharedFileList 格式，需要解析内嵌的 bookmark 数据才能还原路径 ✅；旧的 `LSSharedFileList` API 已废弃且不可靠 ✅。
- 🔶 **因此 macOS 上解析最近文件属于"实现细节，可能随系统版本变化"**——这不是官方承诺的 API 面。

**结论**：这一项 macOS 上**比 Windows 更脆**。PopDrop 在 Windows 上读 Recent 目录是个相对稳定的做法，macOS 侧解析 `sfl3` 是逆向行为。🔶 更稳的替代是**自己记录**最近使用（就像 PopDrop 自己维护"最近目标最多 3 个"那样），或者用 `NSDocumentController` 的最近文档（只覆盖基于文档的应用）。

### 4.10 配置与缓存 —— 差异小

- PopDrop：`config.ini`（UTF-16LE + BOM + CRLF + 六个 `; <PopDrop:area N>` 布局锚点）+ SQLite（系统 `winsqlite3.dll`，WAL 模式，损坏隔离）。
- macOS：plist / JSON 是惯例，SQLite 系统自带 `libsqlite3`（也有 GRDB 这类成熟封装）。
- PopDrop 那套"**无损布局感知的 INI 编辑**"（保留注释、未知键、原子替换 `ReplaceFileW`）在 macOS 上**没有必要**——`UserDefaults` / plist 天然是结构化的，不存在"手改注释被冲掉"的问题。🔶 这是"Windows 生态带来的复杂度"，移植时可以直接砍掉。

### 4.11 跨应用文本注入

PopDrop 的"快速发送 / 前置发送 / 终端发送"三条路径，在 macOS 上的对应做法：

| 手段 | 说明 | 代价 |
| --- | --- | --- |
| **剪贴板 + `CGEventPost(⌘V)`** | Snippet 扩展器的主流做法：备份剪贴板 → 写文本 → 让目标 App 前台 → 合成 ⌘V → 恢复剪贴板 ✅ | 需要辅助功能/输入监控授权；**Secure Input 生效时必须自行暂停**（不能绕过）✅ |
| **Accessibility API 直接写值** | 对支持的原生文本控件更原子、更可靠 ✅ | 依赖目标 App 的可访问性实现质量 |
| **AppleScript / Automation** | iTerm2 `write text ... newline NO`、Terminal `do script` ✅ | 需要 **自动化（Automation）权限** ✅ |

**对 PopDrop 的含义**：

- PopDrop 在 Windows 上为终端单独写了一整个分支（2.4.1：识别宿主 → 头尾 CRLF 清理 → 中文免确认规则 → Console Host 走 `WM_PASTE` / Windows Terminal 走 `Shift+Insert` → 只投送正文不发回车）。macOS 上**识别宿主简化成 bundle identifier 判断**，**投送简化成一行 AppleScript**，但**"头尾空行清理"与"中文免确认"这两条业务规则仍然要自己写**——AppleScript 不知道你要不要保留首尾空行。
- **`Shift+Insert` 那个特殊分支在 macOS 上不存在**：那个分支是为了绕开 Claude Code 这类原始输入 TUI 对 bracketed paste 的处理；macOS 上 iTerm2 的 `write text ... newline NO` 是原生接口。🔶
- **Secure Input 是 macOS 独有的一道坎** ✅：在安全输入框获得焦点时，系统会阻止全局键盘监听与事件注入。负责任的做法是**检测到就暂停自己**，而不是试图绕过——这与 PopDrop 在 Windows 上"安全输入框时不自动粘贴、正文留在剪贴板"的处理**是同一个设计哲学**。

### 4.12 UI 与分发

- **UI**：PopDrop 用原生 Win32 控件 + 极少量 Owner Draw，这个"尽量不自绘"的取向在 macOS 上同样是对的（AppKit 原生控件 + `NSTableView`/`NSCollectionView` 的 group 支持）。PopDrop 手搓 `LVGROUP` 结构的那些工作，在 macOS 上变成设置 `NSTableView` 的 group row。**不需要跨越的鸿沟，但确实省掉一层。**
- **分发**：这是最后一个根本差异。

| | Windows / PopDrop | macOS |
| --- | --- | --- |
| 产物 | 单目录 + `PopDrop.exe`（Ahk2Exe 编译）+ `native\bin\x64|x86` | **`.app` bundle**（内含 `Contents/MacOS` 可执行文件、资源、扩展） |
| 架构 | x64 + x86 两份二进制 | Universal 2（arm64 + x86_64）或分别出包 |
| 签名 | 无强制（可选 Authenticode） | **必须代码签名**，否则 Gatekeeper 直接拒绝 |
| 公证 | 无 | **必须 notarization**，否则用户侧弹警告 ✅ |
| 权限声明 | 无 | `Info.plist` 用途描述字符串 + entitlements |
| 上架 MAS | 不适用 | 需沙盒 → **§4.4 的能力互斥** |

---

## 5. 汇总：哪些更简单、哪些更难、哪些做不了

### 5.1 在 macOS 上**更简单**的

1. **文档预览与缩略图** —— Quick Look 系统提供，PopDrop 那一整套 PDFium / IFilter / WIC 管线不用写。
2. **终端发送** —— iTerm2 / Terminal.app 有官方 AppleScript，且有 `newline NO`，不用像 Windows 那样靠窗口类猜宿主、靠 `Shift+Insert` 绕 bracketed paste。
3. **不用手写 COM vtable** —— `IDropTarget`/`IDropSource`/`IDataObject`、`LVGROUP` 结构、x86/x64 布局分支，全部消失。
4. **自动隐藏** —— `NSWindow` 的失焦通知在进程内就能拿到，不需要原生 `SetTimer` + `WinEvent` 前台钩子这类"绕过 AHK 定时器"的手段。
5. **文件操作** —— `NSFileManager` 是正常 API，不像 `IFileOperation` 那样必须实现一整套 `IFileOperationProgressSink`。
6. **配置读写** —— plist 天然结构化，不需要"布局感知的无损 INI 编辑"。
7. **全文检索** —— Spotlight 是系统级能力，Windows 侧要靠 IFilter 自建。

### 5.2 在 macOS 上**更难**的

1. **选择窗口定位到此（2.9）** —— 从"发窗口消息"降级为"走 Accessibility 侦测 + 操作可访问元素"，且必须在非沙盒下做。这是差异最大的一项。
2. **沙盒下的文件访问** —— 拿到 URL ≠ 有权限；需要 security-scoped bookmark 的完整生命周期管理，用户不授权就是读不了。
3. **最近文件列表** —— 要解析私有的 `.sfl3` 格式，属于"可能随系统版本失效"的实现细节。
4. **权限引导** —— 辅助功能 / 输入监控 / 完全磁盘访问 / 自动化，四项权限要分别在合适的时机引导用户开启，且用户随时可以撤销（**撤销后要让功能优雅降级**）。
5. **分发链路** —— 签名 + 公证 + 权限说明，比"编译出一个 exe"复杂一个数量级。
6. **跨应用文本注入** —— `CGEventPost` 需要授权，Secure Input 生效时必须暂停，Chromium / Electron / 终端 / 密码框各有 fallback（与 Windows 侧一样碎，只是碎在不同的地方）。

### 5.3 在 macOS 上**做不了 / 不该做**的

| 项 | 原因 |
| --- | --- |
| 上架 Mac App Store 且保留全部能力 | 沙盒与跨进程 AX 控制基本互斥（§4.4）🔶 |
| 用代码注入往任意 App 里塞 UI | SIP + Hardened Runtime + 库校验，基本被堵死 ✅ |
| 往 Finder 顶层右键菜单塞任意项 | Finder Sync 扩展能力受限，Services/快速操作没有受支持的方式提升为顶层项 ✅ |
| 绕过 Secure Input 做键盘监听 | 系统明确阻止，负责任的做法是暂停自己 ✅ |
| 用"复制后删除"模拟移动 | 与 PopDrop 自身的设计判断一致地**不应该做**——交给 `NSFileManager` |

---

## 6. 如果要把 PopDrop 的场景搬到 macOS

🔶 以下为基于本调研的推断，未做原型验证。

### 6.1 技术可行性分档

| 档 | 能力 | 判断 |
| --- | --- | --- |
| **A. 直接可做** | 面板 + 来源分栏 + 固定项、文本块卡片、拖入拖出、Quick Look 预览、终端发送、打开方式、文件管理器跳转 | 全部有直接对等机制，无系统级障碍 |
| **B. 能做但要设计** | 全局热键 + 双击判定、FSEvents 扫描与缓存、跨应用文本注入、File Promise 接收、权限引导 | 有对等机制，但语义或权限模型不同，需要重新设计 |
| **C. 显著变难** | 选择窗口定位到此、最近文件侧边栏、沙盒下的任意目录索引 | 依赖 AX / 私有格式 / 用户授权，稳定性和覆盖面都要打折 |
| **D. 需要取舍** | 上架 MAS ↔ 保留全部能力 | 二选一，不能兼得 |

### 6.2 三条产品路线

| 路线 | 能力 | 代价 |
| --- | --- | --- |
| **官网直发（Default Folder X 路线）** | 完整能力，含跨应用控制 | 无 MAS 曝光；必须签名 + 公证；要引导用户开辅助功能权限；用户可能因授权畏难而流失 |
| **MAS 沙盒（Yoink / Dropover 路线）** | 自己的容器：货架、文本块、预览、拖入拖出 | 放弃"操作别人的窗口"（选择窗口定位、跨应用投送受限）；但可上架、安装无摩擦 |
| **菜单栏工具（HighTop / Recent File Picker 路线）** | 快速取用 + 拖入拖出 | 能力最小，但最符合 macOS 使用习惯，且几乎不需要敏感权限 |

### 6.3 对"是否值得移植"的判断

🔶 从调研看，**PopDrop 在 macOS 上的差异化空间比 Windows 上小**：

- Windows 上 PopDrop 填补的空白是"**没有系统级的取用面板**"（资源管理器是重形态，Seer/QuickLook 要外接）。macOS 上这块空白**被系统能力和大量第三方产品共同填掉了**：Quick Look 管预览、Spotlight/Raycast 管查找、Yoink/Dropover/FilePane 管中转、Finder 侧边栏管最近。
- 真正**没有对标**的只剩两处：**① 按"来源分栏"组织的多文件夹面板（而不是一个货架）**；**② 投送到呼出前窗口 / 原输入内容最前方这个精确语义**。而这两处恰好都不是"系统做不到"，而是"没人这么做"。
- 因此更现实的判断是：**直接把 PopDrop 搬过去价值有限；但它的两个设计判断值得借鉴** —— "面板不抢焦点、用完即走"和"投送到呼出前的窗口/位置"。前者 macOS 上用菜单栏形态天然满足，后者是一个可以独立成立的小而美的功能点。

---

## 7. 参考来源

**macOS 对标产品**

- [Yoink — Mac App Store](https://apps.apple.com/us/app/yoink/id457622435?mt=12)
- [Dropover — 官网](https://dropoverapp.com/) · [Mac App Store](https://apps.apple.com/us/app/dropover-easier-drag-drop/id1355679052?mt=12)
- [Unclutter Files — 官网](https://unclutterapp.com/panels/files) · [Mac App Store](https://apps.apple.com/us/app/unclutter/id577085396?mt=12)
- [FilePane — 官网](https://mymixapps.com/filepane) · [Mac App Store](https://apps.apple.com/us/app/filepane-drag-drop-utility/id847515307?mt=12)
- [Dropzone 4 — Mac App Store](https://apps.apple.com/us/app/dropzone-4/id1485052491?mt=12)
- [Notchy](https://notchy.dev/mac-file-drop-app/) · [Dockside（Reddit）](https://www.reddit.com/r/macapps/comments/1gadeow/introducing_dockside_a_simple_file_shelf_beside/)
- [Folder Slice](https://folderslice.com/) · [HighTop](https://hightop.app/)
- [Raycast Snippets 手册](https://manual.raycast.com/snippets) · [Alfred Snippets](https://www.alfredapp.com/help/features/snippets/) · [Espanso](https://github.com/espanso/espanso) · [Refrain](https://refrainformac.com/)
- [Default Folder X 用户指南（PDF）](https://www.stclairsoft.com/DefaultFolderX/guide/EN.pdf) · [6.x 指南（PDF）](https://www.defaultfolder.com/DefaultFolderX/DefaultFolderXGuide.pdf) · [关于其依赖辅助功能的社区讨论](https://www.reddit.com/r/macapps/comments/16riuey)

**Apple 官方文档**

- [AXUIElement](https://developer.apple.com/documentation/applicationservices/axuielement_h) · [AXUIElementCreateApplication](https://developer.apple.com/documentation/applicationservices/1459374-axuielementcreateapplication) · [AXUIElementPerformAction](https://developer.apple.com/documentation/applicationservices/1462091-axuielementperformaction)
- [Accessing files from the macOS App Sandbox](https://developer.apple.com/documentation/security/accessing-files-from-the-macos-app-sandbox) · [withSecurityScope](https://developer.apple.com/documentation/foundation/nsurl/bookmarkcreationoptions/withsecurityscope)
- [Finder Sync App Extension Programming Guide](https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Finder.html)
- [Supporting Drag and Drop Through File Promises](https://developer.apple.com/documentation/appkit/supporting-drag-and-drop-through-file-promises) · [NSFilePromiseProvider](https://developer.apple.com/documentation/appkit/nsfilepromiseprovider) · [NSFilePromiseReceiver](https://developer.apple.com/documentation/appkit/nsfilepromisereceiver)
- [QLPreviewPanel](https://developer.apple.com/documentation/QuickLookUI/QLPreviewPanel?language=objc) · [Quick Look UI](https://developer.apple.com/documentation/QuickLookUI)
- [NSMetadataQuery](https://developer.apple.com/documentation/foundation/nsmetadataquery) · [Searching File Metadata with NSMetadataQuery](https://developer.apple.com/library/archive/documentation/Carbon/Conceptual/SpotlightQuery/Concepts/QueryingMetadata.html)
- [NSWorkspace.activateFileViewerSelecting](https://developer.apple.com/documentation/appkit/nsworkspace/activatefileviewerselecting%28_%3A%29) · [NSWorkspace.selectFile](https://developer.apple.com/documentation/appkit/nsworkspace/selectfile%28_%3A%29) · [NSWorkspace.frontmostApplication](https://developer.apple.com/documentation/appkit/nsworkspace/frontmostapplication)
- [NSSavePanel](https://developer.apple.com/documentation/AppKit/NSSavePanel) · [Using the Open and Save Panels](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/FileSystemProgrammingGuide/UsingtheOpenandSavePanels/UsingtheOpenandSavePanels.html)
- [Automating the User Interface（Mac Automation Scripting Guide）](https://developer.apple.com/library/archive/documentation/LanguagesUtilities/Conceptual/MacAutomationScriptingGuide/AutomateTheUserInterface.html)
- [Microsoft: MSAA 与 UI Automation 对比](https://learn.microsoft.com/en-us/windows/win32/winauto/microsoft-active-accessibility-and-ui-automation-compared)

**技术讨论与实现参考**

- [全局快捷键：Carbon RegisterEventHotKey 对比 CGEventTap](https://dev.to/quicopy/shipping-global-keyboard-shortcuts-on-macos-sandbox-the-part-apple-doesnt-document-57no) · [Go hotkey 包（Carbon 说明）](https://pkg.go.dev/github.com/go-macos/hotkey) · [Sequoia 上 RegisterEventHotKey 的 -9868 问题](https://developer.apple.com/forums/thread/763878)
- [Apple 论坛：全局事件监听与输入监控授权](https://developer.apple.com/forums/thread/811443) · [沙盒应用与辅助功能/输入监控](https://developer.apple.com/forums/thread/724608)
- [CGEvent 模拟按键的原理与限制](https://quietclip.app/blog/cgevent-keystroke-simulation/) · [向指定应用发送粘贴事件](https://stackoverflow.com/questions/51865080/sending-keystroke-event-paste-to-a-specific-application-mac) · [Cocoa 跨应用粘贴的常见实现](https://stackoverflow.com/questions/2680760/how-to-paste-text-from-one-app-to-another-using-cocoa)
- [开源 snippet 管理器实现（含 Secure Input 处理）](https://github.com/wowlocal/snippets)
- [FSEvents / inotify / ReadDirectoryChangesW 对比](https://gity.neullabs.com/blog/fsevents-inotify-readdirectorychangesw-cross-platform/) · [fsnotify/fsevents 说明](https://github.com/fsnotify/fsevents)
- [Finder 上下文菜单方案对比（逆向笔记）](https://github.com/sherman-yang/mac-finder-menu/blob/main/docs/FINDINGS.md) · [沙盒下 FinderSync 文件访问权限问题](https://stackoverflow.com/questions/30276155/read-and-write-access-for-findersync-extension-in-a-sandboxed-environment)
- [在 Finder 中显示并选中文件（多选方案对比）](https://stackoverflow.com/questions/7652928/launch-finder-window-with-specific-files-selected/7669412)
- [解析 .sfl / .sfl3 SharedFileList（Python）](https://gist.github.com/pudquick/4776b4b2075bf9b7e512) · [mac_apt RECENTITEMS 文档](https://github.com/ydkhatri/mac_apt/wiki/RECENTITEMS)
- [iTerm2 AppleScript 文档](https://stage.iterm2.com/documentation-scripting.html) · [Terminal.app 的 do script 用法](https://stackoverflow.com/questions/1870270/sending-commands-and-strings-to-terminal-app-with-applescript) · [Karabiner：常见终端 bundle identifier](https://karabiner-elements.pqrs.org/docs/json/complex-modifications-manipulator-definition/conditions/frontmost-application/)
