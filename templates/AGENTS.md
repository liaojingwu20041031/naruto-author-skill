# Naruto Author Agent Guide

本项目可由 Claude Code / Codex 或其他本地代码代理共同维护。所有代理都应把 `.claude/skills/naruto-author/` 当作 Naruto Author Skill 的源目录，把项目根目录下的 `naruto_fanfic_db/` 当作当前连载优先资料库。

## 自然语言触发

用户优先用中文自然语言表达意图，代理负责映射到底层脚本：

| 用户说法 | 执行动作 |
|---|---|
| “帮我打磨大纲”“优化主线”“这段大纲不对” | 运行 `outline_manager.py --root . propose --request "用户原话"`，生成八层改纲提案包，人工确认前不写回 |
| “改纲推演：如果让带土活下来”“推演纲手提前入场” | 生成改纲提案包，并输出原著锚点时间轴、势力响应树、场景链影响、下游剧情债 |
| “确认采用这个改纲”“按这个方案写入大纲” | 先按人工确认修改 `00_memory`，再运行 `outline_manager.py --root . record ...` |
| “查看剧情债”“现在大纲版本是多少” | 运行 `outline_manager.py --root . status`，并读取未关闭的 `downstream_obligations` |
| “继续写下一章”“续更”“写第 N 章” | 执行章节闭环，生成 Beat、写作包、正文和审核包 |
| “查一下神威”“这个忍术能这么用吗” | 运行 `query_db.py search` 或 `query_db.py mentions` |
| “审核这一章”“看看有没有毒点” | 运行 `orchestrator.py --root . audit --mode auto`，由 DeepSeek 优先生成毒点报告 |

原则：自然语言触发优先；命令行只是可审计的底层实现。

## 必用脚本

```bash
# 初始化项目骨架
python .claude/skills/naruto-author/scripts/init_project.py --root .

# 根据 Beat 自动命中人物、忍术、组织、忍具、尾兽和世界观规则
python .claude/skills/naruto-author/scripts/query_db.py mentions "本章 Beat 原文"

# 不确定关键词在哪张表时做跨表搜索
python .claude/skills/naruto-author/scripts/query_db.py search "关键词"

# 生成改纲提案包，人工确认后再记录改纲版本
python .claude/skills/naruto-author/scripts/outline_manager.py --root . propose --request "想打磨的大纲变动"
python .claude/skills/naruto-author/scripts/outline_manager.py --root . record --summary "改纲摘要" --request "人工确认说明" --obligation "后续剧情债" --target-volume "第一卷" --active-from-chapter 4 --due-chapter 6
python .claude/skills/naruto-author/scripts/outline_manager.py --root . scope-obligation --id "obligation_id" --target-volume "第二卷" --status deferred --nonblocking
python .claude/skills/naruto-author/scripts/outline_manager.py --root . status --chapter 4

# 生成带【资料库命中锚点】的章节写作包
python .claude/skills/naruto-author/scripts/orchestrator.py --root . prompt --chapter 1 --beat-file 04_editing/gate_artifacts/chapter_001_beat.md

# 调用 DeepSeek 暗部审核；无 key 时自动生成投喂包
python .claude/skills/naruto-author/scripts/orchestrator.py --root . audit --chapter 1 --chapter-file 03_manuscript/第001章_标题.md --mode auto

# 只生成 DeepSeek 审核投喂包，不调用 API
python .claude/skills/naruto-author/scripts/orchestrator.py --root . audit --chapter 1 --chapter-file 03_manuscript/第001章_标题.md --mode prompt

# 单章自动修稿最多 2 次，超过后停止并交给人工裁决
python .claude/skills/naruto-author/scripts/revision_loop.py --root . --chapter 1 status
python .claude/skills/naruto-author/scripts/revision_loop.py --root . --chapter 1 bump --reason "暗部审核打回后自动修稿"

# 检查 Skill 和资料库是否可用
python .claude/skills/naruto-author/scripts/smoke_test.py
```

## 工作规则

- 写正文前必须读取 `00_memory/novel_plan.md`、`00_memory/novel_state.md`、`00_memory/story_graph.json`。
- 人工打磨大纲必须先生成提案包；确认前不得写回正式记忆，确认后必须记录到 `00_memory/outline_changelog.md`。
- 大纲生成和改纲必须采用“时间线-势力-场景链”八层结构：核心摘要、原著切入、原著锚点时间轴、蝴蝶传播图、势力博弈图、三卷总纲、小篇章纲、场景链/连载节奏。
- 场景链优先于章号：规划时以幕/场景为最小推进单位，章节只是发布包装；不得用“第 N 章必须发生 X”的固定章号配额替代因果链。
- 每卷至少拆成 3-5 个小篇章；每个小篇章再拆成关键场景链，并标明目标、阻碍、误判、关系变化、结束状态和追更钩子。
- 每个重大变动必须同步推演反派响应树：最早察觉者、最快反应者、最可能误判者、最危险反制手段、反派智商在线时的下一步行动。
- 写新章前检查 `story_graph.json` 里的 `downstream_obligations`，只承接当前卷/当前章节已到期剧情债；未来卷、未到期或未归档剧情债不得强行提前兑现。
- 章节写作包里的【资料库命中锚点】必须优先于模型记忆；冲突时先改 Beat 或更新资料库，再重新生成写作包。
- 写作保持 4000-5000 字章节约束，扩写事件链、互动和场景，不靠纯心理独白凑字。
- 情绪表达遵守轻量规则：事件、互动、误会和选择推动情绪，用动作、物件、环境和对话潜台词承载，不机械数词频。
- 暗部审核优先交给 DeepSeek。Codex/Claude 负责调用脚本、读取报告和修稿，不默认承担整章长文本人工审稿。
- 每章 DeepSeek 审核通过后，更新 `00_memory` 中的生死状态、位置、查克拉/伤势、伏笔、秘密知情范围和蝴蝶效应。
- 自动修稿最多 2 次；两次后仍未通过，输出人工裁决清单，不继续重写。
