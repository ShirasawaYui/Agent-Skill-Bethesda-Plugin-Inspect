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
import sys
import time
from pathlib import Path

PLUGIN_EXT = {".esp", ".esm", ".esl"}

OPTIONAL_TOOLS = (
    ("Champollion", "champollion/Champollion.exe",
     "https://github.com/Orvid/Champollion/releases  (LGPL-3.0)"),
    ("BSA Browser CLI", "bsa-browser/bsab.exe",
     "https://github.com/AlexxEG/BSA_Browser/releases  (GPL-3.0)"),
)

INSTALL_HINT = """\
bethkit 不可用。安装方式：

  # 建隔离环境（已存在则跳过）
  <PYTHON> -m venv "C:/Users/Administrator/.workbuddy/binaries/python/envs/default"

  # 安装
  "C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" install bethkit

  # 验证
  "C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe" -c "import bethkit; print('ok')"

仓库与更新说明见 references/bethkit.md。
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

def _read_load_order(plugins_txt):
    order = []
    raw = Path(plugins_txt).read_text(encoding="utf-8-sig", errors="replace")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("*"):
            order.append(line[1:].strip())
    return order


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

    order = _read_load_order(args.plugins_txt)
    if not order:
        print("plugins.txt 中没有启用项（以 * 开头的行）。", file=sys.stderr)
        return 2

    mods_root = Path(args.mods_root) if args.mods_root else _infer_mods_root(args.plugins_txt)
    if mods_root is None or not mods_root.is_dir():
        print("无法确定 mods 目录，请用 --mods-root 指定。", file=sys.stderr)
        return 2

    index = {}
    for p in _scan_plugins(mods_root):
        index.setdefault(p.name.lower(), p)

    local_id = int(args.local_id, 16) if args.local_id.lower().startswith("0x") \
        else int(args.local_id)
    want_sig = args.signature.encode("ascii") if args.signature else None

    print(f"load order: {len(order)} 个启用插件")
    print(f"mods 目录 : {mods_root}")
    print(f"目标      : local_id={hex(local_id)}"
          f"{'  signature=' + args.signature if args.signature else ''}\n")

    t0 = time.time()
    chain = []
    missing = 0
    for pos, name in enumerate(order):
        path = index.get(name.lower())
        if path is None:
            missing += 1
            continue
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
        print(f"未找到该记录（扫描 {len(order) - missing} 个插件，耗时 {time.time() - t0:.1f}s）。")
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
    p.set_defaults(func=cmd_chain)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
