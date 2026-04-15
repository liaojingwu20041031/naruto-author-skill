# Claude Code / Codex 使用手册：火影长篇资料库

本项目的资料库位于：
`naruto_fanfic_db/`

资料库目标不是做百科搬运，而是给长篇同人创作提供可检索、可追踪、可审计的原著锚点和一致性约束。任何新增资料都必须服务于写作时的判断：这个角色现在能不能这样行动，这个术能不能这样用，这个原著节点被改动后后面哪里会崩。

## 必读文件顺序

Claude Code / Codex 或其他本地代码代理每次开始新会话、写新章、改大纲或做一致性审查时，按以下顺序读取：
1. `README.md`
2. `pre_main_timeline.json`
3. `canon_plot.json`
4. `world_background.json`
5. `characters.json`
6. `organizations.json`
7. `relations.json`
8. `jutsus.json`
9. `tailed_beasts.json`
10. `artifacts.json`
11. `data_quality_report.json`

如果后续初始化了长篇写作记忆，还必须额外读取：
`00_memory/novel_plan.md`
`00_memory/novel_state.md`
`00_memory/story_graph.json`

## 资料表职责
- `pre_main_timeline.json`：正篇前史时间线。写前传、宇智波政治线、晓起源等必读。
- `canon_plot.json`：原著正篇剧情锚点。
- `world_background.json`：世界观规则。
- `characters.json`：人物百科与长篇连续性索引。
- `organizations.json`：组织表。
- `relations.json`：有方向的关系图。
- `jutsus.json`：忍术/能力表。
- `tailed_beasts.json`：尾兽与人柱力表。
- `artifacts.json`：关键物品表。
- `data_quality_report.json`：数据清洗规则。

## 写作流程与一致性检查
写正文前必须回答：
- 角色现在是 alive、dead、sealed、incapacitated、edo_tensei，还是 missing？
- 他现在知道哪些秘密？不知道哪些秘密？
- 他当前阵营是什么？
- 他能否使用本章要出现的忍术？查克拉、伤势、冷却是否允许他这样打？
- 本章是否让某个原著事件失效？如果失效，后续谁来补位？

每章结束后必须更新 `00_memory/story_graph.json` 的相关状态。
