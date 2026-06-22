"""2.8 元类实战：完整可运行示例
===================================
覆盖 __init_subclass__、__set_name__、元类实践、决策树。
每段代码独立可运行，可直接复制到交互环境测试。

运行方式:
    python metaclasses_practice.py
"""

# ============================================================
# Part A: __init_subclass__  —— 覆盖 90% 元类场景的替代品
# ============================================================

def demo_plugin_registry():
    """场景 A1：插件自动注册 —— 子类定义即注册"""

    class Plugin:
        """插件基类——子类自动注册到 _plugins"""
        _plugins: dict[str, type["Plugin"]] = {}

        def __init_subclass__(cls, **kwargs):
            """子类定义时自动调用——父类的 __init_subclass__"""
            super().__init_subclass__(**kwargs)
            name = getattr(cls, "plugin_name", cls.__name__)
            if name in cls._plugins:
                raise TypeError(f"插件名 '{name}' 已被注册")
            cls._plugins[name] = cls

        @classmethod
        def get(cls, name: str) -> type["Plugin"] | None:
            return cls._plugins.get(name)

    class TextParser(Plugin):
        plugin_name = "text"

        def parse(self, data: str) -> list[str]:
            return data.split()

    class JsonParser(Plugin):
        plugin_name = "json"

        def parse(self, data: str) -> list[str]:
            import json
            return list(json.loads(data).keys())

    # 验证：无需手动注册，子类定义即注册
    print("已注册插件:", list(Plugin._plugins.keys()))
    parser = Plugin.get("json")
    if parser is not None:
        p = parser()
        result = p.parse('{"name": "Alice", "age": 30}')
        print(f"JSON 解析结果: {result}")


def demo_subclass_constraints():
    """场景 A2：强制子类约束 —— 必须定义某些属性"""

    class Animal:
        required_attrs: tuple[str, ...] = ("sound",)

        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            for attr in cls.required_attrs:
                if not hasattr(cls, attr) or getattr(cls, attr) is None:
                    raise TypeError(
                        f"{cls.__name__} 必须定义类属性 '{attr}'"
                    )

    class Dog(Animal):
        sound = "汪汪"

    dog = Dog()
    print(f"Dog.sound = {dog.sound}")

    # 验证约束生效
    try:
        class Cat(Animal):        # 没有定义 sound
            pass
    except TypeError as e:
        print(f"约束生效: {e}")


# ============================================================
# Part B: __set_name__  —— 描述符知道自己叫什么名字
# ============================================================

class Validated:
    """带校验的描述符 —— 通过 __set_name__ 获取字段名
    职责：类型检查 + 自我感知
    """
    def __init__(self, expected_type: type):
        self.expected_type = expected_type
        self.name: str | None = None         # __set_name__ 填入
        self.storage_name: str | None = None # 实际在实例上存储的属性名

    def __set_name__(self, owner: type, name: str):
        """类创建完成后，Python 自动调用此方法"""
        self.name = name
        self.storage_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        if obj is None:              # 类级别访问：返回描述符本身
            return self
        return getattr(obj, self.storage_name)

    def __set__(self, obj, value):
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} 期望 {self.expected_type.__name__}，"
                f"实际是 {type(value).__name__}"
            )
        setattr(obj, self.storage_name, value)


class Person:
    """使用 Validated 描述符的数据类"""
    name = Validated(str)
    age = Validated(int)

    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def __repr__(self):
        return f"Person(name={self.name!r}, age={self.age})"


def demo_set_name():
    """展示 __set_name__ 如何让描述符获得字段名"""
    p = Person("Alice", 30)
    print(p)

    # 类型校验生效
    try:
        p.age = "not a number"
    except TypeError as e:
        print(f"校验生效: {e}")

    # 类级别访问：返回描述符对象
    print(f"类级别访问 Person.name: {Person.name!r}")


# ============================================================
# Part C: 元类实战 —— 真正需要修改类创建过程的场景
# ============================================================

# --- C1: 简易 ORM 元类 ---

class ModelMeta(type):
    """ORM 元类：自动收集字段、生成表名
    这是元类的'经典'用法——Django、SQLAlchemy 都在用。
    """
    def __new__(mcs, name, bases, namespace):
        # 收集当前类中所有非私有的非可调用属性作为"数据库字段"
        fields = {
            k: v for k, v in namespace.items()
            if not k.startswith('_') and not callable(v)
        }
        namespace['_fields'] = fields

        # 自动生成表名：类名小写 + s
        if 'table_name' not in namespace:
            namespace['table_name'] = name.lower() + 's'

        return super().__new__(mcs, name, bases, namespace)


class Model(metaclass=ModelMeta):
    """ORM 基类"""
    _fields: dict = {}
    table_name: str = ""

    def save(self):
        columns = ', '.join(self._fields.keys())
        placeholders = ', '.join('?' for _ in self._fields)
        values = [getattr(self, f) for f in self._fields]
        sql = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        print(f"SQL: {sql}")
        print(f"参数: {values}")


class User(Model):
    name = ""
    age = 0
    email = ""


class Product(Model):
    title = ""
    price = 0.0


def demo_orm_metaclass():
    """展示 ORM 元类如何自动收集字段和生成表名"""
    print(f"{'模型':<10} {'表名':<12} {'字段'}")
    print("-" * 45)
    for model_cls in [User, Product]:
        print(f"{model_cls.__name__:<10} {model_cls.table_name:<12} {model_cls._fields}")

    u = User()
    u.name, u.age, u.email = "Bob", 25, "bob@test.com"
    u.save()


# --- C2: 注册表元类 ---

class RegistryMeta(type):
    """元类注册表：类定义时自动注册到中央字典"""
    _registry: dict[str, type] = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:  # 跳过基类自身，只注册子类
            mcs._registry[name] = cls
        return cls


class Command(metaclass=RegistryMeta):
    """命令基类——所有命令自动注册"""

    def execute(self) -> str:
        raise NotImplementedError


class SaveCommand(Command):
    def execute(self) -> str:
        return "保存文件"


class OpenCommand(Command):
    def execute(self) -> str:
        return "打开文件"


def demo_registry_metaclass():
    """展示元类注册表模式"""
    print(f"已注册命令: {list(RegistryMeta._registry.keys())}")

    for name, cmd_cls in RegistryMeta._registry.items():
        cmd = cmd_cls()
        print(f"  {name}.execute() → {cmd.execute()}")


# --- C3: Singleton 元类（模块就够用了） ---

class SingletonMeta(type):
    """单例元类——但通常你不需要它"""
    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        """拦截实例化调用，返回已缓存的实例"""
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class AppConfig(metaclass=SingletonMeta):
    """应用配置——全局唯一实例"""
    def __init__(self):
        self.database_url: str = "sqlite:///:memory:"
        self.debug: bool = True

    def __repr__(self):
        return (f"AppConfig(database_url={self.database_url!r}, "
                f"debug={self.debug})")


def demo_singleton():
    """展示 Singleton 元类，同时说明为什么模块就够了"""
    a = AppConfig()
    b = AppConfig()
    print(f"a is b: {a is b}")
    a.database_url = "postgresql://prod"
    print(f"修改 a 后, b.database_url = {b.database_url}")
    print()

    # 对比：模块级单例（Python 推荐方式）
    print("模块单例等价写法（推荐）:")
    print("  # config.py")
    print("  class _Config: ...")
    print("  config = _Config()  # 模块加载时创建一次")
    print("  # 其他文件: from config import config")


# ============================================================
# Part D: 决策树演示 —— 什么时候该用什么工具
# ============================================================

def demo_decision_tree():
    """对比类装饰器、__init_subclass__、元类三种方案"""

    # 方案一：类装饰器 —— 最简单
    def add_created_at(cls):
        cls.created_at = "2024-01-01"
        return cls

    @add_created_at
    class MyClass:
        pass

    print(f"类装饰器方案: MyClass.created_at = {MyClass.created_at}")

    # 方案二：__init_subclass__ —— 需要跨子类自动化
    class Base:
        def __init_subclass__(cls, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.created_at = "2024-01-01"

    class MySub(Base):
        pass

    print(f"__init_subclass__ 方案: MySub.created_at = {MySub.created_at}")

    # 方案三：元类 —— 需要修改创建前的命名空间
    class Meta(type):
        def __new__(mcs, name, bases, namespace):
            namespace['created_at'] = "2024-01-01"
            return super().__new__(mcs, name, bases, namespace)

    class MyClassWithMeta(metaclass=Meta):
        pass

    print(f"元类方案: MyClassWithMeta.created_at = {MyClassWithMeta.created_at}")


# ============================================================
# 主程序入口
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("2.8 元类实战 —— 完整示例")
    print("=" * 55)

    print("\n── Part A1: 插件自动注册 ──")
    demo_plugin_registry()

    print("\n── Part A2: 子类约束 ──")
    demo_subclass_constraints()

    print("\n── Part B: __set_name__ 描述符 ──")
    demo_set_name()

    print("\n── Part C1: ORM 元类 ──")
    demo_orm_metaclass()

    print("\n── Part C2: 注册表元类 ──")
    demo_registry_metaclass()

    print("\n── Part C3: Singleton 元类 ──")
    demo_singleton()

    print("\n── Part D: 三方案对比 ──")
    demo_decision_tree()
