# Research OS Changelog

所有版本变更记录。日期格式：YYYY-MM-DD。

## [v0.5] - 2026-07-04

### 破坏性变更
- 统一版本号到 v0.5，废弃 v0.1-v0.10 的碎片化版本号
- `00-使用说明.md` 完全重写（v0.1 → v0.5，同步到系统真实状态）
- `create_research_project.py` 完全重写（v0.1 → v0.5）
- `14-研究执行状态机.md` 重写（v0.4 → v0.5）

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
- `00-使用说明.md` v0.1 → `archive/v0.1/`
- `01-调研任务卡.md.v07.bak` → `archive/v0.7/`
- `intent_discovery.py.v08.bak` → `archive/v0.8/`
- `research_router.py.v08.bak` → `archive/v0.8/`
- `validate_research_project.py.v08.bak` → `archive/v0.8/`
- `build_research_html.py.v09.bak` → `archive/v0.9/`
- `build_research_html.py.v091.bak` → `archive/v0.9/`
- `13-假设账本.md` v0.3 → `archive/v0.9/13-假设账本.md.v0.3.bak`
- `_call_deepseek.py` → `archive/misc/`

### 修复的问题
1. **入口文档严重过时**：`00-使用说明.md` 停留在 v0.1（Dify 时代），完全没提到 ros CLI、intent_discovery、goal_tracker、reader_simulation、concept_ladder、core_generators、layout_spec、5 幕叙事、写-读-改闭环。✅ 已重写为 v0.5。
2. **脚手架严重过时**：`create_research_project.py` 是 v0.1，只复制 5 个模板，新建项目缺一半必产物导致 validator FAIL。✅ 已重写为 v0.5，复制全部 14 个模板。
3. **版本号碎片化**：v0.1 / v0.2 / v0.3 / v0.4 / v0.7 / v0.8 / v0.9 / v0.10 散落在不同文件。✅ 统一到 v0.5。
4. **重复文件**：`04-假设账本.md`（v0.9）vs `13-假设账本.md`（v0.3）共存。✅ 13 归档，保留 04。
5. **.bak 文件污染**：6 个 .bak 文件散落主目录。✅ 全部归档到 `archive/v0.x/`。
6. **美学规范分散**：美学规范分散在状态机文档、build_research_html.py CSS、09-可视化视图模型.md 三处。✅ 抽取为独立的 `09-HTML美学规范.md`。

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
