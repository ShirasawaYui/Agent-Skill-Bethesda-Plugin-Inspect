#!/usr/bin/env python3
"""esp_inspect.py — 读取 Bethesda 插件（esp/esm/esl）记录与字段。

依赖 bethkit（安装方式见 references/bethkit.md）。
本脚本只做本地读取，不联网、不修改任何插件。

用法:
    python esp_inspect.py doctor
    python esp_inspect.py find  <mods_root> <keyword> [keyword ...]
    python esp_inspect.py dump  <plugin_path> <editor_id|0xFORMID>
    python esp_inspect.py chain <plugins_txt> <local_id> [--mods-root DIR] [--signature SIG]
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLUGIN_EXT = {".esp", ".esm", ".esl"}

# MO2 不把官方主文件写进 plugins.txt，但它们在 loadorder.txt 里，且可能改过记录
# （实测：Update.esm 改过 AVSmithing，USSEP 改过 AVDestruction）
OFFICIAL_MASTERS = {
    "skyrim.esm", "update.esm", "dawnguard.esm", "hearthfires.esm", "dragonborn.esm",
}

# Skyrim 原版 18 棵星座树的载体 AVIF。
# ⚠ 幻术树那条记录叫 AVMysticism —— 上古卷轴 4 的旧名（4 代该学派叫 Mysticism），
#   5 代改了学派名却没改记录名；AVIllusionMod / AVIllusionPowerMod /
#   AVIllusionSkillAdvance 三条只是修饰用 actor value，不是树。
SKILL_AVIF = [
    ("AVOneHanded", "单手武器"), ("AVTwoHanded", "双手武器"), ("AVMarksman", "箭术"),
    ("AVBlock", "格挡"), ("AVSmithing", "铁匠"), ("AVHeavyArmor", "重甲"),
    ("AVLightArmor", "轻甲"), ("AVPickpocket", "扒窃"), ("AVLockpicking", "开锁"),
    ("AVSneak", "潜行"), ("AVAlchemy", "炼金"), ("AVSpeechcraft", "口才"),
    ("AVAlteration", "变化"), ("AVConjuration", "召唤"), ("AVDestruction", "毁灭"),
    ("AVMysticism", "幻术"), ("AVRestoration", "恢复"), ("AVEnchanting", "附魔"),
]

OPTIONAL_TOOLS = (
    ("Champollion", "champollion/Champollion.exe",
     "https://github.com/Orvid/Champollion/releases  (LGPL-3.0)"),
    ("BSA Browser CLI", "bsa-browser/bsab.exe",
     "https://github.com/AlexxEG/BSA_Browser/releases  (GPL-3.0)"),
)

INSTALL_HINT = """\
bethkit 不可用。在**任意**隔离环境里装上即可 —— 不绑定本机路径，换台机器也能跑：

  # 1) 建隔离环境（已存在则跳过）；<PYTHON> 是任意 Python 3.10+，<VENV> 换成你自己的路径
  <PYTHON> -m venv <VENV>

  # 2) 安装
  <VENV>\\Scripts\\pip.exe install bethkit      （Windows）
  <VENV>/bin/pip install bethkit               （macOS / Linux）

  # 3) 验证
  <VENV>\\Scripts\\python.exe -c "import bethkit; print('ok')"

装好后用它的解释器调用本脚本：

  <VENV>\\Scripts\\python.exe esp_inspect.py <子命令> ...

参考：安装、检查更新与回滚见 references/bethkit.md。
本脚本不含任何绝对路径 —— 所有位置都由命令行参数传入，或从参数向上查找派生。
"""


def _safe_stdout():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _import_bethkit(required=True):
    try:
        import bethkit  # noqa: F401
        return bethkit
    except ImportError:
        if required:
            print(INSTALL_HINT, file=sys.stderr)
            sys.exit(2)
        return None


def _game(bethkit, name):
    try:
        return getattr(bethkit.Game, name.upper())
    except AttributeError:
        print(f"未知游戏标识: {name}", file=sys.stderr)
        sys.exit(2)


def _iter_group(g):
    for i in range(g.child_count):
        if g.child_is_record(i):
            r = g.child_as_record(i)
            if r is not None:
                yield r
        else:
            sub = g.child_as_group(i)
            if sub is not None:
                yield from _iter_group(sub)


def _iter_records(plugin):
    for gi in range(plugin.group_count):
        g = plugin.group_at(gi)
        if g is None:
            continue
        yield from _iter_group(g)


def _subrecord_count(record):
    n = record.subrecord_count
    return n() if callable(n) else n


def _subrecord_sigs(record):
    return [record.subrecord_at(i).signature.decode("ascii", "replace")
            for i in range(_subrecord_count(record))]


def _text_of(record, sig=b"FULL"):
    sr = record.find_subrecord(sig)
    if sr is None:
        return ""
    try:
        return sr.as_str()
    except Exception:
        return ""


def _scan_plugins(root):
    return sorted(p for p in Path(root).rglob("*")
                  if p.suffix.lower() in PLUGIN_EXT and p.is_file())


# ---------------------------------------------------------------- doctor

def cmd_doctor(args):
    bethkit = _import_bethkit(required=False)
    tools = Path(__file__).resolve().parent.parent / "tools"

    print("环境自检")
    print(f"  Python          : {sys.version.split()[0]}  ({sys.executable})")

    if bethkit is None:
        print("  bethkit         : 未安装")
        print()
        print(INSTALL_HINT)
    else:
        import importlib.metadata as md
        try:
            ver = md.version("bethkit")
        except Exception:
            ver = "?"
        print(f"  bethkit         : {ver}")
        try:
            cat = bethkit.SchemaCatalog.embedded()
            pkg = cat.package(_game(bethkit, args.game))
            man = pkg.manifest()
            src = (man.get("source_tag", "?") if isinstance(man, dict)
                   else getattr(man, "source_tag", "?"))
            print(f"  schema          : {args.game.lower()} 可用（源自 {src}）")
        except Exception as e:
            print(f"  schema          : 加载失败 - {type(e).__name__}: {e}")

    print("  可选工具（不在包内分发，缺失不影响主流程）:")
    for label, rel, url in OPTIONAL_TOOLS:
        p = tools / rel
        print(f"    {label:<16}: {'已内置' if p.is_file() else '未安装 -> ' + url}")

    print()
    print("  存档读取（save 子命令）:")
    sr = _save_reader_dir()
    if (sr / "ReSaver.jar").is_file() and (sr / "SaveReader.class").is_file():
        print("    组件            : 就绪")
        java = _find_java()
        print(f"    Java 运行时     : {java if java else '未找到（需要 Java 8 或更高）'}")
    else:
        print(f"    组件            : 缺失 -> {sr}")

    return 0

# ---------------------------------------------------------------- find

def cmd_find(args):
    bethkit = _import_bethkit()
    game = _game(bethkit, args.game)
    root = Path(args.mods_root)
    if not root.is_dir():
        print(f"目录不存在: {root}", file=sys.stderr)
        return 2

    keys = [k.lower() for k in args.keywords]
    files = _scan_plugins(root)
    print(f"扫描 {len(files)} 个插件，关键词: {', '.join(keys)}")

    t0 = time.time()
    hits = failures = 0
    for path in files:
        try:
            with bethkit.Plugin.open(path, game) as pl:
                for r in _iter_records(pl):
                    eid = r.editor_id or ""
                    full = _text_of(r)
                    hay = (eid + " " + full).lower()
                    if not any(k in hay for k in keys):
                        continue
                    hits += 1
                    print(f"  {path.relative_to(root)}")
                    print(f"      {r.signature.decode('ascii', 'replace')}  "
                          f"EditorID={eid}  FormID={hex(r.form_id)}  NAME={full}")
        except Exception as e:
            failures += 1
            print(f"  ! 跳过 {path.name}: {type(e).__name__}: {e}")

    print(f"\n命中 {hits} 条记录；读取失败 {failures} 个插件；耗时 {time.time() - t0:.1f}s")
    if failures:
        print("失败插件未被覆盖，不可据此判定「它没有该记录」。")
    return 0


# ---------------------------------------------------------------- dump

def cmd_dump(args):
    bethkit = _import_bethkit()
    game = _game(bethkit, args.game)
    path = Path(args.plugin)
    if not path.is_file():
        print(f"插件不存在: {path}", file=sys.stderr)
        return 2

    token = args.target
    want_id = None
    want_eid = None
    if token.lower().startswith("0x") or token.isdigit():
        want_id = int(token, 16) if token.lower().startswith("0x") else int(token)
    else:
        want_eid = token

    ctx = None
    try:
        ctx = bethkit.SemanticContext(
            package=bethkit.SchemaCatalog.embedded().package(game))
    except Exception as e:
        print(f"[提示] schema 不可用，退化为原始子记录输出: {type(e).__name__}: {e}",
              file=sys.stderr)

    with bethkit.Plugin.open(path, game) as pl:
        print(f"插件: {pl.source_name}  类型: {pl.kind}  masters: {pl.master_count}")
        print(f"masters: {[pl.master_at(i) for i in range(pl.master_count)]}\n")

        found = []
        for r in _iter_records(pl):
            if want_eid is not None:
                if (r.editor_id or "") == want_eid:
                    found.append(r)
            else:
                if r.form_id == want_id or (r.form_id & 0x00FFFFFF) == (want_id or 0):
                    found.append(r)
        if not found:
            print("未找到目标记录。")
            return 1

        for r in found:
            sigs = _subrecord_sigs(r)
            print(f"==== {r.signature.decode('ascii', 'replace')}  "
                  f"EditorID={r.editor_id}  FormID={hex(r.form_id)}  "
                  f"子记录={len(sigs)}  VMAD={'有' if 'VMAD' in sigs else '无'}")
            print(f"     子记录序列: {' '.join(sigs)}")

            if ctx is not None:
                try:
                    view = ctx.view(r)
                    fields = view.fields()
                    print(f"     字段解码（{len(fields)} 项）:")
                    for f in fields:
                        print(f"       {str(f)[:200]}")
                except Exception as e:
                    print(f"     [字段解码失败] {type(e).__name__}: {e}")
            print()
    return 0


# ---------------------------------------------------------------- chain

def _read_order_and_enabled(plugins_txt):
    """返回 (load order 全序, plugins.txt 里带 `*` 的集合)。

    顺序取自同目录的 `loadorder.txt`（**全序**，含官方主文件与全部插件）；
    `*` 集合取自 `plugins.txt`，并**补上 5 个官方主文件** —— 它们不写进 plugins.txt，
    却可能改过记录（实测 Update.esm 改过 AVSmithing）。

    ⚠ **不要把 `*` 当成"是否生效"的唯一依据**：实测本机 `plugins.txt` 里
    `Vokrii - Minimalistic Perks of Skyrim.esp` 没有 `*`，但游戏内显然在用它的技能树
    （有 enabled 插件以它为 master）。所以调用方**默认按 load order 全序扫描**，
    只把"未勾选"作为提示信息打印出来；要严格过滤需显式打开 `--only-enabled`。
    """
    p = Path(plugins_txt)
    if p.is_dir():
        p = p / "plugins.txt"
    enabled, listed = set(OFFICIAL_MASTERS), []
    for line in p.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            name = line[1:].strip()
            if name:
                enabled.add(name.lower())
                listed.append(name)
    order_file = p.parent / "loadorder.txt"
    order = []
    if order_file.is_file():
        for line in order_file.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                order.append(line)
    if not order:
        order = listed
    return order, enabled


def _find_data_dir(mods_root):
    """从 mods 目录向上找含 Skyrim.esm 的 Data 目录（MO2 便携实例装在游戏目录内）。"""
    for parent in list(Path(mods_root).resolve().parents)[:5]:
        cand = parent / "Data"
        if (cand / "Skyrim.esm").is_file():
            return cand
    return None


def _index_plugins(mods_root, modlist_txt=None, dup_policy="first"):
    """插件文件名 -> 路径。重名时按 `modlist.txt` 行序取（行首＝高优先级，依 MO2 惯例）。

    返回 (index, dups)：dups 只收「重名且各副本大小不一致」的项，附带全部候选，
    以便明确告知取用了哪一份 —— MO2/mods 下同一个插件名可能有多份副本。
    """
    rank = {}
    if modlist_txt and Path(modlist_txt).is_file():
        for i, line in enumerate(Path(modlist_txt).read_text(
                encoding="utf-8-sig", errors="replace").splitlines()):
            line = line.strip().lstrip("+-")
            if line and not line.startswith("#"):
                rank.setdefault(line.lower(), i)

    groups = {}
    for f in _scan_plugins(mods_root):
        groups.setdefault(f.name.lower(), []).append(f)

    index, dups = {}, {}
    for name, paths in groups.items():
        if len(paths) == 1:
            index[name] = paths[0]
            continue

        def _key(f, _root=Path(mods_root)):
            try:
                mod = f.relative_to(_root).parts[0].lower()
            except Exception:
                mod = ""
            r = rank.get(mod, 10 ** 6)
            return r if dup_policy == "first" else -r

        ordered = sorted(paths, key=_key)
        index[name] = ordered[0]
        if len({f.stat().st_size for f in paths}) > 1:
            dups[name] = ordered
    return index, dups


def _avif_identities(plugin, filename):
    """返回 [(owner_plugin_name, lo, editor_id)] —— 记录身份，不看内容。

    owner 换算：formid 高字节 < master 数量 → 引用第 N 个 master；≥ → 本插件自身。
    """
    masters = []
    mc = getattr(plugin, "master_count", 0)
    mc = mc() if callable(mc) else mc
    for i in range(mc):
        try:
            masters.append(str(plugin.master_at(i)).lower())
        except Exception:
            masters.append("")
    me = str(filename).lower()
    out = []
    for r in _iter_records(plugin):
        if r.signature != b"AVIF":
            continue
        f = r.form_id
        hi, lo = f >> 24, f & 0xFFFFFF
        owner = me if hi >= len(masters) else masters[hi]
        try:
            eid = r.editor_id
        except Exception:
            eid = "?"
        out.append((owner, lo, eid))
    return out


def _avif_nodes(plugin, want_sigs=("AVSK", "PNAM")):
    """返回 {local_id: (PNAM 节点数, 是否含 AVSK)} —— 用来判断"是不是一棵树"。"""
    out = {}
    for r in _iter_records(plugin):
        if r.signature != b"AVIF":
            continue
        sigs = _subrecord_sigs(r)
        out[r.form_id & 0xFFFFFF] = (sigs.count(want_sigs[1]), want_sigs[0] in sigs)
    return out


def _infer_mods_root(plugins_txt):
    p = Path(plugins_txt).resolve()
    # .../MO2/profiles/<name>/plugins.txt  ->  .../MO2/mods
    for parent in p.parents:
        cand = parent / "mods"
        if cand.is_dir():
            return cand
    return None


def cmd_chain(args):
    bethkit = _import_bethkit()
    game = _game(bethkit, args.game)

    order, enabled = _read_order_and_enabled(args.plugins_txt)
    if not order:
        print("plugins.txt 中没有可用条目。", file=sys.stderr)
        return 2

    mods_root = Path(args.mods_root) if args.mods_root else _infer_mods_root(args.plugins_txt)
    if mods_root is None or not mods_root.is_dir():
        print("无法确定 mods 目录，请用 --mods-root 指定。", file=sys.stderr)
        return 2

    index, _dups = _index_plugins(
        mods_root, Path(args.plugins_txt).parent / "modlist.txt")

    local_id = int(args.local_id, 16) if args.local_id.lower().startswith("0x") \
        else int(args.local_id)
    want_sig = args.signature.encode("ascii") if args.signature else None

    print(f"load order: {len(order)} 项，plugins.txt 已勾选 {len(enabled)} 个（含 5 个官方主文件）")
    print(f"mods 目录 : {mods_root}")
    print(f"目标      : local_id={hex(local_id)}"
          f"{'  signature=' + args.signature if args.signature else ''}\n")

    t0 = time.time()
    chain = []
    missing = 0
    scanned = 0
    for pos, name in enumerate(order):
        if args.only_enabled and name.lower() not in enabled:
            continue
        path = index.get(name.lower())
        if path is None:
            missing += 1
            continue
        scanned += 1
        try:
            with bethkit.Plugin.open(path, game) as pl:
                for r in _iter_records(pl):
                    if (r.form_id & 0x00FFFFFF) != local_id:
                        continue
                    if want_sig and r.signature != want_sig:
                        continue
                    sigs = _subrecord_sigs(r)
                    chain.append({
                        "pos": pos, "name": name, "sig": r.signature.decode("ascii", "replace"),
                        "eid": r.editor_id, "form": r.form_id,
                        "n": len(sigs), "vmad": "VMAD" in sigs,
                    })
                    break
        except Exception as e:
            print(f"  ! {name}: {type(e).__name__}: {e}")

    if not chain:
        print(f"未找到该记录（扫描 {scanned} 个插件，耗时 {time.time() - t0:.1f}s）。")
        if missing:
            print(f"另有 {missing} 个插件未在 mods 目录中找到。")
        return 1

    width = max(len(c["name"]) for c in chain)
    for i, c in enumerate(chain):
        mark = "  <- 最终生效" if i == len(chain) - 1 else ""
        print(f"  [{c['pos']:>3}] {c['name']:<{width}}  {c['sig']}  "
              f"EditorID={c['eid']:<16} FormID={hex(c['form'])}  "
              f"子记录={c['n']:>3}  VMAD={'有' if c['vmad'] else '无'}{mark}")

    print(f"\n共 {len(chain)} 份定义；耗时 {time.time() - t0:.1f}s")
    print("提示：最终生效版可能与首版差异很大（字段数、EditorID、脚本挂载）。"
          "下结论前务必以生效版为准。")
    if missing:
        print(f"注意：{missing} 个启用插件未在 mods 目录中找到，覆盖链可能不完整。")
    return 0


# ---------------------------------------------------------------- grep

def cmd_grep(args):
    """纯字节串搜索：不需要 bethkit 的降级定位手段。"""
    target = Path(args.target)
    if target.is_dir():
        files = _scan_plugins(target)
    elif target.is_file():
        files = [target]
    else:
        print(f"路径不存在: {target}", file=sys.stderr)
        return 2

    keys = []
    for k in args.keywords:
        keys.append((k, k.encode("utf-8")))
        try:
            blob = k.encode("gbk")
            if blob != keys[-1][1]:
                keys.append((k + "(gbk)", blob))
        except UnicodeEncodeError:
            pass

    print(f"扫描 {len(files)} 个文件，关键词: {', '.join(args.keywords)}")
    t0 = time.time()
    hits = 0
    for path in files:
        try:
            data = path.read_bytes()
        except Exception as e:
            print(f"  ! 跳过 {path.name}: {type(e).__name__}: {e}")
            continue
        found = [f"{label}@{hex(data.find(blob))}"
                 for label, blob in keys if data.find(blob) >= 0]
        if found:
            hits += 1
            name = path.name if target.is_file() else str(path.relative_to(target))
            print(f"  {name}  -> {', '.join(found)}")

    print(f"\n命中 {hits} 个文件；耗时 {time.time() - t0:.1f}s")
    print("注意：字节命中只说明该字符串出现在文件里，无法区分记录名与普通文本。")
    print("     结论必须回到 find / dump 在记录层复核。")
    return 0


# ---------------------------------------------------------------- save

SAVE_READER_HINT = """\
存档读取组件不可用。该组件应位于本技能目录下：

    tools/save-reader/
    ├── ReSaver.jar        解析引擎（Apache-2.0，来自 ReSaver / FallrimTools）
    ├── SaveReader.class   导出入口
    ├── SaveReader.java    入口源码
    ├── lib/               运行依赖
    └── LICENSE.txt        解析引擎许可

另需 Java 运行时（Java 8 或更高）。"""


def _save_reader_dir():
    return Path(__file__).resolve().parent.parent / "tools" / "save-reader"


def _find_java():
    """按 环境变量 → 常见安装位置 → PATH 的顺序查找 java。"""
    exe = "java.exe" if os.name == "nt" else "java"

    home = os.environ.get("JAVA_HOME")
    if home:
        cand = Path(home) / "bin" / exe
        if cand.is_file():
            return str(cand)

    if os.name == "nt":
        bases = [r"C:\Program Files\Java", r"C:\Program Files\Eclipse Adoptium",
                 r"C:\Program Files\Zulu", r"C:\Program Files\Microsoft"]
        found = []
        for base in bases:
            b = Path(base)
            if b.is_dir():
                found.extend(p for p in b.glob("*/bin/java.exe") if p.is_file())
        if found:
            return str(sorted(found, reverse=True)[0])

    return shutil.which("java")


def cmd_save(args):
    """读取 Skyrim 存档（.ess）内容 —— 透传给 tools/save-reader/SaveReader。"""
    sub_args = list(args.save_args)
    if not sub_args:
        print("用法: esp_inspect.py save <info|globals|inventory|forms> <存档.ess> [过滤词]",
              file=sys.stderr)
        return 2

    tools = _save_reader_dir()
    if not (tools / "ReSaver.jar").is_file() or not (tools / "SaveReader.class").is_file():
        print(SAVE_READER_HINT, file=sys.stderr)
        return 2

    java = _find_java()
    if java is None:
        print("未找到 Java 运行时（需要 Java 8 或更高）。请在 PATH 或 JAVA_HOME 中提供 java。",
              file=sys.stderr)
        return 2

    cp_parts = [str(tools), str(tools / "ReSaver.jar")]
    lib_dir = tools / "lib"
    if lib_dir.is_dir():
        cp_parts.extend(str(p) for p in sorted(lib_dir.glob("*.jar")))

    cmd = [java, "-Dstdout.encoding=UTF-8", "-Dfile.encoding=UTF-8",
           "-cp", os.pathsep.join(cp_parts), "SaveReader"] + sub_args
    try:
        return subprocess.run(cmd).returncode
    except OSError as e:
        print(f"调用 Java 失败: {e}", file=sys.stderr)
        return 2


# ---------------------------------------------------------------- tree

def cmd_tree(args):
    """原版星座树的替换关系：一行一棵输出「技能 → 覆盖链 → 末端生效插件」。

    仅适用于 **Skyrim 原版技能树**。自定义技能树框架（Custom Skills Framework 系列，
    如 EldenPerkTree）不写 AVIF 记录，本命令看不见它们。
    """
    bethkit = _import_bethkit()
    game = _game(bethkit, args.game)

    prof = Path(args.profile)
    plugins_txt = (prof / "plugins.txt") if prof.is_dir() else prof
    if not plugins_txt.is_file():
        print(f"找不到 plugins.txt：{plugins_txt}", file=sys.stderr)
        return 2

    order, enabled = _read_order_and_enabled(plugins_txt)
    mods_root = Path(args.mods_root) if args.mods_root else _infer_mods_root(plugins_txt)
    if mods_root is None or not mods_root.is_dir():
        print("无法确定 mods 目录，请用 --mods-root 指定。", file=sys.stderr)
        return 2
    data_dir = Path(args.data_dir) if args.data_dir else _find_data_dir(mods_root)
    if data_dir is None or not (data_dir / "Skyrim.esm").is_file():
        print("找不到 Skyrim.esm，请用 --data-dir 指定游戏的 Data 目录。", file=sys.stderr)
        return 2

    index, dups = _index_plugins(mods_root, plugins_txt.parent / "modlist.txt",
                                 args.dup_policy)

    unstarred = [n for n in order if n.lower() not in enabled]
    print("Skyrim 原版星座树 · 替换关系（只读，不联网）")
    print(f"  配置档    : {plugins_txt.parent}")
    print(f"  mods 目录 : {mods_root}")
    print(f"  Data 目录 : {data_dir}")
    print(f"  load order: {len(order)} 项"
          f"{'（--only-enabled：只扫 plugins.txt 已勾选者）' if args.only_enabled else ''}")
    if unstarred:
        print(f"  未勾选    : {len(unstarred)} 个 —— {'、'.join(unstarred[:6])}"
              f"{' …' if len(unstarred) > 6 else ''}")
        print("              默认仍按 load order 全序扫描（实测未勾选者也可能在游戏内生效）；"
              "要严格过滤请加 --only-enabled")

    baseline = {}
    with bethkit.Plugin.open(data_dir / "Skyrim.esm", game) as pl:
        for owner, lo, eid in _avif_identities(pl, "Skyrim.esm"):
            baseline[(owner, lo)] = eid
    print(f"  基线      : Skyrim.esm 共 {len(baseline)} 条 AVIF（只取身份，不解析内容）\n")

    t0 = time.time()
    chain = {k: [] for k in baseline}
    winner, unmatched = {}, {}
    scanned = absent = failed = 0
    for pos, name in enumerate(order):
        if args.only_enabled and name.lower() not in enabled:
            continue
        path = index.get(name.lower())
        if path is None:
            absent += 1
            continue
        scanned += 1
        try:
            with bethkit.Plugin.open(path, game) as pl:
                for owner, lo, eid in _avif_identities(pl, name):
                    key = (owner, lo)
                    if key in baseline:
                        chain[key].append((pos, name))
                        winner[key] = (pos, name, path)
                    else:
                        unmatched[(name, owner, lo)] = eid
        except Exception as e:
            failed += 1
            print(f"  ! {name}: {type(e).__name__}: {e}")

    cache = {}

    def nodes_of(path):
        if path not in cache:
            try:
                with bethkit.Plugin.open(path, game) as pl:
                    cache[path] = _avif_nodes(pl)
            except Exception:
                cache[path] = {}
        return cache[path]

    print(f"{'AVIF':<19} {'技能':<5} {'节点':>3}  末端生效插件")
    print("-" * 78)
    modded = 0
    for eid, cn in SKILL_AVIF:
        key = next((k for k, v in baseline.items() if v == eid), None)
        if key is None:
            print(f"{eid:<19} {cn:<5} {'-':>3}  基线里没有这条 AVIF")
            continue
        ch = chain.get(key) or []
        if len(ch) <= 1:
            print(f"{eid:<19} {cn:<5} {'-':>3}  无人修改（仍用原版）")
            continue
        pos, name, path = winner[key]
        n, has_avsk = nodes_of(path).get(key[1], (0, False))
        if not has_avsk or n == 0:
            print(f"{eid:<19} {cn:<5} {n:>3}  [{pos:>3}] {name}   ⚠ 无节点组，可能不是树")
            continue
        modded += 1
        print(f"{eid:<19} {cn:<5} {n:>3}  [{pos:>3}] {name}")
        print(f"{'':<19} {'':<5} {'':>3}       链：{' → '.join(x[1] for x in ch)}")

    print("-" * 78)
    print(f"被人修改过的树 {modded} / 18　｜　扫描 {scanned} 个插件"
          f"（{absent} 个文件缺失，{failed} 个读取失败）　｜　耗时 {time.time() - t0:.1f}s")

    if dups:
        print(f"\n⚠ 重名插件 {len(dups)} 组（副本大小不一致，按 --dup-policy={args.dup_policy} 取用）：")
        for nm, paths in sorted(dups.items()):
            print(f"  {nm}")
            for f in paths:
                mark = "← 采用" if f == index[nm] else ""
                print(f"      {f.parent.name}  ({f.stat().st_size} B) {mark}")
        print("  取用方向依 MO2 惯例推断（行首＝高优先级），未在本机验证；以 MO2 左侧面板为准。")
    else:
        print("\n✓ 无内容不一致的重名插件")

    print(f"未匹配到基线的 AVIF：{len(unmatched)} 条"
          + ("（说明基线之外还有自建 AVIF，见 references/records.md 第 8 节）"
             if unmatched else "（即没有插件自建新 AVIF）"))
    return 0


# ---------------------------------------------------------------- main

def main():
    _safe_stdout()
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--game", default="SKYRIM_SE",
                        help="游戏标识，如 SKYRIM_SE / FALLOUT4 / STARFIELD（默认 SKYRIM_SE）")

    ap = argparse.ArgumentParser(
        description="读取 Bethesda 插件记录与字段（只读，不联网）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor", parents=[common], help="环境自检")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("find", parents=[common],
                       help="在模组目录中按名称或 EditorID 检索记录")
    p.add_argument("mods_root")
    p.add_argument("keywords", nargs="+")
    p.set_defaults(func=cmd_find)

    p = sub.add_parser("grep", parents=[common],
                       help="纯字节串搜索（无需 bethkit 的降级手段）")
    p.add_argument("target", help="模组目录或单个文件")
    p.add_argument("keywords", nargs="+")
    p.set_defaults(func=cmd_grep)

    p = sub.add_parser("dump", parents=[common], help="导出单条记录的全部字段")
    p.add_argument("plugin")
    p.add_argument("target", help="EditorID 或 FormID（0x 前缀）")
    p.set_defaults(func=cmd_dump)

    p = sub.add_parser("chain", parents=[common], help="还原记录的 load order 覆盖链")
    p.add_argument("plugins_txt", help="MO2 配置档的 plugins.txt")
    p.add_argument("local_id", help="本地 object_id，如 0x20000F")
    p.add_argument("--mods-root", default=None)
    p.add_argument("--signature", default=None, help="限定记录签名，如 NPC_")
    p.add_argument("--only-enabled", action="store_true",
                   help="只扫 plugins.txt 已勾选（带 *）的插件；默认按 load order 全序扫")
    p.set_defaults(func=cmd_chain)

    p = sub.add_parser("tree", parents=[common],
                       help="原版星座树的替换关系（仅 Skyrim 原版技能树）")
    p.add_argument("profile", help="MO2 配置档目录（或其中的 plugins.txt）")
    p.add_argument("--mods-root", default=None, help="省略时从配置档目录向上查找 MO2/mods")
    p.add_argument("--data-dir", default=None,
                   help="省略时从 mods 目录向上查找含 Skyrim.esm 的 Data")
    p.add_argument("--dup-policy", default="first", choices=("first", "last"),
                   help="重名插件的取用方向（默认 first＝modlist 行首）")
    p.add_argument("--only-enabled", action="store_true",
                   help="只扫 plugins.txt 已勾选（带 *）的插件；默认按 load order 全序扫")
    p.set_defaults(func=cmd_tree)

    p = sub.add_parser("save", parents=[common],
                       help="读取 Skyrim 存档（.ess）内容：info / globals / inventory / forms")
    p.add_argument("save_args", nargs="+",
                   help="透传参数，如：info <存档.ess> | globals <存档.ess> [过滤词]")
    p.set_defaults(func=cmd_save)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
