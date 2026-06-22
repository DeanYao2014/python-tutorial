"""3.4 描述符协议：完整可运行示例
===========================================
覆盖描述符协议本质、数据描述符 vs 非数据描述符、内置描述符解构、
实用描述符实现、描述符+元类协同。

运行方式:
    python descriptors_deep.py
"""

from typing import Any, Callable


# ============================================================
# Part A: 描述符协议基础 —— __get__、__set__、__delete__、__set_name__
# ============================================================

def demo_basic_descriptor():
    """最小描述符：打印每次属性访问"""
    class RevealAccess:
        def __get__(self, instance, owner=None):
            print(f"  __get__: instance={instance!r}, "
                  f"owner={owner.__name__ if owner else None}")
            return 42

        def __set__(self, instance, value):
            print(f"  __set__: instance={instance!r}, value={value!r}")

        def __delete__(self, instance):
            print(f"  __delete__: instance={instance!r}")

    class MyClass:
        x = RevealAccess()

    obj = MyClass()
    print("实例访问:")
    print(f"  obj.x = {obj.x}")
    print("实例赋值:")
    obj.x = 100
    print("实例删除:")
    del obj.x
    print("类访问:")
    print(f"  MyClass.x → {MyClass.x} (instance=None)")


def demo_set_name():
    """__set_name__ 让描述符知道自己叫什么名字"""
    class Typed:
        def __init__(self, expected_type: type):
            self.expected_type = expected_type
            self.private_name: str = ""

        def __set_name__(self, owner, name: str):
            self.private_name = f"_{name}"
            print(f"  __set_name__: owner={owner.__name__}, name='{name}'"
                  f" → storage='{self.private_name}'")

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return getattr(instance, self.private_name)

        def __set__(self, instance, value):
            if not isinstance(value, self.expected_type):
                raise TypeError(
                    f"期望 {self.expected_type.__name__}，"
                    f"实际 {type(value).__name__}"
                )
            setattr(instance, self.private_name)

    class Point:
        x = Typed(int)
        y = Typed(float)

        def __init__(self, x: int, y: float):
            self.x = x
            self.y = y

        def __repr__(self):
            return f"Point(x={self.x}, y={self.y})"

    p = Point(3, 4.5)
    print(f"  {p}")

    try:
        p.x = "not int"
    except TypeError as e:
        print(f"  类型校验: {e}")


# ============================================================
# Part B: 数据描述符 vs 非数据描述符 —— 优先级链
# ============================================================

def demo_priority_chain():
    """证明数据描述符 > 实例__dict__ > 非数据描述符"""
    class DataDesc:
        def __get__(self, instance, owner=None):
            print("  DataDesc.__get__")
            return "数据描述符的值"

        def __set__(self, instance, value):
            print(f"  DataDesc.__set__({value})")

    class NonDataDesc:
        def __get__(self, instance, owner=None):
            print("  NonDataDesc.__get__")
            return "非数据描述符的值"

    class Test:
        data_des = DataDesc()
        nondata_des = NonDataDesc()

    t = Test()

    print("── 数据描述符：写入失败（被 __set__ 拦截）──")
    print(f"  初始: {t.data_des}")
    t.data_des = "覆盖尝试"
    print(f"  覆盖后: {t.data_des}")
    print(f"  __dict__: {t.__dict__}")

    print("\n── 非数据描述符：写入成功（进入 __dict__）──")
    print(f"  初始: {t.nondata_des}")
    t.__dict__['nondata_des'] = "实例覆盖"
    print(f"  覆盖后: {t.nondata_des}")


def demo_staticmethod_shadow():
    """证明 @staticmethod 是「非」数据描述符——可被实例属性遮蔽"""
    class Demo:
        @staticmethod
        def greet():
            return "hello"

    d = Demo()
    print(f"  通过实例: {d.greet()}")
    d.greet = lambda: "goodbye"
    print(f"  覆盖后:   {d.greet()}")

    # 对比：@property 不能被遮蔽
    class Demo2:
        @property
        def value(self):
            return 42

    d2 = Demo2()
    print(f"  @property 初始: {d2.value}")
    d2.__dict__['value'] = 99
    print(f"  写入 __dict__ 后: {d2.value}")   # 仍然 42


# ============================================================
# Part C: 内置描述符解构 —— @property、@staticmethod、@classmethod
# ============================================================

def demo_property_equivalent():
    """简化版 property —— 展示它是数据描述符"""
    class Property:
        def __init__(self, fget=None, fset=None, fdel=None):
            self.fget = fget
            self.fset = fset
            self.fdel = fdel

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            if self.fget is None:
                raise AttributeError("属性不可读")
            return self.fget(instance)

        def __set__(self, instance, value):
            if self.fset is None:
                raise AttributeError("属性不可写")
            self.fset(instance, value)

        def __delete__(self, instance):
            if self.fdel is None:
                raise AttributeError("属性不可删")
            self.fdel(instance)

        def setter(self, fset):
            return type(self)(self.fget, fset, self.fdel)

        def deleter(self, fdel):
            return type(self)(self.fget, self.fset, fdel)

    class Temperature:
        def __init__(self, celsius=0):
            self._celsius = celsius

        def get_celsius(self):
            return self._celsius

        def set_celsius(self, value):
            if value < -273.15:
                raise ValueError("低于绝对零度")
            self._celsius = value

        celsius = Property(get_celsius, set_celsius)

    t = Temperature(100)
    print(f"  celsius = {t.celsius}")
    t.celsius = 50
    print(f"  celsius = {t.celsius}")


def demo_staticmethod_equivalent():
    """简化版 staticmethod —— 非数据描述符"""
    class StaticMethod:
        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner=None):
            return self.func   # 不绑定，直接返回原始函数

    class Demo:
        @StaticMethod
        def add(a, b):
            return a + b

    print(f"  Demo.add(1, 2)   = {Demo.add(1, 2)}")
    d = Demo()
    print(f"  d.add(3, 4)      = {d.add(3, 4)}")


def demo_classmethod_equivalent():
    """简化版 classmethod —— 非数据描述符，但绑定到类"""
    class ClassMethod:
        def __init__(self, func):
            self.func = func

        def __get__(self, instance, owner=None):
            if owner is None:
                owner = type(instance)

            def bound(*args, **kwargs):
                return self.func(owner, *args, **kwargs)

            return bound

    class Demo:
        @ClassMethod
        def from_string(cls, text: str):
            obj = cls()
            obj.text = text
            return obj

    d = Demo.from_string("hello")
    print(f"  Demo.from_string('hello').text = {d.text}")


def demo_slots_descriptor():
    """__slots__ 成员是 member_descriptor——C 实现的数据描述符"""
    class Point:
        __slots__ = ('x', 'y')

        def __init__(self, x, y):
            self.x = x
            self.y = y

    print(f"  Point.__dict__['x'] = {Point.__dict__['x']!r}")
    print(f"  type = {type(Point.__dict__['x']).__name__}")

    p = Point(1, 2)
    print(f"  p.x = {p.x}")

    try:
        del p.x
    except AttributeError as e:
        print(f"  del p.x → {e}")


# ============================================================
# Part D: 描述符实战
# ============================================================

def demo_validated_field():
    """ValidatedField: 类型检查 + 自定义校验"""
    class ValidatedField:
        def __init__(
            self,
            expected_type: type,
            validators: list[Callable[[Any], bool]] | None = None,
        ):
            self.expected_type = expected_type
            self.validators = validators or []
            self.storage_name = ""

        def __set_name__(self, owner, name: str):
            self.storage_name = f"_{name}"

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return getattr(instance, self.storage_name)

        def __set__(self, instance, value):
            if not isinstance(value, self.expected_type):
                raise TypeError(
                    f"期望 {self.expected_type.__name__}，"
                    f"实际 {type(value).__name__}"
                )
            for v in self.validators:
                if not v(value):
                    raise ValueError(f"校验失败: {value!r}")
            setattr(instance, self.storage_name)

    class User:
        name = ValidatedField(str, validators=[lambda v: len(v) > 0])
        age = ValidatedField(int, validators=[lambda v: v >= 0])

        def __init__(self, name: str, age: int):
            self.name = name
            self.age = age

        def __repr__(self):
            return f"User(name={self.name!r}, age={self.age})"

    u = User("Alice", 30)
    print(f"  {u}")

    try:
        u.age = -1
    except ValueError as e:
        print(f"  ValueError: {e}")


def demo_lazy_property():
    """LazyProperty: 非数据描述符实现的计算缓存"""
    class LazyProperty:
        def __init__(self, func):
            self.func = func
            self.__doc__ = func.__doc__

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            value = self.func(instance)
            # 写入实例 __dict__ → 因为是非数据描述符，下次优先从 __dict__ 读
            instance.__dict__[self.func.__name__] = value
            return value

    class DataSet:
        def __init__(self, numbers: list[int]):
            self.numbers = numbers

        @LazyProperty
        def avg(self):
            print("  (正在计算 avg...)")
            return sum(self.numbers) / len(self.numbers)

    ds = DataSet([1, 2, 3, 4, 5])
    print(f"  第一次访问: {ds.avg}")
    print(f"  第二次访问: {ds.avg}")  # 不触发计算


def demo_alias_field():
    """AliasField: 将一个属性映射到另一个属性"""
    class Alias:
        def __init__(self, target: str):
            self.target = target

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return getattr(instance, self.target)

        def __set__(self, instance, value):
            setattr(instance, self.target, value)

        def __delete__(self, instance):
            delattr(instance, self.target)

    class Contact:
        email = "alice@example.com"
        mail = Alias("email")

    c = Contact()
    print(f"  mail 别名: {c.mail}")
    c.mail = "bob@test.com"
    print(f"  修改 mail 后 email 变成: {c.email}")


def demo_positive_number():
    """Positive: 强制属性 > 0"""
    class Positive:
        def __set_name__(self, owner, name: str):
            self.name = name
            self.storage = f"_{name}"

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return getattr(instance, self.storage, 0)

        def __set__(self, instance, value):
            if not isinstance(value, (int, float)):
                raise TypeError(f"{self.name} 必须是数字")
            if value <= 0:
                raise ValueError(f"{self.name} 必须 > 0，得到 {value}")
            setattr(instance, self.storage, value)

    class Rectangle:
        width = Positive()
        height = Positive()

        def __init__(self, width: float, height: float):
            self.width = width
            self.height = height

        @property
        def area(self):
            return self.width * self.height

    r = Rectangle(5.0, 3.0)
    print(f"  Rectangle(width=5, height=3) area = {r.area}")

    try:
        r.width = -1
    except ValueError as e:
        print(f"  ValueError: {e}")


def demo_drf_serializer():
    """DRF 风格序列化器：字段即描述符"""
    class Field:
        def __set_name__(self, owner, name: str):
            self.name = name

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return instance._data.get(self.name)

        def __set__(self, instance, value):
            instance._data[self.name] = self._clean(value)

        def _clean(self, value):
            return value

    class CharField(Field):
        def _clean(self, value):
            return str(value).strip()

    class IntegerField(Field):
        def _clean(self, value):
            return int(value)

    class Serializer:
        def __init__(self, data: dict):
            self._data: dict = {}
            for key, value in data.items():
                if hasattr(type(self), key):
                    setattr(self, key, value)
                else:
                    self._data[key] = value

        @property
        def validated_data(self):
            return dict(self._data)

    class UserSerializer(Serializer):
        name = CharField()
        age = IntegerField()

    s = UserSerializer({"name": " Alice ", "age": "30"})
    print(f"  name = {s.name!r}")   # 'Alice'
    print(f"  age  = {s.age}")      # 30
    print(f"  validated_data = {s.validated_data}")


# ============================================================
# Part E: 描述符 + 元类协同 —— Mini-ORM
# ============================================================

def demo_orm_descriptor_metaclass():
    """描述符定义列行为 + 元类收集列"""
    class Column:
        def __set_name__(self, owner, name: str):
            self.name = name

        def __get__(self, instance, owner=None):
            if instance is None:
                return self
            return instance._row.get(self.name)

        def __set__(self, instance, value):
            instance._row[self.name] = value

    class ModelMeta(type):
        def __new__(mcs, name, bases, namespace):
            cls = super().__new__(mcs, name, bases, namespace)
            # 只收集当前类直接定义的 Column，继承链上的 Column 由父类管理
            own_columns = {
                k: v for k, v in namespace.items()
                if isinstance(v, Column)
            }
            # 合并父类列（支持继承）
            for base in bases:
                if hasattr(base, '_columns'):
                    own_columns = {**base._columns, **own_columns}
            cls._columns = own_columns
            return cls

    class Model(metaclass=ModelMeta):
        _columns: dict = {}

        def __init__(self, **kwargs):
            self._row: dict = {}
            for col_name in self._columns:
                setattr(self, col_name, kwargs.get(col_name))

        def save(self):
            cols = ", ".join(self._columns)
            vals = ", ".join(repr(self._row[c]) for c in self._columns)
            print(f"  INSERT INTO {type(self).__name__.lower()} "
                  f"({cols}) VALUES ({vals})")

    class User(Model):
        name = Column()
        age = Column()
        email = Column()

    print(f"  User._columns = {list(User._columns.keys())}")
    u = User(name="Bob", age=30, email="bob@test.com")
    u.save()


# ============================================================
# 主程序入口
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("3.4 描述符协议 —— 完整示例")
    print("=" * 55)

    print("\n── Part A1: 最小描述符 ──")
    demo_basic_descriptor()

    print("\n── Part A2: __set_name__ ──")
    demo_set_name()

    print("\n── Part B1: 优先级链 ──")
    demo_priority_chain()

    print("\n── Part B2: @staticmethod 可被遮蔽 ──")
    demo_staticmethod_shadow()

    print("\n── Part C1: 简化版 @property ──")
    demo_property_equivalent()

    print("\n── Part C2: 简化版 @staticmethod ──")
    demo_staticmethod_equivalent()

    print("\n── Part C3: 简化版 @classmethod ──")
    demo_classmethod_equivalent()

    print("\n── Part C4: __slots__ 描述符本质 ──")
    demo_slots_descriptor()

    print("\n── Part D1: ValidatedField ──")
    demo_validated_field()

    print("\n── Part D2: LazyProperty ──")
    demo_lazy_property()

    print("\n── Part D3: AliasField ──")
    demo_alias_field()

    print("\n── Part D4: Positive ──")
    demo_positive_number()

    print("\n── Part D5: DRF 序列化器 ──")
    demo_drf_serializer()

    print("\n── Part E: ORM 描述符 + 元类 ──")
    demo_orm_descriptor_metaclass()
