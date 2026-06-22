# ─────────────────────────────────────────────────────────────
# 第 3.6 章：并发：asyncio 深入 — 代码示例
# Python 3.11+ 可运行。3.12/3.13 特性带版本守卫。
# ─────────────────────────────────────────────────────────────

import asyncio
import time
import signal
import sys
from typing import Any

# ═══════════════════════════════════════════════════════════════
# Part A: 协程本质 — 最小事件循环实现 (30 行)
# ═══════════════════════════════════════════════════════════════

def demo_mini_event_loop() -> None:
    """30 行实现一个最小的事件循环——帮你理解 asyncio 的本质"""
    from collections import deque

    class MiniLoop:
        """极简事件循环: 用一个队列管理待运行的协程"""

        def __init__(self) -> None:
            self._ready: deque[Any] = deque()

        def create_task(self, coro: Any) -> int:
            """把协程加入就绪队列，返回任务 ID"""
            task_id = id(coro)
            self._ready.append(coro)
            return task_id

        def run(self) -> None:
            """不断从队列取协程，推进，直到队列空"""
            while self._ready:
                coro = self._ready.popleft()
                try:
                    # 推进协程一步：send(None) 相当于 await 放行一次
                    # coroutine.__next__() 等价于 send(None)
                    coro.send(None)
                    # 协程还没结束，放回队列尾部
                    self._ready.append(coro)
                except StopIteration:
                    pass  # 协程结束了，不放了

    async def task(name: str, countdown: int) -> None:
        for i in range(countdown, 0, -1):
            print(f"[{name}] {i}")
            await asyncio.sleep(0)  # 主动让出控制权
        print(f"[{name}] done!")

    loop = MiniLoop()
    print("MiniLoop 本质: 队列 + 轮转调度 = 协程调度器")


def demo_manual_coroutine() -> None:
    """手动操控协程 —— 看看 async def 底层长什么样"""
    async def say_hello() -> str:
        await asyncio.sleep(0)
        return "hello"

    coro = say_hello()
    print(f"type(coro) = {type(coro)}")           # <class 'coroutine'>
    print(f"has __await__: {hasattr(coro, '__await__')}")  # True

    # 手动驱动协程（不推荐，只用于理解底层）
    try:
        coro.send(None)  # 启动协程
    except StopIteration as e:
        print(f"返回值: {e.value}")  # 协程结束时抛出 StopIteration，value 是返回值


# ═══════════════════════════════════════════════════════════════
# Part B: Task 和 Future
# ═══════════════════════════════════════════════════════════════

async def demo_task_basics() -> None:
    """asyncio.create_task: 将协程包装成 Task，提交到事件循环并发运行"""
    async def fetch(url: str) -> str:
        await asyncio.sleep(0.2)
        return f"OK({url})"

    # 方式 1: create_task —— 立即调度
    t1 = asyncio.create_task(fetch("a.com"))
    t2 = asyncio.create_task(fetch("b.com"))
    r1 = await t1  # 等待任务完成，获取返回值
    r2 = await t2
    print(f"create_task: {r1}, {r2}")

    # 方式 2: 等价写法（但不推荐——失去并发）
    # r1 = await fetch("a.com")  # ← 先等 a 完成
    # r2 = await fetch("b.com")  # ← 再等 b 完成（没有并发！）


async def demo_gather() -> None:
    """asyncio.gather: 并发运行多个协程，收集所有结果"""
    async def fetch(id: int) -> str:
        await asyncio.sleep(0.1)
        return f"result-{id}"

    results = await asyncio.gather(
        fetch(1),
        fetch(2),
        fetch(3),
    )
    print(f"gather: {results}")  # ['result-1', 'result-2', 'result-3']

    # 默认行为: 一个失败，全部失败（但其他任务仍在运行）
    async def fail() -> str:
        raise ValueError("boom")

    try:
        await asyncio.gather(fetch(1), fail(), fetch(3))
    except ValueError as e:
        print(f"gather 异常: {e}  —— 但 fetch(1) 和 fetch(3) 可能仍在运行！")


async def demo_taskgroup() -> None:
    """asyncio.TaskGroup (3.11+): 结构化并发 —— 推荐的新标准"""
    async def fetch(id: int) -> str:
        await asyncio.sleep(0.1)
        return f"result-{id}"

    async def fetch_fail(id: int) -> str:
        await asyncio.sleep(0.05)
        if id == 2:
            raise ValueError(f"任务 {id} 失败了")
        return f"result-{id}"

    # ── 正常使用 ──
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch(1))
        t2 = tg.create_task(fetch(2))
        t3 = tg.create_task(fetch(3))
    print(f"TaskGroup: {t1.result()}, {t2.result()}, {t3.result()}")

    # ── TaskGroup vs gather 的核心区别 ──
    async def demo_taskgroup_cancellation() -> None:
        """TaskGroup: 一个失败，自动取消所有兄弟姐妹任务"""
        results_queue: list[str] = []

        async def task_with_cleanup(id: int) -> None:
            try:
                await asyncio.sleep(0.1 * id)
                if id == 2:
                    raise ValueError(f"任务 {id} 失败了")
                results_queue.append(f"result-{id}")
            except asyncio.CancelledError:
                results_queue.append(f"任务 {id} 被取消了")
                raise  # 必须重新抛出 CancelledError

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(task_with_cleanup(1))
                tg.create_task(task_with_cleanup(2))  # ← 这个会失败
                tg.create_task(task_with_cleanup(3))
        except* Exception as eg:
            # 使用了 except* (3.11+ ExceptionGroup)
            print(f"TaskGroup 捕获异常: {eg}")

        print(f"结果: {results_queue}")
        # gather 不会取消其他任务，TaskGroup 会

    await demo_taskgroup_cancellation()


async def demo_wait_for() -> None:
    """asyncio.wait_for: 给协程加超时"""
    async def slow_work() -> str:
        await asyncio.sleep(1.0)
        return "太慢了"

    try:
        result = await asyncio.wait_for(slow_work(), timeout=0.2)
    except asyncio.TimeoutError:
        print("wait_for: 超时了！协程被自动取消")


async def demo_as_completed() -> None:
    """asyncio.as_completed: 哪个先完成，先处理哪个"""
    async def fetch(id: int, delay: float) -> str:
        await asyncio.sleep(delay)
        return f"result-{id} ({delay}s)"

    tasks = [
        asyncio.create_task(fetch(1, 0.3)),
        asyncio.create_task(fetch(2, 0.1)),
        asyncio.create_task(fetch(3, 0.2)),
    ]

    for coro in asyncio.as_completed(tasks):
        result = await coro
        print(f"as_completed: {result}")


# ═══════════════════════════════════════════════════════════════
# Part C: 最新推荐语法 (Python 3.11-3.13)
# ═══════════════════════════════════════════════════════════════

async def demo_to_thread_311() -> None:
    """Python 3.11+: asyncio.to_thread —— 在线程池中运行同步代码"""
    import time

    def blocking_io(id: int) -> str:
        """同步阻塞 I/O —— 不能在事件循环中直接调用"""
        time.sleep(0.2)  # 同步 sleep！不会释放控制权给事件循环
        return f"sync-result-{id}"

    # 旧方式: loop.run_in_executor(None, blocking_io, 1)  ← 繁琐
    # 新方式: asyncio.to_thread —— 一行搞定
    r1 = await asyncio.to_thread(blocking_io, 1)
    r2 = await asyncio.to_thread(blocking_io, 2)

    # 真正的并发: 两个任务在线程池中并行
    t1 = asyncio.create_task(asyncio.to_thread(blocking_io, 3))
    t2 = asyncio.create_task(asyncio.to_thread(blocking_io, 4))
    results = await asyncio.gather(t1, t2)
    print(f"to_thread: {r1}, {r2}, 并发: {results}")


async def demo_eager_task_factory_312() -> None:
    """Python 3.12+: eager_task_factory —— 更快的任务创建"""
    if sys.version_info < (3, 12):
        print("eager_task_factory 需要 Python 3.12+")
        return

    # 默认行为: create_task 后，任务在事件循环下一轮才执行
    # eager: create_task 后立即执行第一步，直到遇到 await
    loop = asyncio.get_event_loop()
    loop.set_task_factory(asyncio.eager_task_factory)

    async def quick() -> str:
        return "done"

    # eager 模式下，create_task 立即执行协程的第一步
    # 对于不需要真正暂停的任务，避免了事件循环的一次调度开销
    task = asyncio.create_task(quick())
    result = await task
    print(f"eager_task_factory: {result}")

    # 恢复默认（避免影响其他示例）
    loop.set_task_factory(asyncio.Task)


async def demo_timeout_313() -> None:
    """Python 3.13: asyncio.timeout() 上下文管理器 —— 更优雅的超时控制"""
    old_way = """\
    # 旧方式
    try:
        result = await asyncio.wait_for(slow_op(), timeout=5.0)
    except asyncio.TimeoutError:
        ...
    """

    # Python 3.13+ 新方式
    if sys.version_info >= (3, 13):
        print("Python 3.13+ asyncio.timeout() 上下文管理器:")
        try:
            async with asyncio.timeout(0.2):
                await asyncio.sleep(0.1)  # 模拟耗时操作
                print("  0.1s: 完成（未超时）")
        except TimeoutError:
            print("  不应该超时")

        # 真正超时的场景
        try:
            async with asyncio.timeout(0.1):
                await asyncio.sleep(0.3)
                print("  不应该到这里")
        except TimeoutError:
            print("  0.3s: 超时了！")
    else:
        print(f"asyncio.timeout() 需要 Python 3.13+ (当前 {sys.version_info.major}.{sys.version_info.minor})")
        print("替代方案: await asyncio.wait_for(slow_op, timeout=5.0)")


def demo_version_compare_table() -> None:
    """Python 版本并发特性对比表"""
    features = [
        ("Python 3.11", "TaskGroup, to_thread(), ExceptionGroup"),
        ("Python 3.12", "eager_task_factory, asyncio.Queue 改进"),
        ("Python 3.13", "asyncio.timeout() 上下文管理器, 性能改进"),
    ]
    for ver, feat in features:
        print(f"  {ver}: {feat}")


# ═══════════════════════════════════════════════════════════════
# Part D: 实战模式
# ═══════════════════════════════════════════════════════════════

async def demo_producer_consumer() -> None:
    """生产者-消费者模式: asyncio.Queue"""
    async def producer(q: asyncio.Queue[int], n: int) -> None:
        for i in range(n):
            await asyncio.sleep(0.05)  # 模拟生产耗时
            await q.put(i)
            print(f"生产: {i}")
        await q.put(None)  # 哨兵：生产结束

    async def consumer(q: asyncio.Queue[int], name: str) -> None:
        while True:
            item = await q.get()
            if item is None:
                await q.put(None)  # 把哨兵放回去，让其他消费者也看到
                break
            await asyncio.sleep(0.1)  # 模拟消费耗时
            print(f"[{name}] 消费: {item}")

    q: asyncio.Queue[int] = asyncio.Queue(maxsize=3)  # 限制队列大小——背压
    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(q, 6))
        tg.create_task(consumer(q, "A"))
        tg.create_task(consumer(q, "B"))


async def demo_rate_limit() -> None:
    """速率限制: asyncio.Semaphore"""
    semaphore = asyncio.Semaphore(3)  # 最多 3 个并发请求

    async def limited_request(id: int) -> str:
        async with semaphore:  # 获取名额
            await asyncio.sleep(0.2)  # 模拟请求
            return f"请求 {id} 完成"

    tasks = [asyncio.create_task(limited_request(i)) for i in range(10)]
    results = await asyncio.gather(*tasks)
    print(f"限速请求: {len(results)} 个")


async def demo_graceful_shutdown() -> None:
    """优雅关闭: 信号处理 + 清理"""
    stop_event = asyncio.Event()

    # 设置信号处理器（在 Unix 环境有效）
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()

        def handle_signal() -> None:
            print("\n收到 SIGINT，开始优雅关闭...")
            stop_event.set()

        loop.add_signal_handler(signal.SIGINT, handle_signal)

    async def worker(name: str) -> None:
        """运行直到收到停止信号"""
        count = 0
        while not stop_event.is_set():
            await asyncio.sleep(0.1)
            count += 1
        print(f"[{name}] 处理了 {count} 轮，退出")

    print("按 Ctrl+C 触发优雅关闭 (等待 2s 超时)...")
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker("A"))
            tg.create_task(worker("B"))
            # 定时器：2 秒后自动停止
            async def auto_stop() -> None:
                await asyncio.sleep(2)
                stop_event.set()
            tg.create_task(auto_stop())
    except* Exception:
        pass
    print("优雅关闭完成")


async def demo_blocking_pitfall() -> None:
    """常见陷阱: 在事件循环中调用同步阻塞函数"""
    import time

    async def bad() -> None:
        """错误: time.sleep 阻塞整个事件循环"""
        print("错误示范: time.sleep 阻塞事件循环")
        time.sleep(0.5)  # ← 整个事件循环卡死!
        print("(这行打印被延迟了)")

    async def good() -> None:
        """正确: 用 asyncio.sleep 或 to_thread"""
        await asyncio.sleep(0.5)  # ← 释放控制权
        print("正确: asyncio.sleep 不阻塞")

    # 错误示范
    start = time.perf_counter()
    coros = [bad(), bad()]
    await asyncio.gather(*coros)
    print(f"time.sleep 总耗时: {time.perf_counter() - start:.2f}s (应该 ~1.0s)")

    # 正确示范
    start = time.perf_counter()
    coros = [good(), good()]
    await asyncio.gather(*coros)
    print(f"asyncio.sleep 总耗时: {time.perf_counter() - start:.2f}s (应该 ~0.5s)")


# ═══════════════════════════════════════════════════════════════
# 测试入口
# ═══════════════════════════════════════════════════════════════

async def all_async_demos() -> None:
    sep = "=" * 60

    print("=" * 60)
    print("Part A: 协程本质")
    print(sep)
    demo_mini_event_loop()
    demo_manual_coroutine()

    print(f"\n{sep}")
    print("Part B: Task 基础")
    print(sep)
    await demo_task_basics()

    print(f"\n{sep}")
    print("Part B: gather")
    print(sep)
    await demo_gather()

    print(f"\n{sep}")
    print("Part B: TaskGroup (3.11+ 结构化并发)")
    print(sep)
    await demo_taskgroup()

    print(f"\n{sep}")
    print("Part B: wait_for")
    print(sep)
    await demo_wait_for()

    print(f"\n{sep}")
    print("Part B: as_completed")
    print(sep)
    await demo_as_completed()

    print(f"\n{sep}")
    print("Part C: to_thread (3.11+)")
    print(sep)
    await demo_to_thread_311()

    print(f"\n{sep}")
    print("Part C: eager_task_factory (3.12+)")
    print(sep)
    await demo_eager_task_factory_312()

    print(f"\n{sep}")
    print("Part C: asyncio.timeout (3.13+)")
    print(sep)
    await demo_timeout_313()

    print(f"\n{sep}")
    print("版本特性对照")
    print(sep)
    demo_version_compare_table()

    print(f"\n{sep}")
    print("Part D: 生产者-消费者")
    print(sep)
    await demo_producer_consumer()

    print(f"\n{sep}")
    print("Part D: 速率限制")
    print(sep)
    await demo_rate_limit()

    print(f"\n{sep}")
    print("Part D: 优雅关闭")
    print(sep)
    await demo_graceful_shutdown()

    print(f"\n{sep}")
    print("Part D: 阻塞陷阱")
    print(sep)
    await demo_blocking_pitfall()

    print(f"\n{'=' * 60}")
    print("所有异步示例运行完毕")


if __name__ == "__main__":
    asyncio.run(all_async_demos())
