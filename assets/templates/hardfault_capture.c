/*
 * Cortex-M HardFault evidence capture skeleton.
 * Adapt logging, retention section, and reset policy for the target project.
 */
#include <stdint.h>

typedef struct {
    uint32_t r0;
    uint32_t r1;
    uint32_t r2;
    uint32_t r3;
    uint32_t r12;
    uint32_t stacked_lr;
    uint32_t stacked_pc;
    uint32_t xpsr;
    uint32_t exc_return;
    uint32_t msp;
    uint32_t psp;
    uint32_t cfsr;
    uint32_t hfsr;
    uint32_t mmfar;
    uint32_t bfar;
} hardfault_capture_t;

volatile hardfault_capture_t g_hardfault_capture;

#define SCB_CFSR  (*(volatile uint32_t *)0xE000ED28u)
#define SCB_HFSR  (*(volatile uint32_t *)0xE000ED2Cu)
#define SCB_MMFAR (*(volatile uint32_t *)0xE000ED34u)
#define SCB_BFAR  (*(volatile uint32_t *)0xE000ED38u)

static void capture_hardfault(uint32_t *stacked, uint32_t exc_return)
{
    uint32_t msp;
    uint32_t psp;

    __asm volatile ("mrs %0, msp" : "=r" (msp));
    __asm volatile ("mrs %0, psp" : "=r" (psp));

    g_hardfault_capture.r0 = stacked[0];
    g_hardfault_capture.r1 = stacked[1];
    g_hardfault_capture.r2 = stacked[2];
    g_hardfault_capture.r3 = stacked[3];
    g_hardfault_capture.r12 = stacked[4];
    g_hardfault_capture.stacked_lr = stacked[5];
    g_hardfault_capture.stacked_pc = stacked[6];
    g_hardfault_capture.xpsr = stacked[7];
    g_hardfault_capture.exc_return = exc_return;
    g_hardfault_capture.msp = msp;
    g_hardfault_capture.psp = psp;
    g_hardfault_capture.cfsr = SCB_CFSR;
    g_hardfault_capture.hfsr = SCB_HFSR;
    g_hardfault_capture.mmfar = SCB_MMFAR;
    g_hardfault_capture.bfar = SCB_BFAR;

    for (;;) {
        __asm volatile ("nop");
    }
}

__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile (
        "tst lr, #4                    \n"
        "ite eq                        \n"
        "mrseq r0, msp                 \n"
        "mrsne r0, psp                 \n"
        "mov r1, lr                    \n"
        "b capture_hardfault           \n"
    );
}
