import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def read_text_arg(text: str | None = None, text_file: str | None = None) -> str:
    if text_file:
        return Path(text_file).read_text(encoding="utf-8")
    if text:
        return text
    raise ValueError("需要提供文本或文本文件")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_optional(path: Path, max_chars: int = 16000) -> str:
    if not path.exists():
        return "【文件不存在】"
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n【已截断，完整内容请读取原文件】"
    return text


OUTLINE_ARCHITECTURE_REQUIREMENTS = """## 必须采用的八层长篇大纲架构

提案不是卷级宣传提纲，必须按“摘要 -> 时间线 -> 势力 -> 卷纲 -> 小篇章 -> 场景链 -> 连载节奏”的顺序展开。

### 第 1 层：核心故事摘要
- 一句话主线：主角是谁、何时切入、为了什么、对抗谁、最终改变什么。
- 50 字摘要：只写主线驱动力。
- 200-300 字故事摘要：交代背景、主角限制、主要对抗、结局方向，不写枝叶。
- 最终主题句：本书最终要证明或反驳的核心命题。

### 第 2 层：原著切入与变数定义
- 精确切入节点：落到原著锚点或木叶纪年。
- 第一处违背原著的关键选择。
- 主角初始优势、限制、代价和最怕暴露的秘密。

### 第 3 层：原著锚点时间轴
- 至少列出与本次改纲有关的原著锚点，必要时扩展到 15-30 个。
- 每个锚点必须写：原著事件、主角知道什么、能做什么、实际做什么、没来得及做什么、世界线偏移结果。
- 若提前或推迟原著节点，必须说明原因和后果。

### 第 4 层：蝴蝶效应传播图
每个重大改动必须写：
- 直接结果、延迟结果、发酵期。
- 谁受益、谁受损、谁起疑、谁误判、谁修正计划。
- 木叶反应、晓组织反应、外村反应、反派修正方案。

### 第 5 层：势力博弈图与反派响应树
至少覆盖木叶高层、宇智波、晓组织、黑绝/带土/斑、大蛇丸、相关外村。每个势力必须写：
- 当前目标、信息来源、误判、真实判断、战术变化。
- 最早察觉者、最快反应者、最可能误判者、最危险反制手段。
- 若反派智商在线，下一步最合理行动。

### 第 6 层：三卷总纲
每卷必须写：
- 卷名、卷主题、卷主线问题、卷目标、卷对手/卷障碍。
- 卷中段误判、卷中点逆转、卷末代价、卷后余波。
- 3-5 个小篇章，不得只列 3 个节点。

### 第 7 层：小篇章纲
每个小篇章必须写：
- 起点状态、当段目标、阻碍、升级冲突、中点反转、关系变化、阶段性得失、结束状态、收尾钩子。
- 建议 3-8 章弹性窗口，由事件密度、战斗长度和关系戏密度决定，不写死章号。

### 第 8 层：场景链 / 幕纲与连载节奏
- 每个关键小篇章至少展开 8-15 个场景链样例。
- 每场必须写：场景目的、出场人物、地点/时段、行动、直接冲突、结果、下一场钩子。
- 情绪链必须嵌入场景字段：触发事件、外显反应、即时决定、结果余波、是否需要余震场景。
- 每个小篇章标注：开局钩子、中段黏性点、小高潮、误导/反转、爆点、伏笔、追更钩子、下一段最想看的问题。

### 硬约束
- 场景链优先于章号。章节只是发布包装，不能代替剧情骨架。
- 禁止“第 N 章必须发生 X”的机械配额；只能用阶段性篇章窗口约束功能。
- 前一场的结果必须成为后一场的动机、压力或误判来源。
- 改纲方案必须列出失效原著锚点、人物动机变化、秘密知情范围变化和下游剧情债。
"""


def ensure_outline_changelog(root: Path) -> Path:
    path = root / "00_memory" / "outline_changelog.md"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "# 大纲打磨与改纲记录\n\n"
            "本文件只记录已经人工确认或明确驳回的大纲改动。AI 可以提出方案，但不得把未确认方案写成事实。\n\n"
            "## 记录格式\n\n"
            "- **版本 ID**：outline_rev_YYYYMMDD_HHMMSS\n"
            "- **状态**：draft / accepted / rejected / superseded\n"
            "- **改动摘要**：\n"
            "- **人工确认**：\n"
            "- **影响范围**：人物、组织、原著锚点、势力响应、小篇章、场景链、伏笔\n"
            "- **下游剧情债**：后续必须偿还的事件、情绪余波、设定解释或反派反制\n\n",
            encoding="utf-8",
        )
    return path


def ensure_story_graph_outline_fields(root: Path) -> Path:
    path = root / "00_memory" / "story_graph.json"
    graph = read_json(path)
    meta = graph.setdefault("meta", {})
    meta.setdefault("current_outline_version", "outline_v0")
    meta.setdefault("outline_revision_count", 0)
    graph.setdefault(
        "outline_versions",
        [
            {
                "id": "outline_v0",
                "status": "baseline",
                "created_at": "",
                "summary": "初始大纲版本",
                "source": "00_memory/novel_plan.md",
                "artifact": None,
            }
        ],
    )
    graph.setdefault("retcon_log", [])
    graph.setdefault("downstream_obligations", [])
    long_outline = graph.setdefault("long_outline", {})
    long_outline.setdefault(
        "premise_summaries",
        {
            "one_sentence": "",
            "fifty_characters": "",
            "two_hundred_to_three_hundred_characters": "",
            "theme_statement": "",
        },
    )
    long_outline.setdefault("canon_anchor_timeline", [])
    long_outline.setdefault("protagonist_intervention_timeline", [])
    long_outline.setdefault("butterfly_fermentation", [])
    long_outline.setdefault("faction_response_tree", [])
    long_outline.setdefault("volume_outlines", [])
    long_outline.setdefault("arc_outlines", [])
    long_outline.setdefault("scene_chains", [])
    long_outline.setdefault("serialization_markers", [])
    write_json(path, graph)
    return path


def ensure_outline_files(project_root: str | Path) -> None:
    root = Path(project_root).resolve()
    (root / "04_editing" / "gate_artifacts").mkdir(parents=True, exist_ok=True)
    ensure_outline_changelog(root)
    ensure_story_graph_outline_fields(root)


def collect_outline_context(root: Path) -> dict[str, str]:
    return {
        "novel_plan": read_optional(root / "00_memory" / "novel_plan.md"),
        "novel_state": read_optional(root / "00_memory" / "novel_state.md"),
        "story_graph": read_optional(root / "00_memory" / "story_graph.json"),
        "outline_changelog": read_optional(root / "00_memory" / "outline_changelog.md"),
    }


def create_outline_proposal(
    project_root: str | Path,
    request_text: str,
    chapter: int | None = None,
    revision_id: str | None = None,
    out_path: str | Path | None = None,
) -> Path:
    root = Path(project_root).resolve()
    ensure_outline_files(root)
    revision_id = revision_id or f"outline_rev_{now_id()}"
    out = Path(out_path) if out_path else root / "04_editing" / "gate_artifacts" / f"{revision_id}_proposal.md"
    if not out.is_absolute():
        out = root / out
    context = collect_outline_context(root)

    chapter_text = str(chapter) if chapter is not None else "未指定"
    content = f"""# 大纲打磨提案包

- 版本 ID：{revision_id}
- 目标章节/阶段：{chapter_text}
- 状态：draft

## 人工改纲诉求

{request_text.strip()}

## 必须输出的改纲方案

请先产出“方案”，不要直接覆盖 `00_memory/novel_plan.md` 或 `00_memory/story_graph.json`。

{OUTLINE_ARCHITECTURE_REQUIREMENTS}

## 方案评审与人工确认项

必须额外包含：
- 改动摘要。
- 为什么要改。
- 不改会有什么长篇风险。
- 影响范围：人物、组织、原著锚点、伏笔、小篇章、场景链。
- 与 `naruto_fanfic_db` 冲突点。
- 下游剧情债：必须写明目标卷、目标阶段、起始章/截止章、是否硬门禁；未指定范围的剧情债不得作为当前章节打回理由。
- 至少 2 个替代方案。
- 推荐方案。
- 人工确认清单。

## 人工确认门槛

- 人工确认前，任何方案都只能停留在 `04_editing/gate_artifacts/`。
- 人工确认后，才允许修改 `00_memory/novel_plan.md`、`00_memory/story_graph.json` 和 `00_memory/novel_state.md`。
- 修改完成后，必须运行 `outline_manager.py record` 写入 `00_memory/outline_changelog.md`。
- 记录剧情债时必须用 `--target-volume`、`--active-from-chapter` 或 `--due-chapter` 标注适用范围；第二卷内容不得催第一卷兑现。

## 当前 novel_plan.md

```markdown
{context["novel_plan"]}
```

## 当前 novel_state.md

```markdown
{context["novel_state"]}
```

## 当前 story_graph.json

```json
{context["story_graph"]}
```

## 当前 outline_changelog.md

```markdown
{context["outline_changelog"]}
```
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out


def append_changelog(
    changelog_path: Path,
    revision_id: str,
    status: str,
    summary: str,
    request_text: str,
    affected_canon_ids: list[str],
    affected_character_ids: list[str],
    obligations: list[str],
    artifact: str | None,
    obligation_scope: dict[str, Any] | None = None,
) -> None:
    obligation_scope = obligation_scope or {}
    lines = [
        f"\n## {revision_id}",
        f"- **状态**：{status}",
        f"- **记录时间**：{datetime.now().isoformat(timespec='seconds')}",
        f"- **改动摘要**：{summary}",
        f"- **人工确认**：{request_text}",
        f"- **影响原著锚点**：{', '.join(affected_canon_ids) if affected_canon_ids else '无'}",
        f"- **影响人物**：{', '.join(affected_character_ids) if affected_character_ids else '无'}",
        f"- **记录产物**：{artifact or '无'}",
        "- **剧情债适用范围**："
        f"目标卷={obligation_scope.get('target_volume') or '未指定'}；"
        f"目标阶段={obligation_scope.get('target_stage') or '未指定'}；"
        f"起始章={obligation_scope.get('active_from_chapter') or '未指定'}；"
        f"截止章={obligation_scope.get('due_chapter') or '未指定'}；"
        f"是否当前硬约束={obligation_scope.get('blocking', False)}",
        "- **下游剧情债**：",
    ]
    if obligations:
        lines.extend(f"  - {item}" for item in obligations)
    else:
        lines.append("  - 无")
    lines.append("")
    with changelog_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


def record_outline_revision(
    project_root: str | Path,
    summary: str,
    request_text: str,
    affected_canon_ids: list[str] | None = None,
    affected_character_ids: list[str] | None = None,
    obligations: list[str] | None = None,
    status: str = "accepted",
    revision_id: str | None = None,
    artifact: str | None = None,
    target_volume: str | None = None,
    target_stage: str | None = None,
    active_from_chapter: int | None = None,
    due_chapter: int | None = None,
    priority: str = "normal",
    blocking: bool = False,
) -> str:
    root = Path(project_root).resolve()
    ensure_outline_files(root)
    revision_id = revision_id or f"outline_rev_{now_id()}"
    affected_canon_ids = affected_canon_ids or []
    affected_character_ids = affected_character_ids or []
    obligations = obligations or []
    obligation_scope = {
        "target_volume": target_volume,
        "target_stage": target_stage,
        "active_from_chapter": active_from_chapter,
        "due_chapter": due_chapter,
        "priority": priority,
        "blocking": blocking,
    }

    graph_path = root / "00_memory" / "story_graph.json"
    graph = read_json(graph_path)
    meta = graph.setdefault("meta", {})
    meta["current_outline_version"] = revision_id
    meta["outline_revision_count"] = int(meta.get("outline_revision_count") or 0) + 1

    version_entry = {
        "id": revision_id,
        "status": status,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "summary": summary,
        "request": request_text,
        "affected_canon_ids": affected_canon_ids,
        "affected_character_ids": affected_character_ids,
        "artifact": artifact,
    }
    graph.setdefault("outline_versions", []).append(version_entry)
    graph.setdefault("retcon_log", []).append(
        {
            "id": f"retcon_{revision_id}",
            "outline_revision_id": revision_id,
            "status": status,
            "summary": summary,
            "affected_canon_ids": affected_canon_ids,
            "affected_character_ids": affected_character_ids,
        }
    )

    downstream = graph.setdefault("downstream_obligations", [])
    for index, obligation in enumerate(obligations, start=1):
        downstream.append(
            {
                "id": f"{revision_id}_obligation_{index}",
                "source_outline_revision_id": revision_id,
                "description": obligation,
                "status": "open",
                "target_volume": target_volume,
                "target_stage": target_stage,
                "active_from_chapter": active_from_chapter,
                "due_chapter": due_chapter,
                "priority": priority,
                "blocking": blocking,
                "scope_note": "只有到达 target_volume/active_from_chapter/due_chapter 后才作为当前硬约束；未到期前不得强行提前兑现。",
            }
        )
    write_json(graph_path, graph)

    changelog_path = ensure_outline_changelog(root)
    append_changelog(
        changelog_path,
        revision_id,
        status,
        summary,
        request_text,
        affected_canon_ids,
        affected_character_ids,
        obligations,
        artifact,
        obligation_scope,
    )
    return revision_id


def parse_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def classify_obligations(obligations: list[dict[str, Any]], chapter: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    active: list[dict[str, Any]] = []
    upcoming: list[dict[str, Any]] = []
    unscoped: list[dict[str, Any]] = []

    for item in obligations:
        if not isinstance(item, dict):
            continue
        status = item.get("status", "open")
        if status == "closed":
            continue
        if status in {"deferred", "future", "upcoming"}:
            upcoming.append(item)
            continue

        active_from = parse_int(item.get("active_from_chapter"))
        due_chapter = parse_int(item.get("due_chapter"))
        has_scope = any(
            item.get(field) not in (None, "")
            for field in ["target_volume", "target_stage", "active_from_chapter", "due_chapter"]
        )

        if chapter is not None and active_from is not None and chapter >= active_from:
            active.append(item)
        elif chapter is not None and due_chapter is not None and chapter >= due_chapter:
            active.append(item)
        elif has_scope:
            upcoming.append(item)
        else:
            unscoped.append(item)

    return active, upcoming, unscoped


def obligation_summary(item: dict[str, Any]) -> str:
    scope = []
    for field, label in [
        ("target_volume", "目标卷"),
        ("target_stage", "阶段"),
        ("active_from_chapter", "起始章"),
        ("due_chapter", "截止章"),
        ("priority", "优先级"),
        ("status", "状态"),
    ]:
        value = item.get(field)
        if value not in (None, ""):
            scope.append(f"{label}={value}")
    suffix = f" ({'; '.join(scope)})" if scope else ""
    return f"{item.get('id', 'unnamed')}: {item.get('description', '未填写描述')}{suffix}"


def outline_status(project_root: str | Path, chapter: int | None = None) -> str:
    root = Path(project_root).resolve()
    ensure_outline_files(root)
    graph = read_json(root / "00_memory" / "story_graph.json")
    meta = graph.get("meta", {})
    open_items = [
        item for item in graph.get("downstream_obligations", []) if isinstance(item, dict) and item.get("status") != "closed"
    ]
    active, upcoming, unscoped = classify_obligations(open_items, chapter=chapter)
    lines = [
        f"当前大纲版本: {meta.get('current_outline_version', 'outline_v0')}",
        f"改纲次数: {meta.get('outline_revision_count', 0)}",
        f"检查章节: {chapter if chapter is not None else '未指定'}",
        f"当前必须处理剧情债: {len(active)}",
        f"未来/未到期剧情债: {len(upcoming)}",
        f"未归档剧情债: {len(unscoped)}",
    ]
    if active:
        lines.append("\n【当前必须处理】")
        lines.extend(f"- {obligation_summary(item)}" for item in active)
    if upcoming:
        lines.append("\n【未来/未到期，不得强行提前兑现】")
        lines.extend(f"- {obligation_summary(item)}" for item in upcoming)
    if unscoped:
        lines.append("\n【未归档，需补目标卷/章节；补完前不作为写作打回理由】")
        lines.extend(f"- {obligation_summary(item)}" for item in unscoped)
    return "\n".join(lines)


def scope_obligation(
    project_root: str | Path,
    obligation_id: str,
    target_volume: str | None = None,
    target_stage: str | None = None,
    active_from_chapter: int | None = None,
    due_chapter: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    blocking: bool | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    ensure_outline_files(root)
    graph_path = root / "00_memory" / "story_graph.json"
    graph = read_json(graph_path)
    obligations = graph.setdefault("downstream_obligations", [])
    for item in obligations:
        if not isinstance(item, dict) or item.get("id") != obligation_id:
            continue
        if target_volume is not None:
            item["target_volume"] = target_volume
        if target_stage is not None:
            item["target_stage"] = target_stage
        if active_from_chapter is not None:
            item["active_from_chapter"] = active_from_chapter
        if due_chapter is not None:
            item["due_chapter"] = due_chapter
        if status is not None:
            item["status"] = status
        if priority is not None:
            item["priority"] = priority
        if blocking is not None:
            item["blocking"] = blocking
        if note is not None:
            item["scope_note"] = note
        item["updated_at"] = datetime.now().isoformat(timespec="seconds")
        write_json(graph_path, graph)
        return item
    raise ValueError(f"未找到剧情债: {obligation_id}")


def split_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Naruto Author 大纲打磨与改纲版本管理")
    parser.add_argument("--root", default=".", help="项目根目录")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("ensure", help="补齐 outline_changelog 与 story_graph 改纲字段")

    propose = subparsers.add_parser("propose", help="生成改纲提案包，不修改正式大纲")
    propose.add_argument("--request", help="人工改纲诉求")
    propose.add_argument("--request-file", help="人工改纲诉求文件")
    propose.add_argument("--chapter", type=int, help="目标章节或阶段")
    propose.add_argument("--revision-id", help="指定版本 ID")
    propose.add_argument("--out", help="输出文件")

    record = subparsers.add_parser("record", help="记录已人工确认的改纲")
    record.add_argument("--summary", required=True, help="改动摘要")
    record.add_argument("--request", help="人工确认说明")
    record.add_argument("--request-file", help="人工确认说明文件")
    record.add_argument("--status", default="accepted", choices=["draft", "accepted", "rejected", "superseded"])
    record.add_argument("--revision-id", help="指定版本 ID")
    record.add_argument("--artifact", help="关联的提案/审核文件")
    record.add_argument("--affected-canon", help="逗号分隔的原著锚点 ID")
    record.add_argument("--affected-characters", help="逗号分隔的人物 ID")
    record.add_argument("--obligation", action="append", default=[], help="下游剧情债，可重复")
    record.add_argument("--target-volume", help="剧情债目标卷，例如 第二卷")
    record.add_argument("--target-stage", help="剧情债目标阶段，例如 忍校期/毕业季")
    record.add_argument("--active-from-chapter", type=int, help="从第几章开始成为当前硬约束")
    record.add_argument("--due-chapter", type=int, help="最晚第几章偿还")
    record.add_argument("--priority", default="normal", choices=["low", "normal", "high"])
    record.add_argument("--blocking", action="store_true", help="到期后是否作为硬门禁")

    scope = subparsers.add_parser("scope-obligation", help="给既有剧情债补目标卷/章节，避免提前催债")
    scope.add_argument("--id", required=True, help="剧情债 ID")
    scope.add_argument("--target-volume", help="目标卷，例如 第二卷")
    scope.add_argument("--target-stage", help="目标阶段")
    scope.add_argument("--active-from-chapter", type=int, help="起始章")
    scope.add_argument("--due-chapter", type=int, help="截止章")
    scope.add_argument("--status", choices=["open", "deferred", "future", "upcoming", "closed"])
    scope.add_argument("--priority", choices=["low", "normal", "high"])
    scope.add_argument("--blocking", action="store_true", help="设置为硬约束")
    scope.add_argument("--nonblocking", action="store_true", help="设置为非硬约束")
    scope.add_argument("--note", help="范围说明")

    status = subparsers.add_parser("status", help="查看改纲状态")
    status.add_argument("--chapter", type=int, help="按当前章节判断哪些剧情债已到期")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.command in (None, "ensure"):
        ensure_outline_files(root)
        print("[OK] 已补齐大纲打磨基础文件")
        return 0

    if args.command == "propose":
        request_text = read_text_arg(args.request, args.request_file)
        path = create_outline_proposal(root, request_text, args.chapter, args.revision_id, args.out)
        print(f"[OK] 已生成改纲提案包: {path}")
        return 0

    if args.command == "record":
        request_text = read_text_arg(args.request, args.request_file)
        revision_id = record_outline_revision(
            root,
            summary=args.summary,
            request_text=request_text,
            affected_canon_ids=split_csv(args.affected_canon),
            affected_character_ids=split_csv(args.affected_characters),
            obligations=args.obligation,
            status=args.status,
            revision_id=args.revision_id,
            artifact=args.artifact,
            target_volume=args.target_volume,
            target_stage=args.target_stage,
            active_from_chapter=args.active_from_chapter,
            due_chapter=args.due_chapter,
            priority=args.priority,
            blocking=args.blocking,
        )
        print(f"[OK] 已记录改纲版本: {revision_id}")
        return 0

    if args.command == "scope-obligation":
        if args.blocking and args.nonblocking:
            parser.error("--blocking 和 --nonblocking 不能同时使用")
        blocking = True if args.blocking else False if args.nonblocking else None
        item = scope_obligation(
            root,
            obligation_id=args.id,
            target_volume=args.target_volume,
            target_stage=args.target_stage,
            active_from_chapter=args.active_from_chapter,
            due_chapter=args.due_chapter,
            status=args.status,
            priority=args.priority,
            blocking=blocking,
            note=args.note,
        )
        print(f"[OK] 已更新剧情债范围: {obligation_summary(item)}")
        return 0

    if args.command == "status":
        print(outline_status(root, chapter=args.chapter))
        return 0

    parser.error("未知命令")
    return 2


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
