<!-- ros-version: v1.5 | last-updated: 2026-07-20 | status: current -->

# Research OS

**深度调研工作流系统**。给定一个研究主题，引导走完"任务定义 → 方向选择 → 候选源采集 → 证据矩阵 → 假设账本 → 核心对象直采 → 多 Agent 分析 → 行文思路规划 → 反方审计 → 独立审计 → 对抗式审核 → 读者模拟 → 写-读-改闭环 → 最终报告 → HTML 可视化"的完整链路，产出有信任度保证的深度报告。

**当前版本**：v1.5（2026-07-20）

**设计哲学**：**Smart Agent. Dumb Tools.**——工具只做机械检查（存在性、字数、格式、字段值非空），语义判断（好不好、要不要重写、质量高低）交给 Agent。

## 快速开始

### 1. 入口文档

**先读 [`templates/00-使用说明.md`](templates/00-使用说明.md)**——这是唯一入口，与系统真实状态同步。如果它与其他文件冲突，以它为准。

### 2. 创建项目

```bash
python ros.py new --name "项目名" --type product --depth R2 --html
```

### 3. 完整流程（16 步 + 9 个强制门禁）

详见 [`templates/14-研究执行状态机.md`](templates/14-研究执行状态机.md)。

### 4. 验证

```bash
python validate_research_project.py "项目路径"
```

验证器全部为机械检查，无语义判断。

## 核心文档

| 文档 | 作用 |
|---|---|
| [`templates/00-使用说明.md`](templates/00-使用说明.md) | **唯一入口**，强制先读 |
| [`templates/14-研究执行状态机.md`](templates/14-研究执行状态机.md) | 16 步流程 + 9 个门禁 |
| [`templates/09-HTML美学规范.md`](templates/09-HTML美学规范.md) | HTML 视觉规格的**单一真相源** |
| [`templates/16-独立审计Agent.md`](templates/16-独立审计Agent.md) | 独立审计 Agent 协议 |
| [`templates/17-核心对象直采协议.md`](templates/17-核心对象直采协议.md) | 核心对象直采协议 |
| [`templates/20-方向选择协议.md`](templates/20-方向选择协议.md) | 方向选择（边界追问）协议 |
| [`templates/21-对抗式审核协议.md`](templates/21-对抗式审核协议.md) | 对抗式审核协议（subagent 攻击报告） |
| [`templates/22-第一性原理拆解协议.md`](templates/22-第一性原理拆解协议.md) | 第一性原理三层结构 |
| [`templates/23-行文思路规划协议.md`](templates/23-行文思路规划协议.md) | 行文思路规划（narrative-plan） |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本变更记录 |
| [`archive/README.md`](archive/README.md) | 历史版本归档说明 |

## v1.5 核心升级

1. **治理统一**：版本号/门禁数回归单一真相——全部模板头 v1.5，门禁统一 9 个（补门禁9 美学合规验证）
2. **术语统一**：规范去外部品牌词（「Kimi式」→「边界追问」）；反方审计与对抗式审核职责边界写清
3. **构建器收敛**：HTML 构建只留 `build_html_v07.py`，`ros build` 改调 v07；重复/死文件归档
4. **验证器补齐**：补 step_10.5（写-读-改闭环）产物检查与 step_10.5/11/12 依赖链
5. **看板重做**：看板作为独立产品从第一性原理重设计——sync 数据链 + 工作流形象化

## 版本治理

- **当前版本**：v1.5
- **版本标记**：每个文件头 `<!-- ros-version: v1.5 | last-updated: YYYY-MM-DD | status: current -->`
- **归档规则**：旧版本移到 `archive/`，不作为当前规范
- **变更记录**：见 [`CHANGELOG.md`](CHANGELOG.md)
- **发布完整性**：每次发布必须同步更新 README / 00-使用说明 / CHANGELOG / 14-状态机 / 所有模板版本头

## 目录结构

```
research-os/
├── README.md                    # 本文件
├── CHANGELOG.md                 # 版本变更记录
├── ros.py                       # CLI 入口
├── config.py                    # 配置 + SYSTEM_VERSION 单一真相源
├── validate_research_project.py # Dumb Validator
├── build_html_v07.py            # 唯一 HTML 构建器
├── *.py                         # Python 引擎
├── templates/                   # 模板库（24 个）
├── dashboard/                   # 系统看板（React）
├── scripts/sync_dashboard.py    # 看板数据同步
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
