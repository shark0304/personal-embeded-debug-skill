# FreeRTOS Deadlock Runbook

## Trigger symptoms

- Task starvation, queue/semaphore assert, watchdog reset, no idle time, blocked high-priority task.

## Minimum evidence

- Task list, priorities, states, stack high-water marks, heap free/min-ever-free.
- Resource owners/waiters for mutexes, queues, semaphores.
- ISR priorities and FromISR API usage.

## Fast triage

1. Run `rtos_snapshot_check.py`.
2. Model owners/waiters with `freertos_wait_graph.py`.
3. Check ISR priority rules with `nvic_priority_check.py`.

## High-probability root causes

- Priority inversion, deadlock cycle, blocking in callback, ISR API misuse, heap/stack exhaustion.

## Scripts to run

- `scripts/rtos_snapshot_check.py`
- `scripts/freertos_wait_graph.py`
- `scripts/nvic_priority_check.py`

## Manual experiments

- Reduce logging, enable asserts, record last progress markers, temporarily add resource ownership tracing.

## Fix patterns

- Priority inheritance mutex, bounded queues, correct ISR deferral, shorter critical sections.

## Regression tests

- Task snapshot golden packet and watchdog no-reset HIL run.

## Do-not-guess rules

- Do not add delays before proving ownership and priority relationships.
