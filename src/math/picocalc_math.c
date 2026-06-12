// picocalc_math.c — Hybrid math kernel + expr for SuperCalc.OG Phase 1+
// Thin C extension boundary: MPy calls these for speed/accuracy on hot paths.
// Built via USER_C_MODULES + micropython.cmake (LofiFren/zenodante-style base).
//
// When the custom UF2 is flashed, `import picocalc_math` succeeds from device REPL
// and calls execute in native code (RP2350 FPU for doubles).
//
// Provides: basic ops, trig/log/exp/pow, and rpn_eval (C stack machine for expressions).
// MPy side owns infix->RPN parsing and variable/env; C owns numeric + RPN dispatch.
//
// Offline-first, 320x320-aware, double baseline per DECISIONS.md.

#include "py/obj.h"
#include "py/runtime.h"
#include "py/objiter.h"
#include <math.h>
#include <string.h>

// --- Thin documented API (subject to small evolution in Phase 1) ---

STATIC mp_obj_t picocalc_math_version(void) {
    const char *v = "SuperCalc.OG-hybrid-proof-0.3";
    return mp_obj_new_str(v, strlen(v));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(picocalc_math_version_obj, picocalc_math_version);

// add: accepts int or float; returns float result (math spirit, not limited to small-int)
STATIC mp_obj_t picocalc_math_add(mp_obj_t a_in, mp_obj_t b_in) {
    double a = mp_obj_get_float(a_in);
    double b = mp_obj_get_float(b_in);
    return mp_obj_new_float(a + b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_add_obj, picocalc_math_add);

// sin(x) — demonstrates <math.h> hot path + double precision
STATIC mp_obj_t picocalc_math_sin(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    double r = sin(x);
    return mp_obj_new_float(r);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_sin_obj, picocalc_math_sin);

// sqrt(x) — useful primitive; errors on negative via runtime (or we can raise ValueError)
STATIC mp_obj_t picocalc_math_sqrt(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    if (x < 0.0) {
        mp_raise_ValueError(MP_ERROR_TEXT("sqrt of negative"));
    }
    return mp_obj_new_float(sqrt(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_sqrt_obj, picocalc_math_sqrt);

// --- Phase 1 core math additions (C hot path) ---
STATIC mp_obj_t picocalc_math_sub(mp_obj_t a_in, mp_obj_t b_in) {
    double a = mp_obj_get_float(a_in);
    double b = mp_obj_get_float(b_in);
    return mp_obj_new_float(a - b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_sub_obj, picocalc_math_sub);

STATIC mp_obj_t picocalc_math_mul(mp_obj_t a_in, mp_obj_t b_in) {
    double a = mp_obj_get_float(a_in);
    double b = mp_obj_get_float(b_in);
    return mp_obj_new_float(a * b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_mul_obj, picocalc_math_mul);

STATIC mp_obj_t picocalc_math_div(mp_obj_t a_in, mp_obj_t b_in) {
    double a = mp_obj_get_float(a_in);
    double b = mp_obj_get_float(b_in);
    if (b == 0.0) {
        mp_raise_ValueError(MP_ERROR_TEXT("division by zero"));
    }
    return mp_obj_new_float(a / b);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_div_obj, picocalc_math_div);

STATIC mp_obj_t picocalc_math_cos(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    return mp_obj_new_float(cos(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_cos_obj, picocalc_math_cos);

STATIC mp_obj_t picocalc_math_tan(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    return mp_obj_new_float(tan(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_tan_obj, picocalc_math_tan);

STATIC mp_obj_t picocalc_math_exp(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    return mp_obj_new_float(exp(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_exp_obj, picocalc_math_exp);

STATIC mp_obj_t picocalc_math_log(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    if (x <= 0.0) {
        mp_raise_ValueError(MP_ERROR_TEXT("log of non-positive"));
    }
    return mp_obj_new_float(log(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_log_obj, picocalc_math_log);

STATIC mp_obj_t picocalc_math_pow(mp_obj_t x_in, mp_obj_t y_in) {
    double x = mp_obj_get_float(x_in);
    double y = mp_obj_get_float(y_in);
    return mp_obj_new_float(pow(x, y));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(picocalc_math_pow_obj, picocalc_math_pow);

STATIC mp_obj_t picocalc_math_fabs(mp_obj_t x_in) {
    double x = mp_obj_get_float(x_in);
    return mp_obj_new_float(fabs(x));
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_fabs_obj, picocalc_math_fabs);

// rpn_eval(tokens) — C kernel for expression system (Phase 1).
// tokens: iterable of numbers (int/float) and op strings.
// Supported: binary + - * / pow ^ ; unary sin cos tan sqrt log exp fabs neg ;
// stack: dup drop swap over ; result is top of stack at end.
// Thin: MPy (or future compiler) produces token stream; C does fast stack eval with FPU doubles.
// Errors on underflow, unknown op, domain (via the leaf funcs).
#define RPN_STACK_MAX 32
STATIC mp_obj_t picocalc_math_rpn_eval(mp_obj_t tokens_in) {
    double stack[RPN_STACK_MAX];
    int sp = 0;  // stack pointer (next free)

    mp_obj_iter_buf_t iter_buf;
    mp_obj_t iter = mp_obj_get_iter(tokens_in, &iter_buf);
    mp_obj_t item;
    while ((item = mp_iternext(iter)) != MP_OBJ_STOP_ITERATION) {
        double v;
        if (mp_obj_get_float_maybe(item, &v)) {
            if (sp >= RPN_STACK_MAX) {
                mp_raise_ValueError(MP_ERROR_TEXT("rpn stack overflow"));
            }
            stack[sp++] = v;
            continue;
        }
        if (!mp_obj_is_str(item)) {
            mp_raise_ValueError(MP_ERROR_TEXT("rpn token must be number or op str"));
        }
        const char *op = mp_obj_str_get_str(item);
        if (strcmp(op, "+") == 0 || strcmp(op, "add") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double b = stack[--sp];
            double a = stack[--sp];
            stack[sp++] = a + b;
        } else if (strcmp(op, "-") == 0 || strcmp(op, "sub") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double b = stack[--sp];
            double a = stack[--sp];
            stack[sp++] = a - b;
        } else if (strcmp(op, "*") == 0 || strcmp(op, "mul") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double b = stack[--sp];
            double a = stack[--sp];
            stack[sp++] = a * b;
        } else if (strcmp(op, "/") == 0 || strcmp(op, "div") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double b = stack[--sp];
            double a = stack[--sp];
            if (b == 0.0) mp_raise_ValueError(MP_ERROR_TEXT("division by zero"));
            stack[sp++] = a / b;
        } else if (strcmp(op, "pow") == 0 || strcmp(op, "^") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double b = stack[--sp];
            double a = stack[--sp];
            stack[sp++] = pow(a, b);
        } else if (strcmp(op, "sin") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = sin(a);
        } else if (strcmp(op, "cos") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = cos(a);
        } else if (strcmp(op, "tan") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = tan(a);
        } else if (strcmp(op, "sqrt") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            if (a < 0.0) mp_raise_ValueError(MP_ERROR_TEXT("sqrt of negative"));
            stack[sp++] = sqrt(a);
        } else if (strcmp(op, "log") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            if (a <= 0.0) mp_raise_ValueError(MP_ERROR_TEXT("log of non-positive"));
            stack[sp++] = log(a);
        } else if (strcmp(op, "exp") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = exp(a);
        } else if (strcmp(op, "fabs") == 0 || strcmp(op, "abs") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = fabs(a);
        } else if (strcmp(op, "neg") == 0 || strcmp(op, "chs") == 0) {  /* HP-like chs */
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double a = stack[--sp];
            stack[sp++] = -a;
        } else if (strcmp(op, "dup") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            if (sp >= RPN_STACK_MAX) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack overflow"));
            stack[sp] = stack[sp-1];
            sp++;
        } else if (strcmp(op, "drop") == 0) {
            if (sp < 1) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            sp--;
        } else if (strcmp(op, "swap") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            double t = stack[sp-1];
            stack[sp-1] = stack[sp-2];
            stack[sp-2] = t;
        } else if (strcmp(op, "over") == 0) {
            if (sp < 2) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack underflow"));
            if (sp >= RPN_STACK_MAX) mp_raise_ValueError(MP_ERROR_TEXT("rpn stack overflow"));
            stack[sp] = stack[sp-2];
            sp++;
        } else {
            mp_raise_msg_varg(&mp_type_ValueError, MP_ERROR_TEXT("unknown rpn op: %s"), op);
        }
    }
    if (sp < 1) {
        mp_raise_ValueError(MP_ERROR_TEXT("rpn empty stack at end"));
    }
    return mp_obj_new_float(stack[sp-1]);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(picocalc_math_rpn_eval_obj, picocalc_math_rpn_eval);

STATIC const mp_rom_map_elem_t picocalc_math_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_picocalc_math) },
    { MP_ROM_QSTR(MP_QSTR_version), MP_ROM_PTR(&picocalc_math_version_obj) },
    { MP_ROM_QSTR(MP_QSTR_add),     MP_ROM_PTR(&picocalc_math_add_obj) },
    { MP_ROM_QSTR(MP_QSTR_sub),     MP_ROM_PTR(&picocalc_math_sub_obj) },
    { MP_ROM_QSTR(MP_QSTR_mul),     MP_ROM_PTR(&picocalc_math_mul_obj) },
    { MP_ROM_QSTR(MP_QSTR_div),     MP_ROM_PTR(&picocalc_math_div_obj) },
    { MP_ROM_QSTR(MP_QSTR_sin),     MP_ROM_PTR(&picocalc_math_sin_obj) },
    { MP_ROM_QSTR(MP_QSTR_cos),     MP_ROM_PTR(&picocalc_math_cos_obj) },
    { MP_ROM_QSTR(MP_QSTR_tan),     MP_ROM_PTR(&picocalc_math_tan_obj) },
    { MP_ROM_QSTR(MP_QSTR_sqrt),    MP_ROM_PTR(&picocalc_math_sqrt_obj) },
    { MP_ROM_QSTR(MP_QSTR_exp),     MP_ROM_PTR(&picocalc_math_exp_obj) },
    { MP_ROM_QSTR(MP_QSTR_log),     MP_ROM_PTR(&picocalc_math_log_obj) },
    { MP_ROM_QSTR(MP_QSTR_pow),     MP_ROM_PTR(&picocalc_math_pow_obj) },
    { MP_ROM_QSTR(MP_QSTR_fabs),    MP_ROM_PTR(&picocalc_math_fabs_obj) },
    { MP_ROM_QSTR(MP_QSTR_rpn_eval), MP_ROM_PTR(&picocalc_math_rpn_eval_obj) },
};
STATIC MP_DEFINE_CONST_DICT(picocalc_math_module_globals, picocalc_math_globals_table);

const mp_obj_module_t picocalc_math_module = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t *)&picocalc_math_module_globals,
};

MP_REGISTER_MODULE(MP_QSTR_picocalc_math, picocalc_math_module);