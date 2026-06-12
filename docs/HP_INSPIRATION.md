# HP Programmable Calculator Inspiration Notes

**Goal for SuperCalc.OG**: Capture the *soul* and *power* of the classic HP programmable machines — especially the HP-41 series and the RPL machines (HP-48, 49, 50) — while being native and delightful on the PicoCalc hardware.

## What Made the HP Programmables Special

### HP-41C / CV / CX (Keystroke Programming)
- **Alpha-numeric display** + full keyboard with many shifted functions.
- **Programmable with labels, subroutines, conditionals, loops, indirect addressing**.
- **User-defined functions** that could be assigned to keys.
- **Modules / extensions** (application pacs) that added serious capability (math, stats, surveying, etc.).
- **"Synthetic programming"** culture — people pushed the machine far beyond original intent.
- Excellent catalog of functions, clear "shift" discipline.
- Strong emphasis on **stack + LASTx** discipline for reliable calculations.

### HP-48 / 49 / 50 Series (RPL — Reverse Polish Lisp)
This is the gold standard for "programmable calculator as real computer".

- **RPL language**: A true Lisp-like language that is stack-based. Programs are objects (`<< ... >>`).
- **First-class programs**: You can store a program in a variable, pass it as an argument, return it, build lists of programs, etc.
- **Rich object system**: Numbers (real, complex, integer, fraction), arrays/matrices, lists, strings, programs, algebraic expressions, graphics objects, units with dimensions, etc.
- **Local variables**: `-> x y << ... >>` syntax for clean scoping.
- **Powerful stack manipulation** and **stack-based thinking** as a first-class skill.
- **Conditionals and loops** that feel natural in postfix: `IF ... THEN ... ELSE ... END`, `START ... NEXT`, `FOR ... NEXT`, `DO ... UNTIL`, `WHILE ... REPEAT`.
- **User libraries** and the concept of "soft menus" (application-specific key assignments).
- **Equation writer** (2D pretty printing of algebraics) alongside pure stack/RPN.
- **Units** with automatic conversion and dimensional analysis — one of the best ever implemented on a handheld.
- **CAS** (especially on 49/50) that could do symbolic math, integration, differentiation, solving.
- **Graphics**: Plotting with trace, zoom, intersection finding, etc., all integrated with the programming model.
- **Extremely long battery life** and "always on" feel (instant on from deep sleep in many cases).

**The magic**: A person could carry one device that was simultaneously:
- A powerful scientific calculator
- A programmable computer with a real language
- A CAS
- A data logger / custom instrument (via I/O)
- A personal library of tools they wrote themselves

## What We Want to Emulate (Prioritized for Our Project)

1. **Programmability that feels powerful and fun**
   - User can create named programs and functions that persist on SD.
   - Clean local variables and control structures.
   - Ability to build higher-order things (programs that take programs as arguments, generate other programs).

2. **Stack discipline + RPN as a first-class mode**
   - Even if we offer nice infix entry, the underlying engine and the "pro" mode should reward RPN/RPL thinking.

3. **Algebraic + RPN/RPL coexistence**
   - HP-48 let you enter algebraics that could be evaluated on the stack. We should support both direct algebraic entry and pure stack work.

4. **Units & constants as first-class citizens** (later phases)
   - Being able to say `5_m / 2_s` or attach units to results is incredibly satisfying.

5. **Catalog / discoverability**
   - On-device way to find functions, programs, and examples.

6. **Performance that doesn't kill the magic**
   - Classic HPs felt snappy for their era. Our C VM + math kernel must make user programs feel fast.

7. **"It just works" for real work**
   - Reliable numerics, good solvers, graphing you can actually use to find roots/intersections/areas.

## Specific Features to Steal / Adapt

- `LASTx` (or LAST stack) behavior.
- Soft menus / context-sensitive actions (we can do this with on-screen labels + physical keys).
- Program objects that are editable and runnable.
- Local variable syntax that is clean (`->` or a modern equivalent).
- Strong separation between "enter a calculation" and "I'm programming now".
- The idea that the device grows with the user — a beginner can use it as a fancy calculator; an expert writes a personal library of solvers and plotters.

## What We Can Improve On (Modern Advantages)

- Much more RAM + fast SD for huge user libraries and data sets.
- Real color (even if reduced-bit via LUT) and square 320×320 screen — graphing can be genuinely good.
- Full backlit QWERTY instead of the classic HP key-per-function density (trade-off: we have to design good shift layers or command entry).
- Faster CPU (RP2350) + ability to write hot code in C.
- On-device text editor that is actually pleasant (the community ports already have good ones).
- Modern language ergonomics while keeping the RPL soul (we don't have to be 100% syntactically compatible).

## Language Design Direction (Initial)

For Phase 2 we will create a **custom language** that is:
- RPL-inspired in semantics and power (programs as objects, excellent stack model, locals, control structures).
- More ergonomic to type on a QWERTY keyboard than classic RPL (less `<<` `>>` ceremony if possible, while keeping the spirit).
- Compiled or quickly interpreted by a small C VM for speed.

Two modes we may eventually offer:
- **RPL / Text Program mode** (the powerful one).
- **Keystroke / HP-41 style** (record keypresses, with labels and conditionals) for users who love that workflow.

We will validate the language with real HP-style example programs (quadratic formula as a program, numerical integration by rectangle rule, simple games or simulations, custom solvers, etc.).

## References (for the team)

- HP-48 Owner's Manual / Programming Examples (still some of the best written calculator docs ever).
- "RPL: A Language for Programmable Calculators" type articles and the HP Museum archives.
- Existing RPL implementations and emulators for exact semantics when we need fidelity.
- The community PicoCalc ports that already mention "graphing functions and scientific calculations" as target features.

---

We are not building an emulator. We are building a **spiritual successor** that a serious HP-48 fan would enjoy using on this beautiful little machine, while also being accessible to someone who just wants a great graphing calculator with some programming power.
