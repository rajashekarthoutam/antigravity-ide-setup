---
name: sic-power-electronics
description: Silicon Carbide (SiC) MOSFET gate drive design, sub-microsecond fault protection (<500ns), solid-state circuit breakers (SSCB), and True-RMS power telemetry.
---

# Silicon Carbide (SiC) Power Electronics & High-Speed Circuit Protection

Engineering standards for ultra-fast solid-state circuit breakers (SSCB), isolated gate drives, and high-voltage SiC power stages.

---

## 1. High-Voltage SiC Gate Driving

- **Voltage Rails**: Typical asymmetric gate drive voltages: `+18V` for full saturation (minimizing $R_{DS(on)}$ conduction loss) and `-4V` for safe noise-immune turn-off.
- **Miller Clamp & Ringing Suppression**:
  - Integrate active Miller clamp circuits to prevent parasitics-induced spurious turn-on from high $dv/dt$ (>50V/ns).
  - Minimize gate loop parasitic inductance by routing gate-source traces as tight Kelvin-source differential pairs.

---

## 2. Sub-Microsecond (<500ns) Fault Interruption

```mermaid
flowchart LR
    Fault["Overcurrent / Short Circuit"] --> Sensor["High-Speed Shunt / Hall Sensor"]
    Sensor --> Comp["Analog Fast Comparator (<50ns)"]
    Comp --> Latch["Hardware Hardware Watchdog / Flip-Flop"]
    Latch --> Driver["Opto-Isolated Gate Driver (<150ns)"]
    Driver --> Gate["SiC Channel Clamped OFF (<250ns)"]
```

- **Zero-Firmware Trip Loop**:
  Autonomous fault detection must NEVER wait for ADC polling or software interrupts. The primary trip path is 100% hardware-latched via high-speed analog comparators directly disabling gate driver output pins within 300-500ns.
- **Clamping & Energy Absorption**:
  Use Metal Oxide Varistors (MOVs) and Transient Voltage Suppressors (TVS) sized to absorb inductive flyback energy ($E = \frac{1}{2} L I^2$) when current is abruptly interrupted at peak fault.

---

## 3. True-RMS Telemetry & Isolation

- Use galvanic opto-isolation or digital capacitive isolators (>5kV isolation rating) between high-voltage power planes and digital microcontroller domains.
- Compute True-RMS power using hardware DSP floating-point units (FPU) across 50/60Hz cycle windows.
