import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import PythonRunner from './PythonRunner.vue'
import PythonRepl from './PythonRepl.vue'
import HeroBackground from './HeroBackground.vue'
import './custom.css'

export default {
  extends: DefaultTheme,

  enhanceApp({ app }) {
    app.component('PythonRunner', PythonRunner)
    app.component('PythonRepl', PythonRepl)
  },

  Layout() {
    return h(DefaultTheme.Layout, null, {
      // 首页 Hero 区域注入 Canvas 粒子背景
      'home-hero-before': () => h(HeroBackground),
      // 文档页底部注入 REPL
      'doc-footer-before': () => h(PythonRepl),
    })
  },
}
