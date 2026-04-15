import argparse
import shutil
import json
import sys
from pathlib import Path


def configure_utf8_output():
    """Keep Chinese CLI output readable when launched from Windows agent shells."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def init_naruto_project(project_root):
    """
    初始化长篇火影同人的物理级持久化架构
    该脚本对应于 SKILL.md 中的 /一键木叶 命令
    """
    configure_utf8_output()
    root = Path(project_root)
    print(f"[Start] 正在为『Naruto Author AI』初始化长篇架构于: {root.absolute()}")

    # 1. 创建绝对物理目录结构
    dirs_to_create = [
        "00_memory",
        "naruto_fanfic_db",  # 替换原本的 02_knowledge_base
        "03_manuscript",
        "04_editing/gate_artifacts",
        ".claude/commands"
    ]

    for d in dirs_to_create:
        dir_path = root / d
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"   [+] 创建目录: {d}/")

    # 2. 从 templates/ 复制核心长篇状态文件
    # 获取当前 skill 安装路径下的 templates 目录
    # 注意：这里的绝对路径可能因环境而异，我们通过当前脚本推导
    skill_dir = Path(__file__).parent.parent
    templates_dir = skill_dir / "templates"

    if templates_dir.exists():
        # 复制 00_memory 文件
        for tmpl in ["novel_plan.md", "novel_state.md", "story_graph.json", "outline_changelog.md"]:
            src = templates_dir / tmpl
            dst = root / "00_memory" / tmpl
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                print(f"   [+] 复制模板文件: 00_memory/{tmpl}")
            else:
                print(f"   [!] 模板文件已存在或源文件丢失: 00_memory/{tmpl}")

        agents_src = templates_dir / "AGENTS.md"
        agents_dst = root / "AGENTS.md"
        if agents_src.exists() and not agents_dst.exists():
            shutil.copy2(agents_src, agents_dst)
            print("   [+] 复制通用代理说明: AGENTS.md")
        elif agents_dst.exists():
            print("   [!] AGENTS.md 已存在，跳过复制")

    # 3. 如果需要，初始化空数据库占位符 (现在移除了对 02_knowledge_base 的依赖，改用 naruto_fanfic_db)
    # 此处假设 naruto_fanfic_db 已经由 Codex 获取并存在于 skill 内部
    skill_db_dir = skill_dir / "naruto_fanfic_db"
    dest_db_dir = root / "naruto_fanfic_db"

    if skill_db_dir.exists():
        # 如果 skill 内部带了数据库，将其复制到用户项目目录下（如果不存在则复制，避免覆盖用户修改）
        for item in skill_db_dir.iterdir():
            s = item
            d = dest_db_dir / item.name
            if s.is_dir():
                # 仅当目标目录不存在时复制，或者复制内部缺失文件，但 shutil.copytree(dirs_exist_ok=True) 依然会覆盖同名文件
                # 为安全起见，只对不存在的 db 文件进行 copy
                if not d.exists():
                    shutil.copytree(s, d)
            else:
                if not d.exists():
                    shutil.copy2(s, d)
        print(f"   [+] 成功从 Skill 内核复制原著数据库到: naruto_fanfic_db/")
    else:
        # 如果没有自带，则生成空的占位符
        kb_files = ["characters.json", "jutsus.json", "relations.json", "canon_plot.json", "pre_main_timeline.json"]
        for kb in kb_files:
            dst = dest_db_dir / kb
            if not dst.exists():
                with open(dst, 'w', encoding='utf-8') as f:
                    json.dump({}, f)
                print(f"   [+] 创建空的知识库文件: naruto_fanfic_db/{kb}")

    # 4. 复制 .prompt 命令文件到项目 .claude/commands 目录
    commands_dir = skill_dir / ".claude" / "commands"
    dest_commands_dir = root / ".claude" / "commands"
    if commands_dir.exists():
        for prompt_file in commands_dir.glob("*.prompt"):
            dst = dest_commands_dir / prompt_file.name
            if not dst.exists():
                shutil.copy2(prompt_file, dst)
                print(f"   [+] 复制命令文件: .claude/commands/{prompt_file.name}")

    print("\n[Done] 初始化完成！")
    print("[Next] 请用中文补全开书五要素：")
    print("1. 时间线切入点：例如第三次忍界大战 / 九尾之乱 / 疾风传初期")
    print("2. 主角阵营与身份：例如木叶平民 / 宇智波幸存者 / 雨忍村孤儿")
    print("3. 金手指限度：能力边界、代价、冷却和成长速度")
    print("4. 蝴蝶效应核心目标：例如救水门 / 阻止灭族 / 改变长门信念")
    print("5. 期望文风：热血羁绊 / 黑暗冷酷 / 腹黑苟道 / 轻松吐槽")
    print("[Tip] 收到五要素后，再使用 /忍界推演 或 /构建人物卡。")

def build_parser():
    parser = argparse.ArgumentParser(description="初始化 Naruto Author 长篇项目骨架")
    parser.add_argument("--root", default=".", help="要初始化的项目根目录，默认当前目录")
    return parser


if __name__ == "__main__":
    configure_utf8_output()
    args = build_parser().parse_args()
    init_naruto_project(args.root)
