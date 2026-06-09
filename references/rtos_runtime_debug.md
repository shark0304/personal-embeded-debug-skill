# RTOS Runtime Debug

Use this reference when an RTOS system boots but behaves incorrectly at runtime: missed deadlines, deadlocks, task starvation, queue/semaphore asserts, stack overflow, heap exhaustion, logging stalls, watchdog resets, or ISR-to-task handoff failures.

## Evidence to Collect

- RTOS, port, tick rate, scheduler mode, and enabled debug options.
- Full assert/fault text and file/line when available.
- Task/thread list with priority, state, stack size, high-water mark, and CPU/runtime stats.
- Heap free/min-ever-free and allocation failure hooks.
- ISR list that calls RTOS APIs plus NVIC priorities.
- Mutex/semaphore/queue ownership and waiters.
- Watchdog feed location and last-progress marker.
- Whether logging/printf is called from ISR, high-priority task, or timing-critical path.

Use `scripts/rtos_snapshot_check.py` when task/thread stack usage and states are available. Use `rtos_irq_priority.md` for Cortex-M ISR priority rules.

## Field Lessons

- The most useful RTOS snapshot is the one captured at the failure point, not after reset.
- Stack overflow often corrupts unrelated state first; a later assert may be a symptom, not the cause.
- A queue or semaphore assert is often caused by lifetime, priority, ISR context, or stack corruption rather than the queue itself.
- `printf()` and heavy logging can create timing failures, stack pressure, reentrancy problems, or deadlocks.
- Priority inversion is likely when a high-priority task blocks on a resource held by a lower-priority task while a medium-priority task keeps running.
- A watchdog feed in the idle loop can hide a stuck high-priority task; a feed in a high-priority task can hide starvation below it.
- RTOS-aware debugger views are useful, but stale symbols or optimized builds can mislead. Confirm with runtime dumps when possible.

## Triage Flow

1. Preserve the first failure: assert file/line, fault registers, task snapshot, heap, and reset reason.
2. Identify the active context: task, ISR, idle hook, timer service, or fault handler.
3. Check stack high-water marks and stack overflow hooks before chasing logic bugs.
4. Check ISR API use and interrupt priorities.
5. For deadlock/starvation, list each blocked task, resource waited on, resource owner, and owner priority.
6. For deadline misses, measure each stage and compare against period/watchdog budget.
7. Temporarily reduce logging and instrumentation to separate observer effect from root cause.

Use `scripts/freertos_wait_graph.py` when task/resource ownership and blocked waiters are known.

## Fix Patterns

- Enable asserts, stack overflow hooks, malloc failed hooks, and hard fault capture in debug builds.
- Name tasks/threads and expose a shell/debug command that prints task state, stack, heap, and last-progress marker.
- Use priority inheritance mutexes for shared resources that cross priority levels.
- Keep ISR handlers short; defer work to tasks with explicit ownership and bounded queues.
- Avoid blocking calls in timer service callbacks and high-priority control loops.
- Feed watchdog only after the critical pipeline makes progress.
