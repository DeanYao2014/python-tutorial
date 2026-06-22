---
title: 装饰器深度解析
order: 5.5
---

# 装饰器深度解析

## 目标

1. 装饰器的定义和本质, 函数装饰器是闭包, 类装饰器是类装饰器接受func初始化__init__(func), 调用就是__call__(*args,**kwargs) 
2. 保留func的原始信息 `@functools.wraps` ; `functools.update_wrapper(self, func)` 
3. 参数装饰器: 最外层接受参数, 第二层是装饰器接受函数 ,第三层是func; 
4. 洋葱模型: 从下往上装饰, 从上往下执行

## 装饰器就是语法糖——闭包的第一个应用

装饰器的本质: 它是一个高阶函数(或可调用对象), 他接受一个可调用对象(callable)函数/类作为输入, 并返回一个新得可调用对象作为输出, 从而在不修改原对象源码的情况下, 动态的扩展或改变他的行为
> A function returning another function, usually applied as a function transformation using the @wrapper syntax. Common examples for decorators are classmethod() and staticmethod(). 


> The decorator syntax is merely syntactic sugar

> `@decorator` →  `原函数 = decorator(原函数)`

```python-run
@timer
def slow_add(a, b):
    time.sleep(0.5)
    return a + b
```

等价于：

```python
slow_add = timer(slow_add)
```

**装饰发生在函数定义时**，不是在调用时。装饰器接收函数、返回函数——通常返回一个**闭包**，这个闭包捕获了原函数。

> 装饰器能工作的前提就是闭包。没有闭包，`wrapper` 拿不到 `func`。

---

## 最简装饰器 → 真正的装饰器

```python-run
# 什么都不做的装饰器
def identity(func):
    return func

# 真正的装饰器：返回一个闭包替换原函数
def announce(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper   # ← 闭包：wrapper 捕获了 func

@announce
def greet(name):
    return f"Hello, {name}"

print(greet("Dean"))  # 先打印，再返回结果
```

这里 `wrapper` 是一个闭包，`func` 是它的自由变量。装饰器本质上就是**把原函数包裹进一个新闭包里**。

---

## `@functools.wraps` —— 为什么必须加

```python-run
import functools

def without_wraps(func):
    def wrapper(*args, **kwargs):
        """wrapper 的文档"""
        return func(*args, **kwargs)
    return wrapper

def with_wraps(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        """wrapper 的文档"""
        return func(*args, **kwargs)
    return wrapper

@without_wraps
def foo():
    """foo 的文档"""
    pass

@with_wraps
def bar():
    """bar 的文档"""
    pass

print(f"不加 @wraps: name={foo.__name__}, doc={foo.__doc__}")
print(f"加了 @wraps: name={bar.__name__}, doc={bar.__doc__}")
```

不加 `@wraps`，被装饰函数的 `__name__`、`__doc__`、`__module__` 都会变成 wrapper 的值。这对：

- **调试**（traceback 里看到的函数名）
- **文档生成**（Sphinx 等读 `__doc__`）
- **IDE 智能提示**
- **`inspect.signature()`** 获取参数签名

都是灾难。

> **`@wraps` 本身也是一个装饰器**——它用 `functools.update_wrapper()` 把 `func` 的元数据复制到 `wrapper` 上。

### @wraps 做不到的事

`@wraps` 复制元数据，但**不复制参数签名**。类型检查器（mypy/pyright）需要额外帮助。Python 3.10+ 引入 `ParamSpec` 解决这个问题：

```python
from typing import ParamSpec, TypeVar, Callable

P = ParamSpec("P")
R = TypeVar("R")

def log(func: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper
```

`ParamSpec` 让类型检查器能"看穿"装饰器，知道返回的函数和原函数有**完全相同的参数类型**。

---

## 参数化装饰器：三层函数

```python-run
def retry(times=3, delay=1.0):
    """最外层：接收装饰器的"配置参数" """
    def decorator(func):
        """中间层：这就是标准的装饰器 """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """最内层：替换原函数的新函数 """
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if i == times - 1:
                        raise
                    print(f"重试 {i+1}/{times}...")
                    time.sleep(delay)
        return wrapper
    return decorator
```

`@retry(times=3, delay=0.5)` 的执行流程：

```
retry(times=3, delay=0.5)     →  返回 decorator
decorator(flaky_func)         →  返回 wrapper
                                wrapper 替换 flaky_func
```

**三层的原因**：装饰器本身只能接收一个参数（被装饰的函数）。要传额外参数，必须在外面再包一层——这层返回真正的装饰器。

> **记忆法**：装饰器有几层括号，就是几层函数嵌套。`@deco` — 两层；`@deco(args)` — 三层。

---

## 类装饰器：用 `__call__` 替代闭包

当装饰器需要维护复杂状态时，类比闭包更清晰：
> `@MyDecorator`  →  `原函数 = MyDecorator(原函数)`
> 
```python-run
'''
定义 say_hello 并加上装饰器的那一刻，Python 就自动用原函数作为参数，实例化了这个装饰器类（触发了 __init__），并把生成的实例对象重新赋值给了 say_hello 这个名字。

'''
import functools


class MyDecorator:
  def __init__(self, func):
    '''接受一个函数'''
    # @functools.wraps(func) 函数装饰器中使用
    # 保留func的原始信息
    functools.update_wrapper(self, func)
    self.func = func
    self.name = func.__name__ # 保留函数名
    print(f'装饰器初始化完成, 接管了函数{func.__name__},/n被装饰器的装饰的函数,实际上已经是一个装饰器的实例了,MyDecorator(func)')

  def __call__(self, *args,**kwargs):
    print('调用被装饰器装饰的函数, 会执行__call__, 被装饰器装饰的函数,实际上已经是一个装饰器实例')
    return self.func(*args, **kwargs) # 返回函数的结果


# say_hello = MyDecorator(say_hello) 
@MyDecorator
def say_hello(name):
  return f"你好, {name}!"

# @MyDecorator →  MyDecorator(say_hello) → __init__(self,say_hello)
print(f'现在的say_hello的类型: {type(say_hello)}') # <class '__main__.MyDecorator'>

# 调用函数say_hello('dean') → __call__(self, 'dean') → 调用原函数self.func('dean')
result = say_hello('dean')
print(result)


```

```python-run
class CountCalls:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"第 {self.count} 次调用")
        return self.func(*args, **kwargs)

@CountCalls
def process():
    return "done"

process()  # 第 1 次
process()  # 第 2 次
print(process.count)  # 2 — 状态存在实例属性上，自在
```

| | 闭包装饰器 | 类装饰器 |
|--|----------|---------|
| 状态存储 | cell 对象（隐藏） | 实例属性（可访问） |
| 代码量 | 少 | 稍多但结构清楚 |
| 适合场景 | 简单逻辑 | 多状态、需要对外暴露方法 |
| 典型用例 | `@timer`、`@log` | `@CountCalls`、带配置的复杂装饰器 |

---

## 装饰器叠加：洋葱模型

```python-run
@bold     # 第二步执行
@italic   # 第一步执行
def text():
    return "Hi"

print(text())  # <b><i>Hi</i></b>
```

执行顺序：**从下往上装饰，从上往下执行**。

```
装饰时（定义时）：italic(text) → italic_wrapper
                 bold(italic_wrapper) → bold_wrapper

调用时：bold_wrapper → italic_wrapper → 原 text → italic 包裹 → bold 包裹
```

可以记成：**"洋葱从里往外剥，装饰从下往上穿"**。

---

## 常见装饰器模式

### 1. 计时（最常用）

```python-run
import time, functools

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        t = time.perf_counter()
        r = func(*args, **kwargs)
        print(f"{func.__name__}: {time.perf_counter()-t:.6f}s")
        return r
    return wrapper
```

### 2. 缓存（手动 lru_cache 简化版）

```python-run
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@memoize
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)

print(fib(30))  # 不带缓存永远算不完，带缓存瞬间出结果
```

### 3. 注册表（Flask 路由的底层）

```python-run
routes = {}

def route(path):
    def decorator(func):
        routes[path] = func   # 注册，不修改原函数
        return func           # 原样返回
    return decorator

@route("/home")
def home(): return "首页"

print(routes)  # {'/home': <function home>}
```

### 4. 前置/后置钩子

```python
def with_hooks(before=None, after=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if before: before()
            result = func(*args, **kwargs)
            if after: after()
            return result
        return wrapper
    return decorator
```

---

## 装饰器的设计哲学

装饰器是 Python 对 **AOP（面向切面编程）** 最自然的表达：

| AOP 概念 | Python 表达 |
|----------|-----------|
| 切面（Aspect） | 装饰器函数 |
| 切入点（Pointcut） | `@decorator` 标注 |
| 通知（Advice） | wrapper 中的前置/后置代码 |
| 织入（Weaving） | 装饰器叠加的洋葱模型 |

> Python 不需要 XML 配置文件、不需要编译期字节码注入——装饰器就是 AOP，而且更简单。

`@staticmethod`、`@classmethod`、`@property`、`@dataclass`、`@functools.lru_cache`……Python 标准库自己就是装饰器最忠实的用户。

---

## 装饰器 vs 上下文管理器

| | 装饰器 | 上下文管理器 |
|--|--------|------------|
| 作用范围 | **每次函数调用** | **一段代码块** |
| 典型场景 | 计时、日志、权限、缓存 | 文件、锁、数据库事务 |
| 语法 | `@decorator` | `with` 语句 |
| 可组合性 | 叠加多个 `@` | 嵌套 `with` 或 `ExitStack` |

> **经验法则**：如果在很多函数里都要做同样的事，用装饰器。如果只是某一段代码需要准备和清理资源，用 `with`。

> 📖 **官方文档**：[Function Definitions — Decorators](https://docs.python.org/3/reference/compound_stmts.html#function-definitions), [functools.wraps](https://docs.python.org/3/library/functools.html#functools.wraps), [PEP 318 — Decorators](https://peps.python.org/pep-0318/), [PEP 612 — ParamSpec](https://peps.python.org/pep-0612/)

---

## 本章小结

- 装饰器是语法糖：`@deco` 等价于 `func = deco(func)`；装饰发生在**定义时**，不是在调用时
- 装饰器本质是闭包的应用——wrapper 捕获原函数，在不修改原函数代码的前提下增加新行为
- `@functools.wraps` 必须加——否则被装饰函数的 `__name__`、`__doc__`、签名全部丢失；`ParamSpec` 进一步保证类型安全
- 参数化装饰器需要三层：外层收配置参数 → 中层是标准装饰器 → 内层是替换函数
- 装饰器叠加是洋葱模型：从下往上装饰，从上往下调用；装饰器是 Python 对面向切面编程（AOP）最自然的表达

---

## 思考题

1. 不使用 `@` 语法，用原始写法重写 `@retry(times=3) def f(): pass`。为什么参数化装饰器需要三层？
2. `@wraps` 复制了哪些属性？哪些东西它**没复制**？为什么 `ParamSpec` 是必要的？
3. 写一个 `@once` 装饰器：被装饰的函数无论调用多少次，只执行第一次，重复调用返回缓存结果。这个装饰器需要闭包还是类更合适？为什么？
4. 下面两个写法有什么区别？`@bold @italic def f()` 和 `@italic @bold def f()`
