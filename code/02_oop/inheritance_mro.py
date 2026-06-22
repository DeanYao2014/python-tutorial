"""2.5 继承与MRO：C3算法、super()、Mixin、ABC"""

import time
import json
from abc import ABC, abstractmethod


# ══════════════════════════════════════════════════════════════════════
# 1. MRO 查看
# ══════════════════════════════════════════════════════════════════════

class A: pass
class B(A): pass
class C(A): pass
class D(B, C): pass

print("D.__mro__:", D.__mro__)
# 输出: (D, B, C, A, object)


# ══════════════════════════════════════════════════════════════════════
# 2. super() 沿 MRO 链走，不直接找父类
# ══════════════════════════════════════════════════════════════════════

class A1:
    def who(self):
        return "A1"

class B1(A1):
    def who(self):
        return "B1 → " + super().who()   # super() 去找 MRO 里的下一个

class C1(A1):
    def who(self):
        return "C1 → " + super().who()

class D1(B1, C1):
    def who(self):
        return "D1 → " + super().who()

print("D1.who():", D1().who())
# D1 → B1 → C1 → A1
# B1 的 super() 调到了 C1！不是 A1！


# ══════════════════════════════════════════════════════════════════════
# 3. 协作式多重继承——钻石问题
# ══════════════════════════════════════════════════════════════════════

class Root:
    def __init__(self):
        print("Root.__init__")
        self.name = "root"

class Left(Root):
    def __init__(self):
        print("Left.__init__")
        super().__init__()
        self.left_only = True

class Right(Root):
    def __init__(self):
        print("Right.__init__")
        super().__init__()
        self.right_only = True

class Bottom(Left, Right):
    def __init__(self):
        print("Bottom.__init__")
        super().__init__()

print("\n--- 协作式 super()：每条链自己调 super() ---")
b = Bottom()
print(f"name={b.name}, left_only={b.left_only}, right_only={b.right_only}")


# ══════════════════════════════════════════════════════════════════════
# 4. 不走 super() 的悲剧：父类 __init__ 被重复调用
# ══════════════════════════════════════════════════════════════════════

class LeftBad(Root):
    def __init__(self):
        print("LeftBad.__init__")
        Root.__init__(self)

class RightBad(Root):
    def __init__(self):
        print("RightBad.__init__")
        Root.__init__(self)

class BottomBad(LeftBad, RightBad):
    def __init__(self):
        print("BottomBad.__init__")
        LeftBad.__init__(self)
        RightBad.__init__(self)

print("\n--- 不走 super() 的悲剧：Root.__init__ 被调两次 ---")
BottomBad()


# ══════════════════════════════════════════════════════════════════════
# 5. 协作式 __init__ 的参数传递：**kwargs
# ══════════════════════════════════════════════════════════════════════

class Root2:
    def __init__(self, **kwargs):
        print("Root2.__init__")

class Left2(Root2):
    def __init__(self, left_arg=None, **kwargs):
        print(f"Left2.__init__(left_arg={left_arg})")
        super().__init__(**kwargs)

class Right2(Root2):
    def __init__(self, right_arg=None, **kwargs):
        print(f"Right2.__init__(right_arg={right_arg})")
        super().__init__(**kwargs)

class Bottom2(Left2, Right2):
    def __init__(self, **kwargs):
        print("Bottom2.__init__")
        super().__init__(**kwargs)

print("\n--- 参数传递：每个类吃掉自己的参数 ---")
Bottom2(left_arg=1, right_arg=2)


# ══════════════════════════════════════════════════════════════════════
# 6. Mixin 模式
# ══════════════════════════════════════════════════════════════════════

class LoggingMixin:
    """给类加上方法调用日志能力"""
    def _log(self, method_name, *args, **kwargs):
        print(f"[{time.strftime('%H:%M:%S')}] "
              f"{self.__class__.__name__}.{method_name}({args}, {kwargs})")


class SerializableMixin:
    """给类加上 JSON 序列化能力"""
    def to_json(self) -> str:
        data = {k: v for k, v in self.__dict__.items()
                if not k.startswith('_')}
        return json.dumps(data, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)


class User(LoggingMixin, SerializableMixin):
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def greet(self):
        self._log("greet")
        return f"Hello, I'm {self.name}"

print("\n--- Mixin 示例 ---")
u = User("Alice", 30)
print(u.greet())
print("JSON:", u.to_json())

u2 = User.from_json('{"name": "Bob", "age": 25}')
print(f"复原: {u2.name}, {u2.age}")


# ══════════════════════════════════════════════════════════════════════
# 7. issubclass() 与 isinstance()
# ══════════════════════════════════════════════════════════════════════

class Animal: pass
class Dog(Animal): pass
class Robot: pass

d = Dog()
print("\n--- isinstance / issubclass ---")
print(f"isinstance(d, Dog):     {isinstance(d, Dog)}")
print(f"isinstance(d, Animal):  {isinstance(d, Animal)}")
print(f"isinstance(d, Robot):   {isinstance(d, Robot)}")
print(f"issubclass(Dog, Animal):{issubclass(Dog, Animal)}")
print(f"issubclass(Dog, Dog):   {issubclass(Dog, Dog)}")


# ══════════════════════════════════════════════════════════════════════
# 8. ABC 抽象基类
# ══════════════════════════════════════════════════════════════════════

class AnimalABC(ABC):
    @abstractmethod
    def speak(self) -> str:
        """子类必须实现"""
        ...

class DogABC(AnimalABC):
    def speak(self) -> str:
        return "Woof!"

class CatABC(AnimalABC):
    pass                          # ← 没实现 speak()，也是抽象的

print("\n--- ABC ---")
dog = DogABC()
print(f"Dog speaks: {dog.speak()}")

try:
    cat = CatABC()                # 不能实例化
except TypeError as e:
    print(f"CatABC 实例化失败: {e}")

try:
    a = AnimalABC()               # 同样不能
except TypeError as e:
    print(f"AnimalABC 实例化失败: {e}")


# ══════════════════════════════════════════════════════════════════════
# 9. ABC.register() — 虚拟子类
# ══════════════════════════════════════════════════════════════════════

class Flyable(ABC):
    @abstractmethod
    def fly(self) -> str: ...

class Bird:
    def fly(self) -> str:
        return "飞起来了"

Flyable.register(Bird)             # 不需要继承

print("\n--- 虚拟子类 ---")
print(f"issubclass(Bird, Flyable):  {issubclass(Bird, Flyable)}")
print(f"isinstance(Bird(), Flyable):{isinstance(Bird(), Flyable)}")


# ══════════════════════════════════════════════════════════════════════
# 10. 模板方法模式：ABC 定义骨架，子类填空
# ══════════════════════════════════════════════════════════════════════

class DataProcessor(ABC):
    @abstractmethod
    def process(self, data: list) -> list: ...

    @abstractmethod
    def validate(self, data: list) -> bool: ...

    def run(self, data: list) -> list:
        """模板方法：算法骨架由 ABC 控制"""
        if not self.validate(data):
            raise ValueError("数据校验失败")
        return self.process(data)

class NoOpProcessor(DataProcessor):
    def validate(self, data: list) -> bool:
        return True

    def process(self, data: list) -> list:
        return data

print("\n--- 模板方法 ---")
proc = NoOpProcessor()
print(f"run([1,2,3]): {proc.run([1, 2, 3])}")


# ══════════════════════════════════════════════════════════════════════
# 11. C3 失败的例子
# ══════════════════════════════════════════════════════════════════════

class X: pass
class Y: pass
class AX(X, Y): pass              # MRO: AX, X, Y, object
class BY(Y, X): pass              # MRO: BY, Y, X, object

print("\n--- C3 冲突 ---")
try:
    class Impossible(AX, BY):
        pass
except TypeError as e:
    print(f"TypeError: {e}")
