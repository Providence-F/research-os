# Research OS Changelog

所有版本变更记录。日期格式：YYYY-MM-DD。

## [v1.3] - 2026-07-12

### 四组件升级：方向选择 + 对抗审核 + 第一性原理 + 结构化强制

**问题背景**：v1.2 存在两个系统级问题：
1. 人工确认点（step_3_research_plan）在 auto 模式下被跳过——"可跳过"问题
2. 调研报告缺乏第一性原理分析，只罗列数据不讲本质——"可糊弄"问题

**根因分析**：
- "可跳过"是工程问题：结构化字段缺失，验证器无法检测"是否执行了确认"
- "可糊弄"是语义问题：即使有字段，Agent 也能填入浅层内容通过检查
- 单纯的结构化字段只能解决"可跳过"，无法解决"可糊弄"

**解决方案**：4 组件组合升级

#### 组件 A：Kimi 式方向选择（步骤 1.5）
- 新增 `templates/20-方向选择协议.md`
- Agent 给出 2-3 个方向，用户选择 + 修正
- 比完整方案确认更便宜，更早纠偏
- 产物：`00-task/direction_selection.json`
- R2/R3 强制，R0/R1 可跳过

#### 组件 B：结构化强制（验证器升级）
- `STEP_ARTIFACTS` 新增 `step_1_5_direction_selection` 和 `step_9_6_adversarial_review`
- `STEP_DEPENDENCIES` 新增依赖链：step_2 依赖 step_1_5，step_10 依赖 step_9_6
- `JSON_FIELD_REQUIREMENTS` 新增 `first_principles_decomposition: list`
- 新增 7 个检查函数（方向选择/对抗审核/第一性原理报告层/第一性原理意图层/人工确认强制/审计结构化/反方结构化）

#### 组件 C：对抗式 subagent 审核（步骤 9.6）
- 新增 `templates/21-对抗式审核协议.md`
- 核心设计原理：**对抗比评判容易**
- subagent 不需要比主 Agent 更聪明，只需要能打破它的论点
- Context 隔离：对抗审核 subagent 只收到 final-report.md，不收到过程文件
- 产物：`06-review/adversarial_review.json`
- 验证规则：≥3 攻击 + 每个攻击有回应 + 含 first_principles 类型攻击

#### 组件 D：第一性原理三层结构 + 对抗测试
- 新增 `templates/22-第一性原理拆解协议.md`
- 三层结构：
  - 意图层：`intent_doc.json` 的 `first_principles_decomposition` 字段（≥3 条不可再分的底层逻辑）
  - 任务层：调研方案的元问题必填
  - 报告层：final-report.md 的"第一性原理"章节必填
- "再分测试"：subagent 对每条"不可再分"的原理尝试"再分"，如果能再分则不是真第一性原理
- 补全 `templates/19-产品深度拆解标准.md`（v1.2 时是 placeholder）

#### 其他升级
- `intent_discovery.py`：Round 3 prompt 新增第 7 项 first_principles_decomposition 要求
- `finalize_exploration` 函数新增 `first_principles_decomposition` 参数
- `templates/14-研究执行状态机.md`：15 步 → 17 步，6 门禁 → 7 门禁
- `templates/08-最终报告.md`：新增 §2.5 第一性原理章节模板
- `templates/02-调研方案.md`：元问题标注为 v1.3 必填+验证
- 增强独立审计检查：从"PASS 字符串"升级为"5 问结构化检查"
- 增强反方审计检查：从"字符数"升级为"攻击次数 + 降级次数"

**验证结果**：在现有项目（v1.2 下创建）上测试，65 PASS / 6 WARN / 5 FAIL
- 5 个 FAIL 都是预期中的（现有项目缺少 v1.3 新增产物）
- 新检查函数本身运行正常

**设计哲学增强**：
- v1.2 之前：Smart Agent. Dumb Tools.（工具只做机械检查）
- v1.3 增强：结构化字段解决"可跳过"问题 + 对抗测试解决"可糊弄"问题
- 不改变"Dumb Tools"原则——对抗测试仍是机械的（检查攻击次数、回应存在性）

---

## [v1.2] - 2026-07-11

### 术语科普门禁系统（解决"知识的诅咒"）

**问题**：Agent 写报告时默认读者已知行业术语，导致 GTM/ICP/Waterfall Enrichment 等核心概念未解释。用户读完报告才发现需要打补丁——这是"后置验证"范式的根本缺陷。

**根因分析**：
- intent_doc.json 的 concept_ladder_seed 经常为空（Agent 跳过 Round 3 填充）
- reader_model 为空导致 reader_simulation 退化为默认画像
- 验证器注释承诺"术语解释数检查"但未实现
- plain_glossary.py（20+ 术语库）完全孤立，未被任何流程引用

**解决方案**：从"后置验证"转向"前置约束 + 机械门禁"

1. **验证器新增 3 项门禁**（validate_research_project.py）：
   - `check_concept_ladder_seed`：seed >= 3 个术语
   - `check_reader_model`：reader_model.background 非空
   - `check_term_explanation_coverage`：seed 中每个术语在报告首次出现位置附近有解释标记

2. **plain_glossary.py 集成**（concept_ladder_helper.py）：
   - 合并 10 个孤立术语到 GLOSSARY 统一为 6 层结构
   - 消除了 plain_glossary.py 的孤立状态

3. **Lev8 项目修复**：
   - 填充 concept_ladder_seed（10 个术语：GTM/ICP/Waterfall Enrichment 等）
   - 填充 reader_model（background + knowledge_blindspots + comprehension_target）

**验证结果**：62 PASS / 3 WARN / 0 FAIL

---

## [v1.1] - 2026-07-10

### 核心修复：规范与实现断层

**问题背景**：v1.0 升级时归档了 `build_html_v07.py` 但没更新使用说明，导致：
1. 规范文档说"用工具构建HTML"但工具不存在
2. Agent 被迫手写HTML，手写HTML严重偏离美学规范
3. 验证器只检查"禁止模式"不检查"必须结构"，无法发现缺失

### 修复内容

1. **恢复 build_html_v07.py 到根目录**
   - 从 archive/v1.0/ 恢复工具到根目录
   - 升级为 v1.1：新增 wrap_chapters() 函数，包裹 section.chapter 结构
   - 步骤13 HTML构建真正"工具驱动"

2. **验证器增加 HTML 必须结构检查（9项）**
   - 新增 `check_html_required_structures` 函数
   - 检查 9 项必须结构：page-shell/aside.toc/vm-hero/hero-verdict/reading-progress/section.chapter/Lora/#faf9f5/#b85b44
   - 这些检查是机械的正则匹配，符合 Dumb Tools 原则

3. **使用说明同步真实状态**
   - 00-使用说明.md 重写为 v1.1
   - 修复规范与实现的矛盾（工具引用 vs 工具归档）
   - 新增"错误11：手写HTML"和"错误12：规范引用已归档工具"

### 设计哲学修复

**Smart Agent. Dumb Tools. 哲学的盲区修复**：

原来验证器只检查两类：
- ✅ "禁止什么"（不能有 overflow-y:auto）
- ❌ "必须有什么"（必须有 aside.toc）→ 缺失

v1.1 新增第三类：
- ✅ "必须有什么"（9项必须结构正则匹配）

这修复了哲学的执行盲区：工具原来太 dumb（只检查禁止模式），导致 Agent 手写 HTML 缺失关键结构时验证器无法发现。新增的检查仍是机械的（正则匹配字符串是否存在），不是语义判断。

## [v1.0] - 2026-07-09

### 新增检查（2项）

1. **view-model reader-facing 检查**：检查 view-model.json 的 hero 字段是否面向读者
2. **行动方案比例检查**：最终报告中行动方案占比 ≥ 15%
3. **LaTeX 公式渲染检查**：报告含 LaTeX 公式时 HTML 必须有 MathJax/KaTeX

### 已知问题（v1.1 已修复）

- `build_html_v07.py` 被归档到 archive/v1.0/ 但使用说明仍引用
- 验证器不检查 HTML 必须结构
- 使用说明未同步到 v1.0

## [v0.7.1] - 2026-07-05

### Dumb Tools 合规修复
- **`validate_research_project.py` 的 `check_core_object_mentions`**：从硬编码 `["MuseDAM", "atypica", "GEA", "System of Context"]` 改为从 `task-card.md` 的 `## 核心对象` 章节读取 Agent 声明的列表。工具不硬编码项目特定信息。
- **`final_report_writer.py` 的 `build_rewrite_instructions`**：删除 `action` 分类（原来用 `score < 0.3 → action = "rewrite"` 是语义判断）。改为只输出 `data_for_agent`（booleans + counts），action 决策由 Agent 做。

### 入口文档同步更新
- **`README.md`**：从 v0.5 重写到 v0.7.1，加入 Smart Agent Dumb Tools 设计哲学、v0.7 7 项检查摘要、v0.6 三大模块说明、发布完整性条款
- **`templates/00-使用说明.md`**：从 v0.5 完全重写到 v0.7.1，包含 v0.6/v0.7/v0.7.1 全部新内容
- **`archive/README.md`**：从 v0.5 同步到 v0.7.1
- **所有模板文件的 `ros-version` 头**：统一从 v0.5/v0.6 升级到 v0.7.1

### 修复的发布不完整问题
1. **入口文档严重过时**：v0.7 升级后只推送了核心代码，没有同步更新入口文档。已修复，README/00-使用说明/CHANGELOG/archive 全部同步到 v0.7.1。
2. **版本号碎片化**：14 个模板文件中 11 个还标 v0.5，3 个标 v0.6，1 个标 v0.7。统一到 v0.7.1。
3. **缺少发布完整性条款**：之前升级没有强约束"每次发布必须同步入口文档"。v0.7.1 在版本治理规则中加入"发布完整性"条款。

## [v0.7] - 2026-07-05

### 新增 7 项机械检查（validate_research_project.py）
1. **`check_json_field_values`**：JSON 字段值非空检查（解决空 JSON 通过问题）
2. **`check_task_card_field_values`**：task-card 字段值检查（解决模板说明文字占字符数问题）
3. **`check_step_dependencies`**：步骤依赖检查（step N done 则依赖项必须 done）
4. **`check_depth_metrics`**：内容深度指标（URL 数、数据点数、章节数）
5. **`check_html_forbidden_patterns`**：HTML 禁止模式（滚轮、未闭合 div）
6. **`check_core_object_mentions`**：核心对象提及次数（从 task-card 读取声明，不硬编码）
7. **`check_prerequisite_gate`**：前置门禁（核心对象直采前必须完成任务卡和研究计划）

### 新增通用 HTML 构建器（build_html_v07.py）
- 命令行参数支持任意项目路径
- 动态可视化组件识别（基于关键词模式匹配）
- 固化美学规范（从 `09-HTML美学规范.md` 读取，不在代码里硬编码）
- 修复 v0.6 的滚轮 bug（aside.toc overflow: hidden）
- 修复 v0.6 的附录 div 闭合 bug

### 升级写-读-改闭环（final_report_writer.py）
- 结构化重写指令（`rewrite_instructions.json`）
- 迭代状态追踪（`iteration_state.json`）
- 最多 2 轮迭代，第 3 轮 fail 让人接手

### 升级状态机模板（14-研究执行状态机.md）
- 从 15 步线性流程升级为 15 步 + 5 个强制门禁
- 加入 step 6.5 核心对象直采（强制门禁）
- 加入 step 9.5 独立审计（强制门禁，5 问全 PASS）
- 加入 step 10.5 写-读-改闭环（强制门禁，max 2 轮）
- 加入 HTML 禁止模式检查（强制门禁）

### 新增模板
- `templates/16-独立审计Agent.md`：独立审计 Agent 协议
- `templates/17-核心对象直采协议.md`：核心对象直采协议
- `templates/18-核心对象直采模板.md`：核心对象直采模板

### 验证
- 在特赞项目上验证：38 PASS / 1 WARN / 16 FAIL，发现 14 个 v0.6.1 漏检问题
- HTML v0.7 构建器验证：无禁止模式警告
- 写-读-改闭环验证：通过，overall_score=0.85

## [v0.6] - 2026-07-04

### 新增模块
- **独立审计 Agent**（步骤 9.5，强制门禁，5 问全 PASS）
  - 由独立会话的审计 Agent 执行
  - 不知道调研过程，只看产物
  - 5 个问题全 PASS 才能进入步骤 10
- **核心对象直采协议**（步骤 6.5，强制门禁）
  - core_objects_fetch_log.md 必须存在
  - URL >= 3 + 对象 >= 3 + 字符数 >= 200
  - 前置：步骤 2 和 3 必须 done
- **写-读-改闭环**（步骤 10.5）
  - reader_simulation.py 模拟读者
  - final_report_writer.py 根据读者反馈重写
  - 最多 2 轮迭代

### 设计哲学确立
- **Smart Agent. Dumb Tools.** 原则确立
- 工具只做机械检查（存在性、字数、格式、字段值非空）
- 语义判断（好不好、要不要重写、质量高低）交给 Agent
- 分权制衡：调研 Agent（生产权）/ 审计 Agent（验证权）/ 工具（记录权）

### 新增模板
- `templates/08-最终报告.md`：升级到 v0.6（加入核心对象直采引用要求）
- `templates/16-独立审计Agent.md`
- `templates/17-核心对象直采协议.md`
- `templates/18-核心对象直采模板.md`

## [v0.5] - 2026-07-04

### 破坏性变更
- 统一版本号到 v0.5，废弃 v0.1-v0.10 的碎片化版本号
- `00-使用说明.md` 完全重写（v0.1 到 v0.5，同步到系统真实状态）
- `create_research_project.py` 完全重写（v0.1 到 v0.5）
- `14-研究执行状态机.md` 重写（v0.4 到 v0.5）

### 新增
- **`09-HTML美学规范.md`**：从 `build_research_html.py` 的 CSS（v0.8 + v0.9.1 + v0.9.2 + v0.10）抽取并固化为独立文档。这是 HTML 视觉规格的**单一真相源**。
- **`archive/` 目录**：所有 `.bak` 文件归档于此，明确标注"不作为当前规范"。
- **`archive/README.md`**：说明归档规则。
- **`CHANGELOG.md`**：本文件，版本变更记录。
- 每个文件头加 `<!-- ros-version: v0.5 | last-updated: YYYY-MM-DD | status: current -->` 版本标记。

### 改进
- **`create_research_project.py`**：
  - 从复制 5 个模板扩展到复制 14 个模板
  - 初始化 `candidates.md` + `discarded.md`（不只是 `candidate_pool.json`）
  - 初始化 `intent_doc.json` + `goal_ledger.json`
  - schema_version 升级到 v0.5
  - 状态机加入完整 15 步流程状态
  - 加入 3 个人工确认点标记
- **`14-研究执行状态机.md`**：
  - 从 12 步线性流程升级为 15 步 + 写-读-改闭环
  - 加入 step 0 scaffold / step 7 analysis / step 10 reader_simulation / step 15 publish
  - 加入 3 个人工确认点
  - 加入版本一致性质量底线
  - 加入 HTML 美学合规质量底线

### 归档
- `00-使用说明.md` v0.1 到 `archive/v0.1/`
- `01-调研任务卡.md.v07.bak` 到 `archive/v0.7/`
- `intent_discovery.py.v08.bak` 到 `archive/v0.8/`
- `research_router.py.v08.bak` 到 `archive/v0.8/`
- `validate_research_project.py.v08.bak` 到 `archive/v0.8/`
- `build_research_html.py.v09.bak` 到 `archive/v0.9/`
- `build_research_html.py.v091.bak` 到 `archive/v0.9/`
- `13-假设账本.md` v0.3 到 `archive/v0.9/13-假设账本.md.v0.3.bak`
- `_call_deepseek.py` 到 `archive/misc/`

### 修复的问题
1. **入口文档严重过时**：`00-使用说明.md` 停留在 v0.1（Dify 时代）。已重写为 v0.5。
2. **脚手架严重过时**：`create_research_project.py` 是 v0.1，只复制 5 个模板。已重写为 v0.5，复制全部 14 个模板。
3. **版本号碎片化**：v0.1 / v0.2 / v0.3 / v0.4 / v0.7 / v0.8 / v0.9 / v0.10 散落在不同文件。统一到 v0.5。
4. **重复文件**：`04-假设账本.md`（v0.9）vs `13-假设账本.md`（v0.3）共存。13 归档，保留 04。
5. **.bak 文件污染**：6 个 .bak 文件散落主目录。全部归档到 `archive/v0.x/`。
6. **美学规范分散**：美学规范分散在状态机文档、build_research_html.py CSS、09-可视化视图模型.md 三处。抽取为独立的 `09-HTML美学规范.md`。

## [v0.10] - 2026-07-03（已归档）

- 引入 `reader_simulation.py` 写-读-改闭环
- `final_report_writer.py` 支持 5 幕叙事
- `intent_discovery.py` 加入意图探索
- `concept_ladder_helper.py` 术语阶梯
- `build_research_html.py` CSS v0.10

## [v0.9] - 2026-07-02（已归档）

- `build_research_html.py` CSS v0.9.1 + v0.9.2
- `intent_discovery.py` v0.9
- `research_router.py` v0.9
- `04-假设账本.md` v0.9（融入 ljg-think drill_down）

## [v0.8] - 2026-07-01（已归档）

- `build_research_html.py` CSS v0.8（Anthropic cream + Lora + Starlight asides）
- `intent_discovery.py` v0.8
- `research_router.py` v0.8
- `validate_research_project.py` v0.8

## [v0.7] - 2026-06-30（已归档）

- `research_planner.py` v0.7
- `validate_research_project.py` v0.7
- `goal_tracker.py` v0.7
- `iteration_log.py` v0.7

## [v0.4] - 2026-06-26（已归档）

- `14-研究执行状态机.md` v0.4（12 步线性流程）
- `15-结论溯源清单.md` v0.4
- `research_run_step.py` v0.4

## [v0.3] - 2026-06-25（已归档）

- `research_status.py` v0.3
- `research_planner.py` v0.3
- `validate_research_project.py` v0.3
- `13-假设账本.md` v0.3（已归档，被 04 取代）
- `12-候选池.md` v0.3

## [v0.2] - 2026-06-24（已归档）

- `09-可视化视图模型.md` v0.2

## [v0.1] - 2026-06-22（已归档）

- `00-使用说明.md` v0.1（Dify 时代，已归档）
- `create_research_project.py` v0.1（已重写为 v0.5）
- `research_status.py` v0.3
- `config.py` v0.1
- `ros.py` v0.1（CLI 入口）
- `llm_client.py` v0.1
- `research_planner.py` v0.1
- `research_router.py` v0.1
- `research_run_step.py` v0.1
- `validate_research_project.py` v0.1
- `build_research_html.py` v0.1
- 5 个核心模板：00-使用说明 / 01-调研任务卡 / 02-调研方案 / 03-证据矩阵 / 04-假设账本
- R0/R1/R2/R3 深度档位定义
- 8 种调研类型：company-jd / product / user-research / industry / competitor / topic / portfolio / mixed
