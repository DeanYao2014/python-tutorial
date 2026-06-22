"""3.7 内存管理与性能：完整可运行示例
===============================================
覆盖引用计数、分代GC、weakref、__slots__内存分析、
tracemalloc、dis字节码、性能优化技巧。

运行方式:
    python memory_performance.py
"""

import sys
import gc
import weakref
import time
import dis
import tracemalloc
import functools
from dataclasses import dataclass


# ============================================================
# Part A: 引用计数
# ============================================================

def demo_refcount():
    """sys.getrefcount() 基础 + 引用循环"""
    # ── 基本引用计数 ──
    a = []
    print(f"  a = [] → refcount: {sys.getrefcount(a)}")

    b = a
    print(f"  b = a  → refcount: {sys.getrefcount(a)}")

    c = [a]
    print(f"  c = [a] → refcount: {sys.getrefcount(a)}")

    del b, c
    print(f"  del b, c → refcount: {sys.getrefcount(a)}")

    # ── 循环引用 ──
    class Node:
        def __init__(self, name: str):
            self.name = name
            self.next: "Node | None" = None

    a = Node("A")
    b = Node("B")
    a.next = b
    b.next = a          # 循环引用

    print(f"\n  循环引用: a refs = {sys.getrefcount(a) - 1}"
          f", b refs = {sys.getrefcount(b) - 1}")
    # 打印可到达对象（GC 视角）
    print(f"  GC 可追踪的垃圾: {gc.collect()}")


# ============================================================
# Part B: 分代垃圾回收
# ============================================================

def demo_generational_gc():
    """GC 代、阈值、手动回收"""
    print(f"  GC 启用: {gc.isenabled()}")
    print(f"  默认阈值: {gc.get_threshold()}")

    before = gc.get_count()
    print(f"  回收前计数: gen0={before[0]}, gen1={before[1]}, gen2={before[2]}")

    # 创建一批临时对象，然后丢弃
    for i in range(1000):
        temp = {"data": i, "next": f"value_{i}"}

    during = gc.get_count()
    print(f"  创建对象后: gen0={during[0]}, gen1={during[1]}, gen2={during[2]}")

    # 手动触发所有代的回收
    unreachable = gc.collect()
    after = gc.get_count()
    print(f"  回收 {unreachable} 个对象后: "
          f"gen0={after[0]}, gen1={after[1]}, gen2={after[2]}")

    # 展示阈值调整
    old = gc.get_threshold()
    gc.set_threshold(2000, 15, 15)
    print(f"  调高阈值后: {gc.get_threshold()}")
    gc.set_threshold(*old)  # 恢复


# ============================================================
# Part C: weakref
# ============================================================

def demo_weakref_basic():
    """弱引用不增加引用计数"""
    class Data:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"Data({self.name!r})"

    d = Data("alpha")
    r = weakref.ref(d)

    print(f"  r()   = {r()}")
    print(f"  refs  = {sys.getrefcount(d) - 1}")  # 不含 r

    del d
    print(f"  删除后: r() = {r()}")  # None


def demo_weak_value_dict():
    """WeakValueDictionary：自动清理的缓存"""
    class Image:
        def __init__(self, key: str, data: bytes):
            self.key = key
            self.data = data

        def __del__(self):
            print(f"  [GC] 卸载 {self.key}")

    cache = weakref.WeakValueDictionary()

    img1 = Image("hero.png", b"x" * 100)
    img2 = Image("logo.png", b"y" * 200)

    cache["hero"] = img1
    cache["logo"] = img2
    print(f"  缓存键: {list(cache.keys())}")

    del img1           # 删除 img1 的唯一强引用
    print(f"  删除 img1 后: {list(cache.keys())}")

    del img2
    print(f"  删除 img2 后: {list(cache.keys())}")  # 空！


def demo_weak_key_dict():
    """WeakKeyDictionary：键是弱引用——附加元数据"""
    metadata = weakref.WeakKeyDictionary()

    class Connection:
        def __init__(self, conn_id: int):
            self.conn_id = conn_id

        def __del__(self):
            print(f"  [GC] 关闭连接 {self.conn_id}")

    conn = Connection(42)
    metadata[conn] = {"last_query": "SELECT *", "duration_ms": 15}

    print(f"  元数据: {metadata.get(conn)}")
    print(f"  条目数: {len(metadata)}")
    del conn
    print(f"  删除后条目数: {len(metadata)}")


def demo_finalize():
    """weakref.finalize：GC 时机清理回调"""
    class ManagedFile:
        def __init__(self, path: str):
            self.path = path
            self._file = open(path, 'w')
            weakref.finalize(self, self._cleanup, path)

        @staticmethod
        def _cleanup(path: str):
            print(f"  [finalize] 清理文件: {path}")

    f = ManagedFile("/tmp/test.log")
    print(f"  ManagedFile 已创建")
    del f
    print(f"  ManagedFile 已删除")


# ============================================================
# Part D: __slots__ 内存分析
# ============================================================

def demo_slots_memory():
    """__slots__ vs __dict__ 内存占用对比"""
    class WithDict:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    class WithSlots:
        __slots__ = ('x', 'y', 'z')

        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    d = WithDict(1, 2, 3)
    s = WithSlots(1, 2, 3)

    print(f"  WithDict  实例: {sys.getsizeof(d)} bytes")
    print(f"  WithDict __dict__: {sys.getsizeof(d.__dict__)} bytes")
    print(f"  WithDict  总计:   {sys.getsizeof(d) + sys.getsizeof(d.__dict__)} bytes")
    print(f"  WithSlots 实例:   {sys.getsizeof(s)} bytes")
    print(f"  WithSlots 有 __dict__: {hasattr(s, '__dict__')}")

    # 100 万个实例的成本估算
    print(f"\n  100 万个实例成本估算:")
    print(f"    WithDict:  ~{(sys.getsizeof(d) + sys.getsizeof(d.__dict__)) * 1_000_000 / 1024 / 1024:.0f} MB")
    print(f"    WithSlots: ~{sys.getsizeof(s) * 1_000_000 / 1024 / 1024:.0f} MB")


def demo_dataclass_slots():
    """@dataclass(slots=True)：现代内存高效数据类"""
    @dataclass(slots=True)
    class Vector3:
        x: float
        y: float
        z: float

    @dataclass
    class Vector3NoSlots:
        x: float
        y: float
        z: float

    v_slots = Vector3(1.0, 2.0, 3.0)
    v_noslots = Vector3NoSlots(1.0, 2.0, 3.0)

    print(f"  Vector3(slots=True):  {sys.getsizeof(v_slots)} bytes")
    print(f"  有 __dict__: {hasattr(v_slots, '__dict__')}")
    print(f"  Vector3(slots=False): {sys.getsizeof(v_noslots)} bytes"
          f" + __dict__ {sys.getsizeof(v_noslots.__dict__)} bytes"
          f" = {sys.getsizeof(v_noslots) + sys.getsizeof(v_noslots.__dict__)} bytes")


# ============================================================
# Part E: tracemalloc 内存追踪
# ============================================================

def demo_tracemalloc_top():
    """找出当前内存分配最大的代码位置"""
    tracemalloc.start()

    # 分配不同大小的内存
    data1 = [bytearray(512) for _ in range(100)]
    data2 = "x" * (256 * 1024)  # 256 KB 字符串
    data3 = [0] * 10000

    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')

    print("  Top 5 内存分配来源:")
    for stat in top_stats[:5]:
        print(f"    {stat}")

    tracemalloc.stop()


def demo_tracemalloc_diff():
    """对比快照找内存增量"""
    tracemalloc.start()

    snap_before = tracemalloc.take_snapshot()

    # 模拟：创建一批对象，再释放一部分
    cache = {}
    for i in range(2000):
        cache[f"key_{i}"] = bytearray(128)

    for i in range(1500):
        del cache[f"key_{i}"]

    snap_after = tracemalloc.take_snapshot()

    stats = snap_after.compare_to(snap_before, 'lineno')
    print("  内存变化 Top 3:")
    for stat in stats[:3]:
        print(f"    {stat}")

    tracemalloc.stop()


def demo_tracemalloc_leak():
    """用 tracemalloc 找内存泄漏"""
    class LeakyCache:
        """故意写的不清理缓存——模拟内存泄漏"""
        _cache: dict[str, bytes] = {}

        @classmethod
        def get(cls, key: str) -> bytes:
            if key not in cls._cache:
                cls._cache[key] = key.encode() * 512
            return cls._cache[key]

    tracemalloc.start(10)

    snap1 = tracemalloc.take_snapshot()
    for i in range(1000):
        LeakyCache.get(f"req_{i}")
    snap2 = tracemalloc.take_snapshot()

    stats = snap2.compare_to(snap1, 'lineno')
    print("  内存泄漏来源 Top 3:")
    for stat in stats[:3]:
        print(f"    {stat}")

    tracemalloc.stop()


# ============================================================
# Part F: dis 字节码
# ============================================================

def demo_dis_basic():
    """基本字节码反编译"""

    def add(a, b):
        return a + b

    print("  函数 add(a, b): return a + b")
    dis.dis(add)


def demo_dis_compare():
    """列表推导式 vs for 循环的字节码对比"""

    def squares_comp(n):
        return [x * x for x in range(n)]

    def squares_loop(n):
        result = []
        for x in range(n):
            result.append(x * x)
        return result

    print("  === 列表推导式 ===")
    dis.dis(squares_comp)
    print("\n  === for 循环 ===")
    dis.dis(squares_loop)


def demo_dis_global_vs_local():
    """LOAD_GLOBAL vs LOAD_FAST 的字节码对比"""

    def slow(items):
        total = 0
        for x in items:
            # 每次循环都 LOAD_GLOBAL
            total = total + x
        return total

    def fast(items):
        total = 0
        _add = total.__add__  # 一次 LOAD_ATTR，循环内用 LOAD_FAST
        for x in items:
            total = _add(x)
        return total

    print("  === slow (每次循环 LOAD_GLOBAL total) ===")
    dis.dis(slow)
    print("\n  === fast (缓存 __add__ 到局部变量) ===")
    dis.dis(fast)


# ============================================================
# Part G: 性能优化技巧
# ============================================================

def demo_local_cache():
    """循环中缓存全局变量到局部"""
    import math

    items = list(range(5_000_000))

    # 每次循环访问全局的 math.sqrt
    start = time.perf_counter()
    for x in items:
        _ = math.sqrt(x)
    t_slow = time.perf_counter() - start

    # 缓存到局部变量
    start = time.perf_counter()
    sqrt = math.sqrt
    for x in items:
        _ = sqrt(x)
    t_fast = time.perf_counter() - start

    print(f"  LOAD_GLOBAL (每次循环): {t_slow:.3f}s")
    print(f"  LOAD_FAST   (缓存到局部): {t_fast:.3f}s")
    print(f"  加速: {t_slow / t_fast:.2f}x")


def demo_lru_cache():
    """functools.lru_cache 用于重复计算"""

    @functools.lru_cache(maxsize=128)
    def fib(n: int) -> int:
        if n < 2:
            return n
        return fib(n - 1) + fib(n - 2)

    start = time.perf_counter()
    result = fib(200)
    elapsed = time.perf_counter() - start

    print(f"  fib(200) = {result}")
    print(f"  耗时: {elapsed:.6f}s")
    print(f"  缓存信息: {fib.cache_info()}")

    # 对比无缓存版本（仅 n=35，因为指数级增长）
    def fib_no_cache(n):
        if n < 2:
            return n
        return fib_no_cache(n - 1) + fib_no_cache(n - 2)

    start = time.perf_counter()
    result = fib_no_cache(35)
    t_no_cache = time.perf_counter() - start
    print(f"\n  无缓存 fib(35) = {result}, 耗时: {t_no_cache:.3f}s")
    # fib(35) 无缓存要 1-3 秒，fib(200) 不可能完成


def demo_slots_speed():
    """__slots__ 的属性访问速度对比"""
    class WithDict:
        def __init__(self):
            self.x = 0

    class WithSlots:
        __slots__ = ('x',)
        def __init__(self):
            self.x = 0

    N = 10_000_000
    d_obj = WithDict()
    s_obj = WithSlots()

    start = time.perf_counter()
    for _ in range(N):
        _ = d_obj.x
    t_dict = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(N):
        _ = s_obj.x
    t_slots = time.perf_counter() - start

    print(f"  __dict__  读取: {t_dict:.3f}s")
    print(f"  __slots__ 读取: {t_slots:.3f}s")
    if t_slots < t_dict:
        print(f"  __slots__ 快 {t_dict / t_slots:.2f}x")


def demo_cached_property():
    """functools.cached_property：惰性计算+缓存"""

    class DataSet:
        def __init__(self, numbers: list[int]):
            self.numbers = numbers

        @functools.cached_property
        def avg(self):
            print("  (正在计算 avg...)")
            return sum(self.numbers) / len(self.numbers)

    ds = DataSet([1, 2, 3, 4, 5])
    print(f"  第一次: {ds.avg}")
    print(f"  第二次: {ds.avg}")  # 不重新计算


# ============================================================
# 主程序入口
# ============================================================

if __name__ == '__main__':
    print("=" * 55)
    print("3.7 内存管理与性能 —— 完整示例")
    print("=" * 55)

    print("\n── Part A: 引用计数 ──")
    demo_refcount()

    print("\n── Part B: 分代 GC ──")
    demo_generational_gc()

    print("\n── Part C1: weakref.ref ──")
    demo_weakref_basic()

    print("\n── Part C2: WeakValueDictionary ──")
    demo_weak_value_dict()

    print("\n── Part C3: WeakKeyDictionary ──")
    demo_weak_key_dict()

    print("\n── Part C4: weakref.finalize ──")
    demo_finalize()

    print("\n── Part D1: __slots__ 内存 ──")
    demo_slots_memory()

    print("\n── Part D2: dataclass(slots=True) ──")
    demo_dataclass_slots()

    print("\n── Part E1: tracemalloc Top ──")
    demo_tracemalloc_top()

    print("\n── Part E2: tracemalloc Diff ──")
    demo_tracemalloc_diff()

    print("\n── Part E3: tracemalloc 泄漏 ──")
    demo_tracemalloc_leak()

    print("\n── Part F1: dis 基础 ──")
    demo_dis_basic()

    print("\n── Part F2: 列表推导式 vs for 循环 ──")
    demo_dis_compare()

    print("\n── Part F3: LOAD_GLOBAL vs LOAD_FAST ──")
    demo_dis_global_vs_local()

    print("\n── Part G1: 局部缓存 ──")
    demo_local_cache()

    print("\n── Part G2: lru_cache ──")
    demo_lru_cache()

    print("\n── Part G3: __slots__ 速度 ──")
    demo_slots_speed()

    print("\n── Part G4: cached_property ──")
    demo_cached_property()
