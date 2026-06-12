# SuperCalc.OG — Decisions Log (Living Document)

Record significant architectural, technical, and scope decisions with rationale and date. This helps the Ralph Loop reviews.

## 2026-06 (Phase 0)

### Base Firmware Choice
**Decision**: Build on LofiFren/PicoCalc (Pico 2 W focused) + zenodante/PicoCalc-micropython-driver foundations.

**Rationale**:
- Explicit Pico 2 W support and prebuilt UF2s.
- Excellent developer experience (dashboard, MCP, on-device editor, file sync).
- Already includes high-quality C modules for display (picocalcdisplay), VT100 terminal, keyboard (I2C), SD.
- Proven ulab + eigenmath builds — perfect for symbolic/numeric calculator work.
- Community momentum and the official ClockworkPi repo even calls out graphing/scientific calculations as a natural extension.

**Alternative considered**: Pure official Pico SDK C application or PicoMite BASIC. Rejected for this project because hybrid MPy + C + existing excellent hardware abstractions give fastest path to a rich calculator while still allowing deep C optimization.

### Custom Language Direction
**Decision**: Create a custom RPL-inspired language (programs as first-class objects, excellent stack model, locals via `->` or equivalent, control structures) executed by a small dedicated C VM/bytecode interpreter. Support both text program entry and (later) keystroke recording mode.

**Rationale**:
- Matches user's explicit request for "functionality of the old HP programmables" and "custom language for the functions".
- RPL (HP-48 lineage) is the pinnacle of calculator programmability — we want that power and expressiveness.
- C VM gives the speed and deterministic behavior that makes programming feel good (classic HPs were responsive for their time).
- Still allows a friendly infix/algebraic entry mode on top for everyday use.

### Hybrid Boundary
**Decision**: Keep the boundary thin and explicit. MPy owns UI, parsers (initially), program source management, high-level orchestration. C owns math kernel, plotting sampling + rendering primitives, and the language VM/bytecode execution.

**Rationale**:
- Lets us iterate UI and language syntax quickly in Python.
- Puts performance-critical loops (function evaluation during plotting, VM inner loop, heavy numerics) where they belong.
- Plays nicely with the existing frozen C module pattern in the base ports.

### Graphing Color & Memory Strategy
**Decision**: Start with the existing LUT / reduced-bit modes from the base display driver (excellent for speed and RAM on 320x320). Extend the LUT or add higher-fidelity paths only where graphing quality justifies it. Leverage PSRAM for any large plot data.

**Rationale**:
- The community ports already solved the hard problem of making the SPI display feel good.
- Graphing is one of the most RAM- and CPU-intensive things we will do — we must be disciplined.
- 320x320 square is a gift for plots; we can deliver very usable graphs even in 16-color or 8-color + dither modes.

### Offline-First Policy
**Decision**: All core features (calculation, graphing, programming, storage) must work with zero network. WiFi/BT features (if any) are strictly optional and non-blocking for main use.

**Rationale**:
- Matches user requirement.
- Classic HP programmables were self-contained powerhouses — that independence is part of the charm and reliability.
- Keeps the device useful in the field, classroom, or anywhere without connectivity.

### Numeric Baseline
**Decision**: Double-precision floating point as the primary numeric type for Phase 1–2, with clear extension points for higher-accuracy techniques (compensated summation, decimal, etc.) and integer/fraction types later. Complex numbers supported from the start.

**Rationale**:
- Double is fast on RP2350 (has FPU), widely understood, and sufficient for the vast majority of scientific/graphing work.
- We can demonstrate clear accuracy wins by moving hot functions into well-implemented C.
- ulab + eigenmath already bring strong numeric and symbolic capabilities we can build on.

### Parser Location (Initial)
**Decision**: Infix and RPN parsers start in MicroPython for rapid iteration and easy experimentation with syntax. Hot evaluation path immediately calls into C. We can move parser pieces to C later if profiling shows it is a bottleneck.

**Rationale**:
- Syntax is likely to evolve during Phase 1–2. Python is far faster to change.
- The expensive work is evaluation + plotting loops — those go to C immediately.

## Future Decision Areas (to be filled)

- Exact local variable syntax for the custom language.
- Whether to offer a pure keystroke programming mode in addition to text RPL-style.
- Depth of units system (full dimensional analysis vs. simple tagged units).
- How much CAS surface we expose directly vs. through eigenmath calls.
- Default view window and zoom behavior for graphing (HP-like vs. Desmos-like).
- Whether the custom firmware will be a single "everything" UF2 or a base + loadable modules model.

---

Add entries at the end of each phase or when a significant choice is locked. Include date, decision, rationale, and alternatives considered.
