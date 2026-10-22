# 全能解压缩（OmniZip）— 技术栈与目录结构分析

- **分析对象**：`F:\downloads\omnizip\omnizip\1.0.108.0\`（程序主目录，v1.0.108.0）
- **产品名**：全能解压缩 / OmniZip（`setup.exe` 版本资源：ProductName=`omnizip`，FileDescription=`全能解压缩 安装程序`）
- **签名/归属主体**：`Copyright (C) jianleiyun.com All Rights Reserved.`，签名时间戳链为 GlobalSign CodeSign 2025
- **分析方法**：PE 资源解析 + 导出的调试符号名（MSVC 未 strip 符号）+ 内嵌开源许可清单 + 目录文件清单
- **分析日期**：2026-10-16
- **数据来源级别**：本文除标注「推断」外，全部为 **【实测·二进制静态解析】**，可逐条复核（复核路径见附 A）

---

## 0. TL;DR（结论先行）

1. **它不是 Electron、不是 Qt、不是 .NET，而是一个 32 位 Windows 原生 C++ 客户端**（MSVC 2022 / v143 工具链，全目录主体二进制均为 `x86 32-bit`）。唯一的 64 位模块是 `omnizip_shell64.dll`（资源管理器右键菜单扩展）。
2. **UI 层"三套并存"**，这是全目录最有信息量的发现：
   - **DuiLib**（原生 DirectUI，BSD-2）——主窗口 `ZipCompressWindow` / `ZipDecompressWindow` / `DeepCompressionWindow`，皮肤在 `skin.zip` 的 XML 里；
   - **字节跳动 Lynx**（Apache-2.0，`lynx.dll` + `resources/*.lynx.bundle`）——新一代声明式 UI，bundle 由 **React + React Router v6** 编译而来（ReactLynx 路线）；
   - **微软 WebView2**（固定版本 109.0.1518.78 x86）——登录、支付、反馈等 H5 弹窗。
3. **应用框架自研，代号 `QFrameWork`**：把登录（LoginService）、支付（PaymentService）、激励视频（RewardVideoService）、开屏广告（SplashAdService）、WebView2 封装（WebView2Impl）全部 Service 化，H5 与原生通过注入的 `window.external.AppCmd/GetSID/GetMID` 桥通信。
4. **能力内核全是成熟开源件**：压缩解压 = 7-Zip/LZMA SDK（`7z.dll`，含 Rar1/2/3/5 解码）+ bit7z；音视频 = FFmpeg 7.1；图片 = ImageMagick 7.1.2-13（**以子进程调用 `magick.exe`**）；PDF = QPDF；本地 AI = ONNX Runtime + OpenCV 4.8 + RetinaFace/ModNet 模型（证件照/抠图）。
5. **商业链路深度绑定 360 生态**：登录走 `coapi.browser.360.cn`、激励视频走 360 MediaV（`static-ssl.mediav.com`）、推广应用走 **360 OEM SDK**（`360OemSdk.dll` / `OEMSDK_SoftDownload`）、安装器还会静默装 360 安全浏览器/360 安全卫士。
6. **代码基线是 Chromium 式的自研工程结构**（`base/ components/ third_party/ ui/ webview/ installer/`），与 360 系产品（360 压缩/360 安全浏览器）同源痕迹明显。
7. **待注意的瑕疵**：生产包里带着 Lynx **开发运行时残留**——`resources/lynx_core_dev.js`（1.37 MB，dev 版）、字符串 `lynx-dev-server` / `__lynx_dev/poll_build`。
8. **"调起 Edge"的唯一入口**：`appmain.dll` 内 `webview/webview2/webview2_impl.cc` → `QFrameWork::WebView2Impl::Init()` 调用 `CreateCoreWebView2EnvironmentWithOptions`（即 WebView2 = Edge 内核，拉起 `msedgewebview2.exe`）。**机器没装 Edge WebView2 时，它用自带下发的 Edge Chromium 109 固定版内核**（`Microsoft.WebView2.FixedVersionRuntime.109.0.1518.78.x86.cab`，与 ffmpeg/magick 同一套运行时下发机制）。另有一条 `ShellExecuteExW` 外链路径（交给系统默认浏览器）。详见第 4 节专题。

---

## 1. 样本清单与逐个文件职责

| 文件 | 大小 | 位宽 | 实际职责 | 判定依据 |
|---|---|---|---|---|
| `appmain.dll` | 7.63 MB | x86 | **主程序全部业务逻辑**（UI 窗口、压缩管线、VIP 门禁、登录/支付/广告 Service） | 未 strip 的 C++ 符号：`ZipMainWindow`、`VipGateTrialManager`、`WebView2Impl@QFrameWork` 等 |
| `lynx.dll` | 14.57 MB | x86 | **Lynx 渲染引擎运行时**（含 Skia / QuickJS / ICU 74 / ANGLE） | 路径字符串 `third_party/skia/...`、`core/runtime/jsi/quickjs/...`、导出 `lynx_view_create` |
| `setup.exe` | 8.92 MB | x86 | 安装器（自带 DuiLib 界面 + `Install.xml` + 装机推广逻辑） | 字符串 `--silent-install --360se_pid=yasuo_0`、`360dm_install_bg_normal.png` |
| `omnizip_shell32.dll` | 0.14 MB | x86 | 32 位 Shell 扩展（右键菜单） | 导出 `DllGetClassObject/DllRegisterServer`、CLSID `{B3A7D8F2-1C4E-4A6B-9F3D-0E5C8B2A1D7E}` |
| `omnizip_shell64.dll` | 0.19 MB | **x64** | 64 位 Shell 扩展（右键盘符/文件） | 同上（32/64 各一，覆盖双环境 explorer） |
| `7z.dll` | 1.43 MB | x86 | **压缩解压内核**（7-Zip，Igor Pavlov，1999–2025） | 字符串 `Rar1/Rar2/Rar3/Rar5`、`LZMA2/7zAES/7zXZ/BZip2/PPMd/Deflate64` |
| `pdf_compress_facade.dll` | 0.94 MB | x86 | **PDF 压缩/加密门面**（QPDF 封装） | 符号 `QPDFPageObjectHelper`、`JpegImageOptimizer`、导出 `pdf_compress` / `pdf_is_encrypted` / `pdf_check_password` |
| `ffmpeg2.exe` | 86.77 MB | x86 | 音视频压缩/转码（外部进程） | `ffmpeg version git-2025-09-26-a54d6b1`，mingw32 x86 静态构建 |
| `ffprobe.exe` | 86.58 MB | x86 | 媒体信息探测（外部进程） | 同 FFmpeg 构建 |
| `magick.exe` | 23.97 MB | x86 | 图片压缩/转码（外部进程） | `ImageMagick 7.1.2-13 Q16-HDRI x86`（build 20260119） |
| `qfa_sdk.dll` | 2.62 MB | x86 | **行为埋点/崩溃上报 SDK** | 版本资源：`QFAnalytics SDK`，`Copyright (C) zbrowser.cn`，上报 `tracking.zbrowser.cn/api/dd`、`crash.zbrowser.cn` |
| `vcomp140.dll` | 0.16 MB | x86 | MSVC OpenMP 运行库（多线程压缩用） | `Microsoft® C/C++ OpenMP Runtime` 14.42.34433.0 |
| `skin.zip` | 3.35 MB | — | DuiLib 皮肤包（418 个文件：XML + 位图） | `DlgMain.xml`/`MsgBox.xml`/`strings/strings.xml`，节点为 DuiLib 语法 |
| `resources/` | — | — | Lynx 资源：`app/settings/about/feedback.lynx.bundle`、`lynx_core.js`(+`_dev.js`)、`icudtl.dat`(10.1 MB)、`static/image/*` | bundle 头部魔数 `d8780400 22192400` + React Router 字符串 |

> 目录里**没有**但代码引用的运行时资产（按需下载）：`libcef_x86.7z`、`ffmpeg_x86.7z`、`magick_x86.7z`、`idphoto_x86.7z`、`office_x86.7z`、`360OemSdk.dll`、`Microsoft.WebView2.FixedVersionRuntime.109.0.1518.78.x86.cab`。

---

## 2. 技术栈总览（分层）

| 层 | 技术选型 | 许可 | 证据 |
|---|---|---|---|
| 语言/运行时 | C++17+ / MSVC v143（VS2022）+ OpenMP | 专有 | `vcomp140.dll 14.42.34433`、MSVC 修饰名（`?AV<lambda_0>@...`） |
| 目标架构 | 主体 x86 32-bit；Shell 扩展 x86+x64 双份 | — | PE `Machine` 字段逐个校验 |
| 应用框架 | **自研 `QFrameWork`**（Service 化：Login/Payment/RewardVideo/SplashAd/WebView2） | 专有 | `LoginServiceImpl@QFrameWork`、`WebView2Impl@QFrameWork::AddAppCmdAPI` |
| 原生 UI | **DuiLib**（DirectUI，XML 皮肤驱动） | BSD-2 | `WindowImplBase@DuiLib`、`skin.zip` 内 XML |
| 声明式 UI | **字节跳动 Lynx**（ReactLynx：React 18 + React Router v6 → `.lynx.bundle`） | Apache-2.0 | `resources/*.lynx.bundle` 内 `reactrouter.com` 链接；`lynx_view_*` C API |
| Lynx 内部栈 | Skia（Ganesh/GL）+ HarfBuzz + ICU 74 + ANGLE + **QuickJS**（JSI 后端） | Apache-2.0 / 各自 | `third_party/skia/...`、`icu_74`、`jsi/quickjs/quickjs_runtime.cc` |
| H5 容器 | **WebView2 固定版本 109.0.1518.78 (x86)**；另有 CEF 3.2704.1414 按需下载 | 微软专有 / BSD-3 | `webview/webview2/*.cpp`、`libcef_x86.7z`、CEF 条目（见附 B） |
| 桥接协议 | `window.external.AppCmd(sid, module, command, params, extra, callback)`、`GetSID/GetMID/GetVersion`；Lynx 侧同款 `LynxWindowWin::AppCmd` | 专有 | appmain.dll 内注释串 `// external.AppCmd(...)` |
| 压缩解压 | **7-Zip / LZMA SDK**（`7z.dll`）+ **bit7z** 封装 | 公共领域(RAR 受限) / MPL-2.0 | `bit7z_engine.cc`、`Rar5` 解码器、`7zAES` |
| PDF | **QPDF**（+ 自研 `JpegImageOptimizer`） | Apache-2.0 | 符号 `qpdf::Writer`、`QPDF_Stream` |
| 音视频 | **FFmpeg 7.1**（2025-09-26 git 构建，x86 mingw 静态） | LGPL-2.1+（含 GPL/nonfree 开关） | `ffmpeg2.exe -version` 实测 |
| 图片 | **ImageMagick 7.1.2-13**（外部进程） | ImageMagick License | `magick.exe -version`；`compress/imagemagick/compress_image.cc` |
| 本地 AI | **ONNX Runtime + OpenCV 4.8.0** + RetinaFace（人脸检测）+ ModNet（人像抠图） | MIT / Apache-2.0 | `retinaface_runner.cc`、`modnet_runner.cc`、`[IdPhoto]` 日志串 |
| 网络 | libcurl + libcpr + cpp-httplib + BoringSSL(Chromium fork) | curl/MIT/OpenSSL | 内嵌许可清单 |
| 基础库 | Abseil、nlohmann/json 3.11.3、spdlog+{fmt}、glog(symbolize)、libevent 1.4.15、CityHash、SuperFastHash、double-conversion | 见附 B | 内嵌许可清单 |
| 崩溃/埋点 | **Crashpad**（Chromium 系）+ `QFAnalytics`（360 zbrowser） | Apache-2.0 / 专有 | `crashpad` 条目、`qfa_sdk.dll` |
| 更新/分发 | 自研 `installer/update/*` + 云端软推（`yasuo.jianleiyun.com/cfg/soft_list.json`）+ 360 OEM SDK | 专有 | `installer/update/update_mgr.cc`、`OEMSDK_SoftDownload` |

---

## 3. 关键判断（选型意图与代价）

### 3.1 为什么是 32 位 x86 主体

- **实测**：`appmain.dll`/`lynx.dll`/`setup.exe`/`ffmpeg2.exe`/`magick.exe`/`7z.dll`/`pdf_compress_facade.dll` 全部 `Machine=0x14C (x86)`，仅 `omnizip_shell64.dll` 为 x64。
- **推断（依据：目录内全部媒体/AI 资产均为 x86 预编译包名 `*_x86.7z`，且 `magick.exe` 为第三方官方 x86 构建，build 时间 20260119）**：选择 x86 是为了**直接复用现成的 32 位预编译二进制**（FFmpeg mingw x86、ImageMagick x86、OpenCV world 4.8 x86、onnxruntime x86），省掉自己交叉编译的成本；同时天然兼容 32/64 位 Windows 与老设备。
- **代价**：单进程 4 GB 地址空间 + 大文件解压/视频转码内存压力；这也是它把 FFmpeg/ImageMagick 拆成**独立子进程**的合理动机。

### 3.2 为什么三套 UI 并存（不是技术债，是分层策略）

| 场景 | 用的技术 | 推断动因 |
|---|---|---|
| 主窗口、压缩/解压/深度压缩对话框 | DuiLib | 存量代码继承（360 系产品线标配），自绘窗口、体积小 |
| 设置/关于/反馈/新版首页 | Lynx（ReactLynx） | **可热更新**（`LynxTemplateRenderer::LoadTemplateFromURL`、`lynx_load_meta_set_url`）、React 生态复用、开发效率 |
| 登录弹窗、VIP 支付中心、开屏广告、激励视频 | WebView2（+ H5） | 合规要求（登录/支付必须与线上页面一致）、运营可随时换活动页；且**无需发版**即可改 |

> 一句话：**DuiLib 保老代码，Lynx 做新 UI，WebView2 扛合规与运营**。三套并存换来的是迭代速度，代价是三套渲染栈都要维护、包体与内存占用上升。

### 3.3 AI 到底在哪里（避免被"AI 压缩"话术误导）

- `login_view/config.js` 与 `login_suc.html` 里的"AI 修图 / AI 生成 / AI 视频工具"**全部是外链**（`bangong.360.cn/ai-tools`、`kuaijianji.com`），不是本机能力。
- **真正的本地 AI 只有一处**：`components/compress/idPhoto/` 下的**证件照处理**——RetinaFace（人脸检测）+ ModNet（人像抠图），经 ONNX Runtime 推理，OpenCV 4.8 做图像预处理，模型在按需包 `idphoto_x86.7z` 里。
- 其余"压缩率提升"来自传统算法（LZMA/FFmpeg CRF/ImageMagick 量化），**没有任何本地生成式模型**。【实测：binaries 内无 diffusion/LLM 权重与相关运行时】

### 3.4 商业链路的 360 依赖（技术层面的硬绑定）

| 环节 | 依赖 | 证据 |
|---|---|---|
| 账号登录 | 360 账号体系 | `coapi.browser.360.cn/bai/login/cfg`、`dd.browser.360.cn/static/a/...`、`window.external.GetMID/GetSID` |
| 激励视频广告 | 360 MediaV | `static-ssl.mediav.com/js/reward_video_pc.min.js` |
| 推广应用下载 | 360 OEM SDK | `components/oem_sdk/sdk_dll_downloader.cc`、`OEMSDK_SoftDownload`、`https://yasuo.jianleiyun.com/cfg/soft_list.json` |
| 装机交叉推广 | 360 安全浏览器 / 360 安全卫士 | `--silent-install --360se_pid=yasuo_0`、`down.360safe.com/se/360se6_setup.exe`、`SOFTWARE\...\App Paths\360safe.exe` |
| 埋点/崩溃 | 360 浏览器体系（zbrowser.cn） | `qfa_sdk.dll`（`QFAnalytics SDK`） |
| 广告位治理 | 云端配置开关 | `channel_policy.cc`、`[AdChannelPolicy] field=ad_promotion_blocklist source=cloud_config` |

> 结论：**这是一个挂着自有品牌（jianleiyun.com）、跑在 360 技术底座与流量体系上的产品**。技术上"独立"，商业上强依赖 360 的账号、广告与分发通道。

### 3.5 值得指出的工程瑕疵

1. **生产包含 Lynx 开发运行时**：`resources/lynx_core_dev.js`（1.37 MB，另有正式版 `lynx_core.js` 140 KB）、字符串 `lynx-dev-server`、`__lynx_dev/poll_build`。属于把调试构建打进了正式包，至少是多占 1.4 MB 与潜在调试面暴露。
2. **符号未 strip**：`appmain.dll` 保留了完整的 C++ 类名/文件名/源码相对路径（`../../components/...`），等于把**模块划分与源码结构图**公开发布（本文分析的一大半信息就来自这里）。商业产品通常会剥离符号。
3. **构建机路径泄漏**：字符串 `C:\autobuild-components`（自动构建流水线目录）。
4. **7-Zip 的 RAR 解码许可**：`7z.dll` 含 `Rar1/Rar2/Rar3/Rar5` 解码器。7-Zip 官方发行版该部分受 **unRAR restriction**（不得用于逆向 RAR 压缩算法）约束，商业产品自带该 codec 需注意合规。

---

## 4. 专题：页面渲染链路 —— 哪部分在调起 Edge

> 回答"这里哪部分会设置/调起 Edge 浏览器处理页面"。**结论：全部集中在 `appmain.dll` 内编译的 `webview/webview2/*`（`QFrameWork::WebView2Impl`）+ `app/appmain/runtime_binary_manager.cc`（内核下发）三个源码单元**，WebView2 的内核即 Edge Chromium，调起的进程是 `msedgewebview2.exe`。

### 4.1 三条链路，别混在一起

| 链路 | 触发场景 | 代码位置 | 是否"调起 Edge" |
|---|---|---|---|
| **A. 内嵌 Edge 内核（WebView2）** | 登录、支付、开屏广告、激励视频、`ZhikeWindow` | `webview/webview2/webview2_impl.cc` → `QFrameWork::WebView2Impl::Init()` | **是**，拉起 `msedgewebview2.exe` 子进程，渲染在应用窗口内 |
| **B. 甩给系统默认浏览器** | 外链（`bangong.360.cn/ai-tools`、`kuaijianji.com`、活动页） | `ShellExecuteExW` / `ShellExecuteW`（`[LoginWindow] OnOpenUrl:`、`SplashAd:`、`[CommercialPkg]:`） | 取决于默认浏览器；默认是 Edge 则表现为"打开 Edge" |
| C. Lynx 自渲染 | 设置/关于/反馈/首页 | `lynx.dll`（不涉及浏览器） | 否 |

### 4.2 链路 A 的完整执行序列（按代码内日志串还原）

```
WebView2Impl::Init()
 ├─ GetFixedVersionRuntimePath()                 ← 决定用哪个 Edge 内核
 │   ├─ DIR_EXE= / DirectoryExists=
 │   ├─ has_msedgewebview2= ???                  ← 探测系统是否已装 Edge WebView2 Runtime
 │   ├─ 有 → browser_executable_folder=nullptr   ← 直接用系统装好的 Edge 内核
 │   └─ 无 → runtime_dir= ...\WebView2\...       ← 用自带的固定版内核目录
 │        └─ .cab → ExtractCabFile() （见 4.3）
 ├─ CreateCoreWebView2EnvironmentWithOptions(browser_executable_folder, userDataFolder=...)
 │      ★ 这一行才是真正"调起 Edge"的动作
 ├─ [EnvCompleted] CreateCoreWebView2Controller(parent_hwnd=...)
 ├─ put_IsVisible(TRUE/FALSE) → 挂进原生窗口
 └─ OnWebViewCreated → AddAppCmdAPI / AddFileAPI / AddRegistryAPI（注入桥，见 4.4）
```

**判定由宏 `has_msedgewebview2=` 主控**：机器上没装 Edge WebView2 Runtime 时，才走自重打包的固定版内核——这正是它把 **Edge Chromium 109 内核当成"运行时二进制"下发**的原因。

### 4.3 Edge 内核从哪来（与 ffmpeg/magick 同一套下发机制）

`app/appmain/runtime_binary_manager.cc` → `RuntimeBinaryManager` 统一管理 6 个运行时资产：

| 资产 | 用途 |
|---|---|
| `ffmpeg_x86.7z` | 音视频 |
| `magick_x86.7z` | 图片 |
| `libcef_x86.7z` | CEF 备用内核 |
| `idphoto_x86.7z` | 证件照模型 |
| `office_x86.7z` | Office 文件处理 |
| **`Microsoft.WebView2.FixedVersionRuntime.109.0.1518.78.x86.cab`** | **Edge 内核（固定版）** |

流程：`DownloadIfMissingAsync` → 下载 → `ExtractCabFile` → 校验（`Incomplete WebView2 extraction dir, removing:` 会清掉半成品目录）→ 落到 `runtime_dir`。

> 值得注意：**它不依赖用户机器上是否装了 Edge**，自带一份 Edge 109 内核（36 位 x86 版）。代价是老内核（109 对应 2023 年初的 Chromium 版本），存在长期不更新的安全风险。

### 4.4 同一条链路里注入的页面桥（能力比想象的大）

`webview2_impl.cc` 里通过 `AddScriptToExecuteOnDocumentCreated` 向每个页面注入以下 JS（原文可在二进制中直接读到）：

| 桥对象 | 暴露的能力 | 原生处理器 |
|---|---|---|
| `window.external.GetSID/GetMID/GetVersion` | 取会话 ID / 机器 ID / 版本 | `AddAppCmdAPI` |
| `window.external.AppCmd(sid, module, command, params, extra, callback)` | **通用命令通道**，走 `window.chrome.webview.postMessage`，带 `requestId` + 超时回调 | `components/ui/webview_window/handler/appcmd_window_handler.cc` → `HandleAppCmd` |
| `window.fs.*` | **文件系统全量操作**：readFile / writeFile / appendFile / readdir / mkdir / rmdir / unlink / stat / exists / rename / copyFile | `webview2_file_handler.cpp` |
| 注册表 | **注册表读写删**：createKey / deleteKey / keyExists / read/write/delete registry，支持 HKCR / HKCU / HKLM | `webview2_registry_handler.cpp` |

**这是本次逆向里风险面最大的一处**：任何在该 WebView 中打开的页面（包括远程 H5，如 `vip.jianleiyun.com` 的支付页）都能通过 `postMessage` 调用**文件读写 + 注册表写**。代码里未见针对远程域名的能力降级或 `NavigationStarting` 白名单拦截（见缺口声明第 8 项）。

### 4.5 窗口宿主：Edge 控件贴在哪

`components/ui/webview_window/win/webview_window_win.cc` → `QFrameWork::WebViewWindowWin`，做法是 **DuiLib 窗口 + 挖洞贴 Edge 控件**：

```
[ZhikeWindow] Loading default skin: compress/zhike.xml (Win8+)   ← 皮肤里定义 web_view_area 控件
[ZhikeWindow] web_view_area control not found in XML             ← 找不到就给默认矩形
[ZhikeWindow] Setting WebView bounds: ...                        ← 按控件矩形摆 WebView2
[WebViewWindowWin] InitWebView calling webview_->Init (WebView2)
```

对应 `login_view/`、`payment_view/`、`splash_ad_view/`、`reward_video_view/` 四个 H5 目录，均由该窗口宿主承载。

---

## 5. 可复用能力清单（自研桌面 mini-tool 参考）

按"**拿来即用程度**"排序，全部为本次实测确认存在的依赖，非推荐清单式猜测：

| 能力 | 复用物 | 许可 | 落地成本 | 备注 |
|---|---|---|---|---|
| 压缩/解压 | `7z.dll` + bit7z | LZMA SDK 公共领域；bit7z MPL-2.0（**动态链接 7z.dll 可规避 MPL 传染**） | 低 | 内置 40+ 格式、AES 加密；RAR 解码注意 unRAR 条款 |
| PDF 压缩/加密 | QPDF | Apache-2.0 | 低 | 可做 pdf_compress / 密码检测 / 重压缩 |
| 图片批处理 | ImageMagick 7 CLI | ImageMagick License（宽松，兼容商用） | 极低 | **他们就是当子进程调的**——最省事的工程范式 |
| 音视频 | FFmpeg | LGPL-2.1+（**注意该构建含 `--enable-gpl --enable-nonfree`**，商用需换成 LGPL-only 构建） | 低 | 直接抄"外部进程 + 参数模板"的做法 |
| 端侧 AI 推理 | ONNX Runtime + OpenCV | MIT / Apache-2.0 | 中 | 证件照=RetinaFace+ModNet 是现成的可抄用例 |
| 声明式 UI | Lynx（ReactLynx） | Apache-2.0 | 中高 | 中文资料少、需自己搭编译链（rspeedy）；换来的热更新能力对 C++ 桌面端很值 |
| 轻量原生 UI | DuiLib | BSD-2 | 低 | 成熟但社区停滞（duilib.com） |
| H5 弹窗容器 | WebView2 固定版本 | 微软专有（免费分发） | 低 | 固定版本 = 不依赖用户机器已装 Runtime |
| 崩溃采集 | Crashpad | Apache-2.0 | 中 | Chromium 同款，Windows 端成熟 |

**不建议照抄的两点**：
- **三套 UI 并存**：对个人/小团队是纯负担，选 Lynx **或** DuiLib/WebView2 二选一即可。
- **360 生态依赖链**（OEM SDK + MediaV + 账号）：属于渠道绑定，独立开发者拿不到同等条件。

---

## 6. 缺口声明（未取得的数据）

| 缺口 | 影响 | 获取路径 |
|---|---|---|
| Lynx SDK 精确版本号 | 无法判断其 Lynx 版本新旧与可用特性边界 | `lynx.dll` 无版本资源；bundle 内仅见 `Lynx sdk version 2.16` 的兼容性判断串。**建议**：启动程序后读 `lynx.__version` 或抓 `lynxSdkVersion` 上报字段 |
| Lynx bundle 编译工具链与脚手架版本 | 无法直接复现其构建流程 | bundle 头部含 `0.2.x` 段（格式版本），需对照 lynx-family/lynx 的 `lynx-template-bundle` 格式文档 |
| 完整源码模块树（仅见文件名级） | 只能到"模块划分"级别，无内部实现细节 | 逆向 `appmain.dll` PDB 符号（若可获取未 strip 的 PDB）或动态调试 |
| `setup.exe` 内 `Install.xml` 完整装机清单 | 无法完整枚举捆绑推广项 | 解包 setup.exe 资源段提取 `Install.xml` |
| IDPhoto 模型文件的具体来源与精度 | 无法判断是自训还是开源权重微调 | `idphoto_x86.7z` 未在本目录（按需下载），需抓包或断点取包 |
| 云端软推 `soft_list.json` 内容 | 无法确认推广应用的具体范围 | 请求 `https://yasuo.jianleiyun.com/cfg/soft_list.json`（需环境可达） |
| jianleiyun.com 与 360 的工商关联关系 | 只能确认"技术+流量绑定"，无法确认股权/授权关系 | 工商信息核验 + 360 官方渠道声明（本文不作推断） |
| 8 | 是否对**远程 H5** 同样注入 `fs` + 注册表全量桥 | 无法判断是该桥仅对本地页面开放、还是对 `vip.jianleiyun.com` 等远程页也开放，这直接决定安全暴露面大小 | 动态验证：启动程序 → 打开支付/广告页 → 在 WebView2 里执行 `typeof window.fs.readFile` 与 `typeof window.external.AppCmd`（或用 DevTools 协议挂载） |
| 9 | 是否存在 `NavigationStarting` 域名白名单拦截 | 静态字符串中未见白名单逻辑，但需动态确认 | 同上，尝试在 WebView 内跳转到任意外部域名，观察是否被拦截 |
| 10 | `msedgewebview2.exe` 的实际启动参数与 userDataFolder 落盘路径 | 影响缓存隔离与取证 | 运行后 `Get-Process msedgewebview2 | Select-Object -ExpandProperty Path` / 观察 `%LOCALAPPDATA%` 下新建目录 |

---

## 附 A｜证据明细（可复核）

| # | 结论 | 复核方式 | 原始证据 |
|---|---|---|---|
| 1 | 主体为 x86 32 位 | 读 PE `Machine` @ `e_lfanew+4` | appmain/lynx/setup/ffmpeg2/magick/7z/pdf 均为 `0x14C`；shell64 为 `0x8664` |
| 2 | 产品名与厂商 | PE 版本资源 | `ProductName=omnizip`、`FileDescription=全能解压缩 安装程序`、`FileVersion=1.0.108.0`、`LegalCopyright=Copyright (C) jianleiyun.com` |
| 3 | 使用 Lynx | appmain.dll 字符串 | `https://github.com/lynx-family/lynx`、`lynx_view_builder_*`、`LynxWindowWin`、`LynxTemplateRenderer`、`resources\homepage\main.lynx.bundle` |
| 4 | bundle 由 React 编译 | bundle 内字符串 | `reactrouter.com/v6/upgrading/future#v7_starttransition`、`ReactLynx::patch`、`useLynxGlobalEventListener` |
| 5 | Lynx 内部含 Skia/QuickJS/ICU74 | lynx.dll 字符串 | `../../third_party/skia/src/gpu/ganesh/gl/GrGLGpu.cpp`、`core/runtime/jsi/quickjs/quickjs_runtime.cc`、`icu_74` |
| 6 | 使用 WebView2 固定版 109 | appmain.dll 字符串 | `Microsoft.WebView2.FixedVersionRuntime.109.0.1518.78.x86.cab`、`webview2_impl.cc`、`AddAppCmdAPI@WebView2Impl@QFrameWork` |
| 7 | 使用 DuiLib | 符号 + skin.zip | `WindowImplBase@DuiLib`、`Notify@ZipCompressWindow@@MAEXAAUtagTNotifyUI@DuiLib@@@Z`、`DlgMain.xml` |
| 8 | 桥协议 AppCmd | appmain.dll 注释串 | `// external.AppCmd(sid, module, command, params, extra, callback)`、`// external.GetSID()`、`AppCmd expects exactly 6 arguments` |
| 9 | 压缩内核 | 7z.dll 字符串 | `Rar1/Rar2/Rar3/Rar5`、`7zAES`、`LZMA2`、`Copyright (c) 1999-2025 Igor Pavlov` |
| 10 | 媒体处理版本 | 执行 `--version` | FFmpeg `git-2025-09-26-a54d6b1`（x86 mingw）；ImageMagick `7.1.2-13 Q16-HDRI x86 20260119` |
| 11 | PDF 用 QPDF | pdf_compress_facade.dll 符号 | `QPDFPageObjectHelper`、`JpegImageOptimizer`、`pdf_compress`、`pdf_is_encrypted` |
| 12 | 本地 AI 仅证件照 | appmain.dll 日志串 | `[IdPhoto] RetinaFace CreateSession failed`、`[IdPhoto] ModNet ...`、`components/compress/idPhoto/internal/*` |
| 13 | 360 生态绑定 | appmain/setup/qfa_sdk 字符串 | `coapi.browser.360.cn/bai/login/cfg`、`static-ssl.mediav.com/js/reward_video_pc.min.js`、`OEMSDK_SoftDownload`、`--silent-install --360se_pid=dpjzyasuo`、`tracking.zbrowser.cn/api/dd` |
| 14 | 开发运行时残留 | 文件清单 + 字符串 | `resources/lynx_core_dev.js`(1.37 MB)、`lynx-dev-server`、`__lynx_dev/poll_build` |
| 15 | 构建机路径 | appmain.dll 字符串 | `C:\autobuild-components` |
| 16 | 签名/时间戳 | 证书链字符串 | `GlobalSign Offline R45 Timestamping CA 2025`、`GlobalSign TSA for CodeSign 2025` |
| 17 | 调起 Edge 的位置 | appmain.dll 符号 + 日志串 | 源码路径 `../../webview/webview2/webview2_impl.cc`、`GetFixedVersionRuntimePath begin thread_id=`、`[WebView2][Init] CreateCoreWebView2EnvironmentWithOptions userDataFolder=`、`[WebView2][EnvCompleted] CreateCoreWebView2Controller parent_hwnd=` |
| 18 | 用系统 Edge 还是自带内核 | appmain.dll 日志串 | `has_msedgewebview2=`、`[WebView2][Runtime] runtime_dir=`、`[WebView2][Init] browser_executable_folder=nullptr` |
| 19 | Edge 内核随包下发 | appmain.dll 字符串 | `Microsoft.WebView2.FixedVersionRuntime.109.0.1518.78.x86.cab`、`[RuntimeBinaryManager] Extracting cab:`、`Incomplete WebView2 extraction dir, removing:`、`DownloadIfMissingAsync`（`../../app/appmain/runtime_binary_manager.cc`） |
| 20 | 注入页面桥的原文 | appmain.dll 内嵌 JS | `window.external.AppCmd = function (sid, module, command, params, extra, callback)`、`window.chrome.webview.postMessage(message)`、`window.fs = { readFile: ...`、`HandleReadRegistry` / `HandleWriteRegistry` / `Root key, sub key and value name are required` |
| 21 | Edge 控件挂载方式 | appmain.dll 日志串 | `[ZhikeWindow] web_view_area control not found in XML`、`[ZhikeWindow] Setting WebView bounds:`、`[WebViewWindowWin] InitWebView calling webview_->Init (WebView2)`（`components/ui/webview_window/win/webview_window_win.cc`） |
| 22 | WebView2 用微软 WRL/COM 直连 | appmain.dll 符号 | `WRL::RuntimeClass<...ICoreWebView2CreateCoreWebView2EnvironmentCompletedHandler>`、`CreateCoreWebView2EnvironmentWithOptions`（静态链接 WebView2Loader，`Microsoft.MSEdgeWebView.Loader` 为载入器 ETW 提供者名） |
| 23 | 另有"甩给系统浏览器"路径 | appmain.dll 日志串 | `[LoginWindow] OnOpenUrl:`、`SplashAd: ShellExecuteExW failed:`、`[CommercialPkg] ShellExecuteExW failed:`、`LaunchDefaultAppsSettingsForExtension` |

---

## 附 B｜第三方组件与许可清单（源自程序自带许可声明，非本文推测）

| 组件 | 声明版本 | 许可 |
|---|---|---|
| nlohmann/json | v3.11.3 | MIT |
| spdlog（含 {fmt}） | latest / bundled | MIT |
| libcpr (C++ Requests) | latest | MIT |
| cpp-httplib | latest | MIT |
| CityHash | 1.1.1 | MIT |
| ONNX Runtime | latest | MIT |
| Abseil-cpp | commit 8aa88cd | Apache 2.0 |
| QPDF | latest | Apache 2.0 |
| OpenCV | **4.8.0** | Apache 2.0 |
| Crashpad | latest | Apache 2.0 |
| Lynx | latest | Apache 2.0 |
| DUILib | latest | BSD 2-Clause |
| NASM | latest | BSD 2-Clause |
| double-conversion | commit 32bc443 | BSD 3-Clause |
| libevent | 1.4.15 | BSD 3-Clause |
| Symbolize (google/glog) | commit b70ea80 | BSD 3-Clause |
| CEF (Chromium Embedded Framework) | **3.2704.1414** | BSD 3-Clause |
| BoringSSL | Chromium fork | OpenSSL/ISC/MIT |
| curl / libcurl | 2024 | curl License |
| zlib | 1.3.0.1 | zlib |
| FreeType | 2.13.3 | FTL |
| libjpeg (IJG) | Release 10 | IJG |
| bit7z | latest | MPL 2.0 |
| FFmpeg | latest | LGPL 2.1+ |
| LZMA SDK | — | Public Domain |
| SuperFastHash | — | Public Domain 组 |
| ImageMagick（`magick.exe`） | 7.1.2-13 | ImageMagick License（**未在其许可清单中声明**，疑漏） |
| Microsoft WebView2 Fixed Runtime | 109.0.1518.78 | 微软专有（**未声明**） |
| 7-Zip `7z.dll`（RAR 解码部分） | 1999–2025 | 7-Zip License + **unRAR restriction**（**未单列**） |

---

## 附 C｜一句话总结

**技术上是"Chromium 式自研 C++ 工程 + 7-Zip/FFmpeg/ImageMagick/QPDF/ONNX 开源内核 + DuiLib/Lynx/WebView2 三套 UI"，商业上是"自有品牌 + 360 底座"的捆绑式桌面工具**——它的可学习点不在 UI，而在**用外部进程（ffmpeg/magick）+ 按需 7z 模块包**把体积与依赖复杂度压下来的工程做法。
