"""
Chapter 3.8: 元编程 — 代码示例
覆盖 exec/eval/compile, type(), inspect, AST, 实际应用
"""

import functools

# ============================================================
# Part 1: exec / eval / compile
# ============================================================

# --- 1.1 exec: 执行动态代码块 ---

namespace = {}
code = """
def greet(name):
    return f"Hello, {name}!"

message = greet("World")
"""
exec(code, namespace)
print(f"=== exec ===\n{namespace['message']}\n")


# --- 1.2 eval: 求值单个表达式 ---

result = eval("3 ** 4 + 2 * 5", {"__builtins__": {}})
print(f"=== eval ===\n3**4 + 2*5 = {result}\n")

# eval 只能处理表达式, 不能处理语句
# eval("x = 1")  # SyntaxError


# --- 1.3 compile: 编译为代码对象 ---

src = "x + y"
code_obj = compile(src, "<string>", "eval")
print(f"=== compile ===\ncompile('x+y'): {code_obj.co_name}, {code_obj.co_code}\n")

# 三种模式:
# 'exec': 多行代码块
# 'eval': 单个表达式
# 'single': 交互式单条语句

block = compile("a=1\nb=2\nprint(a+b)", "<dynamic>", "exec")
print("exec 模式运行:")
exec(block)
print()


# --- 1.4 安全: 限制 builtins 命名空间 ---

safe_globals = {"__builtins__": {"abs": abs, "min": min, "max": max}}
try:
    eval("open('/etc/passwd')", safe_globals)
except NameError as e:
    print(f"=== 安全限制 ===\n受限命名空间: {e}\n")


# ============================================================
# Part 2: type() 动态创建类
# ============================================================

# --- 2.1 type(name, bases, namespace) 三参数用法 ---

Dog = type("Dog", (object,), {
    "species": "Canis familiaris",
    "__init__": lambda self, name: setattr(self, "name", name),
    "bark": lambda self: f"{self.name} says woof!",
})

d = Dog("Buddy")
print(f"=== type()动态创建类 ===\n{d.bark()}, species={d.species}")

# 等价于:
# class Dog:
#     species = "Canis familiaris"
#     def __init__(self, name): self.name = name
#     def bark(self): return f"{self.name} says woof!"
print()


# --- 2.2 动态 ORM 模型 ---

def create_model(table_name: str, **fields):
    """根据 schema 动态创建数据模型类"""
    def __init__(self, **kwargs):
        for k, v in fields.items():
            setattr(self, k, kwargs.get(k, v))
    def __repr__(self):
        parts = ", ".join(f"{k}={getattr(self, k)!r}" for k in fields)
        return f"{table_name}({parts})"
    namespace = {
        "_table": table_name,
        "_fields": fields,
        "__init__": __init__,
        "__repr__": __repr__,
    }
    return type(table_name, (object,), namespace)

User = create_model("User", name="", age=0, email="")
u = User(name="Alice", age=30)
print(f"=== 动态ORM模型 ===\n{u}")
print(f"User._table = {User._table}")
print(f"User._fields = {User._fields}")
print()


# ============================================================
# Part 3: inspect 模块
# ============================================================

import inspect

# --- 3.1 inspect.signature: 获取函数签名 ---

def connect(host: str, port: int = 5432, *, timeout: float = 30.0):
    """建立数据库连接"""
    pass

sig = inspect.signature(connect)
print("=== inspect.signature ===")
for name, param in sig.parameters.items():
    print(f"  {name}: kind={param.kind.name}, "
          f"default={param.default}, "
          f"annotation={param.annotation}")
print()


# --- 3.2 inspect.getsource: 获取函数源码 ---

src = inspect.getsource(connect)
print(f"=== inspect.getsource ===\n{src}")


# --- 3.3 inspect.getmembers: 遍历对象成员 ---

members = inspect.getmembers(Dog, predicate=inspect.isfunction)
print(f"=== inspect.getmembers(Dog) ===\nDog 的方法: {[n for n, _ in members]}")
print()


# --- 3.4 实战: 自动生成 API 文档 ---

def auto_doc(func):
    """从类型注解自动生成文档字符串"""
    sig = inspect.signature(func)
    params = []
    for name, param in sig.parameters.items():
        annot = param.annotation if param.annotation is not param.empty else "Any"
        default = f" = {param.default}" if param.default is not param.empty else ""
        params.append(f"    {name}: {annot.__name__ if hasattr(annot, '__name__') else str(annot)}{default}")
    return (
        f"def {func.__name__}{sig}:\n"
        f"    {func.__doc__ or '无文档'}\n\n"
        f"参数:\n"
        + "\n".join(params)
    )

print(f"=== 自动文档 ===\n{auto_doc(connect)}")


# ============================================================
# Part 4: AST (Abstract Syntax Tree)
# ============================================================

import ast

# --- 4.1 ast.parse: 解析为 AST ---

source = """
def greet(name):
    message = f"Hello, {name}!"
    print(message)
"""
tree = ast.parse(source)
print(f"=== ast.parse ===\nast.dump 前 500 字符:\n{ast.dump(tree, indent=2)[:500]}\n...")


# --- 4.2 遍历 AST 节点 ---

class VariableCollector(ast.NodeVisitor):
    """收集所有变量名"""
    def __init__(self):
        self.variables = set()

    def visit_Name(self, node):
        self.variables.add(node.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.variables.add(node.name)
        self.generic_visit(node)

vc = VariableCollector()
vc.visit(tree)
print(f"=== AST 节点遍历 ===\n变量: {vc.variables}")
print()


# --- 4.3 ast.NodeTransformer: 转换 AST ---

class AddPrintTransformer(ast.NodeTransformer):
    """在每个函数体开头插入 print 语句"""
    def visit_FunctionDef(self, node):
        print_call = ast.Expr(
            value=ast.Call(
                func=ast.Name(id="print", ctx=ast.Load()),
                args=[ast.Constant(value=f"进入 {node.name}")],
                keywords=[],
            )
        )
        node.body.insert(0, print_call)
        return node

source2 = """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
tree2 = ast.parse(source2)
transformer = AddPrintTransformer()
tree2 = transformer.visit(tree2)
ast.fix_missing_locations(tree2)
transformed_code = compile(tree2, "<transformed>", "exec")
print("=== AST 转换: 注入 print ===")
exec(transformed_code)
print()


# --- 4.4 实战: 简单代码规则检测器 ---

class ForbiddenPatternDetector(ast.NodeVisitor):
    """检测不推荐的代码模式"""
    def __init__(self):
        self.issues = []

    def visit_Call(self, node):
        # 检测 eval/exec 调用
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self.issues.append(
                f"行{node.lineno}: 使用了 {node.func.id}() —— 请确认无安全风险"
            )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node):
        # 检测裸 except
        if node.type is None:
            self.issues.append(f"行{node.lineno}: 裸 except —— 请指定具体异常类型")
        self.generic_visit(node)

check_source = """
def dangerous(data):
    try:
        result = eval(data)  # 风险
    except:                  # 裸except
        pass
    return result
"""

check_tree = ast.parse(check_source)
detector = ForbiddenPatternDetector()
detector.visit(check_tree)
print("=== 代码规则检测器 ===")
for issue in detector.issues:
    print(f"  {issue}")
print()


# ============================================================
# Part 5: 实际应用场景
# ============================================================

# --- 5.1 简易模板引擎: 编译模板为 Python 代码 ---

import re

def compile_template(template_str: str):
    """将 {{ var }} 模板编译为可执行函数"""
    parts = []
    last = 0
    for match in re.finditer(r"\{\{(.+?)\}\}", template_str):
        parts.append(repr(template_str[last:match.start()]))
        var_name = match.group(1).strip()
        # 通过 _c 字典查找变量
        parts.append(f"str(_c[{var_name!r}])")
        last = match.end()
    parts.append(repr(template_str[last:]))

    code = "def render(_c):\n"
    code += f"    return ''.join([{', '.join(parts)}])\n"

    namespace = {}
    exec(code, namespace)
    return namespace["render"]

# 编译模板并查看生成的 Python 代码
template_str = "Hello, {{ name }}! You have {{ count }} messages."
# 展示编译后的代码 (动态编译的函数没有文件源码)
parts = []
last = 0
for match in re.finditer(r"\{\{(.+?)\}\}", template_str):
    parts.append(repr(template_str[last:match.start()]))
    var_name = match.group(1).strip()
    parts.append(f"str(_c[{var_name!r}])")
    last = match.end()
parts.append(repr(template_str[last:]))
generated = f"def render(_c):\n    return ''.join([{', '.join(parts)}])\n"

template = compile_template(template_str)
result = template({"name": "Dean", "count": 5})
print(f"=== 简易模板引擎 ===\n{result}")
print(f"编译后的 Python 代码:\n{generated}")


# --- 5.2 代码生成: 从 schema 生成模型代码 ---

def generate_model_code(class_name: str, fields: dict) -> str:
    """从字段定义生成 Python 类代码"""
    lines = [f"class {class_name}:", '    """自动生成的模型类"""', ""]
    # __init__
    params = ", ".join(f"{k}: {v} = None" for k, v in fields.items())
    lines.append(f"    def __init__(self, {params}):")
    for k in fields:
        lines.append(f"        self.{k} = {k}")
    lines.append("")
    # __repr__
    parts = ", ".join(f"{k}={{self.{k}!r}}" for k in fields)
    lines.append("    def __repr__(self):")
    lines.append(f'        return f"{class_name}({parts})"')
    return "\n".join(lines)

code = generate_model_code("Book", {"title": "str", "author": "str", "price": "float"})
print(f"\n=== 代码生成 ===\n{code}\n")


# --- 5.3 简单的依赖注入框架 ---

_registry = {}

def inject(**dependencies):
    """通过 inspect.signature 实现依赖注入"""
    def decorator(func):
        sig = inspect.signature(func)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for name, param in sig.parameters.items():
                if name in dependencies and name not in kwargs:
                    kwargs[name] = dependencies[name]()
            return func(*args, **kwargs)
        return wrapper
    return decorator

def create_db():
    return "Database connection"

def create_cache():
    return "Cache connection"

@inject(db=create_db, cache=create_cache)
def handle_request(user_id, db, cache):
    return f"处理 {user_id}: db={db}, cache={cache}"

print(f"=== 依赖注入 ===\n{handle_request(42)}\n")


print("=" * 50)
print("全部示例运行完毕")
