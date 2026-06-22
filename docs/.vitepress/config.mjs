import { defineConfig } from 'vitepress'
import { set_sidebar } from './utils/auto_sidebar.js'

// ──────────────────────────────────────────────
// VitePress 站点配置
// https://vitepress.dev/reference/site-config
// ──────────────────────────────────────────────
export default defineConfig({

  // GitHub Pages 部署基路径（本地 dev 时自动忽略）
  base: '/python-tutorial/',

  // 站点元信息
  title: 'Python 进阶教程',
  description: '深入 Python 内部机制、现代用法、设计思想',
  lang: 'zh-CN',

  // 页面 head 注入
  head: [
    ['link', { rel: 'icon', href: '/favicon.ico' }],
  ],

  // ============================================
  // 主题配置
  // https://vitepress.dev/reference/default-theme-config
  // ============================================
  themeConfig: {

    // ── 顶部导航栏（手动维护，5 项不常变） ──
    nav: [
      {
        text: '基础入门',
        link: '/00_快速基础/',
        activeMatch: '/00_快速基础/',
      },
      {
        text: '基础进阶',
        link: '/01_基础/',
        activeMatch: '/01_基础/',
      },
      {
        text: '面向对象',
        link: '/02_面向对象/',
        activeMatch: '/02_面向对象/',
      },
      {
        text: '高级主题',
        link: '/03_高级主题/',
        activeMatch: '/03_高级主题/',
      },
      {
        text: '库与生态',
        link: '/04_库与生态/',
        activeMatch: '/04_库与生态/',
      },
      {
        text: '设计与品味',
        link: '/05_设计与品味/',
        activeMatch: '/05_设计与品味/',
      },
      {
        text: '算法',
        link: '/06_python的基础算法/',
        activeMatch: '/06_python的基础算法/',
      },
    ],

    // ── 侧边栏（自动生成，基于目录结构和 Frontmatter） ──
    // set_sidebar 已返回绝对路径（如 /01_基础/filename），无需 base 前缀
    sidebar: {
      '/00_快速基础/':      set_sidebar('00_快速基础'),
      '/01_基础/':      set_sidebar('01_基础'),
      '/02_面向对象/':  set_sidebar('02_面向对象'),
      '/03_高级主题/':  set_sidebar('03_高级主题'),
      '/04_库与生态/':  set_sidebar('04_库与生态'),
      '/05_设计与品味/': set_sidebar('05_设计与品味'),
      '/06_python的基础算法/': set_sidebar('06_python的基础算法'),
    },

    // ── 大纲（右侧目录） ──
    outline: {
      level: [2, 3],   // 显示 h2 和 h3
      label: '本页目录',
    },

    // ── 本地搜索（基于页面文本，无需外部服务） ──
    search: {
      provider: 'local',
      options: {
        translations: {
          button: {
            buttonText: '搜索',
            buttonAriaLabel: '搜索文档',
          },
          modal: {
            displayDetails: '显示详情',
            resetButtonTitle: '清除',
            backButtonTitle: '返回',
            noResultsText: '无结果',
            footer: {
              selectText: '选择',
              navigateText: '切换',
              closeText: '关闭',
            },
          },
        },
      },
    },

    // ── 社交链接（右上角） ──
    socialLinks: [
      { icon: 'github', link: 'https://github.com/DeanYao2014/python-tutorial' },
    ],

    // ── 页脚 ──
    docFooter: {
      prev: '上一章',
      next: '下一章',
    },

    // ── 编辑链接 ──
    editLink: {
      pattern: 'https://github.com/DeanYao2014/python-tutorial/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页',
    },

    // ── 最后更新时间 ──
    lastUpdated: {
      text: '最后更新',
      formatOptions: { dateStyle: 'medium' },
    },
  },

  // ============================================
  // 忽略死链接（页面尚未编写完成）
  // ============================================
  ignoreDeadLinks: true,

  // ============================================
  // Markdown 配置
  // ============================================
  markdown: {
    // 行号显示
    lineNumbers: false,
    // 代码块主题
    theme: {
      light: 'github-light',
      dark: 'github-dark',
    },

    /**
     * 自定义 markdown-it 插件：
     * 将 ```python-run 代码块转换为可交互的 Python 运行环境
     */
    config(md) {
      // 保存默认 fence 渲染器
      const defaultFence = md.renderer.rules.fence

      md.renderer.rules.fence = (tokens, idx, options, env, self) => {
        const token = tokens[idx]
        const info = token.info.trim()

        // 匹配 ```python-run 或 ```python run
        if (info === 'python-run' || info === 'python run') {
          const encoded = Buffer.from(token.content, 'utf-8').toString('base64')
          // 临时将语言名改为 python，让 Shiki 正确高亮
          // 渲染后恢复原始 info（避免影响后续处理）
          token.info = 'python'
          const highlighted = defaultFence(tokens, idx, options, env, self)
          token.info = info
          return `${highlighted}\n<ClientOnly><PythonRunner code="${encoded}" /></ClientOnly>`
        }

        // 其他语言走默认渲染
        if (typeof defaultFence === 'function') {
          return defaultFence(tokens, idx, options, env, self)
        }
        return self.renderToken(tokens, idx, options)
      }
    },
  },

  // ============================================
  // Vite 配置
  // ============================================
  vite: {
    ssr: {
      // Pyodide 仅浏览器端使用，SSR 构建时跳过
      noExternal: [],
    },
  },
})
