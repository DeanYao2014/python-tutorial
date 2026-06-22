"""2.2 属性控制 —— 代码示例合集

每个示例独立可运行，展示 Python 属性访问控制的完整机制。
"""

import sys
import timeit
from typing import Any


# ============================================================
# 1. @property 完整用法：校验、计算、删除
# ============================================================

def demo_property_full():
    """展示 @property 的 getter/setter/deleter 及计算属性"""

    class Temperature:
        """温度类——摄氏度 + 华氏度双向转换"""
        def __init__(self, celsius: float = 0):
            self._celsius = celsius

        @property
        def celsius(self) -> float:
            """摄氏度：内部存储值"""
            print("  [读 celsius]")
            return self._celsius

        @celsius.setter
        def celsius(self, value: float):
            """摄氏度：带绝对零度校验"""
            print(f"  [写 celsius ← {value}]")
            if value < -273.15:
                raise ValueError(f"低于绝对零度: {value}°C")
            self._celsius = value

        @celsius.deleter
        def celsius(self):
            """摄氏度：删除时重置为 0"""
            print("  [删 celsius → 重置为 0]")
            self._celsius = 0

        @property
        def fahrenheit(self) -> float:
            """华氏度：只读计算属性"""
            print("  [计算 fahrenheit]")
            return self._celsius * 9 / 5 + 32

        @fahrenheit.setter
        def fahrenheit(self, value: float):
            """华氏度：写时反向计算摄氏度"""
            print(f"  [写 fahrenheit ← {value}]")
            self.celsius = (value - 32) * 5 / 9  # 走 celsius.setter 校验

    t = Temperature(100)
    print(f"\n初始化: celsius={t.celsius}°C, fahrenheit={t.fahrenheit}°F")

    print("\n--- 设置 fahrenheit=32°F ---")
    t.fahrenheit = 32
    print(f"结果: celsius={t.celsius}°C, fahrenheit={t.fahrenheit}°F")

    print("\n--- 删除 celsius ---")
    del t.celsius
    print(f"结果: celsius={t.celsius}°C")

    print("\n--- 校验：尝试 -300°C ---")
    try:
        t.celsius = -300
    except ValueError as e:
        print(f"  校验拦截: {e}")


# ============================================================
# 2. __getattr__：懒加载 + 代理模式
# ============================================================

def demo_getattr():
    """__getattr__ 的两种经典用法"""

    # 用法一：懒加载属性（首次访问时计算并缓存）
    class LazyConfig:
        """数据库配置：首次访问时才从环境变量加载"""
        def __init__(self):
            self._loaded: set[str] = set()
            self._env = {"DB_HOST": "localhost", "DB_PORT": "5432",
                         "DB_USER": "admin", "DB_PASS": "secret"}

        def __getattr__(self, name: str):
            if name.startswith('_'):
                raise AttributeError(name)
            if name not in self._env:
                raise AttributeError(f"未知配置项: {name}")
            # 模拟昂贵加载
            value = f"[loaded] {self._env[name]}"
            setattr(self, name, value)     # 缓存！下次不再走 __getattr__
            self._loaded.add(name)
            print(f"    首次加载: {name} = {value}")
            return value

    cfg = LazyConfig()
    print(f"第1次访问 DB_HOST: {cfg.DB_HOST}")  # 触发 __getattr__
    print(f"第2次访问 DB_HOST: {cfg.DB_HOST}")  # 从 __dict__ 直接读取
    print(f"已缓存: {cfg._loaded}")

    try:
        cfg.UNKNOWN_KEY
    except AttributeError as e:
        print(f"未定义配置项: {e}")

    # 用法二：代理模式——转发属性访问
    print("\n--- 代理模式 ---")
    class ForwardingProxy:
        """把读取操作转发给目标对象"""
        def __init__(self, target):
            self._target = target

        def __getattr__(self, name):
            print(f"    转发: {name}")
            return getattr(self._target, name)

    original = type('_', (), {'say_hello': lambda self: "Hello from original!"})()
    proxy = ForwardingProxy(original)
    print(proxy.say_hello())


# ============================================================
# 3. __getattribute__：全拦截（含危险性展示）
# ============================================================

def demo_getattribute():
    """展示 __getattribute__ 的正确写法与常见陷阱"""

    class SafeAuditor:
        """安全的全属性访问记录器"""
        def __init__(self, name):
            # 必须用 object.__setattr__ 绕过自己的逻辑
            object.__setattr__(self, 'name', name)
            object.__setattr__(self, '_log', [])

        def __getattribute__(self, name):
            # 获取内部状态——必须走 object
            if name != '_log' and not name.startswith('__'):
                log = object.__getattribute__(self, '_log')
                log.append(name)
            return object.__getattribute__(self, name)

        def __setattr__(self, name, value):
            self._log.append(f"SET {name}={value!r}")
            object.__setattr__(self, name, value)

        def show_log(self):
            return self._log

    s = SafeAuditor("Alice")
    _ = s.name       # 记录
    _ = s.name       # 再次记录
    s.age = 30       # 记录 SET

    print("审计日志:")
    for entry in s.show_log()[:5]:
        print(f"  {entry}")

    # 陷阱展示：无限递归
    print("\n--- 陷阱：无限递归 ---")

    class BadGetattribute:
        """错误示范——self 访问导致无限递归"""
        def __init__(self):
            self.value = 42

        def __getattribute__(self, name):
            # 错！self.value 会再次触发 __getattribute__
            if name == 'value':
                return self.value  # RecursionError!
            return object.__getattribute__(self, name)

    b = BadGetattribute()
    try:
        b.value
    except RecursionError:
        print("  RecursionError: self.value 在 __getattribute__ 中无限递归")
        print("  正确做法: 应该用 object.__getattribute__(self, 'value')")


# ============================================================
# 4. __setattr__ + __delattr__：变更日志代理
# ============================================================

def demo_setattr_delattr():
    """完整的属性变更审计代理"""

    class AuditProxy:
        """代理目标对象，记录所有属性变更"""
        def __init__(self, target: object, label: str = ""):
            object.__setattr__(self, '_target', target)
            object.__setattr__(self, '_log', [])
            object.__setattr__(self, '_label', label)
            if label:
                self._log.append(f"--- 开始审计: {label} ---")

        def __getattr__(self, name):
            # 读操作委托给目标，不在代理中记录（读的频率太高）
            return getattr(self._target, name)

        def __setattr__(self, name, value):
            old = getattr(self._target, name, None)
            self._log.append(f"SET {name}: {old!r} → {value!r}")
            object.__setattr__(self._target, name, value)

        def __delattr__(self, name):
            old = getattr(self._target, name, "<不存在>")
            self._log.append(f"DEL {name} (was {old!r})")
            object.__delattr__(self._target, name)

        def audit_report(self) -> list[str]:
            return self._log

    class BankAccount:
        def __init__(self, owner: str, balance: float):
            self.owner = owner
            self.balance = balance

        def __repr__(self):
            return f"BankAccount({self.owner}, ¥{self.balance})"

    acct = BankAccount("张三", 1000.0)
    proxy = AuditProxy(acct, label="交易会话 #1")

    # 操作
    proxy.balance -= 100       # 取款
    proxy.balance += 500       # 存款
    proxy.owner = "张三(已婚)"  # 改名
    del proxy.balance          # 删除余额
    proxy.balance = 0.0        # 重建余额

    # 注意：对代理的读操作直接委托给 target
    print(f"账户: {proxy}")

    print("\n审计报告:")
    for entry in proxy.audit_report():
        print(f"  {entry}")


# ============================================================
# 5. __slots__：内存与性能对比
# ============================================================

def demo_slots():
    """对比 __slots__ 的内存节省和属性访问速度"""

    class PointWithDict:
        def __init__(self, x, y, z=0):
            self.x = x
            self.y = y
            self.z = z

    class PointWithSlots:
        __slots__ = ('x', 'y', 'z')
        def __init__(self, x, y, z=0):
            self.x = x
            self.y = y
            self.z = z

    # 1. 内存对比 (sys.getsizeof 只算对象本身，不含 __dict__)
    pd = PointWithDict(1.0, 2.0)
    ps = PointWithSlots(1.0, 2.0)

    dict_size = sys.getsizeof(pd.__dict__)
    obj_size_no_slots = sys.getsizeof(pd)
    obj_size_slots = sys.getsizeof(ps)

    print(f"PointWithDict:  对象={obj_size_no_slots}B, __dict__={dict_size}B, 合计≈{obj_size_no_slots + dict_size}B")
    print(f"PointWithSlots: 对象={obj_size_slots}B, 无 __dict__")
    print(f"每个实例节省: 约 {obj_size_no_slots + dict_size - obj_size_slots}B")

    # 2. 演示：__slots__ 禁止动态添加属性
    try:
        ps.color = "red"
    except AttributeError as e:
        print(f"\n__slots__ 限制生效: {e}")

    # 3. 属性访问速度对比
    N = 5_000_000
    print(f"\n属性访问速度对比 ({N:,} 次):")

    t_dict = timeit.timeit(
        "obj.x; obj.y; obj.z",
        globals={'obj': PointWithDict(1.0, 2.0, 3.0)},
        number=N
    )
    t_slots = timeit.timeit(
        "obj.x; obj.y; obj.z",
        globals={'obj': PointWithSlots(1.0, 2.0, 3.0)},
        number=N
    )
    print(f"  WithDict:  {t_dict:.3f}s")
    print(f"  WithSlots: {t_slots:.3f}s")
    print(f"  加速比:    {t_dict / t_slots:.2f}x")

    # 4. 继承中 __slots__ 的行为
    print("\n--- 继承中的 __slots__ ---")

    class Base:
        __slots__ = ('x',)

    class ChildWithDict(Base):
        pass  # 没有 __slots__ → 自动获得 __dict__

    class ChildWithSlots(Base):
        __slots__ = ('y',)  # 合并为 ('x', 'y')

    c_dict = ChildWithDict()
    c_dict.x = 1
    c_dict.z = 3  # OK！有 __dict__
    print(f"ChildWithDict: x={c_dict.x}, __dict__={c_dict.__dict__}")

    c_slots = ChildWithSlots()
    c_slots.x = 1
    c_slots.y = 2
    print(f"ChildWithSlots: x={c_slots.x}, y={c_slots.y}")
    print(f"  无 __dict__: {not hasattr(c_slots, '__dict__')}")

    try:
        c_slots.z = 3
    except AttributeError as e:
        print(f"  按预期: {e}")

    # 5. __slots__ 与多继承的注意事项
    print("\n--- __slots__ 多继承限制 ---")

    class A:
        __slots__ = ('a',)

    class B:
        __slots__ = ('b',)

    # Python 允许多个有 __slots__ 的父类（只要没有 __dict__ 冲突）
    try:
        class C(A, B):
            __slots__ = ('c',)

        c = C()
        c.a = 1
        c.b = 2
        c.c = 3
        print(f"C 可以多继承 __slots__ 类: a={c.a}, b={c.b}, c={c.c}")
    except TypeError as e:
        print(f"  多继承失败: {e}")

    # 但如果一个父类有 __dict__，另一个有 __slots__，就会冲突
    class HasDict:
        pass  # 有 __dict__

    try:
        class Conflicted(HasDict, A):
            pass
    except TypeError as e:
        print(f"  冲突: {e}")


# ============================================================
# 6. 描述符协议：从底层实现 property 的效果
# ============================================================

def demo_descriptor_protocol():
    """手写数据描述符 vs 非数据描述符，展示优先级差异"""

    # 数据描述符：__get__ + __set__
    class ValidatedField:
        """带类型检查和值校验的可复用描述符"""
        def __init__(self, field_type: type, *, min_value=None, max_value=None):
            self.field_type = field_type
            self.min_value = min_value
            self.max_value = max_value
            self._name = None  # 由 __set_name__ 设置

        def __set_name__(self, owner, name):
            """Python 3.6+ 自动调用：让描述符知道自己的属性名"""
            self._name = name

        def __get__(self, instance, owner):
            if instance is None:
                return self  # 类级别访问返回描述符本身
            # 从实例的 __dict__ 读取实际值
            return instance.__dict__.get(self._name, None)

        def __set__(self, instance, value):
            if not isinstance(value, self.field_type):
                # 尝试类型转换
                try:
                    value = self.field_type(value)
                except (ValueError, TypeError):
                    raise TypeError(
                        f"{self._name} 期望 {self.field_type.__name__}, "
                        f"得到 {type(value).__name__}"
                    )
            if self.min_value is not None and value < self.min_value:
                raise ValueError(f"{self._name} 不能小于 {self.min_value}")
            if self.max_value is not None and value > self.max_value:
                raise ValueError(f"{self._name} 不能大于 {self.max_value}")
            instance.__dict__[self._name] = value

        def __delete__(self, instance):
            instance.__dict__.pop(self._name, None)

    # 非数据描述符：只有 __get__
    class LazyAttribute:
        """懒加载属性——只有 __get__，实例属性可以覆盖它"""
        def __init__(self, factory):
            self.factory = factory
            self._name = None

        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, instance, owner):
            if instance is None:
                return self
            # 每次访问都计算（不缓存），展示非数据描述符的行为
            value = self.factory(instance)
            print(f"    LazyAttribute 计算: {self._name} = {value}")
            # 不缓存到 instance.__dict__，下次还会走 __get__
            return value

    # 使用描述符
    class Product:
        name = ValidatedField(str)                    # 数据描述符
        price = ValidatedField(float, min_value=0.01)  # 数据描述符
        stock = ValidatedField(int, min_value=0)       # 数据描述符

        @property  # 也是数据描述符
        def total_value(self):
            return self.price * self.stock

        created_at = LazyAttribute(lambda self: "2024-01-01")  # 非数据描述符

        def __init__(self, name, price, stock):
            self.name = name
            self.price = price
            self.stock = stock

    p = Product("Widget", 9.99, 100)
    print(f"产品: name={p.name}, price={p.price}, stock={p.stock}")
    print(f"总价值: {p.total_value}")

    # 校验
    try:
        p.price = -1
    except ValueError as e:
        print(f"校验: {e}")

    try:
        p.stock = "很多"  # str 不能转为 int(也不是数字)
    except TypeError as e:
        print(f"类型错误: {e}")

    # 类型转换：int 可接受 float-like string
    p.stock = "200"
    print(f"stock 从 '200' 转换为: {type(p.stock).__name__}({p.stock})")

    # 非数据描述符 vs 实例属性
    print(f"\n首次访问 created_at: {p.created_at}")     # 走 __get__
    p.__dict__['created_at'] = "被覆盖了"              # 实例属性覆盖非数据描述符
    print(f"覆盖后访问 created_at: {p.created_at}")    # 不走 __get__ 了！

    # 但对于数据描述符，实例属性会被忽略
    p.__dict__['price'] = 999  # 不会生效
    print(f"price 仍然是: {p.price}")  # 9.99，不是 999

    # 类级别访问
    print(f"\n类级别访问: Product.price = {Product.price!r}")  # ValidatedField 对象


# ============================================================
# 7. AttributeError 陷阱：描述符内部抛异常
# ============================================================

def demo_attribute_error_trap():
    """展示属性访问中 AttributeError 的特殊语义"""

    class Problematic:
        def __init__(self):
            self._ready = False

        def __getattr__(self, name):
            print(f"  __getattr__ 被触发: {name}")
            return f"default for {name}"

        @property
        def data(self):
            """属性内部抛 AttributeError——危险的信号"""
            if not self._ready:
                raise AttributeError("data 尚未就绪")
            return self._ready

    p = Problematic()

    # 问题：property 内部抛了 AttributeError，Python 会怎样？
    print("访问 p.data (未就绪状态):")
    try:
        _ = p.data
    except AttributeError as e:
        print(f"  捕获 AttributeError: {e}")
        # 注意：不会触发 __getattr__，因为 property 是描述符
        # 描述符的 __get__ 已经处理了这个异常，Python 识别到
        # 属性"存在"（property在类字典中），只是值获取失败

    # 对比：访问一个真正不存在的属性
    print("\n访问 p.nonexistent:")
    print(f"  {p.nonexistent}")  # 触发 __getattr__

    # 正确姿势：property 内部用具体异常
    class Correct:
        def __init__(self):
            self._ready = False

        def __getattr__(self, name):
            print(f"  __getattr__ 被触发: {name}")
            return f"default for {name}"

        @property
        def data(self):
            if not self._ready:
                # good: 用 RuntimeError 而不是 AttributeError
                raise RuntimeError("data 尚未就绪——请先调用 .prepare()")
            return "ready!"

        def prepare(self):
            self._ready = True

    c = Correct()
    try:
        _ = c.data
    except RuntimeError as e:
        print(f"\n正确异常类型: {e}")

    c.prepare()
    print(f"就绪后: {c.data}")


# ============================================================
# 8. 综合实战：不可变对象（Frozen Class）
# ============================================================

def demo_frozen_class():
    """组合使用属性控制实现不可变对象"""

    class Frozen:
        """一旦创建就不可修改的对象（类似 namedtuple 但更灵活）"""
        def __init__(self, **kwargs):
            # 初始化时允许写入
            for key, value in kwargs.items():
                object.__setattr__(self, key, value)
            self._frozen = True

        def __setattr__(self, name, value):
            if getattr(self, '_frozen', False):
                raise AttributeError(f"不可修改：{type(self).__name__} 是冻结的")
            object.__setattr__(self, name, value)

        def __delattr__(self, name):
            raise AttributeError(f"不可删除：{type(self).__name__} 是冻结的")

        def __repr__(self):
            items = [f"{k}={v!r}" for k, v in self.__dict__.items()
                     if not k.startswith('_')]
            return f"{type(self).__name__}({', '.join(items)})"

    point = Frozen(x=1, y=2)
    print(f"创建: {point}")

    try:
        point.x = 10
    except AttributeError as e:
        print(f"写入被拒: {e}")

    try:
        del point.y
    except AttributeError as e:
        print(f"删除被拒: {e}")

    # 但如果真的需要"修改"，可以返回一个新对象
    class FrozenPoint(Frozen):
        def update(self, **kwargs) -> 'FrozenPoint':
            """返回一个新对象而非修改自身"""
            new_data = {k: v for k, v in self.__dict__.items()
                       if not k.startswith('_')}
            new_data.update(kwargs)
            return FrozenPoint(**new_data)

    p1 = FrozenPoint(x=1, y=2)
    p2 = p1.update(y=99)
    print(f"\n原对象: {p1}")
    print(f"新对象: {p2}")
    print(f"不同对象: {p1 is not p2}")


# ============================================================
# 运行所有演示
# ============================================================

if __name__ == '__main__':
    demos = [
        ("1. @property 完整用法", demo_property_full),
        ("2. __getattr__ 懒加载与代理", demo_getattr),
        ("3. __getattribute__ 全拦截", demo_getattribute),
        ("4. __setattr__ + __delattr__ 审计代理", demo_setattr_delattr),
        ("5. __slots__ 内存与性能", demo_slots),
        ("6. 描述符协议从底层实现", demo_descriptor_protocol),
        ("7. AttributeError 陷阱", demo_attribute_error_trap),
        ("8. 综合实战：不可变对象", demo_frozen_class),
    ]

    for title, func in demos:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        func()
