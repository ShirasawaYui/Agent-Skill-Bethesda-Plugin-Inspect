import resaver.ess.ESS;
import resaver.ess.ModelBuilder;
import resaver.ess.ChangeForm;
import resaver.ess.ChangeFormCollection;
import resaver.ess.RefID;
import resaver.ess.GlobalVariable;
import resaver.ess.Element;
import resaver.ess.ChangeFormData;
import resaver.ess.ChangeFormACHR;
import resaver.ess.ChangeFormInventoryItem;
import resaver.ProgressModel;

import java.io.PrintStream;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;

/**
 * 存档数据导出入口。
 *
 * 解析能力全部来自 ReSaver（Apache-2.0，resaver.ess 包），本类只负责取数与排版。
 *
 * 用法: SaveReader <info|globals|inventory|forms> <存档.ess> [过滤词]
 */
public class SaveReader {

    public static void main(String[] args) {
        try {
            System.setOut(new PrintStream(System.out, true, "UTF-8"));
            System.setErr(new PrintStream(System.err, true, "UTF-8"));
        } catch (Exception ignored) {
        }

        if (args.length < 2) {
            usage();
            System.exit(2);
        }

        String cmd = args[0];
        Path saveFile = Paths.get(args[1]);

        try {
            long t0 = System.currentTimeMillis();
            ESS.Result result = ESS.readESS(saveFile, new ModelBuilder(new ProgressModel(1)));
            ESS save = result.ESS;
            System.err.println("[解析耗时 " + (System.currentTimeMillis() - t0) + " ms]");

            switch (cmd) {
                case "info":
                    cmdInfo(save);
                    break;
                case "globals":
                    cmdGlobals(save, args.length > 2 ? args[2] : null);
                    break;
                case "inventory":
                    cmdInventory(save);
                    break;
                case "forms":
                    cmdForms(save);
                    break;
                default:
                    usage();
                    System.exit(2);
            }
        } catch (Throwable t) {
            System.err.println("!! 失败: " + t.getClass().getName() + ": " + t.getMessage());
            t.printStackTrace(System.err);
            System.exit(1);
        }
    }

    private static void usage() {
        System.out.println("用法: SaveReader <命令> <存档.ess> [过滤词]");
        System.out.println();
        System.out.println("  info      存档摘要（角色、等级、种族、位置、游戏日期、各部分体积）");
        System.out.println("  globals   全局变量表；可附加过滤词，只输出名字或十六进制值命中的项");
        System.out.println("  inventory 玩家背包（FormID:插件,数量）");
        System.out.println("  forms     ChangeForm 总数与按类型统计");
    }

    // ---------------------------------------------------------------- info

    private static void cmdInfo(ESS save) {
        System.out.println("========== 存档摘要 ==========");
        System.out.println(stripHtml(save.getInfo(Optional.empty())));

        System.out.println();
        System.out.println("--- 结构 ---");
        System.out.println("解压后字节 : " + save.getOriginalSize());
        System.out.println("isSkyrim   : " + save.isSkyrim());
        System.out.println("hasCosave  : " + save.hasCosave());
        System.out.println("全局变量数 : " + save.getGlobals().getVariables().size());
        System.out.println("ChangeForm : " + save.getFormIDs().length);
    }

    // ------------------------------------------------------------- globals

    private static void cmdGlobals(ESS save, String filter) {
        List<GlobalVariable> vars = save.getGlobals().getVariables();
        String needle = filter == null ? null : filter.toLowerCase();
        int shown = 0;

        System.out.println("========== 全局变量（共 " + vars.size() + " 个） ==========");
        for (GlobalVariable v : vars) {
            String line = v.toString();
            if (needle != null && !line.toLowerCase().contains(needle)) {
                continue;
            }
            System.out.println(line);
            shown++;
        }
        if (needle != null) {
            System.out.println();
            System.out.println("--- 过滤词 \"" + filter + "\" 命中 " + shown + " / " + vars.size() + " ---");
        }
    }

    // ----------------------------------------------------------- inventory

    private static void cmdInventory(ESS save) {
        System.out.println("========== 玩家背包 ==========");
        try {
            RefID playerID = save.make(0x400014);
            ChangeForm form = save.getChangeForms().getChangeForm(playerID);
            if (form == null) {
                System.out.println("(未找到玩家 ChangeForm; 该存档可能尚未生成玩家变更记录)");
                return;
            }
            ChangeFormData data = form.getData(Optional.empty(), save.getContext(), true);
            if (!(data instanceof ChangeFormACHR)) {
                System.out.println("(玩家记录类型非 ACHR: " + data.getClass().getSimpleName() + ")");
                return;
            }
            ChangeFormACHR achr = (ChangeFormACHR) data;
            Element[] inv = achr.INVENTORY;
            if (inv == null) {
                System.out.println("(背包为空)");
                return;
            }
            for (Element e : inv) {
                System.out.println("  " + stripHtml(String.valueOf(e)));
            }
            System.out.println();
            System.out.println("--- 共 " + inv.length + " 项 ---");
        } catch (Throwable t) {
            System.out.println("(读取背包失败: " + t.getClass().getSimpleName() + ": " + t.getMessage() + ")");
        }
    }

    // ---------------------------------------------------------------- forms

    private static void cmdForms(ESS save) {
        ChangeFormCollection forms = save.getChangeForms();
        Map<String, Integer> byType = new TreeMap<>();

        for (ChangeForm cf : forms) {
            try {
                byType.merge(String.valueOf(cf.getType()), 1, Integer::sum);
            } catch (Throwable ignored) {
            }
        }

        System.out.println("========== ChangeForm 统计 ==========");
        System.out.println("总数       : " + forms.size());
        System.out.println();
        System.out.println("--- 按类型 ---");
        byType.entrySet().stream()
                .sorted((a, b) -> b.getValue() - a.getValue())
                .forEach(e -> System.out.println(String.format("  %-12s %d", e.getKey(), e.getValue())));
    }

    // ----------------------------------------------------------------- misc

    private static String stripHtml(String html) {
        if (html == null) {
            return "(无)";
        }
        return html
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replaceAll("(?i)</li>", "\n")
                .replaceAll("(?i)<li>", "  - ")
                .replaceAll("(?i)<br\\s*/?>", "\n")
                .replaceAll("(?i)</h3>|</p>|</ul>|</code>", "\n")
                .replaceAll("(?i)<h3>|<p>|<ul>|<code>", "")
                .replaceAll("<[^>]+>", "")
                .replaceAll("[ \\t]+\\n", "\n")
                .replaceAll("\\n{3,}", "\n\n")
                .trim();
    }
}
