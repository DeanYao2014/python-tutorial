<!--
  PythonRunner.vue — 为 VitePress 代码块添加"运行"功能
  ======================================================
  渲染在 Shiki 语法高亮代码块下方，提供运行按钮和输出区域。
  仅在浏览器端渲染（ClientOnly），Pyodide 惰性加载。
-->
<template>
  <div class="py-runner">
    <div class="py-runner-bar">
      <span class="py-runner-badge">Python 3.12+</span>
      <span v-if="isLoading" class="py-runner-status loading">
        <span class="spinner"></span>加载 Pyodide...
      </span>
      <span v-else-if="isReady" class="py-runner-status ready">就绪</span>
      <button
        class="py-runner-btn"
        :disabled="isLoading"
        @click="execute"
      >
        <span v-if="isLoading" class="spinner"></span>
        <span v-else>&#9654; 运行</span>
      </button>
    </div>
    <div v-if="output || error" class="py-runner-output">
      <pre v-if="output" class="output-text">{{ output }}</pre>
      <pre v-if="error" class="error-text">{{ error }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { usePyodide } from './usePyodide.js'

const props = defineProps({
  code: { type: String, required: true },
})

const { isLoading, isReady, runCode } = usePyodide()

const output = ref('')
const error = ref('')

async function execute() {
  output.value = ''
  error.value = ''
  const result = await runCode(props.code, { b64: true })
  output.value = result.output
  error.value = result.error
}
</script>

<style scoped>
.py-runner {
  margin-top: -17px;   /* 紧贴代码块底部（抵消 VitePress 代码块 margin-bottom ~16px + border 1px） */
  margin-bottom: 1rem;
}

/* ── 工具栏 ── */
.py-runner-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.4rem 0.75rem;
  background: var(--vp-c-bg-mute);
  border: 1px solid var(--vp-c-divider);
  border-top: none;
  border-radius: 0 0 8px 8px;
}
.py-runner-badge {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--vp-c-brand);
  background: var(--vp-c-brand-soft);
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}
.py-runner-status {
  font-size: 0.7rem;
  color: var(--vp-c-text-2);
}
.py-runner-status.ready {
  color: var(--vp-c-brand);
}
.py-runner-btn {
  margin-left: auto;
  padding: 3px 12px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid var(--vp-c-brand);
  border-radius: 5px;
  background: var(--vp-c-brand);
  color: #fff;
  cursor: pointer;
  transition: opacity 0.15s;
  display: flex;
  align-items: center;
  gap: 4px;
}
.py-runner-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.py-runner-btn:hover:not(:disabled) {
  opacity: 0.85;
}

/* ── 输出区 ── */
.py-runner-output {
  margin-top: 0.5rem;
}
.output-text {
  margin: 0;
  padding: 0.5rem 0.75rem;
  background: var(--vp-c-bg-soft);
  border: 1px solid var(--vp-c-divider);
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.83rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--vp-c-text-1);
}
.error-text {
  margin: 0.25rem 0 0;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 0, 0, 0.06);
  border: 1px solid rgba(255, 0, 0, 0.15);
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 0.83rem;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--vp-c-danger-1, #d32f2f);
}

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
