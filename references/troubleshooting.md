# 异常处理

> 版本：v1.1.2 · 最后更新：2026-10-02

## 1. bethkit 相关

| 现象 | 原因 | 处理 |
|---|---|---|
| `ModuleNotFoundError: No module named 'bethkit'` | 用错解释器 | 必须用安装 bethkit 的那个 venv 解释器（见 `references/bethkit.md`） |
| `BethkitLibraryNotFoundError` | 原生库缺失或损坏 | 重装 `pip install --force-reinstall bethkit` |
| `AttributeError: 'str' object has no attribute 'name'` | `Plugin.open` 收到了 `str` | 改为 `pathlib.Path(...)` |
| `TypeError: 'method' object cannot be interpreted as an integer` | 忘了 `subrecord_count()` 的括号 | `subrecord_count` 是方法，`group_count` / `child_count` 是属性 |
| `BethkitClosedError: Plugin is closed` | 句柄已被 `PluginCache.add()` 接管，或已出 `with` 块 | 遍历必须在 `add` 之前完成；需要复用就另开句柄 |
| `RecordDecodeError` / `SchemaMismatchError` | 记录结构与该版本 schema 不符 | 多为异常插件。改为按子记录签名逐条读取，跳过解码；必要时报出该记录供人工核查 |
| 解析结果字段名与预期不符 | schema 版本变化 | 对照 `references/bethkit.md` 的检查更新流程 |

## 2. 文本编码

- **看到 `æœºç\x81µä¹‹é¼\xa0æˆ’æŒ‡` 这类输出不是数据损坏，也不是 GBK** —— 那是 **UTF-8 字节被按 Latin-1 打印**。
  判定：字符集中落在 U+0080–U+00FF 且成对连排（`æ` `ç` `å` `é` …）。
  `dump` 输出的 `Name` / `Description` 通用解码配方：

  ```python
  s.encode('latin1').decode('utf-8')
  ```

- ⚠️ **别去调终端编码**：`PYTHONIOENCODING=utf-8`、换代码页、重定向到文件，**全都无效**。
  乱码在**取值那一刻就已经产生**（字段值本身就是 Latin-1 化的 `str`），不是打印环节的锅；
  脚本自己已把 stdout 设成 UTF-8。只能在拿到值之后用上面那行配方还原。
- `dump` 打印的**长字段（如 `Description`）可能只显示前半截**，不要据此判断原文长度；
  要全文就走第 3 节「读偏移附近字节窗口」那一行的办法。
- 插件内中文**既可能是 GBK 也可能是 UTF-8**：按 UTF-8 解码乱码时改用 GBK 重试；
  但**能用上面配方解出来就说明源是 UTF-8**，不要再去试 GBK。
- 输出到终端乱码不影响数据本身，落盘时统一按 UTF-8 写入即可。

### 译名 / 文案类结论的定案纪律

**别只靠截图或描述文本给名字定案。** 降采样截图会把形近字认错 ——
实测同一名字被读错两次、错法还不一样（`幔` U+5E54 / `漫` U+6F2B / `峰` U+5C71 互串）。

定案顺序：

1. `dump` 取 `Name`（或 `FULL`）字段 → 按上面配方解码，拿到码点
2. 用候选写法各做一次 `grep`，**比对命中文件数**，命中多的那个是正字
3. 三步一致才算定案；只有截图一致不算

## 3. 关键词检索

| 现象 | 原因 | 处理 |
|---|---|---|
| 命中一大堆无关插件 | 关键词是常见子串 | 提高关键词特异性；改用 EditorID 精确匹配 |
| 明明存在的记录搜不到 | 记录被改名（覆盖链中重命名） | 用最终生效版本的 EditorID 检索，或先做覆盖链还原 |
| 某个插件读取出错被跳过 | 文件损坏、被占用或非标准格式 | 单独重试该文件；仍失败则在报告中标注该插件未被覆盖，不要当作"它没有该记录" |
| 每次扫描都**固定**跳过同一个插件，报 `BethkitNativeError: ... invalid UTF-8 in EDID subrecord` | 该插件的 EDID 字节不是合法 UTF-8（本机定点：`EldenSkyrim.esp`） | 属**已知无损跳过**，不必反复排查；只要记住该插件未参与本次检索即可 |
| 关键词只在脚本或资源里，插件记录里搜不到 | `find` 只检索记录字段，不检索文件字节 | 用 `esp_inspect.py grep` 做字节级搜索，或直接对 pex / bsa 内资源单独处理 |
| `grep` 搜不到明明存在的文本 | 文本位于 pex、bsa 内，或使用了非 UTF-8/GBK 编码 | `grep` 会自动同时尝试 UTF-8 与 GBK；打包在归档内的内容需先提取再搜 |
| `grep` 命中后想看**整段**文本，但不知道它是哪条记录 | `grep` 只报文件与偏移 | **直接读该偏移附近的字节窗口**，不需要 EditorID：<br>`open(p,'rb').read()[off-400:off+2000].decode('utf-8','replace')`<br>攻略/指南类长文本常整段连续存放，一次就能捞出全文（含它自报的记录边界，可反推 EDID） |
| 同一关键词有多种写法，要知道哪个是正字 | 中文形近字易串、作者笔误 | 两种写法各 `grep` 一次，**比对命中文件数**；命中数悬殊时少数那个多半是笔误 |

**检索结论必须落到记录层**。字符串出现 ≠ 记录存在，两者不可混淆。

## 4. 覆盖链

| 现象 | 原因 | 处理 |
|---|---|---|
| `resolve` 返回 `None` | 传了带加载槽位的完整 FormID | 只用低 24 位本地 `object_id` |
| `find_by_editor_id` 返回 `None`，但记录确实存在 | 索引的是最终生效版本的 EditorID | 用生效版本的 EditorID，或改用 `chain` 还原覆盖链 |
| 载入 load order 时大量失败 | `plugins.txt` 里含未启用项或插件不在扫描目录 | 只处理 `*` 开头的行，并把未找到的插件列入报告 |
| 覆盖链顺序与实际不符 | 直接用了 `plugins.txt` 行号 | 实际加载槽位受 ESL 影响，行号不等于槽位；以 `global_form_id` 为准 |
| `chain` 抛 `TypeError: unsupported format string passed to NoneType.__format__` | 覆盖链里存在**无 EDID 的记录**（用低位 local_id 检索时几乎必撞，实测同一 id 命中 45 份定义） | v1.4.6 已修（`(c['eid'] or '?')`）。旧副本自行打同一补丁；只想避坑就改用高特异性 local_id |

## 5. 外部工具

| 工具 | 现象 | 处理 |
|---|---|---|
| `Champollion.exe` | 无输出 | 确认工作目录可写；输出固定在**当前工作目录**，不是 pex 所在目录 |
| `Champollion.exe` | 报缺少运行库 | 系统需有 VC++ 运行库；正常 Windows 环境已具备 |
| `bsab.exe` | 无法打开归档 | 加 `-i` 忽略错误继续；确认同目录下 `Sharp.BSA.BA2.dll` 等依赖文件齐全 |
| 未安装第三方工具 | 本包不分发二进制（体积与第三方许可义务考量） | 从官方 releases 获取，链接见 `SKILL.md` 的「可选工具」。esp 记录读取只依赖 bethkit，归档读取由 bethkit.Archive 覆盖，**两者缺失都不阻断主流程** |

## 6. 降级路径

按可靠性从高到低：

1. **bethkit 记录级解析**（首选）
2. **bethkit 仅遍历子记录**（schema 解码失败时，退一步只读原始签名与字节）
3. **其他解析库**（如 `esplib`，见 `references/bethkit.md` 第 6 节）
4. **纯字节串搜索**（`esp_inspect.py grep`，不需 bethkit，仅用于缩小范围，结论不可直接采信）
5. **移交人工**（用 SSEEdit 打开亲自确认）

降级要显式声明。用低可靠性手段得到的结论，必须标注为待核实。

## 7. 机制查不到时的判断纪律

想查「某个游戏机制**是怎么实现的**」（采集数量、伤害公式、等级缩放……），三层依次找，
**找不到不等于不存在**——结论只能停在找到的那一层：

| 层 | 能看到什么 | 怎么找 |
|---|---|---|
| 记录层 | 数据：记录字段、GMST、perk 的 entry point、MGEF 参数 | `find` / `dump` / `chain` |
| 脚本层 | 行为：Papyrus 逻辑 | `dump` 看 VMAD → 反编译 pex；或直接翻 `Scripts/` 目录里名字相关的 pex |
| 插件层 | **什么都看不到**（native DLL 的行为不在 esp 里） | 只能看 `SKSE/Plugins/*.dll` 的**文件名**作提示 |

纪律：

- **记录层查不到 ⇒ 只能说「记录层无实现」**，不能对用户断言「这个包没有这个机制」。
  引擎行为（尤其是整合包自制的战斗/采集改动）常驻 SKSE 插件，任何 esp 工具都读不到。
- **字节串命中不等于记录存在**：EDID 常与资源路径（`Plants\FloraXxx.nif`）同形，
  `grep` 命中后必须回 `dump` 核实；反过来，`dump` 报「未找到」也只能说明**该 EditorID 不存在**，
  真名可能不同（例：山花是 `TREE` 记录、真名 `TreeFloraMountainFlower01Blue`，不是 `FLOR`）。
- 给用户的收尾应是：**已查到哪一层、卡在哪一层、以及游戏内怎么自行验证**（采 N 次记分布 / 看 MCM）。

**实例（2026-10-02，采集数量）**：要查「一次采到多份材料」出自哪里，逐层排查后——
炼金树无采集类 perk；`Requiem.esp` 覆盖的 54 条 `FLOR` 每条只挂单一 `PFIG`；
炼金相关 GMST 只有成长因子与金价倍率；无采集类脚本、无同名 SKSE 插件。
→ 判定为**记录层无实现**，机制在引擎/插件层，未定位。
