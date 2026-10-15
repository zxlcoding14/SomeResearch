# last30days-skill 安装与使用指南（Windows / WorkBuddy）

> 对象仓库：https://github.com/mvanhorn/last30days-skill
> 版本基线：v3.28.0（2026-10）· MIT 许可 · 2,700+ 测试
> 本机环境核验日：2026-10-15

---

## TL;DR

1. **它不是软件，是一个 agent skill** —— 装到支持 skill 的宿主里才能用，单跑一个 `.exe` 是没有的。
2. **它做的事**：把 Reddit / X / YouTube / TikTok / Hacker News / Polymarket / GitHub / 小红书 等十几个源的「近 30 天」帖子 + 真实互动数据（upvote / 点赞 / 播放 / 真金下注赔率）拉回来，同事件跨平台合并，再由 agent 综合成一份带出处的简报。
3. **零配置可用**：Reddit（含评论与真实 upvote）、HN、Polymarket、GitHub、StockTwits、arXiv、Techmeme、Digg —— 不用任何 key。
4. **要 key 才能扩**：X（可改用浏览器登录态）、YouTube 评论、TikTok / Instagram / Threads / LinkedIn（ScrapeCreators）、小红书（本地 MCP 服务）、Brave Web 搜索、Perplexity。
5. **Windows 现实**：README **没有 WorkBuddy 这一条安装路径**，`npx skills` 的宿主清单里也没有 WorkBuddy。要用只能**手动把 `skills/last30days` 目录放进 `~/.workbuddy/skills/`**（下文第 2 节）。
6. **两个必须提前知道的坑**：① 它在 Windows 上默认把简报写到 `C:\Users\<你>\Documents\Last30Days\`，产物是 html / json / sqlite，**不是 md**，与你「只出 md」的规则冲突，要显式改 `--save-dir`；② SKILL.md 里的命令写死 `python3`，Windows 上通常只有 `python`，大概率要改名或建别名。

---

## 一、它是什么（定位）

| 维度 | 说明 |
|---|---|
| 品类 | 跨平台「近 30 天真实民意」聚合研究器（agent skill） |
| 相对 Google/ChatGPT 的差异 | Google 聚合编辑推荐；它聚合**真实互动数据**排序的社区声音。单一 AI 都拿不到全源（ChatGPT 有 Reddit 没 X，Gemini 有 YouTube 没 Reddit，Claude 基本都没有），它靠用户自带 key + 浏览器会话一次性桥接 |
| 排序信号 | 真实 upvote / 点赞 / 播放量 / Polymarket 真金赔率 / GitHub star 增速 —— 不是编辑权重 |
| 工作方式 | 7 步：输入话题 → agent 解析实体（X handle / GitHub repo / subreddit / hashtag）→ 并行搜源 → 抓深度内容（完整转录、顶级评论）→ 同故事跨平台合并 → 综合成带出处简报 → 会话内成为该话题专家，可继续追问 |
| 隐私 | 无追踪、无分析，研究数据留本地 |
| 许可 | MIT |

**能力边界（先说死）**：它给你的是「社区在说什么 + 有多少人真的在乎」，**不给**权威数据、财报口径、付费调研结论。价格 / ARR / 用户量这类数字，它给的是**社区转述**，口径不可信，不能直接当审计数据用。

---

## 二、安装（WorkBuddy / Windows 实路径）

### 2.1 前置条件核验（本机结果，2026-10-15）

| 依赖 | 要求 | 本机实际 | 结论 |
|---|---|---|---|
| Python | 3.12+ | 3.13.14（`C:\Users\zhangxinliang1\.workbuddy\binaries\python\versions\3.13.12\python.exe`） | ✅ 满足 |
| Node.js | 需要（X 搜索内置 Bird 客户端） | v22.22.2 | ✅ 满足 |
| git | 需要 | 2.55.0.windows.3 | ✅ 满足 |
| yt-dlp | 仅 YouTube 源需要 | 未安装 | ⚠️ 可选，暂缺 |
| uv | Python 供给用 | 未安装 | ⚠️ 可选（有系统 Python 3.13 可绕过） |
| python3 命令 | SKILL.md 写死 `python3` | Windows 只有 `python` | ❌ **需处理**（见 2.3） |

### 2.2 安装步骤（手动，WorkBuddy 唯一可行路径）

```bash
# 1) clone 到一个不放 skill 运行目录的临时位置
git clone https://github.com/mvanhorn/last30days-skill.git D:/tmp/last30days-skill

# 2) 把 skill 核心目录整个复制进 WorkBuddy 的用户级 skills 目录
#    注意：复制的是 skills/last30days 这一层，不是仓库根目录
cp -r D:/tmp/last30days-skill/skills/last30days \
      "C:/Users/zhangxinliang1/.workbuddy/skills/last30days"

# 3) 验证结构：SKILL.md 与 scripts/ 必须是同级兄弟
ls "C:/Users/zhangxinliang1/.workbuddy/skills/last30days"
# 期望看到：SKILL.md  scripts/  references/

# 4) 冒烟测试（不启动研究，只做预检）
"C:/Users/zhangxinliang1/.workbuddy/binaries/python/versions/3.13.12/python.exe" \
  "C:/Users/zhangxinliang1/.workbuddy/skills/last30days/scripts/last30days.py" --preflight
```

> ⚠️ SKILL.md 明确要求：`SKILL_DIR` 必须绑定到**实际加载的根 SKILL.md 所在目录**，且 SKILL.md 与 `scripts/` 必须同级。所以**不要**只拷 `scripts/`，也不要拷成 `skills/last30days/last30days/` 双层。

### 2.3 Windows 上必须处理的两件事

1. **`python3` → `python`**
   SKILL.md 与文档里所有命令都是 `python3 ...`。Windows 没有 `python3` 这个名字。三种解法，推荐第一种：
   - 在 Git Bash 里建别名：`alias python3="C:/Users/zhangxinliang1/.workbuddy/binaries/python/versions/3.13.12/python.exe"`（注意 skill 实际执行时是新 shell，别名不一定继承）
   - 复制一份 `python3.exe`（或做 `.cmd` 包装）放到 PATH 上的目录
   - 直接改 skill 内部脚本里的调用（改动会阻碍后续 `git pull` 升级，不推荐）
2. **产物目录**：Windows 默认 `LAST30DAYS_MEMORY_DIR = C:\Users\<你>\Documents\Last30Days\`。想让它别乱写，先设环境变量：
   ```bash
   export LAST30DAYS_MEMORY_DIR="D:/code/Test/SomeResearch/调研/_l30d_raw"
   ```

### 2.4 不要用的安装方式（在本机无效）

| 方式 | 为什么不行 |
|---|---|
| `/plugin marketplace add mvanhorn/last30days-skill` | 这是 Claude Code 的斜杠命令，WorkBuddy 没有 `/plugin` |
| `npx skills add mvanhorn/last30days-skill -g` | 该 CLI 的宿主清单（codex / cursor / copilot / gemini-cli / claude-code / windsurf / cline / continue / roo / aider-desk / opencode / goose）**不含 WorkBuddy** |
| Claude Desktop `.mcpb` | 官方明确 **Windows 支持 deferred**（"Windows support is deferred until per-platform manifest entry points are sorted out"） |
| claude.ai 上传 `.skill` | 需要 claude.ai 账号与 Code execution 开关，跟本地无关 |

---

## 三、怎么用

### 3.1 触发方式（WorkBuddy 与 Claude Code 不同）

| 宿主 | 触发 |
|---|---|
| Claude Code / Codex / Cursor 等 | 斜杠命令：`/last30days Peter Steinberger` |
| **WorkBuddy** | **没有斜杠命令**。skill 由 description 匹配自动加载，所以用自然语言：「用 last30days 研究一下 X 最近 30 天的情况」「帮我跑近 30 天 Reddit/X 上对 X 的讨论」 |
| 脚本 / cron（绕过 agent，最可靠） | `python last30days.py "话题" --emit=json` |

> 想让 agent 稳定触发，最省事的办法是**直接告诉它跑哪个脚本**，而不是指望它自己匹配 description。

### 3.2 直接调引擎（推荐：可控、可复算）

```bash
PY="C:/Users/zhangxinliang1/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK="C:/Users/zhangxinliang1/.workbuddy/skills/last30days/scripts/last30days.py"

# 基础研究
"$PY" "$SK" "AI coding agents"

# 机器可读（给下游分析用）—— 推荐接入你自己的 pipeline
"$PY" "$SK" "AI coding agents" --emit=json

# 生成自包含 HTML 简报（可分享）
"$PY" "$SK" "AI coding agents" --emit=html

# 话题发现：扫出 5-10 个增速排名的新兴话题
"$PY" "$SK" --discover "AI agents"

# 竞品对比（star 数从 GitHub API 实时拉）
"$PY" "$SK" "OpenClaw vs Hermes vs Paperclip" --competitors

# 招聘信号（读对方招聘页，反推战略重点）
"$PY" "$SK" "Listen Labs" --hiring-signals

# 预检：只打印「打算读什么、写什么」，不启动研究
"$PY" "$SK" --preflight

# 诊断：每个源都跑一遍，报「缺哪个 key / 哪个 CLI 不在 PATH / 哪个 cookie 过期」
"$PY" "$SK" --diagnose
```

### 3.3 关键参数表

| 参数 | 作用 |
|---|---|
| `--emit=json` | 版本化 JSON，机器可读（**接你自己的分析流程用这个**） |
| `--emit=html` | 自包含 HTML 简报 |
| `--emit=compact` | 精简输出（宿主 WebSearch 路径用） |
| `--save-dir <path>` | 改保存目录 |
| `--output <file>` | 指定精确输出文件路径 |
| `--save-suffix=<name>` | 同一话题多版本区分 |
| `--discover "X"` | 话题发现模式 |
| `--competitors` | 自动发现竞品并对比 |
| `--hiring-signals` | 招聘信号分析 |
| `--github-user=<name>` | GitHub 个人模式 |
| `--as-of` | 历史回溯（按指定时间点重跑） |
| `--store` | 持久化到 SQLite，用于趋势监控 |
| `--search xhs` / `--search dripstack` | 按需启用小红书 / DripStack 源 |
| `--allow-browser-cookies` | 允许读浏览器 cookie（默认不读） |
| `--preflight` / `--diagnose` | 预检 / 诊断 |
| `--agent` | 技能级模式引导（不是引擎参数） |

**输出后**：可以说 `eli5 on` 切到「讲给小孩听」的简化模式。

### 3.4 订阅/监控类（脚本或 cron）

```bash
"$PY" "$SK" library feed                        # 看研究库 feed
"$PY" "$SK" library search "MCP servers"        # 搜你自己的历史研究库
```
配套脚本：`watchlist.py`（定时跑 + Slack/webhook 通知）、`briefing.py`（每日/每周摘要）。

---

## 四、数据源与开卡成本

### 4.1 零配置可用

| 源 | 拿到什么 |
|---|---|
| Reddit | 帖子 + **真实 upvote** + 顶级评论（RSS + shreddit 抓取） |
| Hacker News | 帖子 + 分数 |
| Polymarket | 真金白银下的赔率 |
| GitHub | PR 速度、按 star 排名的仓库、release notes |
| StockTwits | 话题是股票代码或加密时自动激活 |
| arXiv / Techmeme / Digg | 首次运行自动装 CLI（免费） |

### 4.2 要配置才能用

| 源 | 需要什么 | 成本 |
|---|---|---|
| X / Twitter | `X_BEARER_TOKEN`（官方 API）**或**浏览器登录 x.com（免 key）**或** `XQUIK_API_KEY` / `XAI_API_KEY` | 官方 API 吃你自己的 X 开发者额度；cookie 免费 |
| YouTube 转录 / 评论 | `yt-dlp` | 免费 |
| Bluesky | bsky.app App password | 免费 |
| TikTok + Instagram + Threads + Pinterest + LinkedIn + YouTube 评论 | `SCRAPECREATORS_API_KEY` | 前 10,000 次免费，之后按量付费 |
| 小红书 RED | 本地跑 x-mcp 浏览器插件或 `xiaohongshu-mcp` 服务，`--search xhs` | 无 last30days key；依赖本地服务 |
| Web 搜索 | `BRAVE_API_KEY` | 每月 2,000 次免费 |
| Perplexity | Perplexity key（OpenRouter 作 Sonar 兜底） | 按量付费 |

**最小可用配置**（0 成本）：什么都别配，先跑一次看 Reddit + HN + Polymarket + GitHub 的效果。Reddit 这一层对「桌面工具 / mini-tool」这类话题其实已经是最有信息量的源。

环境变量落点：`~/.config/last30days/.env`（首次运行会写 `SETUP_COMPLETE=true`）。

---

## 五、风险与注意事项（用之前先看）

| 风险 | 说明 | 处理 |
|---|---|---|
| **产物格式冲突** | 默认产出 html / json / sqlite 到 `Documents\Last30Days\`，**不是 md** | 用 `--emit=json` 拿数据，自己转成 md 再归档；或 `--save-dir` 指到 `调研\` 之外 |
| **脚本读 cookie** | X 免 key 路线靠读浏览器登录态 | 默认不读，需 `--allow-browser-cookies` 或 `FROM_BROWSER` 显式开启；不想给就别开，改用 `X_BEARER_TOKEN` |
| **第三方代码** | 2,700+ 测试 ≠ 已验证；SKILL.md 自己写 "Review scripts before first use" | 装前扫一遍 `scripts/`；它只用 Python 标准库 + node，无重依赖，可读 |
| **数据口径不可当审计** | 社区转述的价格 / ARR / 用户量全不可信 | 只把它当**信号源**，数字一律回原始出处核 |
| **Windows 未充分验证** | Claude Desktop 的 Windows 支持官方 deferred；有一批「Windows 兼容性改进」但无 Windows CI 证据 | 首次跑务必先 `--preflight` + `--diagnose` |
| **升级流程不顺** | 手动拷进 `~/.workbuddy/skills/` 后，升级要重新 `git pull` + 重拷 | 保留 `D:/tmp/last30days-skill` 作为工作树，升级即重拷 |

---

## 六、对你当前研究线的实际用法（3 条）

1. **桌面 mini-tool 机会发现** —— `--discover "desktop AI tools"` / `--discover "windows productivity tools"`，扫近 30 天增速话题，补充 `产品信号渠道地图.md` 里「论坛 / 社区信号」这一层的一手数据源。
2. **样本案例动态跟踪** —— 对 `renameai.online`、`PopDrop` 这类标的跑 30 天窗口，看社区实际抱怨与付费意愿讨论，比官网文案可信。
3. **竞品对比补证** —— `"X vs Y" --competitors`，拿 GitHub star 实时数与社区讨论量作为**辅助**信号（主判断仍走 `开源竞品与可复用能力.md` 那套「先判死再省钱」）。

> 定位建议：把它当**信号采集器**，不当分析器。它的输出是原料，PM 判断仍走 `调研\方法\` 那套框架。

---

## 附：一页速查

```bash
# 装
git clone https://github.com/mvanhorn/last30days-skill.git D:/tmp/last30days-skill
cp -r D:/tmp/last30days-skill/skills/last30days "C:/Users/zhangxinliang1/.workbuddy/skills/last30days"

# 查
PY="C:/Users/zhangxinliang1/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK="C:/Users/zhangxinliang1/.workbuddy/skills/last30days/scripts/last30days.py"
"$PY" "$SK" --preflight     # 预检
"$PY" "$SK" --diagnose      # 各源诊断

# 用
"$PY" "$SK" "话题" --emit=json
"$PY" "$SK" --discover "话题域"
"$PY" "$SK" "A vs B vs C" --competitors

# 升级
cd D:/tmp/last30days-skill && git pull
rm -rf "C:/Users/zhangxinliang1/.workbuddy/skills/last30days"
cp -r D:/tmp/last30days-skill/skills/last30days "C:/Users/zhangxinliang1/.workbuddy/skills/last30days"
```

---

## 附：缺口声明

- **未实测**：本文所有命令均来自仓库 README / SKILL.md 逐字提取，**未在本机实际运行**（未 clone、未安装）。第 2 节的环境核验是真实探测结果，但「装完能不能跑通」未知。
- **未取得**：仓库无公开的 issue 区 Windows 成功率统计；Windows 具体哪些源会挂，只能说「未验证」。
- **版本漂移**：基线 v3.28.0。该项目迭代快（changelog 密集），半年后参数表可能已变，重查 `skills/last30days/SKILL.md`（官方声明为命令与设置行为的唯一权威源）。
