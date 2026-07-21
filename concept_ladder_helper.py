#!/usr/bin/env python3
"""Research OS v1.2 concept_ladder_helper为 intent_doc.concept_ladder_seed 里的每个术语生成 6 层解释：
  1. intuition       直觉比喻（用日常事物类比）
  2. definition      基础定义（一句话说清楚）
  3. mechanism       工作机制（怎么运转的）
  4. industry_context 行业语境（这个领域怎么用）
  5. user_concern    用户关心点（这玩意跟我有什么关系）
  6. project_anchor  项目锚点（在本次调研的哪个项目里能看到它）

借鉴 STORM PersonaGenerator 的 persona 控制——不直接让 LLM 写定义，
而是先指定 6 个视角，每个视角独立填一行，避免 LLM 写得笼统。

用法：
  python concept_ladder_helper.py <project_dir>
  → 读取 00-task/intent_doc.json 的 concept_ladder_seed
  → 输出 07-output/view-model.json 的 concept_ladder 字段（6 层解释）

数据流（v2.0 明确，已联通）：
  intent_discovery 固化 00-task/intent_doc.json 的 v07.concept_ladder_seed（术语种子）
  → 本工具 update_view_model 读 seed、生成 6 层解释，写入 07-output/view-model.json
    的 concept_ladder 字段
  → check_term_explanations 对 final-report.md 做报告术语解释检查：
    机械判断每个种子术语后 100 字符内是否带解释性标点（：或（或——）。
    纯字符匹配，不判断解释质量（质量判断是 Agent 的事，符合 Dumb Tools）。
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path
from typing import Any


# 预置术语库——覆盖深度调研领域常见技术名词的 6 层解释
# 用户可扩展。如果种子术语不在库里，调 LLM 生成
GLOSSARY: dict[str, dict[str, str]] = {
    "planner agent": {
        "intuition": "像一个项目经理，接到大任务先拆成几个小任务，再分给团队",
        "definition": "在 AI 调研系统里负责把用户的大问题拆成几个具体子问题的 LLM 角色",
        "mechanism": "读取用户 query → LLM 生成 N 个研究子问题 → 子问题分发给执行 agent 并行检索",
        "industry_context": "GPT Researcher 用它，STORM 的 WikiWriter 是它的变体（带 persona 视角）",
        "user_concern": "拆得好不好直接决定调研质量——拆歪了后面所有搜索都是浪费",
        "project_anchor": "GPT Researcher 第一步就是 planner agent",
    },
    "persona": {
        "intuition": "像让不同职业的人看同一个问题——记者看到新闻点、工程师看到技术点、投资人看到商业点",
        "definition": "给 LLM 套一个虚拟身份（如'你是资深维基编辑'），让它从这个身份的视角提问/写作",
        "mechanism": "PersonaGenerator 找相关参考文档 → LLM 生成 N 个 persona 描述 → 每个 persona 用自己视角跑独立对话",
        "industry_context": "STORM 论文核心创新——证明直接让 LLM 提问效果差，必须用 persona 控制",
        "user_concern": "没有 persona 控制，LLM 经常问重复或跑偏的问题——这是 GPT Researcher issue 区抱怨的根因",
        "project_anchor": "STORM 的 PersonaGenerator 模块",
    },
    "CodeAgent": {
        "intuition": "像让 AI 自己写 Python 代码来操作工具，而不是按固定模板填表",
        "definition": "HuggingFace smolagents 框架的特色——LLM 直接生成 Python 代码调用工具，不输出 JSON 工具调用协议",
        "mechanism": "LLM 收到任务 → 写一段 Python 代码（如 result = search('query')）→ 框架执行代码 → 把结果返回给 LLM → 循环",
        "industry_context": "HuggingFace 博客称比 JSON tool-call 成本降 30%，因为代码能组合多个工具调用",
        "user_concern": "代码生成质量取决于模型能力——o1 这种强模型效果好，弱模型容易写错代码",
        "project_anchor": "HF Open Deep Research 的 manager_agent",
    },
    "ReAct loop": {
        "intuition": "像人解决问题——思考一步、做一步、看结果、再思考下一步",
        "definition": "Reason+Act 循环：LLM 在每一步先写思考（Thought）再写动作（Action）→ 执行 → 看结果（Observation）→ 下一步",
        "mechanism": "循环 N 次：Thought → Action → Observation → 直到 LLM 调 final_answer 或达到 max_steps",
        "industry_context": "HF 和 Owl 都是 ReAct 变体——HF 加 planning_interval 周期性反思，Owl 用 User/Assistant 双角色",
        "user_concern": "循环次数上限 max_steps 决定成本和质量——少了不够深，多了烧 token",
        "project_anchor": "HF manager_agent 的 max_steps=12 + planning_interval=4",
    },
    "dspy": {
        "intuition": "像把 prompt 当成可调参数的代码模块——不写死 prompt，而是声明输入输出接口让框架优化",
        "definition": "Stanford 出的 LLM 编程框架，把 prompt 当成可优化的代码模块，不直接写 prompt 字符串",
        "mechanism": "声明 Signature（输入输出契约）→ 写 Module（业务逻辑）→ 用 Optimizer 自动调优 prompt",
        "industry_context": "STORM 用 dspy 写所有 LLM 调用——好处是 prompt 可优化，坏处是学习成本高",
        "user_concern": "对最终用户不可见——它只影响开发者体验，但决定了 STORM 修改 prompt 的灵活性",
        "project_anchor": "STORM 的所有 LLM 调用都用 dspy Signature",
    },
    "LangGraph": {
        "intuition": "像把多 agent 工作流画成状态机——每个节点是一个 agent，边是状态转换",
        "definition": "LangChain 出的 agent 编排框架，把多 agent 工作流建模成有向图（DAG）",
        "mechanism": "定义 StateGraph → 每个节点是一个 agent 函数 → 边定义状态转换条件 → 编译成可执行 pipeline",
        "industry_context": "GPT Researcher multi_agents 模式用它，LangChain open_deep_research 也用它",
        "user_concern": "比 ReAct loop 更可控——状态机让流程可预测、可观测、可调试",
        "project_anchor": "GPT Researcher 的 multi_agents 模式",
    },
    "MCP": {
        "intuition": "像 AI 工具的 USB-C 接口——统一标准让任何 AI 都能调用任何工具",
        "definition": "Model Context Protocol，Anthropic 2024 年提出的开放标准，定义 AI 如何调用外部工具",
        "mechanism": "工具方实现 MCP server 暴露能力 → AI 方实现 MCP client 连接 → 通过 JSON-RPC 协议通信",
        "industry_context": "GPT Researcher 和 Owl 支持，STORM 和 HF Open Deep Research 不支持",
        "user_concern": "支持 MCP 意味着你的 AI agent 可以调用这个工具——是 2025+ 生态入场券",
        "project_anchor": "GPT Researcher 的 mcp_configs 参数",
    },
    "RolePlaying": {
        "intuition": "像让两个演员演对手戏——一个演用户下指令，一个演助手执行，多轮对话完成任务",
        "definition": "CAMEL 首创的多智能体协作范式，两个 agent 分别扮演'用户'和'助手'通过多轮对话完成复杂任务",
        "mechanism": "User Agent 发指令 → Assistant Agent 用工具执行 → User Agent 看结果再下指令 → 直到 TASK_DONE",
        "industry_context": "Owl 用它跑 GAIA benchmark 拿开源第一（69.09%）",
        "user_concern": "比单 agent 强制多轮思考——但 token 消耗翻倍（每轮调 LLM 2 次）",
        "project_anchor": "Owl 的 RolePlaying 模式",
    },
    "embedding 过滤": {
        "intuition": "像用语义相似度当筛子——把网页内容向量化，只留跟研究问题语义接近的部分",
        "definition": "把文本转成向量（embedding），用 cosine 相似度筛掉与查询不相关的内容",
        "mechanism": "网页内容 → embedding 模型转向量 → 与查询向量算 cosine 相似度 → 阈值过滤或 top-K 截取",
        "industry_context": "GPT Researcher >8KB 走这个；STORM 用 SentenceTransformer 做 section 级检索",
        "user_concern": "决定调研精度——筛狠了漏信息，筛松了喂给 LLM 太多噪音",
        "project_anchor": "GPT Researcher 的 COMPRESSION_THRESHOLD=8KB 阈值",
    },
    "evidence quoting": {
        "intuition": "像写论文引用文献——不直接说，而是附上原文摘录让读者自己判断",
        "definition": "不只是总结网页内容，还把原文关键段落（key_excerpts）原样保留作为可审计证据",
        "mechanism": "LLM 生成 summary 时同时输出 key_excerpts 字段 → 结构化存到证据库 → 报告引用时附原文",
        "industry_context": "LangChain open_deep_research 有这个（Summary 结构）；GPT Researcher/HF/Owl 都没有",
        "user_concern": "决定报告可信度——有原文摘录才能反查，否则只能信 LLM 总结",
        "project_anchor": "LangChain 版的 Summary 数据结构",
    },
}



# v1.2: 合并 plain_glossary.py 的术语库（原孤立工具，统一为 6 层结构）
_PLAIN_GLOSSARY_MIGRATED: dict[str, dict[str, str]] = {
    "execution agent": {
        "intuition": "像装修队的泥瓦工——队长让他贴客厅瓷砖，他就去贴",
        "definition": "AI 里真正干活的员工，按项目经理分的任务去搜索和总结",
        "mechanism": "接收 planner agent 分派的子任务 -> 调用搜索工具 -> 总结结果返回",
        "industry_context": "GPT Researcher 和 STORM 都用这个分工模式",
        "user_concern": "执行质量决定信息收集的全面性——漏搜了关键来源后面全歪",
        "project_anchor": "GPT Researcher 的 execute_agent",
    },
    "LangChain": {
        "intuition": "像乐高积木套装——不用从零造轮子，拼装即可",
        "definition": "帮你写 AI 应用的工具箱，里面有现成的零件拼一拼就能用",
        "mechanism": "提供 Chain/Agent/Memory/Tool 等组件 -> 开发者组合构建应用",
        "industry_context": "LangChain open_deep_research 用它构建调研 pipeline",
        "user_concern": "组件多但学习曲线陡——简单任务用它杀鸡用牛刀",
        "project_anchor": "LangChain open_deep_research 项目",
    },
    "smolagents": {
        "intuition": "像让员工自己写操作手册——不给他固定流程，让他看着办",
        "definition": "HuggingFace 出的轻量 AI 框架，特色是让 AI 自己写 Python 代码调工具",
        "mechanism": "LLM 收到任务 -> 直接生成 Python 代码 -> 框架执行 -> 返回结果",
        "industry_context": "HuggingFace Open Deep Research 用它",
        "user_concern": "轻量但功能少——适合快速原型，不适合复杂生产场景",
        "project_anchor": "HF Open Deep Research",
    },
    "ToolCallingAgent": {
        "intuition": "像点外卖——AI 看菜单点单，厨房按单做",
        "definition": "传统 AI 调工具的方式——AI 输出一段 JSON 告诉系统调哪个工具",
        "mechanism": "LLM 输出 JSON -> 框架解析 -> 调用工具 -> 返回结果",
        "industry_context": "LangChain 默认模式，对比 CodeAgent 模式",
        "user_concern": "比 CodeAgent 灵活性差——不能组合多个工具调用",
        "project_anchor": "LangChain 的 AgentExecutor",
    },
    "Workforce": {
        "intuition": "像公司组织架构——CEO 派活给市场/技术/财务各部门",
        "definition": "把任务按层级分工——一个总调度派活给多个专职工种 AI",
        "mechanism": "TaskPlanner 分解任务 -> 分派给 Specialist Agent -> 结果汇总",
        "industry_context": "CAMEL Owl 用这个模式跑 GAIA benchmark",
        "user_concern": "多 agent 协作的协调成本高——任务分配不当导致闲置或拥堵",
        "project_anchor": "Owl 的 Workforce 模块",
    },
    "viewport": {
        "intuition": "像看 PDF 翻页——不一次性全展开，一页页读",
        "definition": "把长网页切成一页页的小窗口，AI 一页页翻着看",
        "mechanism": "网页内容 -> 按视口高度分页 -> AI 逐页读取 -> 提取信息",
        "industry_context": "STORM 用这个模式处理长网页",
        "user_concern": "分页粒度决定信息完整性——太粗漏内容，太细成本高",
        "project_anchor": "STORM 的网页处理模块",
    },
    "hypothesis ledger": {
        "intuition": "像科学家做实验——先有假设再用数据验证",
        "definition": "调研一开始先写下假设，随着证据进来修订或推翻",
        "mechanism": "初始化假设列表 -> 每条证据进来打支持/反对 -> 假设状态动态更新",
        "industry_context": "Research OS 的核心模块",
        "user_concern": "防止确认偏误——人倾向于找支持自己结论的证据",
        "project_anchor": "Research OS 的 03-evidence/hypothesis_ledger.json",
    },
    "反方审计": {
        "intuition": "像法庭辩论——控方说完辩方必须反驳",
        "definition": "派一个角色专门攻击自己结论——找漏洞、降级、推翻",
        "mechanism": "Agent 写完报告 -> Red Team 逐条攻击 -> 标记脆弱结论 -> Agent 修订",
        "industry_context": "Research OS 的 step_8_red_team",
        "user_concern": "自己查自己很难客观——必须有制度化的对抗机制",
        "project_anchor": "Research OS 的 06-review/red_team.md",
    },
    "证据等级": {
        "intuition": "像新闻可信度——官方通报 A 级，大媒转述 B 级，路边消息 C 级",
        "definition": "给每条信息打等级——A 一手权威、B 二手可靠、C 单源、D 未验证",
        "mechanism": "每条证据标注来源类型 -> 按来源权威性打等级 -> 报告引用时标注",
        "industry_context": "Research OS 的证据矩阵",
        "user_concern": "低等级证据堆砌不等于高质量结论——必须看证据等级",
        "project_anchor": "Research OS 的 03-evidence/evidence_matrix.md",
    },
    "来源独立性": {
        "intuition": "像传话游戏——10 个人传同一句话，源头只有一个不算 10 个证据",
        "definition": "两条证据如果都引用同一个原始来源，算一条不算两条",
        "mechanism": "追溯每条证据的原始来源 -> 识别共同源头 -> 合并去重",
        "industry_context": "Research OS 的证据矩阵",
        "user_concern": "看起来证据很多但源头只有一个——这是常见的调研陷阱",
        "project_anchor": "Research OS 的 evidence_matrix.md 独立性列",
    },
}

GLOSSARY.update(_PLAIN_GLOSSARY_MIGRATED)

def enrich_ladder(seed_terms: list[str]) -> list[dict[str, str]]:
    """为种子术语生成 6 层解释。优先用 GLOSSARY 预置库，找不到的留空待人工填。"""
    enriched = []
    for term in seed_terms:
        term_lower = term.lower().strip()
        # 精确匹配
        if term_lower in GLOSSARY:
            entry = dict(GLOSSARY[term_lower])
            entry["term"] = term
            enriched.append(entry)
            continue
        # 模糊匹配（包含关系）
        matched = False
        for key, val in GLOSSARY.items():
            if key in term_lower or term_lower in key:
                entry = dict(val)
                entry["term"] = term
                enriched.append(entry)
                matched = True
                break
        if not matched:
            enriched.append({
                "term": term,
                "intuition": "",
                "definition": "",
                "mechanism": "",
                "industry_context": "",
                "user_concern": "",
                "project_anchor": "",
                "_needs_manual_fill": True,
            })
    return enriched


def update_view_model(project: Path) -> int:
    """读取 intent_doc.json 的 concept_ladder_seed，
    写入 view-model.json 的 concept_ladder 字段。"""
    intent_path = project / "00-task" / "intent_doc.json"
    vm_path = project / "07-output" / "view-model.json"
    if not intent_path.exists():
        print(f"[skip] no intent_doc.json at {intent_path}", file=sys.stderr)
        return 1
    intent = json.loads(intent_path.read_text(encoding="utf-8"))
    v07 = intent.get("v07") or intent
    seed = v07.get("concept_ladder_seed") or []
    if not seed:
        print(f"[skip] no concept_ladder_seed in intent_doc", file=sys.stderr)
        return 1
    enriched = enrich_ladder(seed)
    # 写入 view-model.json
    vm = {}
    if vm_path.exists():
        vm = json.loads(vm_path.read_text(encoding="utf-8"))
    vm["concept_ladder"] = enriched
    vm_path.parent.mkdir(parents=True, exist_ok=True)
    vm_path.write_text(json.dumps(vm, ensure_ascii=False, indent=2), encoding="utf-8")
    filled = sum(1 for e in enriched if not e.get("_needs_manual_fill"))
    print(f"[ok] concept_ladder written: {filled}/{len(enriched)} 已填，{len(enriched)-filled} 待人工")
    return 0


# 解释性标点：全角冒号、半角冒号、全角括号、半角括号、破折号（—— 含单个 —）
EXPLANATION_MARKS = "：:（(—–"


def check_term_explanations(report_text: str, terms: list) -> dict:
    """机械检查报告里每个术语是否带解释（v2.0 报告术语解释检查）。

    规则：术语任意一次出现后 100 字符内存在解释性标点（：或（或——）
    即视为 covered。纯字符匹配，不判断解释质量——质量判断是 Agent 的事。

    返回 {"covered": [...], "missing": [...], "coverage": float}
    """
    covered: list[str] = []
    missing: list[str] = []
    for term in terms:
        term = str(term).strip()
        if not term:
            continue
        pattern = re.compile(re.escape(term) + r"[\s\S]{0,100}[" + EXPLANATION_MARKS + "]")
        if pattern.search(report_text):
            covered.append(term)
        else:
            missing.append(term)
    total = len(covered) + len(missing)
    return {
        "covered": covered,
        "missing": missing,
        "coverage": round(len(covered) / total, 3) if total else 0.0,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: concept_ladder_helper.py <project_dir>", file=sys.stderr)
        sys.exit(1)
    sys.exit(update_view_model(Path(sys.argv[1])))
