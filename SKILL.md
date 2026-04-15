---
name: naruto-author
description: 火影忍者同人长篇小说全流程创作技能。支持自然语言触发，例如“帮我打磨大纲”“改纲推演”“确认采用这个改纲”“查看剧情债”“继续写下一章”“查一下神威”“审核这一章”；用于开书初始化、人物卡、蝴蝶效应推演、资料库查询、章节续写、暗部审核、修稿和百万字连载一致性维护；适配轻松快乐向、二创向、系统文，重点防止角色底层动机断裂、战力崩坏、设定魔改、注水剧情、无脑黑原著、情绪空转和伏笔遗忘。
---

# Naruto Author - 火影同人长篇创作技能 v1.5.0

本 Skill 面向 **Claude Code / Codex / 其他本地代码代理** 通用。`.claude/commands/*.prompt` 是 Claude 风格快捷入口；Codex 或其他代理可直接读取 `AGENTS.md`，并调用 `scripts/` 下的同一套 Python 工具。

## 0. 自然语言优先触发

用户不需要记命令。只要用中文描述意图，代理应自动映射到底层脚本和工作流；只有在会写回正式记忆时才要求人工确认。

| 用户自然语言 | 应触发的流程 |
|---|---|
| “帮我打磨大纲”“优化主线”“这段大纲不对，帮我重构一下” | 读取 `00_memory`，运行 `outline_manager.py propose`，生成改纲提案包，不直接写回 |
| “改纲推演：如果让带土活下来”“推演纲手提前入场的影响” | 执行 `/改纲推演` 逻辑，列出失效原著锚点、人物动机变化和下游剧情债 |
| “确认采用这个改纲”“按这个方案写入大纲” | 先修改 `novel_plan.md` / `story_graph.json` / `novel_state.md`，再运行 `outline_manager.py record` 留痕 |
| “查看剧情债”“现在大纲版本是多少”“还有哪些改纲没偿还” | 运行 `outline_manager.py status`，必要时读取 `story_graph.json.downstream_obligations` |
| “继续写下一章”“续更”“按当前大纲写第 N 章” | 执行 `/继续连载` 闭环，生成 Beat、写作包、正文和审核包 |
| “查一下神威”“这个忍术能这么用吗”“第八班相关设定” | 使用 `query_db.py search` 或 `query_db.py mentions` |
| “审核这一章”“看看有没有毒点” | 运行 `orchestrator.py audit --mode auto`，由 DeepSeek 暗部审核官优先生成毒点报告 |

默认策略：自然语言触发优先；命令行只作为可审计、可复现的底层执行方式。

## ⚔️ 忍界铁律 (Style Guardrails)

本书是轻松快乐向、二创向、系统文。审核时守住底层逻辑，不把所有喜剧化偏移都判成毒点。详细标准以 `prompts/anti-patterns.md` 为准，摘要如下：

⛔ **第一铁律：守住角色根子，允许有限风格化**
- 禁的不是“偏”，而是角色底层欲望、长期执念、行为逻辑断裂，或为了服务主角而降智。
- 允许鸣人更会耍宝、卡卡西更黑色幽默、三代更像老油条管理者、佐助更早显出别扭、自来也保留好色取材外壳。
- 口头禅和称呼可以少量保留或中文化处理；毒点是机械堆砌罗马音/日式尾巴，或把角色写成单一标签。

⛔ **第二铁律：系统可以爽，但战力不能失控**
- 系统奖励可以离谱、反差可以好笑，但必须有条件、代价、冷却、误用风险或成长门槛。
- 外挂提供优势和新解法，不能代替查克拉基础、战斗经验、情报判断和现场选择。

⛔ **第三铁律：跨体系能力要接进忍界规则**
- 外来能力可以先用后解释，通过旁人观察、误判、研究和拆解分步揭示。
- 最终必须能与查克拉、自然能量、封印术、血继、忍具、灵魂或时空间规则接轨，不能无视忍界法则硬覆盖。

⛔ **第四铁律：每章必须有有效内容，不要求每章强推主线**
- 有效内容包括主线推进、关系变化、世界观信息自然揭示、伏笔埋设、角色形象强化、笑点与情感记忆点。
- 日常、小任务、误会、制度梗都允许，只要写完后留下变化或后续回收点。

⛔ **第五铁律：少讲说明书，多让信息从互动里长出来**
- 设定信息可以拆进对话、误会、战斗反馈、任务文书、暗部报告或系统提示。
- 不要连续贴百科式旁白，也不要让主角在心里背资料库。

⛔ **第六铁律：玩梗是资产，但必须从处境里长出来**
- 允许人物关系梗、制度梗、误会梗、信息差梗和主角内心现代吐槽。
- 禁止在生死场面硬插段子、让原著角色说现代网络流行语、或一章反复靠同一个梗撑场面。

⛔ **第七铁律：情绪轻量、具体、别空转**
- 情绪由事件、互动、误会和选择推动；少说抽象情绪，多写动作、物件、视线、停顿和对话潜台词。
- 不机械用“500 字几次”判高压线；真正要打回的是同一情绪无新事件支撑地反复重说。

## 1. 核心命令表

| 命令 | 功能描述 | 适用场景 |
|------|---------|---------|
| `/一键木叶` | 引导用户完成“开书五要素”，自动生成大纲锚点和初始知识图谱，并关联 `naruto_fanfic_db` 原著锚点。 | 第一次开项目 |
| `/忍界推演` | 根据主角设定，结合 `pre_main_timeline` 和 `canon_plot` 推演原著锚点、主角介入线、反派修正线。 | 确定大纲主线 |
| `/打磨大纲` | AI 生成“时间线-势力-场景链”八层改纲提案，人工打磨确认后再写回 `novel_plan.md`、`story_graph.json` 并记录版本。 | 人工精修主线、卷结构、人物关系 |
| `/改纲推演` | 推演某个剧情变动造成的蝴蝶效应、势力响应树、失效原著锚点和下游剧情债。 | 大幅偏离原著或重构主线前 |
| `/构建人物卡`| 严格根据战力铁律，并校验 `jutsus.json` 与 `characters.json`，生成主角或配角档案。 | 设计主角/配角 |
| `/查询资料库`| 快速检索 `naruto_fanfic_db` 数据库中的人物状态、忍术代价或崩溃风险。 | 写作遇到设定模糊时 |
| `/继续连载` | 自动执行单章生产闭环（检索 -> Beat生成 -> 正文撰写 -> 图谱回写）。 | 日常推进章节 |
| `/暗部审核` | DeepSeek 暗部审核官对当前章节进行毒点扫描（角色根子、战力溢出、资料库一致性、情绪空转、设定说明文检测）。 | 写完单章后强制执行 |
| `/幻术解除` | 修复未通过 `/暗部审核` 的章节，重新生成符合铁律的正文。 | 审核失败后 |

## 1.1 脚本工具入口

优先用脚本处理可重复、可审计的动作，避免每次靠口头记忆重写流程：

```bash
# 初始化项目骨架
python .claude/skills/naruto-author/scripts/init_project.py --root .

# 查询资料库
python .claude/skills/naruto-author/scripts/query_db.py risk "卡卡西"
python .claude/skills/naruto-author/scripts/query_db.py jutsu "螺旋丸"
python .claude/skills/naruto-author/scripts/query_db.py search "神威"
python .claude/skills/naruto-author/scripts/query_db.py mentions "鸣人在木叶学习螺旋丸并发现神威痕迹"

# 大纲打磨与改纲版本管理
python .claude/skills/naruto-author/scripts/outline_manager.py --root . propose --request "让纲手提前进入第一卷主线"
python .claude/skills/naruto-author/scripts/outline_manager.py --root . record --summary "纲手提前入场" --request "人工确认采用" --affected-characters "tsunade" --obligation "后续三章承接纲手第一印象" --target-volume "第一卷" --active-from-chapter 4 --due-chapter 6 --blocking
python .claude/skills/naruto-author/scripts/outline_manager.py --root . scope-obligation --id "obligation_id" --target-volume "第二卷" --status deferred --nonblocking
python .claude/skills/naruto-author/scripts/outline_manager.py --root . status --chapter 4

# 生成章节写作包与暗部审核包
python .claude/skills/naruto-author/scripts/orchestrator.py --root . prompt --chapter 12 --beat-file 04_editing/gate_artifacts/chapter_12_beat.md
python .claude/skills/naruto-author/scripts/orchestrator.py --root . context --beat-file 04_editing/gate_artifacts/chapter_12_beat.md
python .claude/skills/naruto-author/scripts/orchestrator.py --root . audit --chapter 12 --chapter-file 03_manuscript/第012章_标题.md --mode auto
python .claude/skills/naruto-author/scripts/orchestrator.py --root . audit --chapter 12 --chapter-file 03_manuscript/第012章_标题.md --mode prompt

# 单章自动修稿最多 2 次，超过后必须人工裁决
python .claude/skills/naruto-author/scripts/revision_loop.py --root . --chapter 12 status
python .claude/skills/naruto-author/scripts/revision_loop.py --root . --chapter 12 bump --reason "暗部审核打回后自动修稿"

# 检查 skill 框架是否仍可用
python .claude/skills/naruto-author/scripts/smoke_test.py
```

## 2. 三位一体创作流水线 (The Shinobi Editorial Team)

本技能采用严格的职责分离机制，确保文章逻辑严密且文笔地道：

1. **主笔作家 (Claude Code / Codex)**：
   - 每次写前必须加载并读取 `naruto_fanfic_db` 中的锚点文件（角色生死、忍术代价、尾兽状态）。
   - 负责宏观剧情把控、知识图谱（人物关系/时间线）维护。
   - 负责生成 **Beat Sheet (分镜头剧本)**，并**亲自撰写高质量的中文正文**。
   - 擅长画面感描写、高燃战斗分镜描写，彻底消除 AI 翻译腔。
2. **情报顾问 (DeepSeek API)**：
   - 专职“中文质询”与脑洞拓展，也是暗部审核的外部模型底座；质询是可选增强能力，审核是长章门禁优先路径。
   - 当遇到复杂的中文语境设定、忍术推演、或需要查阅模糊设定的资料时，可通过项目根目录 `.env` 中的 `DEEPSEEK_API_KEY` 调用 DeepSeek 进行快速质询和灵感发散。
   - `.env` 必须被 `.gitignore` 忽略；只提交 `.env.example` 模板。禁止把 API key 写入 Skill 文件、脚本、prompt 或正文产物。
   - 代码使用 `python-dotenv` 读取 `.env`。若环境缺少该库，先安装：`pip install python-dotenv`。
3. **DeepSeek 暗部审核官 (DeepSeek API)**：
   - 专职“毒点清道夫”与“设定校对”，用于替代 Codex/Claude 对 4000-5000 字长章的完整人工审稿，降低本地代理超时风险。
   - 通过 `orchestrator.py audit --mode auto` 调用：有 `DEEPSEEK_API_KEY` 时直接生成 `deepseek_audit_report_chapter_*.md`；没有 key 时生成 `deepseek_audit_payload_chapter_*.md`，供人工复制到 DeepSeek 或配置 key 后重跑。
   - 根据《忍界铁律》与 `naruto_fanfic_db` 原著库扫描正文。提前剧透带土身份、死人复活无逻辑、查克拉消耗不对、角色底层动机断裂、情绪空转压过事件推进、正文不足 4000-5000 字等属于高压线；口头禅略生硬、笑点略密等灰区只给小修建议。
   - Codex/Claude 只负责调度脚本、读取报告和执行修稿，不再默认承担整章长文本审核。
   - 自动修稿最多 2 次。两次后仍不通过，停止重写，输出人工裁决清单。

## 3. 300万字长篇核心架构 (Million-Word Engineering Architecture)

写几百万字的长篇，单纯靠 Prompt 绝对会崩盘。本技能复刻了顶级长篇流水线的**物理级持久化架构**。执行 `/一键木叶` 开书后，必须在当前目录下建立以下绝对结构：

```text
<project-root>/
  ├── 00_memory/                # 动态内存区（每章必读/必写，记录蝴蝶效应）
  │   ├── novel_plan.md         # 全局大纲与锚点进度条
  │   ├── novel_state.md        # 当前最新状态（时间、地点、主角查克拉/受伤状态）
  │   └── story_graph.json      # 知识图谱（记录人物生死、蝴蝶效应节点、忍术开发进度）
  │   └── outline_changelog.md  # 人工确认后的改纲版本记录
  ├── 03_manuscript/            # 小说正文区（第NNN章_标题.md）
  └── 04_editing/gate_artifacts/# 门禁产物区（记录每一章的五步质检报告）
  
# 静态原著数据库：
# - Skill 内置只读源：.claude/skills/naruto-author/naruto_fanfic_db/
# - /一键木叶 会复制一份到项目根目录 naruto_fanfic_db/，后续写作优先读项目副本，且初始化不会覆盖已存在文件。
```

## 4. 强制章节闭环：五步质量门禁 (The 5-Step Quality Gate)

单章写作绝不是“一键生成”，而是**多步流水线**。每次执行 `/继续连载`，必须严格按顺序执行以下子流程，任何一步失败，⛔ **绝对禁止进入下一章**：

- [ ] **0. `/大纲版本检查`**：写新章前检查 `outline_changelog.md` 与 `story_graph.json.downstream_obligations`。只处理当前卷/当前章节已经到期的剧情债；未来卷、未到期或未归档剧情债不得作为本章打回理由。
- [ ] **0.1 `/人工打磨大纲`**：任何主线、卷结构、人物关系、金手指限制或原著锚点的大改，都必须先生成改纲提案，人工确认后再写回正式记忆。禁止 AI 直接覆盖大纲。
- [ ] **0.2 `/剧情债范围标注`**：记录剧情债必须写明 `target_volume`、`active_from_chapter`、`due_chapter` 或 `status=deferred`。没有范围的旧债只作为待归档提醒，不是当前硬约束。
- [ ] **1. `/剧情检索 (RAG & DB Check)`**：写前必做。根据本章大纲，从 `00_memory` 检索当前状态，并从 `naruto_fanfic_db` 核对本章将出现的角色、忍术和物品是否越界。
- [ ] **1.1 `/资料库锚点注入`**：生成章节写作包时，`orchestrator.py prompt` 会自动把 Beat 与 `00_memory` 中命中的资料库记录插入【资料库命中锚点】。正文必须逐条遵守这些锚点；若未命中但本章涉及具体设定，先用 `query_db.py mentions` 或 `query_db.py search` 补查，改 Beat 后重跑写作包。
- [ ] **2. `/多步流水线写作`**：
  - 第一步：从当前小篇章与场景链生成 Beat Sheet (分镜头剧本)，不要用章号硬切代替因果链。
  - 第二步：扩写 Beat (加入火影本土化画面感、低密度情绪呈现与梗，保证 Show, Don't Tell)。
  - 第三步：串联合成 4000-5000 字正文。
- [ ] **3. `/更新记忆` ⚠️**：将本章发生的位置转移、生死判定、查克拉消耗、蝴蝶效应偏移分数提取，写入 `novel_state.md` 和 `story_graph.json`。
- [ ] **4. `/节奏、情绪呈现与一致性审查` ⛔**：核对大纲锚点与 DB 原著时间线。死人复活不符合原理、角色知晓了不该知道的情报（如过早得知黑绝）、角色底层动机断裂、情绪空转压过事件推进属于高压线；口头禅略生硬、笑点略密等灰区只给小修建议。
- [ ] **5. `/校稿与去AI化`**：消除翻译腔和生硬说教，并确立 `📝 作者的话` 互动玩梗区。若审核失败，最多自动修稿 2 次；超过后交给人工裁决。

## 5. 长篇大纲系统：时间线-势力-场景链 (Long-Form Outline Spine)

本 Skill 的大纲系统不以“第几章发生什么”为核心，而以 **原著锚点时间轴、势力响应、小篇章弧光、场景链因果** 为骨架。章节只是发布包装；幕/场景才是最小推进单位。

### 5.1 八层大纲输出结构

每次 `/忍界推演`、`/打磨大纲`、`/改纲推演` 必须按以下层级组织方案：

1. **核心故事摘要**：一句话主线、50 字摘要、200-300 字摘要、最终主题句。
2. **原著切入与变数定义**：精确切入节点、第一处违背原著的关键选择、主角优势/限制/最怕暴露的东西。
3. **原著锚点时间轴**：原著锚点、主角知道什么、能做什么、做了什么、没来得及做什么、发酵期、世界线偏移。
4. **蝴蝶效应传播图**：直接结果、延迟结果、谁受益、谁受损、谁起疑、谁误判、谁修正计划。
5. **势力博弈图与反派响应树**：木叶高层、宇智波、晓组织、黑绝/带土/斑、大蛇丸、外村必须同步推演。
6. **三卷总纲**：每卷写卷目标、卷对手、卷中段误判、卷中点逆转、卷末代价、卷后余波，并拆成 3-5 个小篇章。
7. **小篇章纲**：每个小篇章写起点状态、当段目标、升级冲突、中点反转、关系变化、阶段性得失、结束状态、收尾钩子。
8. **场景链/幕纲与连载节奏**：关键小篇章展开 8-15 个场景；每场写目的、人物、时空、行动、冲突、结果、下一场钩子，并标注爆点、伏笔、误导、反转、追更钩子和情绪承接点。

### 5.2 时间轴硬约束

- 火影同人必须同时维护三条线：**原著时间线锚点、主角介入线、反派修正线**。
- 所有重大事件必须落在明确时间锚点上，并标注与原著的偏离方式。
- 若某事件提前或推迟原著节点，必须说明原因、发酵期和后果。
- 不允许第一卷只改一个点、第二卷突然大偏离；中间必须有蝴蝶发酵链和势力响应链。

### 5.3 场景链优先于章号

- 规划时以“幕/场景”为最小推进单位，而非以章号硬切。
- 小篇章可使用 3-8 章弹性窗口，具体章数由事件复杂度、战斗长度、关系戏密度决定。
- 禁止写“第 N 章必须发生 X”的机械配额；只能写“在某个阶段性篇章窗口内完成对应功能”。
- 前一场的结果必须成为后一场的动机、压力、误判或行动条件。

### 5.4 情绪链嵌入场景卡

情绪弧线不能只当审查口号。每个关键场景必须显式给出：

- **触发事件**：角色看见、听见、失去或误判了什么。
- **外显反应**：身体动作、物件处理、停顿、视线、环境注意点或对话潜台词。
- **即时决定**：角色当场做了什么选择。
- **结果余波**：这个选择造成了什么新局面。
- **余震场景**：是否需要在下一场或后续小篇章承接。

### 5.5 反派响应树

每个重大变动必须同步生成反派与势力响应：

- 最直接受影响者。
- 最晚察觉者。
- 最快反应者。
- 最可能误判者。
- 最大的次生危机。
- 对主角最危险的反制手段。
- 若反派智商在线，下一步最合理行动。

### 5.6 连载节奏层

每个小篇章都要输出：

- 开局钩子。
- 中段黏性点。
- 至少两次局势升级。
- 一次误判或信息反转。
- 小高潮位置。
- 结尾悬念类型。
- 下一段最想看的问题。

连载钩子必须有信息量，服务场景因果链，不做无意义断章。
