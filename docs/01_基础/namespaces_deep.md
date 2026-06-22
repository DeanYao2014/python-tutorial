---
title: 命名空间深度解析
order: 3.3
---

# 命名空间深度解析

本章回答 Python 中最容易被忽略的三个问题：**什么是命名空间（Namespace）**、**变量和属性有什么区别**、**为什么 `obj.x` 和 `x` 走的是完全不同的查找路径**。



## 命名空间 = 名字 → 对象的字典

**命名空间（Namespace）**是名字到对象的映射。Python 里到处都是命名空间：

```python-run
# 1. 模块的命名空间 —— globals()
import math
print(type(globals()))  # <class 'dict'>

# 2. 对象的命名空间 —— __dict__
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

p = Point(1, 2)
print(p.__dict__)       # {'x': 1, 'y': 2}

# 3. 类的命名空间
print(Point.__dict__.keys())  # 包含 __init__, __module__ 等

# 4. 内置命名空间 —— builtins
import builtins
print(type(builtins))   # <class 'module'>
```

> 命名空间的本质就是**字典**——一个名字对应于一个对象。`globals()` 是模块的命名空间字典，`__dict__` 是对象的命名空间字典。

但别搞混：**命名空间是抽象概念，字典是实现方式**。不是所有命名空间都能直接拿到字典——`locals()` 在函数内部返回的是快照拷贝，不能修改。

---

## 两类命名空间：作用域 vs 对象

Python 有两种根本不同的命名空间，对应两种根本不同的`名字查找机制`(也就是读取的时候的查找顺序)：

:::tip 属性赋值 vs 属性访问
python的属性访问和属性赋值, 命名空间的操作是略有不同的
如果是赋值操作, 永远操作的是自己的命名空间;
比如`self.x = 100` 就是绑定在实例对象的`__dict__` 中,不会去类中的__dict__查找 ,给类的x的值,这和访问属性不同;
属性访问的话,如果变量没有找到self.x 就回去类的__dict__中查找;

如果x是类的描述符, 赋值优先走set方法;
:::


```
命名空间
├── 作用域命名空间（Scope Namespace）
│   ├── Built-in    —— builtins 模块
│   ├── Global      —— 每个模块的 globals()
│   ├── Local       —— 每次函数调用的帧
│   └── Enclosing   —— 外层函数的 cell 对象
│
└── 对象命名空间（Object Namespace）
    ├── 实例 __dict__
    ├── 类 __dict__
    └── 父类 __dict__（沿 MRO）
```

| | 作用域命名空间 | 对象命名空间 |
|--|-------------|-----------|
| **访问方式** | 裸名字：`x`、`print`、`math` | 点号：`obj.x`、`self.name` |
| **查找机制** | **LEGB 静态链** | **描述符协议 + `__dict__` + MRO** |
| **创建方式** | 赋值语句、`import`、`def`、`for` | `obj.attr = value`、`setattr()` |
| **何时确定** | 编译阶段确定名字归属作用域 | 运行时动态查找 |
| **性能** | `LOAD_FAST`/`LOAD_GLOBAL` 字节码，极快 | 描述符解析 + 字典查找，略慢 |

---

## 变量 = 在作用域命名空间中查找

当你写一个**裸名字**（bare name）时，Python 走 LEGB：

```python-run
import dis

x = 10        # Global 命名空间
def f():
    y = 20    # Local 命名空间
    print(x + y)

# 看字节码：x 是 LOAD_GLOBAL，y 是 LOAD_FAST
dis.dis(f)
```

`LOAD_GLOBAL` 查 `globals()` 字典，`LOAD_FAST` 直接读帧的局部变量数组。**不需要 `__dict__`，不走描述符协议**——这就是"变量查找"。

## 属性 = 在对象命名空间中查找

当你写 `obj.x` 时，Python 走的是完全不同的路径：

```
obj.x
  → type(obj).__getattribute__(obj, 'x')
    → 1. 在 type(obj).__mro__ 中找"数据描述符"（有 __set__ 的）
        找到 → 调用 desc.__get__(obj, type(obj))
    → 2. 在 obj.__dict__ 中找
        找到 → 返回 obj.__dict__['x']
    → 3. 在 type(obj).__mro__ 中找"非数据描述符"（只有 __get__ 的）
        找到 → 调用 desc.__get__(obj, type(obj))
    → 4. 在 type(obj).__mro__ 的 __dict__ 中找普通值
    → 5. 触发 __getattr__（如果定义了）
    → 6. 都没有 → AttributeError
```

```python-run
class Person:
    species = "Homo sapiens"  # 类属性：在 Person.__dict__ 中

    def __init__(self, name):
        self.name = name      # 实例属性：在 p.__dict__ 中

p = Person("Alice")

# 实例属性查找
print(p.name)       # Alice —— 找到 p.__dict__['name']

# 类属性查找（实例上找不到，沿 MRO 到类）
print(p.species)    # Homo sapiens —— 找到 Person.__dict__['species']

# 验证
print("name" in p.__dict__)          # True
print("species" in p.__dict__)       # False
print("species" in Person.__dict__)  # True
```

---

## 变量 vs 属性：并排对比

这是整个章节的核心——把它们放在一起，区别一目了然：

```python-run
# ============ 变量 ============
# 裸名字，无点号，走 LEGB

name = "全球变量"        # 在 globals() 中创建条目

def test_variable():
    name = "局部变量"    # 在函数帧的 locals 中创建条目
    print(name)         # 查找：先找 Local，找到，返回 "局部变量"
    print(len)          # 查找：L→E→G 都没有，Built-in 找到 <built-in function len>

test_variable()

# ============ 属性 ============
# 点号访问，走 object.__getattribute__()

class Scope:
    name = "类属性"     # 在 Scope.__dict__ 中

obj = Scope()
obj.name = "实例属性"   # 在 obj.__dict__ 中

print(obj.name)         # 查找：先在 obj.__dict__ 找到 "实例属性"
del obj.name
print(obj.name)         # 查找：obj.__dict__ 没有，沿 MRO 到 Scope.__dict__
```

### 关键差异一：赋值行为不同

```python-run
# 变量赋值：在当前作用域的命名空间中创建名字
x = 1       # 在 globals() 中创建 'x' → 1
def f():
    x = 2   # 在函数的局部命名空间中创建 'x' → 2，完全不碰外层 x
    print(x)
f()
print(x)    # 1 —— 外层的 x 没受影响

# 属性赋值：在对象的 __dict__ 中创建名字
class Demo:
    pass

d = Demo()
d.x = 1     # d.__dict__['x'] = 1 —— 只在 d 上
d2 = Demo()
# d2.x      # AttributeError —— d2 没有 x
```

> **变量赋值是"在作用域里登记名字"**，`x = 1` 表示"把当前作用域的 `x` 指向 1"。**属性赋值是"在对象上挂载数据"**，`obj.x = 1` 表示"把 `obj` 的 `__dict__['x']` 设为 1"。两者互不相干。

### 关键差异二：作用域声明不适用于属性

```python-run
x = 0

class Counter:
    x = 0     # 这是类属性，在 Counter.__dict__ 中！

    def increment(self):
        # global x     # 这是声明"我用的是模块级的 x"
        # nonlocal x   # 错误！nonlocal 只能用于 Enclosing 函数
        self.x += 1    # self.x 是属性访问，不是变量！

c = Counter()
c.increment()
print(c.x)      # 1
print(Counter.x)  # 0 —— 类属性没变
print(x)         # 0 —— 全局变量没变
```

> `global`/`nonlocal` 只能声明裸名字的作用域。`self.x` 是属性访问——前面有点号，走完全不同的通道。

### 关键差异三：查找失败的行为不同

```python-run
# 变量查找失败 → NameError（编译阶段就能部分检测）
# print(undefined_var)  # NameError: name 'undefined_var' is not defined

# 属性查找失败 → AttributeError（纯运行时）
class Empty:
    pass

e = Empty()
try:
    print(e.undefined_attr)
except AttributeError as ex:
    print(f"AttributeError: {ex}")
```

---

## `vars()` / `dir()` / `__dict__` 的区别

这三个都跟命名空间有关，但各有用途：

| 函数 | 返回什么 | 适用场景 |
|------|---------|---------|
| `vars(obj)` | `obj.__dict__` | 查看实例属性 |
| `vars()` | `locals()`（当前作用域） | 查看局部变量 |
| `dir(obj)` | 属性名列表（整合了 `__dict__` + MRO + `__dir__`） | IDE 自动补全、探索对象 |
| `obj.__dict__` | 实例属性的原始字典 | 直接读写 |

```python-run
class Dog:
    species = "Canis"

    def __init__(self, name):
        self.name = name

d = Dog("Buddy")

print("vars(d):", vars(d))          # {'name': 'Buddy'} —— 仅实例属性
print("dir(d):", [a for a in dir(d) if not a.startswith('_')])
# ['name', 'species'] —— 实例 + 类 + 继承的属性

print("Dog.__dict__:", list(Dog.__dict__.keys())[:4])  # 类的命名空间
```

---

## 实战：看懂 `self` 

`self` 本身就是对"变量 vs 属性"最好的解释：

```python-run
class BankAccount:
    min_balance = 0     # ① 在 BankAccount.__dict__ 中

    def __init__(self, owner, balance):
        self.owner = owner     # ② self.owner → 属性查找 → self.__dict__['owner']
        self.balance = balance # ③ self.balance → 属性查找 → self.__dict__['balance']

    def deposit(self, amount):
        # ④ amount → 变量（LEGB），在 Local 作用域找到
        # ⑤ self.balance → 属性，在 self.__dict__ 找到
        # ⑥ min_balance → 变量？！不是属性！
        self.balance += amount

a = BankAccount("Alice", 100)
a.deposit(50)
print(a.balance)  # 150
```

关键点：`amount` 是变量（LEGB → Local），`self.balance` 是属性（`self.__dict__['balance']`）。`self` 本身也是变量——在 LEGB 的 Local 作用域中。

---

> 📖 **官方文档**：[Naming and Binding](https://docs.python.org/3/reference/executionmodel.html#naming-and-binding), [Scopes and Namespaces](https://docs.python.org/3/tutorial/classes.html#python-scopes-and-namespaces), [Data Model: `__dict__`](https://docs.python.org/3/reference/datamodel.html#the-standard-type-hierarchy), [Customizing Attribute Access](https://docs.python.org/3/reference/datamodel.html#customizing-attribute-access)

---

## 本章小结

- 命名空间是名字到对象的映射——作用域命名空间（LEGB）存变量，对象命名空间（`__dict__`）存属性
- **变量** = 裸名字，查找走 LEGB静态链（编译阶段确定归属作用域），找不到报 `NameError`
- **属性** = `obj.name`，查找走 `__getattribute__` → 描述符协议 → `__dict__` → MRO 链（纯运行时），找不到报 `AttributeError`
- `global`/`nonlocal` 只对变量有效——属性赋值 `obj.x = 1` 永远在对象上，不需要声明
- `vars(obj)` 返回 `obj.__dict__`，`vars()` 等价于 `locals()`；`dir(obj)` 整合了实例 + 类 + 继承的属性

---

## 思考题

1. 下面代码中，哪些名字是变量？哪些是属性？
   ```python
   multiplier = 2
   class Calculator:
       factor = 10
       def compute(self, x):
           return x * self.factor * multiplier
   ```

2. `self.x = 1` 和 `x = 1` 分别发生在哪个命名空间？它们各自走的查找路径是什么？
:::tip 回答
这两个都是赋值操作: 

x = 1 函数作用域命名LEGB规则,直接在当前函数栈创建一个局部变量x
self.x = 1 : 对象属性的命名空间规则,赋值操作直接在self的__dict__命名空间中赋值;
:::

3. 为什么 `nonlocal x` 可以在闭包里声明外层函数的变量，但 `nonlocal self.x` 是语法错误？
:::tip 回答
nonlocal 主要修饰作用域变量 ,无法修改对象属性,让x指向当前函数的外层作用域变量,遵循LEGB变量查找规则;
self.x: (self其实是个变量), 但self.x是属性访问,遵循对象属性的命名空间查找规则
两者是两个完全不通过的东西 ,不能混写;
:::
1. `vars(obj)` 和 `dir(obj)` 返回的结果有什么本质区别？为什么 `dir(obj)` 比 `vars(obj)` 条目多？
:::tip 回答
var(obj) = 直接返回obj.__dict__, 只显示你手动绑定的属性
dir(obj) = 完整的属性查找链条(实例,类+父类,系统内置), 显示所有您能访问到的属性;

:::