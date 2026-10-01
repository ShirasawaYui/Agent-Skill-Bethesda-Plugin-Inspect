# 异常处理

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

- 插件内的中文文本多为 **GBK**，少数为 UTF-8。按 UTF-8 解码出现乱码时改用 GBK 重试，不要直接下"文本损坏"的结论。
- 输出到终端乱码不影响数据本身，落盘时统一按 UTF-8 写入即可。

## 3. 关键词检索

| 现象 | 原因 | 处理 |
|---|---|---|
| 命中一大堆无关插件 | 关键词是常见子串 | 提高关键词特异性；改用 EditorID 精确匹配 |
| 明明存在的记录搜不到 | 记录被改名（覆盖链中重命名） | 用最终生效版本的 EditorID 检索，或先做覆盖链还原 |
| 某个插件读取出错被跳过 | 文件损坏、被占用或非标准格式 | 单独重试该文件；仍失败则在报告中标注该插件未被覆盖，不要当作"它没有该记录" |
| 关键词只在脚本或资源里，插件记录里搜不到 | `find` 只检索记录字段，不检索文件字节 | 用 `esp_inspect.py grep` 做字节级搜索，或直接对 pex / bsa 内资源单独处理 |
| `grep` 搜不到明明存在的文本 | 文本位于 pex、bsa 内，或使用了非 UTF-8/GBK 编码 | `grep` 会自动同时尝试 UTF-8 与 GBK；打包在归档内的内容需先提取再搜 |

**检索结论必须落到记录层**。字符串出现 ≠ 记录存在，两者不可混淆。

## 4. 覆盖链

| 现象 | 原因 | 处理 |
|---|---|---|
| `resolve` 返回 `None` | 传了带加载槽位的完整 FormID | 只用低 24 位本地 `object_id` |
| `find_by_editor_id` 返回 `None`，但记录确实存在 | 索引的是最终生效版本的 EditorID | 用生效版本的 EditorID，或改用 `chain` 还原覆盖链 |
| 载入 load order 时大量失败 | `plugins.txt` 里含未启用项或插件不在扫描目录 | 只处理 `*` 开头的行，并把未找到的插件列入报告 |
| 覆盖链顺序与实际不符 | 直接用了 `plugins.txt` 行号 | 实际加载槽位受 ESL 影响，行号不等于槽位；以 `global_form_id` 为准 |

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
