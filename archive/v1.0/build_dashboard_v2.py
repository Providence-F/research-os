#!/usr/bin/env python3
"""Research OS Dashboard v2.0 Generator.

Outputs a single self-contained HTML file with Bento grid layout.
Spec: docs/superpowers/specs/2026-07-04-research-os-dashboard-redesign-design.md
"""

from __future__ import annotations
from pathlib import Path


# ============================================================
# §0 数据常量
# ============================================================

VERSIONS = [
    {"id": "v0.1", "date": "06-22", "problem": "需要一个调研脚手架",
     "iter": "Dify 时代，5 模板 + 基础 CLI + 4 深度档位",
     "unlock": "R0-R3 深度体系建立"},
    {"id": "v0.2", "date": "06-24", "problem": "缺少视图模型",
     "iter": "引入 09-可视化视图模型.md v0.2",
     "unlock": "调研产物可被结构化呈现"},
    {"id": "v0.3", "date": "06-25", "problem": "状态机散乱",
     "iter": "research_status / planner / validator v0.3 + 候选池/假设账本模板",
     "unlock": "流程可追踪"},
    {"id": "v0.4", "date": "06-26", "problem": "缺执行规范",
     "iter": "14-研究执行状态机.md v0.4（12 步线性）+ 结论溯源清单",
     "unlock": "12 步流程明确化"},
    {"id": "v0.7", "date": "06-30", "problem": "缺迭代追踪",
     "iter": "research_planner / validator / goal_tracker / iteration_log v0.7",
     "unlock": "目标可追踪 + 迭代可记录"},
    {"id": "v0.8", "date": "07-01", "problem": "HTML 输出丑",
     "iter": "build_research_html.py CSS v0.8（Anthropic cream + Lora + Starlight asides）",
     "unlock": "Anthropic 美学确立"},
    {"id": "v0.9", "date": "07-02", "problem": "意图探索不足",
     "iter": "intent_discovery.py v0.9 + research_router.py v0.9 + 假设账本融入 ljg-think drill_down",
     "unlock": "意图可探索 + 路由智能化"},
    {"id": "v0.10", "date": "07-03", "problem": "缺读者视角验证",
     "iter": "reader_simulation.py 写-读-改闭环 + 5 幕叙事 + concept_ladder + CSS v0.10",
     "unlock": "写-读-改闭环确立（核心创新）"},
    {"id": "v0.5", "date": "07-04", "problem": "版本号碎片化",
     "iter": "统一版本号 + 15 步状态机 + 3 人工确认点 + HTML 美学规范独立文档 + archive 归档",
     "unlock": "版本一致性 + 工程化成熟"},
]

WORKFLOW = [
    {"step": 0, "name": "scaffold", "stage": "防方向错", "output": "项目目录 + 14 模板", "human_confirm": False},
    {"step": 1, "name": "route", "stage": "防方向错", "output": "route_result + intent_doc", "human_confirm": False},
    {"step": 2, "name": "task_card", "stage": "防方向错", "output": "task-card.md", "human_confirm": True},
    {"step": 3, "name": "research_plan", "stage": "防方向错", "output": "research-plan.md", "human_confirm": True},
    {"step": 4, "name": "candidates", "stage": "收集证据", "output": "candidates.md + discarded.md", "human_confirm": False},
    {"step": 5, "name": "evidence", "stage": "收集证据", "output": "evidence_matrix.md", "human_confirm": False},
    {"step": 6, "name": "hypothesize", "stage": "收集证据", "output": "hypothesis_ledger.json + conflicts.md", "human_confirm": False},
    {"step": 7, "name": "analysis", "stage": "收集证据", "output": "05-analysis/*.md", "human_confirm": False},
    {"step": 8, "name": "red_team", "stage": "收集证据", "output": "red_team.md（至少 1 次降级）", "human_confirm": False},
    {"step": 9, "name": "report_draft", "stage": "读者读懂", "output": "final-report.md（草稿）", "human_confirm": False},
    {"step": 10, "name": "reader_simulation", "stage": "读者读懂", "output": "final-report.md（重写后）⭐ 写-读-改闭环", "human_confirm": False},
    {"step": 11, "name": "trace_manifest", "stage": "读者读懂", "output": "trace-manifest.json", "human_confirm": False},
    {"step": 12, "name": "view_model", "stage": "读者读懂", "output": "view-model.json", "human_confirm": False},
    {"step": 13, "name": "html_build", "stage": "读者读懂", "output": "08-html/index.html", "human_confirm": True},
    {"step": 14, "name": "validate", "stage": "读者读懂", "output": "validator 报告", "human_confirm": False},
    {"step": 15, "name": "publish", "stage": "读者读懂", "output": "09-publish/ + 桌面副本", "human_confirm": False},
]

STAGES = [
    {"name": "防方向错", "range": "step 0-3", "items": ["地基", "罗盘", "任务卡", "蓝图"]},
    {"name": "收集证据", "range": "step 4-8", "items": ["漏斗", "天平", "账本", "多Agent", "盾牌"]},
    {"name": "读者读懂", "range": "step 9-15", "items": ["草稿", "镜子", "溯源", "JSON", "HTML", "章", "发布"]},
]

PHILOSOPHY = [
    {
        "num": "01",
        "title": "目标在调研过程中\"长出来\"",
        "claim": "传统调研是\"先定题目，再找答案\"。这套系统拒绝这个前提——真实的调研里，你往往调到一半才发现自己问错了问题。系统承认这件事，并把它写进了工作流。",
        "why": "人做调研最大的浪费，不是\"找不到答案\"，而是\"答完了才发现问错了\"。一份目标冻结在开头的调研，到结尾大概率已经偏离了真实需求——因为调研本身就是会改变你认知的过程。如果你一开始就把目标锁死，调研就成了\"为初始假设找证据\"，本质是合理化。但反过来，目标也不能随便漂——漂就成了没有方向的乱翻。所以系统做的是一个折中：目标可以被改，但每次改必须有理由、有痕迹、有人把关，且最多改 3 次。",
        "code": [
            "每个项目有一份目标账本（goal_ledger.json），记录当前目标 + 全部历史修改记录 + 等待处理的修改建议",
            "系统主动扫描三类信号提示目标漂移：反方审计出现\"自我合理化\"攻击 / 多个假设被反复修订 / 目标范围广但证据太少",
            "调整建议不会自动生效，必须显式接受或拒绝；MAX_GOAL_REVISIONS=3，超过 3 次就停止",
            "目标改了之后，旧目标写进 goal_history，不是删除——你可以回看\"我是怎么走到这里的\"",
        ],
        "source": "goal_tracker.py（MAX_GOAL_REVISIONS=3，三类 drift 信号检测，goal_history 不可删除）；00-使用说明.md 步骤 5「目标账本」",
        "highlight": False,
    },
    {
        "num": "02",
        "title": "最终产物是\"给读者看的东西\"",
        "claim": "调研分两层——中间过程是为了让结论站得住脚（给作者自己看的），最终报告是为了让读者读懂（给别人看的）。两层不能混着用，且最终产物必须以\"读者能不能读懂\"为唯一验收标准。",
        "why": "写报告的人天然有一个盲区——你做完了调研，脑子里装着全部上下文，你以为\"这段写得很清楚\"，其实读者根本跟不上你的跳跃。这个盲区无法靠作者自己审稿解决，因为作者永远无法\"忘记自己知道的东西\"。这套系统的解法是：让 AI 来扮演读者。写完之后，AI 切换身份去读，逐段反馈\"哪里没懂、哪里卡住、哪里术语没解释\"，然后写的人（也是 AI）再改。最多两轮，第三轮还不行就交还给人。",
        "code": [
            "报告生成有写-读-改强制循环：写完初稿 → AI 扮演读者逐段读 → 不通过的段落打回重写 → 再读 → 通过才交付",
            "每段读者诊断包含：读懂度分数、读者复述（验证真的读懂了）、卡点位置、改写建议",
            "报告结构强制用 5 幕叙事（问题/探索/冲突/决策/行动），不允许 §1-§7 的并列堆砌",
            "幕后信息会被自动过滤掉——证据编号、假设编号、schema 版本号这些内部术语不该出现在读者视图",
            "内部文件（证据矩阵、假设账本、反方审计）和最终报告是两套产物，前者服务可信度，后者服务读者",
        ],
        "source": "reader_simulation.py（reader persona 逐段诊断 + 读懂度评分 + 2 轮重写上限）；final_report_writer.py（5 幕叙事 + 写-读-改闭环）",
        "highlight": False,
    },
    {
        "num": "03",
        "title": "意图是\"挖出来的\"，不是\"问出来的\"",
        "claim": "用户嘴上说要调研的东西，往往不是他真正需要的东西。系统不直接接受用户的表面需求，而是花 3 轮探索去挖出真实意图。这一条是整套设计哲学里最区别于普通调研工具的地方，也是系统最有灵气的部分。",
        "why": "人提需求的时候，会说一个\"我能想到的版本\"，但真正想解决的问题往往藏在更深处。直接拿表面需求去跑调研，结果就是答得很认真，但答的不是真问题。这种\"嘴上说的 vs 实际要的\"差距，用户自己看不出来——需要外部视角去挖。系统把这件事做成 3 轮结构化探索：先记下嘴上说的，再主动挖差距，最后固化成可验证、可批评的问题说明书。",
        "code": [
            "Round 1 · 宽泛探索：把用户嘴上说的需求原样记下来，不做任何判断。这一步建立\"对照组\"——后续挖出来的差距，要跟这个对比",
            "Round 2 · 挖差距：基于 Round 1 主动问三个问题——\"嘴上说要 X，实际可能要 Y 为什么\" / \"有没有 X 本身就是目的的情况\" / \"这个调研的真实成本，不做会损失什么\"",
            "Round 3 · 固化成问题说明书：把探索结果固化成 AI 能解、可验证、可批评的问题。三个验收维度：可验证（怎么检查被答了）/ 可批评（什么证据能推翻前提）/ AI 可解",
            "交叉验证：Round 2 会读取用户画像里的判断模式；调研结束后比对 stated_intent vs resolved_intent 记录差距（intent_evolution）；这个差距记录会被下次调研读取——下次类似主题，系统会主动提议\"要不要先做个 L1 草稿\"",
            "每轮探索记录存到 exploration_history 字段，让意图形成过程可审计——不是黑盒一次性输出",
        ],
        "source": "intent_discovery.py（3 轮探索 + exploration_history 可审计 + 跨项目 intent_evolution）；profile_updater.py（stated_intent vs resolved_intent 差距记录 + 反哺下次调研）",
        "highlight": True,
    },
    {
        "num": "04",
        "title": "系统会从每次调研中\"学到东西\"",
        "claim": "调研系统不是一次性工具。每次调研完成后，系统会主动复盘这次\"用户真正解决了什么\"\"展现了什么判断倾向\"\"留下了什么没解决的问题\"\"有什么方法论可以跨项目复用\"，把这些写回长期记忆，影响下一次调研的起点。",
        "why": "普通调研工具的痛点是——你调了 10 次调研，但每次都从零开始。这次踩的坑、发现的模式、留下的未解问题，下次完全不记得。等于每次都在重置自己。这套系统拒绝这个前提。调研过程产出的不只是\"报告\"，还有\"对用户的理解\"——用户的判断模式是什么、这次没解决什么、什么洞察可以跨项目复用。这些是比报告本身更值钱的资产，因为报告服务一次决策，而\"对用户的理解\"服务所有未来的调研。",
        "code": [
            "调研完成且校验通过后，触发画像回写：读取完整产出（证据/假设/反方/最终报告/意图文档+修订记录），调 LLM 提取 4 类信息",
            "写回 3 份文件：user_profile.json（判断模式、未解种子、领域偏好）/ project_index.json（resolved_intent + 完成日期）/ insight_memory.json（跨项目可复用洞察，上限 50 条）",
            "硬规则：resolved_intent 必须基于真实调研产出，不是任务卡里写的\"想解决什么\"；judgment_patterns 是稳定判断倾向，不是这次具体结论；unresolved_seeds 是这次没解决、下次可继续挖的；信息不足时输出空数组，不硬编",
            "身份贯穿 3 维度：求职故事（这次调研能不能成为面试时的\"我做过 X\"案例）/ 产品启发（对用户当前产品组合的启发）/ 赛道修正（是否修正了用户对某条赛道的判断）——无关就写\"无关\"，不硬编",
            "下次 ros new 时，intent_discovery 会读取这些记忆——上次留下的未解种子会主动浮出来，问\"要不要继续挖\"",
        ],
        "source": "profile_updater.py（4 类信息提取 + 3 份记忆文件写回 + 身份贯穿 3 维度）；intent_discovery.py（下次调研读取历史未解种子）",
        "highlight": False,
    },
]

PROJECTS = [
    {"name": "AWS-Top20-求职路径", "version": "v0.9", "category": "company-jd", "status": "completed",
     "summary_cards": [
         {"title": "AWS 云服务核心栈", "related": ["职业路径选择"]},
         {"title": "Top20 公司筛选", "related": ["AWS 云服务核心栈"]},
         {"title": "职业路径选择", "related": []},
     ]},
    {"name": "MizzenAI 产品拆解", "version": "v0.9", "category": "product", "status": "completed",
     "summary_cards": [
         {"title": "产品定位", "related": ["用户访谈方法论"]},
         {"title": "用户访谈方法论", "related": []},
         {"title": "竞品对比", "related": ["产品定位"]},
     ]},
    {"name": "知识塔罗定位", "version": "v0.8", "category": "product", "status": "completed",
     "summary_cards": [
         {"title": "用户画像", "related": []},
         {"title": "定价策略", "related": ["用户画像"]},
     ]},
    {"name": "Research-OS-自我审计", "version": "v0.10", "category": "topic", "status": "completed",
     "summary_cards": [
         {"title": "工作流完整性", "related": ["读者模拟有效性"]},
         {"title": "读者模拟有效性", "related": []},
     ]},
    {"name": "Anthropic-美学-研究", "version": "v0.10", "category": "topic", "status": "completed",
     "summary_cards": [
         {"title": "配色规范", "related": ["字体选择"]},
         {"title": "字体选择", "related": []},
         {"title": "简笔画物件", "related": ["配色规范"]},
     ]},
    {"name": "芯片-第一性原理", "version": "v0.7", "category": "topic", "status": "completed",
     "summary_cards": [
         {"title": "制程工艺", "related": ["性能功耗权衡"]},
         {"title": "性能功耗权衡", "related": []},
     ]},
    {"name": "用户访谈方法论", "version": "v0.10", "category": "user-research", "status": "completed",
     "summary_cards": [
         {"title": "访谈大纲设计", "related": ["用户画像"]},
         {"title": "用户画像", "related": []},
     ]},
    {"name": "AI 调研工具横向对比", "version": "v0.9", "category": "competitor", "status": "completed",
     "summary_cards": [
         {"title": "GPT Researcher", "related": ["Deep Research"]},
         {"title": "Deep Research", "related": []},
         {"title": "Perplexity", "related": ["GPT Researcher"]},
     ]},
    {"name": "Agent 集群研究", "version": "v0.10", "category": "industry", "status": "failed",
     "summary_cards": [
         {"title": "Kimi Agent", "related": []},
         {"title": "Claude Code", "related": ["Kimi Agent"]},
     ]},
    {"name": "一人公司可行路径", "version": "v0.8", "category": "industry", "status": "failed",
     "summary_cards": [
         {"title": "赛道选择", "related": []},
     ]},
    {"name": "RAG 系统设计参考", "version": "v0.5", "category": "topic", "status": "failed",
     "summary_cards": [
         {"title": "向量数据库对比", "related": []},
     ]},
    {"name": "产品组合优化", "version": "v0.5", "category": "portfolio", "status": "planned",
     "summary_cards": [
         {"title": "知识塔罗 + Research OS", "related": []},
     ]},
    {"name": "秋招时间线规划", "version": "v0.5", "category": "mixed", "status": "planned",
     "summary_cards": [
         {"title": "面试准备节奏", "related": []},
     ]},
    {"name": "Obsidian 工作流迁移", "version": "v0.5", "category": "topic", "status": "planned",
     "summary_cards": [
         {"title": "知识库结构", "related": []},
     ]},
]

STATS = {"projects": 14, "versions": 9, "modules": 27, "completed": 8}


# ============================================================
# §1 CSS
# ============================================================

CSS = """
:root {
  --bg: #faf9f5;
  --bg-warm: #f4f1e8;
  --surface: #ffffff;
  --text: #141413;
  --text-secondary: #5c5c5c;
  --text-tertiary: #b0aea5;
  --accent: #d97757;
  --accent-deep: #a04e32;
  --accent-light: #f4e4de;
  --blue: #6a9bcc;
  --green: #788c5d;
  --red: #c62828;
  --border: #e8e6dc;
  --shadow: 0 4px 12px rgba(60,40,20,0.06);
  --transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1),
                opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, "Poppins", "Lora", "Noto Sans SC", "PingFang SC", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  padding: 32px;
  -webkit-font-smoothing: antialiased;
}
.dashboard {
  max-width: 1440px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.module {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow);
  transition: var(--transition);
  will-change: transform, opacity;
  cursor: default;
}
.module.expanded {
  grid-column: span 3;
  grid-row: span 2;
}
.module.compressed {
  opacity: 0.55;
  transform: scale(0.97);
}
.m1 { grid-column: span 3; cursor: default; }
.m2 { grid-column: span 2; cursor: pointer; }
.m6 { grid-column: span 1; cursor: pointer; }
.m3, .m4, .m5 { grid-column: span 1; cursor: pointer; }
@media (max-width: 1440px) {
  .dashboard { grid-template-columns: repeat(2, 1fr); }
  .m1, .module.expanded { grid-column: span 2; }
}
@media (max-width: 768px) {
  .dashboard { grid-template-columns: 1fr; }
  .module { grid-column: span 1 !important; }
}

/* M1 */
.m1 { padding: 32px; }
.m1-header { display: flex; align-items: center; gap: 20px; }
.m1-title h1 {
  font-family: "Poppins", sans-serif;
  font-size: 32px; font-weight: 600;
  color: var(--text); letter-spacing: -0.02em;
}
.m1-tagline {
  font-family: "Lora", serif;
  color: var(--text-secondary); font-size: 16px;
}
.m1-version-badge {
  margin-left: auto;
  background: var(--accent); color: white;
  padding: 4px 12px; border-radius: 12px;
  font-size: 13px; font-weight: 500;
}
.m1-stats {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 24px; margin-top: 32px; padding-top: 24px;
  border-top: 1px solid var(--border);
}
.stat { text-align: center; }
.stat-num {
  display: block; font-family: "Poppins", sans-serif;
  font-size: 32px; font-weight: 600; color: var(--accent);
}
.stat-label { color: var(--text-tertiary); font-size: 13px; }

/* M2 */
.m2 { padding: 32px; }
.module-title {
  font-family: "Poppins", sans-serif;
  font-size: 22px; font-weight: 600; color: var(--text);
}
.module-subtitle {
  color: var(--text-secondary); font-size: 14px; margin-top: 4px;
}
.version-timeline { margin-top: 32px; position: relative; padding: 0 16px; }
.version-line {
  position: absolute; top: 20px; left: 16px; right: 16px;
  height: 2px; background: var(--border);
}
.version-nodes {
  display: flex; justify-content: space-between; position: relative;
}
.version-node {
  background: var(--surface); border: 2px solid var(--border);
  border-radius: 50%; width: 48px; height: 48px;
  cursor: pointer; transition: var(--transition);
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; padding: 0; position: relative;
}
.version-node:hover, .version-node.active {
  border-color: var(--accent);
  box-shadow: 0 0 0 6px var(--accent-light);
}
.version-node .v-id {
  font-size: 11px; font-weight: 600; color: var(--text);
  font-family: "Poppins", sans-serif;
}
.version-node .v-date {
  font-size: 8px; color: var(--text-tertiary);
}
.version-panels { margin-top: 24px; min-height: 120px; }
.version-panel {
  display: none; gap: 16px;
  background: var(--bg-warm); padding: 16px;
  border-radius: 12px; border-left: 3px solid var(--accent);
}
.version-panel.active { display: grid; grid-template-columns: repeat(3, 1fr); }
.panel-col .panel-label {
  font-size: 11px; color: var(--text-tertiary);
  text-transform: uppercase; letter-spacing: 0.05em;
  font-family: "Poppins", sans-serif; font-weight: 500;
}
.panel-col .panel-text { font-size: 14px; color: var(--text); margin-top: 4px; }

/* M3 */
.m3 { padding: 32px; }
.matrix-wrap { overflow-x: auto; margin-top: 16px; }
.matrix {
  width: 100%; border-collapse: collapse; font-size: 13px;
}
.matrix th, .matrix td {
  border: 1px solid var(--border); padding: 8px;
  text-align: center; min-width: 80px; min-height: 50px;
}
.matrix th {
  background: var(--bg-warm); font-weight: 500;
  color: var(--text-secondary); font-family: "Poppins", sans-serif;
}
.matrix .row-head { text-align: left; font-size: 12px; padding-left: 12px; }
.matrix td.empty { background: var(--bg-warm); opacity: 0.3; }
.proj-chip {
  display: inline-block; background: var(--surface);
  border: 1px solid var(--border); border-radius: 6px;
  padding: 3px 10px; font-size: 11px; cursor: pointer;
  transition: var(--transition); margin: 2px;
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.proj-chip:hover { border-color: var(--accent); transform: translateY(-1px); }
.proj-chip.completed { border-style: solid; border-color: var(--green); color: var(--green); }
.proj-chip.failed { border-style: dashed; border-color: var(--red); color: var(--red); }
.proj-chip.planned { border-style: dotted; color: var(--text-secondary); }
.node-graph {
  margin-top: 24px; padding: 16px;
  background: var(--bg-warm); border-radius: 12px;
  display: none;
}
.node-graph svg { display: block; margin: 0 auto; }
.node-graph .graph-title {
  font-family: "Poppins", sans-serif;
  font-size: 14px; font-weight: 500; color: var(--text);
  margin-bottom: 8px;
}
.node-circle {
  fill: var(--accent); opacity: 0.85; cursor: drag;
  transition: r 0.2s;
}
.node-circle:hover { opacity: 1; }
.node-text {
  font-size: 11px; fill: var(--text);
  text-anchor: middle; pointer-events: none;
  font-family: -apple-system, "PingFang SC", sans-serif;
}
.node-link {
  stroke: var(--border); stroke-width: 1.5;
  opacity: 0.6;
}

/* M4 */
.m4 { padding: 32px; }
.workflow-stages {
  display: grid; grid-template-columns: repeat(3, 1fr);
  gap: 16px; margin-top: 24px;
}
.workflow-stage {
  background: var(--bg-warm); padding: 20px;
  border-radius: 12px; text-align: center;
}
.stage-name {
  font-family: "Poppins", sans-serif;
  font-size: 16px; font-weight: 600; color: var(--accent);
}
.stage-range {
  font-size: 11px; color: var(--text-tertiary);
  margin-top: 4px; font-family: monospace;
}
.stage-objects {
  display: flex; flex-wrap: wrap; justify-content: center;
  gap: 12px; margin-top: 16px;
}
.workflow-object {
  cursor: pointer; transition: var(--transition);
  display: flex; flex-direction: column; align-items: center;
}
.workflow-object:hover { transform: translateY(-3px); }
.workflow-object svg { display: block; }
.object-label {
  display: block; font-size: 11px;
  color: var(--text-secondary); margin-top: 4px;
}
.stage-steps {
  display: flex; gap: 4px; justify-content: center;
  flex-wrap: wrap; margin-top: 12px; padding-top: 12px;
  border-top: 1px solid var(--border);
}
.step-num {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 4px; padding: 2px 6px;
  font-size: 10px; color: var(--text-tertiary);
  font-family: monospace;
}
.step-num.human-confirm {
  background: var(--accent-light); border-color: var(--accent);
  color: var(--accent-deep); font-weight: 600;
}

/* M5 */
.m5 { padding: 32px; }
.philosophy-cards {
  display: flex; flex-direction: column; gap: 16px; margin-top: 24px;
}
.philosophy-card {
  background: var(--bg-warm); padding: 20px;
  border-radius: 12px; border-left: 3px solid var(--border);
  transition: var(--transition);
}
.philosophy-card:hover { border-left-color: var(--accent); transform: translateX(2px); }
.philosophy-card.highlight {
  background: var(--accent-light);
  border-left-color: var(--accent);
}
.philosophy-card.highlight .ph-num { color: var(--accent-deep); }
.philosophy-card.highlight .ph-title { color: var(--accent-deep); }
.ph-num {
  font-family: "Poppins", sans-serif;
  font-size: 11px; color: var(--text-tertiary);
  letter-spacing: 0.15em; font-weight: 500;
}
.ph-title {
  font-family: "Poppins", sans-serif;
  font-size: 17px; font-weight: 600; color: var(--text);
  margin-top: 4px; line-height: 1.3;
}
.ph-claim {
  font-family: "Lora", serif; font-size: 13px;
  color: var(--text-secondary); margin-top: 8px; line-height: 1.6;
}
.ph-details {
  margin-top: 16px; padding-top: 16px;
  border-top: 1px solid var(--border);
}
.ph-details summary {
  cursor: pointer; font-size: 12px;
  color: var(--accent); font-weight: 500;
  font-family: "Poppins", sans-serif; letter-spacing: 0.02em;
}
.ph-details h4 {
  font-size: 11px; color: var(--text-tertiary);
  margin-top: 14px; text-transform: uppercase;
  letter-spacing: 0.08em; font-family: "Poppins", sans-serif;
}
.ph-details p { font-size: 13px; margin-top: 6px; color: var(--text-secondary); line-height: 1.6; }
.ph-details ul { margin-top: 6px; padding-left: 20px; }
.ph-details li { font-size: 13px; color: var(--text-secondary); margin-bottom: 4px; line-height: 1.5; }
.ph-source {
  font-size: 11px; color: var(--text-tertiary);
  margin-top: 14px; font-style: italic;
  padding-top: 10px; border-top: 1px dashed var(--border);
}

/* M6 */
.m6 { padding: 32px; }
.alert-summary {
  display: grid; grid-template-columns: repeat(2, 1fr);
  gap: 8px; margin-top: 16px;
}
.alert-stat {
  background: var(--bg-warm); padding: 12px;
  border-radius: 8px; text-align: center;
  border-left: 3px solid var(--border);
}
.alert-stat.ok { border-left-color: var(--green); }
.alert-stat.warn { border-left-color: var(--red); }
.alert-stat.pending { border-left-color: var(--blue); }
.alert-num {
  display: block; font-family: "Poppins", sans-serif;
  font-size: 26px; font-weight: 600; color: var(--text);
}
.alert-label {
  font-size: 11px; color: var(--text-tertiary); margin-top: 2px;
}
.alert-list { margin-top: 20px; }
.alert-list h4 {
  font-size: 11px; color: var(--text-tertiary);
  text-transform: uppercase; letter-spacing: 0.08em;
  font-family: "Poppins", sans-serif; font-weight: 500;
}
.alert-list ul { list-style: none; margin-top: 8px; }
.alert-item {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 10px; background: var(--bg-warm);
  border-radius: 6px; margin-bottom: 4px; cursor: pointer;
  transition: var(--transition);
}
.alert-item:hover { background: var(--accent-light); transform: translateX(2px); }
.alert-status {
  font-size: 10px; font-weight: 600; color: white;
  background: var(--red); padding: 2px 6px;
  border-radius: 4px; font-family: monospace; letter-spacing: 0.05em;
}
.alert-name { font-size: 12px; color: var(--text); }
.alert-item.empty {
  color: var(--text-tertiary); font-style: italic;
  justify-content: center; cursor: default;
}
.alert-item.empty:hover { background: var(--bg-warm); transform: none; }
"""


# ============================================================
# §2 HTML 渲染函数
# ============================================================

def render_m1_identity() -> str:
    return f"""
<section class="module m1" data-module="m1">
  <div class="m1-header">
    <div class="m1-logo">
      <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
        <circle cx="24" cy="24" r="20" stroke="#d97757" stroke-width="2"/>
        <path d="M14 24 L22 32 L34 16" stroke="#d97757" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      </svg>
    </div>
    <div class="m1-title">
      <h1>Research OS</h1>
      <p class="m1-tagline">深度调研工作台</p>
    </div>
    <div class="m1-version-badge">v0.5</div>
  </div>
  <div class="m1-stats">
    <div class="stat"><span class="stat-num">{STATS['projects']}</span><span class="stat-label">项目</span></div>
    <div class="stat"><span class="stat-num">{STATS['versions']}</span><span class="stat-label">版本</span></div>
    <div class="stat"><span class="stat-num">{STATS['modules']}</span><span class="stat-label">模块</span></div>
    <div class="stat"><span class="stat-num">{STATS['completed']}</span><span class="stat-label">已完成</span></div>
  </div>
</section>
"""


def render_m2_versions() -> str:
    nodes = "".join(f"""
      <button class="version-node" data-version="{v['id']}" data-date="{v['date']}" title="{v['id']} · {v['date']}">
        <span class="v-id">{v['id']}</span>
        <span class="v-date">{v['date']}</span>
      </button>
    """ for v in VERSIONS)

    panels = "".join(f"""
      <div class="version-panel" data-version="{v['id']}">
        <div class="panel-col">
          <div class="panel-label">问题</div>
          <div class="panel-text">{v['problem']}</div>
        </div>
        <div class="panel-col">
          <div class="panel-label">迭代</div>
          <div class="panel-text">{v['iter']}</div>
        </div>
        <div class="panel-col">
          <div class="panel-label">解锁</div>
          <div class="panel-text">{v['unlock']}</div>
        </div>
      </div>
    """ for v in VERSIONS)

    return f"""
<section class="module m2" data-module="m2">
  <h2 class="module-title">版本演化</h2>
  <p class="module-subtitle">从 v0.1 到 v0.5：9 个版本的真实迭代路径</p>
  <div class="version-timeline">
    <div class="version-line"></div>
    <div class="version-nodes">{nodes}</div>
  </div>
  <div class="version-panels">{panels}</div>
</section>
"""


def render_m3_matrix() -> str:
    categories = sorted({p["category"] for p in PROJECTS})
    versions_order = [v["id"] for v in VERSIONS]

    head_cells = "".join(f"<th>{v}</th>" for v in versions_order)

    rows = ""
    for cat in categories:
        cells = ""
        for v in versions_order:
            cell_projects = [p for p in PROJECTS if p["category"] == cat and p["version"] == v]
            if cell_projects:
                chips = "".join(
                    f'<button class="proj-chip {p["status"]}" data-project="{p["name"]}">{p["name"]}</button>'
                    for p in cell_projects
                )
                cells += f'<td>{chips}</td>'
            else:
                cells += '<td class="empty"></td>'
        rows += f'<tr><th class="row-head">{cat}</th>{cells}</tr>'

    return f"""
<section class="module m3" data-module="m3">
  <h2 class="module-title">调研产出矩阵</h2>
  <p class="module-subtitle">{len(PROJECTS)} 个项目 × {len(versions_order)} 个版本</p>
  <div class="matrix-wrap">
    <table class="matrix">
      <thead><tr><th></th>{head_cells}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
  <div class="node-graph" id="nodeGraph">
    <div class="graph-title" id="graphTitle">点击项目查看主题节点图</div>
    <svg width="100%" height="280" viewBox="0 0 600 280" id="nodeGraphSvg"></svg>
  </div>
</section>
"""


def render_workflow_object(item_name: str) -> str:
    OBJECT_SVGS = {
        "地基": '<rect x="15" y="50" width="50" height="15" fill="#d97757" opacity="0.25" stroke="#a3a299" stroke-width="1.5"/><line x1="10" y1="50" x2="70" y2="50" stroke="#a3a299" stroke-width="1.5"/>',
        "罗盘": '<circle cx="40" cy="40" r="22" fill="none" stroke="#a3a299" stroke-width="1.5"/><polygon points="40,20 44,40 40,60 36,40" fill="#d97757" opacity="0.7"/><circle cx="40" cy="40" r="2" fill="#a3a299"/>',
        "任务卡": '<rect x="18" y="20" width="44" height="44" fill="#fff" stroke="#a3a299" stroke-width="1.5" rx="3"/><line x1="24" y1="30" x2="56" y2="30" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="38" x2="50" y2="38" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="46" x2="52" y2="46" stroke="#a3a299" stroke-width="1"/>',
        "蓝图": '<rect x="14" y="22" width="52" height="36" fill="#d97757" opacity="0.15" stroke="#a3a299" stroke-width="1.5" rx="2"/><line x1="20" y1="32" x2="60" y2="32" stroke="#a3a299" stroke-width="1"/><line x1="20" y1="42" x2="55" y2="42" stroke="#a3a299" stroke-width="1"/><line x1="20" y1="52" x2="48" y2="52" stroke="#a3a299" stroke-width="1"/>',
        "漏斗": '<path d="M15 22 L65 22 L42 50 L42 64 L38 64 L38 50 Z" fill="none" stroke="#a3a299" stroke-width="1.5" stroke-linejoin="round"/><line x1="38" y1="50" x2="42" y2="50" stroke="#a3a299" stroke-width="1.5"/>',
        "天平": '<line x1="40" y1="20" x2="40" y2="60" stroke="#a3a299" stroke-width="1.5"/><line x1="18" y1="32" x2="62" y2="32" stroke="#a3a299" stroke-width="1.5"/><path d="M18 32 L12 44 L24 44 Z" fill="none" stroke="#a3a299" stroke-width="1.2"/><path d="M62 32 L56 44 L68 44 Z" fill="none" stroke="#a3a299" stroke-width="1.2"/><rect x="35" y="60" width="10" height="4" fill="#a3a299"/>',
        "账本": '<rect x="18" y="22" width="44" height="40" fill="none" stroke="#a3a299" stroke-width="1.5" rx="2"/><line x1="40" y1="22" x2="40" y2="62" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="32" x2="36" y2="32" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="42" x2="36" y2="42" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="52" x2="36" y2="52" stroke="#a3a299" stroke-width="1"/>',
        "多Agent": '<circle cx="22" cy="40" r="10" fill="none" stroke="#a3a299" stroke-width="1.5"/><circle cx="58" cy="40" r="10" fill="none" stroke="#a3a299" stroke-width="1.5"/><line x1="32" y1="40" x2="48" y2="40" stroke="#a3a299" stroke-width="1.2" stroke-dasharray="3,2"/><circle cx="22" cy="40" r="2" fill="#d97757"/><circle cx="58" cy="40" r="2" fill="#d97757"/>',
        "盾牌": '<path d="M40 18 L62 28 L62 42 Q62 56 40 64 Q18 56 18 42 L18 28 Z" fill="#d97757" opacity="0.15" stroke="#a3a299" stroke-width="1.5"/><path d="M30 40 L37 47 L52 32" stroke="#d97757" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>',
        "草稿": '<rect x="18" y="18" width="40" height="52" fill="none" stroke="#a3a299" stroke-width="1.5" rx="2"/><line x1="24" y1="28" x2="50" y2="28" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="38" x2="55" y2="38" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="48" x2="48" y2="48" stroke="#a3a299" stroke-width="1"/><line x1="24" y1="58" x2="52" y2="58" stroke="#a3a299" stroke-width="1"/>',
        "镜子": '<ellipse cx="40" cy="40" rx="22" ry="28" fill="none" stroke="#a3a299" stroke-width="1.5"/><line x1="40" y1="14" x2="40" y2="66" stroke="#d97757" stroke-width="1" opacity="0.4"/><circle cx="32" cy="34" r="1.5" fill="#d97757" opacity="0.6"/><circle cx="48" cy="46" r="1.5" fill="#d97757" opacity="0.6"/>',
        "溯源": '<circle cx="40" cy="40" r="18" fill="none" stroke="#a3a299" stroke-width="1.5"/><line x1="40" y1="22" x2="40" y2="58" stroke="#a3a299" stroke-width="1.2" stroke-dasharray="2,2"/><line x1="22" y1="40" x2="58" y2="40" stroke="#a3a299" stroke-width="1.2" stroke-dasharray="2,2"/><circle cx="40" cy="40" r="3" fill="#d97757"/>',
        "JSON": '<rect x="16" y="26" width="48" height="28" fill="none" stroke="#a3a299" stroke-width="1.5" rx="3"/><text x="40" y="46" text-anchor="middle" fill="#d97757" font-size="11" font-family="monospace">{ }</text>',
        "HTML": '<rect x="16" y="26" width="48" height="28" fill="none" stroke="#a3a299" stroke-width="1.5" rx="3"/><text x="40" y="46" text-anchor="middle" fill="#d97757" font-size="11" font-family="monospace">&lt;/&gt;</text>',
        "章": '<circle cx="40" cy="40" r="20" fill="#d97757" opacity="0.2" stroke="#a3a299" stroke-width="1.5"/><line x1="40" y1="20" x2="40" y2="60" stroke="#a3a299" stroke-width="1.2"/><line x1="30" y1="30" x2="50" y2="30" stroke="#a3a299" stroke-width="1"/><line x1="30" y1="50" x2="50" y2="50" stroke="#a3a299" stroke-width="1"/>',
        "发布": '<path d="M28 52 L40 22 L52 52" fill="none" stroke="#a3a299" stroke-width="1.5" stroke-linejoin="round"/><circle cx="40" cy="18" r="4" fill="#d97757"/><line x1="20" y1="60" x2="60" y2="60" stroke="#a3a299" stroke-width="1.5"/>',
    }
    svg_inner = OBJECT_SVGS.get(item_name, '<circle cx="40" cy="40" r="20" fill="none" stroke="#a3a299" stroke-width="1.5"/>')
    return f"""
    <div class="workflow-object" data-object="{item_name}" title="{item_name}">
      <svg width="80" height="80" viewBox="0 0 80 80">{svg_inner}</svg>
      <span class="object-label">{item_name}</span>
    </div>
    """


def render_m4_workflow() -> str:
    stages_html = ""
    for stage in STAGES:
        items = stage["items"]
        items_svg = "".join(render_workflow_object(item) for item in items)
        steps = [s for s in WORKFLOW if s["stage"] == stage["name"]]
        step_labels = "".join(
            f'<span class="step-num{" human-confirm" if s["human_confirm"] else ""}" title="step {s["step"]} · {s["name"]}{" 🛑 人工确认" if s["human_confirm"] else ""}">{s["step"]}</span>'
            for s in steps
        )
        stages_html += f"""
        <div class="workflow-stage">
          <h3 class="stage-name">{stage["name"]}</h3>
          <p class="stage-range">{stage["range"]}</p>
          <div class="stage-objects">{items_svg}</div>
          <div class="stage-steps">{step_labels}</div>
        </div>
        """
    return f"""
<section class="module m4" data-module="m4">
  <h2 class="module-title">工作流引擎</h2>
  <p class="module-subtitle">15 步状态机，分 3 阶段 · 🛑 标记为人工确认点</p>
  <div class="workflow-stages">{stages_html}</div>
</section>
"""


def render_m5_philosophy() -> str:
    cards = ""
    for p in PHILOSOPHY:
        highlight_class = "highlight" if p.get("highlight") else ""
        code_items = "".join(f"<li>{c}</li>" for c in p["code"])
        cards += f"""
        <article class="philosophy-card {highlight_class}" data-num="{p['num']}">
          <div class="ph-num">PRINCIPLE {p['num']}</div>
          <h3 class="ph-title">{p['title']}</h3>
          <p class="ph-claim">{p['claim']}</p>
          <details class="ph-details">
            <summary>展开：为什么这样设计 + 代码如何强制</summary>
            <h4>为什么这样设计</h4>
            <p>{p['why']}</p>
            <h4>代码如何强制</h4>
            <ul>{code_items}</ul>
            <p class="ph-source">来源：{p['source']}</p>
          </details>
        </article>
        """
    return f"""
<section class="module m5" data-module="m5">
  <h2 class="module-title">设计哲学</h2>
  <p class="module-subtitle">4 条哲学，每条对应一段真实代码 · 第 3 条最有灵气</p>
  <div class="philosophy-cards">{cards}</div>
</section>
"""


def render_m6_alerts() -> str:
    completed = sum(1 for p in PROJECTS if p["status"] == "completed")
    failed = sum(1 for p in PROJECTS if p["status"] == "failed")
    planned = sum(1 for p in PROJECTS if p["status"] == "planned")

    failed_projects = [p for p in PROJECTS if p["status"] == "failed"]
    failed_items = "".join(f"""
      <li class="alert-item" data-project="{p['name']}">
        <span class="alert-status">FAIL</span>
        <span class="alert-name">{p['name']}</span>
      </li>
    """ for p in failed_projects) if failed_projects else '<li class="alert-item empty">无异常项目</li>'

    return f"""
<section class="module m6" data-module="m6">
  <h2 class="module-title">自查告警</h2>
  <div class="alert-summary">
    <div class="alert-stat"><span class="alert-num">{len(PROJECTS)}</span><span class="alert-label">总项目</span></div>
    <div class="alert-stat ok"><span class="alert-num">{completed}</span><span class="alert-label">已完成</span></div>
    <div class="alert-stat warn"><span class="alert-num">{failed}</span><span class="alert-label">失败</span></div>
    <div class="alert-stat pending"><span class="alert-num">{planned}</span><span class="alert-label">计划中</span></div>
  </div>
  <div class="alert-list">
    <h4>需要关注</h4>
    <ul>{failed_items}</ul>
  </div>
</section>
"""


# ============================================================
# §3 JS（内嵌简化的 d3-force 替代实现，无需外部依赖）
# ============================================================

JS = r"""
// ============ Bento 展开/压缩 ============
document.querySelectorAll('.module').forEach(mod => {
  mod.addEventListener('click', (e) => {
    if (e.target.closest('button, a, details, summary, .proj-chip, .version-node, .alert-item, .workflow-object, .node-circle, .ph-details')) return;
    if (mod.classList.contains('m1')) return;
    const wasExpanded = mod.classList.contains('expanded');
    document.querySelectorAll('.module').forEach(m => {
      m.classList.remove('expanded', 'compressed');
    });
    if (!wasExpanded) {
      mod.classList.add('expanded');
      document.querySelectorAll('.module').forEach(other => {
        if (other !== mod) other.classList.add('compressed');
      });
    }
  });
});

// ============ M2 版本节点切换 ============
document.querySelectorAll('.version-node').forEach(node => {
  node.addEventListener('click', (e) => {
    e.stopPropagation();
    const vid = node.dataset.version;
    document.querySelectorAll('.version-node').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.version-panel').forEach(p => p.classList.remove('active'));
    node.classList.add('active');
    const panel = document.querySelector('.version-panel[data-version="' + vid + '"]');
    if (panel) panel.classList.add('active');
  });
});
const defaultNode = document.querySelector('.version-node[data-version="v0.5"]');
if (defaultNode) {
  defaultNode.classList.add('active');
  const defaultPanel = document.querySelector('.version-panel[data-version="v0.5"]');
  if (defaultPanel) defaultPanel.classList.add('active');
}

// ============ M3 节点图（原生 SVG + 力导向近似 + 引力浮动）============
const PROJECTS_DATA = [
    {name: "AWS-Top20-求职路径", cards: [{title: "AWS 云服务核心栈", related: ["职业路径选择"]}, {title: "Top20 公司筛选", related: ["AWS 云服务核心栈"]}, {title: "职业路径选择", related: []}]},
    {name: "MizzenAI 产品拆解", cards: [{title: "产品定位", related: ["用户访谈方法论"]}, {title: "用户访谈方法论", related: []}, {title: "竞品对比", related: ["产品定位"]}]},
    {name: "知识塔罗定位", cards: [{title: "用户画像", related: []}, {title: "定价策略", related: ["用户画像"]}]},
    {name: "Research-OS-自我审计", cards: [{title: "工作流完整性", related: ["读者模拟有效性"]}, {title: "读者模拟有效性", related: []}]},
    {name: "Anthropic-美学-研究", cards: [{title: "配色规范", related: ["字体选择"]}, {title: "字体选择", related: []}, {title: "简笔画物件", related: ["配色规范"]}]},
    {name: "芯片-第一性原理", cards: [{title: "制程工艺", related: ["性能功耗权衡"]}, {title: "性能功耗权衡", related: []}]},
    {name: "用户访谈方法论", cards: [{title: "访谈大纲设计", related: ["用户画像"]}, {title: "用户画像", related: []}]},
    {name: "AI 调研工具横向对比", cards: [{title: "GPT Researcher", related: ["Deep Research"]}, {title: "Deep Research", related: []}, {title: "Perplexity", related: ["GPT Researcher"]}]},
    {name: "Agent 集群研究", cards: [{title: "Kimi Agent", related: []}, {title: "Claude Code", related: ["Kimi Agent"]}]},
    {name: "一人公司可行路径", cards: [{title: "赛道选择", related: []}]},
    {name: "RAG 系统设计参考", cards: [{title: "向量数据库对比", related: []}]},
    {name: "产品组合优化", cards: [{title: "知识塔罗 + Research OS", related: []}]},
    {name: "秋招时间线规划", cards: [{title: "面试准备节奏", related: []}]},
    {name: "Obsidian 工作流迁移", cards: [{title: "知识库结构", related: []}]}
];

function renderNodeGraph(projectName) {
    const proj = PROJECTS_DATA.find(p => p.name === projectName);
    if (!proj) return;
    const svg = document.getElementById('nodeGraphSvg');
    const titleEl = document.getElementById('graphTitle');
    const container = document.getElementById('nodeGraph');
    if (!svg || !titleEl || !container) return;

    titleEl.textContent = projectName + ' · 主题节点图';
    container.style.display = 'block';

    while (svg.firstChild) svg.removeChild(svg.firstChild);

    const cards = proj.cards;
    const W = 600, H = 280;
    const cx = W / 2, cy = H / 2;
    const radius = Math.min(W, H) / 3;

    const nodes = cards.map((c, i) => {
        const angle = (i / cards.length) * Math.PI * 2 - Math.PI / 2;
        return {
            title: c.title,
            related: c.related || [],
            baseX: cx + Math.cos(angle) * radius,
            baseY: cy + Math.sin(angle) * radius,
            x: cx + Math.cos(angle) * radius,
            y: cy + Math.sin(angle) * radius,
        };
    });

    const links = [];
    cards.forEach((c, i) => {
        (c.related || []).forEach(target => {
            const j = cards.findIndex(cc => cc.title === target);
            if (j >= 0 && i !== j) links.push({source: i, target: j});
        });
    });

    links.forEach(link => {
        const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
        line.setAttribute('class', 'node-link');
        line.setAttribute('data-source', link.source);
        line.setAttribute('data-target', link.target);
        svg.appendChild(line);
    });

    nodes.forEach((n, i) => {
        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('class', 'node-circle');
        circle.setAttribute('r', '12');
        circle.setAttribute('cx', n.x);
        circle.setAttribute('cy', n.y);
        let dragging = false;
        let startX, startY, startNodeX, startNodeY;
        circle.addEventListener('mousedown', (e) => {
            dragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startNodeX = nodes[i].x;
            startNodeY = nodes[i].y;
            e.preventDefault();
        });
        document.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            nodes[i].x = startNodeX + (e.clientX - startX);
            nodes[i].y = startNodeY + (e.clientY - startY);
        });
        document.addEventListener('mouseup', () => { dragging = false; });
        g.appendChild(circle);

        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('class', 'node-text');
        text.setAttribute('x', n.x);
        text.setAttribute('y', n.y + 28);
        text.textContent = n.title;
        g.appendChild(text);

        svg.appendChild(g);
    });

    let tick = 0;
    function animate() {
        tick += 0.02;
        nodes.forEach((n, i) => {
            n.x = n.baseX + Math.sin(tick + i * 0.7) * 4;
            n.y = n.baseY + Math.cos(tick + i * 1.1) * 4;
        });

        const groups = svg.querySelectorAll('g');
        groups.forEach((g, i) => {
            const circle = g.querySelector('circle');
            const text = g.querySelector('text');
            if (circle && text) {
                circle.setAttribute('cx', nodes[i].x);
                circle.setAttribute('cy', nodes[i].y);
                text.setAttribute('x', nodes[i].x);
                text.setAttribute('y', nodes[i].y + 28);
            }
        });

        svg.querySelectorAll('line.node-link').forEach(line => {
            const s = parseInt(line.dataset.source);
            const t = parseInt(line.dataset.target);
            line.setAttribute('x1', nodes[s].x);
            line.setAttribute('y1', nodes[s].y);
            line.setAttribute('x2', nodes[t].x);
            line.setAttribute('y2', nodes[t].y);
        });

        requestAnimationFrame(animate);
    }
    animate();
}

document.querySelectorAll('.proj-chip').forEach(chip => {
  chip.addEventListener('click', (e) => {
    e.stopPropagation();
    const projectName = chip.dataset.project;
    renderNodeGraph(projectName);
  });
});

// ============ M6 → M3 联动 ============
document.querySelectorAll('.alert-item[data-project]').forEach(item => {
  item.addEventListener('click', (e) => {
    e.stopPropagation();
    const proj = item.dataset.project;
    const m3 = document.querySelector('.m3');
    if (!m3) return;
    document.querySelectorAll('.module').forEach(m => {
      m.classList.remove('expanded', 'compressed');
    });
    m3.classList.add('expanded');
    document.querySelectorAll('.module').forEach(other => {
      if (other !== m3) other.classList.add('compressed');
    });
    m3.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => {
      const chip = document.querySelector('.proj-chip[data-project="' + proj + '"]');
      if (chip) chip.click();
    }, 600);
  });
});
"""


# ============================================================
# §4 main
# ============================================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research OS — 深度调研工作台</title>
<style>{css}</style>
</head>
<body>
<div class="dashboard">
{m1}
{m2}
{m3}
{m4}
{m5}
{m6}
</div>
<script>{js}</script>
</body>
</html>"""


def main():
    html = HTML_TEMPLATE.format(
        css=CSS,
        m1=render_m1_identity(),
        m2=render_m2_versions(),
        m3=render_m3_matrix(),
        m4=render_m4_workflow(),
        m5=render_m5_philosophy(),
        m6=render_m6_alerts(),
        js=JS,
    )
    out = Path(__file__).parent / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"Generated: {out} ({len(html)} bytes)")


if __name__ == "__main__":
    main()
