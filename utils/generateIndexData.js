// generateIndexData.js
import path from 'node:path'
import fs from 'node:fs'
import matter from 'gray-matter'

const ROOT = path.resolve('./') // Markdown 根目录
const BLACK_LIST = ['.vitepress', 'node_modules', 'assets', 'images', 'image', 'index.md']

function walk(dir, group = '') {
  const entries = fs.readdirSync(dir)
  const result = []

  for (const entry of entries) {
    const fullPath = path.join(dir, entry)
    const stat = fs.statSync(fullPath)

    if (stat.isDirectory() && !BLACK_LIST.includes(entry)) {
      result.push(...walk(fullPath, path.relative(ROOT, fullPath)))
    } else if (entry.endsWith('.md')) {
      const content = fs.readFileSync(fullPath, 'utf-8')
      const { data } = matter(content)

      if (data.exclude === true) {
        continue
      }
      // 如果文件名再黑名单中也排除
      if (BLACK_LIST.includes(entry)) {
        continue
      }

      result.push({
        title: data.title || entry.replace(/\.md$/, ''),
        description: data.description || '',
        link: '/' + path.relative(ROOT, fullPath).replace(/\.md$/, '').replace(/\\/g, '/'),
        group: group || 'root'
      })
    }
  }

  return result
}

const indexData = walk(ROOT)

fs.writeFileSync(
  path.resolve('./.vitepress/api-index.data.json'),
  JSON.stringify(indexData, null, 2),
  'utf-8'
)

console.log('✅ API 索引数据已生成')
