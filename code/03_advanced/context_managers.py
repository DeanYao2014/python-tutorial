# 3.3 上下文管理器深度 —— 代码示例 (Python 3.12+)
"""
涵盖：
- with 语句脱糖模式 (mgr, __enter__, __exit__)
- 类实现：file-like, 数据库事务, Timer
- __exit__ 返回值：True 吞异常，False/None 传播
- @contextmanager 装饰器：生成器 → 上下文管理器
- ExitStack：动态管理多个上下文管理器
- suppress()、redirect_stdout()、redirect_stderr()
- 异步上下文管理器：__aenter__/__aexit__
- @asynccontextmanager
- 嵌套 with vs ExitStack 对比
"""

import sys
import time
from contextlib import contextmanager, ExitStack, suppress, redirect_stdout, redirect_stderr
from contextlib import asynccontextmanager
import io
import asyncio


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. with 语句脱糖
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_with_desugaring():
    """展示 with EXPR as VAR: BODY 的完整展开"""
    print("标准 with 写法:")

    # with open("test.txt", "w") as f:
    #     f.write("hello")
    #
    # 等价于：
    mgr = open("_test_with.txt", "w")
    f = mgr.__enter__()                         # 获取资源
    exc_type, exc_val, exc_tb = None, None, None
    try:
        f.write("hello from with desugaring")
        # 正常退出时执行 __exit__(None, None, None)
    except:
        exc_type, exc_val, exc_tb = sys.exc_info()
        # 异常分支：__exit__ 返回 True → 吞异常；返回 False/None → 重新抛
        if not mgr.__exit__(exc_type, exc_val, exc_tb):
            raise
    else:
        # 无异常分支：正常清理
        mgr.__exit__(None, None, None)
    finally:
        # 确保文件已关闭（实际 with 语句的清理在 __exit__ 中完成）
        pass

    print(f"  文件 {f.name!r} 已写入并关闭")
    print(f"  f.closed = {f.closed}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 类实现上下文管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class FileLike:
    """自定义文件操作的上下文管理器——展示 __enter__ + __exit__"""
    def __init__(self, filename: str, mode: str = "r"):
        self.filename = filename
        self.mode = mode
        self._file = None

    def __enter__(self):
        print(f"  [FileLike] 打开 {self.filename!r}")
        self._file = open(self.filename, self.mode)
        return self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"  [FileLike] 关闭 {self.filename!r}")
        if self._file:
            self._file.close()
        return False  # 不吞异常——让调用者看到


def demo_file_like():
    with FileLike("_test_filelike.txt", "w") as f:
        f.write("Hello from FileLike")
    print("  文件自动关闭")


class Transaction:
    """模拟数据库事务的上下文管理器"""
    def __init__(self, db_name: str):
        self.db_name = db_name
        self._committed = False

    def __enter__(self):
        print(f"  [TX] BEGIN — {self.db_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 无异常 → 提交
            print(f"  [TX] COMMIT — {self.db_name}")
            self._committed = True
        else:
            # 有异常 → 回滚
            print(f"  [TX] ROLLBACK — {self.db_name} (异常: {exc_type.__name__})")
        return False  # 传播异常


def demo_transaction():
    # 正常提交
    with Transaction("orders_db") as tx:
        print("    插入订单 1")
        print("    插入订单 2")
        # 无异常 → 自动 COMMIT

    print()

    # 异常回滚
    try:
        with Transaction("orders_db") as tx:
            print("    插入订单 1")
            raise ValueError("库存不足")
    except ValueError as e:
        print(f"  调用者收到异常: {e}")


class Timer:
    """计时代码块执行的上下文管理器"""
    def __init__(self, label: str = ""):
        self.label = label

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.perf_counter() - self.start
        tag = f"[{self.label}] " if self.label else ""
        print(f"  {tag}耗时: {elapsed:.6f}s")
        return False


def demo_timer():
    with Timer("计算"):
        total = sum(range(10_000_000))

    # Timer 也支持手动取值
    with Timer() as t:
        total = sum(range(5_000_000))
    print(f"  可通过 t.start 获取起始时间: {t.start:.2f}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. __exit__ 返回值：True 吞掉异常
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SuppressKeyError:
    """演示 __exit__ 返回 True 吞异常"""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is KeyError:
            print(f"  [SuppressKeyError] 吞掉 KeyError: {exc_val}")
            return True                      # True = 异常已处理，别传播
        return False                         # False/None = 继续传播


def demo_exit_return():
    print("正常执行:")
    with SuppressKeyError():
        print("    一切正常")
    # __exit__(None, None, None) → 返回 False → 无影响

    print("\nKeyError 被吞:")
    with SuppressKeyError():
        d = {}
        print(d["不存在的键"])                # KeyError → __exit__ 返回 True → 吞掉
    print("    异常被吞，代码继续运行")

    print("\nValueError 仍然传播:")
    try:
        with SuppressKeyError():
            raise ValueError("不是 KeyError 哦")
    except ValueError as e:
        print(f"    调用者收到: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. @contextmanager —— 生成器实现上下文管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@contextmanager
def managed_file(filename: str, mode: str = "r"):
    """生成器版 FileLike —— yield 之前的代码 = __enter__，
       yield 之后的代码 = __exit__"""
    print(f"  [managed] 打开 {filename!r}")
    f = open(filename, mode)
    try:
        yield f                                  # 把资源交给 with 块
    finally:
        print(f"  [managed] 关闭 {filename!r}")
        f.close()


def demo_contextmanager():
    with managed_file("_test_managed.txt", "w") as f:
        f.write("来自 @contextmanager 的问候")
    print("  done")

    # 等价于上面的类实现，但代码量减半
    # yield 之前 → 对应 __enter__
    # yield 之后 → 对应 __exit__（必须用 try/finally 确保清理）


@contextmanager
def managed_transaction(db_name: str):
    """生成器版事务管理——展示异常时的行为差异"""
    print(f"  [TX] BEGIN — {db_name}")
    try:
        yield db_name                            # 正常执行点
        print(f"  [TX] COMMIT — {db_name}")
    except Exception:
        print(f"  [TX] ROLLBACK — {db_name}")
        raise                                    # 重新抛出让调用者知道


def demo_contextmanager_tx():
    with managed_transaction("users_db") as db:
        print(f"    操作 {db}")

    print()
    try:
        with managed_transaction("users_db") as db:
            raise RuntimeError("连接断开")
    except RuntimeError as e:
        print(f"  调用者收到: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. ExitStack：动态管理多个上下文管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_exit_stack():
    """ExitStack 示例：程序运行时才知道要打开多少个文件"""
    files_to_open = ["_stack_a.txt", "_stack_b.txt", "_stack_c.txt"]

    with ExitStack() as stack:
        opened_files = []
        for name in files_to_open:
            f = stack.enter_context(open(name, "w"))
            opened_files.append(f)
            f.write(f"Content of {name}\n")
            print(f"  已进入: {name}")
        print(f"  共打开 {len(opened_files)} 个文件")

    # ExitStack.__exit__ 会按 LIFO 顺序关闭所有已进入的上下文
    print("  所有文件已自动关闭")
    for f in opened_files:
        print(f"  {f.name}: closed={f.closed}")


def demo_exit_stack_callback():
    """ExitStack.callback —— 注册任意清理函数（不等价于上下文管理器）"""
    with ExitStack() as stack:
        # 注册清理回调（按注册的逆序执行）
        stack.callback(print, "  清理 3: 最后注册，最先执行")
        stack.callback(print, "  清理 2")
        stack.callback(print, "  清理 1: 最先注册，最后执行")
        print("  正在处理...")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. suppress() 和 redirect_stdout/stderr
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_suppress():
    """suppress() —— 优雅地忽略特定异常"""
    # 传统写法：
    # try:
    #     os.remove("不存在的文件.txt")
    # except FileNotFoundError:
    #     pass

    from contextlib import suppress
    import os

    with suppress(FileNotFoundError):
        os.remove("这个文件绝对不存在.txt")      # 不报错，静默跳过
    print("  文件删除被优雅忽略（文件不存在）")

    # suppress 等价于 try/except ... pass，但更声明式
    # 支持多个异常类型：suppress(ValueError, TypeError)


def demo_redirect():
    """redirect_stdout / redirect_stderr —— 捕获输出"""
    buf = io.StringIO()
    with redirect_stdout(buf):
        print("这条输出被重定向了")
        print("不再在终端显示")

    captured = buf.getvalue()
    print(f"  捕获到的输出: {captured!r}")

    # redirect_stderr 同理
    err_buf = io.StringIO()
    with redirect_stderr(err_buf):
        import sys as _sys
        _sys.stderr.write("stderr 也被捕获\n")
    print(f"  捕获到的 stderr: {err_buf.getvalue()!r}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. 异步上下文管理器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AsyncDatabase:
    """模拟异步数据库连接——__aenter__ / __aexit__"""

    def __init__(self, dsn: str):
        self.dsn = dsn
        self._connected = False

    async def __aenter__(self):
        print(f"  [async DB] 连接 {self.dsn} ...")
        await asyncio.sleep(0.01)                # 模拟异步连接
        self._connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print(f"  [async DB] 断开 {self.dsn} ...")
        await asyncio.sleep(0.01)
        self._connected = False
        return False

    async def execute(self, sql: str):
        print(f"  [async DB] 执行: {sql}")
        await asyncio.sleep(0.01)


async def demo_async_cm():
    async with AsyncDatabase("postgresql://localhost/test") as db:
        await db.execute("SELECT 1")
    print("  异步连接已自动关闭")


class AsyncLock:
    """简化版异步锁——展示资源获取/释放的异步上下文管理器"""
    def __init__(self):
        self._locked = False

    async def __aenter__(self):
        self._locked = True
        print(f"  [Lock] 获取")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._locked = False
        print(f"  [Lock] 释放")
        return False


@asynccontextmanager
async def managed_async_resource(name: str):
    """@asynccontextmanager 实现异步上下文管理器"""
    print(f"  [managed async] 获取 {name}")
    await asyncio.sleep(0.01)
    try:
        yield name
    finally:
        print(f"  [managed async] 释放 {name}")
        await asyncio.sleep(0.01)


async def demo_async_contextmanager():
    """@asynccontextmanager 用法"""
    async with managed_async_resource("session-42") as resource:
        print(f"    使用 {resource}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. 嵌套 with vs ExitStack
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def demo_nested_vs_exitstack():
    """嵌套 with vs ExitStack —— 场景对比"""

    # 方式 1：嵌套 with（资源数量已知）
    print("=== 嵌套 with（静态）===")
    with open("_a.txt", "w") as f1:
        with open("_b.txt", "w") as f2:
            f1.write("hello")
            f2.write("world")
    print("  两个文件都已关闭\n")

    # 方式 2：单行多上下文（Python 3.1+）
    print("=== 单行多上下文 ===")
    with (
        open("_a.txt", "w") as f1,
        open("_b.txt", "w") as f2,
        open("_c.txt", "w") as f3,
    ):
        f1.write("1")
        f2.write("2")
        f3.write("3")
    print("  三个文件都已关闭\n")

    # 方式 3：ExitStack（资源数量运行时才知道）
    print("=== ExitStack（动态）===")
    filenames = ["_d1.txt", "_d2.txt", "_d3.txt"]
    with ExitStack() as stack:
        files = [stack.enter_context(open(n, "w")) for n in filenames]
        for i, f in enumerate(files):
            f.write(f"file {i}")
        print(f"  动态打开了 {len(files)} 个文件")
    print("  所有文件都已关闭")


def demo_exitstack_vs_nested_decision():
    """决策指南：何时用哪种"""
    print("""
    选择 ExitStack 的场景：
      - 上下文管理器数量在运行时才确定
      - 需要条件性地进入/退出一部分上下文
      - 需要组合多个不同类型的清理逻辑

    选择嵌套 with 的场景：
      - 上下文管理器数量固定、编译时就清楚
      - 代码可读性优先（嵌套直观）

    选择单行 with 的场景：
      - Python 3.10+、多个同类型资源、不想缩进地狱
    """)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. 简化实现：@contextmanager 的核心原理
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SimpleContextManager:
    """@contextmanager 装饰器的简化实现（约 40 行）

    原理：
    1. 把被装饰的生成器函数变成 __enter__ / __exit__
    2. __enter__ 启动生成器到第一个 yield，返回 yield 的值
    3. __exit__ 调用 next()（正常）或 throw()（异常）继续生成器
    """
    def __init__(self, gen_func):
        self.gen_func = gen_func
        self.gen = None

    def __call__(self, *args, **kwargs):
        return SimpleContextManager(self.gen_func(*args, **kwargs))

    def __enter__(self):
        if hasattr(self.gen_func, '__call__') and not isinstance(self.gen_func, GeneratorType):
            raise TypeError("需要 (self, *args, **kwargs) 模式时请先实例化")
        self.gen = self.gen_func
        return next(self.gen)                    # 执行到 yield → 返回资源

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # 正常退出：继续执行生成器（yield 之后的部分）
            try:
                next(self.gen)
            except StopIteration:
                return False                     # 生成器正常结束
            else:
                raise RuntimeError("generator didn't stop")
        else:
            # 异常退出：把异常注入生成器
            try:
                self.gen.throw(exc_type, exc_val, exc_tb)
            except StopIteration:
                return True                      # 生成器捕获并处理了异常
            except Exception as e:
                if e is exc_val:
                    return False                 # 异常被重新抛出 → 不吞
                raise
        return False


def demo_simple_contextmanager():
    """验证简化版 @contextmanager"""
    @SimpleContextManager
    def temp_value(new_val):
        """临时替换全局变量，退出时恢复"""
        import builtins
        old = builtins.__dict__.get('_test_var')
        builtins.__dict__['_test_var'] = new_val
        yield new_val
        builtins.__dict__['_test_var'] = old

    with temp_value(42) as val:
        print(f"  with 块内: {val}")
    print("  done")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 入口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    print("=" * 60)
    print("1. with 脱糖")
    print("=" * 60)
    demo_with_desugaring()

    print("\n" + "=" * 60)
    print("2. 类实现：FileLike")
    print("=" * 60)
    demo_file_like()

    print("\n" + "=" * 60)
    print("3. 类实现：Transaction")
    print("=" * 60)
    demo_transaction()

    print("\n" + "=" * 60)
    print("4. 类实现：Timer")
    print("=" * 60)
    demo_timer()

    print("\n" + "=" * 60)
    print("5. __exit__ 返回值：吞异常 vs 传播")
    print("=" * 60)
    demo_exit_return()

    print("\n" + "=" * 60)
    print("6. @contextmanager 生成器版上下文管理器")
    print("=" * 60)
    demo_contextmanager()

    print("\n" + "=" * 60)
    print("7. @contextmanager 事务管理")
    print("=" * 60)
    demo_contextmanager_tx()

    print("\n" + "=" * 60)
    print("8. ExitStack 动态管理")
    print("=" * 60)
    demo_exit_stack()

    print("\n" + "=" * 60)
    print("9. ExitStack.callback")
    print("=" * 60)
    demo_exit_stack_callback()

    print("\n" + "=" * 60)
    print("10. suppress() 和 redirect")
    print("=" * 60)
    demo_suppress()
    demo_redirect()

    print("\n" + "=" * 60)
    print("11. 异步上下文管理器")
    print("=" * 60)
    asyncio.run(demo_async_cm())

    print("\n" + "=" * 60)
    print("12. @asynccontextmanager")
    print("=" * 60)
    asyncio.run(demo_async_contextmanager())

    print("\n" + "=" * 60)
    print("13. 嵌套 with vs ExitStack")
    print("=" * 60)
    demo_nested_vs_exitstack()
    demo_exitstack_vs_nested_decision()

    print("=" * 60)
    print("14. 简化实现：@contextmanager")
    print("=" * 60)
    demo_simple_contextmanager()
