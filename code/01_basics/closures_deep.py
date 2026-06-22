# 闭包深度解析 — 代码示例 (Python 3.12+)
from typing import Callable

# ============================================================
# 1. 闭包是什么：函数捕获了它"出生环境"中的自由变量
# ============================================================

def make_greeter(greeting: str) -> Callable[[str], str]:
    """greeting 是自由变量——既不是参数也不是局部变量，来自外层作用域"""
    def greet(name: str) -> str:
        return f"{greeting}, {name}!"
    return greet  # 返回时，greeting 的值被"封闭"在函数里

hello = make_greeter("Hello")
hi = make_greeter("Hi")
print(hello("Dean"))   # Hello, Dean!
print(hi("Dean"))      # Hi, Dean!
# hello 和 hi 各有自己的 greeting，互不影响

# ============================================================
# 2. 闭包的内部实现：__closure__ 和 cell 对象
# ============================================================

print(f"\n=== 闭包内部结构 ===")
print(f"闭包函数: {hello.__name__}")
print(f"捕获的自由变量: {hello.__code__.co_freevars}")   # ('greeting',)
print(f"__closure__: {hello.__closure__}")                # tuple of cell objects
print(f"cell 数量: {len(hello.__closure__)}")

# cell 对象是闭包存储"被捕获变量值"的地方
cell = hello.__closure__[0]
print(f"cell 内容: {cell.cell_contents}")  # 'Hello'

# 对比：普通函数没有 __closure__
def plain_func(x: int) -> int:
    return x + 1
print(f"\n普通函数 __closure__: {plain_func.__closure__}")    # None
print(f"普通函数 freevars: {plain_func.__code__.co_freevars}")  # ()

# ============================================================
# 3. nonlocal —— 闭包内修改外层变量的唯一方式
# ============================================================

def make_accumulator(start: int = 0):
    total = start  # 被捕获的自由变量
    def add(n: int) -> int:
        nonlocal total        # 没有这行会 UnboundLocalError
        total += n
        return total
    return add

acc = make_accumulator(10)
print(f"\n=== nonlocal 演示 ===")
print(acc(5))   # 15
print(acc(3))   # 18

# 如果没有 nonlocal：
def broken_counter():
    count = 0
    def inc():
        # count += 1  # 取消注释会报错：UnboundLocalError
        # 因为 count += 1 是 count = count + 1 的语法糖
        # Python 看到赋值 → 认为 count 是局部变量 → 右边 count 未定义
        return count  # 只读可以，不需要 nonlocal
    return inc

# ============================================================
# 4. 经典陷阱：循环中的闭包 —— 所有闭包共享同一个变量名
# ============================================================

print(f"\n=== 循环闭包陷阱 ===")

# 陷阱版
funcs = []
for i in range(3):
    funcs.append(lambda: i)  # 所有 lambda 捕获的都是同一个 i
print(f"陷阱: {[f() for f in funcs]}")  # [2, 2, 2]

# 本质：循环变量 i 是同一个名字，每次迭代只是改了它的值
# 闭包捕获的是"名字"（cell），不是"当时的值"
# 当 lambda 被调用时，i 已经是 2 了

# 修复 1：默认参数"冻结"（推荐）
funcs = [lambda i=i: i for i in range(3)]
print(f"修复1: {[f() for f in funcs]}")   # [0, 1, 2]

# 修复 2：工厂函数隔一层
def make_printer(val: int):
    return lambda: val   # val 是工厂函数的局部变量，每次调用独立

funcs = [make_printer(i) for i in range(3)]
print(f"修复2: {[f() for f in funcs]}")   # [0, 1, 2]

# ============================================================
# 5. 用闭包实现有状态的"轻量类"
# ============================================================

def make_stack():
    items: list = []           # 闭包持有的私有状态
    def push(item) -> None:
        items.append(item)
    def pop():
        return items.pop()
    def peek():
        return items[-1] if items else None
    def size() -> int:
        return len(items)
    # 返回一组闭包，共享同一个 items
    return push, pop, peek, size

push, pop, peek, size = make_stack()
print(f"\n=== 闭包实现的栈 ===")
push("a"); push("b"); push("c")
print(f"size: {size()}")     # 3
print(f"peek: {peek()}")     # c
print(f"pop: {pop()}")       # c
print(f"pop: {pop()}")       # b
print(f"size: {size()}")     # 1

# ============================================================
# 6. 闭包 vs 类 —— 状态封装，两种风格
# ============================================================

# 闭包版本：状态隐藏在 cell 里，纯函数接口
def make_counter_closure(start: int = 0):
    count = start
    def inc() -> int:
        nonlocal count
        count += 1
        return count
    def dec() -> int:
        nonlocal count
        count -= 1
        return count
    def reset() -> None:
        nonlocal count
        count = start
    return inc, dec, reset

inc, dec, reset = make_counter_closure(5)
print(f"\n=== 闭包 vs 类 ===")
print(f"闭包 inc: {inc()}")   # 6
print(f"闭包 dec: {dec()}")   # 5

# 类版本：等价的类实现
class Counter:
    def __init__(self, start: int = 0):
        self._count = start
    def inc(self) -> int:
        self._count += 1
        return self._count
    def dec(self) -> int:
        self._count -= 1
        return self._count

c = Counter(5)
print(f"类 inc: {c.inc()}")
print(f"类 dec: {c.dec()}")

# ============================================================
# 7. 运行时窥探：用 inspect 检查闭包
# ============================================================

def outer(msg: str, repeat: int):
    prefix = ">>> "
    def inner(name: str) -> str:
        return f"{prefix}{msg}, {name}!" * repeat
    return inner

f = outer("Hi", 2)
print(f"\n=== runtime 窥探 ===")
# 查看闭包捕获了哪些变量（从外到内）
if f.__closure__:
    freevars = f.__code__.co_freevars
    for var_name, cell in zip(freevars, f.__closure__):
        print(f"  {var_name} = {cell.cell_contents}")
# msg = Hi, prefix = >>> , repeat = 2

# ============================================================
# 8. 闭包就是带了"环境"的函数 —— 这才是关键
# ============================================================

# 同一个函数代码，不同环境 → 不同行为
def make_multiplier(factor: int):
    return lambda x: x * factor

double = make_multiplier(2)
triple = make_multiplier(3)

# 它们的代码一模一样
print(f"\n=== 相同代码，不同行为 ===")
print(f"double 的 code: {double.__code__}")
print(f"triple 的 code: {triple.__code__}")
print(f"代码相同: {double.__code__ is triple.__code__}")        # True
print(f"但闭包 cell 不同: {double.__closure__ is triple.__closure__}")  # False
print(f"double(5)={double(5)}, triple(5)={triple(5)}")

# 这个特性让闭包非常适合做：装饰器、回调注册、延迟求值、偏函数
