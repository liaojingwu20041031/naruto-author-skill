import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


MAX_AUTO_REVISIONS = 2


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def state_path(root: Path, chapter: int) -> Path:
    return root / "04_editing" / "gate_artifacts" / f"revision_loop_chapter_{chapter}.json"


def load_state(root: Path, chapter: int) -> dict[str, Any]:
    path = state_path(root, chapter)
    if not path.exists():
        return {
            "chapter": chapter,
            "auto_revision_count": 0,
            "max_auto_revisions": MAX_AUTO_REVISIONS,
            "status": "open",
            "events": [],
        }
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(root: Path, chapter: int, state: dict[str, Any]) -> Path:
    path = state_path(root, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def status_text(state: dict[str, Any]) -> str:
    count = int(state.get("auto_revision_count") or 0)
    max_count = int(state.get("max_auto_revisions") or MAX_AUTO_REVISIONS)
    remaining = max(max_count - count, 0)
    gate_status = "blocked" if remaining <= 0 else state.get("status", "open")
    return (
        f"章节: {state.get('chapter')}\n"
        f"自动修稿次数: {count}/{max_count}\n"
        f"剩余自动修稿次数: {remaining}\n"
        f"门禁状态: {gate_status}"
    )


def bump_revision(root: Path, chapter: int, reason: str) -> tuple[dict[str, Any], bool]:
    state = load_state(root, chapter)
    count = int(state.get("auto_revision_count") or 0)
    max_count = int(state.get("max_auto_revisions") or MAX_AUTO_REVISIONS)
    if count >= max_count:
        state["status"] = "blocked"
        state.setdefault("events", []).append(
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "type": "blocked",
                "reason": reason,
                "message": "自动修稿次数已达上限，必须人工裁决。",
            }
        )
        save_state(root, chapter, state)
        return state, False

    state["auto_revision_count"] = count + 1
    state["status"] = "open" if state["auto_revision_count"] < max_count else "last_auto_revision_used"
    state.setdefault("events", []).append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "type": "auto_revision",
            "reason": reason,
            "count": state["auto_revision_count"],
        }
    )
    save_state(root, chapter, state)
    return state, True


def reset_state(root: Path, chapter: int) -> dict[str, Any]:
    state = {
        "chapter": chapter,
        "auto_revision_count": 0,
        "max_auto_revisions": MAX_AUTO_REVISIONS,
        "status": "open",
        "events": [
            {
                "time": datetime.now().isoformat(timespec="seconds"),
                "type": "reset",
                "reason": "人工重置修稿循环",
            }
        ],
    }
    save_state(root, chapter, state)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Naruto Author 单章修稿循环计数器")
    parser.add_argument("--root", default=".", help="项目根目录")
    parser.add_argument("--chapter", type=int, required=True, help="章节号")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status", help="查看本章自动修稿次数")
    bump = subparsers.add_parser("bump", help="记录一次自动修稿")
    bump.add_argument("--reason", default="暗部审核打回后自动修稿", help="本次修稿原因")
    subparsers.add_parser("reset", help="人工重置本章修稿计数")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    if args.command in (None, "status"):
        state = load_state(root, args.chapter)
        print(status_text(state))
        return 0

    if args.command == "bump":
        state, allowed = bump_revision(root, args.chapter, args.reason)
        print(status_text(state))
        if not allowed:
            print("[BLOCKED] 自动修稿次数已达 2 次，请停止自动重写，转为人工裁决。")
            return 1
        print("[OK] 已记录一次自动修稿")
        return 0

    if args.command == "reset":
        state = reset_state(root, args.chapter)
        print(status_text(state))
        print("[OK] 已重置")
        return 0

    parser.error("未知命令")
    return 2


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
