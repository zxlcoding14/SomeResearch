# PopDrop 的 Linux 对标调研：场景是否存在、实现差异在哪

> 调研对象：Windows 项目 [hiforrest/PopDrop](https://github.com/hiforrest/PopDrop) 所覆盖的使用场景，在 Linux 上是否有对等场景与产品
> 配套文档：[PopDrop-macOS对标调研.md](PopDrop-macOS对标调研.md)（macOS）、[PopDrop-功能点与技术方案分析.md](PopDrop-功能点与技术方案分析.md)（功能与技术方案）、[PopDrop-功能点清单-简化版.md](PopDrop-功能点清单-简化版.md)（功能速览）
> 调研方式：**公开资料检索 + API/协议语义比对**。Linux 侧结论来自 freedesktop 规范、man 手册、项目仓库与公开技术讨论；未在 Linux 上安装或实测任何产品，也未编写代码验证。
> 证据等级标注：✅ = 有公开资料直接印证；🔶 = 基于 API/协议语义与公开资料的推断，未直接验证。
> **一句话前提**：Linux 不是一个平台，是"X11 / Wayland × GNOME / KDE / wlroots…"的组合。本文所有结论都受这个前提约束，凡与它相关的都会显式说明。

---

## 1. 结论速览

### 1.1 三句话结论

1. **场景覆盖是三个平台里最差的** —— PopDrop 最核心的那类场景（拖放中转站）在 Linux 上**几乎是空白**：唯一直接对标的产品 **KDE FileStash 至今仍在开发中、尚未发布** ✅；macOS 上有七八家成熟商业产品，Windows 上有 PopDrop 本身。
2. **但标准化程度在几个点上反而是三者中最好的** —— 文件管理器定位有跨桌面的 D-Bus 标准接口 `org.freedesktop.FileManager1` ✅，最近文件有公开规范（XBEL）✅，回收站有公开规范 ✅，全局快捷键有 portal 标准 ✅。Windows 靠私有 API，macOS 靠注入或私有格式。
3. **最大的坑不是权限，而是"设计上就不允许"** —— **"没有客户端能读取另一个窗口"是 Wayland 的核心安全属性，通用的 `xdotool`/`wmctrl` 等价物被刻意设计为不可能实现** ✅。这不是用户授权就能解决的问题（不像 macOS 的 TCC），而是协议层面的排除。同一份代码要在 X11 与 Wayland 下走两条完全不同的路。

### 1.2 能力对照表

| PopDrop 能力（完整版章节） | Linux 是否存在同场景 | 代表产品 / 机制 | 实现路径差异 |
| --- | --- | --- | --- |
| 呼出面板取用文件（2.1） | 🔶 部分 | Albert、Ulauncher、Rofi、Kupfer | 高：只有"启动器"形态，没有"分栏浏览已有目录"的面板 |
| 拖放中转站（2.1 / 2.7.4） | ⚠️ **品类几乎空白** | **KDE FileStash（未发布）**、CopyQ、Klipper | 高：没有成熟产品可参考 |
| 来源分栏 + 固定项（2.3 / 2.5） | 🔶 无直接对标 | 无 | 高 |
| 文本块工作区（2.4） | ✅ 存在 | **Espanso**（Linux 是主场）、AutoKey | 中：形态是"关键字展开"而非"卡片浏览 + 发送" |
| Windows 终端兼容发送（2.4.1） | ⚠️ 无标准接口 | `xdotool type` / `wtype` / `ydotool` / `wdotool` | **高**：与 Windows 处境最像，要合成输入 |
| Launcher 模式（2.6） | ✅ 存在 | Rofi、Albert、Ulauncher、`.desktop` 文件 | 低 |
| 外部内容投放 / 下载（2.7.3 / 2.12） | 🔶 部分 | `text/uri-list` + 拉取式传输 | 中高：**无 file promise 等价物**（见 §3.4） |
| 内置文件预览（2.8.1） | ⚠️ 碎片化 | **GNOME Sushi**、Dolphin 内建预览 | 中：能力有，但不跨桌面、且已知有兼容问题 |
| 外部空格键预览（2.8.2） | ⚠️ 同 macOS | GNOME Sushi = 空格预览 | 低：GNOME 下系统-ish，其他桌面无 |
| 选择窗口定位到此（2.9） | ❌ **无对标** | 无（`~/.config/gtk-3.0/bookmarks` 是唯一侧门） | **高到不可行** |
| 右键菜单与文件操作（2.10） | ✅ 存在 | 各文件管理器内建 + 服务菜单 | 中：无统一扩展机制 |
| 打开方式与工具动作（2.11） | ✅ 存在 | `xdg-open`、`.desktop` 文件、MIME 关联 | 低 |
| 文件管理器适配（2.13） | ✅ **标准化最好** | `org.freedesktop.FileManager1`（D-Bus） | **低**：一条标准接口通吃 Nautilus/Dolphin/Thunar |
| 缓存、刷新、变更监听（2.16） | ✅ 存在 | **inotify**（+ fanotify） | 中高：inotify 非递归，逐目录 watch（见 §3.5） |
| 最近文件侧边栏（2.3） | ✅ **有公开规范** | XDG Recent File Storage Spec（`recently-used.xbel`） | 低：格式是文档化的，优于 macOS |

### 1.3 三平台横向对比（关键轴）

| 轴 | Windows（PopDrop） | macOS | Linux |
| --- | --- | --- | --- |
| 同类产品成熟度 | 中（PopDrop 自身） | **高**（Yoink/Dropover/FilePane…） | **低**（FileStash 未发布） |
| 跨进程窗口控制 | `SendMessage`（HWND 全局） | Accessibility API（`AXUIElement`） | X11 可以 / **Wayland 被设计性禁止** |
| 该能力的授权代价 | UIPI（完整性级别） | TCC 辅助功能授权 | X11 无授权 / Wayland 无路径 |
| 全局热键 | `RegisterHotKey`，统一 | `RegisterEventHotKey`，统一 | **按会话类型分两套** |
| 预览能力 | 自建（PDFium/IFilter/WIC） | **系统 Quick Look，统一** | GNOME Sushi，**不跨桌面** |
| 文件管理器定位 | 7 家 provider 各写一套 | Finder + 2 家，系统 API | **一条 D-Bus 标准接口** |
| 最近文件 | 私有目录（相对稳定） | 私有 `.sfl3`（逆向） | **公开规范（XBEL）** |
| 文件删除 | 回收站，运行时才知道不可用 | 废纸篓 API | 有规范，**可提前查询 `CAN_TRASH`** |
| 沙盒 | 无系统级强制 | 可选，但上架 MAS 必需 | **Flatpak 可选；X11 环境下等于没有** |
| 分发复杂度 | 低（单 exe） | 高（签名 + 公证） | **中到高**（多发行版 / Flatpak 权限） |

---

## 2. 场景层：Linux 上有什么

### 2.1 拖放中转站 —— Linux 上最大的空白

这是与 macOS 反差最强烈的一条。

| 平台 | 该品类的状态 |
| --- | --- |
| macOS | Yoink、Dropover、Unclutter、FilePane、Dropzone、Notchy、Dockside… ✅ 成熟品类 |
| Windows | PopDrop 自身；同类还有若干 |
| **Linux** | **唯一直接对标是 KDE FileStash，且"仍在开发中、尚未发布"** ✅ |

现有可用的替代都**不是同一件事**：

- **CopyQ** —— 跨平台**剪贴板管理器**，能存文件与剪贴板内容、分标签组织、支持拖放 ✅。但定位是剪贴板历史，不是"文件货架"。其文档还提到**部分功能在 Wayland 或 GNOME 下不能完全工作** ✅。
- **Klipper** —— KDE Plasma 内建剪贴板管理器，能保留复制的文件条目 ✅，但同样不是持久化的拖放暂存区。

> 🔶 值得注意的方向性差异：macOS 上这个品类繁荣，一个现实原因是**它不需要特殊权限**（自己的窗口 + 标准拖放）；而 Linux 上缺席，可能更多是**生态/商业动机**问题而非技术问题——技术上门槛并不比 macOS 高。这个推断我没有直接证据，仅作为观察记录。

### 2.2 快速取用面板

有大量启动器，但**没有"浏览已有目录分栏"的面板**：

| 产品 | 形态 |
| --- | --- |
| **Albert**、**Ulauncher**、**Kupfer**、**Synapse**、**Rofi** | 键盘唤起 + 搜索/启动 |
| **Rofi** | 可脚本化的通用选择器，常被当作面板基座 |
| `.desktop` 文件 + 应用菜单 | 系统级启动入口 |

**形态差异**：这些是"**输入名字 → 启动**"，PopDrop 是"**浏览目录 → 拖走**"。前者在 Linux 上已经很成熟（GNOME 的 Activities、KDE 的 KRunner 都是系统自带），后者没有对标。

### 2.3 文本块 / Snippet —— Espanso 的主场

- **Espanso** —— **开源（Rust）跨平台文本扩展器，Linux 是它的主场** ✅。系统级 snippet、日期展开、YAML 配置、扩展包生态。
- 还有 **AutoKey** 等 Linux 传统自动化工具。
- 形态仍是"**打缩写自动替换**"，与 PopDrop "打开面板 → 找卡片 → 发送"不同——这一点**与 macOS 完全一致**（Raycast/Alfred/Espanso 同属一类）。

### 2.4 预览 —— 有对标，但碎片化

- **GNOME Sushi 就是 Linux 的 Quick Look**：在 Nautilus（Files）里选中文件按**空格**即预览，支持常见图片、视频、音频、PDF、文本 ✅。GNOME 设计文档明确把 Sushi 与 Quick Look 描述为同一种空格预览工作流 ✅。
- 但它**只在 GNOME/Nautilus 下成立**：
  - 已知有兼容问题，公开报道提到 **Ubuntu 26.04 上 Sushi 的空格预览失效**并有持续修复 ✅。
  - KDE 侧走自己的路：**Dolphin 内建预览面板**，不是 Sushi。
  - XFCE/Thunar、其他文件管理器各有一套。

**与 macOS 的关键差异**：macOS 的 Quick Look 是**系统统一能力**，任何 App 都能调 `QLPreviewPanel`；Linux 上预览是**文件管理器的私有功能**，没有系统级的统一预览 API。🔶

> 对 PopDrop 的含义：PopDrop 需要**外接 Seer/QuickLook** 才有空格预览；Linux 上如果照搬，得**按桌面分别对接**（GNOME 对 Sushi、KDE 对 Dolphin）——比 Windows 还碎。

### 2.5 选择窗口定位到此 —— 没有对标

这是**三个平台上 PopDrop 最独特的功能**：

| 平台 | 是否有对标 |
| --- | --- |
| Windows | PopDrop 自身（`CDM_GETFOLDERPATH` / `BFFM_SETSELECTIONW` / `WM_SETTEXT`） |
| macOS | Default Folder X（唯一，走 Accessibility） |
| **Linux** | **没有对标产品** |

Linux 上的文件选择器现状：

- **GTK 传统对话框**读 `~/.config/gtk-3.0/bookmarks`（每行一个 `file://` URI + 可选显示名）✅ —— 这是唯一一条"从外部影响对话框"的侧门：**写书签**，而不是发送导航指令。
- **portal 时代这条路不一定通**：GTK 3 的 `GtkFileChooserNative` 在有 `org.freedesktop.portal.FileChooser` 时**会走 portal**，对话框由独立的 portal 后端进程显示 ✅；此时 `~/.config/gtk-3.0/bookmarks` **不一定是那个对话框真正读的文件**（取决于后端是 `xdg-desktop-portal-gtk` 还是 GNOME/KDE 后端）✅。
- portal 的 FileChooser 接口**只暴露 `current_folder` / `current_file` / 过滤器等选项，且是给调用方用的**，**没有定义书签配置接口**，更没有"让第三方导航一个已经打开的对话框"的接口 ✅。

🔶 **结论**：Linux 上"选择窗口定位到此"**做不了**，最多做到"往书签里塞一条，让用户自己去点"，而这与 PopDrop"点一下就导航过去"的体验差着一个量级。

### 2.6 文件管理器定位 —— Linux 标准化最好的一个点

PopDrop 支持 7 家文件管理器、各写一套定位逻辑（`dopusrt.exe`、`TOTALCMD64.EXE`、`-C`、`/C`…）。Linux 上这件事有**跨桌面的 D-Bus 标准接口**：

```
接口：org.freedesktop.FileManager1
对象：/org/freedesktop/FileManager1
方法：ShowItems(uris, startupId)        → 打开所在文件夹并选中
      ShowFolders(uris, startupId)      → 打开指定文件夹
      ShowItemProperties(uris, startupId)
```

```bash
gdbus call --session \
  --dest org.freedesktop.FileManager1 \
  --object-path /org/freedesktop/FileManager1 \
  --method org.freedesktop.FileManager1.ShowItems \
  "['file:///home/user/Documents/example.txt']" ""
```

- **Nautilus、Dolphin、Thunar 等主流文件管理器都支持** ✅（行为可能因桌面/版本略有差异）。
- 注意要传**正确转义的 file URI**，不要简单拼接 `file://` + 原始路径 ✅。

**对比**：

| 平台 | 定位机制 | 需要几家适配 |
| --- | --- | --- |
| Windows | 每家有各自的命令行接口 | **7 家**（PopDrop 现状） |
| macOS | `NSWorkspace.activateFileViewerSelecting`（Finder）；第三方需各自 helper | 1 家主 + 2 家可选 |
| **Linux** | **一条 D-Bus 标准接口** | **1 条接口通吃** |

🔶 代价是**适配深度不如 Windows 那套**：标准接口只给了"显示并选中"，没有 Total Commander 那种"在当前源面板打开"的细粒度控制——那需要各家私有接口。

### 2.7 终端发送 —— 没有接口，必须合成输入

- **终端模拟器普遍不提供"往已有窗口的 shell 注入文本"的可移植 D-Bus API** ✅。D-Bus 主要用于启动或控制窗口，**不是往 PTY 写字节**。
- 唯一干净的做法是**自己启动终端**，直接写它的标准输入：
  ```bash
  printf '%s\n' 'echo hello' | gnome-terminal -- bash
  ```
  ✅ ——但这不适用于"用户已经开着的终端"。

对已有终端，只能合成输入，且要按会话类型选工具：

| 环境 | 工具 |
| --- | --- |
| X11 | `xdotool type` |
| wlroots 系（Sway、Hyprland） | `wtype`（virtual-keyboard 协议） |
| GNOME Wayland | `wdotool`（需 GNOME/libei 配置）或 `ydotool` |
| KDE Plasma Wayland | `wdotool` / `ydotool` / KWin 脚本 |
| 需要可靠输入任意 Unicode | **剪贴板 + `wl-copy` 再粘贴更可靠**（终端常用 `Ctrl+Shift+V` 而非 `Ctrl+V`）✅ |

- `ydotool` 走 `/dev/uinput`，需要 `ydotoold` 守护进程与设备访问权限（udev 规则或 input/uinput 组）✅。
- `wtype`/`ydotool`/`wdotool` **都是往当前焦点窗口发送，不能按窗口 ID 定向** ✅。

**与 Windows 的对比**：PopDrop 在 Windows 上靠"顶层窗口类 + 拥有者进程"识别宿主，再用 `WM_PASTE` 或 `Shift+Insert` 定向投送——**Linux 上连"定向"这一步都做不到**，只能"先确保焦点正确，再往焦点发"。这与 macOS 的 `CGEventPost` 处境相近，但比 macOS 更糟：macOS 至少能用 bundle identifier 稳定识别前台 App，Linux 的 Wayland 下拿前台窗口信息都要靠 compositor 私有接口。

---

## 3. 实现层差异

### 3.1 X11 vs Wayland —— 根本分界线

**这是整份调研里最关键的一条，也是 Linux 与 macOS 最大的不同**：macOS 的问题是"要授权"，Linux 的问题是"协议上就没有"。

| | X11 | Wayland |
| --- | --- | --- |
| 客户端能否枚举其他窗口 | **能** | **不能** |
| 能否读取其他窗口内容/元数据 | **能** | **不能** |
| 能否向特定窗口注入输入 | **能** | **不能** |
| 能否任意移动/缩放/聚焦其他窗口 | **能** | **不能**（须 compositor 或私有特权接口） |
| 全局工具 | `xdotool`、`wmctrl` | **无通用等价物** |
| 安全定位 | 无边界（任何客户端可键盘记录） | secure-by-design |

公开资料明确表述：**"没有客户端能读取另一个窗口"是 Wayland 的核心安全属性，完全通用的 `xdotool`/`wmctrl` 等价物在标准 Wayland 协议下被有意设计为不可能** ✅。

**Wayland 下的替代路径都是 compositor 私有的、且能力参差** ✅：

| 桌面 | 可行路径 |
| --- | --- |
| KDE Plasma | KWin 脚本，或 `kdotool` 之类工具 |
| GNOME | Shell 扩展、D-Bus 接口 |
| wlroots 系 | 部分支持 foreign-toplevel-management 协议（支持度与权限各不相同） |
| 仅输入 | `wtype`、`ydotool`、`wdotool` —— 但**无法按窗口 ID 定向** |

**⚠️ Xwayland 不是后门**：通过 Xwayland 运行的 X11 应用受 Xwayland 约束，**原生 Wayland 应用不会因此变成 X11 窗口**；而且 X11 机制**不会自动获得 compositor 级别的权限**，因为 Wayland compositor 仍是输入的最终权威 ✅。

> **对 PopDrop 的含义**：PopDrop 的"选择窗口定位到此"整个功能建立在"拿到 HWND 就能操作"之上。在 X11 下这件事**勉强可行**（`xdotool` + X11 属性），在 Wayland 下**不可行**，且不是权限问题——让用户授权也解决不了。这意味着这份功能在 Linux 上要么只支持 X11 会话，要么放弃。

### 3.2 全局热键

| 会话 | 机制 | 代价 |
| --- | --- | --- |
| X11 | **`XGrabKey`**：向 X server 请求"无论焦点在哪都把匹配按键给我" | 直接、无授权 |
| Wayland | **`org.freedesktop.portal.GlobalShortcuts`**：通过 D-Bus 注册，由 portal/compositor 负责实际检测，激活时回调 `Activated`/`Deactivated` 信号 ✅ | 依赖 portal 后端 + 桌面 + 应用三方支持 |

- Wayland 下**客户端无法直接抓取全局键盘输入**，compositor 拥有输入分发权并有意阻止任意客户端观察全局按键 ✅。
- 实践问题：Electron 的 `globalShortcut` 文档就明确区分了"X11 直接从 X server 抓取"与"Wayland 通过 portal 注册" ✅；Electron 仓库里有 portal 集成的已知兼容问题（涉及应用 ID 与新版 GNOME）✅。说明这条路**在真实项目里是有摩擦的**。

**与 macOS 的对比**：macOS 一个 Carbon `RegisterEventHotKey` 就通吃全平台；**Linux 要在两个完全不同的机制间分支**，且 Wayland 那套的效果取决于用户的桌面环境。

### 3.3 权限模型 —— Linux 是两个极端

| 会话/打包 | 权限模型 | 后果 |
| --- | --- | --- |
| **X11（传统 .deb / AppImage）** | **基本没有边界** | 功能最自由，安全最差（任何客户端可键盘记录、读取他窗内容） |
| **Wayland** | secure-by-design，功能被限制 | 安全最好，但跨窗口能力**被协议排除** |
| **Flatpak** | 沙盒 + portal 中介，需显式声明 `--filesystem=` | 默认读不了任意宿主文件；`--filesystem=home`/`host` 大幅削弱沙盒 ✅ |
| **Snap** | 类似的接口授权模型 | 同上 |

- Flatpak 的 portal 机制：应用请求"打开/保存文件"时，**宿主侧文件选择器可能显示整个文件系统，但这不代表 Flatpak 应用本身能读整个文件系统**——它通常只能访问用户选中的文件或显式授予的路径，文件通过 portal 受控路径（如 `/run/user/$UID/doc/...`）暴露 ✅。
- **portal 只在应用真的走 portal 时才有用**：直接访问 `/home`、`/media` 或自定义目录的应用，仍然需要对应的 Flatpak 文件系统权限 ✅。因此不少 Flatpak 为了兼容性申请了很宽的权限，实际安全收益被削弱 ✅。

**对 PopDrop 的含义**：PopDrop 的核心是"索引用户指定的任意目录"。在 Flatpak 下这意味着 `--filesystem=home` 或更宽——**沙盒就形同虚设了**；而传统 `.deb`/AppImage 下没有沙盒问题，但也就没有 Wayland 下的跨窗口能力。**两者不可兼得，而且是正交的两个限制**。

### 3.4 拖放数据模型 —— 有惰性传输，但没有 file promise

| Windows / PopDrop | Linux（X11 / Wayland） |
| --- | --- |
| `IDataObject` / `IDropTarget` / `IDropSource` | XDND（X11）/ `wl_data_device`、`wl_data_source`、`wl_data_offer`（Wayland） |
| `CF_HDROP` | **`text/uri-list`** |
| `CF_UNICODETEXT` | `text/plain;charset=utf-8` 等 MIME |
| `FileGroupDescriptorW` + `FileContents` | **无标准等价物** ⚠️ |
| 异步 HDROP（延迟下载） | 拉取式 MIME 传输可部分覆盖，但**语义不等价** |
| `RegisterDragDrop` / `DoDragDrop` | 由 toolkit（GTK/Qt）封装的拖放 API |

**核心机制**：Wayland 的数据传输是**拉取式**——源用 `wl_data_source.offer` 声明格式，目的地用 `wl_data_offer.accept` 选择，**只有目的地调用 `receive` 时源才写入**数据（通过文件描述符）✅。

🔶 **这本身就是一种懒惰/延迟传输**：源不必须在拖拽开始时就把数据准备好。但它**不等价于 file promise**：

- **Wayland 基础协议里没有专门的文件承诺协议**（不像 X11 有 X Direct Save 这类机制）✅。
- 应用可以自己约定"先给一个临时/占位文件的 URI，之后异步填充内容"，**但这是应用约定，不是标准化的 file promise 机制** ✅。
- 关键差异：**Wayland 的传输是拉取式的，目的地可能多次调用 `receive`，甚至可能在 `drop` 之前就调用**，源必须能按需生成并可重入 ✅。

**与 macOS 的对比**：macOS 有标准化的 `NSFilePromiseProvider` / `NSFilePromiseReceiver`（惰性生产者 / 延迟消费者）；Linux **没有对应标准**。PopDrop 那个"异步 HDROP 延迟下载 + 目标目录认领 + 图片质量收敛"的复杂场景，在 Linux 上**没有现成机制可依**，只能自己约定临时文件协议。🔶

### 3.5 文件变更监听 —— inotify 非递归，代价比 Windows 高

| | `ReadDirectoryChangesW`（Windows） | **inotify**（Linux） |
| --- | --- | --- |
| 递归 | 单句柄覆盖整个子树 | **内核层面不递归，必须逐目录加 watch** ✅ |
| 递归实现 | 系统提供 | **用户态实现**（`inotifywait -r` 就是这么做的）✅ |
| 新目录竞态 | — | **新目录必须先被发现再加 watch，存在"事件发生在新 watch 装上之前"的竞态窗口** ✅ |
| 资源上限 | 内核缓冲区溢出 | `fs.inotify.max_user_watches`、`max_user_instances`、`max_queued_events` ✅ |

**fanotify 可以避免逐目录 watch**：通过标记整个 mount 或 filesystem 来覆盖整棵树，且是**无竞态**的方式 ✅。但：

- **5.13 之前（以及相关 stable 分支的 5.10.220 之前）`fanotify_init()` 需要 `CAP_SYS_ADMIN`** ✅；
- 新内核允许非特权 fanotify，但**受限**：不能做 mount/filesystem 标记、不能做 permission 事件、队列与标记数受限、必须使用 file-handle 上报 ✅；
- `FAN_UNLIMITED_QUEUE` / `FAN_UNLIMITED_MARKS` 仍然需要 `CAP_SYS_ADMIN` ✅；
- fanotify **不上报 `mmap()`/`msync()`/`munmap()` 引起的变更**，**不捕获远程网络文件系统事件**，队列同样会溢出 ✅。

> **对 PopDrop 的含义**：PopDrop §5.2 那一整套扫描缓存方案（递归扫描跳过符号链接、监听溢出只重建对应来源句柄、网络路径不在刷新关键路径做同步存在性检查、代际 + 指纹三重匹配后才采纳）——**这些坑在 Linux 上一个不少，而且 inotify 还额外多了"逐目录 watch 的数量上限"和"新目录竞态"两个 Windows 上没有的问题**。§5.2 的设计动机在 Linux 上**不但成立，还更强**。

### 3.6 最近文件 —— 有公开规范，比 macOS 好

- Linux 有 **Recent File Storage Specification**（freedesktop 官方规范）✅。
- 位置：`$XDG_DATA_HOME/recently-used.xbel`，未设置时即 `~/.local/share/recently-used.xbel` ✅。
- 格式：**XBEL/XML**，带 `bookmark` 与 `mime` 命名空间 ✅：

  ```xml
  <bookmark href="file:///home/user/document.txt"
            added="2026-09-20T12:00:00Z"
            modified="2026-09-20T12:00:00Z"
            visited="2026-09-20T12:00:00Z">
    <info><metadata><mime:mime-type type="text/plain"/></metadata></info>
  </bookmark>
  ```

| 平台 | 最近文件的可得性 |
| --- | --- |
| Windows | 私有目录（`%APPDATA%\...\Recent` 下的快捷方式），相对稳定 |
| macOS | 私有 **`.sfl3`** SharedFileList 格式，需解析内嵌 bookmark，**属逆向行为** |
| **Linux** | **公开规范 + 文档化 XML 格式**，最好 |

🔶 **但覆盖不全**：这个规范主要由 **GTK 系应用**写入；KDE 生态用自己的机制。所以"最近文件"在 Linux 上格式标准但**内容不全**——这与 Windows 侧"Recent 目录只管一部分程序"是同类问题。🔶 更稳的做法仍是**自己记录最近使用**（PopDrop 本身就自己维护"最近目标最多 3 个"）。

### 3.7 文件操作

| 操作 | Windows / PopDrop | Linux |
| --- | --- | --- |
| 删除到回收站 | `SHFileOperation` → 回收站；**运行时才知道不可用** | `GFile.trash()` / `gio trash`；**有 Freedesktop Trash Specification** ✅；**可提前用 `G_FILE_ATTRIBUTE_ACCESS_CAN_TRASH` 查询能否回收** ✅ |
| 沙盒下删除 | — | `org.freedesktop.portal.Trash`（通过文件描述符）✅ |
| 复制/移动 | `IFileOperation` + 进度接收器 | GIO `GFile` 系列（`gio copy` / `gio move`），或 `NSFileManager` 的对位物 |
| 回收站布局 | 系统管理 | 规范定义：`.trashinfo` 元数据 + 每文件系统回收站位置 ✅ |

- 官方建议用 **`GFile.trash()`** 这个高层 API，而**不是**手工往 `~/.local/share/Trash/files` 里搬文件——GIO 会为不同文件系统/后端选择正确的回收站实现 ✅。
- **比 Windows 好的地方**：`CAN_TRASH` 属性让程序能**提前**知道能不能回收，而不是像 PopDrop 那样必须在操作时才发现"回收站不可用"并拒绝降级为永久删除。

### 3.8 分发

| 方式 | 沙盒 | 与 PopDrop 能力的关系 |
| --- | --- | --- |
| **传统 `.deb` / `.rpm`** | 无 | 能力最大（受会话类型限制，不受打包限制） |
| **AppImage** | 无（除非自己套 Firejail/bubblewrap 等）✅ | 同上，但更便携 |
| **Flatpak** | **有** | 需要 `--filesystem=` 授权；索引任意目录意味着宽权限，**沙盒收益被削弱** ✅ |
| **Snap** | 有（接口授权模型） | 同上 |
| 上架"应用商店" | 各自发行版 | Linux 没有 macOS MAS 那样的单一守门人，但也没有单一分发渠道 |

🔶 **与 macOS 的关键差异**：macOS 是"**沙盒 ↔ 能力**"二选一（§4.4 of macOS 文档），Linux 是**三维正交**：会话类型（X11/Wayland）× 打包方式（沙盒/非沙盒）× 桌面环境（GNOME/KDE/…）。**要覆盖的组数远多于 macOS。**

---

## 4. 汇总：哪些更简单、哪些更难、哪些做不了

### 4.1 在 Linux 上**更简单**的

1. **文件管理器定位** —— 一条 `org.freedesktop.FileManager1` D-Bus 接口通吃 Nautilus/Dolphin/Thunar，不用像 Windows 那样为 7 家各写一套 ✅。
2. **最近文件** —— 有公开规范与文档化 XML 格式，不用像 macOS 那样逆向 `.sfl3` ✅。
3. **回收站** —— 有公开规范，且能**提前查询** `CAN_TRASH`；"回收站不可用"这个坑比 Windows 好处理 ✅。
4. **不用手写 COM vtable** —— 与 macOS 同理，GTK/Qt 是正常 OO API。
5. **不用签名公证** —— 传统 `.deb`/AppImage 分发没有 macOS 那套签名 + 公证链路。
6. **预览/缩略图** —— GNOME 下 Sushi 提供了与 Quick Look 类似的能力，不用自建 PDFium 管线（代价是只覆盖 GNOME）。

### 4.2 在 Linux 上**更难**的

1. **X11 / Wayland 双路实现** —— 全局热键、窗口控制、输入注入、拖放细节都要按会话类型分支，**且这是运行期才知道的**。
2. **选择窗口定位到此** —— 没有对标产品，portal 时代的对话框由独立进程显示且不读 GTK 书签，**基本不可行**。
3. **终端定向投送** —— 没有接口，只能合成输入；且 `wtype`/`ydotool`/`wdotool` **都不能按窗口 ID 定向**，只能依赖焦点正确。
4. **递归文件监听** —— inotify 逐目录 watch + 新目录竞态 + watch 数量上限；fanotify 能解决递归但要权限或牺牲能力 ✅。
5. **桌面环境适配** —— 两个会话类型 × 多套桌面 × 多套文件管理器，**组合数远大于 macOS**。
6. **打包与权限** —— Flatpak 下要为用户目录申请宽权限（削弱沙盒），不通用的发行版格式也让分发复杂。

### 4.3 在 Linux 上**做不了 / 不该做**的

| 项 | 原因 |
| --- | --- |
| **Wayland 下跨窗口读取/控制** | **协议层面有意排除，通用等价物被设计为不可能** ✅；用户授权也解决不了 |
| 依赖 Xwayland 获得旧能力 | Xwayland 不赋予 compositor 级权限；原生 Wayland 应用不会变成 X11 窗口 ✅ |
| 非特权 fanotify 做全挂载点监控 | 需要 `CAP_SYS_ADMIN` 或受限模式（无 mount/filesystem 标记）✅ |
| 靠"写 GTK 书签"实现选择窗口定位 | portal 后端不一定是读取该书签的那个进程 ✅；且体验与"点击即导航"差一个量级 |
| 手工往 `~/.local/share/Trash/files` 搬文件 | 规范 + GIO 明确建议用 `GFile.trash()` 让 GIO 选择正确实现 ✅ |
| 期待单一"Linux 版"覆盖所有人 | 会话类型 × 桌面 × 打包方式三维正交，**不存在一个默认组合** |

---

## 5. 如果要把 PopDrop 搬到 Linux

🔶 以下为基于本调研的推断，未做原型验证。

### 5.1 技术可行性分档

| 档 | 能力 | 判断 |
| --- | --- | --- |
| **A. 可行且比 Windows 简单** | 文件管理器定位（标准 D-Bus）、最近文件（公开规范）、回收站（规范 + 可查询）、打开方式 | 有标准机制，工作量小于 Windows |
| **B. 可行但要看会话/桌面** | 全局热键（X11 `XGrabKey` / Wayland portal）、预览（GNOME Sushi 或按桌面自建）、拖放（XDG/wayland 协议） | 有机制，但要分支，效果取决于用户环境 |
| **C. 显著变难** | 递归扫描与变更监听（inotify 逐目录 + 竞态 + 上限）、终端投送（无定向） | 能做，但稳定性和覆盖面要打折 |
| **D. 只在 X11 可行** | 选择窗口定位、任何"读取/控制其他窗口"的能力 | **Wayland 下协议性不可行** |

### 5.2 三条现实路线

| 路线 | 能力 | 代价 |
| --- | --- | --- |
| **X11 专精** | 能力最全（接近 Windows 版），跨窗口操作可行 | 面向存量 X11 用户；新装的主流发行版越来越多默认 Wayland 🔶 |
| **Wayland 优先** | 符合方向、安全模型良好 | 必须放弃"跨窗口控制"整类功能；核心差异化被砍掉一半 |
| **Flatpak 分发** | 安装方便、沙盒可审计 | 索引任意目录需宽 `--filesystem=` 权限，沙盒收益被削弱 ✅ |

### 5.3 对"是否值得移植"的判断

🔶 综合看，**Linux 是三个平台里最不划算的移植目标**：

- **能力上限最低** —— Wayland 下"跨窗口操作"被协议排除，而这是 PopDrop 差异化最重的一块；X11 下虽然可行，但 X11 是被安全模型判过死刑的存量技术。
- **生态最分散** —— macOS 只需处理"沙盒 / 非沙盒"两态；Linux 要处理会话类型 × 桌面 × 打包方式的三维组合，**测试矩阵最大**。
- **产品空白最大，但需求验证最弱** —— 拖放中转站品类几乎空白（FileStash 未发布），这既可能说明"有空间"，也可能说明"Linux 用户不觉得需要"。🔶 我倾向于后者：macOS 上这个品类繁荣有其交互习惯基础（Spaces、全屏切换频繁），而 Linux 桌面的窗口管理习惯差异较大。
- **但有一个反向论点值得考虑**：PopDrop 里**最独特、最没有对标**的两项——"选择窗口定位到此"和"投送到呼出前窗口 / 原输入内容最前方"——在 Linux 上恰好是**最做不了的两项**。也就是说，PopDrop 的价值主张与 Linux 的能力边界**正好错位**。

**结论**：如果目标是"把 PopDrop 的能力搬过去"，Linux 的性价比最低。如果目标是"在 Linux 上做一个更小的东西"，那么**文件管理器定位（标准 D-Bus）+ 最近文件（公开规范）+ 文本块发送**这三件事在 Linux 上反而是三个平台里最省力的，可以独立成立。**不建议移植整套产品，但建议单独评估这三个点。**

---

## 6. 参考来源

**freedesktop / XDG 官方规范与文档**

- [XDG Desktop Portal — Global Shortcuts API](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.GlobalShortcuts.html) · [GlobalShortcuts 后端接口](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.impl.portal.GlobalShortcuts.html) · [portal 窗口标识](https://flatpak.github.io/xdg-desktop-portal/docs/window-identifiers.html) · [API 参考](https://flatpak.github.io/xdg-desktop-portal/docs/api-reference)
- [File Chooser portal 规范](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.FileChooser.html) · [Documents portal](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Documents.html) · [Trash portal 接口 XML（Debian 源）](https://sources.debian.org/src/glib2.0/2.74.6-2%2Bdeb12u6/gio/org.freedesktop.portal.Trash.xml/)
- [Recent File Storage Specification](https://specifications.freedesktop.org/recent-files/latest/) · [Recent File Storage 规范镜像](https://xdg-specs-technobaboo-f55ac9d85e73073a0c8831695ba0fb110849811c0.pages.freedesktop.org/recent-file-spec/recent-file-spec-latest.html) · [规范索引](https://specifications.freedesktop.org/) · [XDG Base Directory Specification](https://ebassi.pages.freedesktop.org/xdg-specs/basedir-spec/latest/)
- [Freedesktop Trash Specification](https://specifications.freedesktop.org/trash/latest/) · [Trash 规范镜像](https://avolkov.pages.freedesktop.org/xdg-specs/trash-spec/trashspec-latest.html)

**Wayland / X11 协议**

- [Wayland 协议与操作模型](https://wayland.freedesktop.org/docs/book/Protocol.html) · [Wayland 协议规范](https://wayland.freedesktop.org/docs/html/apa.html) · [wayland.xml 协议定义](https://cgit.freedesktop.org/wayland/wayland/tree/protocol/wayland.xml)
- [Wayland Xwayland 文档](https://wayland.freedesktop.org/docs/book/Xwayland.html)
- [wdotool 的 xdotool 兼容性说明（Wayland 能力边界）](https://github.com/cushycush/wdotool/blob/main/docs/xdotool-compat.md) · [wdotool 仓库](https://github.com/cushycush/wdotool)
- [wmctrl 概述](https://en.wikipedia.org/wiki/Wmctrl) · [Unix.SE：X11 与 Wayland 的窗口访问差异](https://unix.stackexchange.com/questions/648178/block-screen-sharing) · [Reddit：Wayland 下 xdotool 的替代讨论](https://www.reddit.com/r/linuxquestions/comments/1blhnpp)
- [GNOME Discourse：gnome-terminal 窗口 ID 无法被 xdotool/wmctrl 找到](https://discourse.gnome.org/t/gnome-terminal-window-id-cannot-be-found-by-xdotool-nor-wmctrl/14835)
- [Hyprland 全局快捷键文档](https://wiki.hypr.land/configuring/core/binds/globals/)

**文件监听**

- [inotify(7) man page](https://linux.die.net/man/7/inotify) · [fanotify(7) man page（Debian）](https://manpages.debian.org/testing/manpages/fanotify.7.en.html) · [fanotify_init(2) man page](https://www.man7.org/linux/man-pages/man2/fanotify_init.2.html)
- [FSEvents / inotify / ReadDirectoryChangesW 跨平台对比](https://gity.neullabs.com/blog/fsevents-inotify-readdirectorychangesw-cross-platform/)

**文件操作 / 定位 / 书签**

- [GIO `GFile.trash()`](https://docs.gtk.org/gio/method.File.trash.html) · [GIO `trash` 虚函数](https://docs.gtk.org/gio/vfunc.File.trash.html) · [`G_FILE_ATTRIBUTE_ACCESS_CAN_TRASH`](https://docs.gtk.org/gio/const.FILE_ATTRIBUTE_ACCESS_CAN_TRASH.html) · [`gio` 命令手册](https://manpages.debian.org/bookworm/libglib2.0-bin/gio.1.en.html)
- [org.freedesktop.FileManager1 使用示例（Unix.SE）](https://unix.stackexchange.com/questions/675902/how-to-reveal-a-file-in-file-explorer) · [接口 XML（Debian 源）](https://sources.debian.org/src/peek/1.5.1-1/src/dbus/org.freedesktop.FileManager1.xml) · [gdbus 调用示例仓库](https://github.com/boydaihungst/org.freedesktop.FileManager1.common)
- [GTK 3 `GtkFileChooserNative`（portal 用法）](https://docs.gtk.org/gtk3/class.FileChooserNative.html) · [xdg-desktop-portal-gtk 的 filechooser 实现](https://github.com/flatpak/xdg-desktop-portal-gtk/blob/main/src/filechooser.c)
- [GTK 书签文件说明（Red Hat 文档）](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/pdf/desktop_migration_and_administration_guide/Red_Hat_Enterprise_Linux-7-Desktop_Migration_and_Administration_Guide-en-US.pdf)

**Flatpak / 打包**

- [Flatpak 沙盒权限](https://github.com/flatpak/flatpak-docs/blob/master/docs/sandbox-permissions.rst) · [权限参考](https://flatpak-docs.readthedocs.io/en/latest/sandbox-permissions-reference.html) · [Flatpak Portals wiki](https://github.com/flatpak/flatpak/wiki/Portals)

**终端输入注入**

- [wtype 仓库](https://github.com/atx/wtype) · [wtype man page](https://manpages.debian.org/testing/wtype/wtype.1.en.html)
- [Electron globalShortcut 文档（X11 抓取 vs Wayland portal）](https://www.electronjs.org/docs/latest/api/global-shortcut) · [Electron issue：Wayland GlobalShortcuts portal 集成](https://github.com/electron/electron/issues/51875)

**对标产品**

- [KDE FileStash（开发中）](https://apps.kde.org/is/filestash/) · [KDE FileStash 备用页](https://apps.kde.org/sr/filestash/)
- [CopyQ](https://hluk.github.io/CopyQ/) · [CopyQ 仓库](https://github.com/hluk/CopyQ) · [CopyQ 文档](https://copyq.readthedocs.io/en/latest/)
- [Klipper 手册（PDF）](https://docs.kde.org/stable_kf6/en/plasma-workspace/klipper/klipper.pdf)
- [GNOME Sushi 仓库](https://github.com/GNOME/sushi) · [GNOME 内容预览设计文档](https://wiki.gnome.org/Design/OS/ContentPreviews) · [Debian gnome-sushi 包](https://packages.debian.org/unstable/gnome/gnome-sushi) · [Ubuntu 26.04 上 Sushi 空格预览问题](https://www.omgubuntu.co.uk/2026/05/gnome-sushi-not-working-ubuntu-26-04)
- [Espanso](https://github.com/espanso/espanso)
