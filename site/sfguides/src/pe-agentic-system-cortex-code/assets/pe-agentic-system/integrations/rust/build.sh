#!/usr/bin/env bash
#
# Build and install the pe_finance Rust extension.
#
# Why this script exists: the working sequence has four non-obvious steps that
# each cost time when discovered the hard way. They are documented inline.
#
# Usage:
#   ./build.sh              # build release wheel + install into current Python
#   ./build.sh --test       # also run cargo tests and the parity suite
#   ./build.sh --debug      # faster compile, slower runtime (don't benchmark this)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PROFILE="--release"
RUN_TESTS=0

for arg in "$@"; do
  case "$arg" in
    --test)  RUN_TESTS=1 ;;
    --debug) PROFILE="" ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cd "$SCRIPT_DIR"

# ---------------------------------------------------------------------------
# GOTCHA 1: rustup installs to ~/.cargo/bin but does not always modify PATH
# (and will not have done so at all if installed with --no-modify-path).
# ---------------------------------------------------------------------------
export PATH="$HOME/.cargo/bin:$PATH"

if ! command -v cargo >/dev/null 2>&1; then
  echo "ERROR: cargo not found."
  echo
  echo "  Install the Rust toolchain:"
  echo "    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal"
  echo "    export PATH=\"\$HOME/.cargo/bin:\$PATH\""
  echo
  exit 1
fi

echo "==> toolchain"
echo "    $(rustc --version)"
echo "    $(cargo --version)"

# ---------------------------------------------------------------------------
# GOTCHA 2: maturin often installs as a module WITHOUT a console script on PATH.
# `maturin` may be "command not found" while `python3 -m maturin` works fine.
# ---------------------------------------------------------------------------
if ! python3 -m maturin --version >/dev/null 2>&1; then
  echo "==> installing maturin"
  python3 -m pip install --quiet maturin
fi
echo "    maturin $(python3 -m maturin --version | awk '{print $2}')"

# ---------------------------------------------------------------------------
# GOTCHA 3: PyO3 is behind a NON-DEFAULT feature. Cargo.toml has
# `[features] default = []`, so a plain build produces a library with no Python
# module in it — importing pe_finance then fails at runtime with no build error.
# `--features python` is mandatory.
#
# GOTCHA 4: `maturin develop` requires an active virtualenv and fails outside
# one. `maturin build` + `pip install` the wheel works with a system Python.
# ---------------------------------------------------------------------------
echo "==> building wheel (features: python)"
python3 -m maturin build $PROFILE --features python

WHEEL="$(ls -t target/wheels/pe_finance-*.whl 2>/dev/null | head -1 || true)"
if [[ -z "$WHEEL" ]]; then
  echo "ERROR: no wheel produced in target/wheels/" >&2
  exit 1
fi

echo "==> installing $(basename "$WHEEL")"
python3 -m pip install --quiet --force-reinstall "$WHEEL"

echo "==> verifying import"
python3 - <<'PY'
import pe_finance
exports = sorted(x for x in dir(pe_finance) if x.startswith("py_"))
assert "py_dcf_exact" in exports, "string entry point missing — built without --features python?"
assert "py_parity_evaluate" in exports, "parity entry point missing"
print("    pe_finance OK")
for e in exports:
    kind = "string API" if e in ("py_dcf_exact", "py_parity_evaluate") else "legacy f64 API"
    print(f"      {e:<22} {kind}")
PY

if [[ "$RUN_TESTS" == "1" ]]; then
  echo "==> cargo test"
  cargo test --lib 2>&1 | tail -20

  echo "==> parity suite (should be 37 passed, 0 skipped)"
  cd "$REPO_ROOT"
  python3 -m pytest tests/test_decimal_parity.py -q 2>&1 | tail -5
fi

cat <<'EOF'

==> done

  IMPORTANT: prefer the string entry points for anything monetary.
  py_calculate_dcf and friends take f64 and corrupt inputs before the decimal
  engine runs — 9 of 11 realistic money literals do not survive an f64 round
  trip. See CLAIMS.md 1.9 and tests/test_decimal_parity.py class 1.

  Next:
    cd integrations/rust/benchmarks
    python3 bench_decimal_dcf.py --grid 40    # Rust decimal vs Python decimal
    python3 bench_monte_carlo.py              # Rust vs vectorized NumPy
EOF
