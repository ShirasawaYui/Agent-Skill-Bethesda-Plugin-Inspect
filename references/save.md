# 存档读取

> 版本：v1.0.0 · 最后更新：2026-10-01

## 1. 为什么需要它

| 数据源 | 回答的问题 | 工具 |
|---|---|---|
| 插件记录（esp/esm/esl） | 这个 mod **声明**要做什么 | bethkit |
| 存档（.ess） | 实际**发生了什么** | `tools/save-reader/` |

一处改动「有没有生效」，只有两边对照才答得准。记录里的值可能与实际表现不一致，常见原因有三：
覆盖链把它改写了、脚本在运行时又改了一次、mod 的开关由全局变量控制。

## 2. 文件格式

| 文件 | 内容 |
|---|---|
| `.ess` | 存档本体。签名 `TESV_SAVEGAMES`（SE 版），ZLIB 压缩。**头部为明文**，含角色名、等级、种族、性别、所在位置、游戏日期、经验 |
| `.skse` | SKSE co-save。各 SKSE 插件的自定义持久化数据，格式由各插件自理，本技能不做解析 |

## 3. 命令

```bash
"$PY" scripts/esp_inspect.py save info      <存档.ess>
"$PY" scripts/esp_inspect.py save globals   <存档.ess> [过滤词]
"$PY" scripts/esp_inspect.py save inventory <存档.ess>
"$PY" scripts/esp_inspect.py save forms     <存档.ess>
```

| 子命令 | 输出 |
|---|---|
| `info` | 角色摘要（名/等级/种族/性别/位置/游戏日期/经验）+ 结构统计（解压后体积、ChangeForm 数、全局变量数、是否有 co-save） |
| `globals` | 全局变量表，每行 `插件名:FormID = 值`；带过滤词时只输出匹配项并给出命中数 |
| `inventory` | 玩家背包，每行 `FormID (count = N)` |
| `forms` | ChangeForm 总数，按记录类型（REFR / ACHR / QUST / NPC_ …）降序排列 |

`globals` 是**最有信息量**的一项：mod 的运行时配置（开关、倍率、阈值）通常以全局变量保存，
按插件名筛选即可直接读出该 mod 当前的生效参数。

## 4. 数据规模参考

以 Skyrim SE 的大型整合包为例：

| 项目 | 典型量级 |
|---|---|
| 解压后体积 | 15–25 MB |
| ChangeForm 总数 | 5–10 万条 |
| 全局变量 | 2–5 千个 |
| Papyrus 脚本数据 | 10–15 MB（通常占比最大） |

ChangeForm 的构成通常是 `REFR`（放置物）与 `ACHR`（已生成角色）占大头，
其次是 `QUST`（任务）、`NPC_`、`LVLI`、`CELL`、`FLST` 等。

## 5. 已知限制

- **存档是快照** —— 只反映保存那一刻的状态。游戏运行中读到的与存档不一致属正常。
- **物品与引用只有 FormID** —— 翻译成可读名需要插件数据。可用本技能记录侧的查询把 FormID 换成名字：
  先用 `dump` 或 `find` 定位该 FormID 对应的记录。
- **`.skse` 只识别存在**，不解析其内部数据。
- **需要 Java 8 或更高** —— `doctor` 会报告组件与 Java 运行时的可用状态。
- 若存档被其他工具改动过，个别字段可能超出预期范围。

## 6. 组件构成与重建

```
tools/save-reader/
├── ReSaver.jar            解析引擎（ReSaver / FallrimTools，Apache-2.0）
├── SaveReader.class       导出入口（编译产物，Java 8 目标）
├── SaveReader.java        入口源码
├── lib/
│   ├── j2html-1.5.0.jar             引擎生成摘要文本所需
│   ├── lz4-pure-java-1.7.0.jar      存档压缩
│   └── juniversalchardet-1.0.3.jar  字符编码探测
└── LICENSE.txt            引擎许可
```

`lib/` 只保留运行必需的三个依赖；ReSaver 发行包中的 JavaFX、picocli、JUnit 与本功能无关，未收录。

仅当修改了 `SaveReader.java` 时才需要重新编译：

```bash
cd tools/save-reader
javac --release 8 -encoding UTF-8 -cp ReSaver.jar -d . SaveReader.java
```

## 7. 与 ReSaver 自带 CLI 的关系

ReSaver 自带命令行选项 `-i`（输出玩家背包），但该选项**实现有缺陷** —— 内部把 `null` 传给了
一个只接受非空参数的方法，运行时必然抛 `NullPointerException`。

本技能的 `save inventory` 是其替代实现，并额外提供 `info` / `globals` / `forms` 三项
该 CLI 本就不具备的导出能力。ReSaver 的图形界面不受影响，仍可正常使用。
