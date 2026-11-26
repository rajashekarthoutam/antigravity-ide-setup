---
name: stm32-firmware-freertos
description: Bare-metal and FreeRTOS firmware design on STM32 (Cortex-M4F), DMA-buffered ADC sampling, hardware timer interrupts, and analog watchdogs.
---

# STM32 Firmware & FreeRTOS Architecture

Production guidelines for deterministic, low-latency firmware targeting ARM Cortex-M4/M7 microcontrollers (STM32G4, STM32F4, STM32H7).

---

## 1. Real-Time Determinism & Interrupt Priorities

- **NVIC Grouping**: Set `NVIC_PriorityGroupConfig(NVIC_PriorityGroup_4)` when using FreeRTOS.
- **SysTick & PendSV**: Set to the lowest possible priority (`0x0F` / 15) so hardware ISRs preempt OS scheduling.
- **FromISR API Invariant**: Never call standard FreeRTOS blocking APIs from an ISR. Always use `xQueueSendFromISR`, `xSemaphoreGiveFromISR` with `pxHigherPriorityTaskWoken`.

---

## 2. Peripheral Pipelining with DMA

- **Zero-CPU ADC Sampling**:
  - Configure high-speed ADC with Timer Trigger Output (TRGO).
  - Stream conversion results directly into RAM ring buffers via Circular DMA.
  - Process samples in the `HAL_ADC_ConvCpltCallback` and `HAL_ADC_ConvHalfCpltCallback` to achieve ping-pong buffering without dropped samples.
- **Analog Hardware Watchdog (AWD)**:
  - Configure AWD thresholds in hardware to trigger emergency trip routines in sub-microsecond timescales independently of firmware execution loops.

---

## 3. FreeRTOS Task Architecture

- **Task Allocation**: Prefer static allocation (`xTaskCreateStatic`) for critical embedded loops to eliminate heap fragmentation risks.
- **Queue Buffering**: Decouple high-frequency sensor acquisition tasks from telemetry/communication tasks using bounded queues.
