#!/usr/bin/env python3
"""
Cross-target verification: does the same kernel produce the same number when
reached through a different binding?

The crate compiles to two deployment targets that are actually built:

  * a CPython extension module via PyO3        (feature "python")
  * a WebAssembly module via wasm-bindgen      (feature "wasm")

The blog post claims "one audited implementation" is a provenance argument. That
claim is only worth making if it is checked, because a shared implementation does
not imply shared *interface* guarantees — each binding declares its own parameter
types, and that declaration happens before the kernel runs.

This script measures three things and prints them:

  1. Agreement between the two targets on identical f64 inputs.
  2. The interface asymmetry: the Python surface exposes an entry point taking
     and returning strings (`py_dcf_exact`), so parsing happens inside the kernel.
     The WebAssembly surface exposes no equivalent — its three functions take f64
     positionally. This is reported, not asserted, because it is a property of the
     bindings rather than a failure.
  3. Whether the Python string path and the shared f64 path agree.

Prerequisites:
    pip install .                       # or maturin develop --features python
    ./build_wasm.sh                     # produces integrations/rust/pkg/

Usage (from repo root):
    python3 integrations/rust/verify_wasm_parity.py
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

RUST = Path(__file__).resolve().parent
PKG = RUST / "pkg"

# One shared case. f64-representable inputs so that the comparison isolates the
# binding rather than the literals: 0.25 and 0.03125 are exact in binary, and
# 50,000,000 is an integer.
CASE = {
    "initial_revenue": 50_000_000.0,
    "growth_rate": 0.0625,
    "ebitda_margin": 0.25,
    "tax_rate": 0.25,
    "wacc": 0.125,
    "terminal_growth": 0.03125,
    "years": 5,
}
ORDER = ["initial_revenue", "growth_rate", "ebitda_margin", "tax_rate",
         "wacc", "terminal_growth", "years"]


def fail(msg: str) -> None:
    print(f"\n  FAILED: {msg}")
    sys.exit(1)


def wasm_dcf() -> str:
    """Call wasm_calculate_dcf through node and return enterprise_value."""
    if not (PKG / "pe_finance.js").exists():
        fail(f"{PKG}/pe_finance.js not found. Run integrations/rust/build_wasm.sh first.")
    if shutil.which("node") is None:
        fail("node not on PATH; needed to execute the WebAssembly module.")

    args = ", ".join(repr(CASE[k]) for k in ORDER)
    script = (
        f'const m = require({str(PKG / "pe_finance.js")!r});'
        f'const r = JSON.parse(m.wasm_calculate_dcf({args}));'
        f'process.stdout.write(String(r.enterprise_value));'
    )
    out = subprocess.run(["node", "-e", script], capture_output=True, text=True)
    if out.returncode != 0:
        fail(f"node failed: {out.stderr.strip()[:300]}")
    return out.stdout.strip()


def python_dcf_f64() -> str:
    import pe_finance
    r = json.loads(pe_finance.py_calculate_dcf(*(CASE[k] for k in ORDER)))
    return str(r["enterprise_value"])


def python_dcf_strings(capex: str, nwc: str) -> str | None:
    """The string-in/string-out path. Unlike the shared f64 signature, this one
    requires capex_pct and nwc_pct to be stated."""
    import pe_finance
    try:
        # Returns a bare decimal string, not a JSON object.
        return pe_finance.py_dcf_exact(
            "50000000", "0.0625", "0.25", "0.25", capex, nwc, "0.125", "0.03125", 5)
    except Exception as e:                                     # noqa: BLE001
        print(f"  py_dcf_exact unavailable: {e}")
        return None


def wasm_surface() -> list[str]:
    """Read the generated .d.ts to report the WebAssembly interface as built."""
    dts = PKG / "pe_finance.d.ts"
    if not dts.exists():
        return []
    return [ln.strip() for ln in dts.read_text().splitlines()
            if ln.strip().startswith("export function")]


def main() -> int:
    print("=" * 78)
    print("CROSS-TARGET VERIFICATION — one kernel, two bindings")
    print("=" * 78)

    w = wasm_dcf()
    p = python_dcf_f64()

    print("\n1. Same kernel, same f64 inputs, two deployment targets:")
    print(f"     CPython extension (PyO3)   {p}")
    print(f"     WebAssembly (wasm-bindgen) {w}")
    if w != p:
        fail(f"targets disagree:\n    python={p}\n    wasm  ={w}")
    print(f"     -> byte-identical ({len(p)} significant characters)")

    print("\n2. Interface surfaces as built:")
    print("     CPython:     py_dcf_exact(initial_revenue: String, ...) -> String")
    print("                  py_calculate_dcf(initial_revenue: f64, ...) -> String")
    for fn in wasm_surface():
        name = fn.split("(")[0].replace("export function ", "")
        print(f"     WebAssembly: {name}(...: number) -> string")
    print("\n     The WebAssembly surface exposes no string-in entry point. The")
    print("     kernel is shared; the declared parameter types are not.")

    # The interesting part. py_calculate_dcf reaches DCFInputs::new_constant_growth,
    # which supplies capex_pct_revenue = 5% and nwc_pct_revenue = 10% that the
    # caller never passed and cannot see from the signature. The string path
    # requires both to be stated. Same formulation, different declared surface.
    bare = python_dcf_strings("0", "0")
    stated = python_dcf_strings("0.05", "0.10")
    if bare is None or stated is None:
        return 1

    print("\n3. The same formulation reached two ways:")
    print(f"     py_calculate_dcf, capex/nwc not in the signature   {p}")
    print(f"     py_dcf_exact,     capex=0.05 nwc=0.10 stated       {stated}")
    if stated != p:
        fail("the two entry points disagree even with assumptions stated; "
             "they no longer implement the same formulation")
    print("     -> byte-identical, so the kernel agrees with itself")

    delta = (float(bare) - float(p)) / float(p) * 100
    print(f"\n     py_dcf_exact,     capex=0 nwc=0                    {bare}")
    print(f"     -> {delta:+.1f}% against the f64 entry point.")
    print("     The gap is not arithmetic. py_calculate_dcf reaches")
    print("     DCFInputs::new_constant_growth, which injects capex = 5% of")
    print("     revenue and NWC = 10% of revenue as hardcoded defaults. Those")
    print("     are economic assumptions, they change the valuation by")
    print(f"     {abs(delta):.0f}%, and nothing in the signature discloses them.")

    print("\nAll assertions passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
