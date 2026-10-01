# bethkit 引述文档

> 版本：v1.0.0 · 最后更新：2026-10-01

> **本文件是 bethkit 工具本身的引述资料（出处、安装、更新、回滚），不属于本技能的工作流。**
> 工作流见 `SKILL.md` 与 `references/workflow.md`；API 用法见 `references/api.md`。

bethkit 是解析 Bethesda 插件（esp/esm/esl）的第三方库：Rust 内核 + Python 绑定。本技能的记录读取能力建立于其上。

---

## 1. 出处

| 项目 | 地址 |
|---|---|
| Python 绑定（`pip install bethkit` 装的就是这个） | https://github.com/Modding-Forge/bethkit.py |
| Rust 内核（实际解析逻辑） | https://github.com/Modding-Forge/bethkit |
| PyPI | https://pypi.org/project/bethkit |
| 官方主页 | https://moddingforge.com/ |
| 许可 | Apache-2.0 |

参考信息：本技能编写时的版本为 **2.2.0**，上游最后提交 2026-09-27。

bethkit 内置的字段 schema 由 **xEdit 官方定义导出**（manifest 中 `source_repository = https://github.com/TES5Edit/TES5Edit`，`source_tag = xedit-4.1.5f`），因此字段名与 SSEEdit 界面显示一致。

## 2. 安装位置

装在**隔离虚拟环境**中，不污染系统 Python：

```
C:\Users\Administrator\.workbuddy\binaries\python\envs\default\
├── Scripts\python.exe              ← 调用解释器
└── Lib\site-packages\
    ├── bethkit\                    ← 包本体
    │   └── bethkit_ffi.dll         ← 自带 Rust 原生库，无需编译器
    └── bethkit-2.2.0.dist-info\
```

唯一外部依赖：`pydantic >= 2.5.3`。

## 3. 未安装时如何安装

先跑自检确认状态：

```bash
"<venv>/Scripts/python.exe" -c "import bethkit; print(bethkit.__version__)"
```

若环境不存在或包缺失，按下面重建（`<PY>` 为任意 Python 3.11+ 解释器）：

```bash
# 1. 建隔离 venv（已存在则跳过）
"<PY>" -m venv "C:/Users/Administrator/.workbuddy/binaries/python/envs/default"

# 2. 安装
"C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" \
    install --disable-pip-version-check bethkit

# 3. 验证
"C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe" \
    -c "import bethkit; from bethkit import Plugin, Game; print('ok')"
```

wheel 自带原生库，**不需要** Rust 工具链或 C 编译器。

## 4. 检查更新

脚本本身不联网；需要时手动执行下列命令比对版本。

```bash
VENV="C:/Users/Administrator/.workbuddy/binaries/python/envs/default"

# 当前已装版本
"$VENV/Scripts/python.exe" -c "import importlib.metadata as m; print(m.version('bethkit'))"

# PyPI 上的最新版本
curl -s -m 20 https://pypi.org/pypi/bethkit/json \
  | "$VENV/Scripts/python.exe" -c "import sys,json; d=json.load(sys.stdin); print('latest:', d['info']['version']); print('released:', d['urls'][0]['upload_time'][:10] if d.get('urls') else '?')"

# 本地候选版本列表（含可回滚的旧版）
"$VENV/Scripts/pip.exe" index versions bethkit

# Rust 内核发版记录
gh api repos/Modding-Forge/bethkit/releases --jq '.[] | "\(.tag_name)  \(.published_at[0:10])"'
```

判断规则：

- **同大版本内的小版本更新**（如 2.2.x → 2.3.0）：先看内核发版说明有无解析行为变化，再升级并回归 `scripts/esp_inspect.py doctor`。
- **大版本更新**（3.x）：API 可能不兼容，升级前先在临时 venv 里验证常用调用。
- **schema 与内核配套**：schema 由包内嵌的 `bethkit_ffi.dll` 提供，升级包同时更新 schema。若字段名突然对不上，先确认是否发生了版本变化。

## 5. 升级与回滚

```bash
VENV="C:/Users/Administrator/.workbuddy/binaries/python/envs/default"

# 升级到最新
"$VENV/Scripts/pip.exe" install -U bethkit

# 升级后必须回归
"<venv>/Scripts/python.exe" <技能目录>/scripts/esp_inspect.py doctor

# 回滚到指定版本
"$VENV/Scripts/pip.exe" install "bethkit==<版本号>"
```

## 6. 何时应当放弃 bethkit

bethkit 是**较新的项目**（仓库规模小、组织 2026 年才出现）。出现下列情况时，按顺序考虑替代方案，而不是继续排查：

1. 上游超过一年无发版，且出现无法绕过的解析错误；
2. 遇到特定插件的解析崩溃，且精简复现后仍失败；
3. 需要的能力（如写入、冲突计算）在 Python 层长期缺失。

替代路径：

| 方案 | 特点 | 代价 |
|---|---|---|
| `esplib`（PyPI，纯 Python） | 无二进制、零依赖，可读记录与字符串 | API 是字典式访问，无 schema 类型化解码；无 load-order 覆盖解析 |
| 纯字节串搜索 | 无任何依赖，几十秒扫全部插件 | 只能证明"该词出现在文件里"，无法区分记录名与任意字符串，误报率高 |
| SSEEdit（人工） | 权威、可视化 | 需手动操作，无法自动化 |

`esplib` 的安装方式与 bethkit 相同（`pip install esplib`）。切换前先确认它能否覆盖当前任务需要的记录类型。
