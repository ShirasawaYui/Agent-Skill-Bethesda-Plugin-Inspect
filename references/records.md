# 记录签名对照

> 版本：v1.0.0 · 最后更新：2026-10-01

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
