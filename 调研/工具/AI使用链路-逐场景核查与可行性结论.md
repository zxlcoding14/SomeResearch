# AI 使用链路 — 逐场景开源核查与可行性结论（PM 视角）

> **文档定位**：《AI使用链路痛点与工程化方向-机会扫描.md》的二轮深化——对首轮识别的全部场景，用同一套方法（开源雷达 → 付费竞品 → 相关产品 → 覆盖度五级 → 个人开发者闸门初判）逐一核查，输出可行性结论。
> **快照时间**：2026-10-22 | **方法**：`product-analysis-framework` §五（先判死再省钱）+ `solo-dev-pm-methodology` 四道闸门
> **数据纪律**：GitHub 数据为【实测·API】（WebFetch/直取通道，采集日 2026-10-22）；市场格局为【二手·需交叉】。Windows 本机 GitHub API 匿名配额间歇性限流，个别 repo 未实测处已标注。

---

## 〇、结论先行（TL;DR）

1. **最大反转：首轮排第 1 的方向 B（引用核验）被本轮证据大幅削弱。** 学术引用核验段已出现**免费、成熟、带桌面 App 的开源成品**（Mark Russinovich 的 RefChecker：548★ / MIT / pushed 2026-10-20，Web UI + 桌面端 + CLI + API 四形态）；通用声明核查段云端商业 L3（Originality.ai / Facticity）；法务判例段的权威源（Westlaw/Lexis/裁判文书网）**个人开发者拿不到合法 API**。B 只剩「中文文献 + 人工服务化」一条窄缝，降级为观察。

2. **方向 C（Agent/Token 成本守门）判死。** LiteLLM 实测 **61,799★**（MIT core，`budgets` 是内置功能）、Langfuse ~34.5k★、Opik ~21.9k★、Portkey ~13k★、Helicone ~6.2k★（2026-03 被收购后进入维护模式）——守门函数已是 L4 级覆盖，「先核 LiteLLM 一周判死」的预判应验，且比预判死得更彻底。

3. **开发者视角的痛点几乎全被开源重兵覆盖。** 三座大山：`llmfit` 38,228★（MIT，创建仅 8 个月，pushed 2026-10-22 当天）覆盖硬件-模型匹配；`docling` 69,302★（MIT）覆盖文档结构化解析；`litellm` 61,799★ 覆盖成本守门。**对个人开发者，这条链路上「做同类工具」已无空位。**

4. **本轮推翻一份既有结论**：《开源竞品与可复用能力.md》§3.3（2026-10-08 快照）记「结构化输出层开源全部没做」——已过时。docling（MIT，结构化输出 + RAG 切块）/ MinerU（66k★级）/ Marker（36k★级）已把库层做满，且都是当周活跃。该文档已加更正注（见其 §3.3）。

5. **幸存的可行性结论只有两类**：① **非开发者可用性层（GUI/小白化）**——底层全是 CLI/Python 框架，普通用户层是 L0–L1（但 model-warden 零 Star 的教训：必须先付需求验证成本，不能默认「免费开源没人做 GUI = GUI 有需求」）；② **本地 RAG 体检 GUI 化（方向 D）**——deepeval 19,017★ / ragas 16,104★ 双宽松许可底座 + 产品层空位，是全场唯一「开源残值清晰 + 无成品」的格子，列为新的第 1 候选。

---

## 一、全景核查矩阵

> 每行 = 一个场景；★ 数据除标注外均为【实测·API】2026-10-22。

| 场景 | 开源代表（Stars/许可/pushed） | 付费竞品 | 覆盖度 | 个人可行性 |
|---|---|---|---|---|
| **1.1 模型文件重复存储** | symlinks 175★MIT🟢 / llamalink 176★MIT 已归档 / model-warden 0★Apache2（完整管家）/ hf-model-tool 36★MIT🟡 / ai-model-scanner 2★MIT | 无 | CLI L2→L3；GUI L0 | ❌ 单点判死；GUI/中国场景两个假设待验 |
| **1.2 硬件-模型匹配** | **llmfit 38,228★MIT🟢（创建 8 个月）** / ollafit（MIT）/ LM Studio 内置 Hardware Check / `ollama show` 自带估算 | 无 | **L4**（开源强者 + 官方内置双覆盖） | ❌ 判死 |
| **1.3 下载加速/镜像** | hf-mirror.com（免费服务）/ hf-transfer（官方工具）/ ModelScope | 镜像站靠赞助，无付费产品 | L3（免费服务成熟） | ❌ 收费不成立（中国用户免费心智 + 官方已覆盖）；只能作管家内功能 |
| **1.4 本地部署安全加固** | local-llm-configuration-auditor / ollama-security（MIT，npx）/ ollama-scout；Shodan 口径 2026-02 约 17.5 万暴露实例【二手】 | 无付费软件；**存在 $99/次人工审计服务**（ollama-security 作者） | 检测段 L2–L3；自动修复段 L1 | ⚠️ 条件可行：检测工具判死；残余 =「一键修复」GUI（体检→自动改 127.0.0.1/防火墙）+ 小微 B 审计服务化；窗口型 |
| **2.1–2.3 Agent 成本守门/归集/路由** | **litellm 61,799★（MIT core，NOASSERTION 总标）** budgets 内置 / langfuse ~34.5k★MIT core / Opik ~21.9k★Apache2 / Portkey ~13k★（gateway 2026-05 后停更）🟡 / Helicone ~6.2k★（被收购后维护模式）🟡 | 云端商业：LangSmith、Langfuse Cloud、Portkey 托管 | **L4** | ❌ 判死（个人）。残余仅剩「非开发者 AI 订阅账单管家」，价值存疑不立项 |
| **3.1–3.3 引用/事实核验·学术段** | **RefChecker 548★MIT🟢（Web UI+桌面+CLI+API 四形态，五库比对+LLM深查）** / hallucinator（多库）/ HalluCiteChecker（Apache2，PyPI，离线）/ check-citations skill（所在 repo ~3.7k★【二手】） | 无直接付费（免费开源成熟） | **L2–L3** | ❌ 判死：免费成品 + 权威库（CrossRef/OpenAlex/S2）公开 API |
| **3.2 引用核验·法务段** | 无成品 | Westlaw/Lexis 付费墙（源不是产品） | L0（无成品）但**源不可得** | ❌ 判死：不是没有位置，是**权威源 API 个人拿不到**（结构性做不到 #4） |
| **3.1 通用声明核查（非引用）** | 研究代码（FacTool 类） | **Originality.ai / Winston / Facticity.AI 云端付费 L3** | L3（商业云端） | ❌ 判死（个人打不过 + 比对源成本） |
| **3.4 AI 代码/输出审查辅助** | 已被通用评测框架覆盖（deepeval 等） | CodeRabbit 等商业 | L3 | ❌（通用段大厂已进，与首轮否决一致） |
| **4.1 AI 输出→结构化落地（解析层）** | **docling 69,302★MIT🟢 / MinerU 66k★级（Apache2+营收门槛，权重另算）🟢 / Marker 36k★级（代码 Apache2、权重 OpenRAIL-M 有 $5M 门槛）** | Reducto / LlamaParse / Unstructured 云端付费 API | **L3–L4**（⚠️ 推翻 10-08 基础文档的 L1 判断） | ❌ 解析层判死；许可三重奏（代码/权重/门槛）是复用时最大的坑，见附 B |
| **4.1 后一公里（解析结果→可直接交付物）** | 库层齐但**成品 GUI 层薄**（表格→Excel、公式→Word 可编辑） | 少（Adobe 系贵而笨） | L1 | ⚠️ 观察项：赌「解析免费了、但小白还是不会用」，需求未验证 |
| **5.1–5.2 本地 RAG 体检** | 库层：**deepeval 19,017★Apache2🟢 / ragas 16,104★Apache2🟡（pushed 2026-02，迁 org 后放缓）** / TruLens 3.4k★MIT（Snowflake）【二手后两者之一已实测】| 云端评测平台（Confident AI $19.99–49/月起【二手】） | **库 L3；产品 GUI L0–L1** | ✅ **全场唯一「底座宽松 + 成品空位」**：新第 1 候选 |
| **6.1 AIGC 标识合规（国内）** | C2PA 工具开源；国内标识工具未查到成品 | 少 | L0–L1 | ⚠️ 待查（政策强制项，可能是 B 端切入缝隙，单独扫描） |

---

## 二、闸门初判（幸存方向）

### 幸存 1：本地 RAG 体检 GUI 化（原方向 D，升为第 1 候选）

- **形态**：面向本地知识库普通用户（非 Python 开发者）的桌面工具——「你的知识库答案，几成真的来自库里？」：导入文档目录 → 自动生成测试问题 → 跑 faithfulness/context 指标 → 输出体检报告。
- **为什么是它**：① 底座零成本（deepeval/ragas 均 Apache-2.0，可闭源商用）；② 成品空位（三个框架全是 Python 库，AnythingLLM 类成品只展示引用、不检引用对错）；③ 痛点有数据（RAG 幻觉 21.9%【二手·需交叉】）。
- **闸门初判**：①收款可（买断/低价订阅）②成本可（本地模型推理或用户自备 API key）③分发可（与原方向 A 同池：本地模型社群）④待算。
- **最大风险（model-warden 教训，写死在前面）**：「库免费、成品缺」≠「用户愿付钱」。model-warden 把完整管家开源出来 7 周零 Star——**先验证再写码**。
- **最小验证（2 周）**：用 deepeval 拼一个无界面脚本，在 2 个本地知识库社群免费给 10 个人跑体检报告，看：① 要不要二次使用 ② 愿不愿意为「定时自动体检」付 ¥30–60。≥3 个付费信号 → 立项写 GUI；无人持续使用 → 回池。

### 幸存 2：本地部署「一键修复」安全工具（原 1.4 残余，条件可行）

- **形态**：不做检测（已 L3），做**修复**——体检报告出来后一键完成：绑定 127.0.0.1、防火墙规则、Ollama 白名单、Defender 排除模型目录。小白不敢自己改系统设置 = 付费理由。
- **变现样本参照**：ollama-security 作者卖 $99/次人工审计【二手】——证明**有人为「有人替他搞定」付钱**，软件版是把这 $99 变成一次性买断 ¥68–99。
- **闸门初判**：①②④可；③客群窄（有暴露风险意识的人）——与方向 A/D 共享分发池。
- **风险**：Ollama 官方新版本若默认收紧绑定（其对 Docker 部署已有动作），窗口关闭。**立项前必查 Ollama release notes。**

### 观察项（不立项，挂起待信号）

| 项 | 挂起原因 | 重启信号 |
|---|---|---|
| 1.1/1.2 的 GUI 化打包 | model-warden 零 Star + llmfit 38k★ 势头，免费档位需求验证为负 | 任一 GUI 化项目出现增长；或社群出现「llmfit 不会用」的原话 |
| 3.x 中文文献核验 | 知网/万方无公开合法 API，源获取是硬门槛 | 官方 API 开放，或找到合规数据源（如学校镜像合作） |
| 4.1 后一公里 GUI | 解析层三巨头迭代太快，壳会被吞 | docling/MinerU API 稳定 6 个月以上 + 小白用户原话出现 |
| 6.1 AIGC 标识 | 未扫描 | 政策执行细则落地后单独跑一轮雷达 |

---

## 三、方法论教训（本轮实证）

1. **「先判死再省钱」这次真的省了钱**：方向 B 首轮排在第 1（付费证据最硬），本轮开源雷达直接把它打到观察区——如果按首轮顺序直接开工，至少浪费 2–4 周。**SOP 第 2 步（雷达提前）是对的，且应该在写任何需求文档之前跑。**
2. **「付费证据硬」不等于「个人可做」**：法务段需求 P5 级真实，但权威源被 Westlaw 封死——这落入结构性做不到 #4（需要我不具备的资源），与努力无关。
3. **免费开源档位的零 Star 是需求信号，不只是竞争信号**：model-warden（完整管家，0★）与 llmfit（单一匹配，38k★）的对比说明——**痛点的「颗粒度」决定免费用户基数**；「管家」式大而全在免费档位反而无人问津。对 GUI 化假设的启示：要么做单点爽功能，要么不做。
4. **基础文档会过期**：10-08 的「结构化输出层开源没做」结论 14 天后即失效。**开源雷达结论必须带快照日，跨轮使用前必须重跑**（已在《开源竞品与可复用能力.md》§3.3 加更正注）。

---

## 附 A · 本轮数据明细

| 项 | 数值 | 口径 | 级别 | 采集日 |
|---|---|---|---|---|
| llmfit | 38,228★ / MIT / pushed 2026-10-22 / Rust / created 2026-02-15 | GitHub API 实测 | ② | 2026-10-22 |
| litellm | 61,799★ / NOASSERTION（MIT core + enterprise 商业许可）/ pushed 2026-10-22 / 5,582 open issues | GitHub API 实测 | ② | 2026-10-22 |
| deepeval | 19,017★ / Apache-2.0 / pushed 2026-10-19 / Python | GitHub API 实测 | ② | 2026-10-22 |
| ragas | 16,104★ / Apache-2.0 / **pushed 2026-02-24（放缓 8 个月，已迁 vibrantlabsai org）** / Python | GitHub API 实测 | ② | 2026-10-22 |
| docling | 69,302★ / MIT / pushed 2026-10-21 / docling-project org（IBM 系转 LF AI）【二手·org 背景】 | GitHub API 实测 | ② | 2026-10-22 |
| refchecker | 548★ / MIT / pushed 2026-10-20 / Python+Tauri 桌面端 | GitHub API 实测 | ② | 2026-10-22 |
| langfuse / Opik / Portkey / Helicone | ~34.5k / ~21.9k / ~13k（gateway 2026-05 后停更）/ ~6.2k（维护模式，2026-03 被收购） | 第三方评测转述 | ④ | 2026-10-22 |
| MinerU / Marker | 66k★级（Apache2 + $20M 月营收门槛）/ 36k★级（代码 Apache2，权重 OpenRAIL-M 三重 $5M 门槛） | 第三方许可分析（含原文引用） | ④（许可条款为引文级） | 2026-10-22 |
| Ollama 暴露实例 | ~175,000（2026-02，LeakIX/Cisco-Shodan）；5,000+（个人 Shodan 扫描） | 二手转述 | ⑤ | 2026-10-22 |
| $99 人工审计服务 | ollama-security 作者固定范围审计 $99/24h | 产品页自述 | ③官方宣称 | 2026-10-22 |
| Confident AI 平台定价 | Free / $19.99 / $49 / Team | 官方定价页转述 | ③ | 2026-10-22 |

## 附 B · 复用三巨头的许可坑（若做幸存方向必读）

| 组件 | 代码许可 | 权重/模型许可 | 复用判读 |
|---|---|---|---|
| docling | MIT | 默认权重 apache-2.0 / cdla-permissive / mit；个别 VLM preset 指向 openrail 仓库 | ✅ 最安全；锁版本+记录权重 rev 即可 |
| deepeval | Apache-2.0 | 无模型权重（LLM-as-judge 调用方自备） | ✅ 可闭源商用；注意其商业平台是独立产品不冲突 |
| ragas | Apache-2.0 | 同上 | ✅ 可用；**维护放缓 8 个月是风险信号**， deepeval 为首选底座 |
| MinerU | MinerU Open Source License（Apache2 + $20M 月营收/1 亿 MAU 门槛 + 在线服务署名义务） | 部分权重仓库无许可标 | ⚠️ 个人远低于门槛可用，但**产品化需在协议里写明上游条款** |
| Marker | Apache-2.0（2026-07-20 起，原 GPL-3.0） | Surya 权重 OpenRAIL-M：$5M 营收 / $5M 融资 / 竞品三重触发 | ⚠️ 同上 |

## 附 C · 缺口声明与应查未查

1. langfuse/Opik/Portkey/Helicone 四项 Stars 为二手口径（litellm/deepeval/ragas/docling/refchecker/llmfit 已实测）——不影响判死结论（量级差两个数量级）。
2. ragas 迁 org 后是否恢复活跃未跟踪（放缓本身已是方向 D 底座选型的依据）。
3. 国内 AIGC 标识合规工具未扫描（观察项，政策驱动单独跑）。
4. ollama-security 的 $99 服务真实成交情况未验证（③自述）。
5. RefChecker 对中文文献的覆盖未实测（判死结论基于英文权威库公开 API 前提；中文段已单独标注判死原因不同——源不可得）。
