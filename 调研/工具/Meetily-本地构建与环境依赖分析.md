# Meetily 开源项目分析：本地构建路径、环境依赖与限制清单

> **分析对象**：`github.com/Zackriya-Solutions/meetily`（旧名 `meeting-minutes`，同一仓库）
> **版本**：v0.4.1（Release 发布于 2026-09-12）
> **采集日**：2026-10-15
> **方法**：GitHub 原始文件（README / docs/BUILDING.md / docs/building_in_linux.md / docs/architecture.md / docs/GPU_ACCELERATION.md / frontend/package.json / frontend/src-tauri/Cargo.toml）+ Release 页 + 官网 FAQ + 第三方实测文章交叉核对
> **本文回答三个问题**：① 怎么在本地构建；② 有哪些限制；③ 是否有环境依赖
> **姊妹文档**：商业化现状见《Meetily-商业化现状与付费产品核查.md》；自动下载资产的许可与商用核查见《Meetily-自动下载资产的许可与商用核查.md》

---

## 0. 结论先行（TL;DR）

| # | 判断 | 依据强度 |
|---|---|---|
| 1 | **它是「Tauri 单进程桌面应用」，不是 Web 服务。** Rust 核心 + Next.js 前端 + 本地 SQLite，无服务端、无 Docker。仓库里那个 `backend/`（Python FastAPI + Docker Compose + Postgres）是 **legacy 归档，当前架构完全不用它** —— 大量中文教程仍按 Docker 部署，全是错的 | 【实测】Cargo.toml + docs/architecture.md |
| 2 | **只想用，别编译。** Windows 有 `x64-setup.exe`、macOS 有 `aarch64.dmg`，装了就能跑，模型在应用内下载。**只有 Linux 必须源码构建**（官方无 Linux 二进制，官网称「原生 Linux 桌面版开发中」） | 【实测】Release 资产 |
| 3 | **真正的前置依赖是「Rust + C++ 工具链」，不是官方 FAQ 里那套 Python。** 必需的只有：Rust ≥1.77、Node、`pnpm@9.15.9`（锁死版本）、CMake、C++ 编译器、libclang。**Python 3.10+ 已不是依赖；FFmpeg 也不再需要你手装**（由 `ffmpeg-sidecar` 自管） | 【实测】Cargo.toml + BUILDING.md |
| 4 | **最容易卡住的三个点**：① Windows 缺 LLVM/libclang → bindgen 报 `Unable to find libclang`（**官方文档完全没写**，但 llama-helper/whisper 的 bindgen 需要）；② 用 npm/yarn 替代 pnpm → `--frozen-lockfile` 流程直接失败；③ 首次构建**必须联网**（cargo 要拉 git 依赖 + 构建脚本要下载预编译二进制） | 【实测】Cargo.toml 依赖树；【推断·依据】下载逻辑 |
| 5 | **性能天花板取决于「有没有装开发 SDK」，不是「有没有显卡」。** 只装驱动不装 CUDA Toolkit / ROCm / Vulkan SDK，脚本一律回退纯 CPU，且不报错 —— 很多人「有显卡却跑 CPU 模式」就是这个原因 | 【实测】docs/BUILDING.md 明写 |
| 6 | **社区版被有意留了功能缺口。** 说话人分离（speaker diarization）、PDF/DOCX 高级导出、自动会议检测、日历集成、自托管团队部署全部划给 **PRO（不同代码库、闭源）**。MIT 只覆盖社区版 | 【实测】README「Meetily PRO」章节 |
| 7 | **对二开/白牌不友好。** 社区版无多用户、单实例锁（`tauri-plugin-single-instance`）、无云同步；作者是公司（Zackriya Solutions）主导而非基金会治理。Linux 上游支持不足已被独立 fork（Parley / Meetily-Local）证实 | 【实测】Cargo.toml + fork README |

**一句话**：构建门槛不高但依赖链条长（Rust→C++→ONNX→CUDA 四层），**Windows 本地源码构建默认只能跑 CPU**；用它「自用」很省事，用它「做生意」要面对开源版被刻意留白的现实。

---

## 1. 项目基本盘

| 指标 | 数值 | 口径 / 来源级别 |
|---|---|---|
| 仓库 | `Zackriya-Solutions/meetily`（曾用 `meeting-minutes`，旧链接会重定向到同一仓库） | 【实测】仓库页 |
| 当前版本 | **v0.4.1** | 【实测】GitHub Release |
| 发布日 | 2026-09-12 | 【实测】Release 页时间戳 |
| 最近提交 | 2026-09-10（`docs(build): correct Windows CPU compatibility guidance`） | 【实测】仓库文件列表 |
| 许可 | **MIT**（社区版） | 【实测】README + Cargo.toml `license = "MIT"` |
| 官方二进制 | Windows `meetily_0.4.1_x64-setup.exe`；macOS `meetily_0.4.1_aarch64.dmg`。**Linux 无官方包** | 【实测】Release 资产清单 |
| Star 数 | **口径冲突，未取得权威当前值**：官网自称 12,730+；第三方文章分别写 18K+ / 23.9K+ | 【未取得】见附 B |
| 安装包体积 | 约 150 MB（含模型，无需另下模型文件） | 【二手】中文评测 |
| 定位 | 隐私优先的本地 AI 会议助手 / 纪要工具，bot-free（不派机器人进会议，直接抓系统音频） | 【实测】README |
| 商业结构 | 社区版（MIT，免费）+ PRO（闭源、另一套代码库、付费）+ Enterprise | 【实测】README |

**核心能力**：本地实时转写（Whisper / Parakeet）+ 本地或云端 LLM 摘要（内置 llama-helper / Ollama / Claude / Groq / OpenRouter / 自建 OpenAI 兼容端点）+ 音频文件导入（Beta）+ 音频混音（麦克风 + 系统音频，带 ducking）。

---

## 2. 架构：为什么它「好构建」也「容易卡」

### 2.1 组件与依赖（五块）

`docs/architecture.md` 明确拆成五块，**全部在同一个 Rust 进程里，前端不碰音频与推理**：

| 组件 | 职责 | 关键 crate / 技术 |
|---|---|---|
| Tauri Core | 窗口、事件、把 Rust 能力暴露给前端 | `tauri 2.6.2`（features: `macos-private-api`、`protocol-asset`、`tray-icon`） |
| Audio Engine | 麦克风 + 系统音频采集、混音、ducking、EBU R128 归一化、RNNoise 降噪 | `cpal 0.15.3`（git patch）、`ebur128`、`nnnoiseless`、`rubato`（重采样）、`realfft` |
| Transcription Engine | 本地实时转写 | **Whisper**：`whisper-rs 0.13.2`（走 whisper.cpp/ggml + CMake 编译）；**Parakeet**：`ort 2.0.0-rc.10`（ONNX Runtime）+ VAD `silero_rs`（git） |
| Database | 会议元数据、转写、摘要 | `sqlx 0.8` + **SQLite**（不是 Postgres） |
| Summary Engine | LLM 摘要 | `llama-helper/` 独立 crate（`llama-cpp-2`）作为 **Tauri sidecar**；外部走 `reqwest` 调用各厂商 API |

### 2.2 仓库目录里的两个陷阱

| 路径 | 是什么 | 陷阱 |
|---|---|---|
| `backend/` | **Legacy Backend Archive**：Python FastAPI + Docker Compose + 独立 whisper-server | 自称「仅供历史参考，不应用于新装、生产部署」【实测】。**任何让你 `docker compose up` 的 Meetily 教程都是过期的** |
| `llama-helper/` | 独立 Rust crate，编译成 sidecar 二进制塞进 `src-tauri/binaries` | 它引入 `llama-cpp-2` → **bindgen → libclang** 依赖，是 Windows 构建最常见的失败点 |
| 根 `Cargo.toml` + `Cargo.lock` | Rust workspace 锁文件 | 已纳入版本管理，说明构建可复现性被在意【实测】 |

**真实依赖链长度**（这也是「卡点」的来源）：

```
Node/pnpm  →  Next.js 14 前端产物
     ↓
Cargo (Rust ≥1.77)  →  whisper-rs  →  whisper.cpp/ggml  →  **CMake + C++ 编译器**
     ↓                                →  bindgen  →  **LLVM / libclang**
     ↓              →  llama-cpp-2  →  同上
     ↓              →  ort (ONNX Runtime)  →  预编译动态库（Windows 动态加载）
     ↓              →  ffmpeg-sidecar  →  外部 ffmpeg 二进制
Tauri CLI  →  打包 .exe / .dmg / .AppImage
```

**四层外部工具链（Node / Rust / C++ / GPU SDK）任一缺失，构建就停在某一层**，而报错信息通常只指向最后一层。

---

## 3. 本地构建：分平台可执行步骤

> 来源：`docs/BUILDING.md`（权威）+ `docs/building_in_linux.md`（Linux 细化）+ `frontend/package.json`（真实脚本入口）
> ⚠️ 全平台第一步统一是：**把 pnpm 固定到 9.15.9**，否则 `--frozen-lockfile` 会因 lockfile 版本不匹配失败。

```bash
npm install -g pnpm@9.15.9
```

### 3.1 Windows（你当前的环境，写最细）

**前置清单**

| 依赖 | 版本/说明 | 来源 |
|---|---|---|
| Windows 10/11 x64 | CPU 需支持 **AVX2**（发行包走 `x86-64-v2`，AVX-512 被禁用） | 【实测】README 兼容性说明 |
| Rust | rustup 安装 stable，MSVC toolchain（`stable-x86_64-pc-windows-msvc`），**≥1.77** | 【实测】`rust-version = "1.77"` |
| Visual Studio Build Tools | 勾选 **「使用 C++ 的桌面开发」** 工作负载（提供 `link.exe` 与 MSVC 编译 ggml） | 【实测】BUILDING.md |
| CMake | whisper.cpp/llama.cpp 均由 CMake 构建（whisper-rs 要求 ≥3.10） | 【实测】BUILDING.md + whisper-rs 构建机制 |
| **LLVM / libclang** | **官方 BUILDING.md 未列，但用 Cargo 构建必然需要**。设 `LIBCLANG_PATH` 指向含 `libclang.dll` 的 bin 目录 | 【推断·依据】llama-cpp-2/whisper-rs 的 bindgen 流程 |
| Node.js | 官方未标版本；Next 14 实际要求 ≥18.17（官网 FAQ 写 18+） | 【二手】 |
| pnpm | **精确 9.15.9** | 【实测】BUILDING.md |
| （可选）CUDA Toolkit | **仅当**要 `--features cuda` 时；只装驱动无效 | 【实测】 |
| （可选）Vulkan SDK + OpenBLAS | 仅当要 `--features vulkan` 时；需 `VULKAN_SDK` + `BLAS_INCLUDE_DIRS` 双变量 | 【实测】 |

**构建命令**

```powershell
git clone https://github.com/Zackriya-Solutions/meetily.git
cd meetily\frontend
pnpm install --frozen-lockfile

pnpm tauri:dev              # 开发（热重载）
pnpm tauri:build            # 生产打包 —— 默认纯 CPU
pnpm tauri:build:cuda       # 有 NVIDIA + CUDA Toolkit
pnpm tauri:build:vulkan     # AMD/Intel + Vulkan SDK
pnpm tauri:build:openblas   # 仅 CPU 但想快一点（需 BLAS_INCLUDE_DIRS）
```

**环境变量示例**

```powershell
setx LIBCLANG_PATH "C:\Program Files\LLVM\bin"
setx CUDA_PATH "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.x"
```

**关键提示**：`pnpm tauri:build`（默认）= CPU-only。想要 GPU 必须**显式换脚本或加 feature** —— 这跟 macOS「自动开 Metal」完全不同。官方发行版安装包则用 Vulkan 构建，普通用户不用管。

### 3.2 macOS

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install cmake node pnpm
# 还需 Xcode Command Line Tools：xcode-select --install
# 还需 Rust：curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

cd meetily/frontend
pnpm install --frozen-lockfile
pnpm tauri:dev
pnpm tauri:build     # Metal + CoreML 自动启用，无需额外配置
```

### 3.3 Linux（只有这条路，没有官方二进制）

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install build-essential cmake git
# Fedora/RHEL: sudo dnf install gcc-c++ cmake git
# Arch:        sudo pacman -S base-devel cmake git

git clone https://github.com/Zackriya-Solutions/meetily.git
cd meetily/frontend
pnpm install --frozen-lockfile
./build-gpu.sh      # 生产；开发用 ./dev-gpu.sh
```

**输出位置**：`src-tauri/target/release/bundle/appimage/Meetily_<version>_amd64.AppImage`

**脚本会自动做的事**：找 `package.json`（根目录或 `frontend/` 均可）→ 调 `scripts/auto-detect-gpu.js` 探测硬件 → 编译 `llama-helper` sidecar 并按 target triple 复制到 `src-tauri/binaries` → 带 feature 调 `tauri build`。

**是否还能在根目录跑 `./build-gpu.sh`**：官方两处文档说法不一致（README 写 `cd frontend`，BUILDING.md 说脚本兼容根目录），**以 `frontend/` 为准最稳**。

### 3.4 GPU 加速矩阵（Linux/Windows 判定规则）

| 优先级 | 硬件 | 检测条件 | feature | 官方标称加速 |
|---|---|---|---|---|
| 1 | NVIDIA CUDA | `nvidia-smi` 存在 **且**（`CUDA_PATH` 或 `nvcc` 可用） | `--features cuda` | 5–10× |
| 2 | AMD ROCm | `rocm-smi` 存在 **且**（`ROCM_PATH` 或 `hipcc` 可用） | `--features hipblas` | 4–8× |
| 3 | Vulkan | `vulkaninfo` 存在 **且** `VULKAN_SDK` **且** `BLAS_INCLUDE_DIRS` 均已设 | `--features vulkan` | 3–6× |
| 4 | OpenBLAS | 仅需 `BLAS_INCLUDE_DIRS` | `--features openblas` | 1.5–2× |
| 5 | CPU | 以上皆无 | 无 | 1×（基线） |

**强制覆盖**：`TAURI_GPU_FEATURE=cuda|vulkan|hipblas|openblas|""`（空字符串=纯 CPU）配合 `./build-gpu.sh`。
**macOS 例外**：Metal + CoreML 在 `Cargo.toml` 里写死默认启用，不参与上述探测。

### 3.5 构建期与运行期的「隐性联网依赖」

| 时点 | 联网原因 | 证据 |
|---|---|---|
| 构建期 | Cargo 需拉取 **git 依赖**：`ffmpeg-sidecar`、`silero_rs`、`cidre`、`esaxx-rs`、以及 `cpal` 的 patch 分支 | 【实测】Cargo.toml 的 git 源 |
| 构建期 | `[build-dependencies]` 含 `reqwest` + `zip` + `tar` + `xz2` + `sha2` + `which`，是典型的**构建脚本下载并解压预编译二进制**（ffmpeg / ONNX Runtime 等）的组合 | 【推断·依据】依赖组合特征 |
| 运行期（首次） | 下载 Whisper / Parakeet 模型（应用内弹窗下载，支持断点续传） | 【实测】README + 第三方评测 |
| 运行期（可选） | Ollama 拉取本地模型；或调用云端 LLM API 时会把**转写文本**（非音频）发出去 | 【实测】README |

**结论**：**离线环境无法完成首次源码构建**，官方「初始设置后无需联网」的说法只适用于二进制安装包路径。

---

## 4. 环境依赖全景清单

### 4.1 必需（缺一个就构建失败）

| 依赖 | 版本要求 | 备注 |
|---|---|---|
| Rust + Cargo | **≥1.77**（MSVC toolchain on Windows） | 【实测】Cargo.toml |
| Node.js | 未在 BUILDING.md 标注；Next 14 实际需 ≥18.17 | 【二手】 |
| pnpm | **恰好 9.15.9** | 用 npm / yarn 会破坏 frozen lockfile |
| CMake | ≥3.10（whisper-rs 要求；建议 3.28+） | ggml/whisper.cpp 编译 |
| C++ 编译器 | Windows：VS Build Tools「桌面 C++」；Linux：`build-essential`；macOS：Xcode CLT | 编译 ggml 与 llama.cpp |
| libclang / LLVM | bindgen 使用，需 `LIBCLANG_PATH` | **官方文档未列**，Windows 最常见失败原因 |
| 系统音频采集权限 | macOS：「屏幕录制」权限（系统音频归入该类）；Windows：WASAPI loopback / 立体声混音 | 【实测】README + 第三方实测 |

### 4.2 可选（决定性能与摘要能力）

| 依赖 | 作用 |
|---|---|
| CUDA Toolkit / ROCm / Vulkan SDK / OpenBLAS | GPU 加速，缺则回退 CPU |
| Ollama | 本地 LLM 摘要（**v0.4 起内置 llama-helper 后不再是必需**） |
| Claude / Groq / OpenRouter / 自建 OpenAI 兼容端点 API Key | 云端摘要；会上传转写文本 |

### 4.3 已废弃（旧教程里的幽灵依赖）

| 依赖 | 状态 |
|---|---|
| Python 3.10+ / venv / pip | **当前架构不需要**。`backend/` 为 legacy 归档 |
| PostgreSQL | 不需要，现为 SQLite |
| Docker / Docker Compose | 不需要 |
| 手工安装 FFmpeg | 不需要（`ffmpeg-sidecar` 自管）；`symphonia` 也承担本地音频解码（aac/mp4/mp3/flac/ogg/vorbis/wav） |

---

## 5. 限制清单

### 5.1 产品能力限制（社区版 vs PRO）

| 能力 | 社区版（MIT） | PRO（闭源付费） |
|---|---|---|
| 实时转写 / 本地摘要 | ✅ | ✅（更高精度模型） |
| **说话人分离（speaker diarization）** | ❌ | 计划中（README 写 mid-June），**且 README 顶部又把 diarization 列为卖点 —— 自相矛盾** |
| 高级导出 PDF / DOCX / MD | ❌ | ✅ |
| 自定义摘要模板 | ❌ | ✅ |
| 自动检测并加入会议 | ❌ | ✅ |
| 日历集成 | ❌ | 计划中 |
| 多用户 / 自托管团队部署 | ❌（单机单用户） | ✅ |
| 音频文件保存 | **release 版默认禁用**（只留实时转写） | — |
| 云同步 | 无（隐私设计取舍） | 自托管集中存储 |

### 5.2 平台与硬件限制

| 平台 | 限制 |
|---|---|
| **macOS** | ① 系统音频走 ScreenCaptureKit，**需 macOS 13+**；② `.dmg` **无 Apple 公证签名**，首次启动被 Gatekeeper 拦截，需去「隐私与安全性」手动放行；③ **官方包只有 `aarch64`（Apple Silicon），Intel Mac 无官方二进制**，只能源码构建；④ 蓝牙麦克风曾有冷启动/断连问题（v0.4.1 修复） |
| **Windows** | ① 发行包**要求 AVX2**（`x86-64-v2`，AVX-512 显式关闭）→ 2013 年前的老 CPU 不支持；② **CUDA 默认不启用**，要 GPU 就得源码构建 + CUDA Toolkit；③ WASAPI 独占模式可能与其他应用冲突；④ 多声道麦克风阵列（>2 声道）因相位干扰**只取前 2 声道** |
| **Linux** | ① **无官方二进制包**，只能源码构建（AppImage）；② 系统音频捕获是上游弱项 —— 独立 fork Parley 明确写「原版需要 cpal/BlackHole 式虚拟设备，本 fork 重写为原生 PipeWire 捕获」，说明**上游 Linux 系统音频体验不可靠**；③ 需 `NO_STRIP=true` 才能避免 AppImage 符号缺失 |
| 通用 | 内存 8 GB 起 / 16 GB 推荐；**单实例锁**（不能同时开两个）；无内置多用户 |

### 5.3 构建与工程限制

| # | 限制 | 影响 |
|---|---|---|
| 1 | 依赖链条四层（Node → Rust → C++/CMake → GPU SDK） | 首次构建失败定位成本高 |
| 2 | **官方文档未提 libclang** | Windows 构建最常见的硬失败（`Unable to find libclang`） |
| 3 | 文档内部不一致 | README 的 quick start 与 BUILDING.md 的脚本路径/行为描述不同；`clean_run.sh` / `clean_build_windows.bat` 等旧入口已被 `dev-gpu.sh` / `build-gpu.sh` 取代 |
| 4 | `build-gpu.ps1` 只出现在 Cargo.toml 注释里 | Windows 侧脚本支持情况不明（官方 BUILDING.md 未收录） |
| 5 | 仓库残留 legacy `backend/`（Python + Docker + Postgres） | 搜到的中文教程大量按 Docker 部署，**照做必错** |
| 6 | pnpm 锁版本 9.15.9 + `--frozen-lockfile` | 换包管理器即失败 |
| 7 | 构建期强依赖网络（git 依赖 + 构建脚本下载二进制） | 内网/离线环境不可构建 |
| 8 | 缺 SDK 只回退不报错 | 「有显卡却跑 CPU」难以自查 |

### 5.4 授权与治理限制

| # | 限制 | 说明 |
|---|---|---|
| 1 | **「开源核心 + 封闭增值」分层** | 社区版 MIT 可商用，但 PRO 是**另一套代码库**，不开放。社区版的功能留白（diarization、导出、团队）正是 PRO 卖点 |
| 2 | 公司主导而非社区治理 | 由 Zackriya Solutions 主导路线图，`Meetily PRO` 推广与社区版发布节奏绑定（例如优惠码有效期「直到下个社区版发布」） |
| 3 | 已有活跃独立 fork | `Hankanman/Meetily-Local (Parley)`：Linux-only、GPUI 原生壳、去掉 Tauri+Next.js、whisper-rs 0.13→0.16。**是「上游 Linux 支持不足」的社区验证** |
| 4 | 遥测 | 依赖 `posthog-rs`，PRIVACY 政策已改为 **opt-in 默认关闭**，但代码路径存在 |

---

## 6. 官方文档与实际仓库的口径冲突（必读）

第三方教程（含官网自家 FAQ）与当前代码已明显脱节，**以仓库 `frontend/` + `docs/BUILDING.md` 为准**：

| 说法出处 | 说法 | 实际 |
|---|---|---|
| 官网 FAQ | 「最低：8 GB RAM、4 核、10 GB 存储，**Node.js 18+、Python 3.10+、FFmpeg**」 | Python 与 FFmpeg **已不在依赖链**；Node 版本 BUILDING.md 未标 |
| 官网 FAQ | 「快速开始：`npm install && npm run setup` → `npm start`」 | 实际是 `pnpm install --frozen-lockfile` → `pnpm tauri:dev/build`；无 `setup` 脚本 |
| 官网 FAQ | 「摘要需要 Ollama」 | v0.4 起**内置 llama-helper** 本地引擎，Ollama 降级为可选 |
| 中文教程 | 「Docker 部署 / 起 Postgres」 | `backend/` 是 legacy 归档，官方明示不用于新装 |
| 中文教程 | 「编译前需装 Python 3.10」 | 不需要 |
| README 标题 | 把 **speaker diarization** 列为核心能力 | PRO 章节写它仍是 PRO 的「计划中」功能；社区版没有 |
| README macOS | 只给 `aarch64.dmg` | Intel Mac 无官方包（也未在任何文档中说明补救路径） |

---

## 7. 可执行判断

### 7.1 如果你要「用」

- **Windows / Apple Silicon Mac**：直接下安装包，别编译。5 分钟可用，模型在应用内下载。
- **Linux**：要么源码构建（接受 AppImage + 系统音频不确定性），要么走 Parley fork（Linux-first、原生 PipeWire）。
- **Intel Mac**：官方无包，只能构建或放弃。
- 首次跑通后记得：Ollama 或内置 llama-helper 二选一；不想要遥测就保持默认（已是 opt-in 关闭）。

### 7.2 如果你要「二开 / 白牌 / 做产品」

| 判断 | 理由 |
|---|---|
| ❌ 不适合直接拿来当多用户 SaaS 底座 | 单实例、单用户、SQLite 本地库、无云同步。团队能力在 PRO（闭源） |
| ⚠️ 适合做垂直场景的本地客户端外壳 | MIT 允许商用，但要接受：功能天花板被 PRO 划走，且上游可能随时把你在意的能力纳入 PRO |
| ✅ 值得借鉴的是**工程选型**而非代码 | 「Tauri + Rust 单进程替代 Electron + Python 双进程」是这类工具的正确方向：消除跨进程延迟、单二进制分发、隐私可审计 |
| 🔍 值得注意的品类信号 | ① 官方为「Linux 用户」单独拉 waitlist（`/granola-for-linux`）说明 Linux 桌面会议工具是真空；② 社区 fork 立刻出现并转向 PipeWire/GPUI —— 需求真实存在；③ 但变现路径被验证为「开源引流 + PRO 收口」，纯开源难直接变现 |

### 7.3 如果你要「评估这条赛道的构建成本」（给机会判断用）

- **技术门槛中等偏上**：不是写个 UI 就行，核心工作量在音频管线（系统音频采集 + 混音 + VAD + 重采样）和模型集成（whisper.cpp / ONNX / llama.cpp 三套 C++ 生态）。
- **平台适配是大头**：三个平台三套系统音频方案（ScreenCaptureKit / WASAPI loopback / PipeWire-or-virtual-device），且各有权限模型 —— 这是「看起来小、做起来重」的典型。
- **依赖风险**：核心能力绑在 C++ 生态（whisper.cpp、ggml、llama.cpp、ONNX Runtime）上，构建环境脆弱（CMake + libclang + GPU SDK），CI 成本被低估。

---

## 附 A：数据明细

| 指标 | 数值 | 口径 | 来源级别 | 采集日 |
|---|---|---|---|---|
| 仓库名 | `Zackriya-Solutions/meetily`（旧 `meeting-minutes`） | 当前主名 | 【实测】 | 2026-10-15 |
| 版本 | v0.4.1 | 最新 Release tag | 【实测】 | 2026-10-15 |
| 发布日 | 2026-09-12 | Release 时间戳 | 【实测】 | 2026-10-15 |
| 最近提交 | 2026-09-10 | 仓库文件列表 | 【实测】 | 2026-10-15 |
| LICENSE | MIT | Cargo.toml `license` 字段 + README | 【实测】 | 2026-10-15 |
| Rust 最低版本 | 1.77 | `rust-version = "1.77"` | 【实测】 | 2026-10-15 |
| 前端框架 | Next.js ^14.2.25 + React 18 | package.json | 【实测】 | 2026-10-15 |
| 桌面框架 | Tauri 2.6.2 | Cargo.toml | 【实测】 | 2026-10-15 |
| 转写引擎 | whisper-rs 0.13.2（Whisper） / ort 2.0.0-rc.10（Parakeet ONNX） | Cargo.toml | 【实测】 | 2026-10-15 |
| 数据库 | SQLite（sqlx 0.8） | Cargo.toml + architecture.md | 【实测】 | 2026-10-15 |
| 音频栈 | cpal 0.15.3 / symphonia 0.5.4 / ebur128 / nnnoiseless / rubato | Cargo.toml | 【实测】 | 2026-10-15 |
| FFmpeg | `ffmpeg-sidecar`（git 依赖） | Cargo.toml | 【实测】 | 2026-10-15 |
| 遥测 | posthog-rs，opt-in 默认关闭 | Cargo.toml + PRIVACY_POLICY 提交记录 | 【实测】 | 2026-10-15 |
| 官方二进制 | Windows x64-setup.exe；macOS aarch64.dmg | Release 资产 | 【实测】 | 2026-10-15 |
| 安装包体积 | 约 150 MB（含模型） | 第三方评测 | 【二手】 | 2026-10-15 |
| 内存要求 | 8 GB 起 / 16 GB 推荐 | 官网 FAQ | 【二手·官方自述】 | 2026-10-15 |
| macOS 最低版本 | 11+（系统音频 ScreenCaptureKit 需 13+） | 第三方评测 + 开发指南 | 【二手】 | 2026-10-15 |
| Windows 最低版本 | Windows 10 64 位 | 第三方评测 | 【二手】 | 2026-10-15 |
| Star 数 | 12,730+（官网）/ 18K+（dev.to）/ 23.9K+（头条） | **三者冲突** | 【未取得】 | 2026-10-15 |

## 附 B：缺口声明与待核实清单

| # | 缺失项 | 为何重要 | 获取路径 |
|---|---|---|---|
| 1 | **当前 star / fork / 下载量的权威值** | 判断热度与采用度 | GitHub API `stargazers_count`（本次触发 IP 限流；shields.io 亦不可达）；或浏览器直接看仓库页 |
| 2 | Open issues 数量与「构建失败类」issue 占比 | 直接量化构建成功率 | `https://github.com/Zackriya-Solutions/meetily/issues?q=is%3Aissue+build` |
| 3 | Windows 上 `build-gpu.ps1` 是否存在、是否官方支持 | 决定 Windows GPU 构建路径 | 抓 `frontend/` 目录列表或本地 clone 后 `ls` |
| 4 | 构建脚本具体下载了哪些二进制（ffmpeg？ONNX Runtime？） | 决定离线/内网可构建性 | 读 `frontend/scripts/*.js` 与 `build.rs` / `.github/workflows/*.yml` |
| 5 | Parakeet / Whisper 各档模型的磁盘占用与内存峰值 | 决定低配机器可用性 | 官方模型下载页 + 实测 |
| 6 | 上游 Linux 系统音频的真实现状（是否仍需虚拟声卡） | 决定 Linux 可用性 | 在 Linux 实机跑 v0.4.1 验证，或读 `src/audio` 下 Linux 分支实现 |
| 7 | PRO 定价与授权条款细则 | 判断商业分层逻辑 | `https://meetily.ai/pro/` |
| 8 | 社区版实际用户量与活跃度（下载量/DAU） | 判断生态规模 | Release 资产下载计数（shields.io 本次不可达，需人工查看） |

> **本文涉及的估算声明**：「构建期下载二进制」为**推断**，依据是 `[build-dependencies]` 中 `reqwest + zip + tar + xz2 + sha2 + which` 的组合特征，**未逐行读构建脚本**。其余判断均直接引自仓库原文或 Release 页面。

## 附 C：数据源清单

| # | 来源 | 类型 | 用途 |
|---|---|---|---|
| 1 | `raw.githubusercontent.com/.../README.md` | 一手 | 定位、平台支持、安装方式、PRO 分层 |
| 2 | `.../docs/BUILDING.md` | 一手 | 三平台构建步骤、环境变量、发布构建约束 |
| 3 | `.../docs/building_in_linux.md` | 一手 | Linux 依赖、GPU 检测逻辑、排错 |
| 4 | `.../docs/architecture.md` | 一手 | 五组件架构、SQLite |
| 5 | `.../docs/GPU_ACCELERATION.md` | 一手 | 加速后端与 feature 对应 |
| 6 | `.../frontend/src-tauri/Cargo.toml` | 一手 | 真实依赖树、feature、Rust 版本、git 依赖 |
| 7 | `.../frontend/package.json` | 一手 | 真实构建脚本入口、前端依赖 |
| 8 | GitHub Release v0.4.1 页面 | 一手 | 版本、日期、资产、变更摘要 |
| 9 | `meetily.ai` 官网 FAQ（中/英） | 官方二手 | 系统要求、平台策略（多处已过期，见第 6 节） |
| 10 | `Hankanman/Meetily-Local (Parley)` README | 第三方一手 | Linux 上游缺陷的社区验证 |
| 11 | txtmix / gitcode / CSDN / 腾讯云社区评测 | 二手 | 构建实操、踩坑、包体积 |
| 12 | whisper-rs / llama-cpp-2 构建文档（第三仓库） | 一手 | libclang / CMake 依赖的机制确认 |
