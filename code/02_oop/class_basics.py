"""2.1 类与元类的基础 —— 代码示例合集

每个示例独立可运行，展示 Python 3.11+ 下的核心机制。
"""

import types
from typing import Any


# ============================================================
# 1. type(name, bases, namespace) —— 动态创建类
# ============================================================

def demo_type_create():
    """演示 type() 的三参数形式动态创建类"""

    # class 关键字背后：Python 执行类体，收集命名空间，调用 type()
    Dog = type('Dog', (), {
        'sound': '汪汪',
        'bark': lambda self: f"{self.sound}!",
        '__repr__': lambda self: f"Dog(sound={self.sound!r})",
    })

    d = Dog()
    print(f"动态创建的类: {d}")               # Dog(sound='汪汪')
    print(f"bark(): {d.bark()}")             # 汪汪!
    print(f"类型: {type(Dog)}")              # <class 'type'>
    print(f"是 type 的实例: {isinstance(Dog, type)}")  # True

    # 带继承的动态创建
    class Animal:
        species = "未知"

        def describe(self):
            return f"物种: {self.species}"

    Cat = type('Cat', (Animal,), {
        'species': '猫',
        'sound': '喵',
    })

    c = Cat()
    print(f"\n继承的类: {c.describe()}")      # 物种: 猫
    print(f"MRO: {[cls.__name__ for cls in Cat.__mro__]}")


# ============================================================
# 2. __new__ vs __init__ —— 创建 vs 初始化
# ============================================================

def demo_new_vs_init():
    """对比 __new__ 与 __init__ 的调用时机和分工"""

    class Tracker:
        """追踪对象创建全流程"""
        def __new__(cls, *args, **kwargs):
            print(f"  __new__({cls.__name__}, args={args}, kwargs={kwargs})")
            instance = super().__new__(cls)
            # 在 __new__ 中 instance 还没有任何通过 __init__ 设置的属性
            print(f"  __new__ 返回前: hasattr(instance, 'name') = {hasattr(instance, 'name')}")
            return instance

        def __init__(self, name):
            print(f"  __init__(self={self}, name={name!r})")
            self.name = name
            print(f"  __init__ 后: self.name = {self.name!r}")

    print("创建 Tracker('Alice'):")
    t = Tracker("Alice")

    # __new__ 返回了其他类型会怎样？
    class Another:
        pass

    class Traitor:
        """__new__ 返回了别的类的实例"""
        def __new__(cls):
            print("  __new__ 返回 Another 的实例，跳过 __init__")
            return Another()  # 不返回 Traitor 实例

        def __init__(self):
            print("  这句话永远不会打印")

    print("\n创建 Traitor():")
    traitor = Traitor()
    print(f"  type(traitor) = {type(traitor).__name__}")  # Another
    print(f"  isinstance(traitor, Traitor) = {isinstance(traitor, Traitor)}")  # False


# ============================================================
# 3. __new__ 的典型应用：不可变类型子类化
# ============================================================

def demo_new_immutable():
    """子类化不可变类型（str、int、tuple）必须重写 __new__"""

    class UpperStr(str):
        """自动转为大写的字符串"""
        def __new__(cls, value):
            return super().__new__(cls, str(value).upper())

        def __add__(self, other):
            # 保持返回 UpperStr 类型
            return type(self)(super().__add__(str(other)))

    s = UpperStr("hello world")
    print(f"UpperStr('hello world') = {s!r}")  # 'HELLO WORLD'
    print(f"type(s) = {type(s).__name__}")     # UpperStr

    # 比较：用 __init__ 试图做同样的事情——无效
    class BrokenStr(str):
        def __init__(self, value):
            # 没用！str 的值在 __new__ 中已经确定了
            value = value.upper()

    b = BrokenStr("hello world")
    print(f"BrokenStr('hello world') = {b!r}")  # 'hello world' ← 大写失败！

    # 带验证的整数类型
    class PositiveInt(int):
        """正整数——在 __new__ 中校验"""
        def __new__(cls, value):
            value = int(value)
            if value < 0:
                raise ValueError(f"期望正数，得到 {value}")
            # 故意不调用 super().__new__，创建普通 int 也可以
            return super().__new__(cls, value)

    try:
        n = PositiveInt(-5)
    except ValueError as e:
        print(f"PositiveInt(-5) 被拒绝: {e}")

    n = PositiveInt(42)
    print(f"PositiveInt(42) = {n}, type = {type(n).__name__}")


# ============================================================
# 4. Singleton —— __new__ 的另一个经典用法
# ============================================================

def demo_singleton():
    """用 __new__ 实现单例模式"""

    class Singleton:
        _instance: 'Singleton | None' = None
        _initialized: bool = False

        def __new__(cls, *args, **kwargs):
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

        def __init__(self, name: str = ""):
            # 注意：__init__ 每次调用都会被触发，即使实例已存在
            if not self._initialized:
                self.name = name
                type(self)._initialized = True
                print(f"  Singleton 初始化: name={self.name!r}")
            else:
                print(f"  Singleton 已存在，忽略 name={name!r}")

    a = Singleton("first")
    b = Singleton("second")
    c = Singleton()

    print(f"  a is b: {a is b}")         # True
    print(f"  a.name: {a.name!r}")       # 'first' —— 没有被覆盖
    print(f"  b.name: {b.name!r}")       # 'first'


# ============================================================
# 5. 元类 __call__ —— 类实例化的真正入口
# ============================================================

def demo_metaclass_call():
    """展示元类的 __call__ 如何控制实例化"""

    class LoggingMeta(type):
        """记录每一次实例化"""
        _instance_count: dict[str, int] = {}

        def __call__(cls, *args, **kwargs):
            # 记录调用统计
            name = cls.__name__
            cls._instance_count[name] = cls._instance_count.get(name, 0) + 1
            count = cls._instance_count[name]

            print(f"[#{count}] {name}.__call__{args} {kwargs}")

            # type.__call__ 内部会调用 cls.__new__ 然后 cls.__init__
            instance = super().__call__(*args, **kwargs)
            print(f"[#{count}] → 返回 {instance!r}")
            return instance

    class Point(metaclass=LoggingMeta):
        def __init__(self, x: float, y: float):
            self.x = x
            self.y = y

        def __repr__(self):
            return f"Point({self.x}, {self.y})"

    print("创建 Point 实例：")
    p1 = Point(1, 2)
    p2 = Point(3, 4)
    print(f"统计: {Point._instance_count}")  # {'Point': 2}


# ============================================================
# 6. 实例属性 vs 类属性 —— 查找顺序
# ============================================================

def demo_attribute_lookup():
    """演示属性查找的顺序和 __dict__ 的分离"""

    class Base:
        color = "红色"
        items: list[int] = []  # 故意用可变类属性展示陷阱

    class Middle(Base):
        color = "蓝色"

    class Child(Middle):
        pass  # 没有自己的 color

    # 属性查找链
    obj = Child()
    print(f"obj.color = {obj.color!r}")      # 蓝色 ← Middle.color
    del Middle.color
    print(f"del Middle.color 后: obj.color = {obj.color!r}")  # 红色 ← Base.color

    # 实例属性覆盖类属性
    obj.color = "绿色"
    print(f"obj.color='绿色' 后: obj.color = {obj.color!r}")  # 绿色 ← 实例

    # 证明它们在不同的 __dict__ 里
    print(f"obj.__dict__:       {obj.__dict__}")
    print(f"Child.__dict__:     {list(Child.__dict__.keys())[:5]}")
    print(f"Middle.__dict__:    {list(Middle.__dict__.keys())[:5]}")
    print(f"Base.__dict__:      {list(Base.__dict__.keys())[:5]}")

    # 可变类属性的陷阱
    print("\n=== 可变类属性陷阱 ===")
    o1 = Base()
    o2 = Base()
    o1.items.append(1)
    print(f"o1.items = {o1.items}, o2.items = {o2.items}")  # 共享！

    # 正确做法：__init__ 中绑定实例属性
    class Safe:
        def __init__(self):
            self.items: list[int] = []  # 每个实例独立

    s1 = Safe()
    s2 = Safe()
    s1.items.append(1)
    print(f"s1.items = {s1.items}, s2.items = {s2.items}")  # 独立


# ============================================================
# 7. Bound Method vs Unbound Function
# ============================================================

def demo_bound_method():
    """理解 self 从哪里来——MethodType 的包装机制"""

    class Greeter:
        greeting = "你好"

        def greet(self, name: str) -> str:
            return f"{self.greeting}, {name}!"

    g = Greeter()

    # 类属性访问：得到普通函数
    func = Greeter.greet
    print(f"Greeter.greet:     {func}, type={type(func).__name__}")       # function

    # 实例属性访问：得到绑定方法
    method = g.greet
    print(f"g.greet:           {method}, type={type(method).__name__}")  # method

    # 绑定方法的内部结构
    print(f"method.__func__:   {method.__func__}")   # 原始函数
    print(f"method.__self__:   {method.__self__}")   # 绑定的实例
    print(f"method() = {method('Alice')!r}")          # 你好, Alice!

    # 手动绑定
    manual_bound = types.MethodType(Greeter.greet, g)
    print(f"手动绑定: {manual_bound('Bob')!r}")       # 你好, Bob!

    # 描述符视角：函数之所以能"绑定"，是因为 function.__get__ 的存在
    print(f"\nfunction.__get__ 存在: {hasattr(Greeter.greet, '__get__')}")  # True

    # 通过描述符协议手动触发绑定
    bound_via_descriptor = Greeter.greet.__get__(g, Greeter)
    print(f"描述符绑定: {bound_via_descriptor('Charlie')!r}")  # 你好, Charlie!

    # 类级别的访问：__get__(None, Greeter) 返回函数本身
    unbound = Greeter.greet.__get__(None, Greeter)
    print(f"__get__(None, cls): {unbound}, is func: {unbound is Greeter.greet}")


# ============================================================
# 8. super() —— 不是父类，是 MRO 的下一个
# ============================================================

def demo_super_mro():
    """super() 沿着 MRO 链查找，不是直接找父类"""

    class A:
        def method(self) -> str:
            return "A"

    class B(A):
        def method(self) -> str:
            return f"B → {super().method()}"

    class C(A):
        def method(self) -> str:
            return f"C → {super().method()}"

    class D(B, C):
        def method(self) -> str:
            return f"D → {super().method()}"

    print(f"D.__mro__: {[c.__name__ for c in D.__mro__]}")
    # ['D', 'B', 'C', 'A', 'object']

    result = D().method()
    print(f"D().method() = {result}")
    # D → B → C → A

    # 验证：B 的父类是 A，但 super().method() 跳到了 C
    # 因为 MRO 中 B 后面是 C，不是 A


# ============================================================
# 9. 描述符初窥 —— 手写 property
# ============================================================

def demo_descriptor_basics():
    """手写一个 property 替代品，展示 __get__ 和 __set__"""

    class MyProperty:
        """简化版 property——展示描述符协议的最小实现"""
        def __init__(self, fget=None, fset=None, fdel=None):
            self.fget = fget
            self.fset = fset
            self.fdel = fdel
            self._name = None  # 存储属性名，用于 __set_name__

        def __set_name__(self, owner, name):
            """Python 3.6+ 自动调用，告知描述符绑定的属性名"""
            self._name = name

        def __get__(self, instance, owner=None):
            if instance is None:
                return self  # 类级别访问返回描述符本身
            if self.fget is None:
                raise AttributeError(f"不可读属性: {self._name}")
            return self.fget(instance)

        def __set__(self, instance, value):
            if self.fset is None:
                raise AttributeError(f"不可写属性: {self._name}")
            self.fset(instance, value)

        def __delete__(self, instance):
            if self.fdel is None:
                raise AttributeError(f"不可删属性: {self._name}")
            self.fdel(instance)

        def setter(self, fset):
            return type(self)(self.fget, fset, self.fdel)

        def deleter(self, fdel):
            return type(self)(self.fget, self.fset, fdel)

    # 使用 MyProperty
    class Person:
        def __init__(self, name: str, age: int):
            self._name = name
            self._age = age

        @MyProperty  # 注意：是 MyProperty，不是 property
        def name(self) -> str:
            return self._name

        @MyProperty
        def age(self) -> int:
            return self._age

        @age.setter
        def age(self, value: int):
            if value < 0:
                raise ValueError("年龄不能为负")
            self._age = value

    p = Person("Alice", 30)
    print(f"Person.name = {p.name!r}")
    print(f"Person.age = {p.age}")
    p.age = 31
    print(f"更新后 Person.age = {p.age}")

    try:
        p.age = -1
    except ValueError as e:
        print(f"校验生效: {e}")

    # 证明 MyProperty 和 built-in property 一样是描述符
    print(f"\nMyProperty 实现了 __get__: {hasattr(MyProperty, '__get__')}")
    print(f"内置 property 实现了 __get__: {hasattr(property, '__get__')}")

    # 验证类级别访问返回描述符本身
    print(f"Person.age 类级别访问: {Person.age!r}")  # MyProperty 对象


# ============================================================
# 10. 元类在现实世界：注册模式
# ============================================================

def demo_metaclass_registry():
    """用元类实现自动注册——常见于插件系统"""

    class PluginRegistry(type):
        """自动把子类注册到 _registry 字典"""
        _registry: dict[str, type] = {}

        def __new__(mcs, name, bases, namespace):
            cls = super().__new__(mcs, name, bases, namespace)
            if not name.startswith('Base'):  # 跳过基类
                mcs._registry[name] = cls
            return cls

        @classmethod
        def list_plugins(mcs):
            return list(mcs._registry.keys())

    class BasePlugin(metaclass=PluginRegistry):
        """插件基类——不会注册自身"""

    class JSONPlugin(BasePlugin):
        """处理 JSON 的插件"""

    class CSVPlugin(BasePlugin):
        """处理 CSV 的插件"""

    class XMLPlugin(BasePlugin):
        """处理 XML 的插件"""

    print(f"注册的插件: {PluginRegistry.list_plugins()}")
    # ['JSONPlugin', 'CSVPlugin', 'XMLPlugin']

    # 运行时创建也生效（因为元类的 __new__ 会被触发）
    class YamlPlugin(BasePlugin):
        """运行时动态加的插件"""

    print(f"新增后: {PluginRegistry.list_plugins()}")
    # ['JSONPlugin', 'CSVPlugin', 'XMLPlugin', 'YamlPlugin']


# ============================================================
# 运行所有演示
# ============================================================

if __name__ == '__main__':
    demos = [
        ("1. type() 动态创建类", demo_type_create),
        ("2. __new__ vs __init__", demo_new_vs_init),
        ("3. 不可变类型子类化", demo_new_immutable),
        ("4. 单例模式", demo_singleton),
        ("5. 元类 __call__", demo_metaclass_call),
        ("6. 属性查找顺序", demo_attribute_lookup),
        ("7. 绑定方法 vs 函数", demo_bound_method),
        ("8. super() 与 MRO", demo_super_mro),
        ("9. 手写描述符替代 property", demo_descriptor_basics),
        ("10. 元类注册模式", demo_metaclass_registry),
    ]

    for title, func in demos:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        func()
