/*
 * FreeRTOS runtime snapshot skeleton.
 * Requires configUSE_TRACE_FACILITY and configGENERATE_RUN_TIME_STATS as needed.
 */
#include "FreeRTOS.h"
#include "task.h"
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>

#ifndef SNAPSHOT_MAX_TASKS
#define SNAPSHOT_MAX_TASKS 16
#endif

typedef void (*snapshot_write_fn)(const char *line);

static void snapshot_write_number(snapshot_write_fn write_line, const char *label, uint32_t value)
{
    char line[96];
    /* Replace snprintf if unavailable in the target C library. */
    snprintf(line, sizeof(line), "%s%lu", label, (unsigned long)value);
    write_line(line);
}

void debug_dump_freertos_snapshot(snapshot_write_fn write_line)
{
    TaskStatus_t tasks[SNAPSHOT_MAX_TASKS];
    UBaseType_t count;
    uint32_t total_runtime = 0;

    if (write_line == NULL) {
        return;
    }

    count = uxTaskGetSystemState(tasks, SNAPSHOT_MAX_TASKS, &total_runtime);
    snapshot_write_number(write_line, "task_count=", (uint32_t)count);
    snapshot_write_number(write_line, "heap_free=", (uint32_t)xPortGetFreeHeapSize());
    snapshot_write_number(write_line, "heap_min_ever_free=", (uint32_t)xPortGetMinimumEverFreeHeapSize());

    for (UBaseType_t i = 0; i < count; ++i) {
        char line[160];
        snprintf(
            line,
            sizeof(line),
            "task=%s prio=%lu state=%lu stack_high_water=%lu runtime=%lu",
            tasks[i].pcTaskName,
            (unsigned long)tasks[i].uxCurrentPriority,
            (unsigned long)tasks[i].eCurrentState,
            (unsigned long)tasks[i].usStackHighWaterMark,
            (unsigned long)tasks[i].ulRunTimeCounter
        );
        write_line(line);
    }
}
