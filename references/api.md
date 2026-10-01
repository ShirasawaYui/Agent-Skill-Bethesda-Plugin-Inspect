# bethkit API 速查

> 版本：v1.0.0 · 最后更新：2026-10-01

面向"读插件"的高频调用与陷阱。完整定义见 https://github.com/Modding-Forge/bethkit.py 。

## 1. 对象模型

```
Plugin           一个 esp/esm/esl 文件
 └─ Group        记录分组（按记录签名分；含子分组）
     └─ Record   一条记录（signature + form_id + editor_id）
         └─ SubRecord   记录的字段原始块（4 字节签名 + 数据）

SchemaCatalog    字段定义目录（xEdit 官方 schema）
 └─ SchemaPackage  某个游戏的 schema 包
SemanticContext  把 Record 解码成带字段名的视图
 └─ RecordView    解码结果，.fields() 返回 NamedField 元组

PluginCache      跨插件的记录索引，用于覆盖解析
Archive          BSA/BA2 归档读取
LoadOrder        load order 与全局 FormID 解析
```

## 2. 基础调用

### 打开插件并遍历记录

```python
from pathlib import Path
from bethkit import Game, Plugin

with Plugin.open(Path(r"F:\...\SomeMod.esp"), Game.SKYRIM_SE) as pl:
    print(pl.source_name, pl.kind, pl.master_count, pl.group_count)
    print("masters:", [pl.master_at(i) for i in range(pl.master_count)])

    for gi in range(pl.group_count):
        g = pl.group_at(gi)
        if not g:
            continue
        for i in range(g.child_count):          # 属性
            if not g.child_is_record(i):
                continue
            r = g.child_as_record(i)
            print(r.signature, hex(r.form_id), r.editor_id)
```

`Game` 可取：`SKYRIM_SE` / `SKYRIM_LE` / `SKYRIM_VR` / `FALLOUT4` / `FALLOUT3` / `FALLOUT_NV` / `FALLOUT4_VR` / `FALLOUT76` / `OBLIVION` / `MORROWIND` / `STARFIELD`。

### 读取子记录

```python
n = r.subrecord_count            # ⚠️ 这是方法
n = r.subrecord_count()
for si in range(n):
    sr = r.subrecord_at(si)
    sr.signature                 # bytes，如 b'FULL'
    sr.as_str()                  # 文本类子记录
    sr.raw_bytes                 # 原始字节

sr = r.find_subrecord(b"FULL")   # 按签名取第一个
```

## 3. 字段级解码（推荐方式）

把记录解成**命名字段**，字段名与 SSEEdit 界面一致：

```python
import bethkit
from bethkit import Game, Plugin, SchemaCatalog, SemanticContext

ctx = SemanticContext(package=SchemaCatalog.embedded().package(Game.SKYRIM_SE))

with Plugin.open(path, Game.SKYRIM_SE) as pl:
    ...
    view = ctx.view(record)          # → RecordView
    for f in view.fields():          # NamedField 元组
        print(f.name, f.value)
```

`f.value` 的类型：

| 类型 | 含义 |
|---|---|
| `FlagsVal(raw_value, active_names)` | 位标志，`active_names` 已解出启用项 |
| `EnumVal(value, name)` | 枚举，已解出可读名 |
| `TypedFormId(raw, allowed_sigs)` | 指向其他记录的引用，附允许的签名 |
| `tuple[NamedField]` | 结构体或数组，继续下钻 |

解码前先确认字段名，不要臆断偏移——schema 是权威来源。

## 4. 覆盖解析

```python
from bethkit import PluginCache

cache = PluginCache()
for name in load_order:                  # 按 load order 顺序
    cache.add(name, Plugin.open(path_of(name), Game.SKYRIM_SE))

cache.record_count                       # 属性
rec = cache.resolve("SomeMod.esp", 0x00001234)     # 本地 object_id，无槽位前缀
hit = cache.find_by_editor_id("SomeEditorID")      # → CacheHit(record, global_form_id)
```

- `resolve` 的 `object_id` 是**去掉加载槽位的低 24 位**。传带槽位的完整 FormID 会返回 `None`。
- `find_by_editor_id` 只索引**最终生效版本**的 EditorID。记录在覆盖链中被改过名时，用旧名查不到。
- `CacheHit.global_form_id.plugin_name` 指向**最初定义**该记录的插件。

## 5. 归档读取

```python
import bethkit
with bethkit.Archive.open(path_bsa) as ar:
    print(ar.format_name, ar.file_count)
    for e in ar.entries():
        print(e.path)
    data = ar.extract("meshes/foo.nif")      # -> bytes | None
    ar.extract_to_file("meshes/foo.nif", out_path)
```

## 6. 陷阱清单

| 陷阱 | 表现 | 处理 |
|---|---|---|
| `Plugin.open` 的 `path` 必须是 `pathlib.Path` | 传 `str` 报 `AttributeError: 'str' object has no attribute 'name'` | 一律用 `Path(...)` |
| `Record.subrecord_count` 是**方法** | `TypeError: 'method' object cannot be interpreted as an integer` | 写 `r.subrecord_count()` |
| `Plugin.group_count` / `Group.child_count` 是**属性** | 加括号会报 `'int' object is not callable` | 不加括号 |
| `Plugin` 没有 `child_count` | `AttributeError` | 先 `group_at(i)` 拿 `Group` |
| `cache.add()` **接管 Plugin 句柄** | 之后访问原对象报 `BethkitClosedError: Plugin is closed` | 需要遍历就先把遍历做完，或为遍历单独再开一个句柄 |
| `RecordView` 禁止直接构造 | `TypeError` | 必须经 `SemanticContext.view()` |
| `resolve` 传入带槽位的 FormID | 返回 `None` | 只用低 24 位 `object_id` |

## 7. 写入能力（本技能不使用）

bethkit 提供 `PluginPatcher.replace_record` / `PluginWriter` / `RecordEditor` / `WritableRecord` 等写入接口。**本技能只做读取**，改插件请使用 SSEEdit。
