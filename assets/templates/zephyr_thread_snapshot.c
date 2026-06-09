/*
 * Zephyr thread/runtime snapshot skeleton.
 * Enable relevant Kconfig options such as CONFIG_THREAD_ANALYZER.
 */
#include <zephyr/kernel.h>
#include <zephyr/debug/thread_analyzer.h>
#include <zephyr/sys/printk.h>

void debug_dump_zephyr_snapshot(void)
{
    printk("uptime_ms=%lld\n", k_uptime_get());

#if defined(CONFIG_THREAD_ANALYZER)
    thread_analyzer_print();
#else
    printk("CONFIG_THREAD_ANALYZER is not enabled\n");
#endif

#if defined(CONFIG_HEAP_MEM_POOL_SIZE) && (CONFIG_HEAP_MEM_POOL_SIZE > 0)
    printk("system heap is configured; add project-specific heap stats here\n");
#endif
}
