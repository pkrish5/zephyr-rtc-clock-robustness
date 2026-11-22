#!/usr/bin/env python3
"""Mechanically generate first-order mutants of the pinned STM32 RTC drivers.

Operator set: the type-free subset of Agrawal et al., "Design of Mutant
Operators for the C Programming Language", Purdue SERC-TR-41-P (Rev 1.04,
2006; first edition 1989):

  Ocor binary-operator replacement (Table 4): ORRN, OAAN, OBBN, OLLN, OSSN,
      OAAA, OBBA, OSSA. Each occurrence is replaced by every other operator of
      the same class.
  OLNG (10.2.2): for x op y with op in {&&, ||}: x op !y, !x op y, !(x op y).
  OCNG (10.2.3): negate the controlling condition of if, while, do-while and
      the for condition. (The ?: form is not implemented.)
  SSDL (9.3): delete each statement in a function body, keeping a ';'.

CRCR, VTWD and other variable/constant operators need type information and
are not used. No mutant is chosen by hand: every site the rules match in an
active line of a function body is emitted, then textual duplicates are
removed.

Active lines: a line is mutable only if the C preprocessor, run with the
recorded configuration of a test application that links the file, keeps it.
Lines excluded by #if for this board/configuration and preprocessor
directives are not mutated (they cannot change the compiled F4 driver).

Usage: generate_mutants.py --out DIR   (refuses to overwrite DIR)
"""
import argparse
import hashlib
import json
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZEPHYR = ROOT / "subjects/upstream/zephyr"
RTC_CC = ROOT / "generated/spec_context_factorial_v1/build_probe/sdk_restored_r01/compile_commands.json"
COUNTER_BUILD = ROOT / ("notes/counter_natural_recovery_2026-11-20_v1/verified-3598828-v1/output/"
                        "builds/natural-original/build/zephyr")

TARGETS = {
    "rtc_ll_stm32.c": ZEPHYR / "drivers/rtc/rtc_ll_stm32.c",
    "counter_ll_stm32_rtc.c": ZEPHYR / "drivers/counter/counter_ll_stm32_rtc.c",
}

CLASSES = {
    "ORRN": ["<", "<=", ">", ">=", "==", "!="],
    "OAAN": ["+", "-", "*", "/", "%"],
    "OBBN": ["&", "|", "^"],
    "OLLN": ["&&", "||"],
    "OSSN": ["<<", ">>"],
    "OAAA": ["+=", "-=", "*=", "/=", "%="],
    "OBBA": ["&=", "|=", "^="],
    "OSSA": ["<<=", ">>="],
}
OP_CLASS = {op: name for name, ops in CLASSES.items() for op in ops}
PUNCT = sorted(["<<=", ">>=", "->", "++", "--", "<<", ">>", "<=", ">=", "==", "!=", "&&", "||",
                "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "...",
                "+", "-", "*", "/", "%", "&", "|", "^", "<", ">", "=", "!", "~", "?", ":",
                ";", ",", ".", "(", ")", "[", "]", "{", "}"], key=len, reverse=True)
KEYWORDS = {"return", "sizeof", "case", "if", "while", "for", "do", "switch", "else", "goto",
            "break", "continue", "default", "typedef", "static", "const", "volatile", "extern",
            "struct", "union", "enum", "inline", "register", "auto", "signed", "unsigned"}
TYPE_WORDS = {"void", "char", "short", "int", "long", "float", "double", "bool", "signed",
              "unsigned", "const", "volatile", "struct", "union", "enum", "static", "register"}
AMBIGUOUS = {"+", "-", "*", "&"}  # binary only when preceded by an operand


def is_type_name(tok):
    return tok in TYPE_WORDS or tok.endswith("_t")


# ---------------------------------------------------------------- active lines
def zephyr_flags(cmd):
    """Keep only preprocessor-relevant flags of a recorded GCC command."""
    args = shlex.split(cmd)
    keep, i = [], 0
    while i < len(args):
        a = args[i]
        if a in ("-imacros", "-isystem", "-include"):
            keep += [a, args[i + 1]]; i += 2; continue
        if a.startswith(("-D", "-I", "-std=")):
            keep.append(a)
        i += 1
    return keep


def counter_autoconf(dst):
    """Write autoconf.h from the archived counter .config (Kconfig's own mapping)."""
    lines = []
    for raw in (COUNTER_BUILD / ".config").read_text().splitlines():
        m = re.match(r"(CONFIG_[A-Za-z0-9_]+)=(.*)$", raw)
        if not m:
            continue
        key, val = m.groups()
        if val == "y":
            val = "1"
        elif val == "m":
            continue
        lines.append(f"#define {key} {val}")
    dst.write_text("\n".join(lines) + "\n")


STUBS = Path(tempfile.mkdtemp(prefix="rtcmut-")) / "stubs"
STUBS.mkdir()
STUB_LOG = set()
SKIPPED_SSDL = []


def marker_copy(src):
    """Copy of src whose non-directive lines are replaced by unique line tokens.

    Directive lines (with continuations) are kept verbatim, so conditional
    inclusion is evaluated exactly; each surviving token marks an active line.
    """
    out, cont = [], False
    for n, line in enumerate(src.read_text().split("\n"), 1):
        directive = cont or line.lstrip().startswith("#")
        cont = directive and line.rstrip().endswith("\\")
        out.append(line if directive else f"RTCMUTLINE_{n}_")
    dst = STUBS.parent / f"marker-{src.name}"
    dst.write_text("\n".join(out))
    return dst


def preprocess_active_lines(src, flags):
    """Active lines of src under clang -E with the recorded configuration.

    The SDK's picolibc headers are not available locally; libc headers that are
    missing are replaced by empty stubs (recorded). Conditional compilation in
    these drivers depends on Kconfig/devicetree macros, not on libc contents.
    """
    copy = marker_copy(src)
    stubs = []
    for _ in range(50):
        cmd = ["clang", "-E", "-P", "-target", "arm-none-eabi", "-mcpu=cortex-m4", "-mthumb",
               "-ffreestanding", "-Wno-everything", "-iquote", str(src.parent), *flags,
               "-idirafter", str(STUBS), str(copy)]
        out = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"fatal error: '([^']+)' file not found", out.stderr)
        if out.returncode == 0 or not m:
            break
        stub = STUBS / m.group(1)
        stub.parent.mkdir(parents=True, exist_ok=True)
        stub.write_text("/* empty stub for active-line analysis */\n")
        stubs.append(m.group(1))
    if out.returncode != 0:
        raise RuntimeError(f"preprocessing failed for {src.name}:\n{out.stderr[-3000:]}")
    STUB_LOG.update(stubs)
    return {int(x) for x in re.findall(r"RTCMUTLINE_(\d+)_", out.stdout)}


def configurations():
    entries = json.loads(RTC_CC.read_text())
    rtc = next(e for e in entries if e["file"].endswith("rtc_ll_stm32.c"))
    base = zephyr_flags(rtc["command"])
    rtc_cfgs = {"rtc_counting": base, "rtc_alarm": base + ["-DCONFIG_RTC_ALARM=1"]}
    tmp = Path(tempfile.mkdtemp())
    counter_autoconf(tmp / "autoconf.h")
    counter = []
    skip = False
    for i, a in enumerate(base):
        if skip:
            skip = False; continue
        if a == "-imacros" and base[i + 1].endswith("autoconf.h"):
            counter += ["-imacros", str(tmp / "autoconf.h")]; skip = True; continue
        if a.startswith("-I") and "build_probe" in a:
            gen = COUNTER_BUILD / "include/generated/zephyr"
            # devicetree_generated.h comes from the archived counter build; other
            # generated headers (syscalls etc.) are configuration-independent here.
            counter += [f"-I{gen}", a]; continue
        counter.append(a)
    return {"rtc_ll_stm32.c": rtc_cfgs, "counter_ll_stm32_rtc.c": {"counter_basic": counter}}


# ---------------------------------------------------------------- lexing
def mask(text, active):
    """Blank comments, strings, directives and inactive lines, preserving offsets."""
    out = list(text)
    n, i = len(text), 0
    def blank(a, b):
        for k in range(a, b):
            if out[k] != "\n":
                out[k] = " "
    while i < n:
        if text.startswith("/*", i):
            j = text.find("*/", i + 2); j = n if j < 0 else j + 2; blank(i, j); i = j
        elif text.startswith("//", i):
            j = text.find("\n", i); j = n if j < 0 else j; blank(i, j); i = j
        elif text[i] in "\"'":
            q, j = text[i], i + 1
            while j < n and text[j] != q:
                j += 2 if text[j] == "\\" else 1
            blank(i + 1, j)  # keep quotes so a literal stays an operand
            i = j + 1
        else:
            i += 1
    masked = "".join(out)
    lines = masked.split("\n")
    in_directive = False
    for k, line in enumerate(lines):
        lineno = k + 1
        directive = in_directive or line.lstrip().startswith("#")
        in_directive = directive and text.split("\n")[k].rstrip().endswith("\\")
        if directive or lineno not in active:
            lines[k] = " " * len(line)
    return "\n".join(lines)


TOKEN = re.compile(r"\s+|(?P<num>\.?\d[\w.]*)|(?P<id>[A-Za-z_]\w*)|(?P<str>\"[^\"\n]*\"|'[^'\n]*')|(?P<p>"
                   + "|".join(re.escape(p) for p in PUNCT) + ")|(?P<other>.)")


def tokenize(masked):
    toks = []
    for m in TOKEN.finditer(masked):
        kind = m.lastgroup
        if kind is None:
            continue
        toks.append(dict(kind=kind, text=m.group(), start=m.start(), end=m.end()))
    return toks


def match_pairs(toks):
    pair, stack = {}, []
    for i, t in enumerate(toks):
        if t["text"] in "([{" and t["kind"] == "p":
            stack.append(i)
        elif t["text"] in ")]}" and t["kind"] == "p":
            if not stack:
                raise RuntimeError(f"unbalanced {t['text']} at offset {t['start']}")
            j = stack.pop(); pair[i] = j; pair[j] = i
    if stack:
        raise RuntimeError("unbalanced brackets")
    return pair


def function_bodies(toks, pair):
    bodies, depth, i = [], 0, 0
    while i < len(toks):
        t = toks[i]
        if t["text"] == "{" and t["kind"] == "p":
            prev = toks[i - 1]["text"] if i else ""
            if prev == ")":
                bodies.append((i, pair[i]))
            i = pair[i] + 1; continue
        i += 1
    return bodies


def is_cast_close(toks, pair, i):
    """True if toks[i] == ')' closes a cast such as (uint32_t) or (struct x *)."""
    j = pair[i]
    inner = [t["text"] for t in toks[j + 1:i]]
    if not inner:
        return False
    words = [w for w in inner if w != "*"]
    return bool(words) and all(re.fullmatch(r"[A-Za-z_]\w*", w) for w in words) and (
        is_type_name(words[0]) or "*" in inner or words[0] in ("struct", "union", "enum"))


def is_binary(toks, pair, i):
    t = toks[i]["text"]
    if t not in AMBIGUOUS:
        return True
    p = toks[i - 1]
    if p["kind"] in ("num", "str"):
        return True
    if p["kind"] == "id":
        if t == "*" and i >= 2 and toks[i - 2]["text"] in ("struct", "union", "enum"):
            return False  # declarator such as `struct foo *p`
        return p["text"] not in KEYWORDS and not is_type_name(p["text"])
    if p["text"] in (")", "]"):
        return not (p["text"] == ")" and is_cast_close(toks, pair, i - 1))
    return False


# ---------------------------------------------------------------- statements
def parse_statements(toks, pair, lo, hi, found):
    """Collect (start_tok, end_tok, kind) statements strictly inside the block (lo, hi)."""
    i = lo + 1
    while i < hi:
        i = parse_stmt(toks, pair, i, hi, found)


def parse_stmt(toks, pair, i, hi, found):
    t = toks[i]["text"]
    # labels: case X:, default:, ident:
    if t in ("case", "default"):
        j = i
        while toks[j]["text"] != ":":
            j += 1
        return j + 1
    if toks[i]["kind"] == "id" and i + 1 < hi and toks[i + 1]["text"] == ":" and t not in KEYWORDS:
        return i + 2
    if t == ";":
        return i + 1
    if t == "{":
        end = pair[i]
        if end > i + 1:
            found.append((i, end, "compound"))
        parse_statements(toks, pair, i, end, found)
        return end + 1
    if t in ("if", "while", "switch", "for"):
        close = pair[i + 1]
        body_end = parse_stmt(toks, pair, close + 1, hi, found)
        if t == "if" and body_end < hi and toks[body_end]["text"] == "else":
            body_end = parse_stmt(toks, pair, body_end + 1, hi, found)
        found.append((i, body_end - 1, t))
        return body_end
    if t == "do":
        body_end = parse_stmt(toks, pair, i + 1, hi, found)
        assert toks[body_end]["text"] == "while"
        close = pair[body_end + 1]
        assert toks[close + 1]["text"] == ";"
        found.append((i, close + 1, "do"))
        return close + 2
    # expression / jump / declaration statement: scan to ';' at depth 0
    j = i
    while toks[j]["text"] != ";":
        if toks[j]["text"] == "{" and toks[j - 1]["text"] == ")":
            # statement-like macro followed by a block, e.g. K_SPINLOCK(&lock) { ... }
            end = pair[j]
            parse_statements(toks, pair, j, end, found)
            found.append((i, end, "macro_block"))
            return end + 1
        if toks[j]["text"] in "([{" and toks[j]["kind"] == "p":
            j = pair[j]
        j += 1
    words = [x["text"] for x in toks[i:j]]
    is_decl = bool(words) and (is_type_name(words[0]) or (
        len(words) > 1 and toks[i]["kind"] == "id" and toks[i + 1]["kind"] == "id" and words[0] not in KEYWORDS)
        or (len(words) > 2 and toks[i]["kind"] == "id" and words[1] == "*" and toks[i + 2]["kind"] == "id"
            and len(words) > 3 and words[3] in ("=", ";", "[", ",")))
    if not is_decl:
        found.append((i, j, "expr" if words[0] not in ("return", "break", "continue", "goto") else words[0]))
    return j + 1


# ---------------------------------------------------------------- operators
def mutants_for(name, text, toks, pair, bodies):
    out = []
    lines = text.count("\n", 0)
    def line_of(off):
        return text.count("\n", 0, off) + 1
    def add(op, a, b, repl, note):
        out.append(dict(file=name, operator=op, start=a, end=b, line=line_of(a),
                        original=text[a:b], replacement=repl, site=note))
    for lo, hi in bodies:
        for i in range(lo + 1, hi):
            t = toks[i]
            if t["kind"] != "p":
                continue
            op = t["text"]
            cls = OP_CLASS.get(op)
            if cls and is_binary(toks, pair, i):
                for other in CLASSES[cls]:
                    if other != op:
                        add(cls, t["start"], t["end"], other, f"{op}->{other}")
            if op in ("&&", "||"):
                # operand extents: to the nearest enclosing delimiter at the same depth
                # operands extend to the nearest same-depth logical operator or delimiter
                stops = {"&&", "||", ",", "?", ":", ";", "=", "return"} | set(CLASSES["OAAA"]) \
                    | set(CLASSES["OBBA"]) | set(CLASSES["OSSA"])
                a = i - 1
                while a > lo:
                    x = toks[a]["text"]
                    if x in (")", "]"):
                        a = pair[a] - 1
                    elif x in stops or x in ("(", "[", "{"):
                        break
                    else:
                        a -= 1
                a += 1
                b = i + 1
                while b < hi:
                    x = toks[b]["text"]
                    if x in ("(", "["):
                        b = pair[b] + 1
                    elif x in stops or x in (")", "]", "}"):
                        break
                    else:
                        b += 1
                b -= 1
                xs, xe = toks[a]["start"], toks[i - 1]["end"]
                ys, ye = toks[i + 1]["start"], toks[b]["end"]
                X, Y = text[xs:xe], text[ys:ye]
                add("OLNG", xs, ye, f"{X} {op} !({Y})", "x op !y")
                add("OLNG", xs, ye, f"!({X}) {op} {Y}", "!x op y")
                add("OLNG", xs, ye, f"!({X} {op} {Y})", "!(x op y)")
        for i in range(lo + 1, hi):
            t = toks[i]
            if t["kind"] == "id" and t["text"] in ("if", "while", "for") and toks[i + 1]["text"] == "(":
                o, c = i + 1, pair[i + 1]
                if t["text"] == "for":
                    semis = [k for k in range(o + 1, c) if toks[k]["text"] == ";"
                             and not any(o < pair.get(m, -1) < k < m or False for m in ())]
                    depth_semis = []
                    k = o + 1
                    while k < c:
                        if toks[k]["text"] in ("(", "["):
                            k = pair[k]
                        elif toks[k]["text"] == ";":
                            depth_semis.append(k)
                        k += 1
                    if len(depth_semis) != 2 or depth_semis[1] == depth_semis[0] + 1:
                        continue
                    s, e = toks[depth_semis[0] + 1]["start"], toks[depth_semis[1] - 1]["end"]
                else:
                    if c == o + 1:
                        continue
                    s, e = toks[o + 1]["start"], toks[c - 1]["end"]
                add("OCNG", s, e, f"!({text[s:e]})", t["text"])
        stmts = []
        parse_statements(toks, pair, lo, hi, stmts)
        for a, b, kind in stmts:
            s, e = toks[a]["start"], toks[b]["end"]
            if re.search(r"^[ \t]*#", text[s:e], re.M):
                SKIPPED_SSDL.append(dict(file=name, line=line_of(s), kind=kind,
                                         reason="statement spans a preprocessor directive"))
                continue
            add("SSDL", s, e, ";", kind)
    return out


def apply(text, m):
    return text[:m["start"]] + m["replacement"] + text[m["end"]:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    cfgs = configurations()
    summary = {}
    with (args.out / "mutants.jsonl").open("x") as fh:
        for name, src in TARGETS.items():
            text = src.read_text()
            active = set()
            per_cfg = {}
            for cfg, flags in cfgs[name].items():
                lines = preprocess_active_lines(src, flags)
                per_cfg[cfg] = len(lines); active |= lines
            masked = mask(text, active)
            toks = tokenize(masked)
            pair = match_pairs(toks)
            bodies = function_bodies(toks, pair)
            raw = mutants_for(name, text, toks, pair, bodies)
            seen, kept, dup = {}, [], 0
            for m in sorted(raw, key=lambda m: (m["start"], m["end"], m["operator"], m["replacement"])):
                mutated = apply(text, m)
                h = hashlib.sha256(mutated.encode()).hexdigest()
                if h in seen or mutated == text:
                    dup += 1; continue
                seen[h] = True
                m["mutated_sha256"] = h
                m["id"] = f"{name.split('.')[0]}-{len(kept) + 1:05d}"
                kept.append(m)
                fh.write(json.dumps(m, sort_keys=True) + "\n")
            by_op = {}
            for m in kept:
                by_op[m["operator"]] = by_op.get(m["operator"], 0) + 1
            code_lines = {m["line"] for m in kept}
            summary[name] = dict(source=str(src.relative_to(ROOT)),
                                 source_sha256=hashlib.sha256(text.encode()).hexdigest(),
                                 total_lines=text.count("\n"), active_lines_union=len(active),
                                 active_lines_by_configuration=per_cfg, function_bodies=len(bodies),
                                 generated=len(raw), textual_duplicates_removed=dup,
                                 mutants=len(kept), by_operator=dict(sorted(by_op.items())),
                                 mutated_lines=len(code_lines))
    summary["_libc_header_stubs_for_active_line_analysis"] = sorted(STUB_LOG)
    summary["_ssdl_sites_not_generated"] = SKIPPED_SSDL
    (args.out / "generation_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
