"""2.7 简化实现：MiniPydantic —— 50行展示 BaseModel 核心原理

展示三个关键机制：
1. __init_subclass__ 收集类型注解
2. 自动生成 __init__（通过 __new__ 控制实例化）
3. 基础校验（类型强制转换）
"""

from typing import get_type_hints, Any


class ValidationError(Exception):
    """校验错误"""
    pass


class MiniModel:
    """MiniPydantic 的基类——展示 BaseModel 核心原理"""
    __fields__: dict[str, type] = {}

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """1. 子类定义时自动收集类型注解 → __fields__"""
        super().__init_subclass__(**kwargs)
        # 收集当前类及所有父类的 annotations
        hints = get_type_hints(cls)
        # 过滤掉内置字段
        cls.__fields__ = {
            name: typ
            for name, typ in hints.items()
            if not name.startswith('_')
        }

    def __init__(self, **kwargs: Any) -> None:
        """2. 自动校验 + 赋值"""
        for field_name, field_type in self.__fields__.items():
            if field_name in kwargs:
                value = kwargs[field_name]
                # 简易校验：尝试类型转换（不强求精确匹配）
                if not isinstance(value, field_type):
                    try:
                        value = field_type(value)
                    except (ValueError, TypeError):
                        raise ValidationError(
                            f"字段 {field_name} 期望 {field_type.__name__}，"
                            f"收到了 {type(value).__name__}: {value}"
                        )
                setattr(self, field_name, value)
            else:
                raise ValidationError(f"缺少必填字段: {field_name}")

    def __repr__(self) -> str:
        fields = ', '.join(
            f"{name}={getattr(self, name)!r}"
            for name in self.__fields__
        )
        return f"{type(self).__name__}({fields})"


# ── 使用 MiniPydantic ──
if __name__ == '__main__':
    class User(MiniModel):
        name: str
        age: int
        email: str = "unknown@example.com"

    # 正常创建
    u = User(name="Alice", age=30)
    print(u)  # User(name='Alice', age=30, email='unknown@example.com')

    # 类型自动转换
    u2 = User(name="Bob", age="25")  # "25" → 25
    print(f"age 类型: {type(u2.age).__name__}")  # int

    # 校验失败
    try:
        User(name="Eve", age="not a number")
    except ValidationError as e:
        print(f"校验失败: {e}")
