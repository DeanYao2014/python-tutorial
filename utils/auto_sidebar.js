import path from 'node:path'
import fs from 'node:fs'
import matter from 'gray-matter'

/**
 * 自动生成 VitePress sidebar 配置脚本
 *
 * 使用方法：
 * 1. 安装依赖：
 *    pnpm add -D gray-matter
 *
 * 2. 将本文件放在 docs/.vitepress/config/auto_sidebar.js 或 .ts 中。
 *
 * 3. 在 VitePress 配置文件中引入：
 *    import { defineConfig } from 'vitepress'
 *    import { set_sidebar } from './auto_sidebar'
 *
 * 4. 在 themeConfig.sidebar 中调用：
 *    export default defineConfig({
 *      themeConfig: {
 *        nav: [
 *          { text: '指南', link: '/guide/' },
 *          { text: '笔记', link: '/notes/' }
 *        ],
 *        sidebar: {
 *          '/guide/': set_sidebar('guide'),
 *          '/notes/': set_sidebar('notes')
 *        }
 *      }
 *    })
 *
 * 5. 在 Markdown 文件中可通过 Frontmatter 控制：
 *    ---
 *    title: 配置说明   # sidebar 显示标题
 *    order: 2         # 排序，数值越小越靠前
 *    exclude: true    # 不生成在 sidebar
 *    ---
 *
 * 返回结果示例：
 * 假设目录结构：
 * docs/
 *   guide/
 *     index.md
 *     getting-started.md
 *     config.md
 *     advanced/
 *       routing.md
 *       data-loading.md
 *       custom-theme.md
 *   notes/
 *     2025年/
 *       january.md
 *       february.md
 *     2024年/
 *       december.md
 *
 * set_sidebar('guide') 返回：
 * [
 *   { "text": "index", "link": "/guide/index" },
 *   { "text": "getting-started", "link": "/guide/getting-started" },
 *   { "text": "config", "link": "/guide/config" },
 *   {
 *     "text": "advanced",
 *     "collapsed": true,
 *     "items": [
 *       { "text": "routing", "link": "/guide/advanced/routing" },
 *       { "text": "data-loading", "link": "/guide/advanced/data-loading" },
 *       { "text": "custom-theme", "link": "/guide/advanced/custom-theme" }
 *     ]
 *   }
 * ]
 *
 * set_sidebar('notes') 返回：
 * [
 *   {
 *     "text": "2025年",
 *     "collapsed": true,
 *     "items": [
 *       { "text": "january", "link": "/notes/2025年/january" },
 *       { "text": "february", "link": "/notes/2025年/february" }
 *     ]
 *   },
 *   {
 *     "text": "2024年",
 *     "collapsed": true,
 *     "items": [
 *       { "text": "december", "link": "/notes/2024年/december" }
 *     ]
 *   }
 * ]
 */

const DIR_PATH = path.resolve('docs')

// 黑名单：排除不需要生成侧边栏的文件和文件夹
const BLACK_LIST = [
  'index.md', // 主页文件
  '.vitepress', // VitePress 配置文件夹
  'node_modules', // 依赖文件夹
  '.idea', // 开发工具文件夹
  'assets', // 资源文件夹
  'image', // 图片文件夹
  'images',
  'data',
  'codes',
  'code'
]

/**
 * 判断路径是否为文件夹
 * @param {string} path - 目标路径
 * @returns {boolean} 是否为文件夹
 */
const isDirectory = (path) => {
  try {
    return fs.lstatSync(path).isDirectory()
  } catch (e) {
    console.error(`无法检查路径 ${path}: ${e.message}`)
    return false
  }
}

/**
 * 获取两个数组的差异：返回 arr1 中有但 arr2 中没有的项
 * @param {string[]} arr1 - 原始数组（文件列表）
 * @param {string[]} arr2 - 黑名单数组
 * @returns {string[]} 过滤后的文件列表
 */
const intersections = (arr1, arr2) =>
  Array.from(new Set(arr1.filter((item) => !new Set(arr2).has(item))))

/**
 * 递归生成侧边栏结构，基于文件夹和 Markdown 文件
 * @param {string[]} params - 当前文件夹下的文件或子文件夹列表
 * @param {string} path1 - 当前文件夹的绝对路径
 * @param {string} pathname - 当前文件夹的相对路径（用于构造 link）
 * @returns {object[]} 侧边栏配置数组
 */
function getList(params, path1, pathname) {
  const res = []

  // 过滤黑名单中的子文件夹
  const filteredParams = intersections(params, BLACK_LIST)

  for (const file of filteredParams) {
    const dir = path.join(path1, file) // 拼接文件/文件夹路径
    const isDir = isDirectory(dir)

    if (isDir) {
      // 处理文件夹：递归获取子文件并生成子菜单
      try {
        const files = fs.readdirSync(dir)
        const subItems = getList(files, dir, `${pathname}/${file}`)
        if (subItems.length > 0) {
          // 仅当子菜单有内容时添加
          res.push({
            text: file, // 文件夹名作为菜单标题
            collapsed: true, // 默认折叠子菜单
            items: subItems
          })
        }
      } catch (e) {
        console.error(`无法读取文件夹 ${dir}: ${e.message}`)
      }
    } else {
      // 处理文件：仅处理 .md 文件
      const name = path.basename(file)
      const suffix = path.extname(file)

      if (suffix !== '.md') {
        continue
      } // 跳过非 Markdown 文件

      // 读取 Markdown 文件，解析 Frontmatter
      try {
        const fileContent = fs.readFileSync(dir, 'utf-8')
        const { data } = matter(fileContent)
        // exclude 则跳过不在生成侧边栏
        if (data.exclude === true) {
          continue
        }
        // 获取 order 和 title，order 未定义时设为 Infinity，title 未定义时用文件名
        const order = data.order !== undefined ? Number(data.order) : Infinity
        const title = data.title || name.replace(/\.md$/, '')

        res.push({
          text: title, // 侧边栏显示文本（优先使用 Frontmatter 的 title）
          link: `/${pathname}/${name.replace(/\.md$/, '')}`, // 页面链接，适配 base: '/docs/'
          order // 存储 order 用于排序
        })
      } catch (e) {
        console.error(`无法读取文件 ${dir}: ${e.message}`)
      }
    }
  }

  // 混合排序：优先按 order 排序，order 相同或未定义时按 text 排序
  res.sort((a, b) => {
    const orderA = a.order || Infinity
    const orderB = b.order || Infinity
    return orderA - orderB || a.text.localeCompare(b.text, undefined, { numeric: true })
  })

  // 移除 order 属性，符合 VitePress 侧边栏格式
  return res.map(({ order, ...item }) => item)
}

/**
 * 生成 VitePress 侧边栏配置
 * @param {string} pathname - Markdown 文件夹的相对路径（例如 '心得笔记/2025年'）
 * @returns {object[]} 侧边栏配置数组
 */
export const set_sidebar = (pathname) => {
  const dirPath = path.join(DIR_PATH, pathname)
  try {
    const files = fs.readdirSync(dirPath) // 读取文件夹内容
    const items = intersections(files, BLACK_LIST) // 过滤黑名单
    const result = getList(items, dirPath, pathname)
    console.log(`生成侧边栏：${pathname}`, JSON.stringify(result, null, 2)) // 调试输出
    return result
  } catch (e) {
    console.error(`无法读取目录 ${dirPath}: ${e.message}`)
    return []
  }
}
