# 并发编程全景：API 与选择 — 代码示例 (Python 3.11+)
import time
import math
import random
import threading
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor


# ═══════════════════════════════════════════════════════════════
# Part 1: 进程 — CPU 密集型并行计算
# ═══════════════════════════════════════════════════════════════

def cpu_bound(n: int) -> int:
    """计算密集型：统计小于 sqrt(n) 的因子数"""
    return sum(1 for i in range(2, int(math.sqrt(n)) + 1) if n % i == 0)


def demo_process_cpu() -> None:
    print("=== 进程：CPU 密集型并行 ===")
    numbers = [1_000_000_000 + i for i in range(12)]  # 大数字确保有足够计算量

    start = time.perf_counter()
    results_single = [cpu_bound(n) for n in numbers]
    t_single = time.perf_counter() - start

    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        results_multi = list(pool.map(cpu_bound, numbers))
    t_multi = time.perf_counter() - start

    print(f"  单进程: {t_single:.3f}s")
    print(f"  4 进程: {t_multi:.3f}s  (加速 {t_single / t_multi:.1f}x)")
    assert results_single == results_multi


# ═══════════════════════════════════════════════════════════════
# Part 2: 进程间通信 — Queue 生产者-消费者
# ═══════════════════════════════════════════════════════════════

from multiprocessing import Process, Queue


# Windows 要求 multiprocessing target 是模块级函数（spawn 需要 pickle）
def _proc_producer(q: Queue) -> None:
    for i in range(5):
        q.put(f"任务-{i}")
    q.put(None)


def _proc_consumer(q: Queue, name: str) -> None:
    while True:
        item = q.get()
        if item is None:
            q.put(None)
            break
        print(f"  [{name}] 处理: {item}")


def demo_process_queue() -> None:
    print("\n=== 进程间通信：Queue ===")

    q: Queue = Queue()
    p = Process(target=_proc_producer, args=(q,))
    c1 = Process(target=_proc_consumer, args=(q, "A"))
    c2 = Process(target=_proc_consumer, args=(q, "B"))
    p.start(); c1.start(); c2.start()
    p.join(); c1.join(); c2.join()


# ═══════════════════════════════════════════════════════════════
# Part 3: 线程 — Event 协调（发令枪模式）
# ═══════════════════════════════════════════════════════════════

def demo_thread_event() -> None:
    print("\n=== 线程：Event 发令枪 ===")

    def racer(name: str, ready: threading.Event, go: threading.Event) -> None:
        print(f"[{name}] 准备完成")
        ready.set()
        go.wait()
        print(f"[{name}] GO!")

    ready_events = [threading.Event() for _ in range(3)]
    go_event = threading.Event()

    racers = [
        threading.Thread(target=racer, args=(f"选手{i}", ready_events[i], go_event))
        for i in range(3)
    ]
    for t in racers: t.start()
    for e in ready_events: e.wait()
    print("  === 所有人就绪，出发！ ===")
    time.sleep(0.3)
    go_event.set()
    for t in racers: t.join()


# ═══════════════════════════════════════════════════════════════
# Part 4: 线程 — Semaphore 限流
# ═══════════════════════════════════════════════════════════════

def demo_thread_semaphore() -> None:
    print("\n=== 线程：Semaphore 限流（最多 2 并发） ===")
    db_lock = threading.Semaphore(2)

    def query(qid: int) -> None:
        with db_lock:
            print(f"  [查询 {qid}] 开始")
            time.sleep(random.uniform(0.1, 0.3))
            print(f"  [查询 {qid}] 完成 [OK]")

    threads = [threading.Thread(target=query, args=(i,)) for i in range(6)]
    for t in threads: t.start()
    for t in threads: t.join()


# ═══════════════════════════════════════════════════════════════
# Part 5: 线程 — threading.local() 线程私有全局变量
# ═══════════════════════════════════════════════════════════════

def demo_thread_local() -> None:
    print("\n=== 线程：threading.local() ===")
    tls = threading.local()

    def show(name: str) -> None:
        try:
            val = tls.value
        except AttributeError:
            val = None
        print(f"  [{name}] tls.value = {val}")
        tls.value = name

    t1 = threading.Thread(target=show, args=("A",))
    t2 = threading.Thread(target=show, args=("B",))
    t1.start(); t2.start()
    t1.join(); t2.join()
    print("  每个线程有自己的 tls.value，互不干扰")


# ═══════════════════════════════════════════════════════════════
# Part 6: 协程 — TaskGroup 结构化并发（3.11+，推荐替代 gather）
# ═══════════════════════════════════════════════════════════════

async def demo_async_taskgroup() -> None:
    print("\n=== 协程：TaskGroup 结构化并发 ===")

    async def fetch(name: str, delay: float) -> dict:
        await asyncio.sleep(delay)
        return {"service": name, "status": 200}

    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch("auth", 0.2))
        t2 = tg.create_task(fetch("db", 0.3))
        t3 = tg.create_task(fetch("cache", 0.1))

    print(f"  结果: {t1.result()}, {t2.result()}, {t3.result()}")


# ═══════════════════════════════════════════════════════════════
# Part 7: 协程 — Semaphore 限流（最多 3 并发请求）
# ═══════════════════════════════════════════════════════════════

async def demo_async_semaphore() -> None:
    print("\n=== 协程：Semaphore 限流（最多 3 并发） ===")
    sem = asyncio.Semaphore(3)

    async def limited_fetch(i: int) -> str:
        async with sem:
            print(f"  请求 /api/{i}...")
            await asyncio.sleep(0.2)
            print(f"  /api/{i} 完成 [OK]")
            return f"OK({i})"

    tasks = [asyncio.create_task(limited_fetch(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"  完成 {len(results)} 个请求")


# ═══════════════════════════════════════════════════════════════
# Part 8: 协程 — asyncio.Queue 生产者-消费者
# ═══════════════════════════════════════════════════════════════

async def demo_async_queue() -> None:
    print("\n=== 协程：asyncio.Queue 生产者-消费者 ===")

    async def producer(q: asyncio.Queue) -> None:
        for i in range(5):
            await asyncio.sleep(0.05)
            await q.put(f"数据-{i}")
            print(f"  生产: 数据-{i}")
        await q.put(None)

    async def consumer(q: asyncio.Queue, name: str) -> None:
        while True:
            item = await q.get()
            if item is None:
                await q.put(None)
                break
            print(f"  [{name}] 处理: {item}")
            q.task_done()

    q: asyncio.Queue = asyncio.Queue(maxsize=3)
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q))
        tg.create_task(consumer(q, "A"))
        tg.create_task(consumer(q, "B"))


# ═══════════════════════════════════════════════════════════════
# Part 9: 协程 — to_thread 同步桥接（3.11+）
# ═══════════════════════════════════════════════════════════════

def sync_blocking_func(n: int) -> str:
    """一个不能改写的同步阻塞函数（模拟旧库）"""
    time.sleep(0.15)
    return f"sync-result-{n}"


async def demo_async_to_thread() -> None:
    print("\n=== 协程：to_thread 同步桥接（3.11+） ===")

    # to_thread 内部用默认线程池，不阻塞事件循环
    results = await asyncio.gather(
        asyncio.to_thread(sync_blocking_func, 1),
        asyncio.to_thread(sync_blocking_func, 2),
        asyncio.to_thread(sync_blocking_func, 3),
    )
    print(f"  结果: {results}")


# ═══════════════════════════════════════════════════════════════
# Part 10: 三种方式对照 —— 同一个任务
# ═══════════════════════════════════════════════════════════════

URLS = [f"https://api.example.com/item/{i}" for i in range(6)]


def blocking_download(url: str) -> str:
    """模拟同步 I/O"""
    time.sleep(0.2)
    return f"OK({url})"


async def async_download(url: str) -> str:
    """模拟异步 I/O"""
    await asyncio.sleep(0.2)
    return f"OK({url})"


def demo_threads_io() -> None:
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(blocking_download, URLS))
    print(f"  多线程: {time.perf_counter() - start:.3f}s — {results[:2]}...")


def demo_processes_io() -> None:
    start = time.perf_counter()
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(blocking_download, URLS))
    print(f"  多进程: {time.perf_counter() - start:.3f}s — {results[:2]}... (慢、序列化开销)")


async def demo_async_io() -> None:
    start = time.perf_counter()
    tasks = [asyncio.create_task(async_download(url)) for url in URLS]
    results = await asyncio.gather(*tasks)
    print(f"  协程:   {time.perf_counter() - start:.3f}s — {results[:2]}...")


def demo_three_way_compare() -> None:
    print("\n=== 三种方式对照：下载 6 个 URL ===")
    demo_threads_io()
    demo_processes_io()
    asyncio.run(demo_async_io())
    print("  结论：纯 I/O -> 协程 > 线程 >> 进程（进程有序列化开销）")


# ═══════════════════════════════════════════════════════════════
# Part 11: 混合使用 — asyncio + 线程/进程池
# ═══════════════════════════════════════════════════════════════

def heavy_io(n: int) -> str:
    """同步阻塞 I/O"""
    time.sleep(0.2)
    return f"IO-{n}"


def heavy_cpu(n: int) -> int:
    """CPU 密集型计算"""
    total = 0
    for i in range(n * 1_000_000):
        total += i
    return total


async def demo_mixed() -> None:
    print("\n=== 混合：asyncio + 线程池 + 进程池 ===")

    # I/O 部分 → 线程池 (to_thread)
    results_io = await asyncio.gather(
        asyncio.to_thread(heavy_io, 1),
        asyncio.to_thread(heavy_io, 2),
    )
    print(f"  I/O 结果: {results_io}")

    # CPU 部分 → 进程池
    loop = asyncio.get_running_loop()
    with ProcessPoolExecutor(max_workers=2) as pool:
        results_cpu = await asyncio.gather(
            loop.run_in_executor(pool, heavy_cpu, 5),
            loop.run_in_executor(pool, heavy_cpu, 6),
        )
    print(f"  CPU 结果: {results_cpu}")


# ═══════════════════════════════════════════════════════════════
# 测试入口
# ═══════════════════════════════════════════════════════════════

async def all_async_demos() -> None:
    await demo_async_taskgroup()
    await demo_async_semaphore()
    await demo_async_queue()
    await demo_async_to_thread()
    await demo_mixed()


def main() -> None:
    print("=" * 60)
    print("并发编程全景：API 与选择 — 代码演示")
    print("=" * 60)

    demo_process_cpu()
    demo_process_queue()
    demo_thread_event()
    demo_thread_semaphore()
    demo_thread_local()
    demo_three_way_compare()

    print("\n" + "=" * 60)
    print("以下为 asyncio 部分")
    print("=" * 60)
    asyncio.run(all_async_demos())

    print("\n" + "=" * 60)
    print("全部演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
