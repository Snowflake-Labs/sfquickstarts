#!/usr/bin/env bash
# Build the WebAssembly deployment target.
#
# The crate declares crate-type = ["cdylib", "rlib"], so the same source that
# builds the CPython extension also builds for wasm32. Two things are not
# obvious and both were discovered by trying:
#
#   1. `rand 0.8` pulls `getrandom 0.2`, which refuses to compile for
#      wasm32-unknown-unknown unless its "js" feature is enabled so it can bind
#      crypto.getRandomValues(). Cargo.toml scopes that dependency to wasm32.
#
#   2. `cargo build` alone is not sufficient. The raw .wasm carries
#      __wbindgen_placeholder__ imports and cannot be instantiated. It has to be
#      post-processed by the wasm-bindgen CLI *at the same version* as the
#      wasm-bindgen crate in Cargo.lock, or loading fails on a schema mismatch.
#
# Usage:
#   ./build_wasm.sh            # nodejs target (default, what verify uses)
#   ./build_wasm.sh web        # browser target, ES modules
set -euo pipefail

cd "$(dirname "$0")"
TARGET="${1:-nodejs}"

export PATH="$HOME/.cargo/bin:$PATH"

command -v cargo >/dev/null || { echo "cargo not on PATH"; exit 1; }

# Pin the CLI to the crate version rather than whatever is installed.
BG_VERSION="$(awk '/^name = "wasm-bindgen"$/{getline; gsub(/[",]/,""); print $3; exit}' Cargo.lock)"
echo "wasm-bindgen crate version from Cargo.lock: ${BG_VERSION}"

if ! command -v wasm-bindgen >/dev/null; then
  echo "installing wasm-bindgen-cli ${BG_VERSION}"
  cargo install wasm-bindgen-cli --version "${BG_VERSION}"
else
  HAVE="$(wasm-bindgen --version | awk '{print $2}')"
  if [[ "${HAVE}" != "${BG_VERSION}" ]]; then
    echo "wasm-bindgen CLI ${HAVE} != crate ${BG_VERSION}; reinstalling to match"
    cargo install wasm-bindgen-cli --version "${BG_VERSION}" --force
  fi
fi

rustup target list --installed | grep -q wasm32-unknown-unknown \
  || rustup target add wasm32-unknown-unknown

echo "building wasm32-unknown-unknown (release, --features wasm)"
cargo build --release --target wasm32-unknown-unknown --features wasm

RAW="target/wasm32-unknown-unknown/release/pe_finance.wasm"
echo "raw artifact: $(du -h "${RAW}" | cut -f1)"

echo "running wasm-bindgen --target ${TARGET}"
wasm-bindgen "${RAW}" --out-dir pkg --target "${TARGET}"

echo
echo "pkg/:"
ls -lh pkg/ | tail -n +2 | awk '{printf "  %-28s %s\n", $9, $5}'
echo
echo "next: python3 verify_wasm_parity.py"
