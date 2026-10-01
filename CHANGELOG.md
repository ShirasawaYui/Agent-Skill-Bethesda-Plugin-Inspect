# CHANGELOG — yui-bethesda-plugin-inspect

版本号同时出现在三处，改版时必须一起同步：
`SKILL.md` frontmatter、`_user_meta.json`、本文件。
（元数据 JSON 的 `version` 优先于 frontmatter，只改一处等于没改。）

本技能为**脱钩的本地独立版**，不跟随任何上游或市场更新。上游仅指 bethkit 与随附的两款第三方工具，
其版本与更新方式见 `references/bethkit.md`。

---

## 1.4.0 — 2026-10-01

**新增子命令 `tree`** —— 把「原版星座树替换关系」这套流程脚本化

- ✚ `esp_inspect.py tree <MO2 配置档目录>`：一行一棵输出 `技能 → 覆盖链 → 末端生效插件`，
  并给出节点数（证明它确实是棵树）。等价于第 8 节「最小实现」的路径 A。
- ✚ 路径**全部靠参数传入或向上查找派生**，不写死任何绝对路径：
  `--mods-root` 省略时从配置档目录上溯找 `MO2/mods`；
  `--data-dir` 省略时从 mods 目录上溯找含 `Skyrim.esm` 的 `Data`
- ✚ **`plugins.txt` 的 `*` 改为只作提示，不再作为过滤依据**（默认按 `loadorder.txt` 全序扫描，
  要严格过滤加 `--only-enabled`）。原因：实测 `Vokrii - Minimalistic Perks of Skyrim.esp`
  那一行没有 `*`，但游戏内显然在用它的技能树 —— 两个已勾选插件
  （`Vokrii - Shadow Spell Package Patch.esp`、`Requiem - EX combat.esp`）的 masters 里都列着它。
  早期实现按 `*` 过滤，曾把 Vokrii 整条从覆盖链里静默删掉，与已知漏洞第 3 条同类。
- ✚ 顺带修掉两类此前记录过的漏洞：
  - **重名插件**：索引改为按 `modlist.txt` 行序取用，并在输出里列出「重名且副本大小不一致」的
    全部候选与采用项（此前 `setdefault` 取到的是先遇到的那份，未必是 MO2 实际加载的）
  - **静默丢弃**：身份不在基线里的 AVIF 现在进"未匹配"桶并计数输出，不再无声消失
- ✚ 修正 `chain` 的顺序来源：改用 `loadorder.txt`（全序）而非 `plugins.txt` 的 `*` 行 ——
  后者不含官方主文件，会漏掉 `Update.esm` 这类改动
- ✚ `INSTALL_HINT` 去掉写死的本机 venv 绝对路径，改为占位符（真实路径见 `references/bethkit.md`）

## 1.3.11 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 按用户要求标注适用范围

- ✚ 第 8 节开头加「适用范围」块，明确**仅限 Skyrim 原版技能树的替换关系查找**
- ✚ 列明四种不适用情形：
  其它游戏（`AVIF` 承载技能树是 Skyrim 的结构）、
  自定义技能树框架自画的树（不写 `AVIF`，如 `EldenPerkTree.esp`）、
  perk 等级 / 前置 / 实际数值（走第 6、7 节）、技能界面的版式与图标
- ✚ `SKILL.md` 的主流程与参考表两处指针对应补注"仅 Skyrim 原版技能树"

## 1.3.10 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 用户追问「孤儿 perk 能不能进统计范围」

- ✚ 第 8 节「判据」补明：成员判定**只看 `PNAM`，与连线无关** ——
  孤立节点（无任何连线、无任何前置）照样算成员；旧那套"孤立性启发式"恰会误杀它
- ✚ 记下"等级 / 前置"列为空对这类 perk 是**正常结果，不是解析失败**，表头须写明
- ✚ 首次校准**连线字段语义**（此前只知 `PNAM`）：
  `INAM` = 节点自身序号；`CNAM` = 该节点连到哪些节点（存目标节点的 `INAM` 值，可多个）；
  树根锚点的 `CNAM` 指向第一个真节点。附开锁树的验证样本

## 1.3.9 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 用户问「只聚焦原版星座树的替换关系，这套流程能简化到什么程度」

- ✚ 第 8 节「最小实现」拆成两条路径：
  - **路径 A（只求"哪棵树归谁"）**：取基线记录头 → 逐插件只登记 AVIF 身份 → 取末端 →
    只对末端解析"是否含 `AVSK` ＋ 节点组"以筛出树（顺带排除被改过的非技能 AV）
  - **路径 B**：要连 perk 成员归属一起做时，才继续切分节点组、解析 `PNAM`
- ✚ 写明全程**只有两处需要读内容**（取基线、判有无节点组），其余只比对记录头与文本清单
- ✚ 补两处易错点：基线**不要按名字挑技能**（幻术树叫 `AVMysticism`）；
  扫描前**必须把 5 个官方主文件补进启用集合**

## 1.3.8 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 用户追问「这套判断逻辑有没有漏洞」，逐条验证后补记

- ✚ 第 8 节新增「已知漏洞（读的时候要防）」四条，均为实测所得：
  1. **`AVIF` 的 EditorID 不能按「AV＋技能名」推** —— 幻术树实际挂在 `AVMysticism` 上
     （上古卷轴 4 的旧名），而 `AVIllusionMod` / `AVIllusionPowerMod` / `AVIllusionSkillAdvance`
     只是修饰用 actor value。已用节点表验证：`AVMysticism` 的节点正是 `IllusionNovice00` /
     `IllusionApprentice25` / `IllusionAdept50` / `IllusionExpert75` / `IllusionMaster100` 等
  2. **同名插件文件在 MO2/mods 下可能有多份**（本项目实测 698 个插件中 26 个重名）——
     按文件名去重会取到不是 MO2 实际加载的那一份，须按 `modlist.txt` 左侧优先级取最高者
  3. **基线之外的身份必须显式归类**，否则静默丢弃：读不到也不报错，结论却成了"没有该改动"
  4. **旧式 `plugins.txt`（无 `*`）**会让"只看 `*`"的解析把全部插件误判为未启用

## 1.3.7 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 补第 8 节缺的"覆盖链末端怎么定"

用户追问「你怎么判断最终的 AVIF 是谁」，据此把方法写实并改正一个实现弱点：

- ✚ 第 8 节新增「覆盖链末端怎么定」四步：
  顺序取自 `loadorder.txt`（全序）；启用状态取自 `plugins.txt` 的 `*`
- ✚ ⚠️ 记下 **官方主文件（Skyrim.esm / Update.esm / 3 个 DLC）不写进 `plugins.txt`**，
  必须自行补入启用集合 —— 否则漏掉它们对记录的改动
  （实测 `Update.esm` 覆盖 `AVSmithing`、USSEP 覆盖 `AVDestruction`）
- ✚ **对齐方式改为必须按 FormID，而非 EditorID**：覆盖 = 同一 FormID 在后排再次出现。
  EditorID 匹配的两种失效情形 —— 新建记录却复用旧名（误判）、覆盖时改名（整条漏掉）
- ✚ 明确前提：这是读物理文件 + 两份 txt 复现 MO2 判定，等价于 usvfs 结果；
  顺序若被外部工具改动而尚未写盘会与游戏不符，**最终以游戏内为准**

## 1.3.6 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 追查「perk 树的成员关系到底存在文件里的哪里」

结论：**不在 PERK 记录里，也没有独立的"树"记录，而是挂在 `AVIF`（技能）记录的节点表中。**

- ✚ `references/records.md` 新增第 8 节「PERK 树的成员关系怎么读」：
  `AVSK` 之后的 `PNAM FNAM XNAM YNAM HNAM VNAM SNAM CNAM INAM` 节点组结构；
  `PNAM`＝perk FormID、`INAM`＝节点序号、`CNAM`＝连线；`PNAM` 为空者为树根锚点
- ✚ 给出明确判据：**perk 属于哪棵树 ⇔ 其 FormID 出现在该技能 AVIF 的 PNAM 列表**
- ✚ 三条陷阱：技能树本身也会被 load order 覆盖、**且不同技能可能由不同插件提供**
  （须按技能逐棵取最后定义者）；`PNAM` 是原版 perk id，解析名字必须走 load order 归属；
  先列出含 AVIF 的少量插件再逐技能取胜者
- ✔ 把原先那套「用 EditorID 前缀 / 孤立性判断某 perk 是否在树上」的启发式**降级为兜底**，
  并写明其已知误伤（异前缀的正当 perk、被书 / 道具前置隔断的链条）

实测样本：同一整合包内铁匠树由 `Fozars_Dragonborn_-_Requiem_Patch.esp` 最终生效，
一并解释了先前「表里缺魔冰 / 晨风 / 诺德锻造」的报错。

## 1.3.5 — 2026-10-01

**仅补充参考文档（脚本无变更）** —— 依据一次实战翻车修正

用户在游戏内截图核对 perk 树，发现表里给出的「不辞辛劳」「地牢大师」**在游戏中根本不存在**。追查后补两条陷阱：

- ✚ `references/records.md` 陷阱 4：**EditorID 带 `NULL` 或被 `===` 包裹 = 已被禁用**。
  Requiem 系整合包会把原版 perk 改名加 `NULL` 后缀屏蔽 —— 记录还在、FULL 名甚至已汉化，
  但游戏内不显示。不剔除会给出「能点却点不了」的错误建议
- ✚ 陷阱 5：**等级门槛 = max(EditorID 三位编号, CTDA 值)**。两者互相补位 ——
  Mastery 组 EditorID 一律写 `000`（靠 CTDA），而 `VKR_Res_070_Necromage` 这类
   EditorID 写明编号、CTDA 反而没有等级条件
- ✚ 新增「判断某 perk 是否在玩家技能树上」的经验规则（4 条剔除条件，标注为启发式）

## 1.3.4 — 2026-10-01

**仅修正主文档路标（脚本无变更）**

- `SKILL.md` 主流程「解析」与 §参考表对 `references/records.md` 的描述已过时 ——
  该文件早已扩至「前置条件（CTDA）」「entry point 实际数值」两节，主文档却仍写作"记录签名对照"，
  且主流程无任何指向。**规则在 references 里、主流程不留路标 = 规则等于不存在**，已补齐两处指向。

## 1.3.3 — 2026-10-01

**仅补充参考文档（脚本无变更）**

- ✚ `references/records.md` 新增 **7. PERK 的实际数值效果怎么读**：
  - entry point 块的结构（Header → Effect Data → CTDA → Type → Data → End Marker）
    与 `Header.Type` 的三类（Entry Point / Ability / Quest+Stage）
  - Function 到可读算式的映射表（`Multiply Value` → `×N` 等）
  - **`Float/AV,Float` 的两个值 = (技能索引, 每点系数)** —— 附实测规律与位模式还原写法
  - 三条注意：描述不等同数值、分档 perk 不叠加、Ability 多为无名隐藏法术

## 1.3.2 — 2026-10-01

**仅补充参考文档（脚本无变更）**

- ✚ `references/records.md` 新增 **6. PERK 的前置条件怎么读**：
  - 区分「学习前置」与「生效条件」两类 CTDA —— 只有**第一个 `DATA` 之前**的那批才是前置
  - CTDA 的 32 字节布局；`GetActorValue`（函数 277，参数为 ActorValue 索引）与
    `HasPerk`（函数 448，参数为 perk FormID）的读法
  - 免手工解析：用内置 schema 的 `SemanticContext.view()` 直接取命名后的条件字段
  - 三个实测陷阱：**EditorID 里的数字不是权威等级**（实例：EditorID `020` 实为 `25`）、
    `_NPC` 后缀记录不属于玩家技能树、FULL/DESC 皆空的空壳记录应归附录

## 1.3.1 — 2026-10-01

**仅补充参考文档（脚本无变更）**

- ✚ `references/api.md` 新增 **4.1 文件内 FormID 映射**：插件内记录的 `form_id` 高字节是**该插件自身
  master 列表的下标**，与全局 load order 无关；**高字节 ≥ master 数表示「引用本插件自身」**，不是数据损坏。
  附 `master_at()` 用法与反例
- ✚ 同文件陷阱清单补两条：把 load order 行号当高字节索引（会解出完全无关的插件）、
  **子记录引用签名 ≠ 目标记录签名**（NPC_ 内 `PRKR`→`PERK`、`SPLO`→`SPEL`，不映射则查询全部落空）
- 动因：解析某 NPC_ 的 Perk / Spell 引用时实际踩到这两处，属于高频误用
- `references/api.md` 文档版本 → v1.1.0

---

## 1.3.0 — 2026-10-01

**新增存档读取能力（脚本逻辑有变更）**

- ✚ **新增 `save` 子命令**，读取 Skyrim 存档（`.ess`）的运行时状态，四项导出：
  - `info` —— 角色摘要（名 / 等级 / 种族 / 性别 / 位置 / 游戏日期 / 经验）＋结构统计
  - `globals` —— 全局变量表，可按关键词筛选；mod 的运行时配置多存于此
  - `inventory` —— 玩家背包
  - `forms` —— ChangeForm 按记录类型的数量统计
- ✚ **随附存档解析组件** `tools/save-reader/`（1.6 MB）。引擎为 **ReSaver / FallrimTools**（Apache-2.0，
  随附 `LICENSE.txt`），另含 3 个运行依赖；入口 `SaveReader` 是自写的薄封装（Java 8 目标），
   **只调用引擎公开 API，未修改引擎源码**
- 动因：插件记录是**静态声明**，存档才是**运行时实际值**。判断一处改动是否真正生效需要两者对照，
  本版补齐这一环
- ✓ `doctor` 增加存档组件与 Java 运行时的检查项（需 Java 8 或更高）
- ✓ 新增 `references/save.md`：文件格式、命令说明、数据规模参考、已知限制、组件构成与重建方式
- ✓ `SKILL.md` 的「何时使用」补入存档场景，并新增「存档（运行时数据）」一节
- ✓ **references 文档统一补版本头**（`> 版本：v1.0.0 · 最后更新：日期`），对齐规范 A8
- ⚠️ 与 ReSaver 自带 CLI 的关系：其 `-i`（输出背包）选项**实现有缺陷** —— 内部把 `null` 传给
  只接受非空参数的方法，运行时必抛 `NullPointerException`。本组件的 `inventory` 是其替代实现。
  详见 `references/save.md` 第 7 节
- 说明：`.skse` co-save 目前仅识别其存在，不解析内部数据

## 1.2.0 — 2026-10-01

**转为可公开发布形态（脚本逻辑有变更）**

- ⚡ **移除随附的第三方二进制**，改为「可选工具 + 官方获取指引」。三条原因叠加：
  1. **许可义务** —— Champollion 为 LGPL-3.0、BSA Browser 为 GPL-3.0，再分发均须附许可全文
     并提供源码获取方式；且 BSA Browser 的作者在发布页声明**不允许转载至其他站点**
  2. **体积** —— WorkBuddy 技能市场要求 ZIP ≤ 3MB，而含工具的包为 7.8MB
  3. **结构** —— 市场认可的结构为 `SKILL.md` + `references/` + `scripts/` + `templates/`，不含 `tools/`
- ✚ 补公开分发所需的文件：`README.md`（仓库首页）、`LICENSE`（MIT）、`.gitignore`
- ✚ `SKILL.md` frontmatter 补市场必填字段：`description_zh`、`description_en`、`author`，另加 `display_name`
- ✓ 归档分支改以 `bethkit.Archive` 为主 —— 它是内置能力，无需外部工具
- ✓ `doctor` 改报「可选工具」状态：未安装时给出官方 releases 链接与许可提示，不再视作缺失
- ✓ `references/workflow.md`、`references/troubleshooting.md` 同步「工具缺失不阻断主流程」的说明
- ✓ 公开版不含 `_user_meta.json`（内含本机绝对路径，且属本机元数据而非技能内容）
- 📌 本地自用版可继续在 `tools/` 下放置工具，`doctor` 会识别为「已内置」；该目录已列入 `.gitignore`

## 1.1.0 — 2026-10-01

**补齐降级路径 + 修正传参缺陷（脚本逻辑有变更）**

- ✚ **新增 `grep` 子命令** —— 纯字节串搜索，不依赖 bethkit。
  动因：文档此前已两处承诺该降级手段（`references/troubleshooting.md` §6 降级路径、
  `references/workflow.md` 第一步的判据表），但技能内**并无实现**——属「规则与实践不一致」。
  实现要点：自动同时尝试 UTF-8 与 GBK 两种编码以覆盖中文插件；`target` 可传目录或单个文件，
  传文件时可用于搜 pex、或搜 bsa 解包后的产物。
- ⚡ **修复 `--game` 传参位置限制** —— 此前挂在顶层参数上，受 argparse 位置规则约束，
  只能写成 `esp_inspect.py --game X find ...`；写在子命令之后会报 `unrecognized arguments`。
  改为经 `parents` 挂到各子命令，两种写法均可。
- ✓ `doctor` 的 schema 检查由硬编码 `SKYRIM_SE` 改为跟随 `--game`。
- ✓ **文档一致性修复**：
  - `SKILL.md` 参考表补登 `references/triggering.md`（文件已存在但未登记）。
  - 主流程命令的解释器写法与「环境准备」不一致（前者写 `python`，后者写 `"<venv>/python.exe"`）
    → 统一为 `$PY`，并在环境准备中说明其含义。
  - `metadata.bundled_tools` 中 Champollion 的版本号系推测（GUI 前端为 v2.1.0.1，内核版本无确证）
    → 去掉版本号，只保留工具名。**不确定的事实不写入元数据。**
- ✓ `references/troubleshooting.md` 补充两条排查项：`find` 只检索记录字段（脚本与归档内文本须用 `grep`）；
  `grep` 搜不到时的编码与归档排查。
- ⚡ **显示名变更**：「结衣的Bethesda插件读取专版」→ **「结衣的Bethesda模组内容分析助手」**。
  依据用户命名约定：**「专版」指内含本机密钥等敏感文件的专用版**，本技能不含敏感文件，故用「助手」。
  （机器名 `yui-bethesda-plugin-inspect` 与目录名均未变。）
- ✚ 补充技能图标 `_icon.png`（1024×1024 / 1848 KB）：金属质感 B 字徽记 + 北欧符文环 + 龙首剪影 +
  古卷肌理；并登记 `_user_meta.json` 的 `iconLocalPath`。
- ✓ 验收：五个子命令（`doctor` / `find` / `grep` / `dump` / `chain`）全部以真实整合包数据回归通过；
  `validate_skill.py` 0 blocker / 0 warning。
- 工作区同步清理：删除被技能取代的四个临时脚本
  （`bethkit_dump_npc.py` / `bethkit_find_npc.py` / `bethkit_probe.py` / `scan_esp.py`，
  分别对应 `dump` / `find` / `dump+doctor` / `grep`）。

## 1.0.0 — 2026-10-01

**建包：把「定位 → 解析 → 归因」固化为可复用流程**

- ✚ 创建用户级技能，封装用 bethkit 读取 Bethesda 插件（esp/esm/esl）记录的完整链路：
  - **定位**（`find`）—— 在模组目录中按名称或 EditorID 检索记录，输出记录级命中
  - **解析**（`dump`）—— 经 xEdit 官方 schema 类型化解码为命名字段，附子记录序列与 VMAD 有无
  - **归因**（`chain`）—— 还原 load order 覆盖链并标出最终生效版本
- ✚ 建包的核心判断：**「找到记录」≠「找到生效记录」**。同一条记录常被多个插件依次覆盖
  （补丁、汉化、难度调整），不还原覆盖链就会取到已被覆盖的过时定义。此判据写入了 `SKILL.md` 主流程。
- ✚ 入口脚本 `scripts/esp_inspect.py`，四个子命令：`doctor` / `find` / `dump` / `chain`。
- ✚ 随附便携工具，使技能**不依赖本机其他盘位**（原工具位于 G 盘，属可被清理的临时盘位）：
  - `tools/champollion/` —— Champollion pex 反编译器（CLI + GUI 前端，含运行依赖）
  - `tools/bsa-browser/` —— BSA Browser CLI（`bsab.exe`，bsa/ba2 列表与提取）
- ✚ `references/` 六篇：
  - `bethkit.md` —— **bethkit 引述文档**（出处、安装位置、未安装时如何安装、检查更新、升级回滚、
    何时应当放弃 bethkit 及替代方案）。应要求**单独成篇**，文首声明「不属于本技能的工作流」。
  - `api.md` —— API 速查与陷阱清单
  - `records.md` —— 记录签名与子记录对照
  - `workflow.md` —— 查询流程细则与交付形态
  - `troubleshooting.md` —— 异常处理与降级路径
  - `triggering.md` —— 触发语料与路由边界（人工回归用）
- ✚ `_user_meta.json`（本地技能元数据，`source: local`）。
- 设计边界：
  - **只读**，不做修改或编译插件（写操作交 SSEEdit）
  - SSEEdit **不纳入本技能**（GUI 程序，属用户手动操作；且读取数据不需要它）
  - 资源内容的视觉查看（模型形态、贴图效果）不由本技能承担，仅负责识别与提取
  - bethkit 的 schema 源自 xEdit 官方导出（manifest 标注 `xedit-4.1.5f`），故字段名与 SSEEdit 界面一致
- ✓ 验收：`validate_skill.py` 0 blocker / 0 warning。
