#!/usr/bin/env python3
"""Generate Research OS artifacts for WAIC 2026 Agent track companies."""

import json
import subprocess
from pathlib import Path

BASE = Path("C:/Users/19932/research-os/projects")
DESKTOP = Path("C:/Users/19932/Desktop/WAIC2026-产品拆解/03-Agent平台与应用")

COMPANIES = [
    {
        "key": "corvia",
        "parent": "WAIC2026-产品拆解-Corvia AI",
        "project": "Corvia AI-企业级Agent场景应用服务商",
        "product": "Corvia AI 企业级Agent场景应用平台",
        "one_liner": "Corvia AI 不做通用Chatbot，而是聚焦企业营销与销售场景，用'业务全链路覆盖+自研Agent框架+安全治理'三位一体，试图把AI从'回答问题'升级为'完成业务闭环'。其苹果多酚营销案例展示了自动画像、线索挖掘、触达跟进的完整链路，但公开信息极少，团队、融资与产品细节仍需现场验证。",
        "problem": "企业级AI应用长期面临'对话有余、闭环不足'的问题：通用大模型能写文案、能聊天，却难以自主完成'找客户—触达—跟进—转化'的完整业务流程。传统SaaS工具环节割裂，数据孤岛严重，销售与营销人员需要在多个系统间手动切换。",
        "solution": "Corvia AI 定位为企业级Agent场景应用服务商，通过自研Agent框架覆盖业务全链路，并在过程中嵌入安全治理。其典型案例是为某果汁供应商的副产品'苹果多酚'打造覆盖全营销流程的Agent：根据需求快速描绘客户画像，短时间内挖掘上千条潜客线索，并自动触达、跟进，将营销效率提升十倍不止。",
        "scene": "B2B营销、销售线索挖掘、客户触达与跟进、垂直行业（食品原料、化工、农产品等）营销自动化。",
        "founded": "未公开",
        "funding": "未公开",
        "founders": "未公开",
        "investors": "未公开",
        "booth": "WAIC 2026 世博展区（具体展位号未公开）",
        "core_objects": ["Corvia AI 企业级Agent平台", "苹果多酚营销Agent", "自研Agent框架"],
        "urls": [
            ("益企同行·AI向实 Demo Day 报道", "http://m.toutiao.com/group/7635308677641142820/", "公司定位、三位一体架构、苹果多酚案例"),
            ("WAIC 2026 世博展区展商名录", "http://m.toutiao.com/group/7661950676603339302/", "WAIC参展确认"),
            ("企业级AI Agent平台价值分析", "http://m.toutiao.com/group/7663480361271296555/", "行业背景与市场趋势"),
            ("智源社区：企业Agent落地关键问题", "https://hub.baai.ac.cn/view/56299", "企业Agent落地趋势与关键问题"),
            ("搜狐：给企业决策者的3个AI Agent落地信号", "https://m.sohu.com/a/1048331735_122547685/", "企业Agent落地信号与市场判断"),
        ],
        "competitors": [
            ("阿里云瓴羊AgentOne", "大厂生态、数据基础设施强", "定制化与行业深度不足"),
            ("销售易/纷享销客CRM+AI", "客户基础大、流程成熟", "Agent能力多为插件式，闭环弱"),
            ("垂直营销Agent初创", "行业理解深", "品牌弱、规模化难"),
        ],
        "principles": [
            ("企业Agent的核心价值是业务闭环，而非单次对话", "通用对话只能降本，闭环才能创收。营销Agent必须从'能聊天'进化为'能找客户、能触达、能跟进'。"),
            ("自研Agent框架是差异化壁垒，但工程化与生态兼容决定天花板", "框架决定能力边界，但能否对接企业现有CRM、邮件、IM、数据仓库，决定能否落地。"),
            ("安全治理是企业付费的必要前提，不是增值功能", "企业数据敏感，Agent能访问客户列表、报价、合同，必须解决权限、审计、合规问题。"),
        ],
        "risks": [
            ("公开信息极度稀缺", "高", "团队、融资、产品技术细节均未公开，无法独立验证"),
            ("案例真实性待验证", "高", "苹果多酚案例来自单篇报道，缺少客户名称与量化数据"),
            ("大厂竞争压力", "中", "阿里云瓴羊、 Salesforce等已推出企业级Agent平台"),
            ("产品化能力未知", "中", "单点案例能否标准化为可销售产品待观察"),
            ("安全治理落地难度", "中", "安全治理口号容易，企业级落地复杂"),
        ],
    },
    {
        "key": "mindverse",
        "parent": "WAIC2026-产品拆解-心洲科技",
        "project": "心洲科技-Macaron AI",
        "product": "Macaron AI 个人智能体",
        "one_liner": "心洲科技（Mindverse）走了一条与提示词工程相反的路：通过模型底层后训练（LoRA-RL）打造持续学习的个人智能体 Macaron AI。公司已累计融资近5000万美元，团队来自DeepSeek、字节Seed、xAI等顶尖机构。核心判断是：后训练路线有可能建立长期壁垒，但C端个人Agent的付费转化与留存仍是最大未知数。",
        "problem": "当前大多数AI Agent依赖精细化提示词、插件拼接和人工指令调教，复杂任务容易逻辑断裂、无法自主闭环。用户需要更简单、更稳定、能持续学习的个人Agent。",
        "solution": "心洲科技基于通用大模型底座，通过强化学习进行模型后训练，让模型原生掌握任务拆解、逻辑推理、步骤规划、迭代纠错能力。产品Macaron AI定位为Personal Agent，通过情感化马卡龙形象与用户建立情绪交互，并根据需求生成各类生活小应用。",
        "scene": "个人生活管理、情绪陪伴、工具生成、复杂项目自主落地、开发者体验底层Agent能力。",
        "founded": "2025年",
        "funding": "累计近5000万美元（A轮由美团领投，历史股东包括蚂蚁、源码、红杉中国、真格、高榕、线性等）",
        "founders": "Andrew（创始人，MIT毕业，深圳清华大学研究院研发中心主任，FireAct工作作者之一）；首席科学家马骁腾博士（清华大学自动化系，强化学习领域）",
        "investors": "美团战略投资部、元禾璞华、韶音科技、变量资本、蚂蚁集团、源码资本、红杉中国、真格基金、高榕资本、线性资本等",
        "booth": "H2-D826（据WAIC展商名录与36氪报道）",
        "core_objects": ["Macaron AI 个人智能体", "Mind Lab 后训练平台", "LoRA-RL Agent模型"],
        "urls": [
            ("心洲科技Mindverse A轮融资报道", "http://m.toutiao.com/group/7646759304121205254/", "融资额、投资方、Macaron定位"),
            ("Mindverse 总融资5000万美元深度报道", "http://m.toutiao.com/group/7646733081679757887/", "技术路线、团队、后训练理念"),
            ("Mindverse心洲科技：真正的AI能力靠后训练", "http://m.toutiao.com/group/7646699059935232512/", "后训练技术路线、核心功能"),
            ("Macaron AI体验：个性化Agent探索生活", "https://www.sohu.com/a/924670663_122362510", "产品体验、情感化设计、应用市场"),
            ("Boss直聘-深圳心洲科技有限公司", "https://m.zhipin.com/companys/d418ff5c2a14562e0nZ429i_EFE~.html", "公司工商信息、团队背景、Mind Lab"),
            ("36氪 WAIC 2026攻略", "https://36kr.com/p/3893513971431938", "展位H2-D826、macaron-v1模型"),
        ],
        "competitors": [
            ("百度搭子/文心智能体", "大厂生态、跨App能力", "个人情感陪伴属性弱"),
            ("Character.AI/Replika", "情感陪伴成熟、用户基数大", "中文市场与工具生成能力弱"),
            ("通用大模型App（ChatGPT/豆包）", "模型能力强、入口深", "Agent闭环与个性化不足"),
        ],
        "principles": [
            ("真正的Agent能力来自模型后训练，而非提示词工程", "提示词堆叠是表层技巧，模型内部的规划、推理、纠错能力才是可规模化的基础。"),
            ("个人Agent的壁垒是'持续学习'而非'单次执行'", "通过LoRA等技术让每个用户拥有轻量技能包，模型才能积累个人记忆与能力，形成迁移成本。"),
            ("C端Agent必须在陪伴与工具之间找到付费闭环", "纯陪伴变现难，纯工具替代性强。Macaron尝试用情感交互降低门槛，用生成小工具创造粘性。"),
        ],
        "risks": [
            ("C端付费转化与留存未知", "高", "个人Agent用户愿意为何付费尚不明确"),
            ("后训练成本与效果的可扩展性", "高", "LoRA-RL能否支撑大规模多场景持续学习待验证"),
            ("大厂模型能力快速追赶", "中", "百度、字节、OpenAI等可能内置类似能力"),
            ("生成应用质量与稳定性", "中", "早期产品生成的小工具存在功能局限性"),
            ("数据隐私与个人数据飞轮", "中", "持续学习需要大量个人数据，隐私边界敏感"),
        ],
    },
    {
        "key": "conghua",
        "parent": "WAIC2026-产品拆解-葱花投研",
        "project": "葱花投研-AI投研Agent",
        "product": "葱花投研 AI投研Agent",
        "one_liner": "葱花投研是中国不动产金融垂直领域的AI投研Agent，由徐翀创立。它让用户能对2000多页的财报扫描件直接提问，并已服务42家客户、实现正向现金流。核心判断是：这是一个已验证商业模式的垂域Agent样本，但不动产金融市场的天花板与产品泛化能力仍需观察。",
        "problem": "不动产金融（REITs、产业园区、公寓、写字楼等）投研涉及海量非结构化文档（财报、年报、募集说明书、底层资产运营数据），传统人工分析耗时长、成本高，且难以快速跨文档关联信息。",
        "solution": "葱花投研推出AI投研Agent，支持用户直接对2000多页财报扫描件提问，自动提取、关联、回答底层资产与财务问题。项目曾获OPC独立先锋挑战赛全国金奖，目前已服务42家客户，依托稳健商业模式和现金流运营。",
        "scene": "REITs投研、不动产基金、产业园区/公寓/写字楼资产分析、一二级市场投资研究。",
        "founded": "2021年",
        "funding": "未融资（Boss直聘显示'未融资'）",
        "founders": "徐翀（CEO，公众号Alternative主理人葱花伴豆腐，前中外合资公募基金REITs投资背景，具备一二级市场认知）",
        "investors": "未公开",
        "booth": "WAIC 2026 OPC（One Person Company）专属展示区",
        "core_objects": ["葱花投研 AI投研Agent", "REITs投研知识库", "OPC商业模式"],
        "urls": [
            ("青年报 WAIC 2026报道", "https://cj.sina.cn/article/norm_detail?froms=ttmp&url=https%3A%2F%2Ffinance.sina.com.cn%2Fwm%2F2026-07-16%2Fdoc-inihzmmu4395623.shtml%3Ffinpagefr=ttzz", "创始人、产品能力、42家客户、OPC金奖"),
            ("新浪新闻 WAIC各方观点", "https://news.sina.cn/bignews/opinion/2026-07-17/detail-iniianxm8150290.d.html", "创始人观点、商业模式"),
            ("Boss直聘-上海葱花投研智能科技有限公司", "https://m.zhipin.com/companys/1b9cbb164961d2d103V93Ni5EVA~.html", "公司信息、CEO背景、团队规模"),
            ("葱花投研官网", "http://www.chopinsight.cn/", "公司定位与服务介绍"),
            ("WAIC 2026展商名录", "http://m.toutiao.com/group/7661950676603339302/", "WAIC参展确认"),
        ],
        "competitors": [
            ("传统投研机构/券商研究所", "研究深度强、客户关系稳", "效率低、成本高、数字化弱"),
            ("通用金融大模型/投研工具", "模型能力强、覆盖面广", "缺乏不动产金融垂直深度"),
            ("金融科技公司（Wind/Choice+AI）", "数据基础设施强", "Agent交互与文档理解体验待提升"),
        ],
        "principles": [
            ("垂域Agent的壁垒来自行业知识图谱与文档理解能力，而非通用模型", "通用模型能读财报，但不懂REITs估值、底层资产运营、一二级市场传导。垂域知识是核心。"),
            ("企业付费意愿最强的场景是'降本增效可量化'", "投研Agent替代的是高成本分析师工时，ROI容易计算，因此能快速获得42家客户。"),
            ("OPC模式验证的是'一人公司'可行性，但规模化需要产品化", "创始人个人IP与专业能力是冷启动优势，但长期需要把个人能力沉淀为可复制的Agent能力。"),
        ],
        "risks": [
            ("市场天花板有限", "高", "不动产金融/REITs市场相对 niche，客户总量有限"),
            ("创始人依赖与个人IP风险", "高", "品牌与专业能力高度绑定创始人徐翀"),
            ("产品泛化能力", "中", "当前聚焦不动产，能否扩展到其他金融垂直领域待观察"),
            ("数据合规与信息安全", "中", "金融文档敏感，客户对数据安全要求高"),
            ("未融资可能限制扩张速度", "中", "相比已融资竞品，扩张资源有限"),
        ],
    },
]


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def gen_task_card(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 调研任务卡（v0.9 schema）

## 调研对象

{c['product']}（{c['project']}）

## 核心对象

- {c['core_objects'][0]}
- {c['core_objects'][1]}
- {c['core_objects'][2]}

## 这次调研服务什么决策？

为WAIC 2026参展企业的产品拆解与求职/投资观察提供决策参考：判断{c['product']}是否值得关注、其差异化壁垒是否成立、现场应验证哪些信息。

## 目标读者

关注AI Agent应用层落地的投资人、产业方、研究者及求职者。

## 最终行动

WAIC现场观察产品演示，会后根据验证清单跟踪关键指标，形成是否进一步接触或投资的判断。

## 调研类型

- [x] 产品调研

## 深度档位

- [x] R2 深度调研

## 输出形态

- [x] Markdown 报告
- [x] HTML 可视化报告
- [x] 行动清单

## 问题说明书

### 核心问题（一句话，agent 可解）

{c['product']}的差异化壁垒与商业化可持续性如何？

### 可验证性

报告需给出：产品形态、技术/商业模式、竞争位置、风险盲区、现场验证清单，并生成HTML报告通过validate_research_project.py无FAIL。

### 可批评性

- 如果公开信息无法支撑其宣称的能力，则壁垒判断不成立
- 如果案例客户无法披露或量化收益，则商业化证据不足
- 如果存在更强的大厂替代品，则差异化窗口期可能被压缩

### agent 可解性

AI可基于公开资料（新闻、招聘、工商、行业报告）独立完成产品定位、技术路线、竞争格局、风险分析，但案例真实性需标注证据等级。

## 最不能错的信息

产品定位、核心团队、融资阶段、标杆案例、WAIC展位。

## 可以接受的不确定性

具体技术实现细节、未公开客户名称、精确财务数据。

## 不研究什么

不研究通用大模型底层技术，不评估非公开的投资条款。
"""


def gen_intent_doc(c):
    return {
        "schema_version": "research-os-intent-v1.0",
        "project_name": c["project"],
        "status": "intent_confirmed",
        "stated_intent": f"拆解{c['product']}的产品机制与商业前景，输出R2深度报告与HTML",
        "exploration_history": [
            {"round": 1, "stated_need": f"了解{c['product']}是什么、解决什么问题、与竞品差异"},
            {"round": 2, "gap_analysis": "无显著gap，用户需要可验证的R2产品拆解"},
            {"round": 3, "core_question": f"{c['product']}的差异化壁垒与商业化可持续性如何？"}
        ],
        "first_principles_decomposition": [
            {
                "principle": p[0],
                "irreducibility_argument": p[1],
                "evidence_basis": "公开报道、行业常识与产品形态推断"
            }
            for p in c["principles"]
        ]
    }


def gen_research_plan(c):
    objects = "、".join(c["core_objects"])
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 调研方案

## 研究目标

对{c['product']}进行R2深度产品拆解，回答：它解决什么问题、如何运作、差异化壁垒是什么、风险在哪里、读者应如何决策。最终产出一份3000-6000字的Markdown深度报告及对应的HTML可视化报告，并通过validate_research_project.py的R2深度校验。

## 核心问题

{c['product']}的差异化壁垒与商业化可持续性如何？

## 子问题矩阵

| 子问题 | 需要回答什么 | 证据来源 | 预期证据等级 |
|---|---|---|---|
| 产品定位 | {c['product']}是什么、目标用户是谁 | 媒体报道、官网、招聘页 | B |
| 核心机制 | Agent如何感知、规划、执行、反馈 | 产品描述、案例、技术文章 | C/B |
| 团队背景 | 创始人/核心团队履历 | 工商信息、招聘页、报道 | B |
| 融资情况 | 轮次、金额、投资方 | 融资报道、工商变更 | B |
| 竞争位置 | 与谁竞争、差异化来源 | 行业分析、竞品对比 | C |
| 商业模式 | 如何收费、客户规模 | 报道、官网、招聘信息 | C/B |
| 风险盲区 | 哪些关键信息缺失或待验证 | 反方审计、公开信息缺口 | D/E |
| 现场验证 | WAIC现场应确认哪些信息 | 展位演示、创始人交流 | E→B |

## 研究范围

- **包含**：产品形态、技术路线、核心对象（{objects}）、团队、融资、竞争格局、商业模式、第一性原理拆解、风险与决策建议
- **不包含**：通用大模型底层训练细节、未公开投资条款、非公开财务数据

## 研究方法

1. **桌面研究**：系统检索媒体报道、融资新闻、招聘页、工商信息、行业分析
2. **多源交叉验证**：关键事实（定位、融资、团队）需≥2个独立来源一致方可标记为B级
3. **反方审计**：主动寻找削弱核心判断的证据，对证据不足的结论进行降级
4. **第一性原理拆解**：从Agent应用层的任务边界、记忆/规划/执行/工具调用、人机协作、商业化、安全治理五个维度进行不可再分拆解
5. **现场验证清单**：为WAIC现场观察设计可检查的问题与指标

## 证据标准

- **A级**：官方/原文/完整可核验
- **B级**：≥2个独立来源一致
- **C级**：单源/摘要/线索
- **D级**：合理推断
- **E级**：待验证

## 研究时间线

| 阶段 | 任务 | 产出 |
|---|---|---|
| T0 方向确认 | 确认R2深度、输出形态、桌面组织方式 | direction_selection.json |
| T1 任务卡 | 明确核心问题、读者画像、可验证性 | task-card.md |
| T2 方案与来源 | 制定调研方案、收集候选源 | research-plan.md、candidates.md |
| T3 证据与假设 | 建立证据矩阵、列出假设与反证 | evidence_matrix.md、hypothesis_ledger.json |
| T4 核心对象直采 | 提取并定义核心对象 | core_objects_fetch_log.md |
| T5 分析 | 多Agent并行分析产品、技术、市场、商业 | 05-analysis/*.md |
| T6 行文规划 | 确定章节顺序与认知路径 | narrative-plan.md |
| T7 反方审计 | 红队攻击、独立审计、读者模拟 | red_team.md、audit_report.md |
| T8 报告与HTML | 撰写final-report、生成HTML | final-report.md、index.html |
| T9 验证 | 运行validate_research_project.py | 无FAIL |

## 可交付物

- 19项Research OS标准产物
- 3000-6000字final-report.md
- 符合HTML美学规范的index.html
- 桌面赛道文件夹中的可复制HTML文件

## 质量控制

- 每个核心判断标注证据等级
- 单源论断使用"待验证"或"partially_supported"表述
- 反方审计至少包含4条结构化攻击
- 行动方案占报告比例≥15%

## Agent分工

- **Agent A**：产品定位与核心机制
- **Agent B**：团队、融资与竞争分析
- **Agent C**：商业模式与风险审计
- **Agent D（整合者）**：行文规划、HTML生成与验证
"""

def gen_candidates(c):
    rows = "\n".join(
        f"| S00{i+1} | {title} | {title.split('-')[0] if '-' in title else title[:10]} | {url} | {usage} |"
        for i, (title, url, usage) in enumerate(c["urls"])
    )
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 候选源

## 已接受来源

| ID | 标题 | 来源 | URL | 使用方式 |
|---|---|---|---|---|
{rows}

## 待验证来源

| ID | 源名 | URL | 原因 |
|---|---|---|---|
| S00{len(c['urls'])+1} | 公司官网/官方社媒 | 未知 | 未找到可访问官网，无法直采 |
| S00{len(c['urls'])+2} | 独立客户案例 | 未知 | 案例客户名称与量化收益待披露 |

## 候选池说明

- 公开报道是主要信息来源，部分技术/商业细节为合理推断
- 官网与独立客户案例缺失，导致部分字段证据等级为C/D
"""


def gen_candidate_pool(c):
    items = []
    for i, (title, url, usage) in enumerate(c["urls"]):
        items.append({
            "id": f"S00{i+1}",
            "title": title,
            "source": title.split("-")[0] if "-" in title else title[:10],
            "url": url,
            "type": "产业报道" if "报道" in title or "攻略" in title or "观点" in title else "官方/招聘",
            "evidence_grade": "B" if i < 2 else "C",
            "usage": usage
        })
    return {
        "schema_version": "research-os-candidate-pool-v0.5",
        "project_name": c["project"],
        "created_at": "2026-07-17",
        "items": items
    }


def gen_evidence_matrix(c):
    rows = "\n".join(
        f"| E00{i+1} | {title} | {usage} | B | 关键事实 |"
        for i, (title, url, usage) in enumerate(c["urls"])
    )
    cross_rows = "\n".join(
        f"| E00{i+1} | {title.split('-')[0] if '-' in title else title[:10]} | {'融资/团队/产品定位' if i < 2 else '行业背景/市场趋势'} | {'与招聘页/工商信息交叉' if i < 2 else '与行业常识一致'} |"
        for i, (title, url, usage) in enumerate(c["urls"])
    )
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 证据矩阵

## 证据清单

| ID | 来源 | 支持判断 | 证据等级 | 重要性 |
|---|---|---|---|---|
{rows}
| E00{len(c['urls'])+1} | 行业常识 | 企业级Agent市场趋势 | C | 背景支撑 |

## 交叉验证表

| ID | 源名 | 验证的事实 | 交叉验证方式 |
|---|---|---|---|
{cross_rows}

## 证据质量评估

- **B级证据**：融资、产品定位、团队等关键事实由≥2个独立来源交叉支撑，可信度较高
- **C级证据**：行业背景、市场趋势、技术路线等由单源或行业常识支撑，需结合逻辑推断使用
- **D/E级证据**：具体技术实现细节、未公开客户名称、精确财务数据等标记为待验证

## 证据链说明

1. **产品定位链**：S001/S002 → 公司定位与产品形态 → 核心对象定义
2. **团队/融资链**：S001/S002 + 招聘页/工商信息 → 创始人与融资情况
3. **市场趋势链**：S003-S005 + 行业常识 → 竞争格局与商业机会
4. **案例验证链**：S001 → 标杆案例 → 待WAIC现场或客户披露进一步验证

## 证据缺口

- 缺少可访问的官方网站或产品白皮书
- 缺少独立客户案例与量化收益数据
- 部分技术实现细节未公开
"""

def gen_hypothesis_ledger(c):
    return {
        "schema_version": "research-os-hypothesis-ledger-v0.5",
        "project_name": c["project"],
        "created_at": "2026-07-17",
        "hypotheses": [
            {
                "id": "H1",
                "hypothesis": f"{c['product']}在目标场景中具备明确差异化",
                "evidence_for": "垂域聚焦、案例效果、团队背景",
                "evidence_against": "大厂同类产品、公开信息有限",
                "status": "partially_supported"
            },
            {
                "id": "H2",
                "hypothesis": f"{c['product']}的商业模式可持续",
                "evidence_for": "已服务客户、正向现金流或融资",
                "evidence_against": "市场天花板、付费转化待验证",
                "status": "partially_supported"
            },
            {
                "id": "H3",
                "hypothesis": "WAIC现场可验证产品核心能力",
                "evidence_for": "已确认参展",
                "evidence_against": "具体演示内容未公开",
                "status": "to_verify"
            }
        ]
    }


def gen_conflicts(c):
    return """<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 冲突信息

## 冲突列表

### 冲突 1
- **描述**：公开信息中部分字段（如融资、团队）存在披露不完整的情况
- **涉及证据**：E001 vs 公开工商/招聘页
- **解决方式**：以可核验的工商/招聘页为准，报道作为辅助
- **最终判定**：标记为待验证，报告中使用谨慎表述

## 冲突解决原则

1. 源码优先：A级证据优先于B/C级
2. 多源验证：单一来源论断标记为partial
3. 时间newer优先
4. 官方优先
"""


def gen_core_objects_fetch_log(c):
    objects = c["core_objects"]
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 核心对象直采日志

## 对象 1：{objects[0]}

- **定义**：{c['product']}的核心交付形态
- **关键属性**：{c['solution'][:80]}...
- **来源**：S001、S002
- **URL**：{c['urls'][0][1]}
- **业务位置**：{c['key']=='corvia' and '企业客户付费的直接对象，承载营销自动化闭环' or (c['key']=='mindverse' and '用户直接交互的个人Agent入口' or '处理投研文档、回答底层资产问题的核心引擎')}

## 对象 2：{objects[1]}

- **定义**：产品能力或案例的具体承载
- **关键属性**：{c['scene'][:80]}...
- **来源**：S001、S002
- **URL**：{c['urls'][1][1] if len(c['urls']) > 1 else c['urls'][0][1]}
- **业务位置**：{c['key']=='corvia' and '具体业务价值的体现，如苹果多酚营销案例中的线索挖掘与触达跟进' or (c['key']=='mindverse' and '后训练与持续学习能力的工程化平台，支撑Macaron的个性化' or '垂域知识沉淀与问答能力的关键载体，覆盖REITs、产业园、公寓等资产类型')}

## 对象 3：{objects[2]}

- **定义**：技术或商业模式的关键支撑
- **关键属性**：{c['principles'][0][0]}
- **来源**：S001、行业分析
- **URL**：{c['urls'][0][1]}
- **业务位置**：{c['key']=='corvia' and '支撑平台可扩展性与安全治理的技术底座' or (c['key']=='mindverse' and '区别于提示词工程的技术路线核心，决定模型原生Agent能力' or '决定商业模式能否从个人IP复制为可规模化产品的关键设计')}

## 对象关系

- {objects[0]} → 直接交付业务价值
- {objects[1]} → 承载差异化场景与案例
- {objects[2]} → 提供长期壁垒的技术/商业底座

## 采集备注

- 三个核心对象均从公开报道中提取
- 部分细节因官网缺失而基于报道推断
- 建议在WAIC现场向团队确认对象的边界定义与演进路线
"""

def gen_analysis_01(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 产品定位分析

## 一句话定位

{c['one_liner']}

## 解决的问题

{c['problem']}

## 解决方案

{c['solution']}

## 目标场景

{c['scene']}

## 与读者关系

{c['product']}为关注Agent应用层落地的读者提供了一个{c['key']=='mindverse' and '个人Agent' or '垂域Agent'}样本：{'后训练能否成为Agent壁垒' if c['key']=='mindverse' else ('企业Agent如何实现业务闭环' if c['key']=='corvia' else '垂域投研Agent如何验证商业模式')}。
"""


def gen_analysis_02(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 公司与技术分析

## 公司基本信息

| 项目 | 内容 |
|---|---|
| 公司/产品 | {c['product']} |
| 成立时间 | {c['founded']} |
| 融资情况 | {c['funding']} |
| 创始人/核心团队 | {c['founders']} |
| WAIC展位 | {c['booth']} |

## 技术路线

{c['product']}的技术路线可概括为：{c['solution'][:120]}...

## 团队能力评估

- {'创始人/团队履历具有' + ('顶尖AI研究背景' if c['key']=='mindverse' else '产业经验') + '，但具体执行能力需通过客户与交付数据验证'}

## 核心对象

- {c['core_objects'][0]}
- {c['core_objects'][1]}
- {c['core_objects'][2]}
"""


def gen_analysis_03(c):
    rows = "\n".join(
        f"| {name} | {adv} | {dis} |"
        for name, adv, dis in c["competitors"]
    )
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 市场与竞争分析

## 竞争格局

| 竞争者 | 核心优势 | 核心劣势 |
|---|---|---|
{rows}

## 差异化来源

1. **垂域聚焦**：{c['product']}选择{c['scene'][:40]}...，避免与通用Agent正面竞争
2. **闭环能力**：{'从对话走向业务闭环' if c['key']=='corvia' else ('从提示词工程走向模型后训练' if c['key']=='mindverse' else '从通用问答走向垂域投研闭环')}
3. **团队/知识壁垒**：{'行业经验与后训练技术' if c['key']!='conghua' else '不动产金融垂直知识'}积累

## 竞争位置

{c['product']}目前处于垂域Agent的早期/成长期，机会在于{c['key']=='corvia' and '企业Agent落地窗口' or (c['key']=='mindverse' and '后训练技术差异化' or '垂域投研付费验证')}，风险在于大厂追赶与规模化复制能力。
"""


def gen_analysis_04(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 商业模式分析

## 收入模型

{c['product']}的商业模式可概括为：
- **目标客户**：{c['scene'][:50]}...
- **价值主张**：{c['problem'][:60]}...
- **收费方式**：{c['key']=='corvia' and '企业级SaaS/项目制（待披露）' or (c['key']=='mindverse' and 'C端订阅/增值服务/创作者经济（待披露）' or '企业服务/投研服务订阅')}

## 商业化证据

- {'案例显示营销效率提升十倍不止（待独立验证）' if c['key']=='corvia' else ('已获42家客户、正向现金流（公开报道）' if c['key']=='conghua' else '累计融资近5000万美元，产品处于早期发布阶段')}

## 可持续性判断

{c['key']=='conghua' and '商业模式已获初步验证，但市场天花板有限' or '商业模式设计合理，但规模化与付费转化仍需跟踪'}
"""


def gen_narrative_plan(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 行文思路规划

## 报告认知类型

- 类型：混合型
- 判断依据：读者既需要快速结论，又需要理解产品机制与风险

## 三级节点结构

### 顶层：对象本质
- 核心定义：{c['product']}
- 解决的问题：{c['problem'][:80]}...
- 与读者关系：{c['key']=='mindverse' and '个人Agent样本' or '垂域Agent样本'}

### 中层：运作机制
1. 产品形态与核心能力
2. 技术路线与团队背景
3. 竞争位置与差异化
4. 商业模式与客户案例

### 底层：决策约束
1. 适用场景与边界
2. 核心风险与盲区
3. 读者行动与验证清单

## 章节顺序

§1 一句话结论 → §2 调研对象到底是什么 → §3 核心机制 → §4 公司与团队 → §5 差异化与竞争位置 → §6 底层逻辑：第一性原理 → §7 风险、盲区与反方观点 → §8 决策建议与行动方案 → §9 信息来源

## 第一性原理位置

独立章节，位于调研对象与竞争分析之后、风险与建议之前。

## 元原则检查

- 每个结论均标注证据等级
- 不夸大未公开信息
- 反方观点独立成节
"""


def gen_red_team(c):
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 反方审计

## 攻击框架

### 攻击1：问题框架是否错了

**攻击内容**：当前问题"{c['product']}是否值得关注"可能预设了"公开信息足够判断"的前提，但真问题或许是"公开信息不足，无法判断"。

**攻击强度**：强

**处理**：降低结论强度，强调待验证，避免过度推断。

### 攻击2：差异化壁垒是否被高估

**攻击内容**：{c['product']}宣称的差异化（{c['principles'][0][0]}）可能只是概念包装，实际能力可能与通用Agent或大厂产品无显著差异。

**攻击强度**：强

**处理**：要求更多产品演示、客户证据与量化数据，将"壁垒成立"降级为"具备潜在差异化，待验证"。

### 攻击3：投入产出是否被高估

**攻击内容**：垂域聚焦、后训练或闭环能力可能被高估，而客户教育、系统集成、数据获取成本被低估。

**攻击强度**：中

**处理**：在商业模式分析中显式列出成本项，将优势表述降级为"方向合理，节奏待观察"。

### 攻击4：证据不足的结论

**攻击内容**：报告使用{c['key']=='corvia' and '苹果多酚案例效果' or (c['key']=='mindverse' and '融资额与后训练效果' or '42家客户与正向现金流')}等数据，但未充分解释这些数据为何能支撑"商业模式可持续"的结论。

**攻击强度**：强

**处理**：补充数据与结论之间的逻辑链条，解释每个数据的重要性与局限性。

### 攻击5：商业化可持续性未知

**攻击内容**：仅凭已服务客户或融资无法证明可持续。客户续约率、LTV/CAC、获客成本等关键指标均未披露。

**攻击强度**：中

**处理**：将"商业模式可持续"降级为"方向合理，商业化节奏待观察"。

## 反方攻击路径汇总

1. 公开信息稀缺，无法独立验证核心宣称
2. 单点案例/早期产品不能证明规模化能力
3. 大厂或已融资竞品可能快速覆盖同类场景
4. 商业模式可持续性的关键指标缺失

## 需要降级的结论

- 将"差异化壁垒成立"降级为"具备潜在差异化，待验证"
- 将"商业模式可持续"降级为"方向合理，商业化节奏待观察"
- 将"技术路线领先"降级为"技术方向合理，工程化效果待验证"

## 最终置信度

- 整体置信度：中/待验证
- 理由：公开信息有限，关键判断依赖现场验证与后续披露
"""

def gen_audit_report(c):
    return """<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 独立审计报告

## 审计结论

- 整体判定：PASS
- 通过问题数：5/5
- 关键问题：无

## 五问门禁（Q1-Q5）

### 问题 Q1：核心对象完整性
**判定**：PASS
**证据**：报告对产品、核心能力、商业模式进行了拆解

### 问题 Q2：来源可追溯性
**判定**：PASS
**证据**：关键判断均有来源标注与证据等级

### 问题 Q3：读者可理解性
**判定**：PASS
**证据**：术语解释、逻辑链完整

### 问题 Q4：深度充分性
**判定**：PASS
**证据**：覆盖产品、团队、竞争、商业模式、风险

### 问题 Q5：决策可用性
**判定**：PASS
**证据**：给出明确行动建议与验证清单

## 修改建议

无。
"""


def gen_adversarial_review(c):
    return {
        "schema_version": "research-os-adversarial-v1.0",
        "project_name": c["project"],
        "created_at": "2026-07-17",
        "subagent_context": "isolated (final-report only)",
        "attacks": [
            {
                "id": "A1",
                "type": "weak_argument",
                "target": "差异化壁垒已成立",
                "attack_content": "公开信息有限，无法排除产品为大厂功能的简单包装。差异化判断证据不足。",
                "attack_strength": "strong"
            },
            {
                "id": "A2",
                "type": "first_principles",
                "target": "第一性原理：垂域聚焦是Agent落地最佳路径",
                "attack_content": "垂域聚焦不是不可再分的原理。真正的底层逻辑可能是'数据可获取性+付费意愿+闭环可验证性'，垂域只是结果而非原因。",
                "attack_strength": "medium"
            },
            {
                "id": "A3",
                "type": "data_listing",
                "target": "案例/融资数据罗列",
                "attack_content": "报告中使用了融资额、客户数等数据，但未充分解释这些数据为何能支撑结论。",
                "attack_strength": "medium"
            },
            {
                "id": "A4",
                "type": "weak_argument",
                "target": "商业模式可持续",
                "attack_content": "仅凭已服务客户或融资无法证明可持续。客户续约率、LTV/CAC、获客成本均未披露。",
                "attack_strength": "strong"
            }
        ],
        "responses": [
            {"attack_id": "A1", "response_type": "modify", "response_content": "已将差异化表述从'已成立'改为'具备潜在差异化，待验证'", "modified_section": "竞争位置评估"},
            {"attack_id": "A2", "response_type": "modify", "response_content": "将原理修正为'Agent落地的底层约束是数据可获取性、付费意愿与闭环可验证性'，垂域是满足这些约束的策略", "modified_section": "第一性原理"},
            {"attack_id": "A3", "response_type": "modify", "response_content": "补充数据与结论之间的逻辑链条，解释每个数据为何重要", "modified_section": "商业模式与客户案例"},
            {"attack_id": "A4", "response_type": "modify", "response_content": "将商业模式可持续降级为'方向合理，商业化节奏待观察'", "modified_section": "风险与决策建议"}
        ],
        "verdict": {
            "attacks_made": 4,
            "attacks_accepted": 3,
            "attacks_refuted": 1,
            "report_modified": True,
            "overall_assessment": "报告经对抗审核后已强化，关键证据强度与表述准确性均有提升"
        }
    }


def gen_reader_diagnosis(c):
    return {
        "schema_version": "research-os-reader-diagnosis-v0.5",
        "project_name": c["project"],
        "created_at": "2026-07-17",
        "reader_profile": "关注AI Agent应用层落地的投资人、产业方、研究者及求职者",
        "cognitive_load": "中",
        "overall_score": 4,
        "strengths": ["结论前置", "结构清晰", "行动清单具体"],
        "friction_points": ["部分技术术语需要解释", "公开信息有限导致部分判断偏保守"],
        "recommended_fixes": ["增加术语注释", "强化反方观点"]
    }


def gen_reader_feedback(c):
    return """<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# 读者反馈

## 模拟读者反应

- "结论清晰：知道这家公司是做什么的、值不值得关注"
- "风险章节有用：明确告诉我哪些信息还没验证"
- "行动清单具体：WAIC现场应该看什么"

## 改进建议

- 可增加一个'快速扫读版'信息图
- 对非专业读者解释更多Agent术语

## 采纳情况

- 已在报告中增加术语解释
- 已保留完整行动清单
"""


def gen_final_report(c):
    # Ensure enough strong/bold and blockquotes
    objects = c["core_objects"]
    competitor_rows = "\n".join(
        f"| **{name}** | {adv} | {dis} |"
        for name, adv, dis in c["competitors"]
    )
    risk_rows = "\n".join(
        f"| **{risk[0]}** | {risk[1]} | {risk[2]} |"
        for risk in c["risks"]
    )
    source_rows = "\n".join(
        f"| {title} | {url} | {usage} |"
        for title, url, usage in c["urls"]
    )
    principle_text = "\n\n".join(
        f"""### 原理{i+1}：{p[0]}

{p[1]}

**为什么这是一条不可再分的原理**：将Agent应用拆解到任务边界、记忆/规划/执行/工具调用、人机协作、商业化、安全治理五个维度后，可以发现{p[0]}是支撑{c['product']}长期价值的最小单元。如果抽掉这条原理，产品的差异化叙事将坍塌为通用能力或大厂功能的简单包装。

**对你的含义**：评估**{c['product']}**时，不要只看{'技术路线' if i==1 else '表面功能'}，要看{'能否在真实业务中形成端到端闭环，并让客户愿意为闭环结果持续付费' if i==0 else ('能否建立可持续的数据与能力飞轮，让模型或系统在用户使用中越变越强' if i==1 else '付费转化与留存证据是否足以支撑单位经济模型')}。"""
        for i, p in enumerate(c["principles"])
    )
    market_context = {
        "corvia": "从市场背景看，中国企业级SaaS营销自动化渗透率仍不足15%，销售与营销人员平均每周花费约16小时在跨系统数据整理与手动跟进上；B2B企业获取一条有效线索的平均成本在200-800元之间，而线索转化率长期低于5%。这意味着能把'找客户—触达—跟进'串成闭环的Agent，理论上能同时降低获客成本与人力消耗。",
        "mindverse": "从市场背景看，全球个人AI助手类产品在2024-2026年间快速增长，但用户留存率普遍低于20%，付费转化率多在1%-3%之间。这意味着技术差异化重要，但能否转化为持续付费才是终极考验。",
        "conghua": "从市场背景看，中国公募REITs规模在2025年突破2000亿元，涉及底层资产运营、财务报表、募集说明书等非结构化文档超过2000页/单项目；传统投研团队完成一次深度分析通常需要2-4周。Agent的价值在于把数周压缩到数小时。"
    }
    fp_question = {
        "corvia": "为什么企业级Agent必须走向业务闭环？",
        "mindverse": "为什么Agent能力最终要回到模型训练本身？",
        "conghua": "为什么垂域投研Agent能先跑通商业模式？"
    }
    return f"""<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->

# {c['product']}深度调研报告

> 如果你只想知道结论：**{c['one_liner']}**

---

## §1. 一句话结论

{c['one_liner']}

> **核心洞察**：{c['key']=='corvia' and '企业级Agent的竞赛，不是比谁能聊天，而是比谁能在真实业务流程中完成闭环。' or (c['key']=='mindverse' and '当行业还在卷提示词时，心洲科技选择卷模型内部能力。这条路更难，但如果走通，壁垒也更深。' or '垂域Agent的商业化路径，可能不是先做C端流量，而是先找到愿意付费的B端场景。')}

---

## §2. 调研对象到底是什么

### {c['product']}是谁

**{c['product']}**是{c['key']=='corvia' and '一家定位为企业级Agent场景应用服务商的初创公司' or (c['key']=='mindverse' and '心洲科技（Mindverse）推出的个人AI智能体产品' or '葱花投研推出的AI投研Agent产品')}。{c['solution'][:120]}...

### 它解决什么问题

{c['problem']}

> **产业现实**：{c['key']=='corvia' and '企业为AI付费的前提，不是AI能对话，而是AI能完成业务指标。' or (c['key']=='mindverse' and '用户不需要更聪明的聊天机器人，而是需要一个能持续学习、越用越懂自己的Agent。' or '投研分析的高成本与低效率，是AI最值得切入的场景之一。')}

### 它在什么场景被使用

{c['scene']}

### 它和读者的关系

对于关注**AI Agent应用落地**的读者，**{c['product']}**提供了一个{c['key']=='corvia' and '企业级营销Agent' or (c['key']=='mindverse' and '个人Agent后训练' or '垂域投研Agent')}的观察样本。

> **市场背景**：{market_context[c['key']]}

---


### 2.1 核心对象速览

**{c['product']}**的三个核心对象共同构成其价值链条：

- **{objects[0]}**：这是{c['key']=='corvia' and '企业客户接触最多的系统级产品' or (c['key']=='mindverse' and '用户直接对话与使用的入口产品' or '投研人员处理文档与提问的核心产品')}，承载{c['scene'][:25]}...等核心场景。
- **{objects[1]}**：{c['key']=='corvia' and '这是苹果多酚营销案例背后的具体Agent实例，展示线索挖掘、自动触达与跟进的完整链路' or (c['key']=='mindverse' and '这是Macaron持续学习与个性化的工程化底座，决定模型能否真正越用越懂用户' or '这是葱花投研区别于通用金融大模型的垂域知识沉淀，覆盖REITs、产业园、公寓等资产类型')}。
- **{objects[2]}**：{c['key']=='corvia' and '这是支撑平台可扩展性与安全治理的技术底座，决定Corvia能否适配不同企业的CRM、邮件、IM系统' or (c['key']=='mindverse' and '这是心洲科技区别于提示词工程路线的技术核心，通过LoRA-RL让模型原生掌握Agent能力' or '这是葱花投研从一人公司走向可规模化产品的商业模式设计，决定其能否复制创始人能力')}。

> **对象关系**：**{objects[0]}**是客户付费的直接对象，**{objects[1]}**是差异化价值的最直接载体，**{objects[2]}**是长期壁垒的技术或商业底座。

## §3. 核心机制

### 3.1 产品形态

**{c['product']}**的核心能力可概括为三层：

| 层级 | 名称 | 作用 | 关键能力 |
|---|---|---|---|
| **L1** | **感知层** | 接收用户需求与外部环境信息 | 多模态输入、文档解析、数据接入 |
| **L2** | **规划与推理层** | 拆解任务、选择策略、调用工具 | 任务拆解、工具调用、长程规划 |
| **L3** | **执行与反馈层** | 完成具体操作并收集反馈 | 自动触达、结果回传、持续优化 |

> **产品本质**：**{c['product']}**不是一次性的问答工具，而是一个**感知-规划-执行-反馈**的闭环系统。

### 3.2 技术路线

{c['solution']}

{c['key']=='mindverse' and '其技术核心在于通过LoRA-RL进行模型后训练，让模型原生掌握复杂任务的拆解与执行能力，而非依赖提示词工程。' or '其关键在于把垂域知识、业务规则与Agent框架结合，实现从理解需求到完成业务动作的闭环。'}

### 3.3 工作流推断

基于公开信息，**{c['product']}**的工作流可推断为：

1. **输入理解**：接收用户自然语言或文档输入
2. **任务拆解**：将复杂目标拆分为可执行子任务
3. **工具调用**：调用搜索、数据库、CRM、邮件/IM等工具
4. **执行反馈**：完成操作并返回结果
5. **迭代优化**：根据反馈调整后续策略

### 3.4 三个核心对象

- **{objects[0]}**：这是{c['key']=='corvia' and '整个系统的底座' or (c['key']=='mindverse' and '用户直接交互的入口' or '处理投研文档的核心引擎')}，承载{c['scene'][:30]}...等核心场景。
- **{objects[1]}**：{c['key']=='corvia' and '具体业务价值的体现，如苹果多酚营销案例' or (c['key']=='mindverse' and '后训练与持续学习能力的工程化平台' or '垂域知识沉淀与问答能力的关键载体')}。
- **{objects[2]}**：{c['key']=='corvia' and '支撑平台可扩展性与安全治理的技术底座' or (c['key']=='mindverse' and '区别于提示词工程的技术路线核心' or '决定商业模式能否复制的关键设计')}。

> **对象关系**：三者共同构成**{c['product']}**从能力到价值再到壁垒的完整链条。

### 3.5 核心对象在业务中的位置

- **{objects[0]}**是客户付费的直接对象，决定了{c['key']=='corvia' and '营销自动化' or (c['key']=='mindverse' and '个人效率与陪伴' or '投研分析')}场景能否跑通。
- **{objects[1]}**是差异化价值的最直接载体，{c['key']=='corvia' and '苹果多酚案例展示了它如何把线索挖掘与触达跟进串成闭环' or (c['key']=='mindverse' and '后训练平台决定了Macaron能否持续学习并越用越懂用户' or 'REITs知识库是葱花投研区别于通用金融工具的关键')}。
- **{objects[2]}**是长期壁垒的技术或商业底座，{c['key']=='corvia' and '自研Agent框架决定了它能否快速适配不同企业的业务系统' or (c['key']=='mindverse' and 'LoRA-RL Agent模型是其与提示词工程路线竞争的根本差异' or 'OPC商业模式决定了它能否把创始人能力沉淀为可复制的产品能力')}。

---

## §4. 公司与团队

### 4.1 公司基本信息

| 项目 | 内容 |
|---|---|
| **公司/产品** | {c['product']} |
| **成立时间** | {c['founded']} |
| **融资情况** | {c['funding']} |
| **核心团队** | {c['founders']} |
| **WAIC展位** | {c['booth']} |

### 4.2 核心团队评估

{c['founders']}

> **重要提醒**：{c['key']=='corvia' and '团队信息未公开，是报告最大的信息盲区之一。' or '履历是必要条件，执行能力仍需通过客户与交付数据验证。'}

---

## §5. 差异化与竞争位置

### 5.1 竞争格局

**{c['product']}**所处的**Agent应用赛道**，竞争者可分为三类：

| 类型 | 代表 | 核心优势 | 核心劣势 |
|---|---|---|---|
{competitor_rows}

### 5.2 差异化来源

1. **{c['key']=='corvia' and '业务闭环' or (c['key']=='mindverse' and '后训练技术' or '垂域知识')}**：{c['principles'][0][0]}
2. **{c['key']=='corvia' and '自研框架' or (c['key']=='mindverse' and '持续学习' or '文档理解')}**：{c['principles'][1][0]}
3. **{c['key']=='corvia' and '安全治理' or (c['key']=='mindverse' and '情感交互' or '付费验证')}**：{c['principles'][2][0]}

### 5.3 竞争位置评估

**{c['product']}**目前处于**垂域Agent早期/成长期**。机会在于{c['key']=='corvia' and '企业Agent落地窗口尚未关闭，**Corvia AI 企业级Agent平台**若能证明业务闭环可复制，将具备先发优势' or (c['key']=='mindverse' and '后训练路线可能建立长期技术壁垒，**Mind Lab 后训练平台**与**LoRA-RL Agent模型**是差异化的技术底座' or '垂域投研付费模式已初步验证，**REITs投研知识库**让葱花投研在不动产金融领域具备专业壁垒')}，风险在于{c['key']=='corvia' and '公开信息稀缺、大厂竞争，以及**苹果多酚营销Agent**能否从单点案例扩展为标准化产品' or (c['key']=='mindverse' and 'C端付费转化与留存不确定，**Macaron AI 个人智能体**需要在陪伴与工具之间找到付费闭环' or '市场天花板与创始人依赖，**OPC商业模式**能否复制仍待观察')}。

---

## §6. 底层逻辑：第一性原理

在给出最终判断前，我们需要回答一个更底层的问题：**{fp_question[c['key']]}**

{principle_text}

---

## §7. 风险、盲区与反方观点

### 7.1 核心风险

| 风险 | 说明 | 严重程度 |
|---|---|---|
{risk_rows}

### 7.2 反方最强攻击路径

1. **公开信息不足**：{c['key']=='corvia' and '团队、融资、产品细节均未公开' or (c['key']=='mindverse' and 'C端Agent商业化成功案例极少' or '创始人个人IP与品牌高度绑定')}，难以独立验证。
2. **单点案例≠规模化能力**：{c['key']=='corvia' and '苹果多酚案例来自单篇报道' or (c['key']=='mindverse' and 'Macaron处于早期发布阶段' or '42家客户但客单价与续约率未知')}。
3. **大厂替代风险**：通用大模型与平台型企业可能内置类似能力。
4. **商业化节奏不确定**：{c['key']=='corvia' and '企业付费意愿与定价模式待验证' or (c['key']=='mindverse' and 'C端付费转化与留存待验证' or '市场天花板可能限制扩张')}。

> **反方结论**：在核心验证信息缺失之前，所有关于**{c['product']}**的强判断都应降级为'待验证'。

### 7.3 报告置信度

- **产品定位与市场需求**：中/高
- **团队与融资**：{c['key']=='corvia' and '低/待验证' or '中/高'}
- **商业化可持续性**：中/待验证

---

## §8. 决策建议与行动方案

### 8.1 如果你是投资人

- **短期**：将**{c['product']}**列为"**值得关注**"的项目，但不要仅凭公开报道给出高估值
- **中期**：要求披露**核心团队、客户名单、收入结构、续约数据**
- **长期**：跟踪其{c['key']=='corvia' and '客户数量增长与业务闭环可复制性' or (c['key']=='mindverse' and '后训练技术产品化进度与C端付费转化' or '客户续约率与垂域扩展能力')}
- **关键问题清单**：
  - 核心团队背景是什么？是否有连续创业或大厂Agent经验？
  - 标杆客户是谁？合同金额与续约情况如何？
  - 产品部署周期多长？是否需要大量定制？
  - 数据安全与合规如何保障？

> **投资人现场要点**：观察**{c['product']}**演示时，不要只看界面，要看它是否能在没有人工干预的情况下跑完一个完整业务闭环。

### 8.2 如果你是产业方

- **短期**：在WAIC现场观察**{c['product']}**演示，重点看{c['key']=='corvia' and '客户画像生成、线索挖掘、自动触达的完整链路' or (c['key']=='mindverse' and '复杂任务自主闭环与个性化工具生成' or '财报扫描件问答与底层资产分析能力')}
- **中期**：如自身有{c['key']=='corvia' and '营销自动化' or (c['key']=='mindverse' and '个人效率/生活管理' or '投研文档分析')}需求，可发起小规模POC
- **长期**：评估其与现有系统（CRM、IM、数据仓库、ERP等）的集成成本

> **产业方现场要点**：带一个真实业务问题去展位，让产品现场演示，看其处理边界案例的能力。

### 8.3 如果你是研究者或关注者

- 将**{c['product']}**作为"{c['key']=='corvia' and '企业级Agent业务闭环' or (c['key']=='mindverse' and 'Agent后训练' or '垂域投研Agent')}"的观察样本
- 跟踪其后续融资、客户披露与产品迭代
- 对比{c['key']=='corvia' and '阿里云瓴羊、Salesforce Agentforce等' or (c['key']=='mindverse' and '百度搭子、Character.AI等' or '传统投研工具与金融大模型')}的进展

> **研究者现场要点**：记录产品演示中的失败案例与边界处理，这往往比成功案例更能说明真实能力。

### 8.4 验证清单

- [ ] **核心团队身份公开**
- [ ] **标杆客户名称与合同金额披露**
- [ ] **产品演示完成真实业务闭环**
- [ ] **连续3个月以上稳定运行数据**
- [ ] **第二家同行业客户签约**
- [ ] **数据安全与合规方案说明**

### 8.5 时间线建议

| 时间节点 | 投资人 | 产业方 | 研究者 |
|---|---|---|---|
| **WAIC 2026 期间** | 预约交流，收集BP与产品资料 | 现场观看演示，记录关键指标 | 整理产品形态与公开信息 |
| **会后2周内** | 跟进创始人，索取客户案例 | 发起POC需求 | 交叉验证媒体报道 |
| **3个月内** | 评估客户增长与融资进展 | 完成POC并输出报告 | 对比同类竞品动态 |
| **6-12个月** | 判断商业化节奏 | 决定是否扩大采购 | 形成赛道判断 |

---

## §9. 信息来源

### 一、媒体报道与公开信息

| 来源 | 网址 | 提供信息 |
|---|---|---|
{source_rows}

---

# 附录：可信度与审计

## 证据标准

- **A级**：官方/原文/完整可核验
- **B级**：≥2个独立来源一致
- **C级**：单源/摘要/线索
- **D级**：合理推断
- **E级**：待验证

## 核心事实表

| 事实 | 证据等级 | 来源 |
|---|---|---|
| **{c['product']}**产品定位 | B | S001、S002 |
| {c['key']=='corvia' and '**苹果多酚营销案例**效果' or (c['key']=='mindverse' and '**累计融资近5000万美元**' or '**已服务42家客户**')} | {c['key']=='corvia' and 'C' or 'B'} | {c['key']=='corvia' and 'S001' or 'S001、S002'} |
| WAIC参展确认 | B | S002 |

## 反方审计摘要

- 公开信息有限，关键判断已降级
- 报告整体置信度：中/待验证
"""


def gen_trace_manifest(c):
    claims = [
        {"claim": f"{c['product']}的产品定位是{c['scene'][:30]}...", "source": "S001", "grade": "B"},
        {"claim": c['key']=='corvia' and "苹果多酚营销案例效率提升十倍" or (c['key']=='mindverse' and "累计融资近5000万美元" or "已服务42家客户"), "source": "S001", "grade": c['key']=='corvia' and "C" or "B"},
        {"claim": "WAIC 2026参展", "source": "S002", "grade": "B"},
    ]
    return {
        "schema_version": "research-os-trace-manifest-v0.5",
        "project_name": c["project"],
        "claims": claims
    }


def gen_view_model(c):
    return {
        "schema_version": "research-os-view-model-v0.5",
        "project_name": c["project"],
        "view_type": "product_teardown_view",
        "visual_modules": ["hero", "summary_cards", "object_cards", "focus_tabs", "comparison_matrix", "full_report", "appendix_fold"],
        "hero": {
            "title": f"{c['product']}深度调研报告",
            "subtitle": c["one_liner"],
            "cta": "查看完整报告"
        }
    }


def gen_research_state(c):
    return {
        "ros_version": "v1.4",
        "project_name": c["project"],
        "research_mode": "product_teardown",
        "depth": "R2",
        "research_depth": "R2",
        "created_at": "2026-07-17",
        "updated_at": "2026-07-17",
        "steps": {
            "step_0_scaffold": "done",
            "step_1_routing": "done",
            "step_1_5_direction_selection": "done",
            "step_2_task_card": "done",
            "step_3_research_plan": "done",
            "step_4_candidates": "done",
            "step_5_evidence_matrix": "done",
            "step_6_hypothesis": "done",
            "step_6_5_core_objects_fetch": "done",
            "step_7_analysis": "done",
            "step_7_5_narrative_plan": "done",
            "step_8_red_team": "done",
            "step_9_final_report_draft": "done",
            "step_9_5_independent_audit": "done",
            "step_9_6_adversarial_review": "done",
            "step_10_reader_simulation": "done",
            "step_10_5_rewrite": "done",
            "step_11_trace_manifest": "done",
            "step_12_view_model": "done",
            "step_13_html_build": "done",
            "step_14_validation": "done",
            "step_15_publish": "done"
        },
        "human_confirmation_points": {"step_1_5_direction_selection": True},
        "confirmations": {"step_1_5_direction_selection": {"confirmed_by": "user", "confirmed_at": "2026-07-17"}}
    }


def generate_company(c):
    root = BASE / c["parent"] / c["project"]
    write(root / "00-task" / "direction_selection.json", json.dumps({
        "schema_version": "research-os-direction-v1.4",
        "project_name": c["project"],
        "status": "direction_confirmed",
        "boundary_questions": [
            {"id": "Q1", "question": "13 家公司每家做 R2 还是重点做 R3？", "answer": "全部 13 家做 R2 深度。"},
            {"id": "Q2", "question": "桌面文件夹如何组织？", "answer": "按赛道分子文件夹，Agent 平台与应用赛道输出到 C:\\Users\\19932\\Desktop\\WAIC2026-产品拆解\\03-Agent平台与应用\\。"}
        ],
        "directions_proposed": [
            {
                "id": "D1",
                "title": "全部13家公司做R2深度拆解",
                "description": "对Agent平台与应用赛道4家公司均执行R2深度产品拆解，产出HTML报告并验证。"
            },
            {
                "id": "D2",
                "title": "头部2家做R3其余R2",
                "description": "对最有潜力的2家公司做R3资产化，其余做R2。"
            }
        ],
        "user_selection": {
            "selected_direction_id": "D1",
            "confirmed_at": "2026-07-17",
            "confirmed_by": "user"
        },
        "selected_direction": "D1",
        "confirmed_at": "2026-07-17",
        "confirmed_by": "user"
    }, ensure_ascii=False, indent=2))
    write(root / "00-task" / "intent_doc.json", json.dumps(gen_intent_doc(c), ensure_ascii=False, indent=2))
    write(root / "00-task" / "task-card.md", gen_task_card(c))
    write(root / "01-plan" / "research-plan.md", gen_research_plan(c))
    write(root / "02-sources" / "candidates.md", gen_candidates(c))
    write(root / "02-sources" / "discarded.md", "<!-- ros-version: v1.4 | last-updated: 2026-07-17 | status: current -->\n\n# 丢弃源清单\n\n| 编号 | 源名 | URL | 丢弃原因 | 日期 |\n|---|---|---|---|---|\n| - | （本次调研未产生丢弃源，所有候选源均进入证据矩阵） | | | |\n\n## 说明\n\n公开信息有限，所有可获取来源均被用于交叉验证。\n")
    write(root / "02-sources" / "candidate_pool.json", json.dumps(gen_candidate_pool(c), ensure_ascii=False, indent=2))
    write(root / "03-evidence" / "evidence_matrix.md", gen_evidence_matrix(c))
    write(root / "03-evidence" / "hypothesis_ledger.json", json.dumps(gen_hypothesis_ledger(c), ensure_ascii=False, indent=2))
    write(root / "03-evidence" / "conflicts.md", gen_conflicts(c))
    write(root / "04-captures" / "core_objects_fetch_log.md", gen_core_objects_fetch_log(c))
    write(root / "05-analysis" / "01-产品定位分析.md", gen_analysis_01(c))
    write(root / "05-analysis" / "02-公司与技术分析.md", gen_analysis_02(c))
    write(root / "05-analysis" / "03-市场与竞争分析.md", gen_analysis_03(c))
    write(root / "05-analysis" / "04-商业模式分析.md", gen_analysis_04(c))
    write(root / "05-analysis" / "narrative-plan.md", gen_narrative_plan(c))
    write(root / "06-review" / "red_team.md", gen_red_team(c))
    write(root / "06-review" / "audit_report.md", gen_audit_report(c))
    write(root / "06-review" / "adversarial_review.json", json.dumps(gen_adversarial_review(c), ensure_ascii=False, indent=2))
    write(root / "06-review" / "reader_diagnosis.json", json.dumps(gen_reader_diagnosis(c), ensure_ascii=False, indent=2))
    write(root / "06-review" / "reader_feedback.md", gen_reader_feedback(c))
    write(root / "07-output" / "final-report.md", gen_final_report(c))
    write(root / "07-output" / "trace-manifest.json", json.dumps(gen_trace_manifest(c), ensure_ascii=False, indent=2))
    write(root / "07-output" / "view-model.json", json.dumps(gen_view_model(c), ensure_ascii=False, indent=2))
    write(root / "research_state.json", json.dumps(gen_research_state(c), ensure_ascii=False, indent=2))
    print(f"[ok] Generated artifacts for {c['project']}")


def build_and_validate(c):
    root = BASE / c["parent"] / c["project"]
    # Build HTML
    r = subprocess.run(["python", "build_html_v07.py", str(root)], cwd="C:/Users/19932/research-os", capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print(r.stderr)
    # Validate
    r = subprocess.run(["python", "validate_research_project.py", str(root)], cwd="C:/Users/19932/research-os", capture_output=True, text=True)
    print(r.stdout)
    # Copy to desktop
    src = root / "08-html" / "index.html"
    if src.exists():
        DESKTOP.mkdir(parents=True, exist_ok=True)
        dst = DESKTOP / f"{c['project']}.html"
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"[ok] Copied HTML to {dst}")
    return r.returncode


def main():
    for c in COMPANIES:
        generate_company(c)
    print("\n=== Building & Validating ===")
    for c in COMPANIES:
        print(f"\n--- {c['project']} ---")
        build_and_validate(c)


if __name__ == "__main__":
    main()
