---
title: 闭包深度解析
order: 3.5
---

# 闭包深度解析

## 闭包的本质：函数 + 它的"出生环境"

**闭包（Closure）** = 一个函数，加上它定义时所在作用域中的**自由变量**（既不是参数也不是局部变量的名字）。

```python-run
def make_greeter(greeting):
    def greet(name):          # greet 是内层函数
        return f"{greeting}, {name}!"  # greeting 来自外层，是自由变量
    return greet

hello = make_greeter("Hello")
print(hello("Dean"))  # Hello, Dean!
```

`greeting` 不是 `greet` 的参数，也不是它的局部变量——它是 **自由变量（Free Variable）**。当 `greet` 被 `return` 出去时，`greeting` 的值被"打包"进函数，这个"函数 + 被捕获的变量"就是闭包。

> **一句话**：普通函数只看参数表做事；闭包函数还带着它出生时卧室墙上贴的那些便签。

---

## 闭包里面到底长什么样？

Python 把闭包捕获的变量存在 `__closure__` 属性里，每个变量封装在一个 **cell 对象**中：

```
hello
  └── __closure__ = (cell_greeting,)
       └── cell_greeting.cell_contents = "Hello"
```

用代码看：

```python-run
def outer(msg):
    def inner():
        return msg
    return inner

f = outer("hi")

print(f"自由变量名: {f.__code__.co_freevars}")  # ('msg',)
print(f"cell 数量:   {len(f.__closure__)}")      # 1
print(f"cell 内容:   {f.__closure__[0].cell_contents}")  # 'hi'
```

对比：一个不引用任何外层变量的普通函数，`__closure__` 是 `None`：

```python-run
def plain(x):
    return x + 1
print(plain.__closure__)  # None
```

### 关键洞察：闭包捕获的是"名字"（的 cell），不是"当时的值"

```python-run
funcs = []
for i in range(3):
    funcs.append(lambda: i)

print([f() for f in funcs])  # [2, 2, 2] — 为什么不是 [0, 1, 2]？！
```

原因：`for i in range(3)` 的 `i` 始终是**同一个变量名**，每次迭代只是改了它的值。所有 lambda 捕获的都是**同一个 cell**，存的是变量名 `i` 的当前值。lambda 被调用时（循环之后），`i` 的值已经是 2 了。

这在 JavaScript 中也有完全相同的问题（经典 `for(var i=0; ...)` 陷阱），而且因为 JS 的 `var` 没有块级作用域，后果更严重。

**三种修复方法：**

```python-run
# 方法 1：默认参数"冻结"（最 Pythonic）
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])  # [0, 1, 2]

# 方法 2：工厂函数隔一层
def capture(x):
    return lambda: x        # x 是 capture 的局部变量，每次调用独立
funcs = [capture(i) for i in range(3)]
print([f() for f in funcs])  # [0, 1, 2]

# 方法 3：functools.partial
from functools import partial
funcs = [partial(lambda x: x, i) for i in range(3)]

# 方法 4 (Python 3.12+)：itertools.batched / 直接用生成器
```

> 核心：每次循环都要"创造一个新的作用域 + 新的变量"来保存当前值。默认参数在**定义时**求值，所以 `i=i` 可以"快照"当前值。

---

## `nonlocal` —— 给闭包"修改权"

闭包默认只能**读**外层变量。如果要**写**，必须用 `nonlocal`：

```python-run
def make_counter(start=0):
    count = start
    def inc():
        nonlocal count   # 没有这行 → UnboundLocalError
        count += 1       # count = count + 1 触发赋值 → Python 认为 count 是局部变量
        return count
    return inc

c = make_counter()
print(c())  # 1
print(c())  # 2
```

**为什么会 `UnboundLocalError`？**

Python 的规则：函数内**只要出现赋值语句**，这个名字就被标记为"局部变量"。`count += 1` 等价于 `count = count + 1`——Python 看到 `=`，把 `count` 当作局部变量，但右边的 `count` 还没定义，于是报错。`nonlocal count` 告诉 Python：别猜了，count 在外层 Enclosing 作用域。

---

## 闭包 vs 类：Python 中的两种状态封装

同一件事，两种写法：

```python-run
# 闭包版本：状态藏在 cell 里
def make_stack():
    items = []
    def push(x): items.append(x)
    def pop():   return items.pop()
    return push, pop  # 只有函数暴露，items 完全隐藏

push, pop = make_stack()
push(1); push(2)
print(pop())  # 2

# 类版本：状态在 self 上（可被访问和修改）
class Stack:
    def __init__(self):
        self._items = []
    def push(self, x): self._items.append(x)

s = Stack()
s.push(1)
print(s._items)  # 可以直接绕过 API 访问！闭包做不到这一点
```

| | 闭包 | 类 |
|--|------|-----|
| 状态隐藏 | **强**——cell 不可从外部访问 | 弱——属性约定 `_prefix` 但可绕过 |
| 接口灵活性 | 弱——固定返回哪些函数 | **强**——可以动态增删方法 |
| 内存 | 轻——每个闭包一个 cell tuple | 重——每个实例一个 `__dict__` |
| 适合场景 | 装饰器、回调、单状态工厂 | 多状态 + 多方法 + 继承 |

---

## Python 闭包 vs JavaScript 闭包

你说得对——Python 闭包**确实**比 JS 简单，原因：

| Python 没有的坑 | JS 里为什么是坑 |
|-----------------|----------------|
| **没有 `var` 提升（hoisting）** | JS: `var x = 1; function f() { console.log(x); var x = 2; }` 输出 `undefined` |
| **没有 `this` 动态绑定** | JS: 闭包里的 `this` 指向调用者，不是定义者 → 需要 `bind()` / 箭头函数 |
| **块级作用域天然存在** | Python 的函数/模块作用域一开始就是块级，不需要 `let` 来修 |
| **没有"闭包内存泄漏"恐慌** | JS 早期的 DOM 循环引用导致 IE 泄漏，Python 有 GC 兜底 |
| **显式声明修改权（nonlocal）** | JS 直接改外层变量，不声明——更容易无意修改 |
| **没有原型链干扰** | JS: `obj.method` 可能来自原型，闭包可能兜住意外的值 |

**Python 闭包更"安静"的原因**：Python 的作用域模型从 1.0 就是 LEGB，几乎没有历史包袱。JS 的 `var`、`this`、原型链都不是为闭包设计的，闭包是后来"捡来"的能力。

---

## 闭包在哪里用？

```python-run
# 1. 装饰器（第 3.2 章详解）
def logger(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper  # wrapper 闭包捕获了 func

# 2. 延迟求值 / 回调注册
handlers = {}
def register(name):
    def handler():
        return f"处理 {name}"
    handlers[name] = handler

# 3. functools.partial 的底层就是闭包
from functools import partial
# partial 内部用闭包存储被绑定的参数

# 4. 生成"配置好的"函数族
def power(exponent):
    return lambda base: base ** exponent  # 闭包捕获 exponent

square = power(2)
cube = power(3)
print(square(5), cube(5))  # 25, 125 — 同一个 lambda 代码，不同环境
```

---

## 总结：闭包的三个本质问题

1. **是什么**：函数 + 被捕获的自由变量（存在 `__closure__` 的 cell 里）
2. **为什么需要**：让函数"记住"创建时的上下文，不用每次传参。这是装饰器、回调、工厂函数的基石
3. **怎么用对**：循环中用默认参数"冻结"值；需要改外层变量时加 `nonlocal`；别滥用闭包替代类——状态多于 2-3 个时考虑用类

> 📖 **官方文档**：[Naming and Binding](https://docs.python.org/3/reference/executionmodel.html#naming-and-binding), [Data Model: `__closure__`](https://docs.python.org/3/reference/datamodel.html#index-35), [PEP 3104 — nonlocal](https://peps.python.org/pep-3104/)

---

## 本章小结

- 闭包 = 函数 + 它出生环境中被捕获的自由变量（存于 `__closure__` 的 cell 对象中）
- 闭包捕获的是变量名（的 cell），不是当时的值——循环中创建闭包因"延迟绑定"导致所有闭包共享最终值
- 修复循环中的延迟绑定：默认参数"冻结"（`lambda i=i: i`）、工厂函数隔层、`functools.partial`
- `nonlocal` 给闭包写入外层变量的权限；没有 `nonlocal`，赋值操作会让 Python 把该名字标记为局部变量
- 闭包适合轻量状态封装（装饰器、回调），状态超过 2-3 个或需要继承时考虑用类

---

## 思考题

1. 运行这段代码，输出什么？为什么？`funcs = [(lambda: i) for i in range(5)]; print([f() for f in funcs])`
2. 闭包的 `__closure__` 属性什么时候是 `None`？至少找出两种场景。
3. Python 闭包为什么比 JS 闭包简单？根源是 Python 没有哪两个 JS 特性？
4. 用闭包实现一个 `once(fn)` 函数，保证 `fn` 只被调用一次，重复调用返回首次结果。
