import path from 'node:path'
import fs from 'node:fs'

// 文件根目录：使用 resolve() 方法将相对路径转换为绝对路径
// docs 目录通常是你的 源文件文件夹，用于存放 Markdown (.md) 文件，
const DIR_PATH = path.resolve('docs')

// 黑名单（排除不需要的文件和文件夹）
const BLACK_LIST = [
  'index.md', // index.md 通常是主页，不需要出现在侧边栏
  '.vitepress', // VitePress 配置文件夹
  'node_modules', // 依赖文件夹
  '.idea', // 开发工具相关文件夹
  'assets', // 资源文件
  'image',
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
const isDirectory = (path) => fs.lstatSync(path).isDirectory()

/**
 * 获取两个数组的差异：返回 arr1 中有但 arr2 中没有的项
 * @param {string[]} arr1 - 原始数组
 * @param {string[]} arr2 - 需要排除的数组
 * @returns {string[]} 过滤后的数组
 */
const intersections = (arr1, arr2) =>
  Array.from(new Set(arr1.filter((item) => !new Set(arr2).has(item))))

/**
 * 递归获取文件夹下的 Markdown 结构，生成 VitePress 侧边栏
 * @param {string[]} params - 当前文件夹下的所有文件或子文件夹
 * @param {string} path1 - 当前文件夹的绝对路径
 * @param {string} pathname - 当前文件夹的名称，用于构造 link
 * @returns {object[]} 侧边栏配置数组
 */
function getList(params, path1, pathname) {
  const res = []
  for (const file of params) {
    const dir = path.join(path1, file)
    const isDir = isDirectory(dir)

    if (isDir) {
      // 如果是文件夹，则递归获取其子文件
      const files = fs.readdirSync(dir)
      res.push({
        text: file,
        collapsed: true, // 允许折叠
        items: getList(files, dir, `${pathname}/${file}`)
      })
    } else {
      const name = path.basename(file)
      const suffix = path.extname(file)

      if (suffix !== '.md') {
        continue // 只处理 `.md` 文件，忽略其他文件
      }

      res.push({
        text: name.replace(/\.md$/, ''), // 去掉 `.md` 后缀
        link: `/${pathname}/${name.replace(/\.md$/, '')}` // 侧边栏链接，必须以 `/` 开头
      })
    }
  }

  // 按照文件名排序（支持数字排序）
  res.sort((a, b) => a.text.localeCompare(b.text, undefined, { numeric: true }))

  return res
}

/**
 * 生成 VitePress 侧边栏配置
 * @param {string} pathname - md文件夹的名称
 * @returns {object[]} 侧边栏配置数组
 */
export const set_sidebar = (pathname) => {
  const dirPath = path.join(DIR_PATH, pathname)
  const files = fs.readdirSync(dirPath) //获取pathname文件夹下的所有文件和文件夹,不递归
  const items = intersections(files, BLACK_LIST) // 过滤掉黑名单文件(不需要生成侧边栏的文件和文件夹)
  return getList(items, dirPath, pathname) // 递归生成侧边栏数据
}
