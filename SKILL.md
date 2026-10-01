---
name: yui-bethesda-plugin-inspect
display_name: 结衣的Bethesda模组内容分析助手
description: 直接读取 Bethesda 游戏插件（esp/esm/esl）记录，定位某个 mod 改了什么——角色参数、任务流程、道具效果、脚本挂载，并还原 load order 覆盖链确认最终生效值。当用户问「这个 mod 改了什么」「某条记录的最终数值是多少」「这个脚本里写了什么」时使用。不用于修改或编译插件（写操作请用 SSEEdit），不做模型贴图等资源内容的视觉查看。
description_zh: 读取 Bethesda 游戏插件（esp/esm/esl）记录，定位某个 mod 改了什么内容——角色参数、任务流程、道具效果、脚本挂载，并还原 load order 覆盖链确认最终生效值。附带 pex 脚本反编译与 bsa/ba2 归档读取路径。
description_en: Read Bethesda game plugin (esp/esm/esl) records to find out what a mod changes — actor stats, quest flow, item effects, script attachments — and resolve the load-order override chain to determine the finally effective value. Also covers pex decompilation and bsa/ba2 archive reading.
version: 1.3.3
author: Yui
license: MIT
agent_created: true
metadata:
  engine: bethkit
  engine_version: "2.2.0"
  schema_source: xEdit 4.1.5f
---

# Bethesda 插件内容查询

用 bethkit 直接读取 esp/esm/esl 记录，定位 mod 改动内容（角色参数、任务流程、道具效果、脚本挂载），并还原 load order 覆盖链确定最终生效值。只读、不联网、不修改任何插件。

## 何时使用

- 查某个 mod 具体改了什么
- 查某条记录的最终生效值（多个插件都改过它）
- 读 pex 脚本内容
- 查看 bsa/ba2 归档里的资源清单
- 读存档里的运行时状态（角色、全局变量、背包、各类记录的变更统计）

## 何时不使用

- **修改或编译插件** → 用 SSEEdit；本技能只读
- **反编译后要编译回 pex** → 需要 Papyrus 编译器（随 Creation Kit 提供）
- **资源内容的视觉查看**（模型形态、贴图效果） → 用 NifSkope 等专用查看器
- **只要冲突的可视化总览** → 用 SSEEdit 的冲突视图

## 环境准备

命令中的 `$PY` 指**装有 bethkit 的解释器**（路径与安装方式见 `references/bethkit.md`），`scripts/esp_inspect.py` 相对于本技能目录。

```bash
"$PY" scripts/esp_inspect.py doctor
```

`doctor` 报告解释器、bethkit 版本、schema 来源与可选工具的安装情况；bethkit 缺失时按输出指引安装。

非天际游戏用 `--game` 指定（如 `--game FALLOUT4`），默认 `SKYRIM_SE`。

## 主流程

三步，缺一不可。

### 1 定位 —— 哪个插件动过它

```bash
"$PY" scripts/esp_inspect.py find <mods_root> <关键词>
```

输出记录级命中：插件、签名、EditorID、FormID、显示名。
关键词命中后必须核对签名与上下文——字符串出现不等于记录存在。

连关键词都无从下手时，可用字节级粗筛（不需 bethkit）：

```bash
"$PY" scripts/esp_inspect.py grep <目录或文件> <关键词>
```

`grep` 命中只用于缩小范围，结论必须回到 `find` / `dump` 在记录层复核。

### 2 解析 —— 它被改成了什么

```bash
"$PY" scripts/esp_inspect.py dump <插件路径> <EditorID 或 0xFormID>
```

按 xEdit 官方 schema 解码为命名字段，同时打印子记录序列与 VMAD 有无。
字段与记录签名的对照见 `references/records.md`。

### 3 归因 —— 哪一份最终生效

```bash
"$PY" scripts/esp_inspect.py chain <plugins.txt> <local_id> --signature NPC_
```

**「找到记录」不等于「找到生效记录」。** 同一条记录常被多个插件依次覆盖
（补丁、汉化、难度调整），先找到的那份往往不是生效的那份。

输出完整的覆盖链并标出最终生效版本。必须核对三件事：

1. 最终生效的是哪一份（load order 最靠后）
2. EditorID 是否被改过（被改名时用旧名检索会一无所获）
3. 生效版与首版的字段差异（可能多出脚本挂载、法术、Perk 等关键子记录）

**给出任何结论前都要先完成归因。**

## 分支

### 脚本（记录含 VMAD 时）

记录含 VMAD 说明挂了脚本，行为逻辑需反编译后阅读：

```bash
cd <输出目录> && <champollion 路径> <目标.pex>
```

Champollion 的输出落在**当前工作目录**，不是 pex 所在目录 —— 用 `cd` 控制落点。

`VMAD` 只说明挂了脚本；脚本内部对属性的改写不体现在记录字段里，
因此**记录中的数值不等于运行时实际数值**——涉及脚本的结论只能标为待验证。

### 归档（资源打包在 bsa/ba2 时）

优先用 bethkit 内置的归档读取（无需额外工具）：

```python
import bethkit
with bethkit.Archive.open(path_bsa) as ar:
    for e in ar.entries():
        print(e.path)
    ar.extract_to_file("meshes/foo.nif", out_path)
```

如需命令行工具批量处理，见下方「可选工具」。

## 存档（运行时数据）

插件记录是**静态定义**（这个 mod 声明要做什么），存档里才是**运行时实际值**（实际发生了什么）。
两者对照，才能判断一处改动是否真的生效。

```bash
"$PY" scripts/esp_inspect.py save info      <存档.ess>            # 摘要：角色 / 等级 / 种族 / 位置 / 游戏日期
"$PY" scripts/esp_inspect.py save globals   <存档.ess> [过滤词]    # 全局变量表，可按关键词筛选
"$PY" scripts/esp_inspect.py save inventory <存档.ess>            # 玩家背包
"$PY" scripts/esp_inspect.py save forms     <存档.ess>            # 各类记录的变更数量统计
```

解析由随附的 `tools/save-reader/` 完成（引擎为 ReSaver / FallrimTools，Apache-2.0），
需要 **Java 8 或更高**；`doctor` 会报告组件与 Java 的可用状态。
格式细节、数据规模与已知限制见 `references/save.md`。

## 可选工具

以下工具**不在本技能内分发**（二进制体积与第三方许可义务考量），按需自行从官方获取：

| 工具 | 用途 | 许可 | 获取 |
|---|---|---|---|
| Champollion | pex → psc 反编译（CLI） | LGPL-3.0 | https://github.com/Orvid/Champollion/releases |
| BSA Browser | bsa/ba2 图形界面浏览与提取 | GPL-3.0 | https://github.com/AlexxEG/BSA_Browser/releases |

若技能目录下存在 `tools/`（随附版可能内置），直接使用其中的可执行文件，`doctor` 会报告其状态。
**两者缺失都不影响主流程** —— esp 记录读取只依赖 bethkit，归档读取已由 bethkit.Archive 覆盖。

使用第三方工具时请遵守其各自许可：Champollion 为 LGPL-3.0（再分发需附许可并提供源码获取方式）；
BSA Browser 为 GPL-3.0，且其作者在发布页声明**不允许转载至其他站点**。

## 边界

- **记录数值 ≠ 运行时数值**：脚本可改写属性
- **写操作不做**：改插件用 SSEEdit
- **资源内容需专用查看器**：本技能只负责识别与提取
- **结论要可溯源**：区分「记录可证」与「待验证」

## 参考

| 文件 | 内容 |
|---|---|
| `references/bethkit.md` | **bethkit 引述文档**：出处、安装、检查更新、升级回滚、替代方案 |
| `references/api.md` | bethkit API 速查与陷阱清单 |
| `references/records.md` | 记录签名与子记录对照 |
| `references/workflow.md` | 查询流程细则与交付形态 |
| `references/troubleshooting.md` | 异常处理与降级路径 |
| `references/save.md` | **存档读取**：格式、命令、规模参考、已知限制、组件构成与重建 |
| `references/triggering.md` | 触发语料与路由边界（人工回归用） |
