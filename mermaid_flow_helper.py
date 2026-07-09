#!/usr/bin/env python3
"""Research OS v1.0 mermaid_flow_helper提供深度调研开源项目的标准 mermaid 流程图模板。
HTML 生成器 (build_research_html.py) 已支持 mermaid——
检测到 ```mermaid 代码块会自动加载 CDN 并渲染。

这个模块提供常用流程图模板，让 final-report.md 直接引用。

用法：
  from mermaid_flow_helper import FLOWCHARTS
  print(FLOWCHARTS["gpt_researcher"])
"""
from __future__ import annotations


# 所有流程图都用 mermaid 语法，HTML 生成器会自动渲染
FLOWCHARTS: dict[str, str] = {
    "gpt_researcher": """```mermaid
flowchart TD
    A[用户提问<br/>query + 报告类型] --> B[Planner Agent<br/>LLM 把大问题拆成子问题]
    B --> C[13种搜索引擎<br/>Tavily/Bing/DuckDuckGo等<br/>并行检索]
    C --> D[5种网页抓取器<br/>BeautifulSoup/Selenium/<br/>Tavily Extract/Firecrawl]
    D --> E{内容超过8KB?}
    E -->|是| F[embedding向量过滤<br/>筛掉不相关部分]
    E -->|否| G[直接送LLM总结]
    F --> G
    G --> H[Execution Agent<br/>LLM按相关性总结+保留URL]
    H --> I[Planner Agent聚合<br/>filter + aggregate]
    I --> J[最终研究报告<br/>含引用列表]

    style A fill:#e1f5fe
    style J fill:#c8e6c9
    style B fill:#fff3e0
    style H fill:#fff3e0
    style I fill:#fff3e0
```""",

    "storm": """```mermaid
flowchart TD
    A[topic 主题] --> B[Module 1: 知识收集]
    B --> C[PersonaGenerator<br/>找相关维基页面+生成4个persona<br/>如'技术专家''历史学者''批评家']
    C --> D[对话模拟器<br/>每个persona跑3轮对话]
    D --> D1[WikiWriter提问<br/>用persona视角]
    D1 --> D2[TopicExpert搜索<br/>拆query+搜索+生成回答]
    D2 --> D3[收集信息表<br/>按URL去重]
    D3 --> E[Module 2: 大纲生成]
    E --> E1[Draft: 仅用LLM<br/>参数知识生成草稿]
    E1 --> E2[Refine: 用对话历史<br/>精修大纲]
    E2 --> F[Module 3: 文章生成]
    F --> F1[SentenceTransformer<br/>所有snippet向量化]
    F1 --> F2[每个section并行<br/>cosine检索top-3 snippet<br/>LLM生成带1,2引用段落]
    F2 --> F3[合并+统一引用编号]
    F3 --> G[Module 4: 文章打磨]
    G --> G1[生成维基式摘要]
    G1 --> H[最终维基式长文<br/>带行内引用1,2]

    style A fill:#e1f5fe
    style H fill:#c8e6c9
    style B fill:#fff3e0
    style E fill:#fff3e0
    style F fill:#fff3e0
    style G fill:#fff3e0
```""",

    "hf_open_deep_research": """```mermaid
flowchart TD
    A[question 问题] --> B[manager_agent<br/>CodeAgent max_steps=12]
    B --> C{每4步停下来<br/>planning_interval}
    C -->|需要看文件| D[TextInspectorTool<br/>mdconvert转PDF/DOCX为文本]
    C -->|需要看图| E[visualizer<br/>VLM视觉问答模型]
    C -->|需要上网| F[委派给search_agent]
    F --> G[search_agent<br/>ToolCallingAgent max_steps=20]
    G --> H[GoogleSearchTool<br/>Serper/SerpApi]
    H --> I[VisitTool<br/>requests+mdconvert<br/>无JS渲染]
    I --> J[viewport分页<br/>每页5120字符]
    J --> K[LLM翻页浏览<br/>PageUp/Down/Finder]
    K --> L[search_agent返回<br/>run_summary]
    L --> M[manager综合所有结果]
    M --> N[final_answer<br/>agent loop直接返回<br/>无独立报告合成]

    style A fill:#e1f5fe
    style N fill:#c8e6c9
    style B fill:#fff3e0
    style G fill:#fff3e0
    style I fill:#ffcdd2
```""",

    "owl": """```mermaid
flowchart TD
    A[task 任务] --> B{选模式}
    B -->|默认| C[Workforce模式<br/>层级编排]
    B -->|GAIA主力| D[RolePlaying模式<br/>双角色扮演]

    C --> C1[Task Agent<br/>分解任务]
    C1 --> C2[Coordinator Agent<br/>派发子任务]
    C2 --> C3[Web Agent<br/>搜索+Playwright浏览器]
    C2 --> C4[Document Agent<br/>PDF/Word/Excel解析]
    C2 --> C5[Reasoning Agent<br/>写代码+计算]
    C3 --> C6[汇总]
    C4 --> C6
    C5 --> C6

    D --> D1[User Agent<br/>逐步下指令<br/>Instruction: ...]
    D1 --> D2[Assistant Agent<br/>用工具执行<br/>Solution: ...]
    D2 --> D3{User Agent判断<br/>是否完成?}
    D3 -->|否| D1
    D3 -->|是 TASK_DONE| D4[Assistant一次性<br/>合成最终答案]

    C6 --> E[最终结果]
    D4 --> E

    style A fill:#e1f5fe
    style E fill:#c8e6c9
    style C fill:#fff3e0
    style D fill:#fff3e0
```""",

    "comparison": """```mermaid
flowchart LR
    subgraph 流水线派
        A1[GPT Researcher<br/>planner-execution双agent]
        A2[STORM<br/>4模块+persona对话]
    end
    subgraph Agent派
        B1[HF Open Deep Research<br/>CodeAgent两层]
        B2[Owl<br/>多agent角色扮演]
    end

    A1 --> C[固定阶段编排<br/>可复现可控]
    A2 --> C
    B1 --> D[LLM自主ReAct<br/>通用能处理意外]
    B2 --> D

    style A1 fill:#e3f2fd
    style A2 fill:#e3f2fd
    style B1 fill:#fce4ec
    style B2 fill:#fce4ec
```""",
}


def get_flowchart(key: str) -> str:
    """获取流程图 markdown（含 ```mermaid 代码块）"""
    return FLOWCHARTS.get(key, f"<!-- flowchart {key} not found -->")


def list_flowcharts() -> list[str]:
    return list(FLOWCHARTS.keys())


if __name__ == "__main__":
    print("Available flowcharts:")
    for k in list_flowcharts():
        print(f"  - {k}")
    print("\nUsage in final-report.md:")
    print("  直接粘贴 FLOWCHARTS[key] 的内容到 markdown 文件即可")
