# 插件推荐

Python 开发环境推荐组合：Python + Pylance + Ruff + Jupyter，再加上 GitLens、Path Intellisense 等辅助插件。

| 插件 | 作用 |
| --- | --- |
| **Python (ms-python.python)** | 必备，提供调试、运行、Jupyter 支持 |
| **Pylance (ms-python.vscode-pylance)** | 智能提示和类型检查 |
| **Ruff (charliermarsh.ruff)** | Lint + 格式化，替代 Flake8/Black/isort |
| **Jupyter (ms-toolsai.jupyter)** | 在 VS Code 里直接运行 Notebook |
| **Black Formatter (ms-python.black-formatter)** | 如果你更喜欢 Black 格式化，可以和 Ruff 配合使用 |
| **isort (ms-python.isort)** | 专门管理 import 排序（Ruff 已内置，但有时单独插件更灵活） |
| **GitLens** | Git 历史、代码作者信息 |
| **Path Intellisense** | 自动补全文件路径 |
| **Error Lens** | 把错误提示直接显示在代码行上，更直观 |

```json
{
  "python.languageServer": "Pylance",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "charliermarsh.ruff",
  "ruff.enable": true,
  "ruff.lintOnSave": true,
  "ruff.formatOnSave": true
}
```