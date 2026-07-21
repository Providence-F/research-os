// 本文件由 scripts/sync_dashboard.py 自动生成，请勿手改
import type { VersionInfo } from './types';

export const versions: VersionInfo[] = [
  {
    "id": "v2.0",
    "date": "2026-07-21",
    "summary": "新增",
    "changes": [
      "意图拆解协议（24 号模板）：5 轮探索（R1 字面 → R2 差距 → R3 意图树 → R4 路径 → R5 问题说明书），意图树 L0-L4 分层，候选路径剪枝机制",
      "洞察账本协议（25 号模板）：insight_ledger.json，洞察判定三条件（反共识/可证伪/决策力），状态流转 draft→verified/downgraded/rejected",
      "叙事原型系统（23 号重构）：6 种 archetype 替代单一行文思路，选择矩阵 + why_not 防默认",
      "双读者模拟（reader_simulation v2.0）：outsider + layman 双视角，独立阈值",
      "3 个新门禁：gate_10 意图树完整性、gate_11 洞察账本、gate_12 跨产物一致性"
    ],
    "isCurrent": true
  },
  {
    "id": "v1.5",
    "date": "2026-07-20",
    "summary": "系统级审核与治理修复（架构收敛 + 术语统一 + 看板重做）",
    "changes": [
      "config.py SYSTEM_VERSION：v1.1 → v1.5（恢复单一真相源地位）",
      "24 个模板 ros-version 头全部统一 v1.5",
      "00-使用说明：8 门禁 → 9 门禁（补门禁9 美学合规验证），模板数 19 → 24",
      "README 从 v1.2 全面重写至 v1.5",
      "规范去外部品牌词：「Kimi式边界追问」→「边界追问」（规范应自包含）"
    ]
  },
  {
    "id": "v1.4.1",
    "date": "2026-07-18",
    "summary": "新增门禁 9：美学合规验证",
    "changes": [
      "14-研究执行状态机：8 门禁 → 9 门禁，新增门禁9「美学合规验证」（步骤 13）",
      "要求 Agent 构建 HTML 时必须从 09-HTML美学规范.md 读取 CSS，禁止手写"
    ]
  },
  {
    "id": "v1.4",
    "date": "2026-07-12",
    "summary": "核心升级：行文思路规划 + Kimi式边界追问 + 人工确认点精简",
    "changes": [
      "模板被迫同时承担\"内容清单\"和\"行文思路\"两个职责，但它只能履行前者",
      "第一性原理协议的\"在呈现数据前\"被误解为\"在介绍对象前\"",
      "人工确认点与 auto 模式设计哲学冲突",
      "新增 `templates/23-行文思路规划协议.md`",
      "在 step_7（分析）之后、step_8（反方审计）之前执行"
    ]
  },
  {
    "id": "v1.3",
    "date": "2026-07-12",
    "summary": "四组件升级：方向选择 + 对抗审核 + 第一性原理 + 结构化强制",
    "changes": [
      "\"可跳过\"是工程问题：结构化字段缺失，验证器无法检测\"是否执行了确认\"",
      "\"可糊弄\"是语义问题：即使有字段，Agent 也能填入浅层内容通过检查",
      "单纯的结构化字段只能解决\"可跳过\"，无法解决\"可糊弄\"",
      "新增 `templates/20-方向选择协议.md`",
      "Agent 给出 2-3 个方向，用户选择 + 修正"
    ]
  },
  {
    "id": "v1.2",
    "date": "2026-07-11",
    "summary": "术语科普门禁系统（解决\"知识的诅咒\"）",
    "changes": [
      "intent_doc.json 的 concept_ladder_seed 经常为空（Agent 跳过 Round 3 填充）",
      "reader_model 为空导致 reader_simulation 退化为默认画像",
      "验证器注释承诺\"术语解释数检查\"但未实现",
      "plain_glossary.py（20+ 术语库）完全孤立，未被任何流程引用",
      "`check_concept_ladder_seed`：seed >= 3 个术语"
    ]
  },
  {
    "id": "v1.1",
    "date": "2026-07-10",
    "summary": "核心修复：规范与实现断层",
    "changes": [
      "从 archive/v1.0/ 恢复工具到根目录",
      "升级为 v1.1：新增 wrap_chapters() 函数，包裹 section.chapter 结构",
      "步骤13 HTML构建真正\"工具驱动\"",
      "新增 `check_html_required_structures` 函数",
      "检查 9 项必须结构：page-shell/aside.toc/vm-hero/hero-verdict/reading-progress/section.chapter/Lora/#faf9f5/#b85b44"
    ]
  },
  {
    "id": "v1.0",
    "date": "2026-07-09",
    "summary": "新增检查（2项）",
    "changes": [
      "`build_html_v07.py` 被归档到 archive/v1.0/ 但使用说明仍引用",
      "验证器不检查 HTML 必须结构",
      "使用说明未同步到 v1.0"
    ]
  },
  {
    "id": "v0.7.1",
    "date": "2026-07-05",
    "summary": "Dumb Tools 合规修复",
    "changes": [
      "**`validate_research_project.py` 的 `check_core_object_mentions`**：从硬编码 `[\"MuseDAM\", \"atypica\", \"GEA\", \"System of Context\"]` 改为从 `task-card.md` 的 `## 核心对象` 章节读取 Agent 声明的列表。工具不硬编码项目特定信息。",
      "**`final_report_writer.py` 的 `build_rewrite_instructions`**：删除 `action` 分类（原来用 `score < 0.3 → action = \"rewrite\"` 是语义判断）。改为只输出 `data_for_agent`（booleans + counts），action 决策由 Agent 做。",
      "**`README.md`**：从 v0.5 重写到 v0.7.1，加入 Smart Agent Dumb Tools 设计哲学、v0.7 7 项检查摘要、v0.6 三大模块说明、发布完整性条款",
      "**`templates/00-使用说明.md`**：从 v0.5 完全重写到 v0.7.1，包含 v0.6/v0.7/v0.7.1 全部新内容",
      "**`archive/README.md`**：从 v0.5 同步到 v0.7.1"
    ]
  },
  {
    "id": "v0.7",
    "date": "2026-07-05",
    "summary": "新增 7 项机械检查（validate_research_project.py）",
    "changes": [
      "命令行参数支持任意项目路径",
      "动态可视化组件识别（基于关键词模式匹配）",
      "固化美学规范（从 `09-HTML美学规范.md` 读取，不在代码里硬编码）",
      "修复 v0.6 的滚轮 bug（aside.toc overflow: hidden）",
      "修复 v0.6 的附录 div 闭合 bug"
    ]
  },
  {
    "id": "v0.6",
    "date": "2026-07-04",
    "summary": "新增模块",
    "changes": [
      "**独立审计 Agent**（步骤 9.5，强制门禁，5 问全 PASS）",
      "由独立会话的审计 Agent 执行",
      "不知道调研过程，只看产物",
      "5 个问题全 PASS 才能进入步骤 10",
      "**核心对象直采协议**（步骤 6.5，强制门禁）"
    ]
  },
  {
    "id": "v0.5",
    "date": "2026-07-04",
    "summary": "破坏性变更",
    "changes": [
      "统一版本号到 v0.5，废弃 v0.1-v0.10 的碎片化版本号",
      "`00-使用说明.md` 完全重写（v0.1 到 v0.5，同步到系统真实状态）",
      "`create_research_project.py` 完全重写（v0.1 到 v0.5）",
      "`14-研究执行状态机.md` 重写（v0.4 到 v0.5）",
      "**`09-HTML美学规范.md`**：从 `build_research_html.py` 的 CSS（v0.8 + v0.9.1 + v0.9.2 + v0.10）抽取并固化为独立文档。这是 HTML 视觉规格的**单一真相源**。"
    ]
  },
  {
    "id": "v0.10",
    "date": "2026-07-03",
    "summary": "",
    "changes": [
      "引入 `reader_simulation.py` 写-读-改闭环",
      "`final_report_writer.py` 支持 5 幕叙事",
      "`intent_discovery.py` 加入意图探索",
      "`concept_ladder_helper.py` 术语阶梯",
      "`build_research_html.py` CSS v0.10"
    ]
  },
  {
    "id": "v0.9",
    "date": "2026-07-02",
    "summary": "",
    "changes": [
      "`build_research_html.py` CSS v0.9.1 + v0.9.2",
      "`intent_discovery.py` v0.9",
      "`research_router.py` v0.9",
      "`04-假设账本.md` v0.9（融入 ljg-think drill_down）"
    ]
  },
  {
    "id": "v0.8",
    "date": "2026-07-01",
    "summary": "",
    "changes": [
      "`build_research_html.py` CSS v0.8（Anthropic cream + Lora + Starlight asides）",
      "`intent_discovery.py` v0.8",
      "`research_router.py` v0.8",
      "`validate_research_project.py` v0.8"
    ]
  },
  {
    "id": "v0.7",
    "date": "2026-06-30",
    "summary": "",
    "changes": [
      "`research_planner.py` v0.7",
      "`validate_research_project.py` v0.7",
      "`goal_tracker.py` v0.7",
      "`iteration_log.py` v0.7"
    ]
  },
  {
    "id": "v0.4",
    "date": "2026-06-26",
    "summary": "",
    "changes": [
      "`14-研究执行状态机.md` v0.4（12 步线性流程）",
      "`15-结论溯源清单.md` v0.4",
      "`research_run_step.py` v0.4"
    ]
  },
  {
    "id": "v0.3",
    "date": "2026-06-25",
    "summary": "",
    "changes": [
      "`research_status.py` v0.3",
      "`research_planner.py` v0.3",
      "`validate_research_project.py` v0.3",
      "`13-假设账本.md` v0.3（已归档，被 04 取代）",
      "`12-候选池.md` v0.3"
    ]
  },
  {
    "id": "v0.2",
    "date": "2026-06-24",
    "summary": "",
    "changes": [
      "`09-可视化视图模型.md` v0.2"
    ]
  },
  {
    "id": "v0.1",
    "date": "2026-06-22",
    "summary": "",
    "changes": [
      "`00-使用说明.md` v0.1（Dify 时代，已归档）",
      "`create_research_project.py` v0.1（已重写为 v0.5）",
      "`research_status.py` v0.3",
      "`config.py` v0.1",
      "`ros.py` v0.1（CLI 入口）"
    ]
  }
];
