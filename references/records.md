# 记录签名对照

> 版本：v1.1.1 · 最后更新：2026-10-02

按"想查什么"找到对应的记录签名，再决定解析目标。

## 1. 需求 → 记录签名

| 想查的内容 | 记录签名 | 关键子记录 |
|---|---|---|
| 角色/生物参数（等级、血量、属性、技能、Perk、阵营） | `NPC_` | ACBS、AIDT、RNAM、CNAM、SNAM、PNAM、PRKR、SPLO、VTCK、VMAD |
| 任务流程（阶段、目标、别名、触发） | `QUST` | VMAD、INDX、QSDT、ANAM、ALST/ALFR/ALED/ALCO、CTDA、DNAM |
| 对话与分支 | `DIAL` → `INFO` | DATA、CTDA、VMAD |
| 道具（装备/武器/书籍/药水等） | `ARMO`、`WEAP`、`BOOK`、`ALCH`、`INGR`、`MISC`、`AMMO`、`KEYM`、`SLGM`、`LIGH` | DATA/DNAM、EITM、ENCH、KSIZ/KWDA |
| 法术与效果 | `SPEL`、`MGEF`、`ENCH` | SPIT、DATA、EFID/EFIT、VMAD |
| 天赋/被动 | `PERK` | DATA、PRKE、EPFT/EPFD、VMAD |
| 附魔与锻造配方 | `ENCH`、`COBJ` | ENIT/EFID，COBJ 的 CNAM/BNAM |
| 种族与职业 | `RACE`、`CLAS` | DATA、SPLO、VNAM |
| 场景与放置物 | `CELL`、`WRLD`、`REFR`、`ACHR` | DATA、XCLW、NAME、XESP、VMAD |
| 全局变量与设置 | `GLOB`、`GMST` | FLTV，GMST 的 DATA |
| 阵营与关系 | `FACT` | DATA、XNAM |
| 关键字与分类 | `KYWD` | — |
| 声音、光照、气候、天气 | `SOUN`、`LIGH`、`CLMT`、`WTHR` | — |

`VMAD` 表示该记录挂载了脚本——存在 VMAD 才需要进一步读脚本内容（见 `references/workflow.md` 的脚本分支）。

## 2. NPC_ 常用子记录

| 子记录 | 含义 |
|---|---|
| `EDID` | EditorID（编辑器内唯一名） |
| `FULL` | 显示名 |
| `SHRT` | 短名 |
| `ACBS` | 配置：位标志（等级/血量/魔法等是否自动计算）、等级、魔法/耐力偏移、各类数值 |
| `AIDT` | AI 数据：进攻性、勇气、协助、警戒半径等 |
| `RNAM` | 种族 |
| `ATKR` | 攻击种族（可为空） |
| `VTCK` | 声音类型 |
| `CNAM` | 职业（影响升级时的属性成长） |
| `SNAM` | 派系（可多条） |
| `PRKR` | Perk 条目（Perk + Rank），可多条 |
| `PRKZ` | Perk 条目数量 |
| `PNAM` | 已用 Perk 位图（多条） |
| `SPLO` | 施放的法术（可多条） |
| `SPCT` | 法术数量 |
| `PKID` | AI 包列表（可多条） |
| `KSIZ` + `KWDA` | 关键字数量 + 关键字列表 |
| `CNTO` | 携带物品（含数量） |
| `DOFT` / `DPLT` | 死亡掉落相关 |
| `VMAD` | 挂载的脚本与属性 |

**判读提示**：`ACBS` 的标志位决定其他数值字段是否被使用。开启 `Auto-calc stats` 时，等级与属性由引擎按种族/职业推算，记录里的显式数值可能不生效。

## 3. QUST 常用子记录

| 子记录 | 含义 |
|---|---|
| `EDID` / `FULL` | 标识与显示名 |
| `VMAD` | 脚本（任务逻辑通常在此） |
| `DNAM` | 任务标志（是否启用、是否允许重复等） |
| `INDX` + `QSDT` | 阶段序号 + 阶段日志文本 |
| `ANAM` | 阶段结束后是否运行"结束"片段 |
| `ALST` / `ALFR` / `ALED` / `ALCO` | 别名起点 / 匹配派系 / 匹配事件 / 匹配条件 |
| `CTDA` | 条件判定 |
| `SCHR` / `SCTX` | 脚本片段 |

任务的实际推进逻辑（何时进入下一阶段、触发什么效果）通常写在 VMAD 所指的脚本里，记录本身只提供骨架。

## 4. 法术相关

| 子记录 | 含义 |
|---|---|
| `SPIT` | 法术数据：类型、消耗、施法时间、射程 |
| `EFID` + `EFIT` | 效果引用 + 效果参数（数值、范围、持续时间） |
| `MGEF` 的 `DATA` | 效果标志与数值（含学派、抗性交互） |

判断"是否弱某属性"要看 `MGEF` 的 DATA 标志与目标记录的抗性设置，两者可能分别定义在不同插件中。

## 5. VMAD 说明

`VMAD` 内含脚本名与脚本属性绑定。它只说明"挂了这个脚本"，**脚本内部逻辑在 `.pex` 文件中**，需反编译才能阅读：

```bash
<技能目录>/tools/champollion/Champollion.exe <目标.pex>
```

输出落在**当前工作目录**（不是 pex 所在目录），用 `cd` 控制落点。

## 6. PERK 的前置条件怎么读

PERK 记录里**两类 CTDA 含义完全不同**：

| 位置 | 含义 |
|---|---|
| **第一个 `DATA` 子记录之前**的 CTDA | **学习前置条件**（所需技能等级、需先拥有的 Perk） |
| `DATA` 之后、夹在 `PRKE`…`PRKF` 之间的 CTDA | 该 perk 的**生效**条件，不是前置 |

**只取第一个 `DATA` 之前的那批 CTDA**，即可还原"点亮它需要什么"。

### CTDA 的 32 字节布局

| 偏移 | 长度 | 含义 |
|---|---|---|
| 0 | 1 | 比较符：`0x00`=等于、`0x20`=不等于、`0x40`=大于、`0x60`=大于等于、`0x80`=小于、`0xA0`=小于等于 |
| 4 | 4 | 比较值（float） |
| 8 | 2 | 函数索引（uint16） |
| 12 | 4 | 参数 1 |
| 16 | 4 | 参数 2 |
| 20 | 4 | 作用对象（Run On） |
| 28 | 4 | 参数 3 |

### 两个最常用的函数索引

| 索引 | 函数 | 参数 1 的含义 |
|---:|---|---|
| `277` | `GetActorValue` | **ActorValue 索引**（6=单手、7=双手、10=铁匠、20=毁灭系、22=恢复系…） |
| `448` | `HasPerk` | **被要求的 perk 的 FormID**（高字节超过 master 数即指向本插件） |

例：`函数=277、参数1=20、比较值=20.0、比较符=>=` 读作「**毁灭系 ≥ 20**」。

**免去手工解析**：内置 schema 能把条件解成命名后的字段（含枚举与 FormId 类型）：

```python
cat = bethkit.SchemaCatalog.embedded()
ctx = bethkit.SemanticContext(package=cat.package(bethkit.Game.SKYRIM_SE))
for f in ctx.view(record).fields():
    if f.name == "CTDA":
        ...   # 每项含 Function / Comparison Value / Parameter #1
```

### 三个必须知道的陷阱

1. **EditorID 里的数字不是权威等级**。实测：`VKR_Des_020_DestructionDualCasting` 的 EditorID 写 `020`，
   CTDA 实际要求 **25**；`MagicResistance2` 写 `025`，实际要 **50**。**等级一律以 CTDA 为准。**
2. **`_NPC` 后缀的记录不属于玩家技能树**。它们同前缀、同命名风格，但只挂在 NPC 上，
   混进列表会误导（例：`VKR_Des_060_ImpactNPC`）。
3. **FULL / DESC 均为空的记录是空壳**。常见于被后续插件覆盖致失效的原版 perk
   （如整合包里的 `REQ_NULL_*`），应单独归入附录而非主表。
4. **EditorID 带 `NULL` 或被 `===` 包裹 = 已被禁用**。Requiem 系整合包惯用手法：把原版 perk
   **改名加 `NULL` 后缀来屏蔽** —— 记录还在、FULL 名甚至已被汉化，但**游戏内不显示、不可点**。
   实测例：`===VKR_Alc_100_DoubleToilAndTrouble_PerkNULL===`（表里写作「不辞辛劳」）、
   `===VKR_Loc_070_DungeonMaster_PerkNULL===`（「地牢大师」）。
   **不剔除这类记录，会给出"能点却点不了"的错误建议**（已实际踩过一次，靠用户截图才发现）。
5. **等级门槛 = max(EditorID 三位编号, CTDA 值)**。两者互相补位：
   - Mastery 组在 EditorID 里一律写 `000` → 靠 CTDA 给出 20 / 40 / 65 / 90
   - `VKR_Res_070_Necromage` 这类 EditorID 写明编号、**CTDA 却没有等级条件** → 靠 EditorID
   
   **最终仍以游戏内显示的 `REQUIRE n` 为准**（游戏 UI 会直接标出真实门槛）。

### 判断"某 perk 是否在玩家技能树上"

**别用 EditorID 前缀或"孤立性"去猜** —— 两套启发式都会误伤：异前缀的正当 perk（如铁匠的
`FZR_*`）、以及被书 / 道具前置隔断的链条（如「格斗技艺」要有训练秘籍才能点）。
**权威来源是 AVIF 记录里的节点表，见第 8 节。**

读不到 AVIF 时才退回粗筛，按顺序剔除这些**命名标记** —— 它们是整合包把记录"留而不用"的常见手法：
**记录仍在、`FULL` 名甚至已汉化，但游戏内不显示**。

| 标记 | 含义 | 例 |
|---|---|---|
| `NULL` 后缀 | 被禁用 | `===VKR_Alc_100_DoubleToilAndTrouble_PerkNULL===` |
| `===` 包裹 | 同上，双重标记 | 同上 |
| `_old_` | 旧版残留 | `VKR_Alt_old_Concentration_Perk` |
| `DUPLICATE` | 重复记录 | `CorpusEnchanterDUPLICATE001` |
| `_NPC` 后缀/结尾 | 敌人专用，不进玩家技能树 | `VKR_Des_060_XXX_NPC` |

⚠️ **`_Was` 后缀不能剔** —— `VKR_One_025_BasicSword1_Perk_WasBladesman1` 这类正是**正规成员**，
它表示"覆盖了名为 Bladesman 的原记录"。粗筛只能用来"起疑"，**判定一律以第 8 节的节点表为准**。

## 7. PERK 的实际数值效果怎么读

描述（`DESC`）只会说"提升威力"，**具体数值在 entry point** —— 那才是游戏引擎真正执行的部分。

### 结构

一个 perk 可含**多个** entry point 块，每块形如：

```
Header（Type / Rank / Priority）
Effect Data（Entry Point / Function）   ← 作用对象 + 运算方式
[CTDA …]                                ← 该块生效条件（不是学习前置）
Type（数值类型）
Data（数值）
End Marker
```

按 `Header` 出现位置切块、到 `End Marker` 结束即可。`Header.Type` 三类：

| 值 | 含义 | 数值在哪 |
|---|---|---|
| `Entry Point` | 数值修正（绝大多数） | 同块的 `Type` + `Data` |
| `Ability` | 额外挂一个法术 | `Effect Data` 直接是 SPEL 引用，**无 Type/Data** |
| `Quest + Stage` | 完成指定任务阶段后生效 | 无数值 |

### Function（运算方式）

| Function | 读作 |
|---|---|
| `Multiply Value` | `×N`（×0.85 = 减 15%） |
| `Add Value` | `+N` |
| `Set Value` | `= N`（开关型 perk 常用，1 = 开启） |
| `Multiply 1 + Actor Value Mult` | `×(1 + 技能值 × 系数)` |
| `Multiply Actor Value Mult` | `× 技能值 × 系数` |
| `Add Actor Value Mult` | `+ 技能值 × 系数` |
| `Select Spell` / `Add Activate Choice` | 非数值（选择法术 / 新增交互选项） |

### `Float/AV,Float` 的两个值 = (技能索引, 每点系数)

实测规律：**第一个值按整数读出来就是 ActorValue 索引**
（12=轻甲、16=炼金、17=口才、18=变化、19=召唤、20=毁灭、21=幻术、22=恢复…），第二个是该技能每 1 点的增益。
例：`(20.0, 0.02)` 读作「毁灭系技能 × 0.02」。

> bethkit 会把第一个值显示成大整数（float 的位模式，如 `1101004800` = 20.0f）。
> 需还原：`struct.unpack("<f", struct.pack("<I", v & 0xFFFFFFFF))[0]`。

### 注意

- **描述会省略数值，也可能与数值不符** —— 一律以 entry point 为准
- 一条 perk 的多个 entry point **并列生效**；但「新手/学徒/老手/专家/大师」这类
  **按法术等级分档**的 perk 只作用于对应等级的法术，互不叠加
- `Ability` 引用的法术通常是**无名隐藏法术**，解析不出名称属正常（如开锁专长就藏在其中）

## 8. PERK 树的成员关系怎么读（在 AVIF 里）

> **适用范围 —— 仅限 Skyrim 原版技能树的替换关系查找**
>
> 本节讲的是「Skyrim 的 18 棵星座树各归哪个插件」，以及顺着节点表读出「某棵树上有哪些 perk」。
> **以下情形不适用：**
> - **其它游戏**（Fallout 4 / Starfield 等）—— `AVIF` 承载技能树是 Skyrim 的结构，别直接套用；
> - **自定义技能树框架自画的树**（Custom Skills Framework 系列，如 `EldenPerkTree.esp`）——
>   它们**不写 `AVIF` 记录**，本方法看不见，得另找该框架自己的载体；
> - perk 的**等级 / 前置 / 实际数值** —— 走第 6、7 节的 CTDA 与 entry point；
> - 技能界面的**版式、图标**之类表现层问题。

**技能树（星座图）不是 PERK 记录的一部分，也没有独立的"树"记录 —— 它挂在 `AVIF`（Actor Value，技能）记录上。**

### 结构

AVIF 前半段是元数据（`EDID` / `FULL` / `DESC` / [`CNAM`] / `AVSK`），
**`AVSK` 之后是重复出现的节点组**：

```
PNAM FNAM XNAM YNAM HNAM VNAM SNAM CNAM [CNAM…] INAM    ← 一个节点
```

| 子记录 | 含义 |
|---|---|
| `PNAM` | 该节点的 **perk FormID**（4 字节，遵循本插件的 master 索引规则） |
| `INAM` | 节点序号 |
| `CNAM` | 连线目标（其它节点序号，可出现多次） |
| `XNAM` / `YNAM` | 网格坐标 |
| `HNAM` / `VNAM` / `SNAM` | 像素坐标与连线绘制字段 |
| `FNAM` | 伴随字段 |

**`PNAM` 为空的节点是树根锚点**，不是真 perk，读取时应跳过。

### 判据

> 一个 perk 属于哪棵树 ⇔ 它的 FormID 是否出现在该技能 AVIF 的 `PNAM` 列表里。

这是**读取**而非推断，优先于 EditorID 前缀、`_NPC` 剔除、孤立性等一切启发式。

**与连线无关**：`PNAM` 只管"这个节点在不在树上"。所以**孤立节点照样算成员** ——
哪怕它没有任何连线、也没有任何前置（旧那套"孤立性启发式"恰恰会把它误杀）。
这类 perk 的"等级 / 前置"列为空是**正常结果，不是解析失败**，表头应写明。

**连线的字段语义**（要画树形时才用，判定成员不需要）：

- `INAM` = 节点**自身**的序号
- `CNAM` = 该节点**连到哪些节点** —— 存的是目标节点的 `INAM` 值，可出现多个
- 树根锚点的 `CNAM` 指向第一个真节点

验证样本（开锁树）：`锚点 CNAM=[10]` → `INAM=10` 的节点是「雕虫小技」；
`「雕虫小技」CNAM=[1]` → `INAM=1` 的节点是「锁匠知识」；
`「锁匠知识」CNAM=[2,3,4]` → 三个下级节点。

### 多级 perk 不在节点表里 —— 要沿 `Next Perk` 链展开

节点表给的只是**链头**。多级 perk 的后续级通过 perk 记录里的 **`Next Perk`（子记录 `NNAM`）**
串成链，**不**在 `PNAM` 列表里。所以：

> 数"某棵树有多少个 perk"必须**按链展开**，只数节点会**大幅偏少**。
> （实测：单手树节点 20 个 → 展开 51 条；「战斧精通」是 5 级，节点里只有 1 个。）

读法：`NNAM` 是 4 字节 FormID，与其他引用一样按高字节换算归属。沿链走时**必须**设两个保护：

- **深度上限**（防环，16 级足够）
- **已访问集合**（同一记录可能被多棵树引用）

```python
nxt = None
for j in range(n):
    sr = r.subrecord_at(j)
    if sr.signature == b"NNAM":
        d = raw_of(sr)
        if d and len(d) >= 4:
            nxt = struct.unpack_from("<I", d, 0)[0]
        break
```

⚠️ `NNAM` 出现在**第一个 `DATA` 之后**（子记录序列形如
`EDID FULL DESC [CTDA…] DATA NNAM PRKE … PRKF`）—— 它**不是**学习前置条件，
别跟第 6 节那批 `CTDA` 混在一起读。

**副产品**：靠链能把"看着像该树、却不在节点表"的记录解释掉大半
（实测某整合包候选从 116 条降到 16 条，剩下的都是 Vokrii 精简删除后的残留）。
做差集对账时，**先扣掉链上成员再统计**，否则会报出一堆假漏网。

### 覆盖链末端怎么定

1. **顺序来源**：读 MO2 配置档的 `loadorder.txt` —— 它记的是**全序**（含官方主文件与全部插件）。
2. **启用状态**：`plugins.txt` 中以 `*` 开头者为启用。⚠️ **官方主文件
   （`Skyrim.esm` / `Update.esm` / `Dawnguard.esm` / `HearthFires.esm` / `Dragonborn.esm`）
   不写进 `plugins.txt`**，必须自行补入启用集合 —— 否则会漏掉它们对记录的改动
   （实测：`Update.esm` 覆盖了 `AVSmithing`，USSEP 覆盖了 `AVDestruction`）。
3. **对齐方式必须是 FormID，不是 EditorID**。覆盖的定义就是"同一 FormID 的记录在后排再次出现"。
   EditorID 匹配会在两种情形下出错：插件**新建记录却复用旧名**（误判为覆盖）、
   插件**覆盖时把 EditorID 改掉**（**整条漏掉**，此类改名在整合包里很常见）。
   身份换算：取记录的 `form_id`，高字节 < master 数为「引用第 N 个 master」，≥ master 数为「本插件自身」；
   身份 =（**插件名**，低 24 位）。**末端 = 该身份在 load order 中最后出现的那个启用插件。**
4. **前提**：这是直接读 MO2/mods 物理文件 + 上述两份 txt 复现 MO2 的判定，等价于 MO2 usvfs 的结果 ——
   前提是这两份文件即当前生效状态。顺序若刚被外部工具（LOOT 等）改动而尚未写盘，会与游戏不一致；
   **最终仍以游戏内为准**。

**为什么"取末端"不是可选项（实测反例）**：

| 技能 | 该技能 AVIF 的节点数 | 后果 |
|---|---|---|
| `AVAlchemy` | Vokrii **13** 个（含「美食家」）→ 末端 `REQ Chaos Valheim Mode.esp` 只剩 **11** 个 | 取 Vokrii 会把「美食家」**误报成在树上** |
| `AVBlock` | 原版 Skyrim.esm 有「无懈之击」的位置 → 末端 Vokrii 没有 | 取原版会**多报**一个被移除的 perk |

差一个插件，结论就从"有"变"没有"。所以必须**逐棵**按 load order 取最后定义者，
不能图省事只算某个"主技能树插件"。

**回查原版的用途**：拿 Skyrim.esm 的节点表做一次 dif 很有价值 ——
若某记录**原版树上有此位置、末端却没有**，说明它是被整合包**主动移除**的（而非从未存在）。
这比"不在表上"信息量更大，做差集对账时值得标出来。

### 已知漏洞（读的时候要防）

1. **`AVIF` 的 EditorID 不能按「AV ＋ 技能名」去推。** 实测：幻术树挂在 **`AVMysticism`** 上 ——
   那是上古卷轴 4 的旧名（4 代该学派叫 Mysticism），5 代改了学派名却没有改这条记录的 EditorID；
   而 `AVIllusionMod` / `AVIllusionPowerMod` / `AVIllusionSkillAdvance` 三条只是**修饰用 actor value，不是树**。
   已用节点表验证：`AVMysticism` 的节点正是 `IllusionNovice00` / `IllusionApprentice25` /
   `IllusionAdept50` / `IllusionExpert75` / `IllusionMaster100` / `KindredMage` / `Animage` …
   → **树要枚举出来，不要按名字拼。**
2. **同名插件文件在 MO2/mods 下可能有多份**（本项目实测 698 个插件里有 **26 个重名**）。
   直接遍历目录再按文件名去重，会取到**不是 MO2 实际加载的那一份**；
   正确做法是按 `modlist.txt` 的左侧优先级，取优先级最高的那个 mod 目录里的副本。
3. **基线之外的身份必须显式归类。** 若只把"身份落在原版基线里"的记录算作覆盖，其余一律落空，
   就会出现**静默丢弃** —— 读不到也不报错，结论却变成"没有该改动"。
4. **旧式 `plugins.txt`（无 `*`、只列启用者）**会让"只看 `*`"的解析把全部插件误判为未启用。
   换 profile 前先确认格式。
5. **`plugins.txt` 的 `*` ＝ MO2 里勾选启用的插件，应当采信。** 但它只反映 MO2 的
   **最后一次写盘**，与**正在运行的游戏**可能不同步（在 MO2 里改了启用、游戏没重启）。
   → 所以按 `*` 过滤的同时**必须把被过滤掉的名单打印出来**，并留一个"一并扫描"的开关；
   否则文件与游戏一旦不一致，结论就会和眼前所见相反。
   （工具早期在这里改错了方向：把"用户临时关掉某个插件调试"误判为"`*` 不可信"。
   实际该做的是**把过滤结果显式报出来**，而不是取消过滤。）

### 三个陷阱

1. **技能树本身也会被覆盖，且不同技能可能由不同插件提供。** AVIF 同样受 load order 决定 ——
   必须**按技能逐棵**找 load order 里最后一个定义该 `AVIF` 的插件。
   实测（同一整合包内）：铁匠＝`Fozars_Dragonborn_-_Requiem_Patch.esp`，
   箭术 / 重甲 / 轻甲＝`Requiem - EX combat.esp`，双手 / 炼金 / 附魔＝`REQ Chaos Valheim Mode.esp`，
   恢复＝`Requiem - CW - Vicnmods.esp`，其余才轮到 Vokrii。
   **假设"整棵树来自同一个插件"会整棵漏掉。**
2. 节点里的 `PNAM` 是**原版 perk 的 FormID** —— perk 大修普遍复用原版 id 并改写记录内容。
   因此把 FormID 解析成名字时**必须走 load order 归属**；只查 `Skyrim.esm` 只会读到原版旧名。
3. 想缩小扫描面时，可先列出 load order 中含 `AVIF` 的插件（通常只有个位数），再按技能逐棵取胜者；
   但这条捷径只决定"从哪些文件读"，**不改变上面的末端判定口径**。

### 最小实现

> **已脚本化**：`esp_inspect.py tree <MO2 配置档目录>` —— 一行一棵输出「技能 → 覆盖链 → 末端生效插件」。
> 下面写的是它的原理，供复核原理、或换环境重写时参考。

**路径 A —— 只求「哪棵树归谁」（不做成员归属）**

1. 从 `Skyrim.esm` 取全部 `AVIF` 的**记录头身份**（本项目 149 条）—— 不解析任何子记录，
   **也不要按名字挑技能**（幻术树那条叫 `AVMysticism`）；
2. 按 `loadorder.txt` × 启用状态（`plugins.txt` 的 `*` **＋ 5 个官方主文件**）逐插件扫描，
   凡是 `AVIF` 就只登记「(来源插件, 低 24 位)」；
3. 每条基线身份，取 **load order 里最后登记它的那个插件** = 末端；
4. 只对**末端记录**读子记录：**含 `AVSK` ＋ 节点组**的才是技能树，一行一棵输出 ——
   这一步顺带把"被改过但没有节点组的非技能 AV"排除掉。

> 全程只有**两处需要读内容**：取基线（只读记录头）与第 4 步（判断有无节点组）。
> 其余只是文本清单与记录头的比对。实测 594 个插件全扫约 20 秒。

**路径 B —— 连 perk 成员归属一起做**

5. 从 `AVSK` 起切分节点组（`PNAM` 起、`INAM` 止）；
6. `PNAM` → （master 名 或 本插件，低 24 位）→ 走 load order 归属解析成 perk 名称。
