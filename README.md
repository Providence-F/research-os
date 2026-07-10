<!-- ros-version: v1.1 | last-updated: 2026-07-10 | status: current -->

# Research OS

**深度调研工作流系统**。给定一个研究主题，引导走完"任务定义 → 候选源采集 → 证据矩阵 → 假设账本 → 核心对象直采 → 多 Agent 分析 → 反方审计 → 独立审计 → 读者模拟 → 写-读-改闭环 → 最终报告 → HTML 可视化"的完整链路，产出有信任度保证的深度报告。

**当前版本**：v1.1（2026-07-10）

**设计哲学**：**Smart Agent. Dumb Tools.**——工具只做机械检查（存在性、字数、格式、字段值非空），语义判断（好不好、要不要重写、质量高低）交给 Agent。

## 快速开始

### 1. 入口文档

**先读 [`templates/00-使用说明.md`](templates/00-使用说明.md)**——这是唯一入口，已同步到 v1.0 真实状态。

### 2. 创建项目

```bash
python ros.py new "项目名" --type product --depth R2 --html
```

### 3. 完整流程（15 步 + 5 个强制门禁）

详见 [`templates/14-研究执行状态机.md`](templates/14-研究执行状态机.md)。

### 4. 验证

```bash
python validate_research_project.py "项目路径"
```

v0.7 验证器包含 14 项检查（7 项 v0.6 保留 + 7 项 v0.7 新增），全部为机械检查，无语义判断。

## 核心文档

| 文档 | 作用 | 版本 |
|---|---|---|
| [`templates/00-使用说明.md`](templates/00-使用说明.md) | **唯一入口**，强制先读 | v1.0 |
| [`templates/14-研究执行状态机.md`](templates/14-研究执行状态机.md) | 15 步流程 + 5 个门禁 + 写-读-改闭环 | v0.7 |
| [`templates/09-HTML美学规范.md`](templates/09-HTML美学规范.md) | HTML 视觉规格的**单一真相源** | v1.0 |
| [`templates/16-独立审计Agent.md`](templates/16-独立审计Agent.md) | 独立审计 Agent 协议（v0.6 新增） | v0.6 |
| [`templates/17-核心对象直采协议.md`](templates/17-核心对象直采协议.md) | 核心对象直采协议（v0.6 新增） | v0.6 |
| [`templates/18-核心对象直采模板.md`](templates/18-核心对象直采模板.md) | 核心对象直采模板（v0.6 新增） | v0.6 |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本变更记录 | v1.0 |
| [`archive/README.md`](archive/README.md) | 历史版本归档说明 | v1.0 |

## v1.0 核心升级

### v0.7 新增 7 项机械检查

1. **JSON 字段值非空**（解决空 JSON 通过问题）
2. **task-card 字段值**（解决模板说明文字占字符数问题）
3. **步骤依赖**（step N done 则依赖项必须 done）
4. **内容深度指标**（URL 数、数据点数、章节数）
5. **HTML 禁止模式**（滚轮、未闭合 div）
6. **核心对象提及次数**（从 task-card 读取声明，不硬编码）
7. **前置门禁**（核心对象直采前必须完成任务卡和研究计划）

### v1.0 Dumb Tools 合规修复

- `check_core_object_mentions` 从硬编码改为从 task-card.md 读取声明的核心对象
- `build_rewrite_instructions` 删除 action 分类，只提供客观数据，由 Agent 决定 action

### v0.6 新增模块

- **独立审计 Agent**（步骤 9.5，强制门禁，5 问全 PASS）
- **核心对象直采协议**（步骤 6.5，强制门禁，URL ≥ 3 + 对象 ≥ 3）
- **写-读-改闭环**（步骤 10.5，结构化重写指令 + 迭代状态追踪）

## 版本治理

- **当前版本**：v1.0
- **版本标记**：每个文件头 `<!-- ros-version: v1.1 | last-updated: YYYY-MM-DD | status: current -->`
- **归档规则**：旧版本移到 `archive/v0.x/`，不作为当前规范
- **变更记录**：见 [`CHANGELOG.md`](CHANGELOG.md)
- **发布完整性**：每次发布必须同步更新 README.md / 00-使用说明.md / CHANGELOG.md / 所有模板版本头

## 目录结构

```
research-os/
├── README.md                    # 本文件
├── CHANGELOG.md                 # 版本变更记录
├── ros.py                       # CLI 入口
├── validate_research_project.py # v1.0 Dumb Validator
├── build_html_v07.py            # v0.7 通用 HTML 构建器
├── final_report_writer.py       # v1.0 写-读-改闭环
├── *.py                         # Python 引擎（27 个脚本）
├── templates/                   # 模板库（18 个）
├── archive/                     # 历史版本归档
└── projects/                    # 研究项目目录
```

## 设计原则

1. **Smart Agent. Dumb Tools.**：工具只做机械检查，语义判断交给 Agent
2. **单一真相源**：每个规范只有一个权威文件
3. **强制入口**：Agent 必须先读 `00-使用说明.md`
4. **强制验证**：每步完成后必须跑 validator
5. **分权制衡**：调研 Agent（生产权）/ 审计 Agent（验证权）/ 工具（记录权）三权分立
6. **状态-产物绑定**：状态由产物推断，不是 Agent 写的字符串
7. **写-读-改闭环**：报告写完必须跑读者模拟，最多 2 轮迭代
