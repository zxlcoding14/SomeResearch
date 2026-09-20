# PopDrop 功能点与技术方案分析

> 分析对象：[hiforrest/PopDrop](https://github.com/hiforrest/PopDrop)
> 分析版本：源码声明 v2.1.0（开发态）/ 配置版本 30；仓库最新 CHANGELOG 条目为 v2.0.12（commit `8d4e27c4`，2026-08-27，详见 §10）
> 分析目的：梳理该项目的功能点与对应技术方案，作为本项目的技术参考与复用评估依据
> 本文所有结论来自对仓库源码与随仓库文档的实际阅读，未做编译或运行验证

---

## 1. 项目概览

### 1.1 定位

**PopDrop 是一个"不切换当前窗口、随时取用文件与文本"的 Windows 快捷取用面板**，运行于 Windows 10 / 11。

它解决的问题：正在聊天、写文档或使用 AI 时，临时要找一份文件或一段提示词，传统流程必须先离开当前窗口→翻目录→切窗口→找内容。PopDrop 把这段过程压缩为三步：

> **按一下（F2），找到，直接拖走或发送。**

定位声明上明确划清了边界（`README.md`）：**负责快速取用和接收内容，不替代资源管理器 / Total Commander / Directory Opus**。

### 1.2 技术栈与运行形态

| 项 | 内容 |
| --- | --- |
| 主程序语言 | **AutoHotkey v2**（`PopDrop.ahk` + `modules/*.ahk`，纯文本 `#Include` 组织），发布时经 Ahk2Exe 编译为 `PopDrop.exe` |
| 原生扩展 | C++ / MSVC，两个独立 Helper：`PopDropTransfer.exe`（外部内容投放）、`PopDropPreview.exe`（文件预览），均提供 x64 / x86 两份 |
| 第三方库 | **PDFium**（可选组件，用于 PDF 预览，BSD 许可，未捆绑在源码包内） |
| 系统依赖 | Windows 10/11 自带组件；SQLite 走系统 `WinSQLite3.dll`，不可用时回退 INI 快照 |
| 界面实现 | 基本不自绘：**原生 Win32 控件**（`ListView` 分组视图、原生 Tab、原生 Task Link、Owner Draw 仅用于工具栏按钮） |
| 配置文件 | `config.ini`，**UTF-16LE + BOM + CRLF**，带布局锚点注释 |
| 运行期数据 | `cache\index.db`（SQLite 快照）、`cache\preview-cache-v1\`（预览快照与状态）、`data\text-blocks\usage.ini`（文本块使用统计） |

### 1.3 交互模型（三个关键概念）

1. **呼出即用、用完即走**：默认 `temporary` 模式下，切换到其他窗口 / 点击桌面 / Alt+Tab 后面板自动隐藏；软件自身的消息框、文件选择框、右键菜单、拖放操作期间**暂停自动隐藏**。
2. **工作区（Workspace）**：一套"文件来源组合 + 来源专属设置 + 固定项"的集合。不同类型的工作区承担不同职能——`Files`（文件工作区）与 `Text`（文本块工作区）。工作区**不含**快捷键、窗口行为等共享设置。
3. **来源（Source）与固定项（Pinned）**：来源是工作区内的分栏（一个文件夹 = 一栏）；固定项是跨会话常驻的快捷入口，**按工作区独立保存**。

---

## 2. 功能点清单

### 2.1 呼出与面板生命周期

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 主快捷键呼出 | 默认 `F2`，可自定义；语法为 AHK v2 格式（`^`=Ctrl、`!`=Alt、`+`=Shift、`#`=Win） | — |
| 快速双击直达文本区 | 双击主快捷键直达"默认文本块工作区"（`DoubleHotkeyWorkspaceId`） | 双击判定窗口 **400 ms**；目标只能是文本块工作区；过滤长按键盘重复；不执行工作区往返切换 |
| 单击打开哪个工作区 | `MainHotkeyWorkspaceMode`：`LastWorkspace`（上次关闭时的工作区）/ `DefaultWorkspace`（总是默认工作区） | 面板已显示时主快捷键**只关闭面板**，不切工作区 |
| 工作区独立快捷键 | 每个工作区可配置自己的呼出快捷键（`[Workspace:<ID>] Hotkey`） | 不得与主快捷键或其他工作区重复 |
| 三种窗口模式 | `WindowMode`：`temporary`（默认，失焦自动隐藏）/ `always_on_top`（常驻置顶）/ `normal`（普通窗口） | 图钉按钮可实时在 `temporary` ↔ `always_on_top` 间切换并立即保存；`normal` 下点图钉切到 `always_on_top` |
| 自动隐藏保护 | 消息框、文件选择框、右键菜单、拖放、OLE 循环、Shell 冲突/权限窗口、投放执行期间**暂停**自动隐藏，结束后成对恢复 | 拖入外部文件后面板保持打开并重新获得焦点 |
| 原生自动隐藏守卫 | 不依赖 AHK 定时器，用原生 Win32 机制以**真实 HWND 可见性与前台进程**为准，并挂 `EVENT_SYSTEM_FOREGROUND` 前台事件钩子 | 详见 §5.x |
| `Esc` 隐藏面板 | `EscapeHidesPanel=1` 时生效 | 文本块工作区中 `Esc` 优先清空搜索 |
| 开机启动 | `StartupEnabled` | — |
| 托盘菜单 | 打开设置、下载任务等 | 随仓库文档对托盘菜单记载较少 |

### 2.2 工作区系统与 Tab

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 顶部 Tab 切换 | 主面板顶部常驻原生 Tab 显示工作区 | 最多直接显示 **8 个**，其余收拢到"更多"菜单；从"更多"切换后该工作区仍会提升为可见 Tab |
| 工作区类型 | `Files`（文件）/ `Text`（文本块） | 类型创建后不变；旧配置自动迁移为 `Files`。**Launcher 不是工作区类型，而是来源级 `Mode`** |
| 管理工作区 | 设置中新建 / 复制当前 / 重命名 / 删除 | 名称不区分大小写且不能重复；复制时为新工作区及每个来源生成**新 ID**，故两个工作区可用同一路径而互不影响 |
| 工作区排序 | "管理工作区"中上移 / 下移 | 调整后立即保存并刷新，Tab、"更多"、`Ctrl+数字`、`Ctrl+Tab` 全部按新顺序工作 |
| 未保存修改保护 | 切换工作区或打开管理窗口时询问"保存并继续 / 放弃修改并继续 / 取消" | 保存失败保留原草稿与当前工作区；**至少保留一个工作区**；删除工作区**不删除真实文件** |
| 折叠状态记忆 | 来源分栏折叠状态按工作区记忆 | 重启后恢复展开 |
| 快捷键切换 | `Ctrl+1`～`Ctrl+9`、`Ctrl+Tab` 循环 | — |

### 2.3 文件工作区（来源分栏）

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 多来源分栏 | 每个文件夹独立分栏，新文件与最近修改的文件排在前面 | `[Folders]` 每行 `显示名称=文件夹路径`，路径支持 `%USERPROFILE%` 等环境变量 |
| 子文件夹显示范围 | `DisplayScope`：`FilesOnly` / `FilesAndFolders`（子文件夹不平铺）/ `RecursiveFiles`（递归平铺全部后代文件） | 递归扫描默认**不进入符号链接、目录联接与其他重解析点** |
| 文件夹时间语义 | `FolderTimeMode`：`DirectoryModified` / `LatestContent`（界面显示"内容更新于"） | 空文件夹、离线、无权限、扫描失败时回退到文件夹自身修改时间 |
| 排序 | `SortMode`：`ModifiedDesc`（默认）/ `NameAsc`（自然升序） | 支持来源级覆盖 |
| 视图模式 | `ViewMode`：`Thumbnail`（缩略图）/ `List`（文件名 + 修改时间） | 也可从右侧"显示"菜单切换 |
| 每来源最大数量 | `MaxFilesPerFolder`，`0` 或 `All` 表示全部 | 支持"继承全局" |
| 状态栏 | 底栏固定 **42 逻辑像素**高，左侧路径与操作反馈最多两行，右侧下载入口固定 **84 逻辑像素** | — |
| 后台状态文案 | "正在加载 / 更新中 / 已更新 / 已是最新 / 更新失败" | 180 ms 内完成的自动更新不闪"更新中" |
| 最近打开侧边栏 | 读取 `%APPDATA%\Microsoft\Windows\Recent`，**只展示仍存在的文件** | `ShowRecentSidebar`；`RecentFileCount` 1–100；关闭时**不扫描、不解析** Recent |
| 近期栏自适应 | 布局空间不足时**临时隐藏**，拉宽后自动恢复 | 用户的"显示近期栏"设置不被修改 |
| 来源不可用 | 显示"目录不可用"，不报错退出 | 网络盘、离线盘、权限受限目录；恢复连接后点"刷新"即可回来 |
| 筛选无命中 | 分组标题显示"没有符合筛选条件的文件" | 与"目录本身为空"明确区分 |
| 空文件夹 / 失效固定项图标 | 固定使用 `empty-folder.ico` / `unknown-file.ico` | 不再误用列表中第一张缩略图或按失效扩展名请求 Shell 图标 |

### 2.4 文本块工作区（v2.0 核心新增）

将工作区内所有来源及子目录的 `.md` / `.txt` 递归平铺为**卡片**，用于提示词、常用回复、命令片段、写作模板的取用。

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 多关键字搜索 | 多个关键词（半角/全角空格分隔）**AND** 匹配 | 匹配范围含**文件名、正文、来源名和路径**，关键字可分别命中不同字段 |
| "仅标题"范围 | 搜索框右侧勾选，或 `Alt+T` 切换，同一组关键字只匹配卡片上显示的无扩展名标题 | **只在本次窗口显示期间有效，不写入配置**；窗口关闭/自动隐藏/发送后下次呼出复位 |
| 搜索框聚焦 | `/` 或 `Ctrl+F` 聚焦并**全选**已有搜索文字 | 每次显示或切换进入都重新聚焦搜索框 |
| 快速发送 | `Enter` / 双击 / 右键"快速发送"：正文复制并粘贴到**呼出 PopDrop 前的窗口** | 无法粘贴时正文仍留在剪贴板 |
| 前置发送 | `Ctrl+Enter`（或 `Ctrl+双击`）：把正文投送到**原输入内容最前方** | 不自动添加空格/换行/分隔符；无法可靠恢复原窗口与输入焦点、安全输入框、目标位置已变化时**停止自动粘贴**，正文保留在剪贴板 |
| Ctrl+双击细节 | 按住 `Ctrl` 双击直接前置发送 | 只有**单独按住 Ctrl** 生效；以第二次鼠标按下时的修饰键快照为准；第二次左键抬起后立即切回原窗口，**Ctrl 可继续按住**；等待超过 **10 秒**取消 |
| IME 兼容 | 存在尚未上屏的 IME 组合输入时，`Enter` 优先交给输入法 | 组合结束后再按 `Enter` 才发送 |
| 复制正文 | `Ctrl+C`，多选时以**两个换行**连接 | — |
| 拖出语义 | 默认拖出提供 `CF_UNICODETEXT` 正文；**按住 `Alt` 拖出提供真实文件** | 拖出同时提供 `CF_UNICODETEXT` 与 `CF_TEXT` |
| 内置编辑器 | `F4` 打开，支持 `Ctrl+S`、未保存关闭确认、"另存为副本" | 右键菜单也可交给系统默认编辑器 |
| 首尾空行保留 | 读取、复制、发送、编辑器保存/另存为均保留文件首尾空行 | 便于把自带换行边界的文本插入光标位置 |
| 拖入文字捕获 | 从外部拖入选中文字到某来源 → 在该来源根目录创建 UTF-8 `.md`；拖到固定项 → 创建**独立文本块**并置于最前 | — |
| 剪贴板捕获 | 点击"粘贴"图标或按 `Ctrl+V` 把非空白剪贴板文字创建为独立文本块并固定 | **仅在文本工作区**接管；搜索框、重命名框、编辑器等控件不被拦截；无文本时按钮置灰（`btn-paste-gray.png`）|
| 新建内容保护 | 新内容有 **24 小时**优先展示保护 | 之后按"最近使用 / 近 30 天使用次数 / 历史次数"智能排序；连续 10 秒内重复使用同一文本块只计一次 |
| 来源内分类置顶 | 右键"在当前文件夹置顶"/"取消置顶"，卡片显示 `pin.ico` | 置顶卡片全部显示，**不占普通配额**；单个置顶卡片可在来源内拖动排序并立即保存 |
| 卡片宽高 | `TextBlockCardWidth`（140–640 DIP）、`TextBlockCardHeight`（48–320 DIP） | — |
| 固定项链接语义 | 把已有 `.md/.txt` 加入固定项只保存链接，原来源卡片继续显示 | 卡片右下角显示轻量链接图标；PopDrop 管理的独立文本块不显示该图标 |
| 归类语义 | 独立文本块拖到文本来源默认**移动实体**；固定项文件链接默认**复制** | `Ctrl` 复制 / `Shift` 拒绝移动原文件；混选默认拒绝移动 |

#### 2.4.1 Windows 终端兼容发送（v2.0 特有分支）

| 项 | 内容 |
| --- | --- |
| 触发条件 | 呼出前的**顶层窗口**是 Windows Terminal，或 `ConsoleWindowClass` 且实际宿主为 Windows Console Host |
| 识别依据 | **顶层窗口类 + 拥有者进程**，而不是终端里跑的是什么程序 |
| 首版覆盖 | Windows Terminal（稳定版及可识别的预览宿主）、Console Host 承载的 CMD、Console Host 承载的 Windows PowerShell |
| 处理顺序 | ① 从正文**绝对开头和结尾**删除连续 CRLF/LF/CR（混合换行按换行 token 处理）→ ② 保留内部换行、空格、缩进，**不把规范化结果写回文本块** → ③ 清理后为空或仅含空白则**停止** → ④ 单行直接投送，多行先跑中文自然语言规则，不满足才显示**默认选"否"**的确认框 → ⑤ 确认前剪贴板已是清理后的正文 → ⑥ 重新激活并核对同一宿主后**只投送正文，不额外发送回车** |
| 中文免确认规则 | 至少四个汉字；每个非空非标题有效行都含汉字；主体汉字占比 ≥ **35%**；代码围栏、独立英文命令、提示符、路径/URL/参数、变量赋值、管道、重定向等任一出现即**否决免确认** |
| 投送通道 | Console Host 用一次 `WM_PASTE`；Windows Terminal 用一次 `Shift+Insert`（兼容 Claude Code 等原始输入 TUI） |

> 该分支的定位是"减少重复确认"，文档明确声明**不解释命令语义、不代表安全审查**；受 Windows Terminal 自身 `multiLinePasteWarning` / `largePasteWarning` 约束，PopDrop 不读取、修改或绕过这些设置。

### 2.5 固定项（Pinned）

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 加入固定项 | 点「＋ 固定项」选择一个或多个文件 | **该按钮不接收拖放**；拖入走顶部智能入口或直接拖到固定项分组 |
| 文件夹加入 | 文件夹拖到固定项分组，作为**单独固定项**加入 | 不展开、不添加其中内容 |
| 链接图标 | 固定文件与固定文件夹在项目**右下角**显示链接图标 | 表示是原项目的快捷入口；**不会在磁盘上额外创建 `.lnk`** |
| 按工作区独立 | 保存在 `[WorkspacePinned:<WorkspaceId>]` | 同一路径可在多个工作区分别固定、排序或移除 |
| 新批次置前 | 新加入的一批显示在**最前面**，并保持拖入时的原始顺序 | 重复路径自动跳过且不改变已有位置 |
| 内部排序 | 拖动单个固定项到另一个固定项上调整前后顺序，**立即保存** | 多选拖拽仍用于向其他软件发送，不执行内部排序 |
| 移除 | 点「－ 固定项」**只移除当前工作区的面板记录** | 不影响原文件、文件夹或其他工作区；多选批量移出不会删除源文件 |
| 失效路径 | 外部移动/重命名/删除后旧路径显示"项目不存在" | PopDrop 菜单重命名或移动项目时会同步固定路径（含后代） |
| 清理失效项 | 右键"固定项"标题 →"清除全部失效项目" | 无失效项时菜单禁用；只清理当前工作区；配置保存失败时恢复原列表并报错 |
| 旧配置迁移 | 旧版 `[PinnedFiles]` 安全迁移到升级时的当前工作区 | — |

### 2.6 快捷启动栏（Launcher 模式）

把普通文件夹变成**快捷启动面板**：文件夹当作程序分类，文件当作菜单项。

| 项 | 内容 |
| --- | --- |
| 启用方式 | 来源级 `Mode=Launcher`（**不是**工作区类型） |
| 显示内容 | 分组内的 `.lnk`、`.url`、`.exe`，按文件名排序；每个 `[Folders]` 分组成为分类标题 |
| 数字前缀 | 文件名中的数字前缀**控制排序、不参与显示**；只移除 `^\d+[ \t]+` 模式（数字 + 至少一个空格/制表符），故 `7-Zip.lnk`、`3D Viewer.lnk` 保留原名 |
| 默认值 | `IncludeSubfolders=0`、`DisplayScope=FilesOnly`、`SortMode=NameAsc`、`FilterMode=Include`、`FileExtensions=.lnk,.url,.exe`、`StripOrderPrefix=1`、`HideExtensions=1` |
| 拖入行为 | 普通文件/文件夹/`.exe` → 在 Launcher 目录创建指向原项目的 `.lnk`；本地 `.lnk`/`.url` → Shell 复制，原文件不移动 |
| 快捷方式命名 | 名称来自可读原名，清理非法字符、Windows 保留名称与尾部点/空格；重名自动 `名称 (2).lnk`；先写临时名、验证目标后**无覆盖重命名**，失败清理临时文件 |
| 安全语义 | 固定项和 Launcher **不受 Ctrl/Shift 修饰键影响**，绝不会因修饰键移动原文件 |

### 2.7 拖入 / 拖出 / 外部内容投放

#### 2.7.1 顶部拖拽识别区（智能入口）

- Files 工作区**没有可见、可命中的固定项分组**时，拖入外部纯文件夹显示**双入口**：左侧约 70% 添加为来源，右侧约 30% 加入固定项。
- 拖到右侧固定项目标**只记录路径，不移动、不复制、不修改文件夹**。
- 纯文件：已有可见固定项分组时顶部保持普通工具栏；固定项为空/未渲染/已滚出可命中区域时，顶部才切换为「☆ 松开，将文件加入固定项」。
- 侧边"＋固定项"按钮**不再作为拖拽目标**。
- 文件和文件夹**混合选择不显示智能入口**，也不自动拆分；虚拟文件、URL、网页图片、特殊 Shell 对象同样保持普通工具栏。
- 顶部只向 OLE 来源返回 `COPY` 或 `NONE`，**绝不返回 `MOVE`**。
- 添加为来源时逐项校验路径仍存在且可持久化；名称默认取文件夹名，同名用 `名称 (2)`；当前工作区已存在的相同规范路径跳过；整批走**原子事务**（保留注释、未知键、UTF-16LE、CRLF 与六个布局锚点）；成功后只触发**一次**后台扫描。

#### 2.7.2 拖放默认动作表

| 拖拽来源 | 投放目标 | 默认动作 |
| --- | --- | --- |
| 全部为可验证真实文件夹 | 顶部「＋ 添加为来源」 | 追加为当前工作区 Files 来源；不操作真实文件夹 |
| 内部/外部纯文件，且无可见固定项分组 | 顶部「☆ 加入固定项」 | 新批次置于当前工作区固定项最前；不操作真实文件 |
| PopDrop 普通 Files 来源项目 | 另一个 Files 来源 | **移动**真实文件 |
| Windows 资源管理器本地项目 | Files 来源 | **复制**真实文件 |
| PopDrop 固定项或最近文件 | Files 来源 | 复制真实文件 |
| 含固定项/最近文件/来源不确定项的混合选择 | Files 来源 | 复制真实文件 |
| 任意有效本地文件或文件夹 | 固定项分组 | 只加入固定项 |
| 任意有效本地文件或文件夹 | Launcher 来源 | **创建快捷方式**；已有 `.lnk/.url` 只复制 |

- `Ctrl` 请求复制、`Shift` 请求移动；若来源不允许请求的效果，**移动请求可安全回退为复制，复制请求不会回退成可能删除源项目的移动**。

#### 2.7.3 外部内容投放（浏览器 / 网页 / 聊天软件）

对同一个 `IDataObject` **只选择一条链路**，优先级：

1. `CF_HDROP` 本地路径；
2. `FileGroupDescriptorW + FileContents` 虚拟文件；
3. 注册的 `PNG`、`CF_DIBV5`、`CF_DIB`；
4. `UniformResourceLocatorW`、`UniformResourceLocator` 或 `text/uri-list` 中的公开 URL；
5. 都不存在时**拒绝**。

| 机制 | 说明 |
| --- | --- |
| 异步 HDROP 接管 | 来源声明异步能力时**不先读路径**，在 `Drop` 内由 helper 执行唯一一次 `GetData(CF_HDROP)` 并分块复制，避免 Chromium 把两次读取解释为两次延迟下载 |
| 目标目录认领 | 浏览器把自己的下载目录正好作为投放目标时，PopDrop 等待写入完成直接**认领**，不生成 `image (2).jpg`；目录判断用文件系统标识，可处理大小写与 junction 别名 |
| 图片质量收敛 | 异步 HDROP 图片等待写入完成后读取真实像素宽高，优先保留**像素面积较大**的版本，像素相同时保留字节数较大的；结束后还有 **5 秒有界后台收敛** |
| 虚拟文件 | 支持多 `FILEDESCRIPTORW`、Unicode 名称、已知/未知大小、空文件、`TYMED_ISTREAM`、`TYMED_HGLOBAL`；恶意相对/绝对路径收敛为安全文件名；**`TYMED_ISTORAGE` 明确不支持** |
| 公开 URL | 默认允许公开 **HTTPS**，**HTTP 默认关闭**；拒绝 `file:`/`javascript:`/`blob:`/`data:`/UNC/带用户名密码的 URL；用系统代理与正常 TLS 校验，**不发送 Windows 凭据、不读浏览器 Cookie**；最多 **10 次**重定向；全局最多 **3 个**后台任务、同一主机最多 **2 个**；完整 URL 只以当前用户 **DPAPI 加密**短暂保存 |
| 临时文件与原子落盘 | helper 写入先使用目标目录中的隐藏 `.popdrop-part`；成功后刷新缓冲、重新确认唯一名称，再用**同卷原子改名**；失败/取消删除半成品；`.popdrop-part` 无论过滤开关如何都**不会进入面板** |
| 安全标记 | 公开 URL 及带网络 URL 的虚拟文件通过 `IAttachmentExecute` 添加来源信息；异步 HDROP 尽量复制已有 `Zone.Identifier`；**不自动打开 EXE/MSI/脚本/快捷方式/宏文档，也不执行杀毒命令行** |
| helper 握手 | 源码运行优先使用与 AutoHotkey 位数匹配的 `native\bin\x64` / `native\bin\x86`；版本不匹配时明确提示，不继续执行旧逻辑 |
| 诊断开关 | `--inspect-drop` 在系统临时目录生成本次会话的格式诊断日志（格式名、数值 ID、`TYMED`、`lIndex`、异步能力、最终适配器），**不记录聊天文本、图片内容或完整 URL** |

#### 2.7.4 拖出

- 多选后拖拽任意一个已选文件，**所有选中文件一起发送**（支持跨文件夹、跨磁盘）。
- 实现对多选竞态做了加固（`WM_LBUTTONDOWN` 时直接同步读取原生 ListView 选中行并冻结路径与行上下文），确保刚完成 Ctrl/Shift/框选就立即拖动时能拖出完整选择。

#### 2.7.5 按来源投放本地文件（面板内投放）

- 鼠标经过的目标实时解析并高亮；状态栏显示"复制/移动 N 个项目到「来源」""添加到固定项"或"创建快捷方式"，系统拖拽光标与最终动作一致。
- 安全跳过并在结果中计数：项目已属于目标来源（含规范化后指向同一真实路径的两个来源）、移动项目的父目录就是目标目录、文件夹将被投放到自身或后代目录、路径失效/无法由 Shell 解析/当前不可访问。
- 拖到来源内的某个文件图块仍表示投放到**该来源根目录**。
- 不可投放区域（最近文件侧栏、状态栏、普通工具按钮、无法映射到目录的主列表空白区）显示禁止光标并说明原因。

### 2.8 预览（两套独立能力）

#### 2.8.1 内置文件内容预览（悬浮预览）

| 项 | 内容 |
| --- | --- |
| 支持类型 | 图片、文本/日志/配置、代码、CSV/TSV、Markdown、PDF（默认关闭）、DOCX |
| 文本类 | Markdown / 纯文本 / 日志 / 配置 / 常见代码最多读取**开头 512 KiB**；支持 BOM、UTF-8、UTF-16，二进制嗅探通过后有限回退系统代码页 |
| CSV/TSV | 最多 **30 行 × 12 列**，**不执行公式** |
| Markdown | 只绘制静态标题、段落、强调、列表、任务、引用、代码、表格、分隔线；**原始 HTML、脚本、Mermaid、插件、网络资源、链接点击均不执行** |
| PDF | 卡只显示**第一页**；组件未安装时先征求同意再异步下载当前架构 PDFium 并校验 SHA-256；优先动态加载同目录非 V8/XFA `pdfium.dll`，不可用时再通过原生只读随机访问流调用系统自带 `Windows.Data.Pdf` |
| DOCX | 优先用 Windows **IFilter** 提取开头语义文本，无法提取时尝试系统真实缩略图；复杂版式、分页、页眉页脚与嵌入图片可能被简化或忽略 |
| 隔离 | PDF/DOCX 都在**可终止 Helper** 内运行，不启动 Word、不执行宏/OLE/ActiveX、不访问远程关系、不自动下载云端占位文件 |
| 回退顺序 | 原图允许安全解码时优先原图；Windows 已有缩略图只作为**最后回退**并等比放大 |
| 信息栏 | 底部在**不增加总高度**的情况下显示文件名、自动选择 KB/MB 的大小与修改时间；无法预览时显示文件图标及同样信息（`ShowFileInfo`） |
| 后台缓存 | 面板隐藏后开始计时（`CacheStartAfterHiddenSeconds` 默认 10 秒），IDLE 优先级 Helper 串行生成；每次隐藏会话**最多成功生成 50 项**，失败不占成功额度，单轮最多尝试 100 项 |
| 缓存维护 | 软容量 `CacheMaxMB`(256) / 项目数 `CacheMaxItems`(1000) / 单项硬上限 `CacheItemMaxKB`(≤2048) / 未引用期限 `CacheUnreferencedDays`(7)；`CacheEnabled` 只控制**写入**新缓存，关闭后仍可读取已有有效缓存 |
| 超时 | 首次生成约 **120 ms** 内完成则直接显示；否则"首次预览正在生成…"，**5 秒**后更新为长耗时提示，**12 秒硬超时**；错误按资源超限/密码保护/超时/不可访问/损坏不支持区分，并使用**分类负缓存** |
| 交互抑制 | 拖拽超过系统阈值、固定项排序、框选、滚动、菜单、工作区/视图切换、窗口实时移动缩放会立即抑制预览，结束后按当前屏幕坐标自动恢复 |
| 键盘候选 | 方向键、Home、End、Page Up/Down 建立候选；`Enter`/`Esc`/列表失焦/隐藏面板立即关闭 |
| 状态文件 | `cache\preview-cache-v1\cache-status.ini`（`Stage`、`Attempted`、`Succeeded`、`Failed` 与剩余队列） |

#### 2.8.2 外部空格键快速预览（Seer / QuickLook）

- `[QuickPreview]` 默认 `Off`；可选 `Seer`（需 `SeerIntegrationEnabled=1` 且运行中的 Seer 通过 `SeerWindowClass` 检测）或 `QuickLook`（`QuickLookPath` 必须指向桌面版/便携版 `QuickLook.exe` 并做产品信息校验）。
- v2.0 起**悬停在文件上直接按空格即可预览，无需先点击选中**。
- 焦点项变化以 **220 ms** 防抖同步；Seer 路径更新满足其 **5000 命令至少 200 ms** 的调用间隔。
- 外部预览期间 PopDrop **自动让出置顶层级**，会话结束恢复，且**不修改、不保存 PopDrop 的置顶设置**。
- 关闭方式：焦点仍在 PopDrop 时再按 Space 或 Esc；焦点位于 Seer 主预览窗口时由 PopDrop 发送 **5005** 可靠关闭。
- **文本块搜索框聚焦时 Space 始终保留给文字与输入法**，不受鼠标悬停位置影响。
- 能力检测失败时 PopDrop **不接管空格键**；**不安装、不捆绑、不模拟按键调用任何外部查看器**。

### 2.9 选择窗口定位到此

| 项 | 内容 |
| --- | --- |
| 功能 | 从 Windows 标准**打开文件、保存/另存为、选择文件、选择文件夹**窗口呼出 PopDrop 时，每个 Files/Launcher 来源分组标题右侧出现**原生 Task Link**，点击直接导航到对应文件夹 |
| 菜单入口 | 右键菜单保留同名入口（"选择窗口定位到此"/"另存为定位到此"），位于菜单**首项**，与原有命令间用分割线隔开 |
| 显示条件 | **只在文件选择窗口场景显示**；选择窗口关闭或用户转到普通窗口后 Task Link 及时清除 |
| 窗口识别 | 同时校验顶层 `#32770`、IDOK 与 Shell 子窗口结构，覆盖现代 `IFileDialog`、旧式 Common File Dialog 与树形 `SHBrowseForFolder`；避免把普通设置对话框误判为文件选择器 |
| 导航实现 | Explorer 风格窗口用地址栏快捷入口并以 `CDM_GETFOLDERPATH` 核验结果；没有地址栏的旧式树形选择器改用 Unicode `BFFM_SETSELECTIONW` |
| Inno Setup 支持 | v2.0.10 起精确识别其自有 VCL `TSelectFolderForm`，并要求同时具备 `TFolderTreeView`/`SysTreeView32` 与**唯一可见路径输入控件**；其他自定义窗体还需具备明确的多语言 Browse/Select Folder 标题；只向已验证的路径控件发送 `WM_SETTEXT` 并回读核验 |
| 安全约束 | **只导航原选择窗口，不改"文件名"字段、不操作剪贴板、不自动点击打开/保存/选择**；每次发送路径/回车前都验证前台 HWND 仍是原窗口，失去前台立即中止 |

### 2.10 右键菜单与文件操作

| 功能 | 说明 | 关键约束 |
| --- | --- | --- |
| 两套右键菜单 | `DefaultContextMenu`：`PopDrop`（快捷菜单，推荐）/ `System`（Windows 系统菜单） | 设置保存后立即生效，所有工作区与各区域共用同一选择 |
| 切换方式 | 右键 / 键盘菜单键打开**默认**菜单；**按 `Shift` 右键或 `Shift+F10` 打开另一个** | 默认菜单为 PopDrop 时底部提示"更多系统操作… Shift + F10"；为 System 时备用菜单不再显示重复入口 |
| 选择语义 | 右击当前多选中的项目**保留整个选择**；右击未选中项目先改为单选 | 跨父文件夹多选时系统菜单只作用于当前右击/聚焦项目，并在状态栏提示该限制 |
| 重命名 | "重命名…"仅单选有效文件/子文件夹时可用，由 Windows Shell 执行；文件名与扩展名使用**同一行中的独立文本框** | 磁盘/共享根目录不能重命名；目标文件夹本身是已配置来源或包含来源时**拒绝操作**；成功后同步**所有工作区**中该项目及其后代的固定路径 |
| 删除 | `Delete` 或菜单"删除"**立即移入回收站，不弹二次确认** | **回收站不可用时不会改为永久删除**；`Shift+Delete` 先显示**不可撤销警告**，确认后永久删除 |
| 复制 | 使用 `CF_HDROP`，可直接粘贴到资源管理器或支持文件粘贴的软件 | — |
| 复制路径 | `Ctrl+Shift+C`，按当前显示顺序**每行一条，不添加引号** | — |
| 复制到 / 移动到 | 使用 Windows `IFileOperation`，支持文件、文件夹、混合选择、跨来源目录与跨磁盘 | 重名、文件夹合并、权限提升、进度、占用、网络位置、取消与部分完成**均由 Shell 处理**；程序额外检查 `GetAnyOperationsAborted`；**不会静默覆盖，也不会自行用"复制后删除"模拟移动** |
| 常用目标 | 最多 **5 个**，写在配置文件中；首次升级把系统"桌面""下载"迁移为前两项 | 通过 **Windows 已知文件夹**解析，遵循系统把这些目录移到其他磁盘后的设置 |
| 最近目标 | 最多 **3 个**，只记录确实产生文件变化的成功复制/移动目标 | 无效目标标记为不可用并可从菜单移除 |
| 批量后处理 | 整批操作完成后只请求**一次**后台刷新 | 尽量恢复选择、焦点与滚动位置 |

### 2.11 打开方式与工具动作

| 概念 | 说明 |
| --- | --- |
| **打开方式** | "用某个程序打开当前文件"，**只对单个普通文件**显示 |
| **工具动作** | 由应用执行的文件操作，可用于文件、文件夹、混合选择或多选 |

| 功能 | 关键约束 |
| --- | --- |
| 应用配置 | 同一个主程序路径只能保存**一条**应用记录；关闭"显示在打开方式菜单中"后仍可提供工具动作；禁用整个应用会同时隐藏其打开方式与全部动作 |
| 动作管理 | 独立窗口，支持添加、编辑、复制、移除、排序；"复制动作"生成新的稳定动作 ID；改名、改路径、排序都不改变已有 ID；只改设置草稿，主设置窗口"保存"才原子写入 |
| 执行模式 | `PerItem`（逐个项目串行，后台等待前一个外部进程退出后再启动下一项，等待不阻塞界面）/ `Batch`（只启动一个外部进程，`{items}` 展开为多个独立路径参数） |
| 参数变量 | `{item}`、`{items}`、`{folder}`、`{parent}`、`{name}`、`{stem}`、`{ext}`、`{date}`(yyyyMMdd)、`{time}`(HHmmss)、`{index}`、`{count}`、`{size}`（如 `15KB`/`2.4MB`，按 1024 进位） |
| 变量约束 | 每行一个参数，空格/中文/`&`/括号不会造成参数拆分；`{items}` **只允许用于 Batch 且必须单独占一行**；未知变量、不完整大括号、自定义工作目录为空或覆盖程序不是现有 `.exe` 时**阻止保存** |
| 工作目录 | 所选项目所在文件夹 / 程序所在文件夹 / 自定义目录（支持环境变量与标量变量，不支持 `{items}`） |
| 扩展名匹配 | 不区分大小写、自动补全 `.`、去重、支持 `<none>`；按**完整文件名做最长后缀匹配**，故 `.tar.gz` 可作为独立类型；扩展名条件必须对全部选中文件成立 |
| 菜单排序 | 打开应用按当前选择实际适用的**前 5 个**直接显示，其余进"更多已配置应用…"；工具动作按 `Order` 与 `ActionOrder` 排序，过滤后**前 5 个**直显，其余进"更多工具操作…"；重名动作追加应用名 |
| 执行安全 | 回调固定保存生成菜单时的完整选择副本与当前右击项目，执行前再次验证；EXE 路径、逐项转义后的参数、工作目录分别传给 `ShellExecuteExW`，**不经过 `cmd.exe`、PowerShell、批处理、脚本或 Shell 管道**；最终命令行超长则不启动 |
| 可靠性边界 | Batch 的"已启动"只表示 Windows 接受了启动请求；PerItem 只能观察进程是否退出，**无法判断工具是否实际处理成功**——任何状态提示都不代表压缩/解压/转换已完成 |

### 2.12 下载任务（外部传输界面）

| 项 | 内容 |
| --- | --- |
| 底栏入口 | 右侧固定 84 逻辑像素，显示"↓下载""↓2 35%""!失败1""✓完成"等短状态 |
| 时间规约 | 任务持续超过约 **300 ms** 才切换为整体任务数/进度，并**至少保留约 800 ms**；完成提示显示约 **3 秒**后恢复；**未查看的失败保持提示** |
| 进度 | 来源标题显示接收项数或真实百分比；未知总长度只显示已收字节与速度，**不显示虚假百分比** |
| 传输中心 | 点击入口打开**非模态传输中心**，按批次查看文件名、来源、目标、进度、速度、状态；可取消单项/整批、重试公开 URL、打开目标文件夹、清除记录；批次按创建顺序倒序，最新在顶部 |
| 无占位图块 | **不为每个下载创建占位图块**；隐藏或关闭主面板不会取消任务，再次打开恢复最新进度 |
| 退出保护 | 退出时若仍有活动任务，要求"返回"或"取消任务并退出"；**不提供"退出界面但继续传输"的虚假选项** |
| 设置项 | 是否启用公开 HTTPS URL 兜底、是否允许 HTTP（默认关闭）、后台最大并发 1–6（默认 3）、面板隐藏时是否显示批次完成通知 |

### 2.13 文件管理器适配（7 个）

`[FileManager] Provider` 允许值：`WindowsShell`（默认）、`DirectoryOpus`、`TotalCommander`、`XYplorer`、`DoubleCommander`、`Files`、`FreeCommander`。

| Provider | 程序路径 | 定位行为 |
| --- | --- | --- |
| `WindowsShell` | — | 跟随 Windows 系统行为，保持旧版本文件夹打开方式与 Shell 文件定位；也尊重系统级 Explorer Replacement 配置 |
| `DirectoryOpus` | `dopusrt.exe`（手选 `dopus.exe` 时会尝试转换） | 单个项目打开所在文件夹并选中；多选按文件夹去重后打开 |
| `TotalCommander` | `TOTALCMD64.EXE` / `TOTALCMD.EXE` | 优先复用已运行实例并在当前源面板打开目录；**受公开命令行接口限制，暂不自动选中普通文件** |
| `XYplorer` | `XYplorer.exe` | 打开文件夹传入带末尾反斜杠的目录路径；定位单个项目传完整路径；多选不注入脚本 |
| `DoubleCommander` | `doublecmd.exe` | 用 `-C` 优先交给已运行实例；传完整文件路径时打开父目录并把光标移到该文件 |
| `Files` | `Files.exe` / `files-stable.exe` / `files-preview.exe` / `files-dev.exe` | `-directory` 打开文件夹，`-select` 定位单个项目 |
| `FreeCommander` | `FreeCommander.exe` | 用 `/C` 优先交给已运行实例；传完整文件路径时打开父目录并定位光标 |

- "自动查找"只检查常用安装位置与合理的系统注册信息，**不扫描整个磁盘**；便携版可"浏览…"手动选择；Files 会检查 Windows 应用执行别名。
- 第三方程序路径**仅在执行相关操作或点击测试按钮时检查，不会在程序启动时弹窗**。
- **One Commander 明确不在列表中**：其公开命令行接口没有稳定的指定项目选择参数，PopDrop **不会用键盘/鼠标模拟或未公开窗口消息补足**该能力。

### 2.14 设置界面

- **左侧树形导航**（v2.0 起不再使用功能重复的顶部标签栏）；右侧内容区顶部有与左侧导航一致的灰色留白。
- 底部按钮："保存"在左、"取消"在右。
- 页面结构：`共享设置 · 通用`（含"右键菜单""开机启动"）、`共享设置 · 文件打开与操作`（含"文件管理器""应用与工具操作"）、`共享设置 · 界面设置`、`来源与工作区` / `工作区设置 → 当前工作区`（含"管理工作区…"）、`文件来源`（普通文件夹/启动器文件夹）、`文件显示与过滤`（含"文件内容预览"、PDF 预览）、`过滤与显示`（噪音过滤总开关 + "管理忽略规则…"）、`内容更新方式`（极速显示/准确优先）、`常规 → 下载`、`关于 PopDrop`。
- 字号/高度微调参数需改源码顶部常量（主面板、设置页与子窗口一起生效）：`UI_SINGLE_LINE_HEIGHT := 26`、`UI_DROPDOWN_FIELD_HEIGHT := 22`、`UI_DROPDOWN_Y_OFFSET_PX := 1`、`UI_EDIT_TEXT_Y_OFFSET_PX := 0`、`UI_DROPDOWN_TEXT_Y_OFFSET_PX := 0`。
- 图形化管理覆盖：来源管理、打开软件、常用位置、最近目标清空、全局排除名称、来源排除路径与允许覆盖、开机启动。

### 2.15 显示与布局

| 项 | 内容 |
| --- | --- |
| 界面缩放 | `UiScale`：`100`/`125`/`150`/`175`/`200`，默认 `100`；窗口、控件、文字、缩略图、卡片与间距同步缩放，并与 Windows 显示缩放**叠加**；**保存后重启生效**；当前不改变设置窗口与独立对话框的整体尺寸 |
| 缩略图 | `ThumbnailSize` 原生像素边长 48–256（建议 72/96/128/160），**不再乘以 Windows 显示缩放**；`ThumbnailHorizontalGap` 0–128（默认 24）；`ThumbnailVerticalGap` 0–128（默认 4）；`ThumbnailTextLines` 1–2 |
| 分栏间距 | `FileViewGroupTopSpacing` / `FileViewGroupBottomSpacing`，单位 DIP，范围 0–32，默认 4/6；通过 `LVM_SETGROUPMETRICS` 交给 ListView 原生布局 |
| 窗口尺寸 | `WindowWidth` / `WindowHeight`；宽度允许 **330–980** 逻辑像素；新配置默认 **766×576**；重新打开时把超宽值限制到 **980** |
| 右侧工具栏 | 采用逻辑 DIP（按钮基准 **32 DIP**），100%/150%/200% 分别得到 32/48/64 物理像素；九个按钮依据内容区高度统一缩放（正常窗口保持 64 像素，矮窗口不溢出） |
| 工具栏顺序 | 刷新、粘贴、全部展开、全部收起、添加、移除、显示、设置、置顶；"全部展开/收起"为独立按钮组，上下均有分割线；均有悬浮说明、浅蓝 Hover 背景、蓝色描边与按下反馈 |
| 显示菜单 | "缩略图"/"列表"互斥（圆点表示当前），"文件预览"/"近期栏"为独立开关；支持 Tab 聚焦与 Space/Enter/方向键/Esc 操作 |
| 全部展开 / 全部收起 | 只操作当前工作区的 Files、Launcher 与文本来源分栏，**固定项不参与**；结果按工作区在本次运行中记忆；批量收起会清除被隐藏项目的选择并关闭预览 |
| 窄窗布局 | 顶部工作区继续使用原生左右翻页，超 8 个工作区进"更多"菜单；近期栏仅在空间不足时临时隐藏 |

### 2.16 缓存、刷新与维护

| 项 | 内容 |
| --- | --- |
| 缓存位置 | `cache\index.db` 保存每个工作区的事务快照；`CachePath` 留空时优先放软件目录，不可写或非本地磁盘时自动回退 `%LOCALAPPDATA%\PopDrop\cache`；旧 `scan-cache-v4.ini` 只在升级时作为一次性种子，SQLite 不可用时作为安全回退 |
| 缓存内容 | **只保存路径、名称、时间和呈现状态，不保存用户文件内容**；删除缓存不会删除用户文件；缓存不需要手动清理 |
| 重复呼出 | 同一工作区视图未变化时**不清空 ListView、不重建 ImageList，也不再次全量扫描** |
| 变更监听 | 本地来源由异步 `ReadDirectoryChangesW` 监听，**50–120 ms** 内连续事件合并后只重扫受影响来源 |
| 首扫策略 | 首次无缓存或手动刷新时，各来源按**本地优先、配置顺序串行扫描**；一个来源完成后立即以完整分组提交，其他来源继续扫描（机械盘仍保持单路顺序 I/O，但首个分组不再等整个工作区） |
| 网络路径 | UNC、WebDAV 与映射网络目标**不在刷新关键路径执行同步存在性检查**，故失效快捷方式不会拖住来源呈现 |
| 后台校准 | 进程启动、跨日首次呼出、睡眠恢复、监听溢出/句柄错误、来源配置变化与手动刷新会安排后台校准；监听失败只使对应来源失效并重建句柄，不清空其他来源缓存 |
| 一致性检查 | `ConsistencyCheckMinutes`（默认 60，`0`=关闭）：**不启用常驻计时器**，呼出窗口时判断是否到期；窗口关闭后只校验 Dirty、监听失败或不可监听的来源 |
| 内容更新方式 | **极速显示**（默认，持续监听所有工作区本地来源，多工作区引用同一文件夹时变更分别更新各自快照，固定项变化与后台重试期间保留上一份完整画面）/ **准确优先**（呼出窗口及切换工作区时主动确认当前内容，仅限极速模式异常时使用）；扫描异常退出或超 120 秒自动重试一次 |
| 缓存维护 | 改为**面板实际打开并隐藏后的每日机会任务**（启动、首次显示、午夜与固定小时均不主动执行）；单次最多检查 256 个顶层项、尝试删除 24 项或占用 150 ms；**15 分钟以上且不属于当前任务的扫描 IPC 文件/目录自动回收**，写入中间文件保留 1 小时安全窗口；SQLite 损坏备份默认保留 7 天且最多 3 组；WAL 使用 1 MB 尺寸目标与 256 页自动检查点 |
| 维护日志 | `workspace-performance.log`（**默认停写**，需把 `WORKSPACE_PERFORMANCE_LOG_ENABLED` 改为 `true`，上限 512 KB）、`workspace-switch-errors.log`、`cache\preview-cache-v1\cache-status.ini` |

### 2.17 快捷键汇总

| 快捷键 | 作用 |
| --- | --- |
| 主快捷键（默认 `F2`） | 呼出/关闭面板；双击直达默认文本区 |
| 工作区独立快捷键 | 呼出指定工作区 |
| `Ctrl+1`～`Ctrl+9` / `Ctrl+Tab` | 切换 / 循环切换工作区 |
| `Esc` | 隐藏面板（`EscapeHidesPanel=1`）；文本工作区中先清空搜索 |
| `Enter` | 用默认关联打开文件；文本块快速发送 |
| `Ctrl+Enter` | 文件区：在文件管理器中显示；文本块：**前置发送** |
| `Ctrl+双击` | 文本块前置发送（仅单独按住 Ctrl） |
| `Delete` / `Shift+Delete` | 移入回收站 / 确认后永久删除 |
| `Ctrl+C` / `Ctrl+Shift+C` | 复制文件对象或文本块正文 / 复制完整路径文本 |
| 右键、键盘菜单键 / `Shift+F10` | 打开默认右键菜单 / 另一个右键菜单 |
| `F4` / `Ctrl+S` | 文本块内置编辑器 / 保存 |
| `Ctrl+V` | 文本工作区：把剪贴板文字创建为固定文本块 |
| `Ctrl+F` 或 `/` | 聚焦搜索框并全选已有文字 |
| `Alt+T` | 切换"仅标题"搜索范围 |
| `Space` | 悬停文件时调用 Seer/QuickLook 外部预览 |
| 拖放时 `Ctrl` / `Shift` / 拖出时 `Alt` | 请求复制 / 请求移动 / 文本块拖出真实文件 |

---

## 3. 配置系统

### 3.1 文件格式与写入策略

- 文件为 `config.ini`，编码 **UTF-16LE + BOM + CRLF**。
- 其中 `; <PopDrop:area N>` 六行既是普通 INI 注释，也是程序的**布局锚点，不可删除或重复**；另有三个帮助锚点 `<PopDrop:PreviewHelp>`、`<PopDrop:QuickPreviewHelp>`、`<PopDrop:NoiseFilterHelp>`。
- 程序保存时**保留未修改的注释和未知配置项**，并在完整校验通过后**原子替换**原文件（对应源码中的"配置文档"模型，见 §5.x）。
- 仓库同时提供 `config.example.ini`（UTF-16LE 原始格式）与 `config.example.utf8.ini`（便于在 Git / 编辑器 / 跨平台工具中查看），两者内容等价。

### 3.2 配置节清单

| 节 | 用途 | 代表配置项 |
| --- | --- | --- |
| `[General]` | 共享通用设置 | `ConfigVersion`(30)、`StartupEnabled`、`Hotkey`、`DoubleHotkeyWorkspaceId`、`MainHotkeyWorkspaceMode`、`LastFileWorkspaceId`、`WindowMode`、`WindowWidth`/`WindowHeight`、`EscapeHidesPanel`、`UiScale`、`OpenFileMode`、`DefaultContextMenu`、`MaxFilesPerFolder`、`DisplayScope`、`FolderTimeMode`、`SortMode`、`FilterMode`、`FileExtensions`、`ViewMode`、`ThumbnailPolicy`、`ThumbnailSize`、`ThumbnailHorizontalGap`、`ThumbnailVerticalGap`、`ThumbnailTextLines`、`FileViewGroupTopSpacing`/`BottomSpacing`、`TextBlockCardWidth`/`Height`、`ShowRecentSidebar`、`RecentFileCount`、`CachePath`、`ContentUpdateMode`、`ConsistencyCheckMinutes` |
| `[Workspaces]` | 工作区顺序与当前项 | `Order`、`Active`、`PinnedScopeVersion` |
| `[Workspace:<ID>]` | 单个工作区 | `Name`、`Type`(`Files`/`Text`)、`Hotkey`、`SourceOrder` |
| `[WorkspacePinned:<ID>]` | 该工作区的固定项 | `File001`、`File002`… |
| `[TextSourcePinned:<SourceId>]` | 文本来源内部的置顶顺序 | `File001`… |
| `[Source:<ID>]` | 单个来源 | `WorkspaceId`、`Name`、`Path`、`Mode`(`Files`/`Launcher`)、`MaxFilesPerFolder`、`IncludeSubfolders`、`DisplayScope`、`FolderTimeMode`、`SortMode`、`FilterMode`、`FileExtensions`、`StripOrderPrefix`、`HideExtensions`、`OpenFileMode`、`NoiseFilterMode` |
| `[SourceExclude:<ID>]` / `[SourceAllow:<ID>]` / `[SourceIgnore:<ID>]` | 来源专属过滤规则（**按 SourceId 归属**，故重命名工作区或来源不会丢规则） | `PatternCount`、`PatternNNN` |
| `[Preview]` | 内置文件预览 | `Enabled`、`Side`、`HoverDelayMs`、`SwitchDelayMs`、`LeaveGraceMs`、`PreviousPreviewHoldMs`、`BackgroundColor`、`BackgroundOpacity`、`KeyboardDelayMs`、`Width`、`CacheEnabled`、`CacheStartAfterHiddenSeconds`、`CacheMaxMB`、`CacheMaxItems`、`CacheItemMaxKB`、`CacheUnreferencedDays`、`DirectImageMaxFileMB`、`DirectImageMaxEdge`、`DirectImageMaxPixelsMP`、`DirectImageMaxExpandedMB`、`DocumentEnabled`、`PdfEnabled`、`ShowFileInfo` |
| `[QuickPreview]` | 外部空格键预览 | `ExternalQuickPreviewProvider`(`Off`/`Seer`/`QuickLook`)、`SeerIntegrationEnabled`、`QuickLookPath` |
| `[ExternalTransfer]` | 外部投放/下载 | `EnablePublicUrlFallback`、`AllowHttp`(默认 0)、`MaxConcurrent`(1–6，默认 3)、`ShowCompletionNotifications` |
| `[FileManager]` | 文件管理器适配 | `Provider`、`Executable` |
| `[NoiseFilter]` | 噪音文件过滤 | `Enabled`、`HideHidden`、`HideSystem`、`HideTemporaryAttribute`、`HideIncompleteDownloads`、`CustomPatternCount`、`CustomPatternNNN`（只支持 `*` 和 `?`，不区分大小写） |
| `[OpenApps]` / `[OpenApp:<ID>]` / `[OpenAppAction:<appId>:<actionId>]` | 打开方式与工具动作 | `Order`；`Path`、`Name`、`Icon`、`Extensions`、`Enabled`、`ShowInOpenMenu`、`ActionOrder`；`Name`、`Executable`、`TargetTypes`、`ExecutionMode`、`Extensions`、`RequireCommonFolder`、`WorkingDirectoryMode`、`WorkingDirectory`、`Confirm`、`Enabled`、`ArgCount`、`ArgNNN` |
| `[TransferFavorites]` / `[TransferFavoriteLabels]` / `[RecentTargets]` | 复制/移动常用与最近目标 | `Path001`…`Path005`（常用最多 5）、最近最多 3 |
| `[ExcludedFolderNames]` | 全局排除的文件夹名称 | `Name001`…；默认示例 `.git`、`.svn`、`.hg`、`node_modules`、`__pycache__` |
| 兼容节（保留为空） | 旧版本迁移入口 | `[Folders]`、`[Folder:<名称>]`、`[PinnedFiles]`、`[Sources]` |

**布局锚点分区**：

```ini
; <PopDrop:area 1>   [General] / [ExternalTransfer] / [FileManager] / [Preview] / [QuickPreview] / [NoiseFilter]
; <PopDrop:area 2>   [Folders] / [PinnedFiles]
; <PopDrop:area 3>   [Workspaces] / [Workspace:*] / [WorkspacePinned:*] / [Source:*] / [Sources]
; <PopDrop:area 4>   [OpenApps] / [OpenApp:*] / [OpenAppAction:*]
; <PopDrop:area 5>   [TransferFavorites] / [TransferFavoriteLabels] / [RecentTargets]
; <PopDrop:area 6>   [ExcludedFolderNames]
```

### 3.3 未完成下载过滤的扩展名集合

`.crdownload`、`.part`、`.download`、`.opdownload`、`.partial`、`.aria2`，以及迅雷/常见 BT 客户端的 `.td`、`.td.cfg`、`.xltd`、`.bt`、`.bc!`、`.!ut`、`.!qB`；**正常的 `.torrent` 元数据不会被隐藏**。

### 3.4 运行期数据文件

`data\text-blocks\usage.ini`（UTF-16LE）是**文本块使用统计/智能排序数据**，非配置文件：`[Meta] Count=117`，每项 `[ItemNNNNNN]` 含 `Path`、`LastUsed`、`Total`、`WindowStart`、`WindowCount`、`NewUntil`——对应 §2.4 的"24 小时新内容保护 + 近期使用次数/历史次数智能排序"数据模型。

---

## 4. 版本演进（v1.0 → v2.0）

### 4.1 v1.0.0（首个稳定版）

- 版本号由 `0.10.0` 升至 `1.0.0`。
- **工程重构**：把原 **12,996 行 / 约 479 KB** 的单文件 `PopDrop.ahk` 拆分为 `modules/` 下 14 个模块，使用 AHK v2 文本 `#Include`，**零行为变更**；开发文档移入 `dev_doc/`；更新 Ahk2Exe 存根为 v2。
- 已具备能力：文件内容预览（Markdown/文本/代码/CSV 有界语义快照、PDF 第一页、DOCX 开头）、Seer/QuickLook 空格键集成、常驻 `PopDropPreview.exe` Helper、悬浮预览自动选侧、后台缓存生成、PDFium 可选渲染路径、7 个文件管理器适配、来源管理菜单、应用工具动作系统、外部内容投放、本地文件操作（OLE `IDropTarget`、复制到/移动到、回收站删除、重命名、固定项排序）、工作区系统、设置窗口、噪声过滤、下载任务管理、跨平台 Python 自测。

### 4.2 v1.1.x（v2.0 之前的能力积累）

| 版本 | 主要变化 |
| --- | --- |
| v1.1.0 | 主面板 Tab 与右侧纯图标工具栏、"内容更新方式"（极速显示/准确优先）、独立"界面设置"页、主面板整体缩放、`cache\index.db` SQLite 快照、`ReadDirectoryChangesW` 异步监听、后台状态收敛、`ConsistencyCheckMinutes` |
| v1.0.0-pre02 | 文本块工作区首版、来源内分类置顶、固定项实体与链接语义统一、`Ctrl+V`/粘贴按钮创建文本块、文本卡片宽高、主快捷键手势状态机、双击 F2 直达默认文本区 |
| v1.1.2 | 文本块"仅标题"搜索、前置发送快捷键由 `Shift+Enter`/Shift+双击 改为 **`Ctrl+Enter`/Ctrl+双击**（避免外部编辑器把 Shift 解释为扩展选区）、顶部识别区智能入口、分栏折叠、Windows 终端兼容发送、运行缓存无感维护、跨磁盘移动即时刷新 |

### 4.3 v2.0（当前主线）

**新功能**

1. **文本块工作区**：独立工作区类型，`.md`/`.txt` 卡片平铺；多关键字 AND 搜索、置顶、拖拽归类；`Enter` 快速发送；`Ctrl+Enter` 前置发送；Windows Terminal 兼容发送；搜索框"仅标题"范围与 IME 组合输入识别；纯键盘全流程。
2. **Tab 切换工作区 + 极速呈现**：切换从下拉框改为顶部原生 Tab（最多 8 个，其余进"更多"）；右侧纯图标工具栏；**F2 唤出后文件瞬间呈现**，不再等待扫描；双击 F2 直达文本块工作区，F2 首次按下立即显示、不再等待双击判定窗口。
3. **来源分栏折叠**：标题单击折叠/展开、按工作区记忆、工具栏批量展开/收起、分栏上下间距配置。
4. **选择窗口定位到此**（v2.0.9 由"另存为定位到此"扩展，v2.0.10 补 Inno Setup 自定义选择器）。
5. **Seer / QuickLook 改进**：悬停直接按空格预览（无需先选中）；修复多次触发、预览窗口落到 PopDrop 下方、A/B 路径串位；外部预览期间让出置顶层级。
6. **UI 自定义**：界面缩放、图标质量、缩略图大小、文件名行数、文本卡片宽高、分栏间距；新增"界面设置"与"内容更新方式"页。

**内部机制演进**

工作区**热视图**（每工作区保留独立原生 ListView，切换只 Hide/Show）、内容完整性拆分（"安全呈现"与"最新内容"分离）、可见期维护隔离（扫描/持久化/worker 清理以隐藏为边界）、缩略图移入可终止 Helper、逻辑 DIP 侧栏与多 DPI 修正、每日机会式缓存维护、工作区上移/下移排序、固定项"清除全部失效项目"、`Ctrl+Tab` 可靠循环、F2 首帧布局稳定化。

**代表性修复**

拖文件经过来源栏时底部不再误报"已选择 N 个项目"；F2 隐藏后再打开固定项栏不会窜成其他工作区内容；跨磁盘移动文件后旧缩略图立即消失不留空卡片；设置窗口快速操作不再卡死、保存失败自动回滚；Hover 预览切换工作区不再卡死；文本块→文件工作区切换不再残留顶部空白带；空文件夹不显示错缩略图、失效固定项不显示错图标；文本块搜索框聚焦时空格不再误触 Seer 预览。

### 4.4 配置版本演进

24（文本块首版）→ 25（快捷键默认与迁移）→ 26（置顶）→ 27（刷新/监听/稳定呈现）→ 29（v2.0 预发布）→ **30**（v2.0.1 忽略规则扩展）。

---

## 5. 关键技术方案

### 5.1 面板窗口与原生控件方案

#### 5.1.1 总体策略：不是原生窗口，而是"AHK Gui + 精准的原生消息"

全仓库 `CreateWindowEx` **零命中**——主面板由 AHK 的 `Gui()` 创建（`modules\PanelUi.ahk:23-31`）。窗口类注册、消息循环、控件创建等基础设施全部交给 AHK 运行时，项目把精力集中在 **AHK 覆盖不到的地方**：

- 原生控件的高级样式与消息（几乎全是 `SendMessageW` + 手写结构体 `Buffer`）；
- GDI+ 解码 PNG，做图标按钮的自绘；
- `comctl32` 子类化，做 Tab 条自绘；
- `user32` 时钟 / `SetWinEventHook`，做自动隐藏；
- OLE 拖放与 COM（见 §5.5）。

**边界很清晰：能用 AHK 表达的一律用 AHK，只有 AHK 无法表达的才下探到原生 API。** 代价是大量 x86/x64 双布局常量硬编码，收益是代码总量始终可控。

#### 5.1.2 控件选型：每个位域都有理由

主文件视图是**原生 ListView 图标视图**（`PanelUi.ahk:174-203`）：

```ahk
options := "xm y42 w716 h492 Icon +0x100 -E0x200 +Border"
view := Panel.AddListView(ScalePanelGuiOptions(options), ["文件", "修改时间"])
...
DllCall("user32\SendMessageW", "ptr", view.Hwnd, "uint", 0x1036,
    "ptr", 0x410000, "ptr", 0x410000, "ptr")   ; LVM_SETEXTENDEDLISTVIEWSTYLE
```

`0x410000` = `LVS_EX_DOUBLEBUFFER | LVS_EX_TRANSPARENTBKGND`（无闪烁绘制 + 透明背景）；`-E0x200` 去掉 ListView 默认的两像素 `WS_EX_CLIENTEDGE`——注释指出它会与底部实线分隔条 `WorkspaceBottomRule`（`x0 y0 w10 h1`、`0x00B9B9B9`）形成深浅双凹陷线。

**后创建的原生视图必须手工注册 OLE 投放**，因为 `RegisterDragDrop` 是按 HWND 注册的，AHK 新建控件不会自动继承：

```ahk
for targetPtr, _ in DropTargetObjects {
    RegisterDropTargetWindow(view.Hwnd, targetPtr)
    break
}
```

其余控件同样非默认选型：

| 控件 | 做法 | 原因 |
| --- | --- | --- |
| 图标按钮 | `Static` + `+Tabstop +0x100`（Owner Draw），GDI+ 解码 PNG 自绘 | 需要灰化备用图（`btn-paste-gray.png`）与 DPI 精确尺寸，Button 的主题绘制无法满足 |
| 分隔线 | 虚线 `AddPanelDashedSeparator`；实线 `AddPanelSolidRule` 作为独立 1px 控件覆盖在 ListView 顶边上 | 后者用于替代主题相关的 Tab 边框 |
| 下拉框 | `+0x210` = `CBS_OWNERDRAWFIXED \| CBS_HASSTRINGS` | 配合全局 `WM_DRAWITEM(0x002B)` / `WM_MEASUREITEM(0x002C)` 处理 |
| 搜索框 | **复合字段**：带 `+Border` 的外框 `AddText` + 内部 `-Border` 的 `AddUiEdit` + 右侧 `AddCheckBox "仅标题"` | 注释：这样长输入 / 光标 / 选区在任何 DPI 与面板宽度下都不会跑到复选框下面 |
| 占位符 | `EM_SETCUEBANNER (0x1501)` | 原生灰字提示 |
| 底部状态 | `StatusText`（可点击）+ `TransferStatusText`（"↓下载"） | 项数**不是**底部控件，而是纯工作区状态 `ItemCountText := {Text: "共0项"}` |

#### 5.1.3 ListView 原生分组：手写 `LVGROUP`

分组使用 **ListView 自带的 group API**，结构体按 `A_PtrSize` 双布局硬编码（`modules\ScanCacheIntegrity.inc:373-388`）：

```ahk
InsertListGroup(groupId, header, collapsed := false) {
    groupSize := A_PtrSize = 8 ? 152 : 96            ; LVGROUP
    group := Buffer(groupSize, 0)
    stateMaskOffset := A_PtrSize = 8 ? 40 : 28
    stateOffset     := A_PtrSize = 8 ? 44 : 32
    NumPut("uint", groupSize, group, 0)
    NumPut("uint", 0x15, group, 4)                   ; LVGF_HEADER|LVGF_STATE|LVGF_GROUPID
    NumPut("ptr", StrPtr(header), group, 8)
    NumPut("int", groupId, group, A_PtrSize = 8 ? 36 : 24)
    NumPut("uint", 0x1, group, stateMaskOffset)      ; LVGS_COLLAPSED
    NumPut("uint", collapsed ? 0x1 : 0, stateOffset)
    DllCall("user32\SendMessageW", "ptr", FileView.Hwnd, "uint", 0x1091,
        "ptr", -1, "ptr", group.Ptr, "ptr")          ; LVM_INSERTGROUPW，-1 = 追加到末尾
}
```

配套消息：`LVM_SETITEMW 0x104C`（配 `LVIF_GROUPID 0x100` 给行归属分组）、`LVM_REMOVEALLGROUPS 0x10A0`、`LVM_ENABLEGROUPVIEW 0x109D`、`LVM_SETGROUPMETRICS 0x109B` / `LVM_GETGROUPMETRICS 0x109C`。

**分组间距有一个"复利累加"陷阱**（`PanelUi.ahk:205-241`）：`LVM_SETGROUPMETRICS` 是相对当前值的，因此设置前必须先捕获该 HWND 的主题默认基线并缓存，之后每次写 `缓存基线 + 本次 DIP 增量`。注释明确：*不叠加在缓存基线上，刷新或重载设置时会复利累加*。

#### 5.1.4 行 → 数据的映射：并行 `Map`

ListView 行号是纯视觉索引，所有语义数据放在并行 `Map()` 里：

| 全局 | 含义 |
| --- | --- |
| `ItemPaths` | 行号（1-based）→ 文件路径 |
| `ItemLabels` | 行号 → 显示标签 |
| `ItemKinds` | 行号 → `"Folder"` 等 |
| `ItemOpenContexts` | 行号 → `{Area, SourceId, FolderPinned, GroupId, ...}` |
| `ItemFolderPaths` / `GroupFolderPaths` | 行号 / 分组 → 所属文件夹（双击分组标题用） |
| `RecentItemPaths` | 最近打开侧栏行号 → 路径 |
| `CollapsedFolderGroups` | 会话级折叠状态（按工作区 + 稳定 source ID） |

工作区切换时 `ItemKinds` / `ItemOpenContexts` **整体换绑**（从热视图缓存态取回或重建为空）——这是"切工作区零等待"的数据基础。

#### 5.1.5 DPI 适配：没有清单文件，全靠显式换算

项目**没有 DPI 感知清单，也没有调用 `SetProcessDpiAwarenessContext`**。适配完全靠显式换算，并刻意分成两族函数：

| 族 | 位置 | 用途 |
| --- | --- | --- |
| `PanelScale` | `modules\UiControls.ahk:703` | GUI 坐标（AHK 控件布局） |
| `PanelPhysicalScale` | `:719` | **物理像素**（原生 API 参数，如 ListView 分组度量） |

区分二者是必要的：AHK 的 GUI 坐标与原生 API 期望的像素在非 96 DPI 下并不相同。三条教训直接写在注释里：

- 工具栏是固定 **42 DIP** 带（`PanelUi.ahk:28-30`）；
- **AHK 的 `sNN` 是磅值不是像素**——96 DPI 下 14 px 需写成 `14 * 72 / 96 = 10.5` 磅（`:41-47`）；
- 原生度量类增量必须叠加缓存基线（见 5.1.3），像素换算用 `MulDiv` 避免二次取整。

#### 5.1.6 工作区 Tab：原生 Tab + 自绘子类化

刻意用**纯 Tab**（`PanelUi.ahk:33-47`）而非 `AddTab3`，注释记录了原因：

```ahk
; AddTab3 creates a separate themed ahk_dlg page host which AutoHotkey positions
; above the tab strip; on Windows 10 at 96 DPI its top two pixels cover every
; tab item.
tabHeight := PanelPixelsToGui(PANEL_TAB_HEIGHT_PX, Panel.Hwnd)
WorkspaceTabs := Panel.AddTab("xm ym w" PanelScale(620) " h" tabHeight " -Wrap", [""])
tabPointSize := PANEL_TAB_FONT_PX * 72.0 / 96.0    ; sNN 是磅值
WorkspaceTabs.SetFont("s" tabPointSize, "Microsoft YaHei UI")
```

因为导航页**不含任何子控件**（工作区内容是与 Tab 平级的独立 HWND，由应用切换），所以可以安全地子类化自绘：

- `EnableWorkspaceTabItemPadding()`（`:2762`）→ `comctl32\SetWindowSubclass` + `WorkspaceTabItemSubclass`（`:2777`），子类 ID `0x50445449`（"PDTI"），回调用 `CallbackCreate(fn, "", 6)`；
- 自绘 `PaintWorkspaceTabItems`（`:2816`）→ `DrawWorkspaceTabItem`（`:2871`），取系统色 `COLOR_WINDOW(5)` / `COLOR_BTNFACE(15)` / `COLOR_BTNSHADOW(16)`，文本用 `uxtheme\DrawThemeText`；
- 标签条外形用 `CreateRectRgn` + `CombineRgn(RGN_OR = 2)` + `SetWindowRgn` 裁剪（`:3094`）——这是全项目**唯一**的 `SetWindowRgn` 用途；
- 清理用 `RemoveWindowSubclass`（`:2963`）。

分页溢出（默认可见上限 8）由 `ResolveWorkspaceTabIndexes`（`:298`）计算，超出部分交给"更多 ▾"按钮 + 弹出菜单（`:319`、`:340`）。

#### 5.1.7 自动隐藏：原生时钟 + WinEvent 钩子 + 轮询看门狗

临时模式（`WINDOW_MODE_TEMPORARY`）下"失焦即隐藏"由三层共同保证，每层职责不同：

**(a) 原生 100 ms 时钟**（`PanelUi.ahk:1502-1519`）：

```ahk
AutoHideNativeTimerCallback := CallbackCreate(AutoHideNativeTimerProc, "Fast", 4)
AutoHideNativeTimerId := DllCall("user32\SetTimer", "ptr", 0, "uptr", 0,
    "uint", 100, "ptr", AutoHideNativeTimerCallback, "uptr")
```

`CallbackCreate(..., "Fast", 4)` 的 `"Fast"` 是关键——回调**不进入 AHK 的线程 / 状态管理**，避免在窗口消息处理中途破坏 AHK 状态。回调自身只投递自定义消息 `0x8032`，重活交给 AHK 线程的 `AutoHideNativeHidden`（`:1585`）。

**(b) 前台变化钩子**（`:1606-1622`）：

```ahk
AutoHideForegroundHook := DllCall("user32\SetWinEventHook",
    "uint", 0x0003, "uint", 0x0003,          ; EVENT_SYSTEM_FOREGROUND
    "ptr", 0, "ptr", AutoHideForegroundCallback,
    "uint", 0, "uint", 0,
    "uint", 0x0000 | 0x0002,                 ; WINEVENT_OUTOFCONTEXT | SKIPOWNPROCESS
    "ptr")
```

`WINEVENT_SKIPOWNPROCESS (0x0002)` 让本进程内的窗口切换不触发钩子（否则一打开设置窗面板就会隐藏）；跨进程前台变化同样只投递消息 `0x8031` 给 AHK 线程。

**(c) 暂停深度与所有权检查**：`AutoHidePauseDepth` + `BeginAutoHidePause` / `EndAutoHidePause`（`:1889` / `:1896`）供对话框期间暂停；`AutoHidePauseHasLiveOwner`（`:1829`）用 `AutoHideGuiOwnerAlive` 判断对话框是否还活着。最终判定链：`TryAutoHidePanel`（`:1757`）→ `AutoHideForegroundBelongsToCurrentProcess`（`:1819`，`GetWindowThreadProcessId` 与 `GetCurrentProcessId` 比对）→ `IsOwnedByPanel`（`:1856`）。

**(d) 延迟轮询**：`ScheduleAutoHideCheck(delayMs := 150)`（`:1699`）安排一次性检查，`AutoHideWatchdog`（`:1721`）作为低频兜底。

> **贯穿全项目的范式**：所有原生回调只做"投递自定义消息"，逻辑一律回到 AHK 线程执行；自定义消息常量集中在入口文件（`0x8031` / `0x8032`，`PopDrop.ahk:612,618`）。这是 AHK 下做原生互操作最安全的做法。

#### 5.1.8 窗口显示：绕开 AHK 的 `WinActivate`

`ActivatePanelWindowSafely`（`PanelUi.ahk:2139-2159`）注释解释了动机：*AHK 的 `WinActivate` 会重新按标题查找窗口，而原生自动隐藏可能恰好在这个极小时间窗内改变可见性，于是抛异常*。因此全部改为 HWND 直调，且不抛异常：

```ahk
if restore && DllCall("user32\IsIconic", "ptr", hwnd, "int")
    DllCall("user32\ShowWindow", "ptr", hwnd, "int", 9)      ; SW_RESTORE
else if !DllCall("user32\IsWindowVisible", "ptr", hwnd, "int")
    DllCall("user32\ShowWindow", "ptr", hwnd, "int", 5)      ; SW_SHOW
DllCall("user32\BringWindowToTop", "ptr", hwnd, "int")
DllCall("user32\SetForegroundWindow", "ptr", hwnd, "int")
```

窗口图标只在初始化时 `LoadImageW(..., IMAGE_ICON=1, ..., LR_LOADFROMFILE=0x10)` 加载一次，之后经 `WM_SETICON (0x80)` 用 `ICON_SMALL(0)` / `ICON_BIG(1)` 直投 HWND。注释指出编译版主图标已由 Ahk2Exe 嵌入，旧实现每次刷新都重载 `HICON`，造成**句柄泄漏**（`:2499-2519`）。

#### 5.1.9 缩略图布局与标签拟合

`ApplyViewMode`（`:3619`）→ `ApplyThumbnailLayout`（`:3639`）三步：

1. 扩展样式加 `LVS_NOLABELWRAP (0x80)`；
2. `LVM_SETICONSPACING (0x1035)` 设定 `cx` / `cy`；
3. `GetThumbnailLabelReserve`（`:3666`）：`WM_GETFONT (0x31)` 取当前字体 → `GetTextMetricsW` 量出行高，算出标签需保留的垂直空间。

文本拟合 `FitThumbnailLabel`（`:3724`）用**二分搜索 + "…" 省略号**，逐次调用 `MeasureListViewText`（`:3762`）测量宽度，最后由 `ApplyFileViewLabels`（`:3690`）批量回写。这里**没有用系统自带的标签截断**——为的是在缩略图模式下精确控制标签行数与省略位置。

#### 5.1.10 面板交互状态机

**手势是单个对象字面量，没有显式状态枚举**（`modules\PointerInput.ahk:68-87`）：

```ahk
FilePointerGesture := {
    Serial:      ++FilePointerGestureSerial,
    Active:      true,
    Hwnd, Row, Path,
    Key:         GetDisplayedItemActivationKey(hwnd, row, path),
    X, Y, DownTick: A_TickCount,
    DoubleClick: msg = 0x0203,          ; ← 唯一的双击判别式
    Selection:   <snapshot array>,
    Modifiers:   <bitmask>,
    OpenRegion:  row && path != "",
    ChildControl: false,
    Dragging:    false,
    Marquee:     !row,                  ; 空白处按下 = 框选
    Cancelled:   false
}
```

三个值得注意的设计：

**① 双击没有任何时间判别。** `WM_LBUTTONDOWN (0x0201)` 与 `WM_LBUTTONDBLCLK (0x0203)` 注册到**同一个处理器** `FileViewLeftButtonDown`（`PopDrop.ahk:642`），双击语义完全由 `msg = 0x0203` 一个条件区分。单击激活也不是"延迟等待是否双击"型，而是**释放即开**——`OPEN_MODE_SINGLE` 分支在 `OpenFileViewItem` 里直接 `return`（`ItemActions.ahk:36-40`），因为释放时已经打开过。

**② 修饰键必须从消息 `wParam` 补采**（`PointerInput.ahk:48-51`）：快速松键会让 `GetKeyState` 的状态降级，因此按下瞬间用 `GetPointerModifierMaskForMouseMessage(wParam)` 把 `MK_CONTROL (0x0008)` / `MK_SHIFT (0x0004)` 位并进来。释放时复核优先使用**手势里存下的** `Modifiers`（`ResolveFileViewDoubleClickModifierMask`，`:478`），而不是实时状态。

**③ 重排优先于 OLE 拖拽**（`:175-220`）：拖动超过 `SM_CXDRAG` / `SM_CYDRAG`（`GetSystemMetrics(68/69)`）后，先在**整个原生分组矩形内**判定是否落在"固定项 / 文本源重排"区域；命中则 `SetCapture` 进入重排态，走出区域才 `ReleaseCapture` 并落穿到 OLE。注释解释了动机：*只在图块标签区域判定，会导致图块间留白、列表行非标签区域或快速移动时意外切进 OLE，使排序几乎无法触发*。

真正的 OLE 启动（`:222-253`）按工作区类型分流：文本工作区且全部路径都是文本块（且未按 Alt）→ `BeginTextDrag`（`CF_UNICODETEXT`）；否则 → `BeginShellDrag`（`CF_HDROP`）。两者都设置 `ActiveInternalDragContext := {Token, Items, Paths}` 供投放侧识别"内部拖拽"，并在 `finally` 中清理 + `KeepTemporaryPanelVisibleAfterDrag()`。`DoDragDrop` 的允许效果掩码为 `0x7`（`DROPEFFECT_COPY|MOVE|LINK`）。

**取消路径覆盖得很全**（`:533-640`）：右键按下、滚轮 / 滚动条、`WM_CANCELMODE`、`WM_CAPTURECHANGED`、失焦各有独立处理。其中 `FileViewCaptureChanged` **仅当左键仍按下时才取消**——避免正常的 `ReleaseCapture` 误杀正在拖拽的会话。

**重排提交的几何判定**（`:309-323`）用 `LVM_GETITEMRECT (0x100E)` + `LVIR_BOUNDS` 取目标行矩形，**缩略图 / 文本模式按水平中线、列表模式按垂直中线**决定插入在目标之前还是之后。`ReorderPinnedPath`（`:879-910`）在 `RemoveAt` 之后**必须重新解析目标索引**，写盘失败时用 `RestoreActivePinnedPaths(originalPaths)` 回滚；若重排结果与原顺序相同则短路返回，不做无意义的写盘与重绘。

**"Ctrl+单击前置发送"有一个重试循环**（`ItemActions.ahk:61-99`）：只要左键仍按下、或 Shift / Alt / Win 仍按住（**故意允许 Ctrl 位**），就以 `SetTimer(..., -15)` 重新武装，直到 10000 ms 预算耗尽才提示"鼠标或其他修饰键未释放，已取消本次前置发送"——因为要等用户松开 Ctrl 才能安全发送 `^v`。

### 5.2 扫描、缓存与性能方案

#### 5.2.1 核心原则：UI 进程绝不做目录枚举

整个程序是**一个 AHK 脚本 + 三个运行角色**，路由发生在任何 GUI / 热键 / 托盘 / COM 初始化**之前**，且路由后立即 `ExitApp`：

| 角色 | 参数 | 入口 |
| --- | --- | --- |
| 自检 | `--self-test` | `PopDrop.ahk:101-104` |
| 缩略图缓存 worker | `--thumbnail-cache-worker <requestPath> <readyPath>` | `:106-110` |
| 扫描 worker | `--scan-worker` | `:112-118` |
| 主界面 | 无参数 | 继续执行至 `:620+` |

worker 分流时先 `try WinHide("ahk_id " A_ScriptHwnd)` 隐藏解释器窗口（`:107`、`:115`），配合 `#NoTrayIcon`（`:2`）与"托盘图标在 worker 分流之后才打开"（`:120-122` 的 `A_IconHidden := false`）来消除短命 worker 的图标闪烁。

因为要允许 worker 实例共存，入口用 `#SingleInstance Off`（`:3`），改用**命名互斥体**只保护主 UI（`:126-130`）：

```ahk
global MainInstanceMutex := 0
MainInstanceMutex := DllCall("kernel32\CreateMutexW", "ptr", 0, "int", 0,
    "wstr", "Local\PopDrop.Main", "ptr")
if !MainInstanceMutex || DllCall("kernel32\GetLastError") = 183
    ExitApp                                     ; ERROR_ALREADY_EXISTS
```

worker 的创建走同一套模板（`ScanCacheIntegrity.inc:2377` `StartScanWorkerProcess` / `:1108` `StartThumbnailCacheWorkerProcess`）：

```ahk
startupInfoSize := A_PtrSize = 8 ? 104 : 68        ; STARTUPINFOW
startupInfo := Buffer(startupInfoSize, 0)
NumPut("uint", startupInfoSize, startupInfo, 0)
processInfo := Buffer(A_PtrSize * 2 + 8, 0)        ; PROCESS_INFORMATION
DllCall("kernel32\CreateProcessW",
    "wstr", executable, "ptr", commandBuffer.Ptr, "ptr", 0, "ptr", 0, "int", false,
    "uint", 0x08000000,                            ; CREATE_NO_WINDOW
    "ptr", 0, "wstr", A_ScriptDir,
    "ptr", startupInfo.Ptr, "ptr", processInfo.Ptr, "int")
```

- **编译版 / 源码版双形态**：`A_IsCompiled` 时 `executable := A_ScriptFullPath`，否则 `A_AhkPath` + 脚本路径（`:1109-1117`）；
- 命令行由 `QuoteWindowsArgument()` 逐参数转义后写入 `Buffer`——因为 `CreateProcessW` 需要**可写**的 `lpCommandLine`；
- `bInheritHandles = false`、工作目录 `A_ScriptDir`、只关闭 `threadHandle` 并返回 `pid`。

退出时 `modules\Lifecycle.ahk:3` 的 `Cleanup()` 逐项拆除每个定时器 / 进程 / 句柄，以 `OleUninitialize` 结束（`:69`），由 `OnExit(Cleanup)` 挂载。

#### 5.2.2 进程间通信：文件系统 + 三元组校验

扫描结果**没有走管道或共享内存**（共享内存只用于缩略图像素传给原生助手），全部走文件系统，因为这样 AHK 侧不需要任何额外原生代码。目录结构：

```
<CacheDir 或 %TEMP%\PopDrop>\
  request-<生成号>.ini        ← 主进程写，worker 读
  ready-<生成号>\             ← 结果目录
    source-0000.ini           ← 每个来源一个文件
    source-0001.ini
    recent.ini                ← 可选
    complete.ini              ← 完成哨兵（Generation / Fingerprint / WorkspaceId）
```

生成号带 `A_TickCount` 前缀，天然按时间排序且进程内唯一（`:2509-2515`）：

```ahk
ipcDir := CacheWritable ? CacheDir : A_Temp "\PopDrop"
generation := Format("{:016X}-{:08X}", A_TickCount, ++ScanGeneration)
requestPath := ipcDir "\request-" generation ".ini"
readyPath := ipcDir "\ready-" generation
```

**原子写入统一用"`.writing` 临时文件 + `FileMove(temp, final, 1)`"**：`WriteScanResultAtomic`（`:2008`）、`WriteWorkerCompletionAtomic`（`:2063`）、`WriteCurrentScanCache`（`:2856`）、缩略图 worker（`:1148`、`:1171`）一致；worker 异常时会清理残留的 `complete.ini.writing`（`:1879`）。

**结果采纳的门槛是三元组全等**（`PollWorkerResult`，`:2686-2692`）：

```ahk
if FileExist(completePath) {
    validComplete := IniRead(completePath, "Meta", "Generation", "") = ...
        && IniRead(completePath, "Meta", "Fingerprint", "") = ...
        && StrLower(IniRead(completePath, "Meta", "WorkspaceId", "")) = ...
}
```

即 **generation（这是不是我要的那次）+ fingerprint（设置有没有变过）+ workspaceId（是不是这个工作区）** 必须同时匹配。轮询间隔 **75 ms**（`:2557`），而"worker 忙碌"状态**延迟 180 ms 才显示**（`:2556`），避免瞬时闪烁。

#### 5.2.3 增量扫描、合并与过期

请求文件 `request-<生成号>.ini` 的协议版本为 `"6"`（`ReadWorkerRequest` 在 `:1888` 用它 `throw Error("unsupported request version")`），结构为：

- `[Meta]`：`Version`、`Generation`、`Fingerprint`、`WorkspaceId`、`FolderCount`、`RecentFileCount`、`IncludeRecent`、全局排除名（`GlobalExcludedNameCount` / `GlobalExcludedNameNNN`）、固定项路径（`PinnedPathCount` / `PinnedPathNNN`）
- `[FolderNNN]`（三位零填充）：`Scan`、`Name`、`Path`、`IncludeSubfolders`、`DisplayScope`、`FolderTimeMode`、`MaxFilesPerFolder`、`SortMode`、`FilterMode`、`FileExtensions`、`NoiseEnabled`、`HideHidden`、`HideSystem`、`HideTemporaryAttribute`、`HideIncompleteDownloads`、自定义与来源模式、排除/允许路径（各带 `Count` + `NNN` 列表）

注意 `:2347-2349`：**文本工作区的 `MaxFilesPerFolder` 被强制写 0**（文本工作区不按数量截断）。

**`[FolderNNN] Scan` 就是增量开关**：`shouldScan := !IsObject(sourceKeys) || sourceKeys.Has(StrLower(sourceKey))`（`:2339-2341`）；全量扫描时 `sourceKeys = 0`（非对象）。每个来源的脏令牌存在 `WorkerSourceDirtyTokens[key]` / `WorkerRecentDirtyToken`（`:2538-2552`），合并队列为 `PendingScanSourceKeys` / `PendingFullRefresh`（`:2489-2503`）。

**全量扫描的合并规则**（`:2492-2495`）——已经有一个全量扫描在跑时直接丢弃新请求，除非是文件操作触发的：

```ahk
if WorkerRunning {
    if !IsObject(sourceKeys) && WorkerFullScan && reason != "file-operation"
        return                      ; 已有一个全量扫描在跑 → 直接丢弃
    PendingRefresh := true
}
```

但**手动刷新是显式恢复命令**，必须能替换挂起的 worker（`:2481-2491`）：`if WorkerRunning && (workerStale || reason = "manual")` → `ProcessClose(WorkerPid)` + `FinishWorker(false)`。**worker 过期判定**（`:2478-2480`）：工作区 ID 或配置指纹变化即视为过期。

`WriteScanRequest` 还接受一个可选 `context` 参数（`:2310`、`:2314-2318`），允许**为"非活动工作区"构造请求**——这是后台预热的基础。

#### 5.2.4 非活动工作区预热："切工作区不用等"的来源

流水线：`QueueInactiveWorkspaceScans`（`:2955`）→ `StartNextInactiveWorkspaceScan`（`:2968`）→ `PollInactiveWorkspaceScan`（`:3056`，与活动扫描**共用** worker 槽位，因此需要排队）→ `FinishInactiveWorkspaceScan`（`:3169`）。配套的队列去重（`MergeInactiveScanQueueTokens` `:2885`）、令牌清理（`ClearInactiveScanQueueSourceToken` `:2936`）、失败重排（`RequeueInactiveWorkspaceJob` `:3181`）、骨架结果（`BuildWorkspaceScanSkeleton` `:3145`，立即构造供 UI 显示）与快照记忆（`RememberWorkspaceSnapshot` `:3196`）。

真正的"零等待"来自**热视图**：`WorkspaceFileViewStates := Map()`（`PopDrop.ahk:144-147`）为每个访问过的工作区保留**已填充的原生 ListView 控件及其行元数据**，切回时直接 `ShowWindow` 现有 HWND，而不是重建分组 / 项 / 图像。相关函数：`RememberActiveWorkspaceFileView`（`PanelUi.ahk:931`）、`ActivateWorkspaceFileView`（`:996`）、`CommitWorkspaceSwitchVisuals`（`:1169`）。

配套的运行期改动（`PHASE1_MEMORY_WORKSPACE_SWITCH.md`）：切换工作区不再同步重读 / 改写 `config.ini`，改为内存状态绑定 + **延迟 250 ms 合并写盘**。

#### 5.2.5 配置指纹（FNV-1a）：缓存失效的唯一锚点

`ComputeConfigFingerprint`（`:2112-2147`）把所有影响扫描结果的设置拼成一个字符串后哈希，算法是 **FNV-1a 32 位**（`:2149-2156`）：

```ahk
HashString(text) {
    hash := 2166136261                       ; FNV offset basis
    for char in StrSplit(text) {             ; 按 UTF-16 码元迭代
        hash := (hash ^ Ord(char)) * 16777619
        hash := hash & 0xFFFFFFFF
    }
    return Format("{:08X}", hash)
}
```

指纹原文（`:2122-2145`）以 `"v6|"` 开头，含工作区 ID / 类型、`recent`、全局排除名、四项全局噪声开关、全局自定义模式（以 `Chr(30)` 分隔）、固定项路径，随后**逐个文件夹**追加 Name / Path（小写、去尾反斜杠）/ Mode / Sub / Scope / FolderTime / Max / Sort / Filter / Ext / ExcludedPaths / AllowedPaths / NoiseMode / SourcePatterns。

**这个指纹是"复用是否合法"的唯一天平**，三处都校验它：worker 过期（`:2480`）、结果采纳（`:2690`）、快照加载（`RuntimeIndexLoadSnapshot(ActiveWorkspaceId, CurrentConfigFingerprint)`，`:2162`）。由此保证**性能复用永远不会跨越设置变更**。

#### 5.2.6 两级磁盘缓存

**第一级：工作区快照 INI**（`modules\Configuration.ahk:894-900`）：

```ahk
CacheDir := ResolveCacheDirectory(CachePathSetting)
InitializeRuntimeIndex()
CacheFilePath := CacheDir "\workspace-" HashString(StrLower(ActiveWorkspaceId)) ".ini"
```

缓存目录的解析有一条显式降级链（`ResolveCacheDirectory` `:2075-2097`）：用户设置 → `DataRootDir\cache` → `A_ScriptDir\cache` → `%LOCALAPPDATA%\PopDrop\cache`。每一级都要求 **非远程路径且可写**：

```ahk
for candidate in candidates {
    ; Keep the transactional runtime cache off UNC/mapped network drives.
    if !IsPotentiallyRemotePath(candidate) && EnsureCacheDirectory(candidate)
        return candidate
}
return fallback
```

可写性用**写探测文件**（`.write-test-<tick>`）判断而非只看 `DirCreate` 是否成功（`EnsureCacheDirectory` `:2099-2110`）——因为 UNC / 映射盘上 `DirCreate` 可能"成功"但实际不可写。

**第二级：SQLite 运行时索引**（`modules\RuntimeIndex.ahk`），库文件 `index.db` 位于 `CacheDir`：

- 引擎用系统自带的 **`winsqlite3.dll`**，经 `LoadLibraryExW` + `LOAD_LIBRARY_SEARCH_SYSTEM32 (0x800)` 加载（**强制系统副本，防 DLL 劫持**），函数指针按 `cdecl` 调用——不需要任何第三方依赖；
- 表：`meta`、`workspace_snapshot`、`source_snapshot`、`item_snapshot`、`recent_snapshot`、`watch_state`；
- **WAL 模式**；写入用 `BEGIN IMMEDIATE` / `COMMIT` 事务包裹（`RuntimeIndexSaveSnapshot` `:146`）；
- **损坏检疫**：打开或校验失败时把 `index.db` 改名隔离、重建新库，而不是让程序起不来。

读取优先走 `RuntimeIndexLoadSnapshot`（`:2162-2164`），未命中或指纹不符才回退 INI 路径。

#### 5.2.7 缩略图预热与熔断退避

缩略图有**两个机会**，都不在用户等待路径上：

**第一机会：批量预热 worker**（`BeginThumbnailCacheWorker` `:1071`）。子进程调 `WarmShellThumbnailCache(path, size)`（`:1179`）触发 Shell 生成缩略图：

```ahk
initialized := DllCall("ole32\CoInitializeEx", "ptr", 0, "uint", 0, "int") >= 0
count := Max(0, Min(16, Integer(IniRead(requestPath, "Thumbnail", "Count", "0"))))
try size := Integer(IniRead(requestPath, "Thumbnail", "Size", "96")) catch size := 96
Loop count {
    path := IniRead(requestPath, "Thumbnail", "Path" Format("{:03}", A_Index), "")
    results.Push(path != "" && WarmShellThumbnailCache(path, Max(16, Min(size, 512))))
}
FileMove(readyWritingPath, readyPath, 1)
if initialized
    DllCall("ole32\CoUninitialize")
```

**批量上限 16 个 / 批，尺寸夹取 16..512**。

**第二机会：前台可见项用原生助手**（`QueueThumbnailEnhancement` `:543` + `EnhanceNextThumbnail` `:556`）。这条路径走 C++ 的 `PopDropPreview.exe`：`CreateFileMappingW` + `MapViewOfFile` 传像素、3 个命名 `CreateEventW` 握手，并用 Job 对象限制 `JOB_OBJECT_LIMIT_PROCESS_MEMORY | KILL_ON_JOB_CLOSE`（`0x2100`）、上限 **512 MiB**——保证缩略图助手崩溃或失控都不会拖垮主程序，且随主进程退出而终止。

**熔断与退避**：`RegisterNativeThumbnailTransportFailure`（`:627`）/ `...Success`（`:651`）累计失败；`ThumbnailBackgroundStartAllowed`（`:594`）门控是否允许再启动；`ThumbnailBackgroundRetryDelay`（`:614`）给出退避时长（设计文档记录 **60 s 熔断**）。另有像素布局校验 `NativeThumbnailPixelLayoutValid(width, height, stride)`（`:918`）——防止助手传来的畸形缓冲被注入 ImageList。

#### 5.2.8 目录来源实时监听

`modules\SourceWatch.ahk` 用 `ReadDirectoryChangesW` + **重叠 I/O + 轮询**（不是完成例程，因为 AHK 没有天然的 IOCP 回调）：

```ahk
handle := DllCall("kernel32\CreateFileW", "wstr", definition.Path,
    "uint", 0x0001,      ; FILE_LIST_DIRECTORY
    "uint", 0x7,         ; FILE_SHARE_READ|WRITE|DELETE
    "ptr", 0, "uint", 3, ; OPEN_EXISTING
    "uint", 0x42000000,  ; FILE_FLAG_BACKUP_SEMANTICS | FILE_FLAG_OVERLAPPED
    "ptr", 0, "ptr")
...
return DllCall("kernel32\ReadDirectoryChangesW",
    "ptr", watcher.Handle, "ptr", watcher.Buffer.Ptr,
    "uint", watcher.Buffer.Size, "int", watcher.Subtree,
    "uint", 0x5F,        ; FILE_NOTIFY_CHANGE_* 全集
    "ptr", 0, "ptr", watcher.Overlapped.Ptr, "ptr", 0, "int")
```

- `0x42000000` = `FILE_FLAG_BACKUP_SEMANTICS (0x02000000)` \| `FILE_FLAG_OVERLAPPED (0x40000000)`——前者是**能对目录 `CreateFileW`** 的前提条件；
- 通知过滤器 `0x5F` 打开名称 / 属性 / 大小 / 最后写入 / 最后访问 / 创建 / 安全全部变化；
- 轮询用 `WaitForSingleObject`（0 超时）+ `GetOverlappedResult`；**零字节返回表示缓冲区溢出、事件已丢失，必须触发全量重扫**，绝不能当作"无变化"；
- 调度 `ReconcileSourceWatchers`（`:121`）重新对齐要监听的来源集合，随后 `SetTimer(PollSourceWatchers, 150)`（`:190`）；
- **120 ms 防抖**：`QueueSourceWatcherChange`（`:307`）→ `SetTimer(FlushSourceWatcherChanges, -120)`；
- 监听状态持久化在 SQLite 的 `watch_state` 表。

`StartBackgroundScan` 开头即调用 `ReconcileSourceWatchers()`（`ScanCacheIntegrity.inc:2473`），保证"扫描前监听器已对齐"。

#### 5.2.9 排序与过滤

**自然排序直接用 Shell 的 `shlwapi\StrCmpLogicalW`**（`:1722-1725`），不自己实现——这是"文件 2 排在文件 10 前面"的正确做法。

比较器 `CompareFiles(a, b, sortMode)`（`:1727`）的 `ModifiedDesc` 分支是**三级比较**（`:1740-1749`）：时间倒序 → 名称自然序 → 路径大小写不敏感兜底：

```ahk
if a.Modified < b.Modified
    return 1
if a.Modified > b.Modified
    return -1
cmp := StrCmpLogicalW(a.Name, b.Name)
if cmp != 0
    return cmp
return StrCompare(a.Path, b.Path, true)
```

排序算法是 `SortFileArray(&amp;files, sortMode)`（`:1755`）——自底向上**稳定归并排序**，保证同键项的相对顺序确定。但更重要的是**插入时机**：`AddSortedCandidate(&amp;files, candidate, limit, sortMode)`（`:1516`）在**收集阶段就维持有序并按 limit 提前截断**，因此只有恰好超限时才需要完整排序。这是"只显示最新 N 个"场景下避免全量排序的关键。

过滤在 `EnumerateDirectoryForScan`（`:1563`）逐项进行：

- 忽略 / 噪声模式走**预编译**的 `MatchesCompiledIgnorePattern(fileName, patterns)`（`:1642`），而不是逐项现编译正则；
- 噪声诊断有上限 `NOISE_DIAGNOSTIC_LIMIT := 200`（`PopDrop.ahk:88`），避免诊断本身成为负担；
- **"PopDrop 自己正在接收的临时文件"与"未完成下载"是两个独立原因**（`:1582-1585` 的 `PopDropIncompleteTransfer` 与 `IncompleteDownload`）——前者不该被用户看到，后者是用户自己的事；
- 隐藏 / 系统 / 临时属性分别由三个开关控制。

#### 5.2.10 两阶段显示与渲染签名

这是全项目**最重要的性能决策**。`ShowPanelInstant`（`PanelUi.ahk:2161-2196`）与 `FinishPanelShow`（`:2205-2261`）被刻意拆开。

**第一阶段只做能在一帧内完成的事**，注释（`:2169-2174`）写明"保持上一个完整原生帧可见，配置加载与刷新检查刻意移到 `FinishPanelShow()`"：

```ahk
PrepareSaveDialogTaskLinksBeforePanelShow()
PreviewBeginPanelSession()
ApplyWindowMode()
ResizePanel(Panel, 0, PanelScale(WindowWidth), PanelScale(WindowHeight))
Panel.Show("w" PanelScale(WindowWidth) " h" PanelScale(WindowHeight))
PanelVisible := true
ResetPanelIconVisualState(true)
```

关键在 **`ResizePanel` 在窗口隐藏时就执行**，因此第一可见帧已是最终几何；`Panel.Show()` 显式带上 `w/h` 而不依赖 `AutoSize`。

**第二阶段延迟到"主热键双击容差 + 40 ms"之后**（`:2193`）：

```ahk
QueuePanelShowFinish(MainHotkeyDoubleTolerance() + 40)
```

延迟量取这个值是有意的——**在主热键双击窗口关闭之后**才做重活，这样连续两次 F2 不会触发两次昂贵的刷新。任务用 generation 校验（`:2210`），过期即返回。

第二阶段内每件事都先判断"是否真的需要"：

```ahk
configChanged := ConfigFileChangedSinceLoad()   ; 只在配置被外部改过才重载
if configChanged { LoadSettings(); InstallWorkspaceHotkeys(); ApplyWindowMode(); ... }
RepairActiveWorkspacePinnedRuntimeBinding()
if EnforceWorkspaceSearchVisibility() → RequestNativeLayout()
if !ScanResultLoaded → LoadDiskScanCache()
if !IsPanelRenderCurrent() → PopulatePanel()      ; 保留帧仍有效就不重建
if !IsRecentRenderCurrent() → PopulateRecentSidebar()
if !CurrentScanComplete → StartBackgroundScan(0, "incomplete-show", ...)
SetTimer(RequestNativeLayout, -30)
```

注释（`:2213-2216`）解释了为何要省掉配置重载：*重载一份没变的配置会重建 Tab 状态并同步重绘工具栏，结果就是每次呼出都有一个确定的闪烁*。内部写入者会维护 `LoadedConfigStamp`（`PopDrop.ahk:37`），只有真正的外部修改才需要昂贵路径。

**渲染签名短路**由 `ComputePanelRenderSignature` / `IsPanelRenderCurrent` / `ComputeRecentRenderSignature` / `IsRecentRenderCurrent`（`:1363-1390`）实现，使同一工作区的保留帧可以跨多次 F2 召唤存活。此外 `PanelRenderInProgress`（`PopDrop.ahk:150`）保证定时器与 GUI 回调不会交错两次原生 ListView 重建，也不会缓存半成品视图。

#### 5.2.11 隐藏后的延迟阶梯

`HidePanel`（`PanelUi.ahk:2526-2569`）在 `Panel.Hide()` 之后按**递增延迟**排了一整队一次性后台任务（全部用负延迟 `SetTimer`）：

| 延迟 | 任务 | 意图 |
| --- | --- | --- |
| `-1 ms` | `CancelStaleWorkspaceWorker` | 先止损 |
| `-5 ms` | `StartDeferredVisibleBackgroundScan` | |
| `-10 ms` | `FlushPendingScanCacheWrite` | |
| `-20 ms` | `FlushDeferredWorkspaceSnapshotWrites` | |
| `-30 ms` | `FlushWorkspacePerformanceTrace` | |
| `-40 ms` | `ImportNextWarmedThumbnail` | |
| `-50 ms` | `EnhanceNextThumbnail` | |
| `-60 ms` | `PersistPendingActiveWorkspaceState` | |
| `-80 ms` | `StartNextInactiveWorkspaceScan` | 预热放在最后 |
| 之后 | `ScheduleCacheMaintenanceAfterHide()` | 最低优先级 |

设计意图清楚：**面板已不可见，这些工作不再与用户交互竞争**；按 10 ms 间隔错峰，避免单帧内多个重活叠加。所有写盘合并器都带 `force` 参数（`FlushPendingScanCacheWrite(force := false)` 等），退出或重载前强制冲刷。

#### 5.2.12 有界工作与预算

所有后台循环都有硬上限，这是"后台任务不拖慢前台"的制度性保证：

| 机制 | 上限 | 位置 |
| --- | --- | --- |
| 缩略图预热批 | 16 / 批，尺寸夹取 16..512 | `ScanCacheIntegrity.inc:1150`、`:1160` |
| worker 结果轮询 | 75 ms | `:2557` |
| "worker 忙碌"状态延迟 | 180 ms | `:2556` |
| 源监听轮询 / 防抖 | 150 ms / 120 ms | `SourceWatch.ahk:190`、`:307` |
| 原生看门狗时钟 | 100 ms | `PanelUi.ahk:1517` |
| 自动隐藏检查 | 150 ms | `PanelUi.ahk:1699` |
| Ctrl+单击发送重试 | 15 ms × 最多 10000 ms | `ItemActions.ahk:81-90` |
| 缓存维护 | 检查 256 / 删除 24 / 150 ms | `CacheMaintenance.ahk:107-108` |
| 噪声诊断上限 | 200 | `PopDrop.ahk:88` |
| 最近文件默认数 | 12 | `ScanCacheIntegrity.inc:1893` |
| 助手超时 / Job 内存 / 熔断 | 5 s、12 s / 512 MiB / 60 s | 设计文档 `PHASE1_MEMORY_WORKSPACE_SWITCH.md` |

**"每一个后台循环都有预算"这件事本身，就是这套架构能保持响应性的原因**——它不依赖某一处优化，而是把"不许无限工作"变成了全局约定。

### 5.3 进程模型与原生 Helper 通信协议

PopDrop 有**两类原生 Helper**，二者的通信机制完全不同，分别适配各自的负载特征：

| Helper | 启动参数 | 通信机制 | 承载负载 |
| --- | --- | --- | --- |
| `PopDropPreview.exe` | `--shared <会话名>` | **常驻进程 + 共享内存 + 事件** | 预览像素（≤4 MiB 位图）与缓存生成 |
| `PopDropTransfer.exe` | `--request <request.ini 路径>` | **一次性进程 + 文件 + 命令行** | 跨进程 `IDataObject` 接管、网络下载 |

两者都提供 **x64 / x86 两份**，按 `A_PtrSize` 选择。位宽不只是兼容问题：外部拖拽的 `IDataObject` 由来源进程创建，**32 位 helper 不可能接管 64 位来源的对象**（COM 跨位宽 marshaling 会失败），因此 helper 必须与接收端同宽。

#### 5.3.1 预览 Helper：共享内存协议

AHK 侧 `PreviewEnsureHelper()` 的建立顺序：

1. 生成会话 token `Format("{:08X}{:08X}", A_TickCount, GetCurrentProcessId())`；
2. 创建命名对象：`Local\PopDropPreview-<token>-Map`（`CreateFileMappingW`，`PAGE_READWRITE`，**4268288 字节**）、`-Request`、`-Response`（手动态）、`-Shutdown`（自动重置事件，初始已置位）；
3. `MapViewOfFile` → `RtlZeroMemory` 全图 → 写头：偏移 0 = `0x56504450`(`"PDPV"`)，偏移 4 = `PREVIEW_PROTOCOL_VERSION`(5)；
4. `Run('native\bin\<x64|x86>\PopDropPreview.exe --shared "Local\PopDropPreview-<token>"', ..., "Hide", &pid)`。

Helper 侧 `wWinMain` 只接受 `argc == 3 && argv[1] == "--shared"`，随后：

```cpp
SetPriorityClass(BELOW_NORMAL_PRIORITY_CLASS);
winrt::init_apartment(winrt::apartment_type::multi_threaded);  // 必须 MTA，否则 WinRT 的 .get() 会死锁
```

`RunShared` 打开映射与三个事件后**校验 `Field(0) == 0x56504450 && Field(4) == 5`，不匹配直接以退出码 3 结束**——协议演进时不猜测字段语义，宁可不启动。然后进入 `WaitForMultipleObjects({shutdown, request})` 循环。

**共享内存布局**（由 `kMapBytes=4268288`、`kPathOffset=256`、`kPathChars=32768`、`kCacheRootOffset=65792`、`kCacheRootChars=4096`、`kPixelOffset=73984`、`kMaxPixelBytes=4 MiB` 决定，AHK 侧常量与之同名）：

| 偏移 | 类型 | 字段 | 写入方 |
| --- | --- | --- | --- |
| 0 | u32 | Magic `0x56504450` | AHK |
| 4 | u32 | 协议版本 = 5 | AHK |
| 8 | u32 | command（1=Preview / 2=Cache / 3=GenerateDocument） | AHK |
| 12 | u32 | status（2 Ready / 3 NoContent / 4 NeedsGeneration / 5 ResourceLimit / 6 PasswordProtected / 7 Inaccessible / 8 CorruptOrUnsupported） | Helper |
| 16 / 24 / 32 / 40 | i64 | generation / listInstance / panelSession / requestId | AHK |
| 48 / 52 | u32 | maxWidth / maxHeight | AHK |
| 56 / 60 / 64 / 68 | u32 | maxFileMB / maxEdge / maxPixelsMP / maxExpandedMB | AHK |
| 72 / 76 / 80 / 84 / 88 / 92 | u32 | cacheEnabled / MaxMB / MaxItems / ItemMaxKB / UnreferencedDays / TargetEdge | AHK |
| 96 / 100 | u32 | dpi / themeVersion | AHK |
| 128 / 132 / 136 / 140 | u32 | width / height / stride / sourceKind | **Helper** |
| 256 | UTF-16 × 32768 | 文件路径 | AHK |
| 65792 | UTF-16 × 4096 | 缓存根目录 | AHK |
| 73984 | ≤4 MiB | 预乘 BGRA 像素（顶朝下） | **Helper** |

**发布与取回**：Helper 先 `memcpy` 像素 → 写 width/height/stride/sourceKind → `MemoryBarrier()` → **最后**写 `status = 2` → `SetEvent(responseEvent)`。AHK 侧 `PreviewPollResponse` 以 **15 ms 轮询**并 `WaitForSingleObject(responseEvent, 0)`，命中后 `RtlMoveMemory` 拷出像素。**位图回传走共享内存**——不是文件、不是窗口句柄。

**四个值得记录的健壮性设计**：

1. **双侧不信任对方数据**：Helper 侧 `SnapshotRequest` 对**所有数值字段 `std::clamp` 到允许区间**；AHK 侧 `PreviewPixelLayoutIsValid` 以**先除后乘**的方式校验 `stride ≥ width*4` 且 `height ≤ min(4MiB, kMapBytes - kPixelOffset) / stride`。
2. **发布前复核身份**：Helper 在写像素前用 `SameRequest()` 复核 generation/listInstance/panelSession/requestId 是否仍与快照一致，**不一致就直接不发布**——这就是"快速切换只保留最新请求"的实现方式，避免过期结果覆盖新画面。
3. **映射访问与关闭互斥**：AHK 用 `Critical("On")` 包住映射访问并维护显式引用计数 `PreviewMapAccessDepth`；期间若需关闭 Helper 则**延后**（`PreviewHelperClosePending`），最后一个读者离开后再关。注释解释了原因：低编号 `OnMessage` 回调可能在 Critical 段内重入定时器。
4. **崩溃隔离**：`SetInformationJobObject(JobObjectExtendedLimitInformation)`，`LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY | KILL_ON_JOB_CLOSE`，**进程内存硬上限 512 MiB**；配合 3 s / 12 s 硬超时杀进程、60 秒内重启超 3 次即**会话级永久停用预览**、以及分级负缓存（详见 §5.4.9）。

#### 5.3.2 传输 Helper：文件 + 命令行的"批处理作业"模型

`CreateExternalTransfer` 在 `%TEMP%\PopDrop-Transfers-<pid>\<batchId>\` 下建立一批文件，用一个批目录表达一个"作业"：

| 文件 | 方向 | 作用 |
| --- | --- | --- |
| `data-object.bin` | 主 → helper | `CoMarshalInterface` 的结果（**限 16 MiB**） |
| `request.ini` | 主 → helper | `Protocol=2`、`BatchId`、`Adapter`、`TargetPath`、`TargetSourceId`、`TargetName`、`MarshalPath`、`StatePath`、`CancelPath`、`ReadyPath`、`RetryPath`、`AllowHttp`、`MaxConcurrent`、`ShowNotifications` |
| `ready` | helper → 主 | 握手标记，内容 `"READY"`；主程序轮询该文件（**1200 ms 上限**）确认 helper 已就绪 |
| `state.ini` | helper → 主 | 批量与逐项进度（`[Batch]` + `[Item:001]…`），helper 侧以 `.writing` → `MoveFileExW(MOVEFILE_REPLACE_EXISTING \| MOVEFILE_WRITE_THROUGH)` **原子写**；主程序以 250 ms 定时器读取 |
| `cancel` | 主 → helper | 取消标记，helper 轮询 `IsCancelled` |
| `url-retry.dpapi` | 双向 | DPAPI 保护的 URL 重试凭据 |

命令行只有两个参数：`PopDropTransfer.exe --request "<request.ini 路径>"`。主程序另通过 `state.ini` 的 `HelperVersion` 做版本校验，**不匹配时明确报错而非继续执行旧逻辑**。

**为什么这些事 AHK 主进程做不了**（这是引入原生 helper 的完整理由）：

| 能力 | AHK 侧的限制 |
| --- | --- |
| `CoUnmarshalInterface` 跨进程接管 `IDataObject` | AHK 无法把 live COM 接口指针跨进程传递，必须由原生进程 marshal/unmarshal |
| `GetData(CF_HDROP)` **唯一一次**调用 | Chromium 把每次 `GetData` 当一次新的延迟下载请求；主进程读一次 + helper 读一次 = 两次下载 |
| `IDataObjectAsyncCapability::EndOperation` | 需要 `SetAsyncMode(TRUE)` + `StartOperation`/`EndOperation` 正确配对，否则来源程序的数据生命周期不收敛 |
| `FILEDESCRIPTORW`/`FILECONTENTS`、`PNG`/`DIBV5` → WIC、`WinHTTP` 下载 | 需要 `TYMED_ISTREAM` 分块流拷贝、`IWIC`/`CreateStreamOnHGlobal`、WinHTTP 与 DPAPI |
| 分块写入 + 原子落盘 + 隐藏 `.popdrop-part` | 需要 `MoveFileExW` + `FlushFileBuffers` + `FILE_ATTRIBUTE_HIDDEN\|TEMPORARY` 的低层控制 |
| 5 秒有界图片收敛 / PE 级崩溃隔离 | 与 GUI 线程解耦，崩溃不拖死面板 |

用到的关键接口：`CreateStreamOnHGlobal`、`CoMarshalInterface`/`CoUnmarshalInterface`/`CoReleaseMarshalData`、`IDataObject::GetData`、`IStream::Read`、`DragQueryFileW`、`MoveFileExW`、**`IAttachmentExecute`**（为网络来源文件打 `Zone.Identifier` 标记）、`IWIC`/`SHCreateItemFromParsingName`、`WinHTTP`、**`CryptProtectData`**（URL 重试凭据的 DPAPI 保护）、以及**全局命名信号量**做并发闸门（全局最多 3 个后台任务、同一主机最多 2 个）。

### 5.4 文件预览子系统

预览子系统由**同一份常驻原生 Helper**（`PopDropPreview.exe --shared`）承担全部"重活"，AHK 侧只做命中测试、状态机、有界内存拷贝与 GDI 呈现（`Preview.ahk`）。三条路径共用该 Helper 与同一套共享内存协议：

| 路径 | AHK 侧 | 触发 | 备注 |
| --- | --- | --- | --- |
| 主悬浮预览 | `Preview.ahk`（2211 行） | 鼠标/键盘悬停 | 会话命名对象 `Local\PopDropPreview-<tick><pid>` |
| ListView 缩略图增强 | `modules/ScanCache.ahk` | 面板可见时逐行排队 | 独立会话 `Local\PopDropThumbnail-<tick><pid><rand>`，**不占用悬浮预览会话** |
| 外部空格键预览 | `QuickPreview.ahk`（777 行） | Space 热键 | 不渲染，转发给 Seer / QuickLook |

#### 5.4.1 支持范围与渲染器分配

`Preview.ahk:88-109` 的 `PreviewDocumentExtensions()` 是 AHK 侧唯一权威的扩展名表，**63 项** `Map(扩展名 → kind)`：

| kind | 数量 | 扩展名 | 渲染方式 |
| --- | --- | --- | --- |
| `markdown` | 2 | `md` `markdown` | 行级启发式 + GDI 语义化文本页 |
| `text` | 5 | `txt` `log` `ini` `cfg` `conf` | GDI 静态文本页 |
| `code` | 52 | `json` `yaml` `xml` `ahk` `c/cpp/h/cs/java/go/rs/py/js/ts/html/css/sql/ps1/bat/sh/toml/vue/rb/php/lua/r/dart/ex` 等 | GDI 静态文本页（Consolas） |
| `table` | 2 | `csv` `tsv` | GDI 静态表格页 30×12 |
| `pdf` | 1 | `pdf` | PDFium → WinRT → Shell 缩略图（三重回退） |
| `docx` | 1 | `docx` | Windows IFilter 语义文本 → Shell 缩略图 |

原生侧 `RendererId()`（`PopDropPreview.cpp:443-451`）返回对应渲染器标识（`markdown-semantic` / `delimited-table` / `text-code` / `pdf-pdfium-or-winrt-or-shell-first-page` / `docx-semantic-or-shell` / `image-wic-shell`），该标识**参与缓存键**，因此同一文件更换渲染器会自动失效旧缓存。

图片（22 项扩展名，仅用于隐藏期缓存排队判定）走 **WIC 首帧缩放解码**（`DecodeWicFile`），失败/超限才回退 Shell 缩略图。视频、Office（XLSX 明确排除）、字体、压缩包、无扩展名文件**没有专门渲染器**，走通用取图顺序，最终可能落到"回退卡"（文件图标 + 文件名 + 大小 + 修改时间）。

三级开关逐层收窄：`PreviewEnabled`（文件预览）→ `PreviewDocumentEnabled`（文档预览）→ `PreviewPdfEnabled`（PDF 预览，**默认关闭**）。

#### 5.4.2 图片解码管线（纯 WIC，不用 GDI+）

`DecodeWicFile`（`PopDropPreview.cpp:587-732`）的处理顺序值得逐条记录：

1. `CoCreateInstance(CLSID_WICImagingFactory)` → `CreateDecoderFromFilename(..., WICDecodeMetadataCacheOnDemand)` → **`GetFrame(0)`（动图只取首帧）**；
2. **边界拒绝**：`width/height > maxEdge` 或 `width*height > maxPixelsMP*1e6` 直接拒绝；所有乘法走 `SafeMultiply` 防溢出；
3. **EXIF 方向 1–8** → `WICBitmapTransformOptions`（查询 `/app1/ifd/{ushort=274}`，失败回退 `/ifd/{ushort=274}`）；
4. **优先编解码器原生缩放**：`IWICBitmapSourceTransform::{DoesSupportTransform, GetClosestSize, GetClosestPixelFormat, CopyPixels}`，要求目标格式为 `GUID_WICPixelFormat32bppPBGRA`——**避免大图展开成完整 RGBA 中间态**；有内嵌 ICC 色彩上下文时跳过该捷径（避免色彩被绕过）；
5. **回退链**（仅当预计展开内存 ≤ `maxExpandedMB` 时才允许）：`IWICBitmapScaler(Fant)` → `IWICBitmapFlipRotator` → `IWICColorTransform`（内嵌 profile → sRGB，在缩放/旋转**之后**做以保持中间态有界）→ `IWICFormatConverter` → `32bppPBGRA`。

**Alpha 判定是逐像素扫描 alpha 通道**，不依赖元数据。

AHK 侧最终合成（`PreviewBuildCanvas`）：把 BGRA 逐行 `RtlMoveMemory` 进 DIB section（处理 stride → 紧排），背景先铺 **2×2 棋盘格 pattern brush**（替换了原先"数千次 FillRect"的做法），再用 `msimg32.dll!AlphaBlend` 带 `AC_SRC_ALPHA` 合成，最后画边框与信息栏。**画布原子交换**：构造完整新位图后才替换全局 DC/bitmap，`WM_PAINT` 只会看到完整旧帧或完整新帧。

缩放策略由 `sourceKind` 决定：`scaleLimit = (sourceKind == 2 || sourceKind >= 4) ? 1000.0 : 1.0` —— 即 **Shell 回退图（2）与文档渲染图（4/5/6）允许等比放大，WIC 原图（3）与自有图片缓存（1）只缩不放**。这也是"Shell 缩略图太小"问题的修复点。

#### 5.4.3 文本 / Markdown / CSV 渲染

| 环节 | 实现 |
| --- | --- |
| 有界读取 | `ReadBoundedPrefix(path, kTextReadBudget = 512 KiB)`，`FILE_FLAG_SEQUENTIAL_SCAN` |
| 编码识别 | 先做**二进制嗅探**（NUL 字节数 > max(8, size/50) 且无 UTF-16 BOM → 拒绝）；BOM 分支 `FF FE`(UTF-16LE) / `FE FF`(UTF-16BE) / `EF BB BF`(UTF-8)；否则 `MultiByteToWideChar(CP_UTF8, MB_ERR_INVALID_CHARS)`，失败再回退 `CP_ACP` |
| 行切分 | 最多 **180 行**，单行截断到 **4096 字符**并追加 `" …"`，整体未读完时末行追加 `"  ⋯"` |
| Markdown | **不是 DOM 解析器，是行级启发式**：识别 `#` 标题、`- [x]` 任务框（→`☑`/`☐`）、`- * +` 列表（→`•`）、`>` 引用（→`│`）、`**`/`__` 粗体、`*`/`_` 斜体、4 空格缩进与 ``` / ~~~ 代码块；用**哨兵字符 `\x1`(标题) `\x2`(粗) `\x3`(斜) `\x4`(代码)** 前缀标记行，渲染时剥除并选字体。原始 HTML/JS/Mermaid/链接**全部作为纯文本**，不执行、不加载网络资源 |
| CSV/TSV | 手写状态机处理 `""` 转义与引号内换行；最多 **30 行 × 12 列**，单元格超 36 字符截断，列间用 `"  │  "` 分隔；**不计算公式** |
| 绘制 | Helper 内建 `CreateDIBSection` 32bpp 顶朝下位图，米白纸底 `RGB(250,250,248)` + 42px 页眉条；`CreateFontW` 按 DPI `MulDiv(14, dpi, 96)`（clamp 13–28）构造 title/body/heading/bold/italic/code 六个字体（Markdown/CSV 用 `Segoe UI`，代码用 `Consolas`），逐行 `DrawTextW(DT_SINGLELINE|DT_TOP|DT_END_ELLIPSIS|DT_NOPREFIX)` |

**关于换行的关键修复**：覆盖窗口下 `DrawTextW` 的多行测量与推进不可靠（出现错位），最终**不再依赖多行测量**——改为 `WrapVisualLines` 用 `GetTextExtentPoint32W` 做**二分查找**求最大可容纳宽度，优先在空格断行，每条逻辑行最多 **3 条视觉行**，末行加 `…`，再逐条以单行模式绘制并推进 y。

#### 5.4.4 PDF 预览：为什么需要原生组件

**动机**：Shell / WinRT 路径不稳定（可能无 Shell 处理器、无 Windows PDF Runtime），且 Shell 缩略图往往是低分辨率图标级产物；PDFium 提供确定性的首页渲染。

**三重回退链**（`AcquirePreview`）：

1. `DecodeCache()` —— 自有缓存命中；
2. `DecodeShellCache()` —— **`SIIGBF_THUMBNAILONLY | SIIGBF_INCACHEONLY`** 的 Shell 缩略图（**只接受系统已有缩略图，不现场触发 Shell 扩展生成**）；
3. `DecodeShellThumbnail(cacheOnly=false)` —— 允许现场生成并写缓存；
4. 都失败 → 返回 `kStatusNeedsGeneration(4)`，AHK 收到后**升级为文档生成请求**（`command 3`）→ Helper `WriteCache()` → `RenderPdfFirstPage()`。

**PDFium 动态加载**（`PdfiumApi::Load()`）——注意其"先校验导出再使用"的思路，与本项目 OCR 侧的 `onnxruntime.dll` 探测问题同源：

```cpp
// DLL 路径 = Helper 自身所在目录
dll = <Helper exe 所在目录> / L"pdfium.dll";
module_ = LoadLibraryExW(dll, nullptr,
            LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
// 随后 GetProcAddress 解析 13 个导出，任一缺失立即失败：
// FPDF_InitLibrary / DestroyLibrary / LoadCustomDocument / GetLastError / GetPageCount
// FPDF_LoadPage / GetPageWidthF / GetPageHeightF / Bitmap_CreateEx / Bitmap_FillRect
// FPDF_RenderPageBitmap / Bitmap_Destroy / ClosePage / CloseDocument
```

**按需随机读取 + 读取预算**：用 `FPDF_LoadCustomDocument` 配合 `FPDF_FILEACCESS` 回调（`SetFilePointerEx(FILE_BEGIN)` + `ReadFile`）实现流式读取，**累计超过 `kPdfReadBudget = 64 MiB` 即判定资源超限并安全失败**——既不整文件载入内存，也防止恶意/损坏 PDF 无限读取。

**渲染**：只渲染第 0 页（`loadPage(document, 0)`）——**没有分页、没有滚动、没有缩放 UI**，所谓"缩放"只是把首页等比缩小到请求尺寸（AHK 侧 clamp 到 1024）。位图**直接落在即将回传的像素缓冲上**：

```cpp
image.pixels.assign(pixelBytes, 255);
bitmap = pdfium.createBitmap(targetWidth, targetHeight, 4, image.pixels.data(), stride); // BGRA
pdfium.fillBitmap(bitmap, 0, 0, targetWidth, targetHeight, 0xFFFFFFFF);                  // 白底
constexpr int renderFlags = 0x02 /* FPDF_LCD_TEXT */ | 0x200 /* limited image cache */;
pdfium.renderPageBitmap(bitmap, page, 0, 0, targetWidth, targetHeight, 0, renderFlags);
```

渲染后强制 `alpha = 255`、`hasAlpha = false`。**错误分类**直接映射到用户可见文案：`FPDF_GetLastError() == 4` → 密码保护；`== 2` → 不可访问；读取超预算 → 资源超限；其余 → 损坏/不支持。

**WinRT 回退**：`CreateRandomAccessStreamOnFile()` → `Windows.Data.Pdf.PdfDocument::LoadFromStreamAsync()` → `GetPage(0)` → `PdfPageRenderOptions{DestinationWidth/Height, BackgroundColor=White}` → `PreparePageAsync()` → `RenderToStreamAsync()`（**编码流上限 16 MiB**）→ `CreateStreamOverRandomAccessStream()` 得到 `IStream` → `DecodeWicStream()` 解码为 BGRA。优先 PDFium，并**在 PDFium 报"密码/资源/不可访问"时保留其失败分类**，不被 WinRT 覆盖。

**为什么有 x86/x64 两份 dll**：Helper 是 32/64 位两个独立 exe，AHK 按 `A_PtrSize` 选择；进程内 `LoadLibrary` 只能加载**同位数**的 DLL，因此两个目录各需一份。

#### 5.4.5 DOCX：Windows IFilter（不启动 Word）

```cpp
LoadIFilter(path, nullptr, (void**)&filter);   // Windows Search IFilter
filter->Init(IFILTER_INIT_CANON_PARAGRAPHS | IFILTER_INIT_HARD_LINE_BREAKS
           | IFILTER_INIT_APPLY_INDEX_ATTRIBUTES, 0, nullptr, &flags);
while (chunks++ < 512 && text.size() < 128 * 1024) {
    GetChunk -> 仅取 CHUNK_TEXT -> 循环 GetText(2048 字符缓冲) -> 追加 "\n"
}
```

上限 **512 chunk / 128K 字符**，提取结果交给同一套 GDI 文本渲染器（标题用文件名）。**绝不启动 Word / Office COM / 宏 / OLE / ActiveX**。代价是复杂版式、嵌入图片、分页、页眉页脚会丢失。

**密码/加密嗅探**（在解析前拦截）：PDF 检查前 1 MiB 内是否含 `/Encrypt`；DOCX 检查是否以 **OLE 复合文件头 `D0 CF 11 E0 A1 B1 1A E1`** 开头（加密的 docx 会变成复合文件）。

#### 5.4.6 预览缓存

| 环节 | 实现 |
| --- | --- |
| 缓存键 | **稳定文件身份**（卷序列号 + FileId，取不到时回退规范化小写路径）+ 大小 + 最后修改时间 + `RendererId` + `kPreviewSpecVersion(4)` + `cacheTargetEdge` + `dpi` + `themeVersion`，经 `BCrypt` SHA-256 → 64 位十六进制文件名 |
| 目录安全 | 目录必须名为 `preview-cache-v1` 且**非重解析点** |
| 写入 | 先写 `<key>.png` / `<key>.jpg`（命名 `.writing`）→ PNG 真彩压缩 / JPEG 质量 **0.82** → 体量 ≤ `CacheItemMaxKB`（默认 2048 KB）→ `MoveFileEx(MOVEFILE_REPLACE_EXISTING \| MOVEFILE_WRITE_THROUGH)` **原子发布** |
| 超限降级 | 按 **1024 → 768 → 512** 逐级降边重试 |
| 命中即用 | 读取时写回 `ftLastAccessTime` 以支撑 LRU；损坏的"键有效"缓存直接删除 |
| 清理 | 只接受 64 位十六进制名 + `.png/.jpg` 后缀；拒绝目录与重解析点；按期未访问天数（默认 7）与 `CacheMaxMB`(256) / `CacheMaxItems`(1000) 做 LRU 淘汰；清理 24 小时以上的 `.writing`/`.part` |

**一个值得引以为戒的真实 bug**：`cache-status.ini` 长期显示"调度 17 项、成功 0"。根因是 `IWICStream::InitializeFromFilename` 不暴露共享标志，`Commit()` 后仍持有独占句柄，紧接着重开同一文件做 `FlushFileBuffers` **必然共享冲突**，随后代码删除了已编码结果。修复方式是**刷新前释放完整 COM 链**（converter / properties / frame / encoder / stream / bitmap 逐个 `reset()`）再 `CreateFileW(FILE_SHARE_READ)` + `FlushFileBuffers`，并把协议升级到 4、补静态顺序检查防回归。

#### 5.4.7 悬浮预览的状态机与防抖

| 项 | 内容 |
| --- | --- |
| 窗口形态 | `Gui("-Caption +ToolWindow +Owner<面板> +E0x08000000")`，即 **`WS_EX_TOOLWINDOW`（不进 Alt+Tab）+ `WS_EX_NOACTIVATE`（不抢焦点）**，Owner 到面板；绘制走 `WM_PAINT → BitBlt`；z-order 由窗口模式决定 `HWND_TOPMOST(-1)` / `HWND_NOTOPMOST(-2)` |
| 时延 | 首次悬浮 **350 ms**（`HoverDelayMs`）／已显示时切换 **120 ms**（`SwitchDelayMs`）／键盘导航 **250 ms**（`KeyboardDelayMs`）／离开宽限 **140 ms**；已有内容时旧帧最多再保留 **500 ms**（`PreviousPreviewHoldMs`） |
| 尺寸定位 | 宽度 `PreviewWidthDip`(400 DIP) × DPI，上限取左/右侧可用工作区宽度、下限 180 DIP；Auto 模式**优先左侧**（文件列表侧），侧别锁存在 `PreviewSession.Side`，面板移动/缩放结束后重算 |
| 状态机 | `Hidden → Armed → Loading → Visible / Error`，外加 `Suppressed` |
| 身份校验 | **三重身份 `Generation / ListInstance / PanelSession` + `RequestId`**，任一不匹配即丢弃结果 |
| 抑制来源 | 拖拽、框选、滚动、右键菜单、工作区/视图切换、面板移动缩放、设置页、显示菜单均会抑制悬浮并关闭预览，结束后按当前屏幕坐标自动恢复 |
| 键盘候选 | 方向键 / Home / End / Page Up / Page Down 建立候选；`Enter` / `Esc` / 列表失焦 / 隐藏面板立即关闭；鼠标静止在 A 而键盘移到 B 时显示 B，只有鼠标再次真实移动才切回鼠标候选 |
| 状态卡节奏 | **120 ms** → "首次预览正在生成…"；**5000 ms** → "预览生成时间较长…"；**12000 ms** 硬超时 → "暂时无法生成预览"。动画为 350 ms 定时器在标题后追加 `""/" ·"/" ··"/" ···"`。状态卡与最终内容**共用同一外框矩形**，保证"外框不动" |

#### 5.4.8 与外部查看器（Seer / QuickLook）的协同

| 项 | 内容 |
| --- | --- |
| 能力探测 | Seer：`SeerIntegrationEnabled=1` **且** `FindWindowW("SeerWindowClass")` 非 0；QuickLook：路径必须为**绝对路径**、文件存在且非目录、文件名必须是 `quicklook.exe`、版本资源 `ProductName` 含 `quicklook`。Store 版不推断 CLI 能力 |
| Space 接管 | `HotIf(IsPanelQuickPreviewAvailable)` + `Hotkey("Space", ...)`；能力检测失败则**不接管**。`HotIf` 中必须排除"文本块搜索框聚焦"，否则 Space 会被吞掉导致无法输入空格 |
| Seer 协议 | `COPYDATASTRUCT{ uptr command; uint size; ptr payload }` + `SendMessageTimeoutW(WM_COPYDATA, ..., SMTO_ABORTIFHUNG, 250ms)`。命令号：`4000` 由 Seer 索要路径 / `4001` PopDrop 回**本会话已锁定的路径** / `5000` 请求预览某路径 / `5004` 查询可见性 / `5005` 关闭 |
| 调用频率 | Seer 文档要求 5000 命令最小间隔 200 ms，实现用 **220 ms** 并合并快速切换只发最新路径 |
| QuickLook 调用 | `ShellLaunchExecutableWithArgs(QuickLookPath, [path], "")`，关闭用 `WinClose` 找最大可见窗口。**完全不模拟按键** |
| 窗口层级 | 会话开始时以 `SetWindowPos(HWND_NOTOPMOST, SWP_NOACTIVATE\|NOSIZE\|NOMOVE)` **让出面板 topmost**；期间 250 ms 健康检查把查看器（含其弹窗/对话框）置于面板之上——但**仅当它尚未在上方时才调用**（避免 QuickLook 工具栏菜单消失）；会话结束恢复查看器进入前的置顶属性，**不修改、不保存 PopDrop 的置顶设置** |
| 焦点归还 | 查看器取得前台焦点，关闭后归还 PopDrop 原列表控件；`QuickViewActive` 仅用于暂停 temporary 模式的自动隐藏 |

#### 5.4.9 隔离、预算与熔断

| 机制 | 参数 |
| --- | --- |
| Job Object | `SetInformationJobObject(JobObjectExtendedLimitInformation)`，`LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY \| KILL_ON_JOB_CLOSE`，**进程内存上限 512 MiB** |
| 硬超时 | 图片请求 **3000 ms**、文档请求 **12000 ms** 未响应即 `ProcessClose` 杀进程并按类型降级 |
| 重启熔断 | 60 秒窗口内重启超过 **3 次** → `PreviewSessionDisabled = true`，**本次会话内永久停用预览** |
| 传输重试 | 最多 4 次、每次间隔 40 ms；彻底失败才写 20 秒负缓存 |
| 负缓存分级 | 资源超限/密码保护 → **Permanent**（文件修改前不重试）；不可访问 → 30 s；硬超时 → 600 s；其余 → 60 s。键带 `size\|writeTime` 戳，文件变化即自动失效 |
| 优先级 | Helper 常驻 `BELOW_NORMAL_PRIORITY_CLASS`；收到缓存/文档生成命令时降到 `IDLE_PRIORITY_CLASS`，处理完恢复 |
| 并发 | **同一 Helper 串行处理所有请求**，同一路径不会并行解析 |
| 云占位文件保护 | 检查 `FILE_ATTRIBUTE_OFFLINE \| FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS \| FILE_ATTRIBUTE_RECALL_ON_OPEN`，命中即拒绝——**"Never hydrate an online-only placeholder"**，避免悬浮触发 OneDrive 按需下载 |
| 后台缓存有界化 | 只有**本次实际悬浮且来源为未缓存原图/Shell** 的项目才入队；每次隐藏会话**成功上限 50 项、尝试上限 100 项**，失败不占成功额度 |
| 可观测性 | `cache\preview-cache-v1\cache-status.ini` 记录 `Stage / HoverQueueRemaining / VisibleQueueRemaining / Attempted / Succeeded / Failed / LastPath`——正是定位上述缓存 bug 的证据来源 |

#### 5.4.10 验收性能目标与已知限制

- 性能目标（P95）：**自有缓存 80 ms / Shell 缓存 150 ms / 常见原图 250 ms / UI 单次 8 ms**。
- 已知限制（项目自述）：HEIF/AVIF/WebP/RAW 等**依赖系统安装的 WIC 编解码器**；PDF/视频/Office 等非图片在悬浮路径**只使用 Windows 已有的真实缩略图**（`INCACHEONLY`），仅 ListView 后台路径允许现场生成；Alpha 缓存用 WIC 真彩压缩 PNG，**没有内建调色板量化**，超 2 MiB 逐级降到 512px，仍超限则不落盘（但即时预览仍可显示）。
- `dev_doc` 中的测试报告明确列出了**未在 Windows 实机验证**的部分：x86/x64 原生编译与 AHK 启动解析、PDFium/WinRT 首页与 DOCX IFilter 的**真实视觉内容**、100/150/200% DPI 与负坐标多屏、加密/损坏/超大/NAS/云占位的端到端时间与内存、Seer/QuickLook 的真实打开-更新-关闭-崩溃恢复。

### 5.5 拖放、文件操作与外部集成

#### 5.5.1 统一的 COM 互操作手法：手写 vtable

PopDrop 全部互操作层都是**手工构造 COM vtable**，这是 AHK 里使用 COM 的通用做法：

```ahk
; 用 CallbackCreate(..., "Fast", N) 生成函数指针数组，NumPut 进一段 Buffer
; 对象首 (A_PtrSize) 字节存 vtable 指针，紧接 4 字节存手工引用计数
```

全程序在入口依次初始化：`InitDropSource() → InitDropTarget() → InitFileOperationProgressSink() → InitExternalDrop() → InitCudaTextIntegration()`。

结构体偏移**全部按 `A_PtrSize` 在运行时选择**（如 `FORMATETC` 的 `dwAspect@16/8`、`lindex@20/12`、`tymed@24/16`；`STGMEDIUM` 的 union 偏移 `8/4`、`pUnkForRelease` 偏移 `16/8`），这是支撑 x86/x64 双架构的统一手法。

#### 5.5.2 拖出（PopDrop → 其他软件）

**两条数据对象路径**：

- **单文件：直接借用 Shell 自己的 `IDataObject`** —— `SHParseDisplayName` 取 PIDL → `SHBindToParent` 取父 `IShellFolder` 与子 PIDL → `IShellFolder::GetUIObjectOf` 请求 `IID_IDataObject` → `DoDragDrop(obj, src, 0x7 /* COPY|MOVE|LINK */, &effect)`。注释特别说明**不用 `ILCloneFull`**，因为它是 SDK 宏而非可靠导出函数。
- **多文件 / 文本：自建最小 `IDataObject`** —— 自定义 12 项 vtable 严格对应 `IDataObject`。对象 backing `Buffer` 保存在全局寄存器中，**必须活到目标程序结束异步传输为止**，引用计数归零才 `Delete`。内部拖拽**始终走自建 CF_HDROP 对象**，因为"每次内部拖拽都必须携带私有标记"。

| 场景 | 格式 | 说明 |
| --- | --- | --- |
| 文件 | `CF_HDROP`(15) + `TYMED_HGLOBAL` | 手工构造 `DROPFILES`（`pFiles=20`、`fWide=1`）+ UTF-16 路径列表，`GMEM_MOVEABLE\|GMEM_ZEROINIT` 保证双 NUL 结尾；写完用 `DragQueryFileW(..., 0xFFFFFFFF, ...)` **回读校验项数**，不一致就 `GlobalFree` 并返回失败 |
| 文本 | `CF_UNICODETEXT`(13) + `CF_TEXT`(1) | 同时提供两种，兼容只认 ANSI 的目标 |
| 内部拖拽标记 | `RegisterClipboardFormatW("PopDrop.InternalDrag.v1")` | 载荷是该次拖拽的 Token |

**一个与常见做法不同的决策：不使用 `CFSTR_PREFERREDDROPEFFECT`**。全仓库检索无该格式——PopDrop 用私有格式 `PopDrop.InternalDrag.v1` 替代，且拖入侧的内部拖拽判定是**双重**的：既要存在本进程 live 的 `DoDragDrop` 上下文，又要该 `IDataObject` 支持该私有格式。注释明确这样可以防止 Explorer 的 Shell 数据对象被误判为 PopDrop 内部拖拽（外部程序无法同时满足两者）。

**`IDropSource`（5 项 vtable）**：

- `QueryContinueDrag`：Esc → `DRAGDROP_S_CANCEL`；左键松开（`MK_LBUTTON` 位消失）→ `DRAGDROP_S_DROP`；否则 `S_OK`。
- `GiveFeedback`：**恒定返回 `DRAGDROP_S_USEDEFAULTCURSORS`** —— 即 **PopDrop 不提供自定义拖拽图像**，一律用系统默认光标 + 目标程序的拖拽图。界面上的"投放高亮"不是 OLE 光标，而是自绘的 ListView 分组高亮。

**效果语义**：所有 `DoDragDrop` 的 `pdwOKEffect` 只作**可选效果掩码**，实际效果由目标程序决定；文本拖拽普通情况只允许 `COPY`，仅"全部是 PopDrop 收件箱草稿"时才允许 `COPY|MOVE`。**PopDrop 在拖出返回后不删除任何源文件**——返回值在所有调用点都被丢弃，移动语义完全交给接收方（资源管理器按 `CF_HDROP` 自行完成）。

#### 5.5.3 拖入（其他软件 → PopDrop）

**注册**：

- **递归注册所有子 HWND**——Windows 把拖拽路由给指针下**最深**的已注册窗口，只注册顶层 Gui 会漏掉 ListView 和工具栏。
- **Smart 覆盖层除外**，且对该覆盖层返回 `HTTRANSPARENT(-1)`。理由很具体：把覆盖层注册成 OLE 目标会让"悬停中途显示覆盖层"替换掉原生目标 HWND，产生 DragLeave/DragEnter **抖动循环**。
- `RegisterDragDrop` 失败时区分 `0x80040101`（已被别的 OLE 目标注册）并记录到错误表。
- x64/x86 各有两套回调：x64 上 `POINTL`（8 字节）整体打进一个寄存器，需拆分取值；x86 上分两个参数，需处理负坐标的有符号性。

**四个防抖/防重入设计**（这些是拖放交互稳定性的关键）：

| 问题 | 解法 |
| --- | --- |
| 同一个 `IDataObject` 在父子 HWND 间移动导致重复读 HDROP | 重复进入时复用逻辑 session |
| 拖拽期间切换工作区导致落点错乱 | `DragEnter` 时把**当前工作区 ID/名称/类型/来源列表/来源默认值全部快照进 session** |
| 子 HWND 切换产生成对 Leave/Enter 导致闪断 | `DragLeave` **不立即清理**，改为 `SetTimer(FinalizeDeferredDropLeave, -50)` 延迟 50 ms，并用自增 token 取消过期清理 |
| Drop 回调存盘期间重入的 DragLeave 清掉最终状态 | 置"提交护栏" `IncomingDropGestureActive`；且 **Drop 内先把 `ActiveDropSession := 0` 再调用 Shell/UI** |

**格式适配优先级**：`HDrop > Shell IDList > VirtualFiles(FileDescriptorW+FileContents) > Png > DibV5 > Dib > Url > Text > Unsupported`。注册的剪贴板格式包括 `FileGroupDescriptorW`、`FileContents`、`Shell IDList Array`、`PNG`、`UniformResourceLocatorW`、`UniformResourceLocator`、`text/uri-list`，外加硬编码的标准格式 `CF_HDROP`/`CF_DIBV5`/`CF_DIB`/`CF_UNICODETEXT`/`CF_TEXT`。

**延迟渲染（Chromium）的三重防护** —— 这是外部拖放正确性的核心：

1. `DataObjectAsyncMode` 查询 `IIDataObjectAsyncCapability::GetAsyncMode`；
2. `CanPreloadHDropForFolderFeedback` **只在**"内部拖拽 / 有 ShellIDList / 未声明 async / 无 URL / 无虚拟文件 / 无图片载荷"全满足时才允许悬停预读；
3. `HDropShouldUseDirectAsyncTakeover`：外部 async HDROP 投到 Files 时，**主进程完全不读 `CF_HDROP`**，把 marshaling 后的数据对象整个交给 helper 执行唯一一次 `GetData`。

**落点解析**（屏幕点 → 目标描述符）：

| target.Type | 落点行为 |
| --- | --- |
| `Files` / `TextSource` | 复制/移动到该来源文件夹（走 `IFileOperation`） |
| `Pinned` / `TextPinned` | **只写 config.ini 固定项**，不移动文件；effect 恒为 COPY |
| `Launcher` | 生成 `.lnk`；已有 `.lnk`/`.url` 走复制 |
| `AddSource` | 把文件夹写进 config.ini 成为新来源（仅当载荷全部是真实文件夹时可用；设置窗口有未保存草稿时禁用） |

**外部内容不能直接落进固定项**：虚拟或网络内容必须先保存到普通文件夹。

#### 5.5.4 文件操作：`IFileOperation`

统一管线 `PerformShellFileOperation` 承载 copy / move / rename / delete 四类，vtable 调用序号与 `IFileOperation` 顺序严格对应：

| ComCall | 方法 |
| --- | --- |
| 3 / 4 | `Advise(sink, &cookie)` / `Unadvise(cookie)` |
| 5 | `SetOperationFlags(flags)` |
| 9 | `SetOwnerWindow(Panel.Hwnd)` |
| 12 / 14 / 16 / 18 | `RenameItem` / `MoveItem` / `CopyItem` / `DeleteItem` |
| 21 / 22 | `PerformOperations()` / `GetAnyOperationsAborted(&aborted)` |

`PerformOperations` 前后包 `BeginAutoHidePause()/EndAutoHidePause()`，因为 Shell 会在此处进入自己的模态消息循环。

**操作标志**（全部采用"把复杂情况交给 Shell 标准 UI"的策略）：

| 操作 | 标志 | 含义 |
| --- | --- | --- |
| 复制 / 移动 / 重命名 | `0x40240` | `FOF_ALLOWUNDO \| FOF_NOCONFIRMMKDIR \| FOFX_SHOWELEVATIONPROMPT` —— **冲突、占用、合并、取消一律交给 Shell**，PopDrop 不实现自己的冲突对话框 |
| 删除（回收站，默认） | `0x10 \| 0x40 \| 0x200 \| 0x40000 \| 0x80000 \| 0x20000000` | 含 `FOFX_RECYCLEONDELETE \| FOFX_ADDUNDORECORD` |
| 删除（永久，仅 Shift+Delete 且二次确认） | `0x10 \| 0x200 \| 0x40000` | **不含任何回收/撤销标志** |

注释明确："Recycling explicitly requests `FOFX_RECYCLEONDELETE` and never falls back to `FileDelete`/`DirDelete`"——这对应功能层的"回收站不可用时不会改为永久删除"。

**`IFileOperationProgressSink`**：19 项 vtable，只有 `Post*` 回调有实体逻辑，进度相关回调全部空实现（进度由 Shell 自己的 UI 承担）。其中最值得借鉴的一点：**固定项路径同步不靠推测，而靠回调返回的 `createdItem` 反查真实路径**（`IShellItem::GetDisplayName(SIGDN_FILESYSPATH)`）；rename/move 时把 `OldPath → NewPath` 写入 `state.Mappings`，Shell 未返回可验证新路径且该项被任何工作区固定时记入失败列表。这是"固定项自动跟随移动/重命名"的**唯一可信来源**，也解释了为什么功能层能承诺"移动操作包括冲突对话框造成的自动改名"。

**"来源直存认领"**：外部拖拽时若源文件父目录已是目标目录，跳过复制并在状态栏说明"来源已将 N 个项目直接保存到…，PopDrop 未重复复制"，避免浏览器在目标目录里再生成 `image (2).jpg`。

**视图恢复**：移动类操作后以"`PerformOperations` 之后源文件不存在"为**权威判据**确认移动，再恢复选择、焦点与滚动位置。

#### 5.5.5 文本发送：剪贴板 + 原窗口 `Ctrl+V`

**主流程**（不是 `SendInput` 逐字打字）：

1. `JoinTextBlocks(paths)` 拼正文；
2. 目标是终端宿主 → 走终端清洗；
3. 写剪贴板并 `ClipWait`；
4. **恢复原窗口与焦点**：`HidePanel()` → `WinActivate(target)` → `WinWaitActive 0.8s` → 恢复捕获的焦点控件；
5. **焦点校验**：用 `GetGUIThreadInfo` 取目标线程内的 focus HWND，与面板呼出瞬间捕获的 `TextBlockReturnFocus` 逐项比对；**密码框（`ES_PASSWORD`）直接拒绝**；
6. `Send("^v")` 投送。

`TextBlockReturnWindow` / `TextBlockReturnFocus` 在**面板呼出瞬间**捕获——这个"呼出即记录返回目标"的设计是"用完即走"体验的基础。

**「前置发送」（`Ctrl+Enter`）如何插到已有内容前面**：

```ahk
if (prepend) {
    MoveTextBlockCaretToStart(activeFocus)
    Send("^v")
}
```

`MoveTextBlockCaretToStart` 分两类处理：

- 原生 `Edit`/`RichEdit`：`EM_SETSEL(0x00B1)` 设选区到 0 → **`EM_GETSEL(0x00B0)` 回读校验确实为 (0,0)**，否则抛错 → `EM_SCROLLCARET(0x00B7)`。注释说明这避免了依赖应用自己的快捷键处理；
- 浏览器 / Electron 等自定义编辑器：回退 `Send("^{Home}")`。

护栏：**必须有可靠的返回焦点**，否则放弃并把正文留在剪贴板；恢复焦点后要求焦点控件与捕获值一致，位置变了就报错。

**终端特化**：宿主识别**只认顶层窗口类 + 宿主进程名，刻意不查终端内部跑的是什么**（模块头注释明确"`cmd.exe`/`powershell.exe`/`ssh` 既不查询也不作为安全信号"）。投送通道：

- `ConsoleHost` → 一次 `WM_PASTE`，`SendMessageTimeoutW` + `SMTO_ABORTIFHUNG` + 700 ms 超时；
- `WindowsTerminal` → 一次 `Shift+Insert`。注释解释了三个理由：Windows Terminal 不暴露 `WM_PASTE`；在 Claude Code 等 raw/bracketed-input TUI 里 `Ctrl+V` 系绑定可能被吞或解绑；以及**绝不补发第二次按键或右键**——因为 `SendInput` 无法证明第一次是粘贴成功还是弹出了终端自己的警告，重试会重复正文。

#### 5.5.6 CudaText 兼容桥（一个"对方不守协议"的适配案例）

**动机**：CudaText 用 Lazarus 编辑器控件自带的内部文本拖拽路径，**不稳定地提供/接受 Windows OLE 文本 `IDataObject`**。因此做了两条窄范围桥，只在 `cudatext.exe` 是源或目标时生效；其它编辑器一律以标准 OLE 为权威。

- **CudaText → PopDrop**：用 `~LButton` 全局热键驱动。**按下瞬间立刻 `CaptureCudaTextSelection()`**（备份剪贴板 → 清空 → `SendEvent("^c")` → `ClipWait(0.35)`），因为在 CudaText 内部拖拽循环完全接管前才读得到选区；随后 15 ms 定时器用 `SM_CXDRAG`/`SM_CYDRAG` 作拖拽阈值轮询，空结果做**有界重试**（最多 3~4 次、间隔 ≥120 ms）。**若 CudaText 这次真的提供了 OLE 对象，桥立即退出，绝不重复**。
- **光标劫持**（全项目唯一改系统光标的地方）：CudaText 自己的拖拽循环会持续把光标压回 `IDC_NO`，桥用 `CopyImage(LoadCursorW(IDC_HAND))` + `SetSystemCursor(..., OCR_NO)` **把系统的 `OCR_NO` 整体替换为手型**，结束时用 `SPI_SETCURSORS` 重载用户光标方案（含自定义主题）还原。
- **PopDrop → CudaText**：仅在 `DRAGDROP_S_DROP` 且 `effect == 0`（即**没有任何真实目标接受**）时兜底：备份剪贴板 → 写文本 → `WinActivate` → `Click(插入点)` → `Send("^v")` → 还原剪贴板。

#### 5.5.7 打开方式与工具动作的执行

- 默认应用：`Run(path)`；文件夹走文件管理器路由。
- **动作模板渲染**：`{item} {folder} {parent} {name} {stem} {ext} {date} {time} {datetime} {index} {count} {size}`，`{items}` 为特例——只在模板参数**整体等于** `{items}` 时展开为全部路径。
- **两种执行模式**：Batch（全部路径一次传入，单条命令行）/ PerItem（每文件一条命令，用 `WaitForSingleObject` **真正串行**；拿不到可等待的进程句柄就直接失败，**不做"假串行"**）。
- **命令行构造**：每个参数经 `QuoteWindowsArgument` 转义后拼成一条命令行，总长超过安全上限则拒绝；`SHELLEXECUTEINFOW` 手工填充（`fMask = SEE_MASK_NOCLOSEPROCESS \| SEE_MASK_FLAG_NO_UI`，字段偏移按 `A_PtrSize` 选择）。
- **系统右键菜单**是完整实现：`SHParseDisplayName` + `SHBindToParent` → `IShellFolder::GetUIObjectOf` 取 `IID_IContextMenu` → `QueryContextMenu(CMF_EXPLORE|CMF_EXTENDEDVERBS|CMF_SYNCCASCADEMENU)` → `TrackPopupMenuEx(TPM_RETURNCMD)` → 填 `CMINVOKECOMMANDINFOEX`（`lpVerb = command - 1`，即 `MAKEINTRESOURCE` 语义）→ `InvokeCommand`。

#### 5.5.8 选择窗口定位到此：一个"零 COM"的解决方案

**结论先说：整套机制没有使用 `IFileDialog` 或 `IShellBrowser`**（全仓库检索零命中）。它靠"**窗口类启发式 + 通用对话框消息 + 地址栏快捷键 + 回读验证**"实现。

这样做的原因是要同时覆盖现代 `IFileDialog`、旧式 Common File Dialog、树形 `SHBrowseForFolder`，以及 Inno Setup 自己的 VCL `TSelectFolderForm`，同时避免把普通设置对话框误判成文件选择器。

**识别**：统一要求 `GetDlgItem(hwnd, IDOK)` 存在（排除消息框与普通设置框），再分结构判断：

| 类型 | 判据 |
| --- | --- |
| 现代 `IFileDialog` | 含 `directuihwnd` / `shelldll_defview` / `duiviewwndclassname`，或 `comboboxex32` + `syslistview32` |
| 旧式 `SHBrowseForFolder` | `#32770` + 有 `systreeview32` 且**无**上述现代子类 |
| VCL `TSelectFolderForm` | 类名精确匹配 + 同时存在 `TFolderTreeView`/`SysTreeView32` 与**唯一**的路径编辑框 |

**跳转**（三条通道）：

1. **VCL 自绘树对话框** → 对结构校验过的唯一路径编辑框发 `WM_SETTEXT`，**不发 Enter、不点确定、不碰剪贴板**，随后回读校验文本；
2. **旧式 `SHBrowseForFolder`** → `BFFM_SETSELECTIONW` + `wParam=TRUE`（该对话框没有可编辑地址栏，故用文档化消息而非快捷键）；
3. **现代通用对话框** → **`Alt+D` 聚焦地址栏 → `SendText(path)` → `{Enter}`**，每步之后都重校验 `GetForegroundWindow()` 仍是该对话框，任一失焦立即放弃；首轮失败再退到 `Ctrl+L` 重试一次。

**验证是"跳转成功"的唯一权威判据**：发 `CDM_GETFOLDERPATH` 读回对话框当前目录，在 900 ms 内轮询直到路径相等——不靠假设。

**Task Link 的设置方式**：`LVM_SETGROUPINFOW` + `LVGF_TASK` + `pszTask`（偏移按 `A_PtrSize` 选择）；**清空时必须显式写 NULL 指针而不是空串**。另有一个副作用清理：部分通用控件版本在清空 `pszTask` 后仍保留已画出的 Task Link，因此切回普通上下文时走一次完整面板重建。

### 5.6 配置系统与设置界面

#### 5.6.1 配置文件的位置与格式约束

```ahk
global DataRootDir := ResolvePopDropDataRoot()   ; 正常为脚本目录
global ConfigPath  := DataRootDir "\config.ini"
```

`ResolvePopDropDataRoot()` 有一个特殊分支：**若程序被放在"启动"文件夹**，则改用 `%LOCALAPPDATA%\PopDrop`，并顺手把旧位置的 `config.ini` 复制过去。

格式为 **UTF-16LE + BOM + CRLF 的 INI**，且执行层面强制：`PopDropConfigDocument.Load` 先校验头两字节 `0xFEFF`，不符直接抛错"配置文件必须是带 BOM 的 UTF-16LE"；`Save()` 写完回读校验 BOM 存在且**只有一个**。历史遗留的 UTF-8 配置由 `EnsureConfigEncoding` 自动转换：读为 UTF-8 → 写临时文件为 UTF-16 → 用 `ReplaceFileW(..., WRITE_THROUGH)` 原子替换。

首次运行由 `EnsureConfig` 把 `config.example.ini` 复制为 `config.ini`；注释明确 **"config.example.ini is the single source of truth for initial defaults"**，找不到就抛错（**不内置默认值**）。

#### 5.6.2 `ConfigDocument.ahk`：手写的"无损、布局感知"文档模型

文件头注释即设计声明：**"Lossless, layout-aware editor for PopDrop's human-maintained config.ini. It deliberately does not use the Windows profile API for writes."** 这正是它自己实现整个 INI 文档模型的原因。

| 能力 | 实现方式 |
| --- | --- |
| **解析** | 自实现 `ParseSectionLine` / `ParseKeyLine` / `ParseAreaMarker`；内存模型是**字符串行数组**，不解析成字典后重排 |
| **布局锚点** | 六个 `; <PopDrop:area N>` 标记；`InstallAreaMarkers` 能从旧配置的**中文横幅**（`^\s*;\s*[一二三四五六]、`）反推位置并插入锚点，也支持从零构建六区骨架；`ValidateAreaMarkers` 要求 6 个且顺序递增 |
| **区归属 + 区内排序** | `AreaForSection`（按节名前缀归类，如 `sourceexclude:` → 区 6）+ `RankForSection`（区内 rank）；`NormalizeManagedSections` 最多迭代 **4 轮**收敛，不收敛则抛"配置节顺序无法收敛" |
| **无损写** | `ReplaceKnownKeys(section, entries, knownKeys, area)` **只重写"受管理键集合"内的键**，其余键与用户注释原样保留；`FindKeyInsertIndex` 会跳过说明注释块 |
| **禁止歧义** | 重复键、重复节**直接 throw**（`OpenPopDropConfig` 的注释：*"Reject ambiguity before any writer gets a chance to normalize it away"*）——先拒绝，再谈规范化 |
| **自校验** | `Validate(requireVersion)` 检查重复节/重复键/节位置/必有 `[General]`/必有 `ConfigVersion` |

它解决的是"GUI 保存一次就把用户手写的注释和自定义键全冲掉"这个常见痛点。

#### 5.6.3 写盘事务：`AtomicConfigEdit`

配置写入被封装成一个显式事务（`CoreUtilities.ahk`）：

1. `Critical("On")` + `ConfigEditInProgress` **重入锁**；
2. 复制到私有临时副本（`config.ini.tmp-<pid>-<tick>-<serial>`）；
3. 回调**只改副本**；
4. 写盘前用 `OpenPopDropConfig(tempPath)` + `Save()` **复验**——注释明确：malformed / duplicate / wrong layout / BOM corruption **永不触及线上配置**；
5. 用 `BuffersEqual` 与写前 baseline 字节比对，**检测到外部修改就取消本次写入并提示刷新**；
6. `ReplaceFileW` 原子替换，失败退化 `MoveFileExW`；
7. 成功后更新 `LoadedConfigStamp`，配合 `ConfigFileChangedSinceLoad` 让 F2 只在**真有外部改动**时才走昂贵的全量 `LoadSettings`。

#### 5.6.4 三层迁移机制（全部幂等）

| 层 | 时机 | 内容 |
| --- | --- | --- |
| **① 布局/默认值补齐** | 每次都跑，靠 `Dirty` 决定是否写盘 | `NormalizeConfigDocument` 依次调用 9 个 `Ensure*`（Known Folder 默认路径、刷新配置、界面间距、噪音过滤注释、文件管理器、文本卡片、**删除遗留的 `CacheCleanupEnabled`/`CacheRetentionDays`**、预览、快速预览、工作区类型），最后写 `ConfigVersion`。`ConfigLayoutNeedsNormalization` 先在内存里试跑，返回 `doc.Dirty \|\| 版本号 != CONFIG_VERSION`——**正常启动不会反复写盘** |
| **② 结构性迁移** | 一次性，带 `.bak` | `[Workspaces] Order` 为空 → 备份后把旧 `[Folders]`/`[Folder:名称]` 展开成 `[Workspaces]`+`[Workspace:...]`+`[Source:...]`（逐键搬运 13 个来源属性），`[PinnedFiles]` 搬进 `WorkspacePinned:`，并清空旧节。注释强调 **"Migration is its own atomic transaction"** |
| **③ 运行期键级迁移** | 按标志位一次性 | 如 `TransferFavoritesInitialized` 标志控制"把早期在菜单构建时临时注入的 Desktop/Downloads 持久化" |

版本门控是精确的（示例）：`oldVersion < 25 && doubleTarget == "" && firstTextId != ""` 才补 `DoubleHotkeyWorkspaceId`。

`PHASE1_MEMORY_WORKSPACE_SWITCH.md` 描述的是**运行时性能**改动而非配置迁移：切换工作区不再同步重读/改写 `config.ini`，改为内存状态绑定 + **延迟 250 ms 合并写盘**，退出或重载前强制冲刷。

#### 5.6.5 三级校验与过滤规则

| 层 | 位置 | 内容 |
| --- | --- | --- |
| 文档层 | `PopDropConfigDocument.Validate` | 节/键唯一性、节位置、BOM |
| 运行时语义层 | `ValidateConfig(workspaceType)` | 逐节解析成运行时 `Settings`，收集中文可读错误；失败时保留上次有效设置并**只弹一次**提示 |
| 设置页层（最严） | `ValidateSettingsDraft`（**315 行，全文件最大函数**） | 跨工作区来源 ID 不得复用、工作区/来源名称与 ID 唯一性、路径不得重复、排除/允许路径必须位于来源内部（`IsSameOrDescendantPath`）、父子路径重叠→Warning、快捷键重复、软件路径必须是 `.exe`、常用位置最多 5 个、文件管理器可执行文件名必须精确匹配、动作参数校验、忽略规则编译 |

**过滤规则**：

- 扩展名过滤三模式 `All`/`Include`/`Exclude`，其中 `Include` 空列表**防御性放行**、`Exclude` 空列表不排除、**未知模式放行**（选择"宽松优先"而非"安全优先"，因为过滤只影响显示）。
- 忽略（噪音）规则把 `*`→`.*`、`?`→`.` 编译成 `i)^...$` 正则，**编译失败进 Errors 而不是崩溃**。
- 危险规则 `HasDangerousIgnorePattern` 检测 `*` / `*.*`，保存时二次确认。
- 来源级通过 `Inherit`/`Enabled`/`Disabled` 三态叠加共享规则。

#### 5.6.6 设置界面架构

`SettingsGui.ahk` 有 **4615 行 / 189 KB**，因为它不是"一个设置窗口"，而是**一个主窗口 + 11 个 Owner 子窗口 + 三层逻辑**的集合：7 个手写布局页、11 个独立 `Gui(` 子窗口、草稿装载（123 行）、校验（315 行）、脏判定（79 行）、写盘 + 回滚（181 + 115 行）。顶层函数约 130 个，`OnEvent(` 158 处，`c.Loading` 守卫 28 处。**纯手写、非数据驱动**。

**界面骨架**：

```
OpenSettingsGui()
├─ guiObj := Gui("+Owner" Panel.Hwnd ...)         ; 所有者 = 主面板
├─ controller := { Gui, Draft, OriginalSignature, Ready, Loading, ... }
├─ navigation := AddTreeView("xm ym w156 h752")   ; 共享设置(5 页) / 工作区设置(1 页) / 关于(1 页)
├─ tabs := AddTab3("x184 y-26 w852 h790 -Tabstop", [...])
└─ Build*SettingsPage(controller, tabs) × 7
```

其中几处手法都有解释原因的注释，是这个文件可维护的关键：

- **Tab3 的标签条被移出客户区**（`y-26` + `-Tabstop`），让 TreeView 成为唯一可见导航；
- Tab3 原生表头会在标题栏下留白色页面背景，用一条**不可聚焦的原生 spacer** 补灰边；
- **底部按钮必须用绝对 Y**——`y+` 会以"当前活动页最后一个控件"为基准，把 footer 放到 Tab3 底下，**可见但收不到鼠标事件**；
- **`controller.Ready` 延迟发布到 `guiObj.Show()` 之后**，因为面板定时器与工具栏状态同步可能在 GUI 构造中途插入，提前暴露 controller 会让处理器访问尚不存在的控件；构造异常时 catch 块销毁半成品。

**控件 ↔ 配置绑定**：单向"控件 → 草稿对象"，靠 `c.Loading` 标志区分方向（回填时置位、`finally` 复位；回写时开头 `if c.Loading return`）。**枚举/布尔一律在边界转换，草稿里存稳定字符串而非控件序号**。列表类控件用**行号 ↔ 稳定 ID 映射表**（`Map`）。来源页是**延迟提交**：控件值不实时写草稿，而由 `CommitCurrentSourceControlsToDraft` 在"切换来源 / 切换页 / 判脏 / 保存"四个时点统一提交。

**没有"即时生效"**——文件头注释就是契约：*"All controls edit an isolated draft. Disk and runtime state are touched only by SaveSettingsDraft()."*

- **脏判定是"序列化即签名"**：先把所有页面的控件刷进草稿，再把整个草稿扁平化成 `Array` 后 `HashString(JoinArray(parts, Chr(30)))` 与打开时记录的签名比较。新增配置项只需加一行，不必逐控件比对。
- **快捷键冲突检测用"临时注册探测"而不是查表**：执行 `Hotkey(candidate, Probe, "On")` 再 `Off`，捕获异常即不可用；工作区版会先允许同工作区自身复用。

**保存是一个完整事务**（顺序严格）：

```
提交各页控件 → 规范化路径
→ ValidateSettingsDraft
     Errors   非空 → 逐条列出，阻断
     Warnings 非空 → YesNo 确认
→ 危险忽略规则('*' / '*.*') → YesNo 二次确认
→ 快捷键试注册探测（主键 + 每个工作区）
→ CreateConfigBackup()  (FileCopy → .bak)
→ AtomicConfigEdit(WriteSettingsDraft)
→ ApplyStartupShortcut → LoadSettings → ApplyWindowMode
→ InstallHotkey/InstallWorkspaceHotkeys → BuildTrayMenu
→ PopulatePanel/StartBackgroundScan → 刷新签名
catch → 用 .bak 反向 AtomicConfigEdit 回滚 + 重建三处 UI
```

回滚后额外重建面板/最近栏/后台扫描，注释解释：应用设置时会在后续操作完成前就重填原生视图，失败时不重建会留下空面板。

**深链入口**（同一窗口单例复用）：托盘与侧栏齿轮 → 任意页；托盘"关于" → 第 7 页；**文件管理器失败时 → 第 2 页并聚焦 provider 下拉**；面板右键"设置此来源…" → 第 6 页。后者处理了最复杂的语义：目标工作区不存在则报错、草稿有改动时提供"保存/放弃/取消"三选、跨工作区会先切换工作区再重载草稿。

### 5.7 构建、打包与测试体系

#### 5.7.1 `build.ps1`：只做一件事，但带 12 项前置检查

它**只把 `PopDrop.ahk` 编译成 `PopDrop.exe`**——不做资源嵌入（交给源码指令）、不做 zip 打包、不做版本号注入（版本在源码里，脚本只**校验**）。

**① 16 项 pre-flight，每项独立退出码**：Ahk2Exe 存在(1)、入口存在(2)、`#Requires AutoHotkey v2.`(3)、v2 Base 文件(4)、六个 `.ico`(5/6/13/14/16/17)、输出目录可写(7)、同名 exe 未运行(8)、`#Include` 目标存在(9)、**`config.example.ini` 存在(10)**、**源码版本一致(15)**、11 个工具栏 PNG(18)。

**② `#Include` 静态自检**：正则扫描入口文件的 `#Include` 并逐个 `Test-Path`。**必须这么做**，因为 AHK 的 `#Include` 是**文本包含**，编译期不会帮你发现漏掉的模块文件。

**③ 源文件编码自愈**：读入口文件首三字节，非 `EF BB BF` 就**就地补 UTF-8 BOM**，脚本给出的理由是 `"adding BOM for Chinese compatibility"`。

**④ 编译前先跑测试（门禁）**：

```powershell
AutoHotkey64.exe <script> --self-test      # 失败 → exit 11
python -m unittest discover -s tests -v    # 失败 → exit 12；无 python 仅 Warn
```

**⑤ 调用 Ahk2Exe**：

```powershell
Start-Process $CompilerPath -ArgumentList "/in `"$AhkScriptPath`" /out `"$OutputPath`" /base `"$basePath`" /compress 0" `
  -NoNewWindow -Wait -PassThru
```

三个细节都是踩坑得来的：必须用 `Start-Process` 才能拿到退出码（**Ahk2Exe 1.1.x 是 GUI 程序**）；参数必须是**单一字符串**而非数组；**不传 `/icon`**——图标来自源码指令。

**⑥ 日志与判定**：写 `build_logs\build_<时间戳>.log`（环境/路径/完整参数/退出码十进制与十六进制/产物大小），内置 Ahk2Exe 退出码含义表，最终成功要求 `exitCode -eq 0 && 输出存在 && 大小 > 0 && config.example.ini 在旁边`。

#### 5.7.2 资源嵌入与版本，以及一个 Ahk2Exe 陷阱

全部由源码顶部的编译指令完成：

```ahk
;@Ahk2Exe-SetMainIcon assets\app.ico
;@Ahk2Exe-AddResource assets\tray.ico, 555
;@Ahk2Exe-AddResource assets\icon-lnk.ico, 556
;@Ahk2Exe-AddResource assets\pin.ico, 557
;@Ahk2Exe-AddResource assets\empty-folder.ico, 558
;@Ahk2Exe-AddResource assets\unknown-file.ico, 559
;@Ahk2Exe-SetVersion 2.1.0.0
;@Ahk2Exe-SetName PopDrop
```

`BUILD.md` 用大篇幅记录了一个陷阱，值得单独引用：**必须用 `/base 'C:\Program Files\AutoHotkey\v2\AutoHotkey64.exe'`，不能把 `AutoHotkey64.exe` 改名成 `.bin`**。原理是 Ahk2Exe 按 Base 扩展名决定嵌入方式：`.exe` → 写入 `RCDATA #1`，v2 解释器启动时自动加载；`.bin` → 旧式 `>AUTOHOTKEY SCRIPT<` 资源名，**v2 不识别**，编出来的 EXE 退化成解释器（运行时报 "Script file not found"）。验证方法是把 EXE 拷到没有同名 `.ahk` 的空目录运行。

#### 5.7.3 `#Include` 的包含顺序也有语义

`#Include` 在 AHK 中是文本包含，编译期把全部模块内联进单个 EXE。入口文件分两段包含：先包含 6 个紧邻的独立组件（`ConfigDocument`、`FileManager`、`SettingsGui`、`ExternalDrop`、`Preview`、`QuickPreview`），再包含 `modules\` 下 20 个业务模块。

**常量块必须远在 `#Include` 之前**，因为注释要求"worker 函数依赖的所有常量必须在 worker 分流块之前定义"（`--self-test` / `--scan-worker` / `--thumbnail-cache-worker` 分流都依赖它们）。

**一处刻意的重复**：`modules/ScanCache.ahk` 与 `modules/ScanCacheIntegrity.inc` **字节完全相同**（MD5 一致），而入口**只包含 `.inc`**。给出理由是：原 `.ahk` 仅保留用于既有静态契约对照，不参与运行，**避免"附件镜像恢复旧文件"后覆盖完整性修复**。这是防御性重复，不是遗漏。

#### 5.7.4 自测体系

**`--self-test` 是一个启动期参数分流，在"任何 GUI / hotkey / tray / COM 初始化之前"执行**：

```ahk
if A_Args.Length && A_Args[1] = "--self-test" {
    RunSelfTests()
    ExitApp
}
```

只在两处被调用：手动命令行，以及 `build.ps1` 的构建前置门禁。GUI/托盘不提供自测入口。

框架**极简、fail-fast**：唯一断言 `AssertSelfTest(condition, name)` 失败即 `throw`；唯一驱动 `RunSelfTests()` 用一个 `try` 包住全部 suite，成功路径写 `self-test: PASS`，`catch` 里写 `FAIL - <消息>` 然后 `ExitApp(1)`。特点也即局限：**无计数、无跳过机制、失败即停（只报第一个失败）、退出码固定 1**。

**覆盖规模：303 条断言**（`SelfTests.ahk` 260、`FileManager.ahk` 24、`Preview.ahk` 19），suite 按功能切分（配置文档往返、预览、文件管理器、文件夹投放、来源配置、来源管理、来源移除、噪音过滤、工作区解析、缓存维护、动作参数转义），外加约 40 条内联 UI 语义断言（文本块 `Ctrl+V` 归属、Tab 索引计算、多关键字 AND 搜索、**IME 组合期间 Enter 归输入法**、分栏标题展开/收起符号等）。

两个工程细节：① 用例真的建临时目录/文件再 `finally` 清理；② 有针对"自测启动时机"的回归——因为自测在任何 UI 全局初始化之前运行，相关断言必须显式传入缩放参数才能启动安全。

**python 静态契约测试**（`tests/verify_*_contract.py`，共 9 个脚本）在本仓库中**不存在**（`.gitignore` 忽略 `tests/`），只能从文档反推设计：

- **跨平台**——用 python 做**源码文本级契约检查**，不需要 Windows 即可在 CI 上跑（文档明确"当前交付环境没有 AutoHotkey、PowerShell/MSVC 和 Windows Shell/OLE"，说明 python 层就是为无 Windows 环境准备的）；
- **解析包含图**——靠 `tests/project_source.py` 识别 `modules\*.ahk` 的 `#Include` 关系，**把"文件搬家"这种纯机械操作也纳入契约保护**；
- **锁定行为约束而非运行时行为**——命名（"重命名契约""散落修复契约""模块布局契约"）说明断言的是"某函数必须存在 / 某调用点必须保持 / 某反模式不得出现"；
- **也含纯逻辑正反例**——如终端首尾换行清理、宿主识别、单次投送、**中文自然语言规则正反例**；
- **接进构建**——python 存在就跑，失败 `exit 12`。

#### 5.7.5 运行期缓存维护（`CacheMaintenance.ahk`）

目标：只清理 PopDrop 自己产生的运行时缓存残留，**只处理 `CacheDir` 下"精确已知名字的直接子项"**，绝不进入 `preview-cache-v1`（归预览 Helper 全权管理）。

**何时执行**——不是定时器，而是**"面板真的打开又隐藏"后的机会任务**：读 `cache-maintenance.ini` 的 `CompletedDate`，**同一天已完成就不再排**；否则 10 秒一次性定时器。重新打开面板即取消。执行前校验 generation、面板可见性、**不跨午夜**，并且"扫描 worker / 非活动扫描任务 / 待写缓存 / 预览缓存队列"都算高优先级工作，此时 2 秒后重试。

**安全边界（最值得借鉴的部分）**：

| 边界 | 实现 |
| --- | --- |
| **硬预算** | `MaxInspected: 256` / `MaxDeleted: 24` / `MaxMilliseconds: 150` |
| **不追重解析点** | 文件属性含 `L`（符号链接/联接点）直接 `continue` |
| **白名单式名称分类** | 只识别 `ready-<hex>-<hex>` 目录、`inactive-*.ready`、`request-*.request.ini`、`workspace-<hex8>.ini.writing`、`.write-test-N`、`scan-cache-v1..v3.ini`、`workspace-<hex8>.ini`；**不认识的名字永不删** |
| **年龄门槛** | 临时项 ≥900s、写入中 ≥3600s、遗留项 ≥86400s；工作区快照仅当**不在当前工作区列表**且 ≥7 天 |
| **活跃保护** | 当前 worker 的 request/ready 路径、非活动扫描任务的路径**绝不删** |
| **损坏备份有界保留** | `index.db.corrupt-<时间戳>` 组 ≥7 天删，否则**最多保留 3 组**（超出删最旧） |
| **可中断** | 每次循环前查面板可见性/让位请求/预算；让位后**跳过收尾阶段** |

自测只有约 10 条**纯逻辑**断言（测名称分类与删除判定），删除动作本身不测——**破坏性操作不进自测**，是合理取舍。

#### 5.7.6 打包现状与第三方许可

- **仓库里没有 zip / 安装包脚本**。`PACKAGE_CONTENTS.txt` 是人工维护的发布包清单，且内容已与当前版本脱节（仍写"v1.0.0"）。
- 发布清单要求：两个 Helper（**必须 x64，x86 不得与 x64 主程序混用**，启动时握手会明确拒绝不兼容组件而非继续运行旧二进制）、`config.example.ini`、`assets/`、四份文档、`install-pdfium.ps1` + `pdfium-component.ini` + PDFium LICENSE。
- **`THIRD_PARTY_NOTICES.md` 的核心策略是"不捆绑 + 逐条声明不做什么"**：开篇声明源码包没有捆绑 PDFium / Seer / QuickLook / Office / pngquant / libimagequant / GPL 代码或商业组件；PDFium 只**动态加载 DLL、不复制源码**；Seer/QuickLook 不下载、不安装、不复制、不再分发，并**明确声明"不复制 QuickLook 的 GPL 源代码"**（规避 GPL 传染的关键表述）。

#### 5.7.7 值得借鉴的工程实践小结

1. **文本 `#Include` 模块化 + 明确的"修改约定"**：12,996 行单文件拆成"入口只管版本常量/共享状态/依赖加载/进程启动/消息注册，业务进 modules"，且约定"函数名参数调用点不变、不引入新运行时抽象、`OnMessage`/GUI 回调/COM vtable 回调暂时保持自由函数形式以免增加回调绑定和生命周期风险"——**只降低导航成本，不改变行为**。
2. **测试在构建脚本里做门禁，且分三层**：AHK 内纯逻辑/Windows API 自测（303 断言）→ 跨平台 python 静态契约 + 纯逻辑回归（214 项）→ `build.ps1` 编译**前**先跑两者，失败不产出产物。
3. **配置的"无损可人工维护"设计**：只重写受管理键、保留未知键与用户注释、六个区锚点保证人工编辑位置稳定、重复键直接 fail-fast。
4. **写配置的并发安全**：`Critical` + 重入锁 + 私有临时副本 + 写前 baseline 字节比对 + `ReplaceFileW` 原子替换 + `MoveFileExW` 兜底，再配 stamp 区分"自己写的"与"外面改的"。
5. **设置保存是完整事务**：备份 → 原子写 → 应用运行时 → 失败回滚并重建 UI；校验分"Errors 阻断 / Warnings 可确认 / 危险模式二次确认"三级。
6. **注释写"为什么"而不是"是什么"，且专门记录 Windows GUI 陷阱**——这是 4615 行单文件仍可维护的关键（为什么补灰边、为什么 footer 必须绝对 Y、为什么延迟发布 controller、为什么两个 radio 要手工互斥——*"两个控件之间的说明文字让 Windows 无法可靠地把它们当作一个原生 radio group"*）。
7. **交付文档体系**（同类个人项目中罕见）：`DELIVERY_NOTES.md`（约 45 KB）逐轮记录"修正/交付/兼容迁移/验证"并附**可执行的实机人工检查清单**；`dev_doc/*_TEST_REPORT.md` 每个子系统一份并**诚实标注"未执行（环境没有 Windows/AutoHotkey）"**；`CHANGELOG.md`（约 135 KB）按版本+主题分节，写清"保留了什么、没改什么"。
8. **构建可复现**：不依赖 Ahk2Exe 的 GUI 保存设置、所有参数显式传、每次写带时间戳日志、内置退出码含义表。
9. **跨 DPI 的 UI 一致性抽象**：把控件高度、下拉框垂直居中、物理像素偏移收口成工厂函数，并区分"逻辑缩放"与"物理像素"（用 `MulDiv` 避免二次取整）。
10. **把"不做的事"写成契约**：逐条写明不捆绑什么、缓存目录归属、不构造命令行、不依赖 UI 自动化——反向约束使代码审查与安全边界都有据可依。

---

## 6. 工程实践

### 6.1 源码组织：从 12,996 行单文件到"低风险模块化"

旧版 `PopDrop.ahk` 单文件 12,996 行 / 约 479 KB，同时承载启动、配置、UI、扫描、文件操作、OLE 拖放和自测。拆分（`dev_doc/CODE_ORGANIZATION.md`）**刻意选择了最低风险的路径**：

- 用 AutoHotkey v2 的**文本 `#Include`**，而不是引入类/命名空间等运行时抽象；
- **函数名、参数、调用点完全不变**；
- 全局变量仍由入口集中初始化；自动执行段、worker 分流、消息注册次序不变。

拆分后的职责边界很清晰：入口只管"版本与常量、共享状态、依赖加载、进程启动、消息注册"，15 个 `modules/*.ahk` 按职责分列（面板对话框、配置、打开方式、通用工具、原生控件、面板 UI、扫描缓存、项目动作、右键菜单、指针输入、文件操作、`IDropTarget`、`IDragSource`、自测、退出清理）。

**修改约定**同样写进文档而非口头传承：新功能进职责最接近的模块、入口文件只允许新增启动期常量/共享状态/初始化调用/消息注册、`OnMessage`/GUI 回调/COM vtable 回调**暂时保持自由函数形式**（*"以免增加 AutoHotkey 回调绑定和生命周期风险"*）、跨模块状态暂时沿用全局变量但可逐子系统收拢、**移动函数后必须同步维护 `tests/project_source.py` 的包含关系**。

这段"知道自己欠了技术债、但明确不一次性还清"的取舍，比"一次重构成完美架构"更值得个人项目参考。

### 6.2 注释：只写"为什么"，并专门记录 Windows 陷阱

代码里注释的密度分布不均，但有一条稳定规律——**凡是看起来"多余"或"绕"的代码，一定有注释解释为什么不能写成更直观的样子**。例如：

- 为什么两个 radio 要手工互斥：*"两个控件之间的说明文字让 Windows 无法可靠地把它们当作一个原生 radio group"*；
- 为什么设置窗 footer 必须用绝对 Y 而不是 `y+`；
- 为什么自测要在任何 UI 全局初始化之前运行；
- 为什么 `ConfigDocument` 不用 Windows profile API 写配置；
- 为什么 `ScanCache.ahk` 与 `ScanCacheIntegrity.inc` 要字节级重复。

这类注释的价值随维护年限递增——**它们是"防止后人好心改坏"的唯一手段**，也是本项目在缺乏自动化 UI 测试的前提下仍能持续重构的原因。

### 6.3 交付文档体系（同类个人项目中罕见）

| 文档 | 规模 | 特点 |
| --- | --- | --- |
| `CHANGELOG.md` | 约 135 KB | 按"版本 + 主题"分节，不只写改了什么，还写清**保留了什么、没改什么** |
| `DELIVERY_NOTES.md` | 约 45 KB | 逐轮记录"修正 / 交付 / 兼容迁移 / 验证"，并附**可执行的实机人工检查清单** |
| `dev_doc/*_TEST_REPORT.md` | 每子系统一份 | 逐条列出验证项，并**诚实标注"未执行（环境没有 Windows / AutoHotkey）"** |
| `dev_doc/CODE_ORGANIZATION.md`、`WORKSPACE_CONTENT_INTEGRITY.md` 等 | 若干 | 把架构决策与完整性约束固化成可引用文档 |
| `BUILD.md` | — | 用大篇幅记录 *为什么不能这么做*（如 Ahk2Exe 的 `/base` 扩展名陷阱） |
| `THIRD_PARTY_NOTICES.md` | — | 逐条声明"不捆绑什么、不下载什么、不复制定什么" |

其中"**诚实标注未执行**"这一点尤其值得肯定：测试报告里区分"已在 Windows 实机验证"与"环境不具备故未执行"，而不是含糊地写成"已测试"。

### 6.4 验证纪律

三层，且顺序固定（详见 §5.7.4）：

```
AHK 内自测（303 断言，纯逻辑 + Windows API 语义）
      ↓
python 跨平台静态契约（9 个脚本，源码文本级 + 纯逻辑正反例）
      ↓
build.ps1 编译前门禁（失败 exit 11 / 12，不产出产物）
```

**关键设计是"契约测试保护重构"**：把"某函数必须存在 / 某调用点必须保持 / 某反模式不得出现 / 模块包含关系必须完整"写成可执行断言。于是像"函数搬家"这种纯机械但极易出错的重构，也能在无 Windows 的环境里被机器验证——这对"AI 辅助大规模重构"尤其重要。

### 6.5 把"不做的事"写成契约

项目在多处显式声明**不做什么**，且这些声明是分散在代码注释、文档与发布清单里的稳定约束：不替代资源管理器 / Total Commander / Directory Opus；不捆绑 PDFium、Seer、QuickLook、Office、GNU 代码；缓存目录中 `preview-cache-v1` 归预览 Helper 全权管理、他人不得进入；不构造命令行（避免转义与注入问题）；不依赖 UI 自动化。

**反向约束比正向功能说明更能约束后续实现**——每加一个功能，"能不能这么做"有据可依。

### 6.6 面向 AI 辅助开发的工程约束

`CODE_ORGANIZATION.md` 里"移动函数后同步维护 `tests/project_source.py`"这条约定泄露了这个项目的真实工作方式：**它假设相当一部分改动是由 AI 或非原作者完成的**。由此形成的整套约束——模块化降低导航成本、契约测试防止误改、`#Include` 静态自检防止漏文件、BOM 自愈防止编码事故、注释记录陷阱、交付文档写清边界——恰好构成了一套**适合人机协作的工程护栏**。

这一点对本项目（MyScreenshot）的参考价值，可能高于其中任何一项具体技术。

## 7. 与本项目的复用可行性评估

> 本节为附加评估（非原始需求）。前提：**PopDrop 是 AutoHotkey 项目，本项目（MyScreenshot）是 C++ / WTL / ATL 项目，二者无共享代码的可能**，因此以下只评估**架构思路与技术方案**的迁移价值，不涉及代码复制。

### 7.1 结论速览

| PopDrop 技术点 | 本项目现状 | 复用价值 | 迁移成本 |
| --- | --- | --- | --- |
| OLE 拖放（`IDropSource`/`IDataObject`/`CF_HDROP`/`CF_UNICODETEXT`） | 无，截图靠剪贴板 + 另存为 | **高** | 中 |
| 无损、布局感知的 INI 配置模型 | `Screenshot/core/AppSettings.cpp`（368 行，Win32 profile API 扁平读写） | **高** | 中 |
| 配置三级校验 + 保存事务回滚 | `SettingsDlg.cpp` 直接写盘 | **高** | 低 |
| 运行期缓存的硬预算 / 白名单 / 活跃保护 | `cache/` 目录已堆积大量构建日志，无清理机制 | **高** | 低 |
| `IFileOperation` 保存/移动 | 自绘保存路径 | 中 | 低 |
| 常驻 Helper + 共享内存 IPC + Job Object 隔离 | OCR 在进程内（`OcrRapidEngine` 持 onnxruntime） | 中 | 高 |
| PDFium 动态加载 + 导出校验 | 无 PDF 能力 | 中 | 中 |
| IFilter / WinRT `Windows.Data.Pdf` 文本抽取 | OCR 走图像识别，无"文本型 PDF/DOCX 直接抽文本"路径 | 中 | 低 |
| 构建门禁 + 静态契约测试 | 无自动化测试 | 中高 | 中 |
| 注释"为什么" + 陷阱归档 | 已有 `docs/*问题归档.md` 的习惯 | 高（习惯已具备） | 极低 |
| AHK 语言本身、手写 GUI 布局、`Hotkey()` 探测、Tab3/TreeView 技巧 | — | 不适用 | — |

### 7.2 高价值、建议优先考虑

**① OLE 拖放：把"截图 → 保存/复制 → 切窗口 → 粘贴"压缩成一步**

这是本项目 TODO 与使用体验中最明显的一块空白。PopDrop 的完整实现路径可直接对应到 C++（在 C++ 中实现 `IDropSource` / `IDataObject` 比 AHK 手写 vtable **简单得多**）：

- `ShellDrag.ahk` → 构造 `CF_HDROP`（`DROPFILES` + 双 `\0` 结尾的路径列表）与 `CF_UNICODETEXT` 数据对象；
- `DropTarget.ahk` → `RegisterDragDrop` / `RevokeDragDrop` / `IDropTarget::DragEnter-DragOver-Drop` 的返回码语义（`DROPEFFECT_*`）；
- 关键约束（§5.5.1、§8.2）：**`OleInitialize` 必须在 UI 线程**；**跨权限级别拖放会被 UIPI 阻止**，需要在文档与 UI 上明确告知用户，而不是当作 bug 修。

可落地的场景：截图完成后直接拖出、贴图窗口（`CFloatWindow`）拖出、OCR 结果文本拖出。

**② 配置系统的"无损 + 事务"改造**

本项目 `AppSettings.cpp` 目前是扁平的 Win32 profile API 读写、`SettingsDlg` 保存时直接落盘。PopDrop 的两个设计可以低成本补上：

- **无损写**：只重写"受管理键"，保留用户手写注释与未知键；重复节/重复键**直接拒绝**而不是"规范化掉"。本项目配置项已稳定，迁移面可控。
- **保存即事务**：`Critical` 重入锁 → 私有临时副本 → 写前复验 → 与原文件字节比对（**检测到外部修改就取消并提示**）→ `ReplaceFileW` 原子替换 → 失败用 `.bak` 回滚并重建 UI。本项目 `SettingsDlg` 加这一层，能直接消掉"改设置后配置损坏 / 覆盖了手改内容"这类问题。
- **三级校验**（文档层唯一性 → 运行时语义 → 设置页最严格跨项校验）的**分级思路**同样适用：`Errors` 阻断、`Warnings` 可确认、危险项二次确认。

**③ 运行期缓存的"硬预算 + 白名单 + 活跃保护"**

`CacheMaintenance.ahk`（§5.7.5）几乎可以逐条搬用：每轮最多检查 256 项 / 删除 24 项 / 耗时 150 ms；**不认识的文件名永不删**；不追符号链接与联接点；临时项按年龄门槛（900s / 3600s / 86400s）；当前任务正在使用的路径绝不删；**损坏备份最多保留 3 组**。本项目 `cache/` 已被构建日志淹没，且后续若增加"截图历史 / 录屏临时文件"会立刻遇到同样问题。

### 7.3 中等价值、按需考虑

- **`IFileOperation` + `IFileOperationProgressSink`**：让"另存为 / 移动 / 重命名"走系统实现，免费获得进度对话框、同名冲突 UI、撤销支持与长路径处理，省掉自绘对话框（§5.5.4）。
- **文本型文档直接抽文本**：本项目 OCR 走的是图像识别路线。若将来支持"导入 PDF / DOCX 并识别"，`Windows.Data.Pdf`（WinRT）与 `LoadIFilter`（DOCX）能**跳过图像识别直接取文本**，准确率与速度都远优于 OCR。
- **PDFium 动态加载范式**：`LoadLibraryExW` + `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32` + **逐个 `GetProcAddress` 校验 13 个导出，任一缺失立即失败**。这条"**加载成功 ≠ 可用**"的校验纪律，与本项目已有的 onnxruntime.dll 假 stub 探测经验（见记忆：SysWOW64 的 onnxruntime.dll 是 stub）完全一致，值得作为通用加载器规范固化。
- **构建门禁 + 静态契约测试**：本项目受本地安全策略限制不能用 PowerShell（AGENTS.md），但 PopDrop 的**测试先于产物**、**退出码区分失败原因**、**源码文本级契约检查**三点可用 python 实现。尤其"契约测试保护重构"对本项目正在进行的模块化 / 框架迁移（WTL 重构、DuiLib 迁移评估）有直接价值。
- **`BELOW_NORMAL_PRIORITY_CLASS` + Job Object（512 MiB 上限 + `KILL_ON_JOB_CLOSE`）隔离重负载组件**：本项目的 OCR（onnxruntime）是典型的重内存组件，若将来做进程隔离，这套"低优先级 + 内存上限 + 随主进程退出"的组合可直接照搬。

### 7.4 不适用

- AutoHotkey 语言特性、手写 GUI 布局与 `Tab3`/`TreeView` 技巧、`Hotkey()` 试注册探测——均为 AHK 特有，本项目无对应场景；
- 扫描 worker / 缩略图缓存 worker 的多进程扫描架构——本项目无"扫描海量目录"的需求；
- Seer / QuickLook 集成——本项目是截图工具，无"悬停预览文件"场景。

### 7.5 建议的落地顺序

1. **配置无损化 + 保存事务**（改动面小、收益直接、可独立验证）；
2. **缓存维护策略**（纯新增、无侵入、立刻缓解 `cache/` 膨胀）；
3. **拖放支持**（收益最大但涉及 OLE 初始化与线程模型，需单独立项，参考 §5.5.1 / §8.2 的约束）；
4. **构建门禁 + python 契约测试**（长期收益，配合框架迁移一起做）。

---

## 8. 明确的限制与边界

### 8.1 系统与运行环境

- **仅支持 Windows 10 / Windows 11**。
- 源码运行需 **AutoHotkey v2**（v1 不行）；编译需 Ahk2Exe；构建原生 Helper 需 VS 2022 Build Tools"使用 C++ 的桌面开发"工作负载。
- 依赖系统自带 `WinSQLite3.dll`（Windows 10/11 标准组件；不可用时自动回退 INI 快照）。
- 需要 `native\bin\<架构>\PopDropTransfer.exe`（外部内容投放）与 `PopDropPreview.exe`（文件预览）；正式发布包已包含，源码运行需自行构建。

### 8.2 权限与拖放（UIPI）

- **Windows UIPI 会阻止不同管理员权限级别进程之间的拖放**。例如资源管理器为普通权限、PopDrop 以管理员身份运行时，资源管理器可能根本无法把数据送入面板。**要求来源程序与 PopDrop 使用相同权限级别；PopDrop 不绕过这项系统安全限制。**
- 终端发送中权限等级不一致可能使激活或输入投送被 Windows 阻止，此时**安全停止，不向其他窗口降级发送**。

### 8.3 安全软件误报

- 软件使用 AutoHotkey 开发，**少数安全软件可能误报**，文档建议从仓库 Releases 下载。

### 8.4 功能范围声明

- 预览与文档解析：原始 HTML、脚本、Mermaid、插件、网络资源与链接点击**均不执行**；CSV/TSV 不执行公式；复杂 DOCX 版式、分页、页眉页脚与嵌入图片可能被简化或忽略；DOCX 在可终止 Helper 内运行，不启动 Word、不执行宏/OLE/ActiveX。
- **One Commander 明确不在文件管理器支持列表**。
- 筛选**不能避免对目录的完整枚举**，因此不能作为解决超大目录扫描速度的主要手段。
- 工具动作的 PerItem 只能观察进程是否退出，**无法判断工具是否实际处理成功**。
- 缓存**不包含用户文件内容**；噪声过滤只影响显示，不删除、移动或修改真实文件。
- **无多语言界面支持**，全部界面文案为简体中文。

### 8.5 外部分支的兼容边界

- **Windows 终端发送**：用户解绑 Windows Terminal 的 `Shift+Insert` 后 PopDrop 无法确认动作是否生效，因此**不做第二次按键或右键重试**，正文留在剪贴板；宿主窗口无法判断活动窗格内是 Shell、REPL、SSH、全屏程序还是文本选择；**IDE 集成终端、第三方终端与旧式 `ApplicationFrameWindow` 宿主不在首版承诺范围**。
- **外部内容投放**：Chrome/Edge/Firefox/网盘网页/聊天软件是否可用取决于它们是否提供标准格式；**页面内部排序、私有格式、网盘目录树、空目录、需要 Cookie 或特殊请求头的内容不承诺支持**；`TYMED_ISTORAGE` 明确不支持；虚拟目录不支持；HTTP 默认关闭。
- **外部空格键预览**：QuickLook **Microsoft Store 版不具有可假定的命令行接口**；能力检测失败时不接管空格键。
- **选择窗口定位**：普通设置框不会仅凭标题或"确定"按钮被启用；自定义窗体需同时具备树控件、唯一可见路径输入框以及精确窗体类或明确的文件夹选择标题。
- **最近文件侧边栏**：Windows 隐私设置关闭"显示最近打开的项目"或系统无记录时为空，**这不是 PopDrop 的问题**。

### 8.6 明确不做的事

- **不自动打开 EXE、MSI、脚本、快捷方式或宏文档，也不执行杀毒命令行。**
- 固定项、Launcher 与顶部智能入口**绝不会因修饰键移动原文件**；顶部绝不返回 `MOVE`。
- 删除时**回收站不可用不会改为永久删除**。
- 下载任务**不提供"退出界面但继续传输"的虚假选项**。
- **源码包不捆绑 PDFium、Seer、QuickLook、Office、pngquant、libimagequant、GPL 代码或商业组件**；不下载/安装/复制/再分发 Seer 与 QuickLook，也不复制其 GPL 源代码。

---

## 9. 参考文件索引

| 文件 | 内容 |
| --- | --- |
| `README.md` | 项目定位与快速开始 |
| `USAGE.md` | 完整使用指南（约 92 KB，功能与配置的权威来源） |
| `BUILD.md` | 源码运行与构建说明 |
| `CHANGELOG.md` | 全量更新日志（约 135 KB） |
| `RELEASE_NOTES_v1.0.0.md` / `RELEASE_NOTES_v2.0.0.md` | 两个大版本发布说明 |
| `config.example.ini` / `config.example.utf8.ini` | 配置示例（UTF-16LE / UTF-8 两种呈现） |
| `HOT_WORKSPACE_VIEWS.md` | 工作区热视图机制说明 |
| `WORKSPACE_CONTENT_INTEGRITY.md` | 工作区内容完整性（安全呈现 vs 最新内容） |
| `PHASE1_MEMORY_WORKSPACE_SWITCH.md` | 内存态工作区切换阶段记录 |
| `TERMINAL_SEND_VALIDATION.md` | 终端发送验证与兼容边界 |
| `DELIVERY_NOTES.md` | 交付说明（约 45 KB，含大量设计取舍记录） |
| `dev_doc/CODE_ORGANIZATION.md` | 源码模块划分与修改约定 |
| `dev_doc/DOCUMENT_PREVIEW_TECHNICAL.md` | 文档预览技术方案 |
| `dev_doc/*_TEST_REPORT.md` | 各子系统测试报告 |
| `THIRD_PARTY_NOTICES.md` | 第三方许可声明 |
| `PACKAGE_CONTENTS.txt` | 发布包内容清单 |

---

## 10. 分析过程备注：源码中发现的若干不一致

以下是在阅读源码时顺带发现的问题，**不属于本文功能梳理的范围，但可能影响读者对仓库状态的判断**，故单独列出。这些结论来自静态阅读与文件比对，未经运行验证。

| 项 | 观察 | 影响 |
| --- | --- | --- |
| **版本号三处不一致** | `PopDrop.ahk:23-24` 声明 `APP_VERSION := "2.1.0"` / `CONFIG_VERSION := "30"`；`build.ps1` 与 `native` 侧 `kHelperVersion` 均断言 `2.1.0`；而 `CHANGELOG.md` 最新条目为 **v2.0.12** | 本次分析的 commit `8d4e27c4` 是 **v2.1.0 的开发态源码**，v2.1.0 尚未写入 CHANGELOG。§2 的功能描述以源码为准 |
| **`config.example.utf8.ini` 是失效残留** | 零源码引用（`EnsureConfig` 只读 `config.example.ini`）；默认值已过期（如 `MaxFilesPerFolder=13` vs 现值 `10`、`ThumbnailSize=96` vs `106`、`WindowWidth=766` vs `686`）；其首行注释还错误地声称自己是 UTF-16LE | 若用户按它配置会得到过期默认值。`config.example.ini` 才是**唯一权威** |
| **`native/tests/SyntheticDataObjectTest.cpp` 缺失** | `native/build.ps1:55` 引用该文件，但它不在仓库树中；x86 分支不受影响 | x64 原生构建会以 "SyntheticDataObjectTest build failed" 失败 |
| **BOM 状态不一致** | `PopDrop.ahk` 当前**无** UTF-8 BOM（首字节为 `#Re`），而 `SettingsGui.ahk`、`modules/Configuration.ahk` 有 | `build.ps1:256-267` 会在编译前就地补 BOM（"adding BOM for Chinese compatibility"）自愈，故不影响构建，但仓库内编码状态确实是混合的 |
| **`modules/ScanCache.ahk` 与 `ScanCacheIntegrity.inc` 字节相同** | 各 137598 B、MD5 一致，但入口**只包含 `.inc`**（`PopDrop.ahk:684`） | 对 `.ahk` 的任何修改**对运行期无效**。这是按 `WORKSPACE_CONTENT_INTEGRITY.md:59-61` 做的防御性重复，不是遗漏 |
| **`tests/` 不在仓库中** | `.gitignore` 忽略了 `tests/`，因此 §5.7.4 描述的 9 个 `verify_*_contract.py` 无法在克隆中查看 | 该节内容依据 `dev_doc/CODE_ORGANIZATION.md` 的列举与其命名/角色描述反推，标注为**推断**而非实测 |
| **`PACKAGE_CONTENTS.txt` 内容滞后** | 仍写"PopDrop v1.0.0 — 稳定版发布包" | 发布清单与实际版本脱节 |

**另外两处说明**：

- 本文所有 `file:line` 引用均相对仓库根目录，基于 commit `8d4e27c4`（2026-08-27）；
- 仓库中约 12.6 KB 的 `USAGE.md`、135 KB 的 `CHANGELOG.md`、45 KB 的 `DELIVERY_NOTES.md` 与多份 `dev_doc/*_TEST_REPORT.md` 均**未逐字通读**，只在需要核对功能边界与设计取舍时抽查引用。
