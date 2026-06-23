import { ref, readonly } from 'vue'

// ============================================================
// Pyodide 组合式函数 —— 单例管理 Python WASM 运行时
// ============================================================
//
// 设计要点：
// 1. 全局单例：同一页面上 PythonRunner 和 PythonRepl 共享一个解释器
// 2. 惰性加载：页面打开不下载 Pyodide，首次点"运行"才加载（~9MB）
// 3. 状态共享：所有组件通过 ref 响应式感知加载进度
// 4. stdout 捕获：每次执行前重设 stdout，收集输出

// Pyodide CDN 地址（可替换为自建 CDN 或指定版本）
const PYODIDE_URL = 'https://cdn.jsdelivr.net/pyodide/v0.27.0/full/pyodide.js'

// 模块级单例状态
let pyodideInstance = null    // Pyodide 实例缓存
let loadingPromise = null     // 加载中的 Promise，避免重复加载
const isLoading = ref(false)  // 是否正在加载
const isReady   = ref(false)  // 是否已就绪
const loadError = ref(null)   // 加载错误信息

/**
 * 动态加载外部脚本（仅浏览器端调用）
 */
function loadScript(url) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${url}"]`)
    if (existing) return resolve()
    const script = document.createElement('script')
    script.src = url
    script.onload = () => resolve()
    script.onerror = () => reject(new Error(`无法加载 Pyodide: ${url}`))
    document.head.appendChild(script)
  })
}

/**
 * 解码 base64 字符串为 UTF-8 文本
 */
function decodeBase64(b64) {
  const binary = atob(b64)
  const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0))
  return new TextDecoder('utf-8').decode(bytes)
}

/**
 * 主入口：使用 Pyodide 的组合式函数
 *
 * 使用方式：
 *   const { isLoading, isReady, loadPyodide, runCode, pyodide } = usePyodide()
 *
 * @returns {{ isLoading, isReady, loadError, loadPyodide, runCode }}
 */
export function usePyodide() {

  /**
   * 加载 Pyodide（幂等，首次加载后续调用直接返回）
   */
  async function loadPyodide() {
    // 已有实例 → 直接返回
    if (pyodideInstance) return pyodideInstance
    // 正在加载 → 复用加载 Promise
    if (loadingPromise) return loadingPromise

    isLoading.value = true
    loadError.value = null

    loadingPromise = (async () => {
      try {
        await loadScript(PYODIDE_URL)
        // loadPyodide 由脚本注入到 globalThis
        // 显式指定 indexURL：Pyodide 的标准库文件所在目录
        // 必须设为 CDN 路径，否则在 GitHub Pages 等托管环境会 fallback
        // 到 document.baseURI 导致 404
        const PYODIDE_INDEX = 'https://cdn.jsdelivr.net/pyodide/v0.27.0/full/'
        pyodideInstance = await globalThis.loadPyodide({
          indexURL: PYODIDE_INDEX,
        })
        isReady.value = true
        return pyodideInstance
      } catch (err) {
        loadError.value = err.message
        loadingPromise = null  // 允许重试
        throw err
      } finally {
        isLoading.value = false
      }
    })()

    return loadingPromise
  }

  /**
   * 在 Pyodide 中执行 Python 代码，返回 { output, error }
   * @param {string} code - 要执行的 Python 代码
   * @param {object} [opts]
   * @param {boolean} [opts.b64] - code 是否为 base64 编码
   * @returns {Promise<{output: string, error: string|null}>}
   */
  async function runCode(code, { b64 = false } = {}) {
    const pyodide = await loadPyodide()
    const sourceCode = b64 ? decodeBase64(code) : code

    const lines = []
    // 重设 stdout 捕获
    pyodide.setStdout({
      batched: (text) => { lines.push(text) },
    })

    try {
      await pyodide.runPythonAsync(sourceCode)
      return { output: lines.join('\n').trim(), error: null }
    } catch (err) {
      return { output: lines.join('\n').trim(), error: err.message }
    }
  }

  return {
    isLoading: readonly(isLoading),
    isReady:   readonly(isReady),
    loadError: readonly(loadError),
    loadPyodide,
    runCode,
  }
}
