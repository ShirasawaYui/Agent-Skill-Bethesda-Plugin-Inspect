# CHANGELOG — yui-bethesda-plugin-inspect

版本号同时出现在三处，改版时必须一起同步：
`SKILL.md` frontmatter、`_user_meta.json`、本文件。
（元数据 JSON 的 `version` 优先于 frontmatter，只改一处等于没改。）

本技能为**脱钩的本地独立版**，不跟随任何上游或市场更新。上游仅指 bethkit 与随附的两款第三方工具，
其版本与更新方式见 `references/bethkit.md`。

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
