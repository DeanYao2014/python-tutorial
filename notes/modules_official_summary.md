# 6. 模块 — Python 官方教程总结

> 原文：[docs.python.org/zh-cn/3/tutorial/modules.html](https://docs.python.org/zh-cn/3/tutorial/modules.html)
>
> 版本：Python 3.14.5

---

## 1. 模块基本概念

**模块是包含 Python 定义和语句的 `.py` 文件。** 把各种定义存入一个文件，在脚本或解释器中使用——不用把函数定义复制到各个程序。

```python
# fibo.py — 斐波那契数列模块
def fib(n):
    """输出直到 n 的斐波那契数列"""
    a, b = 0, 1
    while a < n:
        print(a, end=' ')
        a, b = b, a + b
    print()

def fib2(n):
    """返回直到 n 的斐波那契数列（列表）"""
    result = []
    a, b = 0, 1
    while a < n:
        result.append(a)
        a, b = b, a + b
    return result
```

- 通过 `import fibo` 导入，然后用 `fibo.fib(1000)` 访问
- 模块全局变量 `__name__` 的值是模块名字符串：`fibo.__name__ == 'fibo'`
- 函数可以赋值给本地变量：`fib = fibo.fib`

---

## 2. import 的 4 种写法

| 写法 | 效果 | 推荐场景 |
|------|------|---------|
| `import fibo` | 导入模块名 `fibo`，需用 `fibo.fib()` | 通用，推荐 |
| `from fibo import fib, fib2` | 直接导入指定名称，不需前缀 | 常用特定函数时 |
| `from fibo import *` | 导入所有不以下划线开头的名称 | **不推荐**（污染命名空间） |
| `import fibo as fib` | 给模块起别名 | 模块名太长或冲突时 |

```python
import fibo as fib
fib.fib(500)

from fibo import fib as fibonacci
fibonacci(500)
```

> ⚠️ `from fibo import *` 在生产代码中强烈不推荐——会导致名称覆盖，代码难以理解。

---

## 3. 模块只被导入一次

每次解释器会话，每个模块只执行一次。修改模块后：

- 重启解释器（推荐）
- 或 `import importlib; importlib.reload(module)`（仅交互测试）

---

## 4. 脚本 vs 模块：`__name__` 的经典用法

```python
# fibo.py 末尾
if __name__ == "__main__":
    import sys
    fib(int(sys.argv[1]))
```

- **作为脚本运行**（`python fibo.py 50`）→ `__name__` = `"__main__"` → 执行 if 块
- **被 import 导入**（`import fibo`）→ `__name__` = `"fibo"` → 不执行 if 块

这是 Python 模块设计最优雅的模式之一：**一个文件既可当脚本用，也可被导入复用。**

---

## 5. 模块搜索路径 (`sys.path`)

当 `import spam` 时，解释器按以下顺序搜索：

1. **内置模块**（`sys.builtin_module_names`）
2. **`sys.path`** 中的目录，按顺序找 `spam.py`

`sys.path` 初始化来源：

| 优先级 | 来源 |
|--------|------|
| 1 | 被命令行直接运行的脚本所在目录 |
| 2 | `PYTHONPATH` 环境变量 |
| 3 | 安装默认路径（含 `site-packages`） |

```python
import sys
sys.path.append('/path/to/my/modules')  # 运行时添加搜索路径
```

> ⚠️ 脚本所在目录优先于标准库目录——别把自己的脚本命名为 `math.py`、`json.py`！

---

## 6. 编译缓存 `.pyc`

- Python 自动将模块编译版本缓存到 `__pycache__/` 目录
- 命名格式：`module.cpython-313.pyc`
- Python 自动对比源文件修改时间，过期则重新编译
- `.pyc` **只加快加载速度，不加快执行速度**
- `-O` 参数去除 assert，`-OO` 额外去除 `__doc__`

```
__pycache__/
  fibo.cpython-313.pyc       # Python 3.13 的编译缓存
  fibo.cpython-314.pyc       # Python 3.14 的编译缓存（共存）
```

---

## 7. `dir()` 函数：查看模块的命名空间

```python
import fibo
dir(fibo)                     # ['__name__', 'fib', 'fib2']

dir()                         # 列出当前命名空间所有名称

import builtins
dir(builtins)                 # 列出所有内置函数和异常
```

- `dir(module)` → 列出模块定义的所有名称（排序后）
- `dir()` → 无参数时列出当前作用域的所有名称
- 不列出内置名称；内置名称在 `builtins` 模块中

---

## 8. 包（Packages）

**包 = 用"点号模块名"构造的模块命名空间。** `A.B` 表示包 `A` 的子模块 `B`。

```
sound/                          # 顶层包
  __init__.py                   # 必须存在（namespace package 除外）
  formats/                      # 子包（文件格式转换）
    __init__.py
    wavread.py
    wavwrite.py
    ...
  effects/                      # 子包（音效）
    __init__.py
    echo.py
    surround.py
    ...
  filters/                      # 子包（过滤器）
    __init__.py
    equalizer.py
    ...
```

### 导入子模块的 3 种方式

```python
# 方式 1：全路径导入
import sound.effects.echo
sound.effects.echo.echofilter(input, output, delay=0.7, atten=4)

# 方式 2：from 子包 import 子模块（推荐）
from sound.effects import echo
echo.echofilter(input, output, delay=0.7, atten=4)

# 方式 3：直接导入函数
from sound.effects.echo import echofilter
echofilter(input, output, delay=0.7, atten=4)
```

> `from package import item` — item 可以是子模块、子包、或包中定义的任何名称（函数、类、变量）。`import item.subitem` 的语法要求除最后一项外，每项都是包。

---

## 9. `__init__.py` 与 `__all__`

**`__init__.py`**：必须存在才能让 Python 将目录当作包（namespace package 除外）。可以是空文件，也可以执行初始化代码。

**`__all__`**：控制 `from package import *` 的行为。

```python
# sound/effects/__init__.py
__all__ = ["echo", "surround", "reverse"]
```

- 定义了 `__all__` → `from sound.effects import *` 导入列表中指定的子模块
- 未定义 `__all__` → 只导入 `__init__.py` 中定义的名称 + 之前显式 import 加载过的模块

> ⚠️ `from package import *` 在生产代码中不推荐。推荐 `from package import specific_submodule`。

---

## 10. 相对导入

在包内部，用前导点号表示当前包和上级包：

```python
# sound/effects/surround.py 中
from . import echo               # 同级：sound/effects/echo.py
from .. import formats           # 上级：sound/formats/
from ..filters import equalizer  # sound/filters/equalizer.py
```

- `.` = 当前包，`..` = 上级包
- 相对导入基于 `__name__` 解析
- **主模块（直接运行的脚本）没有所属包 → 必须使用绝对导入**
- 主模块意味着 `__name__ == "__main__"`，此时相对导入会报错

---

## 11. 模块执行的私有关键点

- 模块有**独立的私有符号表**，模块内定义的函数把它当全局符号表
- 模块内使用全局变量不会与使用者的全局变量冲突
- 可以通过 `module.itemname` 访问模块的全局变量
- `import` 语句可以放在模块任何位置（惯例是放在开头）

---

## 速查：import 决策表

| 场景 | 推荐写法 |
|------|---------|
| 用整个模块 | `import package.module` |
| 用特定函数/类 | `from package.module import name` |
| 给模块起别名 | `import package.module as p` |
| 同包内引用 | `from . import sibling` |
| 同包内上级引用 | `from ..parent_pkg import module` |
| 主模块文件 | 只使用绝对导入 |
| 交互模式偷懒 | `from module import *`（只限交互模式） |
