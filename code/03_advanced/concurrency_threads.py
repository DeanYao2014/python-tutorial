# ─────────────────────────────────────────────────────────────
# 第 3.5 章：并发：线程与 GIL — 代码示例
# Python 3.12+ 可运行
# ─────────────────────────────────────────────────────────────

import sys
import time
import threading
import multiprocessing
import queue
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Any

# ═══════════════════════════════════════════════════════════════
# Part A: GIL 深度剖析
# ═══════════════════════════════════════════════════════════════

def demo_gil_switch_interval() -> None:
    """演示 GIL 切换间隔"""
    print(f"Python 版本: {sys.version}")
    print(f"GIL 切换间隔: {sys.getswitchinterval()} 秒 (~5ms)")

    # 修改切换间隔（通常不需要改）
    sys.setswitchinterval(0.01)  # 改成 10ms
    print(f"修改后: {sys.getswitchinterval()} 秒")


def demo_gil_cpu_bound() -> None:
    """GIL 使 CPU 密集型多线程比单线程更慢"""
    def cpu_work(n: int) -> int:
        total = 0
        for i in range(n):
            total += i * i
        return total

    N = 10_000_000

    # 单线程
    start = time.perf_counter()
    cpu_work(N)
    single_time = time.perf_counter() - start
    print(f"单线程: {single_time:.3f}s")

    # 双线程竞争 GIL
    start = time.perf_counter()
    t1 = threading.Thread(target=cpu_work, args=(N,))
    t2 = threading.Thread(target=cpu_work, args=(N,))
    t1.start(); t2.start()
    t1.join(); t2.join()
    multi_time = time.perf_counter() - start
    print(f"双线程: {multi_time:.3f}s (慢 {multi_time/single_time:.1f}x)")

    # 原因：GIL 强制同一时刻只有一个线程执行，线程切换本身还有开销


# ═══════════════════════════════════════════════════════════════
# Part B: threading 模块
# ═══════════════════════════════════════════════════════════════

def demo_basic_thread() -> None:
    """线程创建与 join"""
    def worker(name: str, delay: float) -> None:
        print(f"[{name}] 开始")
        time.sleep(delay)   # sleep 时释放 GIL，不阻塞其他线程
        print(f"[{name}] 完成")

    t1 = threading.Thread(target=worker, args=("A", 0.5))
    t2 = threading.Thread(target=worker, args=("B", 0.3))

    t1.start()
    t2.start()
    t1.join()  # 等 t1 结束
    t2.join()  # 等 t2 结束
    print("全部完成")


def demo_lock_race() -> None:
    """没有 Lock 时的竞态条件"""
    counter = 0

    def increment() -> None:
        nonlocal counter
        for _ in range(100_000):
            temp = counter
            temp = temp + 1
            counter = temp    # ← 这三步不是原子的！GIL 可能在任意一步切换

    threads = [threading.Thread(target=increment) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"无锁: counter = {counter} (期望 400000)")  # 总是小于期望值


def demo_lock_safe() -> None:
    """用 Lock 保护共享数据"""
    counter = 0
    lock = threading.Lock()

    def increment() -> None:
        nonlocal counter
        for _ in range(100_000):
            with lock:
                counter += 1   # 在锁保护下，是安全的

    threads = [threading.Thread(target=increment) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    print(f"有锁: counter = {counter} (期望 400000)")


def demo_rlock() -> None:
    """RLock: 同一线程可重复获取的锁"""
    rlock = threading.RLock()

    def recursive(n: int) -> None:
        with rlock:
            if n > 0:
                recursive(n - 1)  # 同一线程再次获取 RLOCK —— OK
            print(f"深度 {n}")

    threading.Thread(target=recursive, args=(3,)).start()
    # Lock 会死锁在这里，RLock 不会


def demo_semaphore() -> None:
    """Semaphore: 限制同时访问资源的线程数"""
    semaphore = threading.Semaphore(2)  # 最多 2 个线程同时运行

    def worker(name: str) -> None:
        with semaphore:
            print(f"[{name}] 获取名额")
            time.sleep(0.2)
            print(f"[{name}] 释放名额")

    threads = [threading.Thread(target=worker, args=(f"T{i}",)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()


def demo_thread_local() -> None:
    """threading.local(): 线程独有的存储空间 —— 理解 Flask request 上下文的关键"""
    local_data = threading.local()

    def set_and_print(name: str, value: Any) -> None:
        local_data.value = value           # 只在这个线程可见
        time.sleep(0.1)
        print(f"[{name}] local_data.value = {local_data.value}")

    t1 = threading.Thread(target=set_and_print, args=("T1", 10))
    t2 = threading.Thread(target=set_and_print, args=("T2", 20))
    t1.start(); t2.start()
    t1.join(); t2.join()
    # T1 输出 10，T2 输出 20 —— 互不干扰


def demo_queue_communication() -> None:
    """queue.Queue: 线程间安全的通信通道"""
    q: queue.Queue[int] = queue.Queue()

    def producer() -> None:
        for i in range(5):
            time.sleep(0.1)
            q.put(i)
            print(f"生产: {i}")
        q.put(None)  # 哨兵信号：生产结束

    def consumer() -> None:
        while True:
            item = q.get()
            if item is None:   # 哨兵信号
                q.task_done()
                break
            print(f"消费: {item}")
            q.task_done()

    t_p = threading.Thread(target=producer)
    t_c = threading.Thread(target=consumer)
    t_c.start(); t_p.start()
    t_p.join(); t_c.join()


# ═══════════════════════════════════════════════════════════════
# Part C: multiprocessing 模块
# ═══════════════════════════════════════════════════════════════

def demo_process_gil_bypass() -> None:
    """多进程绕开 GIL —— CPU 密集型真正并行"""
    def cpu_work(n: int) -> int:
        total = 0
        for i in range(n):
            total += i * i
        return total

    N = 10_000_000

    start = time.perf_counter()
    cpu_work(N)  # 单进程
    single_time = time.perf_counter() - start
    print(f"单进程: {single_time:.3f}s")

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(cpu_work, N) for _ in range(4)]
        [f.result() for f in futures]
    multi_time = time.perf_counter() - start
    print(f"4 进程: {multi_time:.3f}s (单任务均摊 {multi_time/4:.3f}s)")


def demo_process_pool() -> None:
    """multiprocessing.Pool: 进程池的经典用法"""
    def square(x: int) -> int:
        return x * x

    with multiprocessing.Pool(processes=4) as pool:
        results = pool.map(square, range(10))
    print(f"pool.map: {results}")


the_global_still_process_local = 0  # 演示多进程不共享内存


def demo_process_no_shared_memory() -> None:
    """多进程警告: 全局变量不共享 —— 每个进程有独立的内存空间"""
    global the_global_still_process_local

    def child_work() -> None:
        global the_global_still_process_local
        the_global_still_process_local = 42  # 只在子进程的内存空间
        print(f"[子进程] 全局变量 = {the_global_still_process_local}")

    p = multiprocessing.Process(target=child_work)
    p.start(); p.join()
    print(f"[主进程] 全局变量 = {the_global_still_process_local}")  # 还是 0！


# ═══════════════════════════════════════════════════════════════
# Part D: concurrent.futures — 统一接口
# ═══════════════════════════════════════════════════════════════

def demo_futures_map() -> None:
    """map() —— 像内置 map 一样批量提交任务"""
    def fetch(url: str) -> str:
        return url.upper()

    urls = ["a.com", "b.com", "c.com", "d.com", "e.com"]
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = executor.map(fetch, urls)
    print(f"map 结果: {list(results)}")


def demo_futures_submit() -> None:
    """submit() —— 逐个提交，逐个获取结果"""
    def fetch(url: str) -> str:
        time.sleep({"a.com": 0.3, "b.com": 0.1, "c.com": 0.5}.get(url, 0.1))
        return f"OK({url})"

    urls = ["a.com", "b.com", "c.com"]
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(fetch, url): url for url in urls}
        for future in as_completed(futures):  # 哪个先完成先处理哪个
            url = futures[future]
            print(f"最先完成: {url} → {future.result()}")


def demo_real_world_download() -> None:
    """实战模式: 并行下载 + 处理"""
    def pretend_download(url: str) -> str:
        delay = hash(url) % 500 / 1000 + 0.05
        time.sleep(delay)
        return f"<content of {url}>"

    def process(content: str) -> int:
        return len(content)

    urls = [f"https://api.example.com/item/{i}" for i in range(10)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        # 第一阶段: 并行下载
        download_futures = {executor.submit(pretend_download, url): url for url in urls}
        # 第二阶段: 逐个处理下载结果
        results: list[int] = []
        for future in as_completed(download_futures):
            content = future.result()
            results.append(process(content))

    print(f"处理了 {len(urls)} 个 URL，总内容大小 {sum(results)}")


# ═══════════════════════════════════════════════════════════════
# 决策对比：I/O 密集型 vs CPU 密集型
# ═══════════════════════════════════════════════════════════════

def demo_benchmark_io_bound() -> None:
    """I/O 密集型: threading 完胜"""
    def io_task(name: str) -> str:
        time.sleep(0.1)  # 模拟 I/O
        return f"done-{name}"

    tasks = list(range(20))

    # threading
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=10) as ex:
        list(ex.map(io_task, [str(t) for t in tasks]))
    t_time = time.perf_counter() - start
    print(f"I/O: Threading     {t_time:.3f}s")

    # multiprocessing (慢，因为序列化开销 > I/O 等待)
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as ex:
        list(ex.map(io_task, [str(t) for t in tasks]))
    p_time = time.perf_counter() - start
    print(f"I/O: Multiprocessing {p_time:.3f}s (线程/进程 = {p_time/t_time:.1f}x)")


def demo_benchmark_cpu_bound() -> None:
    """CPU 密集型: multiprocessing 完胜"""
    def cpu_task(n: int) -> int:
        return sum(i * i for i in range(n))

    tasks = [2_000_000] * 8

    # threading (被 GIL 限制)
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, tasks))
    t_time = time.perf_counter() - start

    # multiprocessing
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as ex:
        list(ex.map(cpu_task, tasks))
    p_time = time.perf_counter() - start

    print(f"CPU: Threading     {t_time:.3f}s")
    print(f"CPU: Multiprocessing {p_time:.3f}s (线程/进程 = {t_time/p_time:.1f}x)")


# ═══════════════════════════════════════════════════════════════
# 测试入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    separator = "=" * 60

    print("=" * 60)
    print("Part A: GIL 切换间隔")
    print(separator)
    demo_gil_switch_interval()

    print(f"\n{separator}")
    print("Part A: CPU 密集型 GIL 惩罚")
    print(separator)
    demo_gil_cpu_bound()

    print(f"\n{separator}")
    print("Part B: 基本线程")
    print(separator)
    demo_basic_thread()

    print(f"\n{separator}")
    print("Part B: 竞态条件（没有 Lock）")
    print(separator)
    demo_lock_race()

    print(f"\n{separator}")
    print("Part B: 使用 Lock 保护")
    print(separator)
    demo_lock_safe()

    print(f"\n{separator}")
    print("Part B: Semaphore 限制并发")
    print(separator)
    demo_semaphore()

    print(f"\n{separator}")
    print("Part B: threading.local() 线程本地存储")
    print(separator)
    demo_thread_local()

    print(f"\n{separator}")
    print("Part B: queue.Queue 线程通信")
    print(separator)
    demo_queue_communication()

    print(f"\n{separator}")
    print("Part C: 多进程绕开 GIL")
    print(separator)
    demo_process_gil_bypass()

    print(f"\n{separator}")
    print("Part C: 进程池 Pool.map")
    print(separator)
    demo_process_pool()

    print(f"\n{separator}")
    print("Part C: 多进程不共享内存")
    print(separator)
    demo_process_no_shared_memory()

    print(f"\n{separator}")
    print("Part D: ThreadPoolExecutor.map")
    print(separator)
    demo_futures_map()

    print(f"\n{separator}")
    print("Part D: submit + as_completed")
    print(separator)
    demo_futures_submit()

    print(f"\n{separator}")
    print("Part D: 并行下载模式")
    print(separator)
    demo_real_world_download()

    print(f"\n{separator}")
    print("决策对比: I/O 密集型")
    print(separator)
    demo_benchmark_io_bound()

    print(f"\n{separator}")
    print("决策对比: CPU 密集型")
    print(separator)
    demo_benchmark_cpu_bound()

    print(f"\n{'=' * 60}")
    print("所有示例运行完毕")
