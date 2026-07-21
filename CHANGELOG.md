# Research OS Changelog

所有版本变更记录。日期格式：YYYY-MM-DD。

## [v2.0] - 2026-07-21

### 新增
- 意图拆解协议（24 号模板）：5 轮探索（R1 字面 → R2 差距 → R3 意图树 → R4 路径 → R5 问题说明书），意图树 L0-L4 分层，候选路径剪枝机制
- 洞察账本协议（25 号模板）：insight_ledger.json，洞察判定三条件（反共识/可证伪/决策力），状态流转 draft→verified/downgraded/rejected
- 叙事原型系统（23 号重构）：6 种 archetype 替代单一行文思路，选择矩阵 + why_not 防默认
- 双读者模拟（reader_simulation v2.0）：outsider + layman 双视角，独立阈值
- 3 个新门禁：gate_10 意图树完整性、gate_11 洞察账本、gate_12 跨产物一致性
- 验证器 7 个新检查函数（intent_tree / insight_ledger / archetype / reader_v2 / term_coverage / hard_constraints / cross_artifact）

### 变更
- 08-最终报告瘦身至原 40%，H1-H12 硬约束清单替代混合内容
- intent_discovery.py 从 3 轮扩到 5 轮，新增 revise_intent_tree 支持中途修订
- workflow_def.py 22→23 步，9→12 门禁
- 14-研究执行状态机.md 追加 v2.0 变更摘要
- 全部模板版本头统一 v2.0
- config.py SYSTEM_VERSION v1.5 → v2.0
- 00-使用说明 / README / CHANGELOG / 看板数据同步至 v2.0

### 修复
- （无 bug 修复，本次为计划性大版本升级）

---

## [v1.5] - 2026-07-20

### 系统级审核与治理修复（架构收敛 + 术语统一 + 看板重做）

**问题背景**：全局审核发现 4 类系统性问题——
1. **治理规则未强制执行**：版本号碎片化（13 个模板 v1.2 / 4 个 v1.3 / 7 个 v1.4），门禁数口径冲突（使用说明 8 vs 状态机 9），config.py 停在 v1.1，README 停在 v1.2
2. **同一职责多个实现**：build_research_html.py 与 build_html_v07.py 双构建器并存，ros build 调旧构建器；dashboard.html / portfolio.html / test-write.txt 等死文件散落根目录
3. **数据链断裂**：看板 React 应用数据靠手维护（projects.ts 硬编码），sync_dashboard.py 与在线看板脱节
4. **规范与实现脱节**：验证器缺 step_10.5 产物检查与依赖链；术语混入外部品牌词；反方审计与对抗式审核职责边界不清

**修复内容**：

#### 组件 A：治理统一
- config.py SYSTEM_VERSION：v1.1 → v1.5（恢复单一真相源地位）
- 24 个模板 ros-version 头全部统一 v1.5
- 00-使用说明：8 门禁 → 9 门禁（补门禁9 美学合规验证），模板数 19 → 24
- README 从 v1.2 全面重写至 v1.5

#### 组件 B：术语统一
- 规范去外部品牌词：「Kimi式边界追问」→「边界追问」（规范应自包含）
- 07-反方审计 / 21-对抗式审核协议：各自补充职责边界定义
  - 反方审计（step_8）：**写报告前**攻击分析过程与证据链，产出 red_team.md
  - 对抗式审核（step_9.6）：**报告写完后** subagent context 隔离攻击成稿，产出 adversarial_review.json

#### 组件 C：架构收敛
- HTML 构建器只留 build_html_v07.py；build_research_html.py 归档 archive/v1.5/
- ros.py `ros build` 改调 build_html_v07
- 死文件归档：dashboard.html / portfolio.html / test-write.txt → archive/v1.5/

#### 组件 D：验证器补齐
- STEP_ARTIFACTS 新增 step_10_5_write_read_rewrite（rewrite_instructions.json + iteration_state.json）
- STEP_DEPENDENCIES 补齐：step_10_5 依赖 step_10；step_11/12 依赖 step_10_5；step_13 依赖 step_10_5
- docstring 更新至 v1.5

#### 组件 E：看板推倒重做
- 看板重新定位为**系统运行状态的监视器**（不是宣传页）
- 数据链：sync_dashboard.py 从 projects/ 自动生成 dashboard 数据，消除手维护
- React 全重写：工作流形象化展示（16 步 + 9 门禁可视化）+ 项目真实状态（步骤进度/门禁通过情况/验证结果）

**设计哲学不变**：Smart Agent. Dumb Tools.——所有新增检查仍是机械的，语义判断仍归 Agent。

---

## [v1.4.1] - 2026-07-18

### 新增门禁 9：美学合规验证

**问题背景**：AI眼镜深度调研报告 HTML 完全手写绕过美学规范，导致 10 项严重违规。原 HTML 门禁只列 9 项必须结构，未强制 Agent 从美学规范读取 CSS，未引用最小强制基线，导致 Agent 可以"凭记忆"生成不合规 HTML。

**修复**：
- 14-研究执行状态机：8 门禁 → 9 门禁，新增门禁9「美学合规验证」（步骤 13）
- 要求 Agent 构建 HTML 时必须从 09-HTML美学规范.md 读取 CSS，禁止手写

**遗留问题（v1.5 已修复）**：00-使用说明.md 未同步门禁数，造成 8 vs 9 口径冲突。

---

## [v1.4] - 2026-07-12

### 核心升级：行文思路规划 + Kimi式边界追问 + 人工确认点精简

**问题背景**：v1.3 存在系统性问题——系统规定了"写什么内容"（章节清单），但没规定"读者应该如何建立认知"（章节递进逻辑）。导致：
1. 章节按"内容分类"组织（产品→技术→团队→岗位），不是按"认知递进"组织
2. 第一性原理被放在对象介绍之前（§2.5），读者还不认识对象就被抛入抽象推理
3. 人工确认点（step_2/step_3）在 auto 模式下被跳过，形同虚设
4. 同一套模板用于所有主题，无法适配不同调研对象的认知特点

**根因分析**：
- 模板被迫同时承担"内容清单"和"行文思路"两个职责，但它只能履行前者
- 第一性原理协议的"在呈现数据前"被误解为"在介绍对象前"
- 人工确认点与 auto 模式设计哲学冲突

**解决方案**：5 组件升级

#### 组件 A：行文思路规划步骤（step_7.5，核心新增）
- 新增 `templates/23-行文思路规划协议.md`
- 在 step_7（分析）之后、step_8（反方审计）之前执行
- 产出 `05-analysis/narrative-plan.md`
- 借鉴 Kimi 深度研究的三级节点提纲法（共识→分歧→边界），适配为（对象本质→运作机制→决策约束）
- 固定元原则（从具象到抽象、认知递进），放开具体结构（Agent 动态决定）
- templates/08 从"必须遵循的模板"降级为"参考结构"

#### 组件 B：Kimi 式边界追问（step_1.5 升级）
- `templates/20-方向选择协议.md` 从"≥2完整方向选择"改为"2个边界追问"
- 更轻量：Agent 只问 2 个边界问题，不设计完整方向
- 更聚焦：问"范围到哪/深度多深"，不问"你要走哪条路"
- 向后兼容 v1.3 的 directions_proposed 格式

#### 组件 C：删除人工确认点
- 删除 step_2（任务卡）人工确认点
- 删除 step_3（调研方案）人工确认点
- 删除 step_13（HTML美学）人工确认点
- 仅保留 step_1.5（方向选择）作为唯一用户参与点
- 防止"自己出题自己改答案"：独立会话审计 + 审计范围扩展 + 读者模拟 + 对抗式审核

#### 组件 D：第一性原理位置修正
- `templates/22-第一性原理拆解协议.md` 修正措辞
- "在呈现数据前"改为"在给出判断和决策前"，消除语义歧义
- 第一性原理位置从固定 §2.5 改为 narrative-plan.md 动态决定
- 新增验证规则：第一性原理章节必须在"调研对象"章节之后

#### 组件 E：验证器升级
- 新增 `check_narrative_plan`：检查存在性 + 关键词 + 元原则检查 section
- 新增 `check_first_principles_position`：检查第一性原理位置
- STEP_ARTIFACTS 新增 step_7_5_narrative_plan
- STEP_DEPENDENCIES 新增依赖链：step_8/step_9 依赖 step_7_5
- MIN_CONTENT_CHARS_BY_DEPTH 新增 narrative-plan.md 阈值

#### 其他升级
- `templates/14-研究执行状态机.md`：15步→16步，7门禁→8门禁
- `templates/08-最终报告.md`：章节顺序调整，第一性原理从 §2.5 移到 §6
- `templates/00-使用说明.md`：全面更新到 v1.4
- `create_research_project.py`：steps 新增 step_7_5，confirmations 更新
- 借鉴 Kimi 深度研究的 23 步推理流程思路（动态循环而非固定线性）

**设计哲学增强**：
- v1.3：Smart Agent. Dumb Tools. + 结构化字段解决"可跳过" + 对抗测试解决"可糊弄"
- v1.4：+ 行文思路规划解决"可填空"（报告不再是模板填空，而是认知递进规划）
- 不改变"Dumb Tools"原则——narrative-plan 检查仍是机械的（存在性+关键词+section）

**验证结果**：待测试项目验证

---

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
