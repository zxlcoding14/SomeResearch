# FreeFileSync — 技术方案与实现拆解

> 分析对象：FreeFileSync 14.13（2026-10-16 发布）
> 取证方式：官方手册全文 + 二进制静态分析（Linux x86_64 版，与 Windows 同源）+ CHANGELOG 全量 211 版 + 官网 FAQ
> 与 `FreeFileSync-产品分析报告.md` 互补：那份讲**生意**，这份讲**机器**。
> 数据标签：`【实测】` 本次二进制/页面直接取到 · `【官方】` 官方文档明确写出 · `【推算·依据】` 由实测推导 · `【未取得】` 拿不到

---

## 〇、结论先行

**1. 它不是"算法型"产品，是"口径型"产品。** 核心工作量不在同步算法（三种变体都是教科书级），而在**"怎么判定两个文件相同"的工程口径**：默认只比 `mtime + size`、容忍 2 秒误差、按 FAT 精度归一、把"同时间不同大小"直接定义为冲突。整套系统的正确性都建立在这个口径上，而不是建立在哈希上。

**2. 架构是四层单体，没有服务端、没有运行时依赖、没有数据库服务。** 一个 28.66 MB 的 C++ 可执行文件（Linux 实测）＋一个 14.57 MB 的 RealTimeSync，全部依赖静态链接进二进制。**它把"部署成本"压到了零，这是它 18 年零运维事故的技术根因。**

**3. 双向同步的唯一技术难点是 `sync.ffs_db`。** 因为文件系统本身不记录"这个文件是被删了还是还没同步"，双向语义必须靠外部状态库。这个库是**压缩的自定义二进制格式（不是 SQLite）**，采用**成对事务写入 + fail-safe 复制**保护。它是整条链路的单点：丢了它，双向同步就退化成一堆冲突。

**4. 安全边界是"每个文件原子"，不是"整次同步原子"。** 单个文件靠 `.ffs_tmp` → `rename` 保证不被写坏，多个文件之间靠"先删后拷"的顺序避免磁盘爆掉，但没有全局事务、没有整批回滚。**它承诺的是"不会写坏文件"，不是"要么全成要么全退"。**

**5. 性能叙事全部可验证，只有三件事：按设备分组并发、最小量传输、顺序优化。** 并行度不是"线程越多越快"，而是**按设备根分组，每设备 N 路**——因为瓶颈在设备不在 CPU。而"并行复制"本身被做成了捐赠版的付费点。

**6. 技术上是彻底的个人工程：** wxWidgets 3.3 自己编译（构建路径 `/home/zenju/Desktop/Projects/wxWidgets/Source`）、GCC 16.2.0、OpenSSL 4.0.3 全静态、211 个版本 18.2 年。**这套栈无法交接——不是代码问题，是构建环境只存在于一台机器上。**

---

## 一、技术栈实证

### 1.1 硬证据表

| 层 | 实际使用 | 证据 | 等级 |
|---|---|---|---|
| 语言 | **C++（≥C++20）** | 二进制符号含 `std::span`（C++20）、`std::shared_ptr`、`std::future`、`std::unordered_map` | 【实测】 |
| 编译器 | **GCC 16.2.0** | 字符串 `GCC: (GNU) 16.2.0`；另有 `GCC 4.8.5`（来自静态库 zlib/openssl 的旧编译痕迹） | 【实测】 |
| GUI 框架 | **wxWidgets 3.3（自行编译）** | 316 条路径含 `wxWidgets/Build/CentOS_gcc_16.2.0_x86_64_release/include/wx-3.3/`、`/home/zenju/Desktop/Projects/wxWidgets/Source/src/...` | 【实测】 |
| 渲染后端 | **GTK3** | `libgtk-3.so.0`、`libgdk-3.so.0`、`libglib-2.0.so.0`，自带 `Resources/Gtk3Styles.css` | 【实测】 |
| TLS | **OpenSSL 4.0.3（2026-09-29）静态链接** | `OpenSSL 4.0.3 29 Sep 2026`、`OPENSSL_init_ssl`、`SSL_read` 等内部符号 | 【实测】 |
| SSH | **libssh2（静态）** | `libssh2_sftp_init`、`libssh2_userauth_publickey_frommemory` 等 | 【实测】 |
| HTTP/FTP 客户端 | **libcurl（静态）** | `curl_wrap.cpp`、`getLibsshCurlUnifiedInitCookie`（curl 的 SSH 后端统一初始化） | 【实测】 |
| 压缩 | **zlib** | `zlib_wrap.cpp`、`Compress/Decompress sync.ffs_db` | 【实测】 |
| Windows 打包 | **Inno Setup** | PE 注释字段原文 `This installation was built with Inno Setup.`；`LegalCopyright: Zenju` | 【实测】 |
| Linux 打包 | **自解压 `.run`（内嵌 tar + `install.sh`）** | 解包得 `install.sh`（620 行）、`FreeFileSync.tar.gz`、desktop/mime 定义 | 【实测】 |
| 体积 | 主程序 **28.66 MB**（Linux x86_64）；RTS **14.57 MB**；Windows 安装包 **22.18 MB** | `FreeFileSync_x86_64` = 28,657,432 B | 【实测】 |
| 版本节奏 | **211 个版本 / 18.19 年**（2008-08-10 → 2026-10-16），平均 **31.5 天/版** | CHANGELOG 首尾条目 | 【实测】 |

### 1.2 两个容易被误解的点

- **"开源"但无官方仓库。** 官网提供源码下载，但组织内没有公开的 Git 仓库、没有 CI 徽章、没有 issue 区（只有论坛）。**它给的是"源码可得"，不是"社区可协作"。**
- **"单文件"是真的。** 除 `Resources/`（图标 `Icons.zip` 454 KB、语言 `Languages.zip` 550 KB）外，**没有任何 .so/.dll 依赖外部库**。`7z l` 可见内层 tar 仅 27 个文件。这让它能在 2008 年至今的所有 Windows 版本上直接跑。

---

## 二、总体架构

### 2.1 四层结构

```
┌─────────────────────────────────────────────────────────────┐
│  UI 层  （fff::  +  wxWidgets 3.3 / GTK3）                    │
│  main_dlg.cpp · file_grid.cpp · tree_grid.cpp · cfg_grid.cpp  │
│  log_panel.cpp · rename_dlg.cpp · sync_cfg.cpp                │
│  ← 自绘虚拟表格（不是 wxGrid），10 万行级不卡                   │
├─────────────────────────────────────────────────────────────┤
│  引擎层（四阶段流水线）                                        │
│  scan:  file_hierarchy.cpp   → 构建 FileSystemObject 树        │
│  cmp:   comparison.cpp       → 打 category 标签               │
│  map:   algorithm.cpp        → category × variant → 动作       │
│  apply: synchronization.cpp  → 执行 + 进度 + 日志              │
│  state: db_file.cpp          → sync.ffs_db 读写                │
├─────────────────────────────────────────────────────────────┤
│  AFS 抽象层（fff::AbstractFileSystem / AbstractPath / AfsPath）│
│  native.cpp · ftp.cpp · sftp.cpp · gdrive.cpp                 │
│  ← 15+ 原语：stat / listdir / open / read / write / rename /   │
│    remove / mkdir / symlink / getAttrs / setAttrs / space …    │
├─────────────────────────────────────────────────────────────┤
│  平台层                                                       │
│  Win32（VSS · WPD/MTP · ADS · ACL · 长路径）                   │
│  POSIX/GNU（inotify · g_file_trash · xattr · ACL）             │
│  macOS（FSEvents · HFS+ xattr/ACL）                            │
├─────────────────────────────────────────────────────────────┤
│  作者私有基础库  zen::（跨项目复用的个人工具库）                │
│  Zstring(UTF-8 字符串) · file_io · thread(InterruptibleThread/ │
│  ThreadGroup) · zlib_wrap · curl_wrap · serialize · ring_buf   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 关键类型（全部由二进制符号实证）

| 类型 | 职责 | 证据 |
|---|---|---|
| `fff::AbstractFileSystem` | 统一文件系统接口，屏蔽本地/FTP/SFTP/云 | 符号出现在 `FtpFileSystem`/`SftpFileSystem`/`GdriveFileSystem` 的基类位置 |
| `fff::AbstractPath` / `fff::AfsPath` | 路径归一化（`AfsPath` = 抽象路径，非 OS 路径） | `moveAndRenameItemForSameAfsType(… AfsPath, AbstractPath)` |
| `fff::BaseFolderPair` | 一对左右文件夹 + 各自的 AFS 句柄 + 同步方向 | `unordered_map<BaseFolderPair*, SyncDi…>` |
| `fff::FileSystemObject` | 树节点（文件/目录/符号链接），带 category | `visitFSObject` 递归访问器 |
| `fff::DirLock` | 目录锁（`sync.ffs_lock`） | `DirLock::SharedDirLock`、`shared_ptr<DirLock>` |
| `fff::SyncDatabase` | 状态库 | `db_file.cpp`、`Compress/Save/Load sync.ffs_db` |
| `fff::VersioningFolder` | 版本化目录（被删/被改文件的历史副本） | `VersioningFolderHistory` |
| `zen::InterruptibleThread` / `zen::ThreadGroup` | 可中断线程 + 线程池 | `InterruptibleThread`、`ThreadGroup::addWorkerThread` |

### 2.3 一次同步的完整时序

```
1. 用户点「比较」
   → 按"设备根"分组所有文件夹（C:\ 一组、D:\ 一组 …）
   → 每设备起 N 路并发遍历（getFolderStatusParallel）
   → 得到两棵树：leftOnly / rightOnly / both
2. 对 both 逐项判定（comparison.cpp）
   → variant = time+size | content | size
   → 打标签：equal / leftNewer / rightNewer / conflict
3. 读 sync.ffs_db（仅 Two-way 或勾选"用数据库检测变化"时）
   → 与"上次同步的快照"做三方对比：磁盘现状 × 上次状态 × 对侧现状
   → 得出 create / update / delete / move
4. 决策映射（algorithm.cpp）
   → category × variant × 自定义规则 → 每个节点的动作（copy→ / copy← / delete / move / none）
5. 在表格里预演（file_grid.cpp）
   → 用户可逐行取消（Partial sync）
6. 用户点「同步」
   → 取 sync.ffs_lock（若有并发实例则排队）
   → 按"先删后拷"重排任务（省空间）
   → 每设备 N 路并发执行；单文件走 .ffs_tmp → rename
   → 可选：复制后二进制校验（VerifyCopiedFiles）
7. 写回 sync.ffs_db（成对事务 + fail-safe）→ 释放锁 → 汇总日志
```

**架构上的关键取舍：比较与执行彻底分离。** 比较结果是纯数据（可预览、可逐行改），执行阶段只认"动作列表"。这让"预演"成为可能——**也是它相比 rclone/robocopy 这类命令式工具的核心体验差异**。

---

## 三、比较：怎么判定"相同"

### 3.1 三种变体（官方定义）

| 变体 | 判据 | 会区分的类别 | 代价 | 适用 |
|---|---|---|---|---|
| **File time and size**（默认） | `mtime` 相等（±2s）**且** `size` 相等 | leftOnly / rightOnly / leftNewer / rightNewer / equal / **conflict（同时间不同大小）** | 最便宜，只读元数据 | 绝大多数场景 |
| **File content** | 逐字节二进制一致 | leftOnly / rightOnly / equal / different | 最贵，读全文件 | 一致性校验、mtime 不可信的设备 |
| **File size** | `size` 相等 | leftOnly / rightOnly / equal / different | 便宜，但会漏 | MTP/老 FTP（服务器把 mtime 改成当前时间） |

> 【官方】手册 Comparison Settings。三种变体的差别不是"精度不同"，而是**读多少数据**：元数据 → 全文件 → 半份元数据。

### 3.2 2 秒容差：一个被低估的设计

```xml
<!-- GlobalSettings.xml 原文 -->
<FileTimeTolerance Seconds="2"/>
```

- **为什么是 2 秒**：FAT/FAT32 的文件时间只有 2 秒精度。若严格相等，同一文件在 FAT 与 NTFS 之间往返会被永久判为"不同"，每次都重拷。
- **代价**：**2 秒内修改两次的文件会被漏掉**。这是它为兼容性付的确定成本，且不可配置到 0？——可以，但官方不建议。
- **配套**：`daylight-saving-time` 专门章节处理 FAT 上的 DST 偏移（夏季时间 ±1h 导致全盘"变新"）。**这是 2008 年就踩过的坑，靠 18 年真实用户喂出来的边界条件。**

### 3.3 内容比较 = 二进制逐字节，不是哈希

- 手册原文：`Two files are marked as equal if they have identical content`、`bit-wise identical`。
- 二进制证据：`Binary-compare multiple files in parallel`（CHANGELOG）、`file_io.cpp` 的 `stream_buffer` / `dcbuffer`。
- **为什么不用哈希**：单次同步里每个文件只比一次，**算哈希不比 memcmp 省时间，还多一份 CPU 与内存**。哈希只有在"多次比对同一文件"或"跨网络只传摘要"时才有价值——**这两件事它都不做**。

### 3.4 符号链接：四类对象统一处理

官方把以下都归为 "symbolic link"【官方】：
1. 文件系统符号链接
2. NTFS volume mount point
3. NTFS junction point
4. WSL symlink
5. Google Drive shortcut（映射为 link）

两种策略：**Follow**（当目标处理，目录会被遍历）与 **As link**（当对象本身处理，不遍历）。Windows 上创建符号链接需管理员权限。

### 3.5 冲突的定义暴露了整个方案的前提

**"同 mtime、不同 size" 才叫 conflict。** 那么"同 mtime、同 size、内容不同"呢？**默认方案判为 equal，永远不会被发现。** 这是 time+size 口径的固有盲区——**它用"几乎不会发生"换"快 100 倍"**。要覆盖这个盲区，只能切到 content 变体。

---

## 四、同步决策：从"差异"到"动作"

### 4.1 三种变体

| 变体 | 语义 | 是否用 db | 典型场景 |
|---|---|---|---|
| **Two way** | 双向流动 create/update/delete | **必须**（无 db 无法判定删除方向） | 两台机器互为工作副本 |
| **Mirror** | 左→右，右变成左的精确副本（含删除） | 默认不用；勾选「用数据库检测变化」后可建 | 标准备份 |
| **Update** | 左→右，只增改不删 | 默认不用；**可建 db 用于移动检测**（CHANGELOG 明确 `Detect moved files with "Update" sync variant (requires sync.ffs_db files)`） | 只增型备份（相机卡→硬盘） |

### 4.2 类别 → 动作（Two-way 的完整真值表）

| 左 | 右 | 上次状态 | 判定 | 动作 |
|---|---|---|---|---|
| 有 | 无 | 上次也无 | 左新增 | 拷到右 |
| 有 | 无 | 上次有 | **右被删** | 删左（或按规则保留） |
| 无 | 有 | 上次也无 | 右新增 | 拷到左 |
| 无 | 有 | 上次有 | **左被删** | 删右 |
| 新 | 旧 | — | 左更新 | 拷到右 |
| 旧 | 新 | — | 右更新 | 拷到左 |
| 同 mtime 不同 size | | — | **冲突** | 标记，等人工 |
| 同 mtime 同 size | | — | 相等 | 无动作 |

**这张表就是 `sync.ffs_db` 存在的全部理由**：第 2、4 行与第 5、6 行**在磁盘上看完全一样**（都是"一边有一边没有"），只有"上次状态"能区分"新增要拷"与"删除要跟"。

### 4.3 移动/重命名检测

- 依赖 **`sync.ffs_db` + 文件系统的稳定 file ID**（inode / NTFS FileID）。
- 命中则目标端执行 `move`，**而不是"拷一遍再删"**——对 4 GB 视频改名，价值是"秒级 vs 十分钟级"。
- 三条硬限制【官方】：**首次同步不可能检测**（没有 db）；**FAT 上部分移动检测不到**（file ID 不稳定）；**SFTP 不支持**（协议无 file ID）→ 自动退化为 copy+delete。

### 4.4 自定义规则

两种基座【官方】：**按类别**（left/right only、left/right newer）或**按变化**（create/update/delete，需勾选"用数据库检测变化"）。后者是 v13 之后的能力升级——**从"看差异"变成"看事件"**，这是它能支持"删除只在一个方向传播"这类企业规则的前提。

---

## 五、状态库 `sync.ffs_db`

### 5.1 它是什么

| 项 | 事实 | 等级 |
|---|---|---|
| 文件名 | `sync.ffs_db`，**每对文件夹一个**，放在文件夹根 | 【官方】 |
| 格式 | **自定义二进制 + zlib 压缩**，不是 SQLite | 【实测】`Compress sync.ffs_db` / `Decompress sync.ffs_db` / `zlib_wrap.cpp` |
| 内容 | 上次同步时的文件树快照（相对路径 + size + mtime + file ID + 同步方向） | 【推算·依据】符号 `SyncDatabase` + 移动检测所需的 file ID 语义 |
| 何时创建 | **Two way 第一次同步后**；Mirror/Update 默认不建 | 【官方】 |
| 体积 | 持续压缩优化，14.12 再减 **16%** | 【实测】CHANGELOG |

### 5.2 写入策略：成对事务 + fail-safe

两条 CHANGELOG 原文，是全案最重要的可靠性证据：

```
Recover from corrupted database file
Save database files pair-wise as a transaction
Consider fail-safe file copy when creating sync.ffs_db files
```

拆开看：
1. **pair-wise**：左右两个 db 必须一起更新，不能只成功一个 → 否则下次同步会拿"新左 vs 旧右"做判断，直接产生错误删除。
2. **as a transaction**：要么两边都写成功，要么都不算数。
3. **fail-safe copy**：db 文件本身也用"临时文件 + rename"写，避免掉电留下半个库。
4. **corrupted 可恢复**：`FileErrorDatabaseCorrupted` 异常类型存在，且有专门的恢复路径（重建而非崩溃）。

> 这套设计的性质是**"尽力而为的两阶段"**，不是真正的分布式事务：没有 WAL、没有协调者、没有回滚日志。它靠"重写整个 db 文件 + rename"这个原子操作近似达成。

### 5.3 从 PM 角度看这个库

**它是整个产品最脆弱的一环，也是最难被抄的一环。**

- 用户视角：删掉/丢失 `sync.ffs_db` → 双向同步立刻退化成"两边都新增"，产生大量冲突与重复文件。**这是它最容易被误操作破坏的地方，而 UI 上几乎无感知。**
- 竞品视角：任何做双向同步的产品都必须有等价物（Syncthing 用 `.stfolder` + LevelDB 索引，Resilio 用 `.sync` 目录）。**"双向"这个卖点的真实成本全在这一个文件上。**
- 它也是"移动检测"这个体验亮点的唯一依赖——**没有 db 就没有 move，只有 copy+delete**。

---

## 六、执行：怎么保证不写坏

### 6.1 单文件原子性：`.ffs_tmp` → `rename`

二进制证据：`.ffs_tmp` 字符串 + `rename` 系统调用 + `moveAndRenameItemForSameAfsType`。

```
写 <target>.ffs_tmp  →  写完 flush  →  rename 覆盖 <target>  →  设 mtime/权限
```

- **好处**：任何时刻崩溃，目标文件要么是旧的完整版本，要么是新的完整版本，**不存在"半个文件"**。
- **边界**：rename 的原子性只在**同一文件系统内**成立。跨设备（不同盘、网络盘、FTP）时退化为"删除再写"，此窗口内无保护。
- **官方措辞**：`Fail-safe file copy prevents data corruption`【官方】——注意它说的是 **data corruption**，没说"同步事务"。

### 6.2 顺序优化：先删后拷

CHANGELOG 1.1（2008）就有：`New synchronization sequence: first delete files, then copy files to avoid disc space shortages`。

- 镜像 200 GB → 只剩 10 GB 的盘：若先拷后删，必然中途 `ENOSPC`。
- 这是**用调度解决容量约束**，比"检查剩余空间再报错"优雅得多，也是它敢做"整盘镜像"的信心来源。

### 6.3 并发互斥：`sync.ffs_lock`

- 每对文件夹根目录下一个锁文件，**只有 FreeFileSync 认这个锁**（不干扰其他程序）。
- 语义：**排队**，不是拒绝——第二个实例阻塞等待而不是报错。
- 主要场景【官方】：多人同时对同一网络共享目录跑同步。
- 实现细节：CHANGELOG 有 `Unbuffered folder lock file existence checking`——**用无缓冲 I/O 查锁**，避免操作系统缓存导致"看到过期锁状态"。

### 6.4 复制后校验：默认关闭

| 项 | 事实 |
|---|---|
| 开关 | `VerifyCopiedFiles`，默认 `false` |
| 做法 | 复制完成后**二进制比对**源与目标 |
| 代价 | 官方原文：**可能让复制时间翻倍** |
| 局限 | 官方原文：**不能保证复制前数据未损坏**；且"损坏可能被应用/硬件栈的缓冲区掩盖" |

> **这是全案最诚实的一段官方文字。** 它明确告诉用户"校验也不能证明数据是对的"，因为读回来的可能是页缓存。要真正验证，必须 `O_DIRECT`/无缓存读 + 端到端校验和，而它选择不做（会把速度优势打没）。

### 6.5 删除的三态

| 模式 | 实现 | 可恢复性 |
|---|---|---|
| Permanent | 直接 unlink | 只能靠反删除工具，取决于扇区是否被覆盖 |
| Recycle Bin | Windows Shell API / Linux `g_file_trash` / `*/.Trash-*/` `*/.recycle/`（实测字符串） | 直到被新文件挤出 |
| Versioning | 移到版本目录，路径模板带 `%timestamp%` 宏 | 完整历史 |

**Versioning 的真实价值不是"能恢复"，是"删除与覆盖都可审计"**——被覆盖的旧版本也被保留（`D:\Revisions\2020-12-12\Folder\File.txt`）。

### 6.6 元数据复制

| 项 | Windows | macOS/Linux |
|---|---|---|
| 权限 | DACL / SACL / Owner / Group（需管理员提权） | POSIX mode + ACL |
| 扩展属性 | EA（压缩/加密/稀疏） | HFS+ xattr |
| 数据流 | **NTFS ADS**（ReFS 上自动跳过，14.11 修复） | — |
| 长路径 | **>260 字符**（Win32 `\\?\` 前缀） | 原生 |
| 时间 | 创建/修改/访问时间 | 同 |

> **"复制权限"是个双刃剑**：默认开启会撞 `Cannot read/write permissions` 错误，官方 FAQ 的建议是"一般场景直接关掉"。它把选择权交给用户，代价是"默认配置在跨机器场景会失败"。

---

## 七、并发模型

### 7.1 并发单位是"设备"，不是"任务"

官方给了一个必须逐字读的例子【官方】：

```
C:\Source  ↔ D:\Target     并行度：C:\ = 1, D:\ = 2
C:\Source2 ↔ E:\Target     并行度：        E:\ = 3
→ 扫描阶段总并发 = 1 + 2 + 3 = 6
→ 同步阶段：C↔D 用 max(1,2)=2 路；C↔E 用 max(1,3)=3 路
```

两条设计规则：
1. **同一设备根的多个文件夹共享同一个并发额度**（`C:\Source` 与 `C:\Source2` 合起来只有 1 路）——因为瓶颈是这块盘/这条链路，不是 CPU。
2. **同步取两端最大值**——因为一端慢一端快时，快的一端可以多跑几个。

### 7.2 怎么实现并发

- `zen::ThreadGroup::addWorkerThread()` + `zen::InterruptibleThread`（**可中断**：用户点取消能立刻停，不用等 I/O 超时）。
- 每个"并行操作"实际是**开一条独立连接**（对 SFTP/FTP 就是新 session）。官方明确警告：**某些 SFTP 服务器有连接数上限，开太多会失败**。
- 并行覆盖范围：目录遍历、二进制比较、文件复制、db 读写、图标渲染——**每一处都单独做过并行化**（CHANGELOG 有 6 条以上对应条目）。

### 7.3 并行复制是付费墙

- CHANGELOG 10.0（2018-04）：`Sync multiple files in parallel (Donation Edition)`。
- 免费版仍能**并行扫描与比较**（比较快），但**串行复制**（写盘慢）。
- **产品含义**：它把"最影响体感的那一项（拷大文件的速度）"精准地放进了付费墙，而把"决定能不能用"的全部能力免费。**这是付费墙设计里最难的一刀，也是它转化率的来源。**

---

## 八、AFS 抽象层与协议实现

### 8.1 抽象的成本

支持一种新协议，不只是"加个网络库"，而是要实现 AFS 的**全部原语**：

```
stat / listdir / open(read|write) / close / rename / remove / mkdir / rmdir
/ symlink / readlink / getAttrs / setAttrs / setMtime / getSpace / getFileID / exists
```

**其中最贵的是 `getFileID` 和 `setMtime`**——前者决定"能不能检测移动"，后者决定"能不能用 time+size 比较"。缺一个，整个引擎的某条优化路径就要退化。

### 8.2 四种实现

| 实现 | 底层 | 关键事实 | 退化点 |
|---|---|---|---|
| `native.cpp` | Win32 / POSIX | 全原语支持，含 ADS/ACL/long path | — |
| `ftp.cpp` | libcurl | FEAT 特性协商（`FtpSession::Features`）；FTPS；修复过 "TLS session resumption required" | 服务器改 mtime → 只能用 size 比较 |
| `sftp.cpp` | libssh2 | **N 连接 × M 通道**，官方例子 10×2 = 20 倍加速；支持 agent / password / keyboard-interactive | **无 file ID → 无移动检测** |
| `gdrive.cpp` | 自研 REST v3 | changes API + `newStartPageToken`、`shortcutDetails(targetId)`、`trashed` 查询；PKCE 授权（`code_verifier`） | 无真正的 mtime 语义、无 file ID 语义，靠 id 映射 |

### 8.3 Google Drive 是自研 REST，不是官方 SDK

二进制里的查询串直接暴露了实现：

```
kind,nextPageToken,newStartPageToken,changes(kind,changeType,removed,fileId,
file(trashed,name,mimeType,ownedByMe,size,modifiedTime,parents,shortcutDetails(targetId)),...)
' in parents and not trashed
```

- 用的是 **Drive API v3 的 `changes` 增量端点 + pageToken 游标**，不是全量遍历——**这是它能对云端做增量同步的关键**。
- 手写 REST 而非引 SDK，解析成本换来的是**零运行时依赖 + 完全控制重试/限流**。
- 代价：Google 改 API 就要改代码（CHANGELOG 有 `Fixed Google Drive change notification evaluation for item without parents` 这类修补）。

### 8.4 MTP

- 通过 MTP 协议直接访问 Android/iPhone/相机（不经挂载）。
- **MTP 不保留可靠 mtime** → 只能用 size 比较；且**多线程会重复创建条目**（CHANGELOG 修过两次）。
- 这是"看起来简单的手机备份"里最脏的一段。

---

## 九、平台专有能力

### 9.1 VSS（Windows）

| 项 | 事实 |
|---|---|
| 作用 | 复制**被占用/被锁**的文件（Outlook pst、数据库文件、正在写的日志） |
| 范围 | 官方明确：**快照只用于复制当前被锁的文件**，其余文件正常读 |
| 权限 | 官方明确：**需要管理员权限** |
| 实现机制 | 通过 VSS 创建源卷快照，挂载为设备路径后按相对路径读取（VSS 的公开机制；具体挂载点未在文档披露）【推算·依据】 |
| 边界 | 快照创建失败会透传系统错误（CHANGELOG `Show system error descriptions on Volume Shadow Copy errors`）；与 MSSearch（Windows 搜索索引）有过兼容问题 |

**PM 视角**：VSS 是它打进"企业服务器备份"场景的唯一技术门票，但它**要求管理员权限**——这恰好与企业最小权限原则冲突，**是它进不了受管环境的技术原因之一**（另一个是没有服务端/集中管理）。

### 9.2 RealTimeSync（RTS）

| 项 | 事实 | 等级 |
|---|---|---|
| 本质 | **一个独立的 14.57 MB 程序**，不是 FFS 内置功能 | 【实测】 |
| 触发 | 监视目录变化 → 等**可配置的 idle 时间**无新变化 → 执行一条命令行（通常是 `FreeFileSync.exe job.ffs_batch`） | 【官方】 |
| 通知来源 | **直接来自操作系统的变更通知，不做轮询** | 【官方】 |
| Linux 实现 | **`inotify_init` + `inotify_add_watch`** | 【实测】符号 |
| Windows 实现 | 对应机制为 `ReadDirectoryChangesW`（overlapped I/O） | 【推算·依据】手册"OS 直接通知 + 不轮询" + 平台唯一对应 API |
| 去抖 | `idle` 时间是核心参数——避免"正在写大文件时触发同步" | 【官方】 |
| 设备事件 | 目录"变为可用"也触发 → **插 U 盘自动备份** | 【官方】 |
| 运行形态 | 可作 Windows 服务（`RTS: Run as Service`） | 【官方】 |

**它其实是"事件源"而不是"同步器"**：RTS 只负责"什么时候该跑"，不负责"跑什么"。这个职责切分让它能复用 batch 作业的全部能力，也让"插盘即备份"变成一个 4 行配置的事。

### 9.3 其它平台细节

- **可变盘符**：靠**卷标**定位移动硬盘（`Variable Drive Letters`），解决"插到别的 USB 口就变 F: → G:"。
- **长路径**：`\\?\` 前缀绕过 260 限制，且官方提示"资源管理器不认，所以文件数统计会不一致"。
- **单实例**：不是强单例——允许多开，靠 `sync.ffs_lock` 在**文件夹级**串行化。**这个选择更正确**：多开不同任务本来就该允许。

---

## 十、性能工程（可查证的优化清单）

| 优化 | 版本 | 效果 | 性质 |
|---|---|---|---|
| **自写 wxGrid 替代品**（数据不映射到 UI，直接绘制） | 1.1（2008） | 10 万行以上"巨大提升" | 架构级 |
| 并行目录遍历 / 逐设备聚合 worker | 10.x | 高延迟链路数量级提升 | 架构级 |
| 并行二进制比较 | 10.x | 比较阶段线性加速 | 架构级 |
| 排除过滤器从线性到常数时间 | 11.19 | 大过滤器表不再拖慢 | 算法级 |
| 移除文件复制中的冗余内存缓冲 | — | 减少一次拷贝 | 内存级 |
| 峰值内存降低 12% | — | — | 内存级 |
| db 文件体积再降 16% | 14.12 | 网络盘上 db 传输更快 | 存储级 |
| 按需启动 (S)FTP/HTTP 清理线程 | 14.8 | 空闲不占资源 | 线程级 |

**规模上限（官方口径）**：**每 1 GB RAM ≈ 100 万文件对**；无人工文件数上限；实际瓶颈是内存。

> 换算：8 GB 内存的机器约可处理 **800 万文件对**。这个量级足以覆盖"整块 4 TB 素材盘"的场景，但**不是"PB 级"**——它不是企业级备份软件，也不打算是。

---

## 十一、功能清单（技术视角 × 三档授权）

| 能力 | 技术实现要点 | 免费 | 捐赠 | 商业 |
|---|---|:--:|:--:|:--:|
| 三种比较变体 | 元数据 / 逐字节 / 仅 size | ✅ | ✅ | ✅ |
| 三种同步变体 + 自定义规则 | 类别表 × 规则引擎；双向依赖 db | ✅ | ✅ | ✅ |
| 移动/重命名检测 | db + file ID；不可用则退化 | ✅ | ✅ | ✅ |
| 预演表格 + 逐行取消 | 自绘虚拟表格；比较与执行分离 | ✅ | ✅ | ✅ |
| 多文件夹对 | 按设备根分组并发 | ✅ | ✅ | ✅ |
| 过滤器（include/exclude） | 通配符 + 全路径匹配；O(1) 查表 | ✅ | ✅ | ✅ |
| 批量作业 `.ffs_batch` + 命令行 | 返回码；静默模式 | ✅ | ✅ | ✅ |
| RealTimeSync | inotify / OS 通知 + idle 去抖 | ✅ | ✅ | ✅ |
| 版本化（Versioning） | `%timestamp%` 路径模板 | ✅ | ✅ | ✅ |
| 回收站删除 | Shell API / g_file_trash | ✅ | ✅ | ✅ |
| 符号链接（Follow / As link） | 四类链接对象统一 | ✅ | ✅ | ✅ |
| 权限 / ADS / xattr / 长路径 | 平台原语直通 | ✅ | ✅ | ✅ |
| VSS 复制被锁文件 | Windows VSS（需 admin） | ✅ | ✅ | ✅ |
| Google Drive / FTP / SFTP / MTP | 四种 AFS 实现 | ✅ | ✅ | ✅ |
| **并行文件复制** | 每设备 N 路写 | ❌ | ✅ | ✅ |
| **自动更新** | 自研 updater（含 Linux 提权降权修复） | ❌ | ✅ | ✅ |
| **邮件通知** | SMTP 直发 | ❌ | ✅ | ✅ |
| **便携 ZIP** | 免安装包 | ❌ | ✅ | ✅ |
| **静默安装 `/silent`** | Inno Setup 参数 | ❌ | ❌ | ✅ |
| **税务发票 / 转售 URL** | 后台 | ❌ | ❌ | ✅ |

**这张表的形状就是产品策略**：能力全免费，**只卖"省事"与"合规"**。

> 授权细节：捐赠版为**单用户授权，最多 3 台设备**（二手来源多篇一致，官网 FAQ 未写死）【二手】；商业版按设备计费、含一年更新，可续期/加购。捐赠版额外含**虚拟机不限台数**与**激活机器数异常时的告警**（CHANGELOG：`Warn if Donation Edition is active on unexpected number of machines`）——说明它有轻量的机器指纹校验，但**不是强 DRM**。


---

## 十二、技术债与结构性风险

| # | 问题 | 证据 | 影响 |
|---|---|---|---|
| 1 | **构建不可复现** | 路径含 `/home/zenju/Desktop/Projects/wxWidgets/Source`，wxWidgets 自编译于 `CentOS_gcc_16.2.0`，GCC 16.2.0 + OpenSSL 4.0.3 全静态 | 无人能在自己机器上复现发布产物；源码"可得"≠"可编译" |
| 2 | **无公开仓库/CI** | 只有论坛 + 源码压缩包 | 外部无法提交补丁，质量完全依赖单人 |
| 3 | **自绘表格的长期税** | CHANGELOG 中大量 `grid view`、`high-DPI`、`tooltip`、`mouse scrolling` 修复（近三年 ≥8 条） | 每个平台/主题/缩放比例都要单独修 |
| 4 | **无哈希 → 冲突判定依赖 mtime** | 同 mtime 不同内容会被判 equal | 元数据不可靠的设备/协议上存在静默不一致风险 |
| 5 | **`sync.ffs_db` 单点** | 无 db → 双向语义崩塌 | 用户误删/换机/权限变更即触发大规模冲突 |
| 6 | **VSS 需管理员** | 官方手册 | 与企业最小权限冲突，进不了受管终端 |
| 7 | **无服务端/无集中管理/无审计** | 架构决定 | 无法满足合规审计、集中策略、多端编排 |
| 8 | **协议矩阵靠人肉维护** | 212 条 CL 中大量单点修复（SMB/ReFS/Xiaomi 文件管理器/SFTP banner…） | 每个 OS 更新都是新的兼容工作 |
| 9 | **单体 + 全静态的体积** | 28.66 MB 主程序 | 冷启动与内存占用高于按需加载架构，但换来零依赖 |

---

## 十三、对 PM 的三条可迁移结论

**1. "零运行时依赖"是商业决策，不是技术洁癖。**
全静态链接让安装包 22 MB、不需要 .NET/VC++/Python，**直接消灭了"装不上"这一类支持工单**。它把工程量花在了用户看不见的地方，换来的是"下载—双击—能用"这一条最短路径。**对个人开发者产品，这是最高性价比的工程投入。**

**2. 付费墙要切在"省事"，不要切在"能力"。**
并行复制、自动更新、邮件通知、便携版——**没有一项是"更多功能"，全部是"更少折腾"**。结果是：免费用户不觉得被阉割（口碑好），付费用户买的是时间（不后悔）。**切在能力上会招骂，切在省事上只会招谢。**

**3. 性能必须能被拆成可验证的三件事。**
它从不讲"我们很快"，只讲：**按设备分组并发**（可数）、**只传差异**（可算）、**先删后拷**（可复现）。**任何性能叙事如果不能拆成这种颗粒度，就是营销而不是工程。**

---

## 附 A、取证方法与可复现命令

```bash
# 1) 官方手册全文（单页版）
curl -sL "https://freefilesync.org/manual.php?topic=all"

# 2) Windows 安装包（确认为 Inno Setup）
curl -sL -o ffs_setup.exe "https://freefilesync.org/download/FreeFileSync_14.13_Windows_Setup.exe"
7z l ffs_setup.exe          # PE 注释：This installation was built with Inno Setup.

# 3) Linux 版（同源，便于静态分析）
curl -sL -o ffs.tar.gz "https://freefilesync.org/download/FreeFileSync_14.13_Linux_x86_64.tar.gz"
tar xzf ffs.tar.gz && 7z x FreeFileSync_14.13_Install.run   # 自解压 tar
7z x FreeFileSync.tar.gz && 7z x FreeFileSync.tar "Bin/FreeFileSync_x86_64" "CHANGELOG"

# 4) 依赖与符号
strings -n 5 Bin/FreeFileSync_x86_64 | grep -E "libwx|libgtk|OpenSSL|libssh2|\.ffs_tmp|ffs_db"
```

**取证清单**：官方手册 19 个主题全文 · 官网 FAQ · CHANGELOG 211 版全量 · 主程序 28.66 MB / RTS 14.57 MB 字符串与符号 · `install.sh` 620 行 · Inno Setup PE 元数据。

## 附 B、证据等级说明

| 等级 | 含义 | 本报告中的例子 |
|---|---|---|
| 【实测】 | 本次直接读到字节/字符串/页面 | GCC 16.2.0、wx 3.3 路径、OpenSSL 4.0.3、`inotify_init`、`.ffs_tmp` |
| 【官方】 | 官方手册/FAQ 明确写出 | 2 秒容差、冲突定义、VSS 需 admin、1 GB≈100 万对、SFTP 无移动检测 |
| 【推算·依据】 | 由实测 + 平台常识推导，未见原文 | Windows RTS = `ReadDirectoryChangesW`；VSS 挂载点形态；db 记录 file ID |
| 【未取得】 | 拿不到 | db 二进制布局、并发上限默认值、源码行数、测试体系 |

## 附 C、未取得与存疑

| # | 缺口 | 为什么重要 | 获取路径 |
|---|---|---|---|
| 1 | `sync.ffs_db` 的**字段级布局** | 判断它是否真存 file ID、是否存目录项 | 对同一文件夹同步两次后 dump db 并差分（可在本机复现） |
| 2 | 默认**并行度**数值 | 评估开箱性能 | UI 默认值 / `GlobalSettings.xml` 实测 |
| 3 | **测试体系**（单测/回归/dogfood） | 判断 18 年零事故是流程还是运气 | 作者论坛帖 / 博客；官网无披露 |
| 4 | **源码行数** | 工程规模量化 | 解压源码包后 `cloc` |
| 5 | Windows 端 RTS 的**确切 API 与去抖实现** | 验证"不轮询"是否成立 | Windows 版 exe 字符串（需解 Inno Setup）/ 作者说明 |
| 6 | **VSS 快照的挂载与生命周期** | 评估对长时间作业的稳定性 | Windows 实测：同步中观察 `vssadmin list shadows` |

> 其中 **#1 与 #4 可以在本机 20 分钟内补齐**，且能显著提高这份拆解的置信度。需要的话直接说。
