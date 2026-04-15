# Naruto Author Skill

一个给本地 AI 写作代理使用的 **火影同人长篇创作 Skill**。

它不是“帮你随便起个爽文大纲”的小纸条，而是一套偏工程化的连载工作台：原著资料库、时间轴、势力响应、场景链、章节写作包、DeepSeek 暗部审核、改纲留痕、剧情债管理，都塞进来了。简单说，它负责在你想让忍界乱起来的时候，提醒你：带土、黑绝、团藏、大蛇丸也不是挂机 NPC。

> 非官方粉丝创作工具。本仓库不隶属于《火影忍者》版权方，只用于同人写作辅助、资料管理和创作流程自动化。

## 适合谁

- 想写几十万字、百万字级火影同人的作者。
- 想让蝴蝶效应真的发酵，而不是“主角救个人，世界线假装没看见”的作者。
- 想让 AI 帮忙续写，但又怕它写崩战力、人物动机、时间线和伏笔的作者。
- 喜欢轻松快乐向、系统文、二创梗，但不想牺牲忍界底层逻辑的作者。

## 它能做什么

- **长篇大纲生成**：按“摘要 -> 原著锚点时间轴 -> 蝴蝶传播 -> 势力博弈 -> 三卷总纲 -> 小篇章 -> 场景链 -> 连载节奏”八层结构规划。
- **改纲推演**：任何重大变动都先生成提案包，人工确认前不写回正式记忆。
- **反派响应树**：每次蝴蝶效应都同步推演木叶高层、宇智波、晓、黑绝/带土/斑、大蛇丸和外村的反应。
- **资料库检索**：内置人物、忍术、组织、原著剧情、忍具、尾兽和世界观规则数据。
- **章节写作包**：根据 Beat 自动注入资料库命中锚点，提醒写作代理守住设定、代价和秘密知情范围。
- **暗部审核**：优先调用 DeepSeek 做毒点扫描；没有 key 时自动生成可复制投喂包。
- **修稿刹车**：单章自动修稿最多 2 次，超过后交给人工裁决，防止 AI 在幻术里越修越偏。

## 目录结构

```text
naruto-author-skill/
  SKILL.md                         # Skill 主说明与触发规则
  README.md                        # 你正在看的说明书
  .claude/commands/                # Claude/Codex 可用的命令入口 prompt
  naruto_fanfic_db/                # 火影同人静态资料库
  prompts/                         # 大纲、人物卡、审核等提示词
  references/                      # 连贯性、钩子、质量清单等参考规则
  scripts/                         # 初始化、检索、写作包、审核、改纲管理脚本
  templates/                       # 新项目初始化模板
```

## 快速安装

把本仓库放到你的本地 skills 目录，或直接复制到项目的 `.claude/skills/naruto-author/`。

示例：

```bash
git clone https://github.com/liaojingwu20041031/naruto-author-skill.git .claude/skills/naruto-author
```

然后在你的小说项目根目录运行：

```bash
python .claude/skills/naruto-author/scripts/init_project.py --root .
```

初始化后会生成：

```text
00_memory/                 # 动态记忆：大纲、状态、知识图谱、改纲记录
03_manuscript/             # 正文目录
04_editing/gate_artifacts/ # 写作包、审核包、提案包等门禁产物
naruto_fanfic_db/          # 项目副本资料库，优先于 skill 内置库
AGENTS.md                  # 给 Codex / Claude Code 等代理看的项目规则
```

## 常用自然语言触发

你不需要记命令。直接对代理说中文即可：

| 你说 | Skill 应该做 |
|---|---|
| “帮我打磨大纲” | 生成八层改纲提案包，人工确认前不写回 |
| “改纲推演：如果让带土活下来” | 输出原著锚点、势力响应、场景链影响和剧情债 |
| “确认采用这个改纲” | 写回 `00_memory` 并记录到 `outline_changelog.md` |
| “查看剧情债” | 检查当前大纲版本和未关闭剧情债 |
| “查一下神威” | 检索资料库设定、代价和风险 |
| “继续写下一章” | 生成 Beat、写作包、正文与审核包 |
| “审核这一章” | 调用 DeepSeek 暗部审核，或生成投喂包 |

## 常用脚本

```bash
# 初始化项目骨架
python .claude/skills/naruto-author/scripts/init_project.py --root .

# 跨资料库搜索
python .claude/skills/naruto-author/scripts/query_db.py search "神威"

# 根据 Beat 命中人物、忍术、组织、忍具、尾兽和世界观规则
python .claude/skills/naruto-author/scripts/query_db.py mentions "鸣人学习螺旋丸，却发现神威痕迹"

# 生成改纲提案包，不修改正式大纲
python .claude/skills/naruto-author/scripts/outline_manager.py --root . propose --request "让纲手提前进入第一卷主线"

# 查看当前剧情债
python .claude/skills/naruto-author/scripts/outline_manager.py --root . status --chapter 4

# 生成章节写作包
python .claude/skills/naruto-author/scripts/orchestrator.py --root . prompt --chapter 1 --beat-file 04_editing/gate_artifacts/chapter_001_beat.md

# 生成或调用 DeepSeek 审核
python .claude/skills/naruto-author/scripts/orchestrator.py --root . audit --chapter 1 --chapter-file 03_manuscript/第001章_标题.md --mode auto

# 自检 skill
python .claude/skills/naruto-author/scripts/smoke_test.py
```

## 大纲系统：不是卷纲，是忍界连锁反应

这个 Skill 的核心变化是：**场景链优先于章号**。

旧式提纲经常写成：

```text
第一卷：起步
第二卷：变强
第三卷：决战
```

然后 AI 就开始原地结印、一路莽到终局。

这里改成八层：

1. 核心故事摘要。
2. 原著切入与变数定义。
3. 原著锚点时间轴。
4. 蝴蝶效应传播图。
5. 势力博弈图与反派响应树。
6. 三卷总纲。
7. 小篇章纲。
8. 场景链 / 幕纲与连载节奏。

也就是说，主角救下一个人，不只是“剧情变爽了”，还要回答：

- 谁最早发现不对？
- 谁会误判？
- 团藏会不会换切入手段？
- 带土会不会改代理方案？
- 黑绝会不会判断这是否影响月之眼？
- 这个变动几天、几月、几年后才爆？
- 前一场的结果怎么变成下一场的动机？

忍界可以乱，但不能糊。

## DeepSeek 暗部审核

如果项目根目录 `.env` 里配置了：

```env
DEEPSEEK_API_KEY="你的 key"
```

`orchestrator.py audit --mode auto` 会优先调用 DeepSeek 生成审核报告。

没有 key 也没关系，Skill 会生成 `deepseek_audit_payload_chapter_*.md`，你可以手动复制给 DeepSeek。

`.env` 必须放进 `.gitignore`，不要把 API key 写进 prompt、脚本、README 或正文产物。

## 设计原则

- 原著资料库命中锚点优先于模型记忆。
- 主角可以爽，但战力必须有代价、冷却、限制或成长门槛。
- 喜剧和玩梗要从处境里长出来，不能让全员变成现代嘴替。
- 情绪用事件、动作、物件、停顿和对话潜台词承载，不靠抽象心理独白灌水。
- 改纲必须先提案，人工确认后再写回。
- 反派必须在线。忍界不是单机游戏。

## 免责声明

本项目仅用于同人创作辅助和本地写作流程自动化。请尊重原作版权，不要把资料库内容包装成官方设定发布。真正的好故事仍然需要作者判断、取舍和最后一刀。

愿你的时间线能偏，但别断。
