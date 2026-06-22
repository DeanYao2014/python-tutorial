# VitePress 设置详解

> 本文档记录本项目的 VitePress 配置、主题定制、Pyodide 集成等全部设置，方便后续维护和复用。

---

## 一、项目依赖

### package.json

```json
{
  "name": "python-tutorial",
  "version": "1.0.0",
  "description": "Python 3.12+ 进阶教程",
  "type": "module",
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  },
  "devDependencies": {
    "gray-matter": "^4.0.3",
    "vitepress": "^1.6.4"
  }
}
```

| 包 | 版本 | 用途 |
|----|------|------|
| `vitepress` | 1.6.4 | 静态文档站点框架 |
| `gray-matter` | 4.0.3 | 解析 Markdown Frontmatter（auto_sidebar.js 使用） |

### 安装命令

```bash
npm install
```

### 启动命令

```bash
npm run docs:dev      # 开发模式（热重载）
npm run docs:build    # 生产构建
npm run docs:preview  # 预览生产构建
```

---

## 二、目录结构

```
python教程/
├── package.json
├── docs/                          # VitePress 文档根目录
│   ├── .vitepress/                # VitePress 配置与主题
│   │   ├── config.mjs             # 站点配置文件（核心）
│   │   ├── theme/                 # 自定义主题
│   │   │   ├── index.js           # 主题入口：注册全局组件 + 布局扩展
│   │   │   ├── custom.css         # 全局样式（CSS 变量、排版、响应式）
│   │   │   ├── usePyodide.js      # Pyodide 组合式函数（单例管理）
│   │   │   ├── PythonRunner.vue   # 方案A：可运行代码块
│   │   │   └── PythonRepl.vue     # 方案B：页面底部 REPL
│   │   └── utils/
│   │       └── auto_sidebar.js    # 侧边栏自动生成脚本
│   ├── public/                    # 静态资源（logo、favicon 等）
│   ├── index.md                   # 首页（hero layout）
│   ├── 01_基础/                   # 第一部分文档
│   ├── 02_面向对象/               # 第二部分文档
│   ├── 03_高级主题/               # 第三部分文档
│   ├── 04_库与生态/               # 第四部分文档
│   └── 05_设计与品味/             # 第五部分文档
├── code/                          # Python 完整示例代码
├── notes/                         # 备课笔记
├── CLAUDE.md
└── 教学计划.md
```

### 设计原则

- **索引文件命名**：每个章节目录下必须有 `index.md`（如 `docs/01_基础/index.md`），作为该章节目录页
- **内容文件命名**：使用 ASCII 命名，中文标题通过 Frontmatter `title` 指定
- **目录前缀**：目录名以数字前缀（`01_`、`02_`）确保文件系统中的排序
- **URL 编码**：`auto_sidebar.js` 自动对中文目录名做 `encodeURIComponent` 编码

---

## 三、config.mjs 配置详解

### 3.1 站点元信息

```js
title: 'Python 进阶教程',
description: '深入 Python 内部机制、现代用法、设计思想',
lang: 'zh-CN',
```

- `lang: 'zh-CN'` 设置 HTML `<html lang>` 属性，影响搜索索引和浏览器翻译行为

### 3.2 顶部导航栏

```js
nav: [
  { text: '基础',      link: '/01_基础/',      activeMatch: '/01_基础/' },
  { text: '面向对象',  link: '/02_面向对象/',  activeMatch: '/02_面向对象/' },
  { text: '高级主题',  link: '/03_高级主题/',  activeMatch: '/03_高级主题/' },
  { text: '库与生态',  link: '/04_库与生态/',  activeMatch: '/04_库与生态/' },
  { text: '设计与品味', link: '/05_设计与品味/', activeMatch: '/05_设计与品味/' },
],
```

**关键说明**：

| 字段 | 作用 | 示例 |
|------|------|------|
| `text` | 导航栏**显示文字**（可随时改，不影响路由） | `'基础'` |
| `link` | 点击跳转的**目标路径**（必须与目录名一致） | `'/01_基础/'` |
| `activeMatch` | 路径**匹配规则**（正则前缀匹配），决定哪个 tab 高亮 | `'/01_基础/'` |

> **为什么不用自动生成 nav？** 顶级导航只有 5 项且基本不变。手写比自动生成更清晰，可自由控制 `text` 显示文字（如去掉数字前缀）。侧边栏才是真正需要自动生成的地方。

### 3.3 侧边栏

```js
sidebar: {
  '/01_基础/':      set_sidebar('01_基础'),
  '/02_面向对象/':  set_sidebar('02_面向对象'),
  '/03_高级主题/':  set_sidebar('03_高级主题'),
  '/04_库与生态/':  set_sidebar('04_库与生态'),
  '/05_设计与品味/': set_sidebar('05_设计与品味'),
},
```

**工作原理**：

1. 当用户访问 `/01_基础/xxx` 页面时，VitePress 匹配 sidebar key `'/01_基础/'`
2. 调用 `set_sidebar('01_基础')` 扫描 `docs/01_基础/` 目录
3. 递归遍历所有 `.md` 文件，子目录自动生成折叠分组
4. 读取每个文件的 Frontmatter（`title`、`order`、`exclude`）控制显示

**Frontmatter 控制**（在 `.md` 文件头部）：

```yaml
---
title: 自定义显示标题    # sidebar 中显示的文字（默认用文件名）
order: 2                # 排序（数值越小越靠前，默认 Infinity）
exclude: true           # true = 不在 sidebar 中显示
---
```

**关于 `base` 前缀**：本配置中不使用 `base`。`set_sidebar` 已返回以 `/` 开头的绝对路径（如 `/01_基础/filename`），直接用即可。

### 3.4 搜索

```js
search: {
  provider: 'local',      // 本地搜索，无需外部服务
  options: {
    translations: { ... } // 汉化搜索 UI
  },
},
```

- `local` 提供商在构建时生成搜索索引，支持中文分词

### 3.5 Markdown 配置

```js
markdown: {
  lineNumbers: false,        // 不显示行号（保持代码块简洁）
  theme: {
    light: 'github-light',  // 亮色代码主题
    dark: 'github-dark',    // 暗色代码主题
  },
  config(md) {
    // 自定义 fence 渲染器：```python-run → 可运行代码块
  },
},
```

### 3.6 自定义 Markdown 栅格（关键功能）

```js
config(md) {
  const defaultFence = md.renderer.rules.fence

  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    const info = token.info.trim()

    // 匹配 ```python-run 或 ```python run
    if (info === 'python-run' || info === 'python run') {
      const encoded = Buffer.from(token.content, 'utf-8').toString('base64')
      return `<ClientOnly><PythonRunner code="${encoded}" /></ClientOnly>`
    }

    // 其他语言走默认渲染
    if (typeof defaultFence === 'function') {
      return defaultFence(tokens, idx, options, env, self)
    }
    return self.renderToken(tokens, idx, options)
  }
}
```

**数据流**：

```
Markdown 源码                  Node 端（SSR/build）              浏览器端
─────────────────────────────────────────────────────────────────────────────
```python-run               →  Buffer.from → base64           → atob → TextDecoder
print("hello")                   ↓                             ↓
```                         <ClientOnly>                  PythonRunner.vue
                              <PythonRunner code="..." />    解码 → 编辑 → 运行
                              </ClientOnly>                     ↓
                                                          Pyodide WASM 执行
                                                             ↓
                                                          显示 output/error
```

**为什么用 Base64？**

- Python 代码可能包含 `` ` ``、`${}`、`<`、`>` 等字符，直接放在 HTML 属性中会破坏模板
- Base64 编码后是纯 ASCII/Base64 字符集，安全通过 HTML 属性传递
- `Buffer.from()` 正确处理 UTF-8（Node 端），`TextDecoder` 正确还原（浏览器端）

**`<ClientOnly>` 的作用**：
- SSR（服务端渲染）时渲染空占位符，避免 Pyodide（仅浏览器可用）导致构建报错
- 客户端激活时渲染真实组件

---

## 四、自定义主题

### 4.1 主题入口 `theme/index.js`

```js
import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import PythonRunner from './PythonRunner.vue'
import PythonRepl from './PythonRepl.vue'
import './custom.css'

export default {
  extends: DefaultTheme,

  // 全局注册组件（markdown 中可直接使用 <PythonRunner />）
  enhanceApp({ app }) {
    app.component('PythonRunner', PythonRunner)
    app.component('PythonRepl', PythonRepl)
  },

  // 自定义 Layout：在文档页底部注入 REPL
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'doc-footer-before': () => h(PythonRepl),
    })
  },
}
```

**设计要点**：
- `extends: DefaultTheme` 保留 VitePress 的全部默认功能（导航、侧边栏、搜索等）
- `enhanceApp` 注册全局组件，供自定义 markdown fence 输出的 `<PythonRunner />` 使用
- `Layout` 通过 Vue 插槽 `doc-footer-before` 在每个文档页脚前注入 REPL

### 4.2 样式 `custom.css`

**CSS 变量覆盖**（`:root` / `.dark`）：

| 变量 | 作用 | 默认值 |
|------|------|--------|
| `--vp-c-brand-1` | 品牌主色 | `#5c6ac4`（蓝紫） |
| `--vp-c-brand-2` | 品牌悬停色 | `#7c8af0` |
| `--vp-font-family-base` | 正文字体 | PingFang SC → Microsoft YaHei → sans-serif |
| `--vp-font-family-mono` | 代码字体 | JetBrains Mono → Fira Code → monospace |
| `--vp-content-max-width` | 内容区最大宽度 | `820px` |

**排版优化**：
- 正文行高 `1.78`，适配中文阅读
- `h2` 带底部分隔线，视觉层次清晰
- 内联代码有背景色和圆角，易于区分
- 代码块圆角 `8px`，内边距 `1.2rem`

---

## 五、Pyodide 集成

### 5.1 组合式函数 `usePyodide.js`

**架构**：

```
usePyodide.js（模块级单例）
├── pyodideInstance       ← 共享的 Pyodide 解释器
├── isLoading / isReady   ← 响应式状态（Vue ref）
├── loadPyodide()         ← 惰性加载（首次调用才下载 9MB）
├── runCode(code)         ← 执行 Python 代码
└── decodeBase64(b64)     ← UTF-8 安全解码
```

**调用时序**：
```
用户点击 "▶ 运行"
  → loadPyodide()
    → 已有实例？→ 直接返回
    → 正在加载？→ 复用现有 Promise
    → 首次加载 → loadScript(pyodide.js) → loadPyodide() → 缓存实例
  → runCode(code)
    → pyodide.setStdout() 捕获输出
    → pyodide.runPythonAsync(code)
    → 返回 { output, error }
```

### 5.2 组件 A：PythonRunner.vue

**触发方式**：markdown 中写 ` ```python-run `

**UI 结构**：
```
┌──────────────────────────────────────┐
│ [Python 3.12+]           [▶ 运行]    │ ← 头部栏
├──────────────────────────────────────┤
│ print("hello world")                 │ ← 可编辑 textarea
│                                      │
├──────────────────────────────────────┤
│ hello world                          │ ← 输出区（仅运行时显示）
└──────────────────────────────────────┘
```

**交互设计**：
- 代码可直接在 textarea 中编辑
- `Ctrl+Enter` 快捷键运行
- 输出和错误分区显示，错误用红色边框
- 按钮显示加载 spinner，不可点击时变灰

### 5.3 组件 B：PythonRepl.vue

**触发方式**：自动注入每个文档页底部

**UI 结构**：
```
┌──────────────────────────────────────┐
│ ▼ Python REPL — 点击加载交互环境      │ ← 折叠条（默认折叠）
├──────────────────────────────────────┤
│ >>> x = 42                           │ ← 历史记录
│ >>> print(x)                         │
│ 42                                   │
│ >>> █                               │ ← 输入区（>>> 提示符）
│                      [⏎ 运行] [✕]   │
└──────────────────────────────────────┘
```

**交互设计**：
- 默认折叠，点击展开 → 自动加载 Pyodide
- `Enter` 执行，`Shift+Enter` 换行
- 变量在命令间持久化（共享全局命名空间）
- 清空按钮重置历史
- 历史区自动滚动到底部

**与 PythonRunner 的关系**：
- 共用同一个 Pyodide 单例
- PythonRunner 中的代码执行**不影响** REPL 的命名空间（每次 runCode 共用全局命名空间，所以会互相影响）
- 先点 Runner 的"运行"，再在 REPL 中输入 → REPL 可以访问 Runner 定义的变量

---

## 六、auto_sidebar.js 工具

### 来源

从用户之前的项目 `vue3_vitepress_001` 迁移而来，进行了以下修改：

### 修改记录

**1. URL 编码（关键修复）**

```diff
- link: `/${pathname}/${name.replace(/\.md$/, '')}`,
+ link: `/${pathname.split('/').map(encodeURIComponent).join('/')}/${encodeURIComponent(name.replace(/\.md$/, ''))}`,
```

**原因**：原始代码在链接中包含中文字符（如 `/01_基础/对象模型`），浏览器导航时 VitePress 的 `decodeURI()` 触发 `URI malformed` 错误。修复后路径段被正确编码（如 `/01_%E5%9F%BA%E7%A1%80/1.1_object_model`）。

**2. 兼容性确认**

- `DIR_PATH = path.resolve('docs')` — 依赖于 CWD 为项目根目录（`vitepress dev docs` 启动时正确）
- `fs.readdirSync` / `fs.lstatSync` — Node.js 内置，无需额外依赖
- `gray-matter` — 解析 Frontmatter，需要 `npm install`

### 黑名单配置

```js
const BLACK_LIST = [
  'index.md',       // 主页文件（会用文件夹名作为导航文本）
  '.vitepress',     // VitePress 配置
  'node_modules',
  '.idea',
  'assets', 'image', 'images',
  'data', 'codes', 'code'
]
```

可根据需要增删。

---

## 七、常见维护操作

### 新增章节

1. 在 `docs/` 下创建目录（如 `docs/06_新主题/`）
2. 创建 `index.md`（含 Frontmatter）
3. 在 `config.mjs` 中：
   - `nav` 数组添加新项
   - `sidebar` 对象添加新 key

```js
// config.mjs
nav: [
  // ... 其他项
  { text: '新主题', link: '/06_新主题/', activeMatch: '/06_新主题/' },
],
sidebar: {
  // ... 其他 key
  '/06_新主题/': set_sidebar('06_新主题'),
},
```

### 新增内容页面

直接在对应目录下创建 `.md` 文件。建议命名规范：
- 文件名用 ASCII（如 `3.2_decorator_guide.md`）
- 中文标题通过 Frontmatter `title` 指定

```yaml
---
title: 装饰器完全指南
order: 2        # 可选，控制排序
---
```

### 隐藏某个页面

在该页面的 Frontmatter 中添加：

```yaml
---
exclude: true
---
```

### 更换 Pyodide 版本

修改 `docs/.vitepress/theme/usePyodide.js` 中的 CDN 地址：

```js
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.XX.X/full/pyodide.js'
```

### 添加 Pyodide 预装包

修改 `usePyodide.js` 中 `loadPyodide` 调用：

```js
pyodideInstance = await globalThis.loadPyodise({
  packages: ['numpy', 'pandas', 'pydantic'],
})
```

> 每个包首次加载时会额外下载，增加加载时间。建议只预装每章需要的包。

---

## 八、已知问题与解决

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| `URI malformed` 错误 | sidebar 链接含中文，浏览器/VitePress 解析失败 | `auto_sidebar.js` 已添加 `encodeURIComponent` 编码 |
| `ENOENT: scandir` 错误 | sidebar key 路径与目录名不匹配 | 确保 `set_sidebar('XXX')` 的参数与 `docs/` 下的目录名完全一致 |
| Pyodide 加载后页面卡顿 | 9MB WASM 文件下载 + 编译 | 惰性加载，用户点击才下载；CDN 加速 |
| Build 时 Pyodide 报错 | SSR 构建时 `document`/`window` 不可用 | `<ClientOnly>` 包裹，SSR 跳过 |

---

## 九、参考链接

- [VitePress 官方文档](https://vitepress.dev/)
- [VitePress 默认主题配置](https://vitepress.dev/reference/default-theme-config)
- [Pyodide 文档](https://pyodide.org/)
- [markdown-it 插件开发](https://github.com/markdown-it/markdown-it/tree/master/docs)
