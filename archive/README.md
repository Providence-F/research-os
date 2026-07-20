# Research OS Archive

此目录存放历史版本归档。**不要参考这里的文件作为当前规范。**

当前规范在：
- `templates/` 目录
- `*.py` 文件（Python 引擎，根目录）

## 归档原因

这些文件是 Research OS 从 v0.1 演进到 v1.1 过程中的历史快照。保留是为了：

1. **版本回退**：如果新版本引入问题，可以从归档恢复
2. **审计**：查看某个功能是怎么演化的
3. **学习**：理解系统设计决策的变迁

## 目录结构

```
archive/
├── v0.1/    # 最早的入口文档（Dify 时代）
├── v0.7/    # 引入 goal_ledger 和 iteration_log 之前
├── v0.8/    # 引入 ljg-* skill 融合之前
├── v0.9/    # 引入 core_generators 之前
├── v1.0/    # v1.0 归档（含旧版 build_html_v07.py，v1.1 已恢复到根目录）
├── v1.5/    # v1.5 架构收敛归档（见下）
└── misc/    # 一次性脚本、临时文件
```

## v1.5 归档内容（2026-07-20 架构收敛）

| 文件 | 归档原因 |
|---|---|
| `build_research_html.py` | 重复 HTML 构建器，v1.5 起唯一构建器为根目录 `build_html_v07.py` |
| `build_dashboard.py` | 旧版单文件看板生成器，v1.5 起看板为 `dashboard/` React 应用 + `scripts/sync_dashboard.py` 数据链 |
| `dashboard.html` | 旧看板静态产物，已被 React 看板取代 |
| `portfolio.html` | 一次性静态产物，非系统组件 |
| `test-write.txt` | 临时测试文件 |
| `system_fix.py` | 一次性修复脚本，已执行完毕 |
| `generate_waic_reports.py` | 一次性 WAIC 报告生成脚本，非系统组件 |

## 当前版本

Research OS 当前版本：**v1.5**（2026-07-20）

统一版本号后，所有文件头标注 `<!-- ros-version: v1.5 -->`。

v1.5 相对 v1.1 的核心变化：
- 治理统一：config.py / README / CHANGELOG / 使用说明 / 状态机 / 24 模板版本头全部回归 v1.5
- 术语统一：去外部品牌词；反方审计（step_8）与对抗式审核（step_9.6）职责边界写清
- 架构收敛：HTML 构建只留 `build_html_v07.py`；看板收敛为 React 应用 + sync 数据链
- 验证器补齐：step_10.5 写-读-改闭环产物检查 + 依赖链补全

v1.1 相对 v1.0 的核心变化：
- 恢复 build_html_v07.py 到根目录（v1.0 误归档）
- 验证器增加 9 项 HTML 必须结构检查
- 使用说明同步真实状态

v1.0 相对 v0.7.1 的核心变化：
- v1.0：新增行动方案比例检查 / LaTeX 公式渲染检查

v0.7.1 相对 v0.5 的核心变化：
- v0.6：新增独立审计 Agent / 核心对象直采协议 / 写-读-改闭环
- v0.7：新增 7 项机械检查 / 通用 HTML 构建器 / 状态机升级
- v0.7.1：Dumb Tools 合规修复（2 处违反已修复）

设计哲学：**Smart Agent. Dumb Tools.**
