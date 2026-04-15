import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


DEFAULT_ENTITY_TABLES = [
    "characters",
    "jutsus",
    "organizations",
    "artifacts",
    "canon_plot",
    "pre_main_timeline",
    "tailed_beasts",
    "relations",
    "world_background",
]


COLLECTION_KEYS_BY_TABLE = {
    "canon_plot": ("arcs",),
    "pre_main_timeline": ("events", "timeline"),
}


TERM_FIELDS = ("id", "name_zh", "name", "title", "eye_type", "aliases")


SUMMARY_FIELDS = (
    "continuity_risk",
    "fanfic_risk",
    "continuity_rule",
    "summary",
    "description",
    "impact",
    "status",
    "role",
    "life_status_canon_end",
)


def configure_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


class FanficDBQuerier:
    """Query helper for the bundled Naruto fanfic continuity database."""

    def __init__(self, db_root: str | Path | None = None):
        self.db_root = self.resolve_db_root(db_root)
        self.db_cache: dict[str, Any] = {}

    @staticmethod
    def resolve_db_root(db_root: str | Path | None = None) -> Path:
        script_skill_root = Path(__file__).resolve().parent.parent
        candidates: list[Path] = []

        if db_root:
            candidates.append(Path(db_root).expanduser())

        cwd = Path.cwd()
        candidates.extend(
            [
                cwd / "naruto_fanfic_db",
                cwd / ".claude" / "skills" / "naruto-author" / "naruto_fanfic_db",
                cwd.parent / "naruto_fanfic_db",
                script_skill_root / "naruto_fanfic_db",
            ]
        )

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved.exists() and resolved.is_dir():
                return resolved

        checked = "\n".join(f"  - {path}" for path in candidates)
        raise FileNotFoundError(f"未找到 naruto_fanfic_db，已检查:\n{checked}")

    def list_tables(self) -> list[str]:
        return sorted(path.stem for path in self.db_root.glob("*.json"))

    def load_table(self, table_name: str) -> Any | None:
        if table_name in self.db_cache:
            return self.db_cache[table_name]

        file_path = self.db_root / f"{table_name}.json"
        if not file_path.exists():
            return None

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:
            print(f"加载 {table_name}.json 失败: {exc}", file=sys.stderr)
            return None

        self.db_cache[table_name] = data
        return data

    @staticmethod
    def _records_from_table(table: Any, collection_key: str) -> Iterable[dict[str, Any]]:
        if not isinstance(table, dict):
            return []

        records = table.get(collection_key)
        if isinstance(records, list):
            return [record for record in records if isinstance(record, dict)]
        if isinstance(records, dict):
            return [record for record in records.values() if isinstance(record, dict)]
        return []

    @staticmethod
    def _looks_like_record(record: dict[str, Any]) -> bool:
        return any(field in record for field in ("id", "name_zh", "title"))

    def iter_table_records(self, table_name: str) -> Iterable[dict[str, Any]]:
        """Yield JSON records from any supported table shape."""
        table = self.load_table(table_name)
        if not isinstance(table, dict):
            return []

        records: list[dict[str, Any]] = []
        seen_object_ids: set[int] = set()
        preferred_keys = COLLECTION_KEYS_BY_TABLE.get(table_name, ())

        for key in (*preferred_keys, table_name):
            value = table.get(key)
            if isinstance(value, list):
                for record in value:
                    if isinstance(record, dict) and self._looks_like_record(record):
                        object_id = id(record)
                        if object_id not in seen_object_ids:
                            seen_object_ids.add(object_id)
                            records.append(record)
            elif isinstance(value, dict):
                for record in value.values():
                    if isinstance(record, dict) and self._looks_like_record(record):
                        object_id = id(record)
                        if object_id not in seen_object_ids:
                            seen_object_ids.add(object_id)
                            records.append(record)

        for value in table.values():
            if isinstance(value, list):
                for record in value:
                    if isinstance(record, dict) and self._looks_like_record(record):
                        object_id = id(record)
                        if object_id not in seen_object_ids:
                            seen_object_ids.add(object_id)
                            records.append(record)
            elif isinstance(value, dict) and self._looks_like_record(value):
                object_id = id(value)
                if object_id not in seen_object_ids:
                    seen_object_ids.add(object_id)
                    records.append(value)
            elif isinstance(value, dict):
                for record in value.values():
                    if isinstance(record, dict) and self._looks_like_record(record):
                        object_id = id(record)
                        if object_id not in seen_object_ids:
                            seen_object_ids.add(object_id)
                            records.append(record)

        return records

    def iter_records(self, tables: list[str] | None = None) -> Iterable[tuple[str, dict[str, Any]]]:
        """Yield (table_name, record) pairs across the fanfic DB."""
        tables_to_scan = tables or self.list_tables()
        for table_name in tables_to_scan:
            for record in self.iter_table_records(table_name):
                yield table_name, record

    @staticmethod
    def _value_matches(value: Any, query: str) -> bool:
        query_lower = query.lower()
        if isinstance(value, str):
            return query_lower in value.lower()
        if isinstance(value, list):
            return any(FanficDBQuerier._value_matches(item, query) for item in value)
        if isinstance(value, dict):
            return any(FanficDBQuerier._value_matches(item, query) for item in value.values())
        return False

    @staticmethod
    def _record_matches(record: dict[str, Any], query: str) -> bool:
        prioritized_fields = ("id", "name_zh", "name", "aliases")
        if any(FanficDBQuerier._value_matches(record.get(field), query) for field in prioritized_fields):
            return True
        return FanficDBQuerier._value_matches(record, query)

    @staticmethod
    def _first_present(record: dict[str, Any], fields: tuple[str, ...]) -> Any | None:
        for field in fields:
            value = record.get(field)
            if value:
                return value
        return None

    @staticmethod
    def _has_cjk(text: str) -> bool:
        return any("\u4e00" <= char <= "\u9fff" for char in text)

    @classmethod
    def _term_is_searchable(cls, term: str) -> bool:
        term = term.strip()
        if not term:
            return False
        if cls._has_cjk(term):
            return len(term) >= 2
        return len(term) >= 3

    @classmethod
    def _record_terms(cls, record: dict[str, Any]) -> list[str]:
        terms: list[str] = []

        def add(value: Any) -> None:
            if isinstance(value, str):
                candidate = value.strip()
                if cls._term_is_searchable(candidate) and candidate not in terms:
                    terms.append(candidate)
            elif isinstance(value, list):
                for item in value:
                    add(item)

        for field in TERM_FIELDS:
            value = record.get(field)
            add(value)
            if field in ("name_zh", "name", "title") and isinstance(value, str):
                for suffix in ("隐村", "之术", "模式", "组织", "一族", "篇"):
                    if value.endswith(suffix):
                        add(value[: -len(suffix)])

        return terms

    @staticmethod
    def _compact_value(value: Any, max_items: int = 2, max_chars: int = 120) -> str:
        if isinstance(value, list):
            text = "、".join(str(item) for item in value[:max_items])
            if len(value) > max_items:
                text += " 等"
        elif isinstance(value, dict):
            text = "；".join(f"{key}={item}" for key, item in list(value.items())[:max_items])
            if len(value) > max_items:
                text += " 等"
        else:
            text = str(value)
        return text[:max_chars]

    @classmethod
    def _record_summary(cls, record: dict[str, Any]) -> str | None:
        parts: list[str] = []
        for field in SUMMARY_FIELDS:
            value = record.get(field)
            if not value:
                continue
            parts.append(cls._compact_value(value))
            if len(parts) >= 2:
                break
        return "；".join(parts) if parts else None

    def find_record(self, table_name: str, collection_key: str, query: str) -> dict[str, Any] | None:
        table = self.load_table(table_name)
        for record in self._records_from_table(table, collection_key):
            if self._record_matches(record, query):
                return record
        return None

    def get_character(self, char_id: str) -> dict[str, Any] | None:
        """查询特定人物。"""
        return self.find_record("characters", "characters", char_id)

    def get_jutsu(self, jutsu_id: str) -> dict[str, Any] | None:
        """查询特定忍术及其代价/限制。"""
        return self.find_record("jutsus", "jutsus", jutsu_id)

    def search(self, query: str, tables: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        """Cross-table fuzzy search for writing-time fact checks."""
        results: list[dict[str, Any]] = []
        tables_to_scan = tables or self.list_tables()

        for table_name, record in self.iter_records(tables_to_scan):
            if not self._record_matches(record, query):
                continue
            results.append(
                {
                    "table": table_name,
                    "id": record.get("id"),
                    "name_zh": self._first_present(record, ("name_zh", "name", "eye_type", "title")),
                    "summary": self._record_summary(record),
                }
            )
            if len(results) >= limit:
                return results

        return results

    def mentioned_records(
        self,
        text: str,
        tables: list[str] | None = None,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Find DB records explicitly mentioned by name/id/alias in a text block."""
        text_lower = text.lower()
        scored_results: list[dict[str, Any]] = []
        tables_to_scan = tables or DEFAULT_ENTITY_TABLES

        for table_name, record in self.iter_records(tables_to_scan):
            matched_terms: list[str] = []
            score = 0
            for term in self._record_terms(record):
                if self._has_cjk(term):
                    matched = term in text
                else:
                    matched = term.lower() in text_lower
                if not matched:
                    continue
                matched_terms.append(term)
                score += 10 + min(len(term), 20)

            if not matched_terms:
                continue

            scored_results.append(
                {
                    "table": table_name,
                    "id": record.get("id"),
                    "name_zh": self._first_present(record, ("name_zh", "name", "eye_type", "title")),
                    "matched_terms": matched_terms[:4],
                    "summary": self._record_summary(record),
                    "record": record,
                    "score": score,
                }
            )

        table_priority = {table: index for index, table in enumerate(DEFAULT_ENTITY_TABLES)}
        scored_results.sort(
            key=lambda item: (
                -item["score"],
                table_priority.get(item["table"], 999),
                str(item.get("id") or ""),
            )
        )
        return scored_results[:limit]

    def check_continuity_risks(self, char_id: str) -> str:
        """检查人物的长篇连载崩坏风险与秘密边界。"""
        char = self.get_character(char_id)
        if not char:
            return "未找到人物信息"

        report = f"【一致性检查 - {char.get('name_zh', char_id)}】\n"
        if char.get("life_status_canon_end"):
            report += f"原著终局状态: {char['life_status_canon_end']}\n"

        risks = char.get("continuity_risks") or []
        if risks:
            report += "写作崩坏风险:\n"
            for risk in risks:
                report += f"  - {risk}\n"

        secrets = char.get("sensitive_secrets") or []
        if secrets:
            report += "核心秘密防线 (绝不能提前泄露的秘密):\n"
            for secret in secrets:
                report += f"  - {secret}\n"

        return report


def dump_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="查询火影同人长篇资料库")
    parser.add_argument("type", choices=["char", "jutsu", "risk", "search", "mentions", "tables"], help="查询类型")
    parser.add_argument("target", nargs="?", help="查询 ID、中文名或关键词")
    parser.add_argument("--db", dest="db_root", help="资料库目录，默认自动定位 naruto_fanfic_db")
    parser.add_argument("--limit", type=int, default=10, help="search 返回数量上限")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    db = FanficDBQuerier(args.db_root)

    if args.type == "tables":
        dump_json(db.list_tables())
        return 0

    if not args.target:
        parser.error("除 tables 外，其他查询类型都需要 target")

    if args.type == "char":
        result = db.get_character(args.target)
        if result:
            dump_json(result)
            return 0
        print(f"未找到人物: {args.target}")
        return 1

    if args.type == "jutsu":
        result = db.get_jutsu(args.target)
        if result:
            dump_json(result)
            return 0
        print(f"未找到忍术: {args.target}")
        return 1

    if args.type == "risk":
        print(db.check_continuity_risks(args.target))
        return 0

    if args.type == "search":
        dump_json(db.search(args.target, limit=args.limit))
        return 0

    if args.type == "mentions":
        results = db.mentioned_records(args.target, limit=args.limit)
        for result in results:
            result.pop("record", None)
            result.pop("score", None)
        dump_json(results)
        return 0

    parser.error("未知的查询类型")
    return 2


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
