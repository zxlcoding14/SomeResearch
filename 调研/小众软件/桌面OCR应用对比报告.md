# 桌面 OCR 应用全景对比报告

> 信息源：小众软件论坛帖子《桌面 OCR 应用》全部 9 层楼层（2023-02）
> 帖子链接：https://meta.appinn.net/t/topic/40814
> 报告视角：产品经理 | 结构：漏斗形（结论先行 → 分层收敛 → 表格展开）

---

## 一、结论先行

1. **帖子共涉及 9 款桌面 OCR 工具**，按形态分 4 类：独立开源 OCR 工具（5 款）、买断制商业软件（白描）、大厂生态附属功能（微信/QQ、有道）、垂直场景工具（LunaTranslator）。
2. **OCR 工具层已被"免费化"压扁**：PaddleOCR、Tesseract、Windows 内置 OCR API 让识别引擎本身零成本，纯 OCR 工具几乎无法收费；9 款中 7 款免费，唯一活下来的付费模式是白描的"一次买断 + 多端通用 + 垂直增值功能"。
3. **最大威胁来自"隐形玩家"**：微信/QQ 截图 OCR、有道词典截图翻译把 OCR 做成免费附属功能，触达数亿用户，独立 OCR 工具的天花板被结构性压低。
4. **活路只有垂直化**：白描（表格转 Excel/公式转 LaTeX/证件扫描）、LunaTranslator（Galgame 实时翻译）、Umi-OCR（离线批量/PDF）都是靠场景纵深而非"识别准"取胜。

---

## 二、产品分层全景（第一层收敛）

### 第 1 类：独立开源 OCR 工具（免费、离线优先）
| 产品 | 引擎/协议 | 平台 | 特点 |
|---|---|---|---|
| **Umi-OCR** | PaddleOCR，开源免费 | Win10/11 | 截屏+批量图片+PDF 识别+二维码生成，离线运行，导出 txt/md/jsonl；缺点：高分屏界面模糊 |
| **gImageReader** | Tesseract，GPL-3.0 | Win/Linux | 内置截图识别、一键去除换行空格；书籍照片识别效果一般；薄荷开源网实测优于 OCRFeeder |
| **Text-Grab** | Windows 内置 OCR API / Tesseract，MIT | Windows | 极简 UI、几乎无后台占用、常用短语管理；作者即 PowerToys Text Extractor 开发者 |
| **dpScreenOCR** | 开源（zlib） | Win/Linux | 功能极简只做截图识别，亮点是**同时识别多种语言** |
| **tianruoocr-cl** | PaddleOCR/Chinese-lite，GPL-3.0 | Windows | 天若 OCR 的开源本地版，推荐 PaddleOCR 引擎 |

### 第 2 类：买断制商业软件
| 产品 | 定位 | 定价（真实数据） |
|---|---|---|
| **白描** | 多平台 OCR 扫描识别全家桶：文字/表格/公式/手写/竖排识别、翻译、文档扫描、PDF 识别，Web/Win/Mac/iOS/安卓/小程序 | **一次买断制**：普通会员 ¥18、黄金会员 ¥40（历史促销 ¥10/¥25）；一次付费终身有效、多端同步；免费版每日 5 次识别/1 次批量/3 次翻译。来源：腾讯云开发者社区（2020）及正版渠道活动页 |

### 第 3 类：大厂生态附属功能（免费、不开源）
| 产品 | 定位 |
|---|---|
| **微信/QQ 截图 OCR** | 常用 IM 自带，"少装一个 app"；缺点：需联网，不能离线 |
| **网易有道词典截图翻译** | 截图+翻译一体，游戏/网页场景顺手；背靠有道词典生态 |

### 第 4 类：垂直场景工具
| 产品 | 定位 |
|---|---|
| **LunaTranslator**（开源，GitHub） | Galgame 翻译器：HOOK / OCR / 剪贴板三种取词方式，视觉小说实时翻译——OCR 的游戏化刚需场景，发帖人原话"OCR 用的最多的时候当然是玩游戏" |

---

## 三、商业化对比（PM 视角）

| 产品 | 模式 | 数据点 |
|---|---|---|
| 白描 | **买断制会员**（该帖唯一明确收费产品） | 免费版 5 次/天 → 普通会员 ¥18（无限识别）→ 黄金会员 ¥40（全部无限）；一次付费多端通用；开发者个人作品起家（"给女朋友做的"），后获 App Store/华为市场推荐 |
| 微信/QQ/有道 | 免费引流 | OCR 是 IM/词典的附属能力，不独立变现，目的是提升主产品粘性 |
| Umi-OCR 等 5 款开源 | 完全免费 | 靠 GitHub 社区声誉，无直接变现 |

### 解读

1. **引擎免费 → 工具免费 → 唯一收费点是"场景增值"**。白描敢收 ¥40 买断，卖的不是识别准确率（开源引擎一样准），而是表格转 Excel、公式转 LaTeX、证件照扫描这类"识别之后"的交付能力。
2. **买断制而非订阅制**：OCR 使用频次低于清理类工具、替代品（免费开源+微信自带）极多，订阅制没有生存空间；¥18~40 的低门槛买断+多端同步是该品类收费上限。
3. **独立 OCR 工具的 TAM 被两端挤压**：上端是微信/有道等免费附属功能（泛用户），下端是开源引擎组装品（极客用户）；中间留下的只有"愿意为省事付费的大众效率用户"——这正是白描的生态位。
4. **垂直场景是第二增长曲线**：LunaTranslator 证明 OCR 在游戏翻译场景有强刚需且几乎无竞品覆盖；同理可推 PDF 批量（Umi-OCR）、无障碍场景等。

---

## 四、差异化能力矩阵（第二层收敛）

| 维度 | Umi-OCR | 白描 | gImageReader | Text-Grab | dpScreenOCR | tianruoocr-cl | LunaTranslator | 微信/QQ | 有道 |
|---|---|---|---|---|---|---|---|---|---|
| 免费离线 | ✅ | ❌（联网） | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| 批量图片/PDF | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 表格→Excel | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 公式→LaTeX | 部分 | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| 翻译集成 | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 多语言同屏识别 | ✅ | ✅ | ✅ | ✅ | ✅ 特色 | ✅ | ✅ | ❌ | ✅ |
| 平台数 | 1 | 6 | 2 | 1 | 2 | 1 | 1 | 2 | 多端 |
| 开源 | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |

**一句话差异点**：Umi-OCR = 免费离线全能桶；白描 = 唯一付费玩家的多端扫描全家桶；Text-Grab = Windows 极简截图取词；dpScreenOCR = 多语言同屏极简款；gImageReader = Linux/Tesseract 生态首选；LunaTranslator = Galgame 翻译刚需；微信/有道 = 免费附属功能的降维打击。

---

## 五、链接清单

**来源帖**
- 帖子：https://meta.appinn.net/t/topic/40814
- Umi-OCR 介绍：https://www.appinn.com/umi-ocr/（帖内引用）
- 白描 Win 版报道：https://www.appinn.com/baimiao-windows/（帖内引用）

**产品链接**
| 产品 | 链接 |
|---|---|
| Umi-OCR | https://github.com/hiroi-sora/Umi-OCR |
| 白描 | https://baimiao.uzero.cn |
| gImageReader | https://github.com/manisandro/gImageReader |
| Text-Grab | https://github.com/TheJoeFin/Text-Grab |
| dpScreenOCR | https://github.com/danpla/dpscreenocr |
| tianruoocr-cl | https://gitee.com/wanglifree/tianruoocr-cl |
| LunaTranslator | https://github.com/HIllya51/LunaTranslator |
| 有道词典 | https://cidian.youdao.com |

---

## 六、PM 行动启示（最后收敛）

1. 该品类**不要做"又一个截图 OCR"**——Text-Grab/dpScreenOCR/微信已把免费下限拉满；要进只能靠垂直场景（表格/公式/游戏/无障碍）或多端买断（白描路线，但窗口极窄）。
2. **引擎选型即产品定义**：PaddleOCR（中文强、可离线打包）是中文市场事实标准，Windows 内置 API 适合极简轻量，Tesseract 适合开源/Linux 生态。
3. 对照上一个卸载工具调研：OCR 品类的商业化空间**比卸载器更小**（连订阅制都撑不起来），独立开发者入局优先选"OCR + X"的 X（X = 翻译/文档管理/游戏辅助），而非 OCR 本身。
