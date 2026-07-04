<!-- ros-version: v0.5 | last-updated: 2026-07-04 | status: current -->

# HTML 美学规范 v0.5

> **单一真相源**：所有 Research OS 生成的 HTML 报告必须遵循本规范。
> 本规范从 `build_research_html.py` 的 CSS（v0.8 + v0.9.1 + v0.9.2 + v0.10）抽取并固化。
> 修改本文件 = 修改所有 HTML 报告的视觉规格。**不要在 .py 代码里写死 CSS，从这里读取**。

---

## 1. 设计哲学

读者打开 HTML 时，带着**决策需求 + 认知差距 + 有限的注意力预算**。可视化的作用是恢复被线性化丢失的结构信息。

**核心原则**：长文论述 + 结构化块穿插，不是仪表盘。读者要的是"能读完的深度报告"，不是"一屏卡片墙"。

## 2. 设计灵感来源

| 来源 | 借鉴了什么 |
|---|---|
| Anthropic claude.ai | 米色背景 `#faf9f5`、Lora 衬线正文、暖砖红 accent |
| Astro Starlight | 内容宽度 45rem、行高 1.75、aside 提示块模式 |
| Stripe Press | 衬线正文、窄栏、慷慨行距 |

## 3. 设计代币（Design Tokens）

### 3.1 颜色

```css
:root {
  /* 背景 */
  --bg: #faf9f5;          /* 米色主背景（Anthropic cream）*/
  --bg-card: #ffffff;      /* 卡片背景 */
  --bg-soft: #f5f4ee;      /* 软背景（代码块、表格 hover）*/
  --bg-softer: #f0eee5;   /* 更软的背景 */

  /* 文字 */
  --fg: #1a1a1a;           /* 主文字 */
  --fg-soft: #3d3d3d;      /* 次要文字 */
  --muted: #6b6b6b;        /* 弱化文字 */
  --muted-2: #8e8e8e;      /* 更弱化 */

  /* 线条 */
  --line: #e5e3d8;         /* 主分隔线 */
  --line-soft: #ede9dd;    /* 软分隔线 */

  /* 主色 */
  --accent: #b85b44;       /* 暖砖红（Anthropic clay 兄弟色）*/
  --accent-soft: #f5e8e0;
  --accent-bg: #fdf6f0;

  /* 多色提示块（Starlight aside 模式）*/
  --note: #2c5f8d;          --note-bg: #eef4fa;       --note-border: #b8d3eb;
  --tip: #5d4ba0;            --tip-bg: #f0ecf7;        --tip-border: #c7b8e0;
  --caution: #b8732e;        --caution-bg: #fbf0e0;    --caution-border: #e8c890;
  --danger: #b85b44;         --danger-bg: #fceeea;     --danger-border: #e8b8a8;
  --ok: #4a7a4a;             --ok-bg: #eef5ee;
}
```

### 3.2 字体

```css
--font-serif: "Lora", "Noto Serif SC", "Source Han Serif SC", Georgia, serif;
--font-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
--font-mono: "JetBrains Mono", "Geist Mono", Consolas, monospace;
```

**字体加载**（必须）：
```html
<link href="https://fonts.googleapis.com/css2?family=Lora:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
```

**使用规则**：
- 正文（`p`, `li`, `h1`, `h2`, `h3`）= `--font-serif`（Lora 衬线）
- 元信息（`.hero-meta`, `.ladder-field`, `th`, `code` 的元信息）= `--font-sans`（Inter 无衬线）
- 代码 = `--font-mono`（JetBrains Mono）

### 3.3 字号

| 元素 | 字号 | 行高 |
|---|---|---|
| `h1` | 38px | 1.15 |
| `.hero-verdict` | 30px | 1.25 |
| `h2`（章节标题） | 26px | 1.25 |
| `h3` | 19px | - |
| `h4` | 14px | - |
| `p`, `li`（正文） | 16px | 1.75 |
| `td`, `th` | 14.5px / 13px | 1.6 |
| `code` | 13.5px | - |
| `.kicker`（小标题） | 11.5px | - |
| `.ladder-term` | 20px | - |

### 3.4 间距

```css
--space-1: 0.25rem;
--space-2: 0.5rem;
--space-3: 0.75rem;
--space-4: 1rem;
--space-5: 1.5rem;
--space-6: 2rem;
--space-7: 3rem;
--space-8: 4rem;
```

### 3.5 圆角

```css
--radius: 6px;       /* 卡片、代码块 */
--radius-sm: 4px;    /* 小元素、按钮 */
```

### 3.6 布局

```css
--sidebar-width: 15rem;     /* 左侧目录栏 */
--reader-width: 56rem;       /* 正文阅读宽度 */
--shell-max-width: 1480px;   /* 页面最大宽度 */
```

**布局规则**：
- `.page-shell`: `grid-template-columns: var(--sidebar-width) minmax(0, 1fr)`
- `aside`: `position: sticky; top: 2rem`（固定侧栏 TOC）
- `main`: 正文区，最大宽度 56rem

## 4. 必须包含的视觉模块

### 4.1 阅读进度条（必须有）

```css
.reading-progress {
  position: fixed; top: 0; left: 0;
  height: 2px; background: var(--accent);
  width: 0; z-index: 50;
  transition: width 0.1s ease-out;
}
```

JavaScript 用 `IntersectionObserver` 或 `scroll` 事件更新 width。

### 4.2 侧栏目录（必须有）

- `<aside>` 包含 `<nav class="toc">`
- 当前可见章节高亮（`.toc a.active`）
- `position: sticky; top: 2rem`

### 4.3 Hero 区（核心判断）

```css
.vm-hero {
  border-left: 3px solid var(--accent);
  padding: 0.5rem 0 0.5rem 1.5rem;
  background: transparent;
  margin-bottom: 3rem;
}
.hero-verdict { font-size: 30px; font-weight: 600; }
```

**Hero 必须包含**：
- `.kicker`（11.5px 全大写 accent 色）
- `.hero-verdict`（30px 衬线一句话结论）
- `.hero-summary`（16px 衬线摘要）
- `.hero-meta`（13.5px 无衬线元信息表）

### 4.4 章节结构

```html
<section class="chapter">
  <h2>§N 章节标题</h2>
  <p>深度正文...</p>
  <h3>小节</h3>
  <p>...</p>
</section>
```

`.chapter` 之间用 `border-top: 1px solid var(--line)` 分隔。

## 5. 视觉模块清单（按需使用）

### 5.1 Concept Ladder（术语阶梯）

非技术背景读者用的术语解释模块。每级含"直觉"和"锚点"双字段。

```html
<ol class="concept-ladder">
  <li class="ladder-entry">
    <div class="ladder-head">
      <span class="ladder-num">1</span>
      <h3 class="ladder-term">术语名</h3>
    </div>
    <div class="ladder-row ladder-intuition">
      <span class="ladder-field">直觉</span>
      <span class="ladder-value">大白话解释</span>
    </div>
    <div class="ladder-row ladder-anchor">
      <span class="ladder-field">锚点</span>
      <span class="ladder-value">类比或锚定物</span>
    </div>
  </li>
</ol>
```

### 5.2 Analogy Card（类比卡）

```html
<div class="analogy-card">
  <div class="analogy-x">源概念</div>
  <div class="analogy-arrow">→</div>
  <div class="analogy-y">类比对象</div>
</div>
```

### 5.3 多色 Aside 提示块

```html
<aside class="note">    <!-- 蓝 #2c5f8d -->
<aside class="tip">     <!-- 紫 #5d4ba0 -->
<aside class="caution"> <!-- 橙 #b8732e -->
<aside class="danger">  <!-- 红 #b85b44 -->
<aside class="ok">       <!-- 绿 #4a7a4a -->
```

### 5.4 证据等级徽章

```html
<span class="evidence-grade evidence-grade-a">A</span>  <!-- 源码/技术报告 -->
<span class="evidence-grade evidence-grade-b">B</span>  <!-- 官方博客 -->
<span class="evidence-grade evidence-grade-c">C</span>  <!-- 社区评测 -->
<span class="evidence-grade evidence-grade-d">D</span>  <!-- 弱证据 -->
```

### 5.5 结论状态徽章

```html
<span class="conclusion-status status-confirmed">confirmed</span>
<span class="conclusion-status status-partial">partial</span>
<span class="conclusion-status status-rejected">rejected</span>
<span class="conclusion-status status-downgraded">downgraded</span>
<span class="conclusion-status status-falsified">falsified</span>
```

### 5.6 图示组件（flowchart-block）

```html
<figure class="flowchart-block">
  <figcaption><span class="fig-num">图 N</span> · 图说明</figcaption>
  <div class="flowchart-canvas"><svg viewBox="0 0 560 420">...</svg></div>
  <p class="flowchart-note">读图说明</p>
</figure>
```

### 5.7 分组卡片（grouped-cards）

```html
<div class="grouped-cards">
  <div class="card-group">
    <div class="card-group-title">组名</div>
    <div class="card-group-desc">描述</div>
    <div class="card-items">
      <div class="card-item">条目</div>
    </div>
  </div>
</div>
```

### 5.8 折叠详情（details）

```html
<details>
  <summary>点击展开</summary>
  <div class="details-body">...</div>
</details>
```

`summary::before` 用 `▸` 旋转箭头，`[open]` 时 `rotate(90deg)`。

### 5.9 代码片段卡（code-snippet-card）

```html
<div class="code-snippet-card">
  <div class="code-snippet-meta">文件路径 · 行号</div>
  <pre><code>代码</code></pre>
</div>
```

### 5.10 表格（Stripe Press 风格）

```css
table { border-collapse: collapse; width: 100%; table-layout: fixed; font-size: 14.5px; }
th { border-bottom: 2px solid var(--fg); font-weight: 600; }
td { border-bottom: 1px solid var(--line); }
tbody tr:hover { background: var(--bg-soft); }
```

**关键**：无重边框，hover 高亮，th 双线底边。

## 6. 必须的 JavaScript

### 6.1 阅读进度条

```javascript
window.addEventListener('scroll', () => {
  const h = document.documentElement;
  const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
  document.querySelector('.reading-progress').style.width = pct + '%';
});
```

### 6.2 TOC 高亮

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      document.querySelectorAll('.toc a').forEach(a => a.classList.remove('active'));
      const link = document.querySelector(`.toc a[href="#${e.target.id}"]`);
      if (link) link.classList.add('active');
    }
  });
}, { rootMargin: '-20% 0px -70% 0px' });
document.querySelectorAll('.chapter').forEach(c => observer.observe(c));
```

### 6.3 Tab 切换（双页报告）

```javascript
function switchTab(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById(pageId).classList.add('active');
  document.querySelector(`[data-page="${pageId}"]`).classList.add('active');
  history.replaceState(null, '', '#' + pageId);
}
// URL hash 支持
if (location.hash) switchTab(location.hash.slice(1));
```

## 7. 美学合规自检清单

生成 HTML 后，必须跑这个清单：

- [ ] `--bg` = `#faf9f5`（不是 `#ffffff`，不是 `#faf7f0`）
- [ ] `--accent` = `#b85b44`（不是 `#8b5a3c`，不是 `#d97757`）
- [ ] `--font-serif` 含 `Lora`
- [ ] `--font-sans` 含 `Inter`
- [ ] Google Fonts CDN 已加载
- [ ] `h1` 字号 = 38px
- [ ] `.hero-verdict` 字号 = 30px
- [ ] `h2` 字号 = 26px
- [ ] `p` / `li` 行高 = 1.75
- [ ] `.reading-progress` 存在
- [ ] `aside.toc` 存在且 sticky
- [ ] `.chapter` 之间有 `border-top`
- [ ] 折叠区用 `<details>` + `▸` 旋转
- [ ] 表格无重边框，th 双线底边

## 8. 禁止事项

- ❌ 不要用纯白背景（`#ffffff`）做主背景
- ❌ 不要用旧版 accent `#8b5a3c`
- ❌ 不要用 `border-radius: 2px`（已废弃，统一 6px/4px）
- ❌ 不要用 Georgia 系统字体替代 Lora
- ❌ 不要把深度正文塞进折叠区（折叠区只放附录）
- ❌ 不要只有卡片没有正文（卡片是辅助，正文是主体）
- ❌ 不要用重边框表格（用 Stripe Press 风格）

## 9. 版本治理

| 版本 | 变更 |
|---|---|
| v0.5 | 从 `build_research_html.py` 抽取并固化为独立文档 |
| v0.8-v0.10 | 散落在 .py 代码里（已归档）|

修改本文件后，必须同步更新 `build_research_html.py` 的 CSS 字符串，或改为从本文件读取。
