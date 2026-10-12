# xsagent Web UI — 设计规范

> 风格代号：**Warm Industrial**  
> 定位：文学编辑工作台 — 工业结构的精确感 + 纸质编辑的温暖质感

---

## 一、设计意图

xsagent 面向长篇作者，界面应像**精装书稿编辑室**，而非通用 SaaS 仪表盘：

- **结构感**：12 列栅格、细线分割、大字号标题 — 传达「编排精密」
- **温暖感**：米灰背景、纸张噪声纹理 — 减少长时间写作的视觉疲劳
- **编辑感**：Playfair Display 衬线标题 — 暗示文学属性
- **技术感**：Inter 无衬线 UI、等宽数据 — 承载 Token、章节号等工程信息

---

## 二、色彩系统

| Token | 值 | 用途 |
|-------|-----|------|
| `--color-bg` | `#EBEBE8` | 页面背景 |
| `--color-bg-elevated` | `#F5F5F2` | 卡片、侧栏 |
| `--color-fg` | `#18181B` | 主文字（Zinc-900） |
| `--color-fg-muted` | `#71717A` | 次要文字（Zinc-500） |
| `--color-accent` | `#0066FF` | 链接、主 CTA、选中态 |
| `--color-accent-muted` | `#0066FF14` | 选中背景（8% 透明度） |
| `--color-border` | `#D4D4D8` | 边框（Zinc-300） |
| `--color-success` | `#16A34A` | 成功、已完成 |
| `--color-warning` | `#CA8A04` | 警告、待处理 |
| `--color-error` | `#DC2626` | 错误、漂移严重 |

**对比度：** 主文字对背景 ≥ 7:1；次要文字 ≥ 4.5:1。

---

## 三、字体

### 3.1 字体族

| 角色 | 字体 | 权重 | 用途 |
|------|------|------|------|
| UI 主字体 | **Inter** | 400, 500, 700, 900 | 导航、按钮、正文、数据 |
| 展示字体 | **Playfair Display** | 400 Italic | 页面主标题、项目名 |
| 等宽 | **JetBrains Mono** 或 `ui-monospace` | 400 | 章节号、ID、Token、日志 |

```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;900&family=Playfair+Display:ital@0;1&display=swap" rel="stylesheet">
```

### 3.2 字号阶梯

| Token | 大小 | 行高 | 用途 |
|-------|------|------|------|
| `text-label` | 10px | 1.2 | 全大写标签 |
| `text-xs` | 12px | 1.4 | 辅助说明 |
| `text-sm` | 14px | 1.5 | 侧栏、表格 |
| `text-base` | 16px | 1.6 | 正文 |
| `text-lg` | 18px | 1.6 | 章节预览 |
| `text-display` | 128–160px | 0.9 | 首页 Hero（`clamp(4rem, 12vw, 10rem)`） |
| `text-title` | 32–48px | 1.1 | 页面标题 |

### 3.3 标签样式（全局）

所有表单标签、区块标签、表格表头：

```css
.label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.2em; /* 重要标签可用 0.3em */
}
```

---

## 四、布局与栅格

### 4.1 12 列结构栅格

- 全页背景叠加 **12 条竖线**（`1px solid var(--color-border)`，opacity 0.5）
- 内容区 `max-width: 1440px`，`margin: 0 auto`，`padding: 0 24px`
- 侧栏固定 `240px`，主内容 `flex-1`

### 4.2 间距（8px 基准）

| Token | 值 |
|-------|-----|
| `space-1` | 4px |
| `space-2` | 8px |
| `space-3` | 12px |
| `space-4` | 16px |
| `space-6` | 24px |
| `space-8` | 32px |
| `space-12` | 48px |
| `space-16` | 64px |

### 4.3 噪声纹理叠加

全屏 `pointer-events: none` 层：

```css
.noise-overlay {
  position: fixed;
  inset: 0;
  opacity: 0.04;
  background-image: url("data:image/svg+xml,..."); /* fractalNoise SVG */
  z-index: 9999;
}
```

---

## 五、组件规范

### 5.1 按钮

| 变体 | 样式 |
|------|------|
| Primary | 背景 `--color-accent`，白字，无圆角或 `2px` |
| Secondary | 透明底，1px border，`--color-border` |
| Ghost | 无边框，hover 下划线 |

```css
.btn {
  transition: transform 0.3s var(--ease-out-expo),
              clip-path 0.3s var(--ease-out-expo);
}
.btn:hover {
  transform: translateY(-1px);
}
```

### 5.2 卡片

```css
.card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  padding: var(--space-6);
  /* 不使用大圆角；可选 2px */
  border-radius: 2px;
}
```

人物卡、伏笔卡：左侧 `3px solid var(--color-accent)` 作为强调边。

### 5.3 输入框

- 高度 `40px`，1px border，背景透明
- Focus：`border-color: var(--color-accent)`，无 glow 阴影
- Textarea：最小高度 `120px`，章节指令编辑器用 `min-height: 200px`

### 5.4 导航侧栏

```
┌─────────────────┐
│ PROJECT         │  ← label
│ 夜半来信        │  ← Playfair Display
├─────────────────┤
│ 概览            │  ← 当前项：accent 左边线
│ 引导            │
│ STORY BIBLE     │
│   人物          │
│   情节          │
│   伏笔          │
│ 章节            │
│ 写作            │
│ 质量            │
└─────────────────┘
```

### 5.5 状态徽章

| 状态 | 颜色 | 示例 |
|------|------|------|
| 进行中 | accent | 写作中 |
| 成功 | success | 记忆已更新 |
| 警告 | warning | 引导未完成 |
| 错误 | error | API 失败 |

---

## 六、动效

**缓动函数（全局）：**

```css
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
```

| 场景 | 属性 | 时长 |
|------|------|------|
| 页面进入 | opacity 0→1, translateY 12px→0 | 400ms |
| 侧栏项 hover | color, border-left | 200ms |
| 卡片 hover | translateY -2px | 300ms |
| 模态打开 | clip-path inset | 350ms |
| SSE 进度条 | width | 线性，实时 |

**原则：** 高惯性、无弹跳；尊重 `prefers-reduced-motion`。

---

## 七、内容排版

### 7.1 章节 Markdown 阅读

- 最大宽度 `65ch`，`font-size: 18px`，`line-height: 1.8`
- 标题用 Playfair Display；正文用 Inter
- 段落间距 `1.5em`；首段无需缩进

### 7.2 Story Bible 数据展示

- 人物 `current_state`：引用块样式，左侧 accent 边线
- 伏笔：卡片 + 章节标签 `CH.04`
- 情节时间轴：竖线连接，已完成节点实心，待展开空心

---

## 八、图标与插图

- 图标库：**Lucide React**，线宽 `1.5px`，尺寸 `16px`（内联）/ `20px`（导航）
- 空状态：单色线性插画，accent 色，无 3D 风格
- 不使用 emoji 作为功能图标

---

## 九、响应式

**Phase 4 目标视口：** 桌面 `≥ 1280px`

| 断点 | 行为 |
|------|------|
| `< 1024px` | 侧栏折叠为抽屉 |
| `< 768px` | 显示「请使用桌面浏览器」提示条 |

---

## 十、无障碍

- 所有交互元素可键盘聚焦，可见 focus ring（`2px accent outline-offset 2px`）
- 图标按钮需 `aria-label`
- SSE 进度区域使用 `aria-live="polite"`
- 色彩不是唯一状态指示（配合文字 / 图标）

---

## 十一、与开发计划对齐

| 阶段 | 设计交付 |
|------|----------|
| P4.1 | Token CSS、AppShell、Button/Card/Label |
| P4.2 | CharacterCard、ForeshadowingBoard、MarkdownView |
| P4.3 | WritePage、JobProgressPanel、ChapterReader |
| P4.4 | QualityDashboard、ApprovalModal |

建议 P4.1 结束前搭建 **Storybook** 或静态组件预览页，冻结基础组件后再铺页面。
