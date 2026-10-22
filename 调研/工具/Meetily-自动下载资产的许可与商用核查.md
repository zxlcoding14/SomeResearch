# Meetily 自动下载资产的许可与商用核查

> **核查对象**：Meetily 社区版运行/构建过程中**自动下载或内置**的全部第三方资产
> **核查方法**：直接读仓库源码，定位**每一处下载 URL 与来源**（附文件 + 行号），再逐一追溯上游许可
> **采集日**：2026-10-15（对应 `main` 分支，社区版 v0.4.1）
> **姊妹文档**：技术构建见《Meetily-本地构建与环境依赖分析.md》；商业化见《Meetily-商业化现状与付费产品核查.md》
>
> ⚠️ **非法律意见。** 本文给出的是许可事实与义务清单，最终合规判断请咨询法务。

---

## 0. 结论先行（TL;DR）

| 问题 | 答案 |
|---|---|
| **模型能商用吗？** | **能。** 全部模型都是开放许可，**没有任何一个禁止商用**。但义务不同：Whisper / Silero / Qwen / ONNX Runtime 是宽松许可（MIT / Apache 2.0），**Parakeet 是 CC-BY-4.0（必须署名）**，**Gemma 3 是 Google 自定义条款（非开源许可，必须传递条款）** |
| **需要授权吗？** | **不需要付费、不需要申请。** 没有一家要求你先获得书面许可或支付版税。CC-BY-4.0 与 Gemma 条款都是「遵守义务即自动获得授权」 |
| **唯一的真实风险点** | **FFmpeg 二进制是 GPLv3 构建**（高置信推断）。自己用完全没问题，但**一旦你再分发**（把 Meetily 打包卖、或塞进自己的产品），就会背上 GPLv3 的源码提供义务 —— 而 Meetily **目前没有随附任何 GPL 声明或源码指引** |
| **Meetily 自身的合规状况** | **不完整**：仓库里**只有 `LICENSE.md`（MIT）一个许可文件，没有 THIRD-PARTY-NOTICES**。唯一做到位的是 ONNX Runtime（构建脚本会把它的 LICENSE 复制进产物）；FFmpeg、Parakeet、Gemma 的义务都没有在产品内落实 |
| **最容易踩的坑** | 以为「MIT 项目 = 里面所有东西都能随便商用」。实际这个 MIT 项目里**打包了 GPL 的 ffmpeg、装了带条款的 Gemma**。MIT 只覆盖 Meetily 自己写的代码 |

**一句话**：**拿来做会议记录，随便用；拿来二次分发（尤其要卖钱），必须自己补一份第三方许可声明 —— 这份声明 Meetily 没给你。**

---

## 1. 自动下载 / 内置资产全清单（实测）

| # | 资产 | 用途 | 实际来源 URL | 引入方式 |
|---|---|---|---|---|
| 1 | **Whisper 模型**（12 个变体） | 转写 | `huggingface.co/ggerganov/whisper.cpp` | 首次使用下载 |
| 2 | **Parakeet TDT 0.6B v3（ONNX）** | 转写（默认） | `huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx` | 首次使用下载 |
| 3 | **Qwen3.5-2B / 4B（GGUF）** | 本地摘要 | `huggingface.co/unsloth/Qwen3.5-2B-GGUF`、`unsloth/Qwen3.5-4B-GGUF` | 首次使用下载 |
| 4 | **Gemma 3 1B / 4B（GGUF）** | 本地摘要 | `huggingface.co/bartowski/google_gemma-3-4b-it-GGUF` | 首次使用下载 |
| 5 | **FFmpeg 二进制** | 音频混音/解码 | `github.com/Zackriya-Solutions/ffmpeg-binaries`（自建镜像仓） | **构建期下载并打包进分发物** |
| 6 | **ONNX Runtime 1.22.0** | Parakeet 推理 | `github.com/microsoft/onnxruntime` 官方 release | 构建期下载（Windows） |
| 7 | **Silero VAD** | 语音活动检测 | `github.com/emotechlab/silero-rs`（上游 snakers4/silero-vad） | Cargo 依赖，编译进二进制 |
| 8 | **whisper.cpp / ggml / llama.cpp** | 推理运行时 | Cargo 依赖（`whisper-rs` 0.13.2、`llama-cpp-2`） | 编译进二进制 |

> **注**：1–4 是「应用内自动下载的模型」，5–8 是「构建期拉取或编译进产物的依赖」。用户问的"自动下载的模型"是 1–4，但 5 是同一类风险且更严重，一并列出。

---

## 2. 逐项许可与商用判断

### 2.1 Whisper 模型 —— MIT（最宽松）

| 项 | 内容 |
|---|---|
| 下载 URL（源码实证） | `whisper_engine.rs` L1077–1088，共 12 个：`ggml-tiny/base/small/medium/large-v3-turbo/large-v3.bin` 及 `-q5_1` / `-q5_0` 量化版 |
| 上游 | OpenAI Whisper 权重 → **MIT** |
| ggml 转换 | ggml 官方项目（ggerganov / ggml-org）→ **MIT** |
| 商用 | ✅ **可以，无任何限制条件** |
| 义务 | 保留版权与许可声明（再分发时） |

### 2.2 Parakeet TDT 0.6B v3 —— CC-BY-4.0（核心义务：署名）

| 项 | 内容 |
|---|---|
| 下载源（源码实证） | `frontend/src/lib/parakeet.ts` L78 注释明确写出：`https://huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx` |
| 上游模型 | `nvidia/parakeet-tdt-0.6b-v3` → **CC-BY-4.0** |
| HF 仓库许可标签 | **cc-by-4.0**（已核实） |
| 商用 | ✅ **可以。NVIDIA 官方模型卡明确写「ready for commercial/non-commercial use」** |
| **义务** | **必须署名（Attribution）**：标注 "Parakeet TDT 0.6B v3" 由 NVIDIA 创建、以 CC-BY-4.0 授权，并给出许可链接 |
| 需要注意 | CC-BY-4.0 **不是**"无义务"，它要求合理的署名方式 + 许可链接 + 修改声明 |

### 2.3 Qwen3.5 2B / 4B —— Apache 2.0（最宽松）

| 项 | 内容 |
|---|---|
| 下载 URL（源码实证） | `summary_engine/models.rs` L172、L185：`unsloth/Qwen3.5-2B-GGUF`、`unsloth/Qwen3.5-4B-GGUF` 的 Q4_K_M |
| 上游 | 阿里 Qwen 系列 → **Apache 2.0** |
| 商用 | ✅ **可以**：无版税、无用户规模门槛、无需商业审批 |
| 义务 | 保留版权/NOTICE；若修改需标注 |

### 2.4 Gemma 3 1B / 4B —— Google 自定义条款（⚠️ 非开源许可）

| 项 | 内容 |
|---|---|
| 下载 URL（源码实证） | `summary_engine/models.rs` L198、L211：`bartowski/google_gemma-3-4b-it-GGUF` 的 Q4_K_M 与 Q8_0 |
| 上游 | Google **Gemma 3** |
| 许可 | **Gemma Terms of Use** —— Google 自维护的**专有许可**，**不是 OSI 认可的开源许可** |
| 商用 | ⚠️ **允许商用**，但**附带条件**：<br>① 必须**随附条款副本**给接收方<br>② 必须把 §3.2 的**使用限制（Gemma Prohibited Use Policy）写入下游分发协议**<br>③ 修改需标明 |
| **口径冲突（必须标注）** | 有来源称「Gemma 3 已改为 Apache 2.0」，另有来源称「改为 Apache 2.0 的是 **Gemma 4**，**Gemma 3 保留自定义条款**」。**本报告按保守口径（自定义条款）处理**【见附 B 第 3 条】 |
| 实务影响 | 若你的产品要用于**医疗诊断、法律建议等高风险场景**，Gemma 条款中的禁用条款可能直接构成障碍 —— **这是唯一一个会因"用途"而受限的模型** |

### 2.5 FFmpeg 二进制 —— ⚠️ GPLv3（本次核查最大的风险点）

| 项 | 内容 |
|---|---|
| 下载源（源码实证） | `frontend/src-tauri/build/ffmpeg.rs` L129–144，共 5 个平台变体：<br>Windows `.../0.0.1/ffmpeg-8.0.1-essentials_build.zip`<br>macOS `ffmpeg80arm.zip`、`ffmpeg-8.0.1.zip`<br>Linux `ffmpeg-release-arm64-static.tar.xz`、`ffmpeg-release-amd64-static.tar.xz` |
| 托管 | **Zackriya 自己开的镜像仓** `Zackriya-Solutions/ffmpeg-binaries`（1 次提交 / 2026-02-08 / **README 无内容、无 LICENSE 文件、无仓库描述**） |
| 构建来源识别 | `ffmpeg-8.0.1-essentials_build.zip` 的命名格式 = **gyan.dev**；`ffmpeg-release-amd64-static.tar.xz` = **johnvansickle** 静态构建 |
| **许可判定** | **gyan.dev 所有构建均为 GPLv3（该站不提供 LGPL 变体）**；johnvansickle 的 static 构建同样含 GPL-only 编解码器 → **GPLv3**。**置信度：高（基于命名与来源惯例的推断，未见其构建配置脚本）** |
| 使用（自己跑） | ✅ **完全没问题**。GPL 不限制使用，个人或公司内部用都可以，商用也不受影响 |
| **再分发** | ⚠️ **触发 GPLv3 义务**：必须①随附 GPLv3 许可文本 ②提供对应源码的获取途径 ③如修改需声明 |
| 为何不算"传染" | Meetily 只把 ffmpeg 当**外部进程调用**（命令行调用，非链接进自身代码），业界通常视为"聚合"，**不导致 Meetily 自身代码被迫 GPL 化**。但**分发该二进制本身的义务仍然存在** |
| **Meetily 现状** | ❌ **未履行**：产品内无 GPL 声明，上游 ffmpeg 镜像仓也无许可文件 |

### 2.6 ONNX Runtime 1.22.0 —— MIT（**唯一做得规范的一项**）

| 项 | 内容 |
|---|---|
| 下载 URL（源码实证） | `build/onnxruntime.rs` L14：`github.com/microsoft/onnxruntime/releases/download/v1.22.0/onnxruntime-win-x64-1.22.0.zip` |
| 许可 | **MIT** |
| ✅ **合规亮点** | 该构建脚本 L39–40 **主动把压缩包里的 `LICENSE` 解出来保存为 `onnxruntime-LICENSE.txt`** —— 说明团队对许可署名是**有意识**的（只是没有全覆盖） |

### 2.7 Silero VAD —— MIT

| 项 | 内容 |
|---|---|
| 引入方式 | `Cargo.toml` 中的 `silero_rs`（git 依赖，`emotechlab/silero-rs`），另有 `silero_rs` 上游 snakers4/silero-vad |
| 许可 | **MIT**（上游官方口径："Published under permissive license (MIT) … zero strings attached"） |
| 商用 | ✅ 可以，无义务 |

### 2.8 whisper.cpp / ggml / llama.cpp —— MIT

| 项 | 内容 |
|---|---|
| 引入 | `whisper-rs` 0.13.2、`llama-cpp-2`、`ffmpeg-sidecar` 等 Cargo 依赖 |
| 许可 | **MIT**（ggml 作者群） |
| 商用 | ✅ 可以 |

---

## 3. 三种场景的义务矩阵（决定你要做什么）

| 你的场景 | Whisper | Parakeet | Qwen | Gemma 3 | FFmpeg | ONNX Runtime |
|---|---|---|---|---|---|---|
| **A. 自己用**（个人或公司内部跑会议记录，不对外分发） | 无义务 | 无义务 | 无义务 | 无义务 | 无义务 | 无义务 |
| **B. 把 Meetily 原样分发给别人**（含免费分享） | 保留声明 | **署名 NVIDIA** | 保留声明 | **随附 Gemma 条款** | **附 GPLv3 + 源码途径** | 保留 LICENSE |
| **C. 塞进自己的产品卖 / 做 SaaS** | 保留声明 | **署名 NVIDIA** | 保留声明 | **随附条款 + 传递使用限制** | **附 GPLv3 + 源码途径** | 保留 LICENSE |
| **D. 用这些模型自己微调后商用** | 保留声明 | **署名 NVIDIA**（衍生作品仍受 CC-BY-4.0） | 保留声明 + 标注修改 | **受 Gemma 条款约束**（且不得闭源再分发权重） | 不适用 | 不适用 |

**结论**：
- **场景 A（绝大多数用户）**：**零义务，随便用。** 这也是 Meetily 的默认定位。
- **场景 B/C/D**：**义务真实存在，且 Meetily 没帮你准备好材料**。你需要自己写一份 THIRD-PARTY-NOTICES，至少覆盖 Parakeet 署名、Gemma 条款、FFmpeg GPLv3 三项。

---

## 4. Meetily 自身的许可合规状况（实测）

| 应有项 | 实际情况 | 判定 |
|---|---|---|
| 项目自身许可 | `LICENSE.md` = **MIT** | ✅ |
| **第三方许可清单**（THIRD-PARTY-NOTICES / NOTICE） | **不存在**（已扫描全仓库文件树，许可类文件仅 `LICENSE.md` + 一个无关的 Pro 数据库迁移文件） | ❌ |
| **产品内许可展示页**（About / Licenses 页面） | **不存在** | ❌ |
| Parakeet (CC-BY-4.0) 署名 | README「Acknowledgments」提及 NVIDIA 与 istupakov，但**无许可性质声明、无 CC-BY-4.0 链接** | ⚠️ 不完整 |
| Gemma 条款随附 | **无** | ❌ |
| FFmpeg GPLv3 声明 | **无**（镜像仓本身连 LICENSE 都没有） | ❌ |
| ONNX Runtime LICENSE | **构建脚本主动提取并随附**（`onnxruntime-LICENSE.txt`） | ✅ |
| Whisper / Silero / ggml (MIT) | 未随附，但 MIT 只在"再分发"时才要求保留声明 | ⚠️ |

**判断**：团队**知道**许可署名这件事（ONNX Runtime 的处理是证据），但**只做了一处**。可以推测是"顺手做了容易的那一个"，而非系统性合规流程。

> **对使用者的实际含义**：Meetily 自己作为 MIT 项目分发时义务履行不完整，**但这对你"使用"它没有影响**。风险只在你**继承它的分发行为**时转移到你身上。

---

## 5. 风险排序（按你的实际暴露程度）

| 排序 | 风险 | 触发条件 | 严重度 |
|---|---|---|---|
| 1 | **FFmpeg = GPLv3，且无许可声明随附** | 你要**再分发** Meetily 或基于它做产品 | **高**（GPL 义务明确且易被审计） |
| 2 | **Gemma 3 自定义条款未随附** | 你要再分发，且**产品内保留了 Gemma 摘要模型** | **中高**（条款要求传递至下游协议） |
| 3 | **Parakeet 无正式署名** | 你要再分发 | **中**（CC-BY-4.0 署名义务，补齐成本很低） |
| 4 | 模型口径/来源可能随版本变化（URL 硬编码在源码中） | 长期依赖 | **低**（版本升级时需复查） |
| 5 | Whisper / Qwen / Silero / ONNX Runtime | 仅需保留声明 | **低** |

---

## 6. 附 A：数据明细（含源码证据链）

| 资产 | 下载源 | 许可 | 义务 | 源码证据 | 级别 |
|---|---|---|---|---|---|
| Whisper ×12 | `huggingface.co/ggerganov/whisper.cpp` | MIT | 保留声明 | `frontend/src-tauri/src/whisper_engine/whisper_engine.rs` L1077–1088 | 【实测】源码 + 【实测】上游许可 |
| Parakeet TDT 0.6B v3 ONNX | `huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx` | **CC-BY-4.0** | **署名** | `frontend/src/lib/parakeet.ts` L78；HF 许可标签已核实 | 【实测】 |
| Qwen3.5-2B / 4B | `huggingface.co/unsloth/Qwen3.5-2B-GGUF` / `-4B-GGUF` | Apache 2.0 | 保留声明 | `frontend/src-tauri/src/summary/summary_engine/models.rs` L172、L185 | 【实测】 |
| Gemma 3 1B / 4B | `huggingface.co/bartowski/google_gemma-3-4b-it-GGUF` | Gemma Terms of Use | 随附条款 + 传递使用限制 | 同上 L198、L211 | 【实测】源 + 【二手】许可（口径有冲突） |
| FFmpeg 8.0.1 | `github.com/Zackriya-Solutions/ffmpeg-binaries` release `0.0.1` | **GPLv3（推断）** | 附许可 + 提供源码途径 | `frontend/src-tauri/build/ffmpeg.rs` L129–144 | 【实测】源 + 【推断·高置信】许可 |
| ONNX Runtime 1.22.0 | `github.com/microsoft/onnxruntime` v1.22.0 | MIT | 保留 LICENSE | `frontend/src-tauri/build/onnxruntime.rs` L14、L39–40 | 【实测】 |
| Silero VAD | `emotechlab/silero-rs` → snakers4/silero-vad | MIT | 保留声明 | `frontend/src-tauri/Cargo.toml` | 【实测】 |
| whisper.cpp / ggml / llama.cpp | Cargo（whisper-rs / llama-cpp-2） | MIT | 保留声明 | `Cargo.toml` | 【实测】 |
| Meetily 自身 | — | MIT | — | `LICENSE.md` | 【实测】 |

## 7. 附 B：缺口声明

| # | 缺口 | 影响 | 验证路径 |
|---|---|---|---|
| 1 | **FFmpeg 二进制的确切构建配置未知**（未读到 `--enable-gpl` 之类的编译参数） | 决定 GPL 义务是否成立；若是 LGPL 构建则义务大幅减轻 | 下载 `Zackriya-Solutions/ffmpeg-binaries` 的 zip，运行 `ffmpeg -version` 看 configuration 行（含 `--enable-gpl` 即为 GPLv3） |
| 2 | 应用内是否另有许可展示界面（如设置页 About）未逐页核对 | 影响"署名是否以合理方式呈现"的判断 | 装一份 Meetily Pro/CE，翻设置页找 Licenses/About |
| 3 | **Gemma 3 许可状态口径冲突**：一说 Gemma 3 已转 Apache 2.0，一说转 Apache 2.0 的是 Gemma 4、Gemma 3 保留自定义条款 | 决定是否必须传递条款 | 直接读 `huggingface.co/google/gemma-3-4b-it` 的 License 字段与 terms 链接 |
| 4 | istupakov 的 ONNX 转换是否引入了额外条款 | 可能叠加义务 | 已读 HF 页面：许可标签为 cc-by-4.0，未见额外限制；但未逐字读其仓库文件 |
| 5 | `bartowski` 的 GGUF 转换是否声明额外条款 | 同上 | 读 `huggingface.co/bartowski/google_gemma-3-4b-it-GGUF` 的 model card |
| 6 | Pro 版是否使用**不同**的模型（Pro 可能有自己的托管摘要通道） | Pro 用户的合规口径可能不同 | 需实测 Pro 客户端设置项（本报告仅覆盖社区版） |
| 7 | 模型 URL 硬编码在源码中，未来版本可能变更 | 长期合规复查 | 定期复查上述源码行 |

> **本报告中的推断声明**：「FFmpeg 为 GPLv3」是基于**文件命名惯例 + 已知来源惯例**的**高置信推断**，**未读到该二进制自身的 `-version` 输出**。这**不影响**"自己使用完全自由"的结论，但**会影响再分发义务的具体内容**（GPLv3 vs LGPL），需按缺口 1 的路径落实。

## 8. 附 C：数据源清单

| # | 来源 | 类型 | 用途 |
|---|---|---|---|
| 1 | `frontend/src-tauri/src/whisper_engine/whisper_engine.rs` | 一手源码 | Whisper 的 12 个下载 URL |
| 2 | `frontend/src/lib/parakeet.ts` | 一手源码 | Parakeet 下载源（L78 注释） |
| 3 | `frontend/src-tauri/src/summary/summary_engine/models.rs` | 一手源码 | 内置摘要模型的 GGUF 来源 |
| 4 | `frontend/src-tauri/build/ffmpeg.rs` | 一手源码 | FFmpeg 二进制来源 |
| 5 | `frontend/src-tauri/build/onnxruntime.rs` | 一手源码 | ONNX Runtime 来源 + LICENSE 随附逻辑 |
| 6 | `frontend/src-tauri/Cargo.toml` | 一手源码 | Silero VAD / whisper-rs / llama-cpp-2 依赖 |
| 7 | GitHub API（`git/trees` 全量递归） | 一手 | 确认仓库无 THIRD-PARTY / NOTICE 文件 |
| 8 | `github.com/Zackriya-Solutions/ffmpeg-binaries` | 一手 | 镜像仓无 README 内容、无 LICENSE |
| 9 | `huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx` | 一手 | CC-BY-4.0 标签确认 |
| 10 | `huggingface.co/nvidia/parakeet-tdt-0.6b-v3` | 一手（模型卡） | 「ready for commercial/non-commercial use」+ CC-BY-4.0 |
| 11 | OpenAI Whisper / whisper.cpp 官方 | 一手 | MIT 许可 |
| 12 | silero-vad 官方模型卡 | 一手 | MIT 许可 |
| 13 | gemma 许可解读（多来源比对） | 二手（口径冲突） | Gemma Terms of Service 的义务内容 |
| 14 | gyan.dev / johnvansickle 构建许可说明 | 二手 | FFmpeg 构建的 GPLv3 判定依据 |
| 15 | 同类项目的 THIRD-PARTY-NOTICES 实践（InsideVoice / FrameShift / steno） | 二手（参照） | 印证上述义务的标准写法 |
