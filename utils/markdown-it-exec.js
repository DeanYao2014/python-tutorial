export function execPlugin(md) {
  md.renderer.rules.fence = (tokens, idx, options, env, self) => {
    const token = tokens[idx]
    const code = token.content.trim()
    const lang = token.info.trim()

    if (lang === 'js') {
      const codeId = `code-${Math.random().toString(36).substr(2, 9)}`
      return `
        <pre><code>${md.utils.escapeHtml(code)}</code></pre>
        <button onclick="executeCode('${codeId}', \`${md.utils.escapeHtml(code)}\`)">运行代码</button>
        <div id="${codeId}-output" class="code-output"></div>
      `
    }

    return `<pre><code>${md.utils.escapeHtml(code)}</code></pre>`
  }
}
