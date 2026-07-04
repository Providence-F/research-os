<!-- ros-version: v0.5 | last-updated: 2026-07-04 | status: current -->

# Research OS

**深度调研工作流系统**。给定一个研究主题，引导走完"任务定义 → 候选源采集 → 证据矩阵 → 假设账本 → 反方审计 → 最终报告 → HTML 可视化"的完整链路，产出有信任度保证的深度报告。

**当前版本**：v0.5（2026-07-04）

## 快速开始

### 1. 入口文档

**先读 [`templates/00-使用说明.md`](templates/00-使用说明.md)**——这是唯一入口，同步到 v0.5 真实状态。

### 2. 创建项目

```bash
python ros.py new "项目名" --type product --depth R2 --html
```

### 3. 完整流程（15 步）

详见 [`templates/00-使用说明.md`](templates/00-使用说明.md) 第 4 节。

### 4. 验证

```bash
python ros.py validate "项目路径"
```

## 核心文档

| 文档 | 作用 |
|---|---|
| [`templates/00-使用说明.md`](templates/00-使用说明.md) | **唯一入口**，强制先读 |
| [`templates/09-HTML美学规范.md`](templates/09-HTML美学规范.md) | HTML 视觉规格的**单一真相源** |
| [`templates/14-研究执行状态机.md`](templates/14-研究执行状态机.md) | 15 步流程 + 写-读-改闭环 |
| [`CHANGELOG.md`](CHANGELOG.md) | 版本变更记录 |
| [`archive/README.md`](archive/README.md) | 历史版本归档说明 |

## 版本治理

- **当前版本**：v0.5
- **版本标记**：每个文件头 `<!-- ros-version: v0.5 | status: current -->`
- **归档规则**：旧版本移到 `archive/v0.x/`，不作为当前规范
- **变更记录**：见 [`CHANGELOG.md`](CHANGELOG.md)

## 目录结构

```
research-os/
├── README.md                    # 本文件
├── CHANGELOG.md                 # 版本变更记录
├── ros.py                       # CLI 入口
├── *.py                         # Python 引擎（27 个脚本）
├── templates/                   # 模板库
├── archive/                     # 历史版本归档
└── projects/                    # 研究项目目录
```

## 设计原则

1. **单一真相源**：每个规范只有一个权威文件
2. **强制入口**：Agent 必须先读 `00-使用说明.md`
3. **强制验证**：每步完成后必须跑 validator
4. **版本治理**：.bak 归档，加版本头
5. **写-读-改闭环**：报告写完必须跑读者模拟
