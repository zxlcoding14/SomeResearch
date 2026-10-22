# 扫描全能王 × 白描 — Flutter 复刻可行性评估与实现方案

> 采集日：2026-10-15 · 前置文档：`扫描全能王×白描-iOS端能力拆解与开源替代盘点.md`
> 数字标签：`【审计】`=官方页面/文档可核 · `【实测】`=本次检索到的仓库/包页面原文 · `【二手】`=第三方 · `【预估·依据】`=有依据的估算 · `【未取得】`=进缺口清单
> 环境基线：Flutter 3.44+ / Dart 3.12+ / Xcode 16+ / iOS 16+（部分组件要求，见 §4）

---

## 0. TL;DR

| 问题 | 结论 |
|---|---|
| Flutter 能不能复刻 | **能，且比想象中乐观。** 采集、透视校正、印刷体 OCR、可搜索 PDF、PDF 编辑、内购这六层都有**成熟的开源 Flutter 组件**，MVP 可做到白描的 80% + 扫描全能王的 60%。 |
| 天花板在哪 | **三块必须绕开或外包**：① 实时相机帧处理管线（iOS 侧帧格式受限，Dart 侧处理开销大）；② 曲面去畸变/去阴影（无端侧成品）；③ 表格结构/公式/版面还原（需服务端模型）。 |
| 最大反直觉的坑 | **Flutter 生态里唯一的文档扫描器包（`google_mlkit_document_scanner`）在 iOS 上不可用**——官方支持矩阵明确标注 iOS ❌。iOS 只能走 VisionKit 封装包或自写插件。 |
| 推荐路线 | **路线 A（薄壳 + 系统能力）** 做 MVP，2–3 周可上架；要"拍出来像扫描仪"再叠加 **路线 C（服务端重处理）**。**不建议**一上来就自绘相机管线（路线 B），那是 2 倍工期的坑。 |
| 最小可行依赖集 | `cunning_document_scanner` + `google_mlkit_text_recognition` + `opencv_dart` + `pdf_document`/`dart_pdf_editor` + `in_app_purchase`（全部见 §2，许可均为 MIT / Apache-2.0） |
| 许可红线 | 避开 **Syncfusion Flutter PDF**（商业许可，免费 Community License 有 ≤5 开发者与营收门槛）；改用 `dart_pdf` 系（Apache-2.0）。 |

---

## 1. 复刻边界：三层能力分级

复刻前必须先认清：**扫描类 App 的能力不是均匀分布的**，它们分布在三个成本量级完全不同的层里。

### 1.1 开箱可得层（有现成 Flutter 包，1–3 人日/项）

| 能力 | 现成组件 | 说明 |
|---|---|---|
| 文档扫描采集（边缘检测 + 自动拍照 + 透视 + 多页 + 导出 PDF） | `cunning_document_scanner` | iOS 端封装 VisionKit，Android 端封装 ML Kit 文档扫描器 |
| 印刷体 OCR（中/日/韩/拉丁/天城文） | `google_mlkit_text_recognition` | iOS 支持；也识别手写（ML Kit 手写支持有限） |
| 端侧离线中文 OCR | `paddle_ocr_native`、`mobile_ocr` | 前者 ONNX PaddleOCR PP-OCRv6；后者 Android 走 ONNX、**iOS 走 Apple Vision** |
| 图像基础处理（灰度/模糊/Canny/轮廓/透视变换） | `opencv_dart`、`flutter_opencv_ffi`、`flutter_document_capture` | FFI 直调 OpenCV |
| 可搜索 PDF（不可见文字层） | `pdf_document` 的 `PdfEditor.injectTextLayer` / `applyOcr` | Apache-2.0，纯 Dart |
| PDF 阅读/编辑/批注/签名/表单 | `dart_pdf_editor` | Apache-2.0，含完整 UI 壳 |
| 内购与订阅 | `in_app_purchase`（官方） | iOS 默认 StoreKit 2 |
| 本地持久化 | `drift` / `sqflite` / `isar` | 文档库元数据 |
| 云同步 | `iCloud`（iOS 原生）/ 自建对象存储 | 跨端同步必须自建 |

### 1.2 需自研层（1–3 周/项）

| 能力 | 为什么不能开箱 | 自研路径 |
|---|---|---|
| 定制化扫描 UI | VisionKit 不暴露 UI 定制（不能改按钮/加滤镜开关）【实测】 | 自写 platform channel 调 AVFoundation + 自绘裁剪页 |
| 实时边缘检测叠加 | iOS 侧相机帧只有 BGRA8888/YUV420，无 JPEG；跨 channel 传输开销大 | 帧处理下沉到原生（Swift/C++）+ FFI，Dart 只收坐标 |
| 多栏/长图/竖排版面解析 | 通用 OCR 只给文本行 | 规则引擎 + 版面模型（见 §1.3） |
| 识别结果交互（画选区、同屏校对、逐行对应） | 无通用组件 | 基于 OCR 返回的 polygon 坐标自绘（`paddle_ocr_native` 与 `mobile_ocr` 都返回四点坐标） |
| 卡证字段结构化抽取 | 无开源通用方案 | 正则 + 位置规则，或自训模型 |

### 1.3 必须服务端层（无法端侧落地）

| 能力 | 原因 | 服务端方案 |
|---|---|---|
| 曲面去畸变（书脊/褶皱） | 端侧无工程化成品；DewarpNet/DocTr++ 均为 PyTorch 论文代码【实测】 | 服务端跑 DocTr++/UVDoc，返回矫正图 |
| 去阴影 | 同上（BEDSR-Net 等） | 同上 |
| 表格 → Excel | PP-StructureV3 体量大（含版面模型，官方示例模型 `pp_doclayout_l.onnx` 约 123 MB）【实测】 | 服务端 PP-StructureV3 / img2table |
| 公式 → LaTeX | PP-FormulaNet | 服务端 |
| 版面还原转 Word/PPT | 需版面坐标 + 生成器 | 服务端 PP-StructureV3 + docx 生成 |
| 高精度手写 | 端侧模型手写弱 | 服务端模型或商业 SDK |

> **一句话决策规则**：能在一秒内用一次屏幕触摸触发的 → 端侧；需要"整页理解"的 → 服务端。

---

## 2. 技术选型：Flutter 侧真实可用组件盘点

以下全部为本次实际核查过的包，含平台支持与坑。

### 2.1 采集层

| 包 | 平台 | 许可 | 状态 | 关键约束 |
|---|---|---|---|---|
| **`cunning_document_scanner`** | Android + iOS | MIT | 活跃（2025-12 更新） | iOS 封装 VisionKit；**iOS 不支持 scanner mode / 滤镜开关**（官方文档明示）；支持 `asPdf: true` 直接出 PDF；iOS 可配 PNG/JPEG 与压缩质量。Android 可限页数 |
| `flutter_document_capture` | iOS 12+ / Android 21+ | MIT | 较新（FFI + OpenCV） | 提供实时角点检测、模糊/亮度/稳定度评分、自动拍照触发、6 种增强模式（含 Sauvola 二值化）。**可用作自绘相机管线的起点** |
| `camera`（官方） | Android + iOS | BSD-3 | 官方维护 | `startImageStream` 在两个平台可用；**iOS 只给 BGRA8888 / YUV420，无 JPEG 帧**，Android 相反【实测】 |
| `simple_edge_detection` | Android + iOS | BSD-2 | 停滞（OpenCV 4.4） | 需手动放 OpenCV framework，仅静态图 |

**采集层结论**：先用 `cunning_document_scanner` 拿到"可用的扫描"，等产品验证了再考虑自绘。自绘的收益只有 UI 定制与滤镜可控，代价是 §1.2 的全部自研成本。

### 2.2 预处理层

| 用途 | 包 | 关键 API（以包内文档为准） |
|---|---|---|
| OpenCV 全功能 | **`opencv_dart`** | `cv.imdecode / cvtColor / gaussianBlur / canny / findNonZero / warpPerspective` |
| OpenCV（build hooks 自动拉预编译包） | `flutter_opencv_ffi` | `CvImage.imread / canny / resize / imencode`；iOS/Android 自动下载 OpenCV SDK |
| 文档专用预处理 | `flutter_document_capture` | `analyzeFrame` → `captureReady` → `enhanceImageWithGuideFrame(enhanceMode: ...)` |

**增强模式清单**（`flutter_document_capture` 实测枚举）：`none` / `whitenBg`（去背景）/ `contrastStretch`（推荐）/ `adaptiveBinarize` / `sauvola`。这一套已经覆盖了商业 App「黑白 / 灰度 / 增强」滤镜的技术内核。

### 2.3 识别层：四条路线必须选一条

| 路线 | 实现 | 实测数据 | 适用 |
|---|---|---|---|
| **① Apple Vision（推荐起步）** | `mobile_ocr`（iOS 分支）/ 自写 channel 调 `VNRecognizeTextRequest` | `mobile_ocr`：Android 走 ONNX PaddleOCR v5、**iOS 直接走 Vision**，同一套 Dart API 与 JSON 结构【实测】 | iOS 单端、要零成本零体积 |
| **② ML Kit** | `google_mlkit_text_recognition` 0.15.1（2026-02） | 30 天 17 万下载、1.25k Star；**iOS 最低部署目标 15.5**，Xcode 15.3+，须排除 armv7 架构【实测】 | 双端统一、要离线 |
| **③ 端侧 PaddleOCR** | `paddle_ocr_native`（ONNX + OpenCV，内置 PP-OCRv6 small 中英模型） | **iOS 16+ / 仅 arm64 真机，模拟器不支持**（OpenCV 4.3 依赖无 Apple Silicon 模拟器 slice）；仅 CocoaPods 不支持 SPM；Flutter 3.44 / Dart 3.12【实测】 | 中文精度优先、可接受"只能真机调试" |
| **④ 服务端 VLM** | `pdf_ocr_vlm` 走 HTTP | 支持 dots.ocr / PaddleOCR-VL / GOT-OCR 2.0；返回 bbox【实测】 | 要精度与版面，且接受上传 |

> ⚠️ **必须记住**：`google_mlkit_document_scanner`（文档扫描器）在官方支持矩阵里是 **Android ✅ / iOS ❌**【实测】。任何"用 Flutter 一次搞定双端文档扫描"的方案，在 iOS 上都会断——iOS 侧必须换成 VisionKit 封装包（`cunning_document_scanner`）或自写插件。
> ⚠️ 另有一条：`image_text_reader`（PaddleOCR v5 + ONNX）标称离线 OCR、MIT，但 **iOS 状态为 🚧 Planned，当前仅 Android**【实测】。

### 2.4 结构化输出层

| 需求 | 方案 |
|---|---|
| 表格 → Excel | 端侧 `img2table` 无 Flutter 版 → **走服务端**（PP-StructureV3 / img2table Python），Flutter 侧只做上传下载 |
| 版面还原 | 服务端 |
| 简单段落还原（自动分段） | 端侧可做：按 OCR 行的 y 坐标聚类 + 行距阈值 |
| 卡证字段抽取 | 端侧规则（正则 + 相对位置），参考开源名片扫描实现的启发式思路 |

### 2.5 PDF 与导出层

**首选 `dart_pdf` 套件（Apache-2.0，纯 Dart）**——本次最重要的发现：

| 包 | 职责 |
|---|---|
| `pdf_cos` | PDF 文件语法、对象、滤镜、加解密 |
| `pdf_document` | 页面树、批注、AcroForm 表单、数字签名、增量保存；**`PdfEditor.injectTextLayer` 写入不可见可搜索文字层**；`PdfEditor.applyOcr` 跑可插拔 OCR 引擎后注入文字层 |
| `pdf_graphics` | 内容流解释、字体、文本抽取 |
| `dart_pdf_editor` | Flutter 完整阅读/编辑器 UI（批注、页面重排、签名、表单、测量工具、Redact） |
| `pdf_ocr_ondevice` | 可选的原生离线 OCR 引擎 |
| `pdf_ocr_vlm` | 可选的 HTTP/VLM OCR 引擎 |

这意味着：**「扫描全能王的 PDF 编辑 + 可搜索 PDF」这一整层，可以直接用 Apache-2.0 组件拼出来**，不需要买 Syncfusion。对比传统 `pdf` + `printing`（dart_pdf 老套件，Apache-2.0），新套件在编辑器与 OCR 注入上更完整。

⚠️ **Syncfusion 替代警告**：`syncfusion_flutter_pdf` / `pdfviewer` 是商业包。34.x 起虽不再强制运行时 license key，但**仍要求持有商业许可或 Community 许可**（Community 门槛：≤5 名开发者 + 营收条件）【实测】。

### 2.6 存储与变现层

| 用途 | 组件 | 说明 |
|---|---|---|
| 本地库 | `drift` / `sqflite` | 文档元数据 + 页序 |
| 文件存储 | 沙盒 + `path_provider` | iOS 开文件共享便于调试 |
| 云同步 | CloudKit / 自建对象存储 | 跨端必须自建（对标扫描全能王 10 GB 云空间） |
| 内购 | **`in_app_purchase`（官方）** | iOS 13.0+ / Android SDK 24+；iOS/macOS **默认 StoreKit 2**【实测】 |
| 内购（托管） | `purchases_flutter`（RevenueCat） | 免自建收据校验后端；代价是抽成与数据归属 |
| 服务端 | 自建或托管 | 收据校验 + 订阅状态必须服务端做 |

**内购的现实**：`in_app_purchase` 只是"底层工具"——收据校验、订阅状态、续订/退订 webhook、试用期判断全部要自己建。若不想做后端，RevenueCat 是标准替代。

---

## 3. 三条技术路线对比

| 维度 | 路线 A：薄壳 + 系统能力 | 路线 B：自绘相机管线 | 路线 C：服务端重处理 |
|---|---|---|---|
| 采集 | `cunning_document_scanner`（VisionKit） | `camera` + OpenCV FFI + 自绘 UI | 同 A，图片上传 |
| 预处理 | VisionKit 自动增强 | 完全自研（含实时角点） | 服务端去畸变/去阴影 |
| OCR | Apple Vision / ML Kit | 端侧 PaddleOCR | 服务端 PP-StructureV3 / VLM |
| 表格/公式 | ✗ | ✗ | ✅ |
| 可搜索 PDF | ✅ `dart_pdf` | ✅ | ✅ |
| 包体 | 小（几十 MB 级） | 中（+OpenCV） | 小（模型在服务端） |
| 开发量 | **低** | 高（≈A 的 2 倍） | 中（含后端） |
| 隐私 | 全本地 | 全本地 | 需上传 |
| 体验上限 | 系统级（不可定制 UI） | 可逼近商业 App | 最高（扫描质量由服务端决定） |
| 适合 | 验证需求、MVP、单端 | 要做差异化相机体验 | 要做"扫描质量"卖点 |
| 工期（MVP）【预估·依据】 | 20–30 人日 | 45–70 人日 | 40–60 人日（含后端） |

**推荐组合**：先 A 上线 → 用数据判断用户是否真的在乎"扫描质量" → 若在乎，插 C（服务端处理），UI 完全不用改；**只有当 UI 定制成为核心卖点时才上 B**。

---

## 4. 关键工程约束清单（踩坑预防）

| # | 约束 | 后果 | 规避 |
|---|---|---|---|
| 1 | ML Kit 文档扫描器 iOS 不支持 | 双端一套代码的设想破产 | iOS 用 `cunning_document_scanner`；或用条件分支：iOS→VisionKit，Android→ML Kit |
| 2 | ML Kit iOS 最低部署目标 **15.5**，且不支持 32 位 | 老设备装不上；`flutter build ipa` 报错 | Podfile 设 `platform :ios, '15.5'`，Excluded Architectures 排除 armv7，post_install 统一 deployment target |
| 3 | `paddle_ocr_native` **不支持模拟器** | 开发调试必须插真机 | 预留一台真机；或用 `mobile_ocr`（iOS 走 Vision，模拟器可用）做开发期替身 |
| 4 | iOS 相机帧无 JPEG（仅 BGRA8888/YUV420） | 实时处理需自己做格式转换，开销大 | 帧处理下沉原生；或干脆放弃实时，改"拍照后处理" |
| 5 | Flutter 不能直接拿相机帧给 Dart 做视觉计算 | 用 `RepaintBoundary.toImage()` 每 500 ms 截图是常见 hack，但延迟高、耗电【二手·高】 | 生产环境禁止该 hack；走原生 + FFI |
| 6 | Syncfusion 是商业许可 | 上架后法务风险 | 用 `dart_pdf` 系（Apache-2.0） |
| 7 | OpenCV（iOS 静态 framework）要求静态链接 | CocoaPods 配置错误会链接失败 | `use_frameworks! :linkage => :static` |
| 8 | 包体积 | 内置模型会显著增大 | ML Kit 用单功能插件（勿用 umbrella `google_ml_kit`）；Paddle 用 small 模型；版面模型（123 MB）放服务端 |
| 9 | 服务端 OCR 涉及隐私合规 | 隐私政策必须披露上传 | 参照白描隐私政策写法：明示"文件上传服务器识别后返回，识别后删除" |

---

## 5. 复现步骤（分阶段可执行）

> 以下命令假设 macOS + Xcode 16+ + CocoaPods。iOS 构建与真机调试必须在 macOS 上完成（Windows 只能写代码，无法本地打包 iOS）。

### P0 · 环境与骨架（0.5–1 人日）

```bash
flutter --version          # 需 3.44+ / Dart 3.12+
flutter doctor -v          # 确认 Xcode / CocoaPods 正常

flutter create --org com.example --platforms=ios,android scan_clone
cd scan_clone
```

`pubspec.yaml` 最小集（路线 A）：

```yaml
name: scan_clone
environment:
  sdk: ">=3.12.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter
  # 采集
  cunning_document_scanner: ^2.7.0
  # OCR
  google_mlkit_text_recognition: ^0.15.1
  # 图像处理
  opencv_dart: ^1.4.0
  image: ^4.0.0
  # PDF
  pdf_document: ^1.2.2
  dart_pdf_editor: ^1.3.2
  # 存储
  path_provider: ^2.1.0
  drift: ^2.0.0
  # 变现
  in_app_purchase: ^3.2.0
  # 权限
  permission_handler: ^11.0.0

dev_dependencies:
  drift_dev: ^2.0.0
  build_runner: ^2.4.0
```

```bash
flutter pub get
```

**验收**：`flutter run` 能在真机上起一个空白 App。

> 版本号请以 pub.dev 当日为准（本次核查到的版本：`cunning_document_scanner` 文档页已存在 2.5.0/2.7.0，而部分聚合站快照仍显示 1.4.0，存在不一致，安装前核对一次）。

### P1 · 采集层（1–2 人日）

`ios/Runner/Info.plist` 增加：

```xml
<key>NSCameraUsageDescription</key>
<string>需要使用相机扫描文档</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>需要访问相册以导入图片进行识别</string>
```

`ios/Podfile` 按 §4 约束 2/7 配置：

```ruby
platform :ios, '15.5'

post_install do |installer|
  installer.pods_project.build_configurations.each do |config|
    config.build_settings["EXCLUDED_ARCHS[sdk=*]"] = "armv7"
    config.build_settings['IPHONEOS_DEPLOYMENT_TARGET'] = '15.5'
  end
  installer.pods_project.targets.each do |target|
    flutter_additional_ios_build_settings(target)
  end
end
```

调用扫描：

```dart
import 'package:cunning_document_scanner/cunning_document_scanner.dart';

final paths = await CunningDocumentScanner.getPictures(
  asPdf: false,
  scannerSource: ScannerSource.cameraAndGallery,
  iosScannerOptions: const IosScannerOptions(
    imageFormat: IosImageFormat.jpg,
    jpgCompressionQuality: 0.8,
  ),
);
```

**验收**：能从相机/相册拿到多页扫描图；用 `asPdf: true` 能直接产出 PDF。
**注意**：iOS 侧拿不到滤镜开关与 scanner mode（VisionKit 不暴露）——这是路线 A 的既定代价。

### P2 · 预处理层（3–5 人日）

```dart
import 'package:opencv_dart/opencv.dart' as cv;

Future<String> enhance(String src, String dst) async {
  final mat = cv.imdecode(File(src).readAsBytesSync(), cv.IMREAD_COLOR);
  final gray = cv.cvtColor(mat, cv.COLOR_BGR2GRAY);
  final denoised = cv.gaussianBlur(gray, (3, 3), 0);
  final binary = cv.adaptiveThreshold(
    denoised, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 25, 10,
  );
  cv.imwrite(dst, binary);
  return dst;
}
```

手动裁剪页（用户拖四角）需要：`cv.getPerspectiveTransform` + `cv.warpPerspective`（API 名以包内文档为准）。

**验收**：黑白/灰度/增强三档滤镜可用；手动四角裁剪后图像无残边。
**提示**：如果自绘管线太重，直接改用 `flutter_document_capture`，它已内置角点检测 + 质量评分 + 6 种增强模式。

### P3 · OCR 层（3–5 人日，路线 A）

```dart
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

final recognizer = TextRecognizer(script: TextRecognitionScript.chinese);
final input = InputImage.fromFilePath(imagePath);
final result = await recognizer.processImage(input);

for (final block in result.blocks) {
  for (final line in block.lines) {
    print('${line.text}  @ ${line.boundingBox}');
  }
}
await recognizer.close();
```

**验收**：拿到文本 + 每个文本行的 boundingBox（后续"画选区识别""同屏校对"都依赖这个坐标）。

若中文精度不够，切端侧 PaddleOCR：

```dart
import 'package:paddle_ocr_native/paddle_ocr_native.dart';

final ocr = PaddleOcr();
await ocr.init(config: const PaddleOcrConfig(), engine: const EngineConfig(numThreads: 4));
final run = await ocr.recognize('/absolute/path/to/image.jpg');
for (final r in run.results) {
  print('${r.text} ${r.confidence} ${r.points}');
}
await ocr.dispose();
```

**注意**：`paddle_ocr_native` 仅 iOS 16+ 真机（模拟器不支持），仅 CocoaPods。

### P4 · 可搜索 PDF（2–3 人日）

用 `pdf_document` 的 OCR 注入能力（`applyOcr` 会栅格化页面 → 跑 OCR 引擎 → 注入不可见可选可搜索文字层）：

```dart
import 'package:pdf_document/pdf_document.dart';

final doc = PdfDocument.open(bytes);
final editor = PdfEditor(doc);
// 有 OCR 引擎时走 applyOcr；只需注入已有坐标时用 injectTextLayer
final saved = editor.save();               // 增量保存
File(out).writeAsBytesSync(saved);
```

**验收**：生成的 PDF 看起来仍是扫描图（文字层不可见），但能在系统预览里选中、复制、搜索。

### P5 · 文档库与编辑（5–8 人日）

- 元数据表（`drift`）：id / 名称 / 页数 / 创建时间 / 标签 / 缩略图路径
- 页序拖拽、旋转、删除、追加页
- 水印、页码、手写签名（`dart_pdf_editor` 已含签名与批注工具）
- 批量导出（txt / md / docx / pdf）

**验收**：主流商业 App 的"文档管理"基础能力对齐。

### P6 · 内购与订阅（3–5 人日，含服务端校验则 +5 人日）

```dart
import 'package:in_app_purchase/in_app_purchase.dart';

final iap = InAppPurchase.instance;
final available = await iap.isAvailable();
final resp = await iap.queryProductDetails({'pro_yearly', 'pro_lifetime'});

final sub = iap.purchaseStream.listen((details) async {
  for (final d in details) {
    if (d.status == PurchaseStatus.purchased || d.status == PurchaseStatus.restored) {
      final ok = await verifyOnServer(d.verificationData.serverVerificationData);
      if (ok && d.pendingCompletePurchase) {
        await iap.completePurchase(d);
      }
    }
  }
});
await iap.buyNonConsumable(
  purchaseParam: PurchaseParam(productDetails: resp.productDetails.first),
);
```

**验收**：能购买、能恢复、重启后权益保留。
**必做**：收据校验放服务端。iOS 默认走 StoreKit 2，收据形态与 StoreKit 1 不同。

### P7 · 上架前检查（2–3 人日）

- App Store Connect：内购项配置、订阅组、隐私清单（`PrivacyInfo.xcprivacy`）
- 隐私政策：若走服务端 OCR，必须披露文件上传与删除策略
- 包体积实测：确认模型/OpenCV 未把包体推过红线
- 真机回归：老机型（iOS 15.5 边界）性能与内存

---

## 6. 工作量与成本估算

| 阶段 | 路线 A | 路线 B | 路线 C（增量） |
|---|---|---|---|
| P0 骨架 | 1 | 1 | +1 |
| P1 采集 | 2 | 10–15 | 0 |
| P2 预处理 | 4 | 12–20 | +3（服务端接口） |
| P3 OCR | 4 | 8–15 | +5（服务端部署调优） |
| P4 可搜索 PDF | 3 | 3 | 0 |
| P5 文档库 | 6 | 6 | +3（云同步） |
| P6 内购 | 4 | 4 | +5（服务端校验） |
| P7 上架 | 3 | 3 | +2 |
| **合计** | **27** | **47–67** | **+19** |

单位：人日。【预估·依据】——依据为「组件成熟度（有多少能直接复用）× 需自研比例 × 联调成本」，非实测工时。**敏感度**：若团队无 iOS/CocoaPods 经验，P0–P1 翻倍；若要求双端一致体验，需求本身不成立（iOS 侧组件与 Android 侧不同源）。

---

## 7. 结论与建议

1. **先做路线 A，不要做 B。** 采集层交给 VisionKit 是 Flutter 复刻扫描 App 最划算的一笔交易——它把最贵的相机/检测/校正一次性外包给了系统。代价只是"UI 不可定制"，而 MVP 阶段你不需要它。
2. **OCR 先上 Apple Vision，别一上来就端侧 PaddleOCR。** 理由是工程效率：Vision 零依赖、模拟器可用、包体为零；`paddle_ocr_native` 只能真机调试，会把开发循环拖慢。等确认中文精度不足再换。
3. **PDF 层千万别选 Syncfusion。** `dart_pdf` 套件（Apache-2.0）已经提供可搜索 PDF 注入 + 完整编辑器 UI + 签名/表单，是这次调研里性价比最高的一组依赖。
4. **"拍出来像扫描仪"这一层，端侧做不到，直接外包给服务端。** 这既是技术判断，也是产品判断：它正是用户愿意付费、且开源不留退路的地方。
5. **白描的护城河不在技术，别用技术去复刻它。** 它的 ¥30–¥40 买断、无广告、极致校对交互，是个人开发者的成本结构支撑的；用团队成本打这个价格带，商业模型不成立。

---

## 附 A｜数据明细

| 指标 | 数值 | 口径 | 来源级别 | 采集日 |
|---|---|---|---|---|
| cunning_document_scanner 平台/许可 | Android+iOS / MIT | pub.dev | 【实测】 | 2026-10-15 |
| cunning_document_scanner 版本 | 文档页存在 2.5.0 / 2.7.0；聚合站快照为 1.4.0（Dec, 2025） | 存在不一致，需现场核对 | 【实测】 | 2026-10-15 |
| cunning_document_scanner 热度 | 256 likes / 30 天 3.06 万下载 / GitHub 109 Star / 37 open issues | 聚合站快照 | 【二手·中高】 | 2026-10-15 |
| google_mlkit_text_recognition | 0.15.1（2026-02）；30 天 17.08 万下载；1.25k Star；iOS ✅ | pub.dev / 聚合站 | 【实测】 | 2026-10-15 |
| ML Kit iOS 最低部署目标 | 15.5；Xcode 15.3+；不支持 32 位（需排除 armv7） | 官方插件文档 | 【实测】 | 2026-10-15 |
| google_mlkit_document_scanner 平台 | Android ✅ / **iOS ❌** | 官方支持矩阵 | 【实测】 | 2026-10-15 |
| paddle_ocr_native 约束 | iOS 16+ arm64 真机；模拟器不支持；仅 CocoaPods；Flutter 3.44+/Dart 3.12+ | 官方文档 | 【实测】 | 2026-10-15 |
| paddle_ocr_native 模型 | PP-OCRv6 small 中英，内置 | 官方文档 | 【实测】 | 2026-10-15 |
| image_text_reader 平台 | Android ✅ / iOS 🚧 Planned | 官方文档 | 【实测】 | 2026-10-15 |
| mobile_ocr 架构 | Android ONNX(PaddleOCR v5) / iOS Apple Vision，共享 Dart API | 仓库 README | 【实测】 | 2026-10-15 |
| flutter_document_capture | iOS 12+ / Android 21+ / MIT；含 6 种增强模式；示例版面模型约 123 MB | 官方文档 | 【实测】 | 2026-10-15 |
| camera 插件 iOS 帧格式 | 仅 BGRA8888 / YUV420（无 JPEG）；Android 支持 YUV420/JPEG | 官方 API 文档 + 社区答复 | 【实测】 | 2026-10-15 |
| pdf_document 能力 | `injectTextLayer` 不可见可搜索文字层；`applyOcr` 可插拔引擎；Apache-2.0 | pub.dev | 【实测】 | 2026-10-15 |
| dart_pdf_editor 能力 | 完整阅读/编辑 UI、批注、签名、表单、Redact；Apache-2.0 | pub.dev changelog | 【实测】 | 2026-10-15 |
| Syncfusion Flutter PDF 许可 | 商业许可或免费 Community 许可（≤5 开发者）；34.x 起无需运行时 key 但仍需许可 | 官方文档 + 第三方 ADR | 【实测 + 二手·中高】 | 2026-10-15 |
| in_app_purchase | 官方插件；iOS 13.0+ / Android SDK 24+ / macOS 10.15+；iOS 默认 StoreKit 2 | 官方 README | 【实测】 | 2026-10-15 |
| 工作量估算 | 路线 A 27 人日 / B 47–67 / C 增量 19 | 组件成熟度 × 自研比例 | 【预估·依据】 | 2026-10-15 |

## 附 B｜估算过程与敏感度

与实测数据分开排版。以下是 §6 工期的推算依据：

**B1. 路线 A 的 27 人日怎么来的**
- 已可复用的部分（采集、OCR 调用、PDF 注入、内购 API）→ 按"集成 + 联调"计，约占 12 人日。
- 需自研的部分（预处理滤镜链、文档库 CRUD、页序交互、上架配置）→ 约 15 人日。
- 依据：每个"开箱可得项"的集成成本按 1–3 人日估（含真机调试与边界情况），每项自研功能按 3–6 人日估。
- 置信度：**中**。样本量小（未做实测开发），核心不确定性在 §4 的 9 条约束会不会额外触发联调。

**B2. 敏感度**
| 变量 | 变动 | 对路线 A 工期的影响 | 结论是否翻转 |
|---|---|---|---|
| 团队无 iOS/CocoaPods 经验 | P0–P1 翻倍 | +5–8 人日 | 不翻转 |
| 需要自绘相机 UI | 转入路线 B | +20–40 人日 | **翻转**（应重新评估是否值得） |
| 中文精度不达标需切端侧 PaddleOCR | P3 翻倍且开发循环变慢 | +5–10 人日 | 不翻转 |
| 需要云同步 / 多端 | P5 + 后端 | +10–20 人日 | 不翻转 |
| 需要表格转 Excel | 必须上服务端 | +8–15 人日 | 不翻转 |

## 附 C｜缺口声明与应查未查

| 项 | 状态 | 建议路径 | 优先级 |
|---|---|---|---|
| `cunning_document_scanner` 当前真实最新版本 | 信息冲突（1.4.0 vs 2.5.0/2.7.0） | 打开 pub.dev 包页核对 | 高 |
| `opencv_dart` 的透视变换 API 确切签名 | 未取得 | 读包内 API reference | 高 |
| 各方案 iOS 包体增量实测值 | 未取得 | 建最小工程分别打包对比（`flutter build ipa --analyze-size`） | 高 |
| `paddle_ocr_native` 中文精度实测 | 未取得 | 自建测试集（印刷体/手写/表格各 50 张）跑准确率 | 中 |
| Apple Vision 与 PaddleOCR 在中文场景的准确率差 | 只有二手数字（94% vs 95–96%），来源为百度系文章，可信度中 | 自测 | 中 |
| `dart_pdf` 套件的生产稳定性与社区规模 | 未取得（Star、issue 响应速度未采集） | 查各仓库活跃度 | 中 |
| 服务端 PP-StructureV3 的部署成本（GPU 规格） | 未取得 | 按官方 benchmark 文档核算 | 中 |
| App Store 对"扫描 + 上传识别"类 App 的审核边界 | 未取得 | 查审核指南 5.1.1/5.1.2 及同类被拒案例 | 中 |

## 附 D｜开源依赖与许可清单

| 包 / 项目 | 许可 | 商用闭源 | 备注 |
|---|---|---|---|
| `cunning_document_scanner` | MIT | ✅ | — |
| `google_mlkit_text_recognition` | MIT（插件）/ ML Kit 自身为免费闭源 SDK | ✅ | 模型随包分发，注意包体 |
| `paddle_ocr_native` | 未核实（社区包） | ❓ | 使用前读 LICENSE；模型源自 PaddleOCR（Apache-2.0，权重版权归百度） |
| `mobile_ocr`（ente-io） | 仓库含 LICENSE 文件，具体类型未核实 | ❓ | 使用前核对 |
| `opencv_dart` / `flutter_opencv_ffi` | 未核实（OpenCV 本身为 Apache-2.0） | ❓ | 核对包内 LICENSE |
| `flutter_document_capture` | MIT | ✅ | — |
| `pdf_cos` / `pdf_document` / `pdf_graphics` / `dart_pdf_editor` | Apache-2.0 | ✅ | **推荐替代 Syncfusion** |
| `pdf_ocr_vlm` / `pdf_ocr_ondevice` | 未核实（同作者套件） | ❓ | 核对 |
| `pdf` + `printing`（dart_pdf 老套件） | Apache-2.0 | ✅ | 纯生成/打印场景可用 |
| `camera` / `in_app_purchase` / `permission_handler` | BSD-3 / BSD-3 / MIT | ✅ | Flutter 官方与主流 |
| `Syncfusion Flutter PDF / PDF Viewer` | 商业许可（或 ≤5 开发者 Community 许可） | ⚠️ 有条件 | **建议避开** |
| Apple VisionKit / Vision | 系统闭源框架 | ✅ | 免费但不可定制 |
| Google ML Kit Document Scanner | 免费闭源 | ❌ iOS 不可用 | 仅 Android |

---

## 一句话总结

**Flutter 复刻扫描类 App，成败不在 Flutter，而在你是否接受"把采集和识别外包给系统、把图像恢复外包给服务端"。** 接受 → 27 人日能做出可上架的 MVP；不接受 → 你会花两倍工期去重造一个更差的 VisionKit。
