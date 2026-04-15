import os
import json
import argparse
import importlib.util
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def configure_utf8_output():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


class NarutoAuthorOrchestrator:
    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()
        # 支持动态定位 prompts 目录
        self.skill_dir = Path(__file__).parent.parent
        self.prompts_dir = self.skill_dir / "prompts"

    def load_iron_laws(self):
        """加载忍界铁律 (anti-patterns)"""
        anti_pattern_file = self.prompts_dir / "anti-patterns.md"
        if anti_pattern_file.exists():
            with open(anti_pattern_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "【未找到忍界铁律文件，请确保目录结构正确】"

    def load_query_db_module(self):
        module_name = "naruto_author_query_db"
        if module_name in sys.modules:
            return sys.modules[module_name]

        module_path = Path(__file__).resolve().parent / "query_db.py"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"无法加载资料库脚本: {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def resolve_db_root(self):
        project_db = self.project_root / "naruto_fanfic_db"
        if project_db.exists():
            return project_db
        return self.skill_dir / "naruto_fanfic_db"

    def load_memory_for_db_context(self, max_chars=18000):
        memory_files = [
            "00_memory/novel_plan.md",
            "00_memory/novel_state.md",
            "00_memory/story_graph.json",
        ]
        chunks = []
        used_chars = 0

        for rel_path in memory_files:
            file_path = self.project_root / rel_path
            if not file_path.exists():
                continue
            text = file_path.read_text(encoding="utf-8", errors="replace")
            remaining = max_chars - used_chars
            if remaining <= 0:
                break
            chunks.append(f"\n[{rel_path}]\n{text[:remaining]}")
            used_chars += min(len(text), remaining)

        return "\n".join(chunks)

    @staticmethod
    def compact_value(value: Any, max_items=3, max_chars=110):
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

    def format_db_record_brief(self, hit):
        record = hit.get("record") or {}
        table = hit.get("table")
        field_labels = [
            ("life_status_canon_end", "原著终局"),
            ("affiliations", "阵营"),
            ("signature_abilities", "招牌能力"),
            ("sensitive_secrets", "秘密边界"),
            ("continuity_risks", "连续性风险"),
            ("rank", "等级"),
            ("prerequisites", "前置条件"),
            ("cost", "代价"),
            ("limitations", "限制"),
            ("continuity_risk", "连续性风险"),
            ("fanfic_risk", "同人风险"),
            ("leader_title", "首领称号"),
            ("continuity_fields", "需记录字段"),
            ("anchor_events", "原著锚点"),
            ("butterfly_sensitive_points", "蝴蝶敏感点"),
            ("summary", "摘要"),
            ("description", "描述"),
            ("status", "状态"),
        ]
        parts = []

        for field, label in field_labels:
            value = record.get(field)
            if not value:
                continue
            parts.append(f"{label}: {self.compact_value(value)}")
            if len(parts) >= 4:
                break

        summary = hit.get("summary")
        if summary and not parts:
            parts.append(f"摘要: {summary}")

        if not parts:
            parts.append(f"表: {table}")

        return "；".join(parts)

    def build_db_context(self, outline_beat, max_results=12, max_memory_results=4):
        query_db = self.load_query_db_module()
        db = query_db.FanficDBQuerier(self.resolve_db_root())

        merged_hits = {}
        for source, text, limit in [
            ("Beat", outline_beat, max_results),
            ("记忆", self.load_memory_for_db_context(), max_memory_results),
        ]:
            if not text.strip():
                continue
            source_hits = 0
            for hit in db.mentioned_records(text, limit=limit):
                key = hit.get("id") or f"{hit.get('table')}:{hit.get('name_zh')}"
                if key in merged_hits:
                    continue
                hit["source"] = source
                merged_hits[key] = hit
                source_hits += 1
                if len(merged_hits) >= max_results:
                    break
                if source == "记忆" and source_hits >= max_memory_results:
                    break
            if len(merged_hits) >= max_results:
                break

        lines = [
            "【资料库命中锚点（自动从 naruto_fanfic_db 注入）】",
            "使用规则：以下记录由脚本根据本章 Beat 与 00_memory 自动命中，正文必须遵守这些原著/长篇连续性边界；不要只凭模型记忆写。",
        ]

        if not merged_hits:
            lines.extend(
                [
                    "- 未从 Beat 或当前记忆中自动命中实体。若本章涉及具体人物、忍术、组织、尾兽或原著事件，先运行：",
                    "  python .claude/skills/naruto-author/scripts/query_db.py search \"关键词\"",
                    "- 也可以把具体实体写进 Beat，再重新生成章节写作包。",
                ]
            )
            return "\n".join(lines)

        for index, hit in enumerate(merged_hits.values(), start=1):
            table = hit.get("table")
            record_id = hit.get("id") or "unknown_id"
            name = hit.get("name_zh") or record_id
            matched_terms = "、".join(hit.get("matched_terms") or [])
            brief = self.format_db_record_brief(hit)
            lines.append(
                f"{index}. [{hit.get('source')}] {table}/{record_id}《{name}》：{brief}；命中词: {matched_terms}"
            )

        lines.append("写作要求：涉及以上条目时，必须把代价、限制、秘密知情范围、生死状态和蝴蝶效应写进动作与选择里。")
        return "\n".join(lines)

    @staticmethod
    def parse_int(value):
        try:
            if value in (None, ""):
                return None
            return int(value)
        except (TypeError, ValueError):
            return None

    def classify_outline_obligations(self, obligations, chapter_num=None):
        active = []
        upcoming = []
        unscoped = []

        current_chapter = self.parse_int(chapter_num)
        for item in obligations:
            if not isinstance(item, dict):
                continue
            status = item.get("status", "open")
            if status == "closed":
                continue

            active_from = self.parse_int(item.get("active_from_chapter"))
            due_chapter = self.parse_int(item.get("due_chapter"))
            target_volume = item.get("target_volume") or item.get("target_arc")
            target_stage = item.get("target_stage")

            if status in {"deferred", "future", "upcoming"}:
                upcoming.append(item)
                continue

            if current_chapter is not None:
                if active_from is not None and current_chapter >= active_from:
                    active.append(item)
                    continue
                if due_chapter is not None and current_chapter >= due_chapter:
                    active.append(item)
                    continue
                if active_from is not None or due_chapter is not None or target_volume or target_stage:
                    upcoming.append(item)
                    continue

            if active_from is None and due_chapter is None and not target_volume and not target_stage:
                unscoped.append(item)
            else:
                upcoming.append(item)

        return active, upcoming, unscoped

    def format_obligation_line(self, item):
        parts = [f"{item.get('id', 'unnamed')}: {item.get('description', '未填写描述')}"]
        scope = []
        for field, label in [
            ("target_volume", "目标卷"),
            ("target_stage", "目标阶段"),
            ("active_from_chapter", "起始章"),
            ("due_chapter", "截止章"),
            ("priority", "优先级"),
            ("status", "状态"),
        ]:
            value = item.get(field)
            if value not in (None, ""):
                scope.append(f"{label}={value}")
        if scope:
            parts.append(f"({'; '.join(scope)})")
        return " ".join(parts)

    def build_outline_guard_context(self, chapter_num=None):
        story_graph_path = self.project_root / "00_memory" / "story_graph.json"
        if not story_graph_path.exists():
            return (
                "【大纲版本与下游剧情债】\n"
                "- 未找到 00_memory/story_graph.json。写作前请先初始化项目或补齐动态记忆。"
            )

        try:
            graph = json.loads(story_graph_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return f"【大纲版本与下游剧情债】\n- story_graph.json 解析失败：{exc}"

        meta = graph.get("meta") if isinstance(graph.get("meta"), dict) else {}
        current_outline_version = meta.get("current_outline_version", "outline_v0")
        obligations = graph.get("downstream_obligations") or []
        active_obligations, upcoming_obligations, unscoped_obligations = self.classify_outline_obligations(
            obligations,
            chapter_num=chapter_num,
        )

        lines = [
            "【大纲版本与下游剧情债】",
            f"- 当前大纲版本：{current_outline_version}",
            f"- 当前章节：{chapter_num if chapter_num is not None else '未指定'}",
        ]
        if active_obligations:
            lines.append("- 当前必须处理剧情债：")
            for item in active_obligations[:8]:
                lines.append(f"  - {self.format_obligation_line(item)}")
            if len(active_obligations) > 8:
                lines.append(f"  - 另有 {len(active_obligations) - 8} 项未列出")
            lines.append("- 写作要求：只有上面“当前必须处理”的剧情债才是本章硬约束。")
        else:
            lines.append("- 当前章节没有必须处理的剧情债。")

        if upcoming_obligations:
            lines.append("- 未来/未到期剧情债（不得强行提前兑现，只可轻描淡写铺垫）：")
            for item in upcoming_obligations[:8]:
                lines.append(f"  - {self.format_obligation_line(item)}")
            if len(upcoming_obligations) > 8:
                lines.append(f"  - 另有 {len(upcoming_obligations) - 8} 项未列出")

        if unscoped_obligations:
            lines.append("- 未归档剧情债（缺少目标卷/起始章/截止章，不作为本章打回理由）：")
            for item in unscoped_obligations[:8]:
                lines.append(f"  - {self.format_obligation_line(item)}")
            lines.append("- 处理建议：先用 outline_manager.py scope-obligation 指定适用卷章，再让它进入写作门禁。")

        return "\n".join(lines)

    def load_env_files(self):
        """Load .env files with project-local settings taking priority."""
        if load_dotenv is None:
            return False

        loaded = False
        env_paths = [
            self.project_root / ".env",
            Path.cwd() / ".env",
            Path(__file__).resolve().parent / ".env",
        ]

        seen = set()
        for env_path in env_paths:
            resolved = env_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            if resolved.exists():
                load_dotenv(dotenv_path=resolved, override=False)
                loaded = True

        return loaded

    def load_deepseek_api_key(self, api_key=None):
        self.load_env_files()
        return api_key or os.environ.get("DEEPSEEK_API_KEY")

    def deepseek_chat(self, messages, api_key=None, temperature=0.3, max_tokens=2000, timeout=60):
        """
        通用 DeepSeek Chat 调用。只接收 messages，不在日志中输出密钥。
        返回 (answer, error_message)。
        """
        api_key = self.load_deepseek_api_key(api_key)
        if not api_key:
            if load_dotenv is None:
                return None, "缺失 DEEPSEEK_API_KEY，且未安装 python-dotenv。请运行 pip install python-dotenv，并在项目 .env 中配置。"
            return None, "缺失 DEEPSEEK_API_KEY。请在项目根目录 .env 中配置，不要把密钥写进 skill 文件。"

        url = os.environ.get("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        data = {
            "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"], None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return None, f"DeepSeek 调用异常: HTTP {exc.code} {detail}"
        except Exception as exc:
            return None, f"DeepSeek 调用异常: {str(exc)}"

    def deepseek_inquiry(self, query, api_key=None):
        """
        DeepSeek 情报顾问 (中文质询与脑洞拓展)
        用于查阅模糊的设定、推演特定忍术原理，获取中文梗、角色心理演化路径。
        """
        print(f"=> [情报顾问 DeepSeek] 正在质询: {query}")

        system_prompt = (
            "你是一个精通《火影忍者》设定的资深同人编辑，深谙中文同人圈的热门梗（如木叶锅王、旗木五五开、大筒木一乐）。"
            "你的任务是回答设气质询，提供极具张力和趣味性的脑洞，"
            "同时你要特别关注【角色的动态心理演变】，在不同时间线/压力下推演合乎逻辑的黑化、洗白或性格重塑路径。"
            "回答必须精炼、富有启发性，且完全符合火影底层逻辑（不生硬、不突兀）。"
        )

        answer, error = self.deepseek_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query},
            ],
            temperature=0.5,
            max_tokens=2000,
            api_key=api_key,
        )
        if error:
            return error
        print("   [DeepSeek] 质询完成。")
        return answer

    def prepare_chapter_prompt(self, outline_beat, chapter_num=1):
        """
        准备发给 AI 主笔作家 (Claude Code / Codex 均可) 的正文写作指令包
        """
        print(f"=> [主控] 准备第 {chapter_num} 章的写作包裹给 Claude Code / Codex...")
        outline_guard_context = self.build_outline_guard_context(chapter_num=chapter_num)
        db_context = self.build_db_context(outline_beat)

        prompt = (
            f"作为【AI 主笔作家（Claude Code / Codex 均可）】，请根据以下分镜剧本(Beat Sheet)，撰写第 {chapter_num} 章的完整小说正文，正文主体字数要求 4000-5000 字左右。\n\n"
            "在动笔前，你必须查阅以下文件确保不会偏离原著锚点（优先读项目内副本，不存在时读 Skill 内置资料库）：\n"
            "- naruto_fanfic_db/canon_plot.json\n"
            "- naruto_fanfic_db/characters.json\n"
            "- naruto_fanfic_db/jutsus.json\n"
            "- 00_memory/novel_plan.md\n"
            "- 00_memory/novel_state.md\n"
            "- 00_memory/story_graph.json\n\n"
            f"{outline_guard_context}\n\n"
            f"{db_context}\n\n"
            "【本书风格】：轻松快乐向、二创向、系统文。允许喜剧化偏移、误会梗、制度梗、系统奖励反差和少量原著口头禅；禁止的是角色底层动机断裂、机械口癖堆砌、战力无代价碾压和设定说明文。\n"
            "注重人物动作描写、心理博弈、忍术释放的画面感和轻喜剧互动。信息要通过事件、对话、误会、旁人观察或系统提示自然带出。\n\n"
            "【场景链约束】：写作以当前小篇章和场景链为骨架，章节只是发布包装。若 Beat 给出了多个场景，必须让前一场的结果成为后一场的动机、压力、误判或行动条件；不要为了满足章号推进而跳过因果发酵、势力反应或人物关系余波。\n\n"
            "【情绪弧线指导】：每章先想清“事件 -> 可见反应 -> 选择 -> 余波”，但正文不要机械套公式。\n"
            "- 关键场景必须能对应到：触发事件、外显反应、即时决定、结果余波；需要承接时，在下一场或下一小篇章留下余震。\n"
            "- 情绪描写短、准、具体：优先写手上动作、视线停顿、物件变化、对话卡壳、环境反应，再用一句短促心理收束。\n"
            "- 不用固定词频判高压线，但要避免同一情绪无新事件支撑地反复换词重说，尤其避免空泛堆“绝望/麻木/愤怒/无力/不甘”。\n"
            "- 轻小说节奏：事件、互动、误会、选择推动情绪；情绪落点之后尽快进入下一个动作、对话、发现或关系变化。\n"
            "- 4000-5000 字主要扩写事件链、人物互动、场面调度、制度梗和小冲突，不扩写纯心理独白。\n"
            "- 章末必须留下情绪余波，写入“暗部查验数据”的【情绪弧线】字段，供下一章承接。\n\n"
            "【请严格遵循以下《忍界铁律》进行创作】：\n"
            f"{self.load_iron_laws()}\n\n"
            f"【本章分镜剧本】：\n{outline_beat}\n\n"
            "请直接输出 Markdown 格式的小说正文，不需要任何前置废话分析。"
        )
        return prompt

    def build_deepseek_audit_prompt(self, chapter_text, chapter_num=None):
        """
        阶段四：构建 DeepSeek 暗部审核 Prompt。
        DeepSeek 只负责毒点审查，不负责续写正文。
        """
        outline_guard_context = self.build_outline_guard_context(chapter_num=chapter_num)
        db_context = self.build_db_context(chapter_text, max_results=18, max_memory_results=4)

        chapter_label = f"第 {chapter_num} 章" if chapter_num else "当前章节"
        return (
            f"你是《Naruto Author AI》的 DeepSeek 暗部审核官。请审核{chapter_label}，只做审稿，不续写、不扩写、不替作者重写整章。\n"
            "重要：全程使用中文；不要展示内部推理过程；不要输出客套话；只输出审核结论、毒点清单和可执行修改建议。\n\n"
            "【输出格式】\n"
            "1. 【审核结论】：通过 / 打回重写 / 需要小修。\n"
            "2. 【毒点清单】：按高压线/灰区可修/通过观察分级。每条必须包含：问题类型、原文短引或位置描述、是否需要打回、怎么改。\n"
            "3. 【资料库一致性】：核对人物、忍术、组织、尾兽、神器、原著事件是否违反 naruto_fanfic_db 的生死状态、秘密知情范围、前置条件、代价、限制和蝴蝶效应风险。\n"
            "4. 【节奏、场景链与字数】：判断正文主体是否约 4000-5000 字；新增字数是否用于事件链、场景因果、人物互动、画面推进，而不是设定水文或纯心理抒情。\n"
            "5. 【情绪呈现】：检查是否存在同一情绪无新事件支撑地反复重说、抽象心理空转、Tell 代替 Show；不要机械按词频判高压线。\n"
            "6. 【轻小说节奏】：检查是否由事件、互动、误会、选择推动情绪，情绪落点后是否进入下一个动作、对话、发现或关系变化。\n"
            "7. 【是否准许进入下一章】：是 / 否。若为否，列出必须先修的 1-5 项。\n\n"
            "【硬性审查项】\n"
            "- OOC：少量原著口头禅、称呼和角色喜剧化偏移允许存在；真正要打回的是底层动机断裂、机械口癖堆砌、为了衬托主角而强行降智或无脑黑原著人物。\n"
            "- 战力：严查无代价外挂、越级秒杀、查克拉消耗不成立、忍术前置条件缺失。\n"
            "- 信息呈现：严查超过三句话的设定说明文、百科式旁白、主角在心里背资料库。\n"
            "- 玩梗：人物关系梗、制度梗、误会梗、系统反差梗是本书资产；只有打断关键情绪、全员现代嘴替、同梗反复撑场时才判为问题。\n"
            "- 情绪：严查 Tell 代替 Show 和心理独白空转。抽象句不是一出现就违规，只有连续替代体验、压过事件推进时才打回。\n"
            "- 作者的话：与正文分开判断。作者的话允许轻度玩梗，但不能泄露未公开设定或破坏严肃章尾。\n\n"
            f"{outline_guard_context}\n\n"
            f"{db_context}\n\n"
            "【附：忍界铁律】\n"
            f"{self.load_iron_laws()}\n\n"
            "【待审正文】\n"
            f"{chapter_text}"
        )

    def audit_artifact_paths(self, chapter_num=None):
        gate_artifacts_dir = self.project_root / "04_editing" / "gate_artifacts"
        gate_artifacts_dir.mkdir(parents=True, exist_ok=True)

        if chapter_num:
            suffix = f"chapter_{chapter_num}"
            legacy_name = f"audit_chapter_{chapter_num}.md"
        else:
            suffix = "temp"
            legacy_name = "temp_audit_payload.md"
        return {
            "payload": gate_artifacts_dir / f"deepseek_audit_payload_{suffix}.md",
            "report": gate_artifacts_dir / f"deepseek_audit_report_{suffix}.md",
            "legacy_payload": gate_artifacts_dir / legacy_name,
        }

    def prepare_deepseek_audit(self, chapter_text, chapter_num=None):
        """
        生成 DeepSeek 审核投喂包，并保留旧 audit_chapter_*.md 文件名兼容旧流程。
        """
        print("=> [DeepSeek 暗部审核官] 准备毒点扫描投喂包...")
        audit_prompt = self.build_deepseek_audit_prompt(chapter_text, chapter_num)
        paths = self.audit_artifact_paths(chapter_num)

        paths["payload"].write_text(audit_prompt, encoding="utf-8")
        paths["legacy_payload"].write_text(audit_prompt, encoding="utf-8")

        print(f"   [OK] DeepSeek 审核包已写入: {paths['payload']}")
        print(f"   [兼容] 同步写入旧入口: {paths['legacy_payload']}")
        return {
            "prompt": audit_prompt,
            "payload_file": paths["payload"],
            "legacy_payload_file": paths["legacy_payload"],
            "report_file": paths["report"],
        }

    def prepare_deepseek_audit_prompt(self, chapter_text, chapter_num=None):
        return self.prepare_deepseek_audit(chapter_text, chapter_num)["prompt"]

    def prepare_anbu_audit(self, chapter_text, chapter_num=None):
        """
        兼容旧调用名：现在暗部审核默认交给 DeepSeek。
        """
        return self.prepare_deepseek_audit_prompt(chapter_text, chapter_num)

    def run_deepseek_audit(self, chapter_text, chapter_num=None, api_key=None, prompt_only=False, timeout=90):
        packet = self.prepare_deepseek_audit(chapter_text, chapter_num)
        if prompt_only:
            return {
                "status": "prompt_only",
                "message": "已生成 DeepSeek 审核投喂包，未调用外部 API。",
                **packet,
            }

        loaded_api_key = self.load_deepseek_api_key(api_key)
        if not loaded_api_key:
            return {
                "status": "missing_key",
                "message": "缺失 DEEPSEEK_API_KEY，已生成审核投喂包。请在项目根目录 .env 中配置后重试。",
                **packet,
            }

        try:
            max_tokens = int(os.environ.get("DEEPSEEK_AUDIT_MAX_TOKENS", "3500"))
        except ValueError:
            max_tokens = 3500

        system_prompt = (
            "你是严格但懂轻松向系统文的中文网文同人审稿编辑，负责火影同人章节的毒点、设定一致性、节奏和情绪呈现审核。"
            "你不续写正文，只给审稿结论。高压线问题必须打回，灰区问题给小修建议，不要把合理风格化偏移误判为毒点。"
        )
        answer, error = self.deepseek_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": packet["prompt"]},
            ],
            api_key=loaded_api_key,
            temperature=0.15,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        if error:
            return {
                "status": "error",
                "message": error,
                **packet,
            }

        packet["report_file"].write_text(answer, encoding="utf-8")
        print(f"   [OK] DeepSeek 审核报告已写入: {packet['report_file']}")
        return {
            "status": "ok",
            "message": "DeepSeek 暗部审核完成。",
            "report": answer,
            **packet,
        }


def read_text_arg(text=None, text_file=None):
    if text_file:
        return Path(text_file).read_text(encoding="utf-8")
    if text:
        return text
    raise ValueError("需要提供 --text/--beat 或对应的 --*-file")


def write_artifact(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def run_smoke(root="."):
    orchestrator = NarutoAuthorOrchestrator(project_root=root)
    test_beat = "主角在九尾之乱当晚，用三身术配合起爆符拖延面具男三秒，救下一名本该阵亡的暗部。"
    print(f"\n--- 测试生成写作包裹 (Project Root: {root}) ---")
    prompt = orchestrator.prepare_chapter_prompt(test_beat, chapter_num=1)
    print(f"   [OK] 写作包裹长度: {len(prompt)} 字符")

    print("\n--- 测试生成 DeepSeek 暗部审核包 ---")
    audit = orchestrator.build_deepseek_audit_prompt("测试正文：不自然口癖 dattebayo。", chapter_num=1)
    print(f"   [OK] 审核包裹长度: {len(audit)} 字符（未写入项目文件）")


def build_parser():
    parser = argparse.ArgumentParser(description="Naruto Author Orchestrator")
    parser.add_argument("--root", default=".", help="Project root directory")
    subparsers = parser.add_subparsers(dest="command")

    prompt_parser = subparsers.add_parser("prompt", help="根据 Beat Sheet 生成章节写作包")
    prompt_parser.add_argument("--chapter", type=int, default=1)
    prompt_parser.add_argument("--beat", help="Beat Sheet 文本")
    prompt_parser.add_argument("--beat-file", help="Beat Sheet 文件")
    prompt_parser.add_argument("--out", help="输出文件，默认写入 04_editing/gate_artifacts")

    context_parser = subparsers.add_parser("context", help="根据 Beat Sheet 生成资料库命中锚点")
    context_parser.add_argument("--beat", help="Beat Sheet 文本")
    context_parser.add_argument("--beat-file", help="Beat Sheet 文件")
    context_parser.add_argument("--limit", type=int, default=12, help="命中条目数量上限")

    audit_parser = subparsers.add_parser("audit", help="根据正文调用 DeepSeek 暗部审核")
    audit_parser.add_argument("--chapter", type=int)
    audit_parser.add_argument("--text", help="章节正文文本")
    audit_parser.add_argument("--chapter-file", help="章节正文文件")
    audit_parser.add_argument(
        "--mode",
        choices=["auto", "deepseek", "prompt"],
        default="auto",
        help="auto=有 key 就调用 DeepSeek，缺 key 则只生成投喂包；deepseek=必须调用 API；prompt=只生成投喂包",
    )
    audit_parser.add_argument("--timeout", type=int, default=90, help="DeepSeek API 超时时间（秒）")

    deepseek_parser = subparsers.add_parser("deepseek", help="调用 DeepSeek 情报顾问")
    deepseek_parser.add_argument("--query", help="质询内容")
    deepseek_parser.add_argument("--query-file", help="质询内容文件")

    subparsers.add_parser("smoke", help="运行最小自检")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    orchestrator = NarutoAuthorOrchestrator(project_root=args.root)

    if args.command in (None, "smoke"):
        run_smoke(args.root)
        return 0

    if args.command == "prompt":
        beat = read_text_arg(args.beat, args.beat_file)
        prompt = orchestrator.prepare_chapter_prompt(beat, args.chapter)
        out = Path(args.out) if args.out else Path(args.root) / "04_editing" / "gate_artifacts" / f"chapter_prompt_{args.chapter}.md"
        write_artifact(out, prompt)
        print(f"[OK] 已写入章节写作包: {out}")
        return 0

    if args.command == "context":
        beat = read_text_arg(args.beat, args.beat_file)
        print(orchestrator.build_db_context(beat, max_results=args.limit))
        return 0

    if args.command == "audit":
        chapter_text = read_text_arg(args.text, args.chapter_file)
        result = orchestrator.run_deepseek_audit(
            chapter_text,
            chapter_num=args.chapter,
            prompt_only=args.mode == "prompt",
            timeout=args.timeout,
        )
        print(f"[{result['status']}] {result['message']}")
        print(f"[payload] {result['payload_file']}")
        if result.get("legacy_payload_file"):
            print(f"[compat] {result['legacy_payload_file']}")
        if result["status"] == "ok":
            print(f"[report] {result['report_file']}")
            return 0
        if result["status"] == "missing_key" and args.mode == "auto":
            return 0
        if result["status"] == "prompt_only":
            return 0
        return 1

    if args.command == "deepseek":
        query = read_text_arg(args.query, args.query_file)
        print(orchestrator.deepseek_inquiry(query))
        return 0

    parser.error("未知命令")
    return 2


if __name__ == "__main__":
    configure_utf8_output()
    raise SystemExit(main())
