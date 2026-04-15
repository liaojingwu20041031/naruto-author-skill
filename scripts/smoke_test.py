import importlib.util
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path


sys.dont_write_bytecode = True


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
DB_DIR = SKILL_ROOT / "naruto_fanfic_db"


def load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载模块: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(condition, message: str):
    if not condition:
        raise AssertionError(message)


def remove_tree_best_effort(path: Path):
    if not path.exists():
        return

    def retry_with_write_permission(func, raw_path, exc_info):
        os.chmod(raw_path, 0o700)
        func(raw_path)

    try:
        shutil.rmtree(path, onerror=retry_with_write_permission)
    except PermissionError as exc:
        print(f"[WARN] 临时目录清理受限，稍后可手动删除: {path} ({exc})")


def validate_frontmatter():
    skill_md = SKILL_ROOT / "SKILL.md"
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert_true(match is not None, "SKILL.md 缺少 YAML frontmatter")

    fields = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip():
            continue
        key, _, value = raw_line.partition(":")
        fields[key.strip()] = value.strip()

    skill_name = fields.get("name")
    valid_root_names = {skill_name, f"{skill_name}-skill"}
    assert_true(SKILL_ROOT.name in valid_root_names, "SKILL.md name 必须与目录名一致，或仓库名使用 <skill-name>-skill")
    assert_true(bool(fields.get("description")), "SKILL.md description 不能为空")
    assert_true(set(fields) == {"name", "description"}, "frontmatter 只应包含 name 和 description")


def validate_agent_neutral_usage():
    skill_md = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    agents_template = SKILL_ROOT / "templates" / "AGENTS.md"
    assert_true(agents_template.exists(), "必须提供 AGENTS.md 模板，方便 Codex 使用")
    agents_text = agents_template.read_text(encoding="utf-8")
    assert_true("Codex" in agents_text and "Claude Code" in agents_text, "AGENTS.md 模板必须说明 Claude/Codex 通用")
    assert_true("query_db.py mentions" in agents_text, "AGENTS.md 模板必须说明资料库实体命中命令")
    assert_true("orchestrator.py --root . prompt" in agents_text, "AGENTS.md 模板必须说明章节写作包命令")
    assert_true("outline_manager.py" in agents_text, "AGENTS.md 模板必须说明正式改纲流程")
    assert_true("DeepSeek" in agents_text, "AGENTS.md 模板必须说明暗部审核由 DeepSeek 优先执行")
    assert_true("Claude Code / Codex" in skill_md, "SKILL.md 必须显式说明 Claude Code / Codex 通用")
    assert_true("DeepSeek 暗部审核官" in skill_md, "SKILL.md 必须说明 DeepSeek 暗部审核官职责")
    assert_true("/打磨大纲" in skill_md and "/改纲推演" in skill_md, "SKILL.md 必须登记正式改纲命令")
    for phrase in ["时间线-势力-场景链", "原著锚点时间轴", "反派响应树", "场景链优先于章号", "小篇章纲"]:
        assert_true(phrase in skill_md, f"SKILL.md 缺少长篇大纲架构说明: {phrase}")
        assert_true(phrase in agents_text, f"AGENTS.md 模板缺少长篇大纲架构说明: {phrase}")
    for stale_phrase in ["每 3-4 章至少", "单章推进配额", "第1-20章", "第21-50章"]:
        assert_true(stale_phrase not in skill_md, f"SKILL.md 不应保留固定章节配额: {stale_phrase}")
    for phrase in ["帮我打磨大纲", "确认采用这个改纲", "查看剧情债", "继续写下一章", "查一下神威", "看看有没有毒点"]:
        assert_true(phrase in skill_md, f"SKILL.md 缺少自然语言触发示例: {phrase}")
        assert_true(phrase in agents_text, f"AGENTS.md 模板缺少自然语言触发示例: {phrase}")

    audit_command = (SKILL_ROOT / ".claude" / "commands" / "暗部审核.prompt").read_text(encoding="utf-8")
    assert_true("DeepSeek" in audit_command, "/暗部审核 命令必须 DeepSeek 优先")
    assert_true("Codex 代理" not in audit_command, "/暗部审核 命令不应继续写成 Codex 代理")


def validate_outline_workflow_assets():
    outline_script = SCRIPTS_DIR / "outline_manager.py"
    assert_true(outline_script.exists(), "缺少 outline_manager.py")
    assert_true((SCRIPTS_DIR / "revision_loop.py").exists(), "缺少 revision_loop.py")
    assert_true((SKILL_ROOT / "templates" / "outline_changelog.md").exists(), "缺少 outline_changelog.md 模板")
    assert_true((SKILL_ROOT / ".claude" / "commands" / "打磨大纲.prompt").exists(), "缺少 /打磨大纲 命令")
    assert_true((SKILL_ROOT / ".claude" / "commands" / "改纲推演.prompt").exists(), "缺少 /改纲推演 命令")

    story_graph_template = json.loads((SKILL_ROOT / "templates" / "story_graph.json").read_text(encoding="utf-8"))
    assert_true("outline_versions" in story_graph_template, "story_graph 模板必须包含 outline_versions")
    assert_true("retcon_log" in story_graph_template, "story_graph 模板必须包含 retcon_log")
    assert_true("downstream_obligations" in story_graph_template, "story_graph 模板必须包含 downstream_obligations")
    assert_true("long_outline" in story_graph_template, "story_graph 模板必须包含 long_outline 长篇大纲结构")
    long_outline = story_graph_template["long_outline"]
    for key in [
        "premise_summaries",
        "canon_anchor_timeline",
        "butterfly_fermentation",
        "faction_response_tree",
        "volume_outlines",
        "arc_outlines",
        "scene_chains",
        "serialization_markers",
    ]:
        assert_true(key in long_outline, f"long_outline 缺少字段: {key}")

    novel_plan_template = (SKILL_ROOT / "templates" / "novel_plan.md").read_text(encoding="utf-8")
    for phrase in ["一句话主线", "原著锚点时间轴", "势力博弈图与反派响应树", "小篇章纲", "场景链 / 幕纲", "连载节奏标记"]:
        assert_true(phrase in novel_plan_template, f"novel_plan 模板缺少八层大纲字段: {phrase}")
    for stale_phrase in ["第1-20章", "第21-50章", "关键剧情节点 (Beats)"]:
        assert_true(stale_phrase not in novel_plan_template, f"novel_plan 模板不应保留旧章号锚点: {stale_phrase}")

    outline_prompt = (SKILL_ROOT / "prompts" / "outline-gen.md").read_text(encoding="utf-8")
    for phrase in ["一句话主线", "200-300 字故事摘要", "时间轴总表", "反派响应树", "场景链优先于章号", "8-15 个场景链"]:
        assert_true(phrase in outline_prompt, f"outline-gen.md 缺少新大纲结构: {phrase}")
    for stale_phrase in ["三卷连载大纲", "每个关键章节必须", "关键剧情节点 (Beats)"]:
        assert_true(stale_phrase not in outline_prompt, f"outline-gen.md 不应保留旧卷节点模板: {stale_phrase}")


def validate_database_json():
    expected = {
        "characters.json",
        "jutsus.json",
        "canon_plot.json",
        "pre_main_timeline.json",
        "world_background.json",
        "relations.json",
        "tailed_beasts.json",
        "artifacts.json",
        "organizations.json",
    }
    existing = {path.name for path in DB_DIR.glob("*.json")}
    assert_true(expected.issubset(existing), f"资料库缺少文件: {sorted(expected - existing)}")

    for path in DB_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert_true(isinstance(data, dict), f"{path.name} 顶层必须是 object")


def get_record_ids(data, collection_name):
    records = data.get(collection_name, [])
    assert_true(isinstance(records, list), f"{collection_name} 必须是 list")
    return {record.get("id") for record in records if isinstance(record, dict)}


def validate_database_enrichment():
    characters = json.loads((DB_DIR / "characters.json").read_text(encoding="utf-8"))
    jutsus = json.loads((DB_DIR / "jutsus.json").read_text(encoding="utf-8"))
    organizations = json.loads((DB_DIR / "organizations.json").read_text(encoding="utf-8"))
    artifacts = json.loads((DB_DIR / "artifacts.json").read_text(encoding="utf-8"))
    world_background = json.loads((DB_DIR / "world_background.json").read_text(encoding="utf-8"))

    character_ids = get_record_ids(characters, "characters")
    assert_true({"chiyo", "mifune", "gamabunta"}.issubset(character_ids), "人物库缺少补充角色")

    jutsu_ids = get_record_ids(jutsus, "jutsus")
    assert_true({"summoning_jutsu", "medical_ninjutsu", "amaterasu"}.issubset(jutsu_ids), "忍术库缺少补充能力")

    organization_ids = get_record_ids(organizations, "organizations")
    assert_true({"team_8", "legendary_sannin", "seven_ninja_swordsmen"}.issubset(organization_ids), "组织库缺少补充组织")

    tool_ids = get_record_ids(artifacts, "standard_tools")
    assert_true({"kunai", "explosive_tag", "forehead_protector"}.issubset(tool_ids), "物品库缺少标准忍具")

    lore_ids = get_record_ids(world_background, "lore_entries")
    assert_true(
        {"mission_rank_system", "chakra_core_mechanics", "kekkei_genkai_system"}.issubset(lore_ids),
        "世界观库缺少补充规则",
    )


def validate_query_script():
    query_db = load_module("query_db", SCRIPTS_DIR / "query_db.py")
    db = query_db.FanficDBQuerier(DB_DIR)

    naruto = db.get_character("鸣人")
    assert_true(naruto and naruto["id"] == "uzumaki_naruto", "人物查询失败: 鸣人")

    rasengan = db.get_jutsu("螺旋丸")
    assert_true(rasengan and rasengan["id"] == "rasengan", "忍术查询失败: 螺旋丸")

    risk_report = db.check_continuity_risks("佐助")
    assert_true("宇智波灭族真相" in risk_report, "风险报告缺少秘密边界")

    search_results = db.search("神威", limit=5)
    assert_true(isinstance(search_results, list), "search 必须返回 list")

    mention_results = db.mentioned_records("鸣人在木叶试图学习螺旋丸，却撞见神威痕迹。", limit=8)
    mention_ids = {item["id"] for item in mention_results}
    assert_true("uzumaki_naruto" in mention_ids, "mentions 必须命中鸣人")
    assert_true("rasengan" in mention_ids, "mentions 必须命中螺旋丸")
    assert_true("kamui" in mention_ids, "mentions 必须命中神威")
    assert_true("konohagakure" in mention_ids, "mentions 必须命中木叶")

    enriched_mentions = db.mentioned_records("第八班在任务中遇见通灵兽蛤蟆文太，又用起爆符拖住敌人。", limit=12)
    enriched_ids = {item["id"] for item in enriched_mentions}
    assert_true("team_8" in enriched_ids, "mentions 必须命中第八班")
    assert_true("gamabunta" in enriched_ids, "mentions 必须命中蛤蟆文太")
    assert_true("explosive_tag" in enriched_ids, "mentions 必须命中起爆符")


def validate_orchestrator_and_init():
    orchestrator_mod = load_module("orchestrator", SCRIPTS_DIR / "orchestrator.py")
    init_mod = load_module("init_project", SCRIPTS_DIR / "init_project.py")
    revision_loop = load_module("revision_loop", SCRIPTS_DIR / "revision_loop.py")
    workspace_tmp = SKILL_ROOT / ".tmp_naruto_author_smoke"
    workspace_tmp.mkdir(exist_ok=True)

    project_root = workspace_tmp / f"naruto_author_{uuid.uuid4().hex}"
    try:
        project_root.mkdir(parents=True, exist_ok=False)
        init_mod.init_naruto_project(project_root)
        assert_true((project_root / "00_memory" / "novel_plan.md").exists(), "初始化未创建 novel_plan.md")
        assert_true((project_root / "00_memory" / "outline_changelog.md").exists(), "初始化未创建 outline_changelog.md")
        assert_true((project_root / "naruto_fanfic_db" / "characters.json").exists(), "初始化未复制资料库")
        assert_true((project_root / ".claude" / "commands" / "一键木叶.prompt").exists(), "初始化未复制命令文件")
        assert_true((project_root / ".claude" / "commands" / "打磨大纲.prompt").exists(), "初始化未复制打磨大纲命令")
        assert_true((project_root / "AGENTS.md").exists(), "初始化未复制 Codex 通用 AGENTS.md")

        outline_manager = load_module("outline_manager", SCRIPTS_DIR / "outline_manager.py")
        outline_manager.ensure_outline_files(project_root)
        proposal = outline_manager.create_outline_proposal(
            project_root,
            request_text="人工想让纲手提前进入第一卷，但不能破坏三忍成长线。",
            chapter=3,
        )
        assert_true(proposal.exists(), "改纲提案包未生成")
        proposal_text = proposal.read_text(encoding="utf-8")
        assert_true("人工确认" in proposal_text and "下游剧情债" in proposal_text, "改纲提案包缺少人工确认/剧情债检查")
        for phrase in ["八层长篇大纲架构", "原著锚点时间轴", "蝴蝶效应传播图", "势力博弈图与反派响应树", "场景链 / 幕纲", "场景链优先于章号"]:
            assert_true(phrase in proposal_text, f"改纲提案包缺少新大纲架构字段: {phrase}")

        outline_manager.record_outline_revision(
            project_root,
            summary="测试记录：纲手提前进入第一卷",
            request_text="人工确认该改动仅作为测试",
            affected_canon_ids=["canon_002_chunin_exam"],
            affected_character_ids=["tsunade"],
            obligations=["第 4 章必须承接纲手对牢潘的第一印象。"],
            status="accepted",
        )
        changelog_text = (project_root / "00_memory" / "outline_changelog.md").read_text(encoding="utf-8")
        assert_true("测试记录：纲手提前进入第一卷" in changelog_text, "改纲记录未写入 outline_changelog.md")
        graph = json.loads((project_root / "00_memory" / "story_graph.json").read_text(encoding="utf-8"))
        assert_true(graph.get("outline_versions"), "story_graph 未记录 outline_versions")
        assert_true(graph.get("retcon_log"), "story_graph 未记录 retcon_log")
        assert_true(graph.get("downstream_obligations"), "story_graph 未记录 downstream_obligations")
        obligation = graph["downstream_obligations"][0]
        assert_true("target_volume" in obligation, "剧情债必须记录 target_volume 字段")
        assert_true("active_from_chapter" in obligation, "剧情债必须记录 active_from_chapter 字段")
        assert_true("due_chapter" in obligation, "剧情债必须记录 due_chapter 字段")

        orchestrator = orchestrator_mod.NarutoAuthorOrchestrator(project_root)
        prompt = orchestrator.prepare_chapter_prompt(
            "测试 Beat：主角在木叶听见鸣人提到螺旋丸，又发现神威留下的空间扭曲痕迹。",
            chapter_num=3,
        )
        assert_true("测试 Beat" in prompt and "忍界铁律" in prompt, "写作包裹内容不完整")
        assert_true("Claude Code / Codex" in prompt, "写作包裹必须对 Claude Code / Codex 通用")
        assert_true("大纲版本与下游剧情债" in prompt, "写作包裹必须包含大纲版本与剧情债检查")
        assert_true("当前必须处理剧情债" in prompt or "当前章节没有必须处理的剧情债" in prompt, "写作包裹必须区分当前剧情债")
        assert_true("未来/未到期" in prompt or "未归档剧情债" in prompt, "写作包裹必须说明未来/未归档剧情债不应提前兑现")
        assert_true("4000-5000" in prompt, "写作包裹必须约束单章正文 4000-5000 字")
        assert_true("情绪弧线" in prompt, "写作包裹必须包含情绪弧线约束")
        assert_true("场景链约束" in prompt and "前一场的结果成为后一场的动机" in prompt, "写作包裹必须包含场景链因果约束")
        assert_true("轻松快乐向" in prompt, "写作包裹必须包含本书轻松向风格定位")
        assert_true("少量原著口头禅" in prompt, "写作包裹必须允许合理口头禅")
        assert_true("不要机械套公式" in prompt, "写作包裹必须避免机械情绪规则")
        assert_true("无新事件支撑" in prompt, "写作包裹必须限制情绪空转")
        assert_true("制度梗" in prompt, "写作包裹必须允许轻松向制度梗")
        assert_true("500 字内不得超过 2 次" not in prompt, "写作包裹不应继续使用机械词频死线")
        assert_true("资料库命中锚点" in prompt, "写作包裹必须自动注入资料库命中锚点")
        assert_true("uzumaki_naruto" in prompt, "资料库命中锚点必须包含鸣人记录")
        assert_true("rasengan" in prompt, "资料库命中锚点必须包含螺旋丸记录")
        assert_true("kamui" in prompt, "资料库命中锚点必须包含神威记录")
        assert_true("konohagakure" in prompt, "资料库命中锚点必须包含木叶记录")

        old_key = os.environ.pop("DEEPSEEK_API_KEY", None)
        try:
            dotenv_key = "dotenv_test_key"
            (project_root / ".env").write_text(f'DEEPSEEK_API_KEY="{dotenv_key}"\n', encoding="utf-8")
            assert_true(orchestrator.load_deepseek_api_key() == dotenv_key, ".env 中的 DEEPSEEK_API_KEY 未被加载")
        finally:
            if old_key is not None:
                os.environ["DEEPSEEK_API_KEY"] = old_key
            else:
                os.environ.pop("DEEPSEEK_API_KEY", None)

        audit = orchestrator.prepare_deepseek_audit_prompt("测试正文 dattebayo", chapter_num=3)
        gate_dir = project_root / "04_editing" / "gate_artifacts"
        audit_file = gate_dir / "deepseek_audit_payload_chapter_3.md"
        legacy_audit_file = gate_dir / "audit_chapter_3.md"
        assert_true(audit_file.exists(), "DeepSeek 审核投喂包未写入文件")
        assert_true(legacy_audit_file.exists(), "旧审核入口兼容文件未写入")
        for phrase in ["DeepSeek 暗部审核官", "毒点清单", "资料库一致性", "情绪呈现", "灰区可修", "少量原著口头禅", "4000-5000", "dattebayo"]:
            assert_true(phrase in audit, f"DeepSeek 审核包缺少关键约束: {phrase}")

        prompt_only_result = orchestrator.run_deepseek_audit("测试正文 dattebayo", chapter_num=4, prompt_only=True)
        assert_true(prompt_only_result["status"] == "prompt_only", "prompt-only 审核模式状态错误")
        assert_true(prompt_only_result["payload_file"].exists(), "prompt-only 未生成 DeepSeek 审核投喂包")

        state, allowed = revision_loop.bump_revision(project_root, 3, "第一次自动修稿")
        assert_true(allowed and state["auto_revision_count"] == 1, "第一次自动修稿计数失败")
        state, allowed = revision_loop.bump_revision(project_root, 3, "第二次自动修稿")
        assert_true(allowed and state["auto_revision_count"] == 2, "第二次自动修稿计数失败")
        state, allowed = revision_loop.bump_revision(project_root, 3, "第三次应阻断")
        assert_true(not allowed and state["status"] == "blocked", "超过两次自动修稿必须阻断")
    finally:
        remove_tree_best_effort(project_root)
        try:
            workspace_tmp.rmdir()
        except OSError:
            pass


def validate_no_hardcoded_secrets():
    for path in [SCRIPTS_DIR / "orchestrator.py", SKILL_ROOT / "SKILL.md"]:
        text = path.read_text(encoding="utf-8")
        assert_true("sk-" not in text, f"疑似硬编码密钥: {path.relative_to(SKILL_ROOT)}")


def main():
    checks = [
        ("frontmatter", validate_frontmatter),
        ("agent-neutral usage", validate_agent_neutral_usage),
        ("outline workflow assets", validate_outline_workflow_assets),
        ("database json", validate_database_json),
        ("database enrichment", validate_database_enrichment),
        ("query script", validate_query_script),
        ("orchestrator/init", validate_orchestrator_and_init),
        ("no hardcoded secrets", validate_no_hardcoded_secrets),
    ]

    for name, check in checks:
        check()
        print(f"[OK] {name}")

    print("[PASS] naruto-author skill smoke test passed")


if __name__ == "__main__":
    main()
