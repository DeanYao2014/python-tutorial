<!--
  PythonRepl.vue — 页面底部持久化 Python REPL（方案 B）
  ======================================================
  终端风格的 Python 交互环境，维护会话状态（变量跨行保留）。
  默认折叠在页面底部，点击展开后可连续输入命令。

  通过 VitePress 主题布局注入到每个文档页底部。
-->
<template>
  <div class="python-repl" :class="{ expanded: isExpanded }">
    <!-- 折叠条 -->
    <button class="repl-toggle" @click="toggle">
      <span class="repl-toggle-icon">{{ isExpanded ? '▼' : '▲' }}</span>
      <span>Python REPL</span>
      <span v-if="!isReady && !loadError" class="repl-hint">— 点击加载交互环境</span>
      <span v-if="isLoading" class="repl-status loading"><span class="spinner"></span>加载中...</span>
      <span v-if="loadError" class="repl-status error">加载失败</span>
    </button>

    <!-- REPL 主体 -->
    <div v-show="isExpanded" class="repl-body">
      <!-- 历史输出 -->
      <div ref="historyEl" class="repl-history">
        <div v-for="(entry, i) in history" :key="i" class="repl-entry">
          <div class="repl-input-line">
            <span class="repl-prompt">&gt;&gt;&gt;</span>
            <pre class="repl-code">{{ entry.code }}</pre>
          </div>
          <pre v-if="entry.output" class="repl-output">{{ entry.output }}</pre>
          <pre v-if="entry.error" class="repl-error">{{ entry.error }}</pre>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="repl-input-area">
        <span class="repl-prompt">&gt;&gt;&gt;</span>
        <textarea
          ref="inputEl"
          v-model="currentInput"
          class="repl-input"
          rows="2"
          spellcheck="false"
          placeholder="输入 Python 代码..."
          @keydown="handleKeydown"
        />
        <button class="repl-run-btn" :disabled="isLoading" @click="execute">
          &#8629; 运行
        </button>
        <button class="repl-clear-btn" @click="clearHistory" title="清空历史">
          &#10005;
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { usePyodide } from './usePyodide.js'

const { isLoading, isReady, loadError, loadPyodide, runCode } = usePyodide()

const isExpanded   = ref(false)
const currentInput = ref('')
const history      = ref([])
const historyEl    = ref(null)
const inputEl      = ref(null)

function toggle() {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    // 展开时惰性加载 Pyodide
    loadPyodide().catch(() => {})
    nextTick(() => inputEl.value?.focus())
  }
}

async function execute() {
  const code = currentInput.value.trim()
  if (!code) return

  const result = await runCode(code)
  history.value.push({
    code:   code,
    output: result.output || null,
    error:  result.error || null,
  })
  currentInput.value = ''

  // 自动滚动到底部
  await nextTick()
  if (historyEl.value) {
    historyEl.value.scrollTop = historyEl.value.scrollHeight
  }
}

function clearHistory() {
  history.value = []
  currentInput.value = ''
}

function handleKeydown(e) {
  // Shift+Enter 换行，Enter 执行
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    execute()
  }
}
</script>

<style scoped>
.python-repl {
  margin: 2rem 0 1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  overflow: hidden;
  background: var(--vp-c-bg-soft);
  transition: border-color 0.2s;
}
.python-repl.expanded {
  border-color: var(--vp-c-brand);
}

/* ── 折叠条 ── */
.repl-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.6rem 1rem;
  border: none;
  background: var(--vp-c-bg-mute);
  color: var(--vp-c-text-2);
  font-size: 0.82rem;
  cursor: pointer;
  text-align: left;
  transition: color 0.15s;
  font-family: inherit;
}
.repl-toggle:hover { color: var(--vp-c-text-1); }
.repl-toggle-icon { font-size: 0.7rem; flex-shrink: 0; }
.repl-hint { color: var(--vp-c-text-3); font-size: 0.78rem; }
.repl-status { font-size: 0.75rem; margin-left: auto; }
.repl-status.loading { color: var(--vp-c-brand); display: flex; align-items: center; gap: 4px; }
.repl-status.error   { color: var(--vp-c-danger-1); }

/* ── REPL 主体 ── */
.repl-body {
  border-top: 1px solid var(--vp-c-divider);
}

/* ── 历史 ── */
.repl-history {
  max-height: 250px;
  overflow-y: auto;
  padding: 0.75rem;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.83rem;
  line-height: 1.55;
}
.repl-entry { margin-bottom: 0.5rem; }
.repl-input-line {
  display: flex;
  gap: 0.4rem;
  align-items: baseline;
}
.repl-prompt {
  color: var(--vp-c-brand);
  font-weight: 600;
  flex-shrink: 0;
  user-select: none;
}
.repl-code {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--vp-c-text-1);
  font-family: inherit;
}
.repl-output {
  margin: 0.2rem 0 0 1.2rem;
  color: var(--vp-c-text-2);
  font-family: inherit;
  white-space: pre-wrap;
}
.repl-error {
  margin: 0.2rem 0 0 1.2rem;
  color: var(--vp-c-danger-1);
  font-family: inherit;
  white-space: pre-wrap;
}

/* ── 输入区 ── */
.repl-input-area {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-top: 1px solid var(--vp-c-divider);
  background: var(--vp-c-bg);
}
.repl-input {
  flex: 1;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.83rem;
  line-height: 1.5;
  resize: none;
  outline: none;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-1);
  transition: border-color 0.15s;
}
.repl-input:focus { border-color: var(--vp-c-brand); }
.repl-run-btn {
  padding: 0.4rem 0.8rem;
  font-size: 0.8rem;
  font-weight: 500;
  border: 1px solid var(--vp-c-brand);
  border-radius: 5px;
  background: var(--vp-c-brand);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  font-family: inherit;
  transition: opacity 0.15s;
}
.repl-run-btn:hover { opacity: 0.85; }
.repl-run-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.repl-clear-btn {
  padding: 0.4rem 0.6rem;
  font-size: 0.85rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 5px;
  background: var(--vp-c-bg);
  color: var(--vp-c-text-2);
  cursor: pointer;
  flex-shrink: 0;
  font-family: inherit;
}
.repl-clear-btn:hover { color: var(--vp-c-danger-1); border-color: var(--vp-c-danger-1); }

/* ── 加载动画 ── */
.spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
  flex-shrink: 0;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
