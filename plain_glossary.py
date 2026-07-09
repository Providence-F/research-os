#!/usr/bin/env python3
"""Research OS v1.0 plain_glossary提供"专业名词 → 通俗解释"的转换工具。
模板要求每个专业名词配 blockquote 解释，但当前解释太技术化。
这个模块提供两层解释：
  - plain: 大白话（12岁能懂）
  - analogy: 类比（用日常事物比喻）

用法：
  from plain_glossary import explain
  print(explain("planner agent"))
"""
from __future__ import annotations


# 专业名词通俗解释库
# 每个 term 两个层：
#   plain: 一句话说清楚，不用任何术语
#   analogy: 用日常事物比喻
PLAIN_GLOSSARY: dict[str, dict[str, str]] = {
    "planner agent": {
        "plain": "AI 里的项目经理，接到大任务先拆成几个小任务再分给团队",
        "analogy": "像装修队长——业主要装三居室，他先拆成水电/泥瓦/木工/油漆几个工种再分派",
    },
    "execution agent": {
        "plain": "AI 里真正干活的员工，按项目经理分的任务去搜索和总结",
        "analogy": "像装修队的泥瓦工——队长让他贴客厅瓷砖，他就去贴",
    },
    "LangGraph": {
        "plain": "把多个 AI 串成一条流水线的工具，每一步是谁干、下一步去哪都画清楚",
        "analogy": "像地铁线路图——每个站是一个 AI，线路规定好谁连谁",
    },
    "LangChain": {
        "plain": "帮你写 AI 应用的工具箱，里面有现成的零件拼一拼就能用",
        "analogy": "像乐高积木套装——不用从零造轮子，拼装即可",
    },
    "smolagents": {
        "plain": "HuggingFace 出的轻量 AI 框架，特色是让 AI 自己写 Python 代码调工具",
        "analogy": "像让员工自己写操作手册——不给他固定流程，让他看着办",
    },
    "CodeAgent": {
        "plain": "让 AI 直接写 Python 代码来调工具，而不是按固定模板填表",
        "analogy": "像让厨师自己颠勺——不给他微波炉加热预制菜，让他真炒菜",
    },
    "ToolCallingAgent": {
        "plain": "传统 AI 调工具的方式——AI 输出一段 JSON 告诉系统调哪个工具",
        "analogy": "像点外卖——AI 看菜单点单，厨房按单做",
    },
    "ReAct": {
        "plain": "AI 解决问题的循环——想一步、做一步、看结果、再想下一步",
        "analogy": "像走迷宫——看一眼、走一步、撞墙了换条路、再走一步",
    },
    "persona": {
        "plain": "给 AI 套一个虚拟身份（如'你是资深记者'），让它从那个身份的视角看问题",
        "analogy": "像让演员演不同角色——同一个人演哈姆雷特和演罗密欧视角完全不同",
    },
    "dspy": {
        "plain": "Stanford 出的工具，让你不写死 prompt，而是声明输入输出接口让框架优化",
        "analogy": "像函数声明——你不写实现，只声明签名，框架帮你调优实现",
    },
    "MCP": {
        "plain": "AI 工具的 USB-C 接口——统一标准让任何 AI 都能调任何工具",
        "analogy": "像 USB-C 取代一堆乱七八糟的充电口——一个标准通吃",
    },
    "embedding": {
        "plain": "把文字转成数字向量，让计算机能用数学算两段话有多像",
        "analogy": "像把每首歌转成一串数字特征——节奏/风格/情绪——然后用数字找相似歌",
    },
    "cosine 相似度": {
        "plain": "用向量夹角算两段内容有多相关——0度完全一样，90度完全不相关",
        "analogy": "像用方向判断远近——两个人朝同方向走就是同类，朝垂直方向走就是无关",
    },
    "RolePlaying": {
        "plain": "让两个 AI 演对手戏——一个演用户下指令，一个演助手执行，多轮对话",
        "analogy": "像相声——一个逗哏一个捧哏，多轮对话把活儿干完",
    },
    "Workforce": {
        "plain": "把任务按层级分工——一个总调度派活给多个专职工种 AI",
        "analogy": "像公司组织架构——CEO 派活给市场/技术/财务各部门",
    },
    "viewport": {
        "plain": "把长网页切成一页页的小窗口，AI 一页页翻着看",
        "analogy": "像看 PDF 翻页——不一次性全展开，一页页读",
    },
    "evidence quoting": {
        "plain": "不只总结网页内容，还把原文关键段落原样保留作为可审计证据",
        "analogy": "像论文引用文献——不直接说，附上原文摘录让读者自己判断",
    },
    "广撒网换稳定性": {
        "plain": "抓 20+ 网页取最常出现的信息——大家都错概率极低",
        "analogy": "像问 20 个人同一个问题——多数答案一致就大概率对",
    },
    "hypothesis ledger": {
        "plain": "调研一开始先写下'我假设什么'，随着证据进来修订或推翻",
        "analogy": "像科学家做实验——先有假设再用数据验证，而不是先有结论再找证据",
    },
    "反方审计": {
        "plain": "派一个角色专门攻击自己结论——找漏洞、降级、推翻",
        "analogy": "像法庭辩论——控方说完辩方必须反驳，反驳不掉的才站得住",
    },
    "证据等级": {
        "plain": "给每条信息打等级——A 一手权威、B 二手可靠、C 单源、D 未验证",
        "analogy": "像新闻可信度——官方通报 A 级，大媒转述 B 级，路边消息 C 级",
    },
    "来源独立性": {
        "plain": "两条证据如果都引用同一个原始来源，算一条不算两条",
        "analogy": "像传话游戏——10 个人传同一句话，源头只有一个不算 10 个证据",
    },
}


def explain(term: str, layer: str = "both") -> str:
    """获取术语的通俗解释。
    layer: 'plain' / 'analogy' / 'both'
    """
    entry = PLAIN_GLOSSARY.get(term.lower().strip())
    if not entry:
        # 模糊匹配
        for key, val in PLAIN_GLOSSARY.items():
            if key in term.lower() or term.lower() in key:
                entry = val
                break
    if not entry:
        return f"<span class='term'>{term}</span>"
    if layer == "plain":
        return entry["plain"]
    if layer == "analogy":
        return entry["analogy"]
    return f"{entry['plain']}（{entry['analogy']}）"


def render_term_with_explanation(term: str) -> str:
    """渲染成 markdown：术语 + 大白话解释 blockquote"""
    entry = PLAIN_GLOSSARY.get(term.lower().strip())
    if not entry:
        for key, val in PLAIN_GLOSSARY.items():
            if key in term.lower() or term.lower() in key:
                entry = val
                break
    if not entry:
        return f"**{term}**"
    return f"**{term}**\n\n> **大白话**：{entry['plain']}\n> **类比**：{entry['analogy']}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Available terms:")
        for t in PLAIN_GLOSSARY:
            print(f"  - {t}")
    else:
        print(render_term_with_explanation(" ".join(sys.argv[1:])))
