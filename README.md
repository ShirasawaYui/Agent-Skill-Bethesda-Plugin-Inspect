# yui-bethesda-plugin-inspect

**结衣的Bethesda模组内容分析助手** — 读取 Bethesda 游戏插件（esp / esm / esl）记录，定位某个 mod 改了什么，并还原 load order 覆盖链确定最终生效值。

A skill for reading Bethesda game plugin records: find out what a mod changes, and resolve which override actually takes effect.

---

## 它解决什么问题

装了整合包之后，想知道「某个 mod 到底改了什么」，通常会遇到三个障碍：

1. **无从下手** —— 几百个插件，不知道改动落在哪个文件里
2. **读不懂** —— 插件是二进制格式，直接看字节没有意义
3. **读到了也不算数** —— 同一条记录常被多个插件依次覆盖（补丁、汉化、难度调整），**你先找到的那份往往不是生效的那份**

本技能把这三步固化为一条可复用流程：

```
定位  →  解析  →  归因
哪个插件改的    改成了什么    哪一份最终生效
```

其中第三步是最容易被跳过、也最容易出错的一步。技能把「**找到记录 ≠ 找到生效记录**」作为硬判据写进了主流程。

## 能力

| 需求 | 手段 |
|---|---|
| 角色参数（等级 / 属性 / 技能 / Perk / 阵营 / 脚本挂载） | 读 `NPC_` 记录 |
| 任务流程（阶段 / 目标 / 别名 / 触发） | 读 `QUST` 记录 |
| 道具效果（法术 / 附魔 / 装备 / 武器） | 读 `MGEF` / `ENCH` / `ARMO` / `WEAP` / `SPEL` |
| 场景与放置物 | 读 `CELL` / `WRLD` / `REFR` |
| 覆盖关系（谁压谁、最终生效的是谁） | 还原 load order 覆盖链 |
| 资源清单（归档里有什么） | 读 `bsa` / `ba2` |
| 脚本行为 | 记录 `VMAD` → 反编译对应 `.pex` |

字段解码使用 **xEdit 官方 schema**（随 bethkit 内置，标注 `xedit-4.1.5f`），因此解出的字段名与 SSEEdit 界面一致，可相互验证。

## 前置依赖

| 依赖 | 说明 |
|---|---|
| Python 3.11+ | 运行脚本 |
| **bethkit** | 核心引擎，`pip install bethkit`（Rust 内核 + Python 绑定，Apache-2.0） |

```bash
python -m venv <你的 venv>
<你的 venv>/Scripts/pip install bethkit
<你的 venv>/Scripts/python.exe scripts/esp_inspect.py doctor
```

`bethkit` 的出处、安装位置、检查更新与回滚方式，见 [`references/bethkit.md`](references/bethkit.md)。

## 使用

```bash
# 环境自检（bethkit 版本 / schema 来源 / 可选工具状态）
"$PY" scripts/esp_inspect.py doctor

# 1 定位：在模组目录中检索记录
"$PY" scripts/esp_inspect.py find <mods_root> <关键词>

# 1' 降级：字节级粗筛（不需要 bethkit）
"$PY" scripts/esp_inspect.py grep <目录或文件> <关键词>

# 2 解析：导出单条记录的全部字段
"$PY" scripts/esp_inspect.py dump <插件路径> <EditorID 或 0xFormID>

# 3 归因：还原 load order 覆盖链
"$PY" scripts/esp_inspect.py chain <plugins.txt> <local_id> --signature NPC_
```

非天际游戏用 `--game` 指定（`SKYRIM_SE` / `SKYRIM_LE` / `FALLOUT4` / `FALLOUT76` / `STARFIELD` 等），默认 `SKYRIM_SE`。

`chain` 的输出形如：

```
  [212] FIN-Combat MergedV2.esp        NPC_  EditorID=00DS1gundir  子记录= 44  VMAD=无
  [402] REQ Chaos Valheim Mode.esp     NPC_  EditorID=EP0BOSS-0    子记录= 50  VMAD=无
  [420] Requiem for the Indifferent.esp NPC_ EditorID=EP0BOSS-0    子记录= 86  VMAD=有  <- 最终生效
```

注意这个例子：首版 44 个子记录、无脚本；生效版 86 个子记录、挂了脚本，EditorID 也被改过名。**只看首版会得出完全错误的结论。**

## 可选工具（不在本仓库内分发）

以下工具**未随本仓库分发**，原因是二进制体积与第三方许可义务。按需自行从官方获取：

| 工具 | 用途 | 许可 | 获取 |
|---|---|---|---|
| [Champollion](https://github.com/Orvid/Champollion) | pex → psc 反编译 | LGPL-3.0 | [releases](https://github.com/Orvid/Champollion/releases) |
| [BSA Browser](https://github.com/AlexxEG/BSA_Browser) | bsa/ba2 图形界面浏览与提取 | GPL-3.0 | [releases](https://github.com/AlexxEG/BSA_Browser/releases) |

**两者的缺失都不影响主流程**：esp 记录读取只依赖 bethkit；归档读取已由 `bethkit.Archive` 覆盖。

使用第三方工具时请遵守其各自许可。特别提示：BSA Browser 的作者在其发布页声明**不允许转载至其他站点**，
这也是本仓库不打包它的原因之一。

## 安装到 WorkBuddy

1. 把本目录放到 `~/.workbuddy/skills/yui-bethesda-plugin-inspect/`
2. 按上文安装 bethkit
3. 运行 `doctor` 确认环境
4. 重启 WorkBuddy 使技能出现在列表中

## 边界

- **只读**：不修改、不编译插件。改插件请用 SSEEdit
- **记录数值 ≠ 运行时数值**：脚本可以改写属性，涉及脚本的结论只能标为待验证
- **不做资源视觉查看**：模型形态、贴图效果需要 NifSkope 等专用查看器
- **结论可溯源**：区分「记录可证」与「待验证」

## 许可

本技能本体采用 [MIT License](LICENSE)。

内部分发的第三方工具（若你自行放入 `tools/`）各自适用其原始许可，与本仓库无关。

## 变更记录

见 [CHANGELOG.md](CHANGELOG.md)。
