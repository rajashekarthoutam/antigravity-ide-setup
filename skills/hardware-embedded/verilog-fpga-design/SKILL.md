---
name: verilog-fpga-design
description: Cycle-accurate Verilog HDL, synchronous FSM design, Clock Domain Crossing (CDC), testbench generation, and FPGA timing closure.
---

# Cycle-Accurate Verilog HDL & FPGA Architecture

Production standards for cycle-accurate digital logic synthesis, FPGA targeting (Xilinx/AMD, Intel, Gowin, Lattice), and hardware verification.

---

## 1. Synthesis Invariants

- **Synchronous Resets**: Standardize on active-low (`rst_n`) or active-high (`rst`) per target architecture. Always reset all state elements in sequential blocks:
  ```verilog
  always @(posedge clk or negedge rst_n) begin
      if (!rst_n) begin
          state_reg <= IDLE;
          counter   <= 32'd0;
      end else begin
          state_reg <= next_state;
          counter   <= next_counter;
      end
  end
  ```
- **Blocking vs. Non-Blocking**:
  - Sequential logic (`always @(posedge clk)`): Strictly use non-blocking assignments (`<=`).
  - Combinational logic (`always @(*)`): Strictly use blocking assignments (`=`).
  - Never mix `<=` and `=` in the same procedural block.
- **Latch Prevention**: In combinational blocks, assign default values at the top to prevent inferred memory latches.

---

## 2. Clock Domain Crossing (CDC) Safety

- **1-Bit Signals**: Use a 2-stage or 3-stage synchronizer flip-flop chain:
  ```verilog
  reg sync_ff1, sync_ff2;
  always @(posedge dest_clk) begin
      sync_ff1 <= async_in;
      sync_ff2 <= sync_ff1;
  end
  assign sync_out = sync_ff2;
  ```
- **Multi-Bit Vectors**: Never synchronize multi-bit data directly through double-FF chains due to skew. Use:
  - Asynchronous FIFOs with Gray code read/write pointers.
  - Four-phase or two-phase handshake protocols (`req`/`ack`).

---

## 3. Finite State Machine (FSM) Design (3-Block Pattern)
1. **State Register**: Sequential `always @(posedge clk)` updating `current_state <= next_state`.
2. **Next State Logic**: Combinational `always @(*)` evaluating input conditions.
3. **Output Logic**: Registered or combinational output generation to prevent glitching.
