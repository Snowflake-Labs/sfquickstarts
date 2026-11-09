"""Additional single-thread CPU benchmark; not a FinanceBench/NVIDIA reproduction."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone

import numba
import numpy as np


DIRECTORY = Path(__file__).resolve().parent
PARAMETERS = (100.0, 100.0, 0.05, 0.20, 1.0)
POINTER = ctypes.POINTER(ctypes.c_double)


def numpy_payoffs(normals, output, spot, strike, rate, volatility, maturity):
    np.multiply(normals, volatility * math.sqrt(maturity), out=output)
    np.add(output, (rate - 0.5 * volatility * volatility) * maturity, out=output)
    np.exp(output, out=output)
    np.multiply(output, spot, out=output)
    np.subtract(output, strike, out=output)
    np.maximum(output, 0.0, out=output)
    np.multiply(output, math.exp(-rate * maturity), out=output)


@numba.njit(fastmath=False)
def numba_payoffs(normals, output, spot, strike, rate, volatility, maturity):
    drift = (rate - 0.5 * volatility * volatility) * maturity
    diffusion = volatility * math.sqrt(maturity)
    discount = math.exp(-rate * maturity)
    for index in range(normals.size):
        terminal = spot * math.exp(drift + diffusion * normals[index])
        output[index] = discount * max(terminal - strike, 0.0)


def analytical_call(spot, strike, rate, volatility, maturity):
    if maturity == 0:
        return max(spot - strike, 0.0)
    if volatility == 0:
        return max(spot - strike * math.exp(-rate * maturity), 0.0)
    scale = volatility * math.sqrt(maturity)
    first = (math.log(spot / strike) + (rate + 0.5 * volatility**2) * maturity) / scale
    second = first - scale
    normal_cdf = lambda value: 0.5 * math.erfc(-value / math.sqrt(2.0))
    return spot * normal_cdf(first) - strike * math.exp(-rate * maturity) * normal_cdf(second)


def load_rust():
    compiler = Path.home() / ".cargo/bin/rustc"
    library_path = DIRECTORY / "liboption_benchmark.dylib"
    command = [str(compiler), "--edition=2021", "--crate-type=cdylib", "-C", "opt-level=3",
               "-C", "target-cpu=native", str(DIRECTORY / "option_kernel.rs"), "-o", str(library_path)]
    subprocess.run(command, check=True)
    library = ctypes.CDLL(str(library_path))
    function = library.option_payoffs
    function.argtypes = [POINTER, POINTER, ctypes.c_size_t] + [ctypes.c_double] * 5
    function.restype = None

    def rust_payoffs(normals, output, *parameters):
        function(normals.ctypes.data_as(POINTER), output.ctypes.data_as(POINTER),
                 normals.size, *parameters)

    return rust_payoffs, command, subprocess.check_output([str(compiler), "--version"], text=True).strip()


def validate(implementations, counts):
    diagnostics = []
    cases = [PARAMETERS, (100.0, 80.0, 0.05, 0.0, 1.0),
             (100.0, 120.0, 0.05, 0.0, 1.0), (100.0, 90.0, 0.05, 0.2, 0.0),
             (100.0, 100.0, -0.02, 0.4, 2.0)]
    for count in counts:
        normals = np.random.default_rng(20260911).standard_normal(count)
        reference = np.empty_like(normals)
        output = np.empty_like(normals)
        for case_index, parameters in enumerate(cases):
            numpy_payoffs(normals, reference, *parameters)
            expected = analytical_call(*parameters)
            price = float(reference.mean())
            standard_error = float(reference.std(ddof=1) / math.sqrt(count))
            assert abs(price - expected) <= 5.0 * standard_error + 1e-10, (count, parameters, price, expected)
            errors = {}
            for name, function in implementations.items():
                function(normals, output, *parameters)
                assert np.isfinite(output).all() and (output >= 0).all()
                np.testing.assert_allclose(output, reference, rtol=1e-12, atol=1e-12)
                errors[name] = float(np.max(np.abs(output - reference)))
            diagnostics.append({"paths": count, "case": case_index, "parameters": parameters,
                                "price": price, "analytical": expected, "standard_error": standard_error,
                                "max_pathwise_absolute_error": errors})
    return diagnostics


def timed_batch(function, iterations):
    started = time.perf_counter_ns()
    for unused in range(iterations):
        value = function()
    elapsed = (time.perf_counter_ns() - started) / 1e9
    assert math.isfinite(value)
    return elapsed / iterations


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--counts", type=int, nargs="+", default=[10_000, 100_000, 1_000_000, 10_000_000])
    parser.add_argument("--repeats", type=int, default=7)
    parser.add_argument("--json", type=Path, default=DIRECTORY / "option_pricing_results.json")
    arguments = parser.parse_args()
    if min(arguments.counts) < 2 or arguments.repeats < 3:
        parser.error("Counts must be >=2 and repeats >=3")
    rust_payoffs, build_command, rust_version = load_rust()
    implementations = {"numpy": numpy_payoffs, "numba": numba_payoffs, "rust": rust_payoffs}
    diagnostics = validate(implementations, arguments.counts)
    print(f"Correctness passed: {len(diagnostics)} cases, 3 implementations", flush=True)
    results = []
    order_generator = random.Random(42)
    for count in arguments.counts:
        normals = np.random.default_rng(20260911).standard_normal(count)
        output = np.empty_like(normals)
        for scope in ["kernel", "end_to_end"]:
            calls = {}
            for name, function in implementations.items():
                if scope == "kernel":
                    def call(function=function):
                        function(normals, output, *PARAMETERS)
                        return float(output.mean())
                else:
                    def call(function=function):
                        generated = np.random.default_rng(20260911).standard_normal(count)
                        allocated = np.empty_like(generated)
                        function(generated, allocated, *PARAMETERS)
                        return float(allocated.mean())
                calls[name] = call
            iterations = {}
            samples = {name: [] for name in calls}
            for name, call in calls.items():
                call()
                initial = timed_batch(call, 3)
                iterations[name] = max(1, min(10000, math.ceil(0.1 / max(initial, 1e-9))))
            for repetition in range(arguments.repeats):
                names = list(calls)
                order_generator.shuffle(names)
                for name in names:
                    samples[name].append(timed_batch(calls[name], iterations[name]))
            baseline = statistics.median(samples["numpy"])
            for name, values in samples.items():
                row = {"paths": count, "scope": scope, "implementation": name,
                       "median_s": statistics.median(values), "min_s": min(values), "max_s": max(values),
                       "samples_s": values, "iterations_per_sample": iterations[name],
                       "speedup_vs_numpy": baseline / statistics.median(values)}
                results.append(row)
                print(f"{count:>10,} {scope:>12} {name:>5}: {row['median_s']*1000:9.3f} ms  {row['speedup_vs_numpy']:.2f}x", flush=True)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workload": "European call, exact risk-neutral GBM terminal sampling, no dividends",
        "parameters": dict(zip(["spot", "strike", "rate", "volatility", "maturity"], PARAMETERS)),
        "environment": {"platform": platform.platform(), "python": sys.version, "numpy": np.__version__,
                        "numba": numba.__version__, "rust": rust_version,
                        "cpu": subprocess.check_output(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip(),
                        "logical_cpus": os.cpu_count(), "compute_threads": 1},
        "methodology": {"repeats": arguments.repeats, "seed": 20260911, "rng": "NumPy default_rng PCG64, float64",
                        "kernel": "Preallocated payoff output, pregenerated normals, payoff transform + common NumPy mean; includes Python/ctypes dispatch",
                        "end_to_end": "Generator initialization, random draws, allocation, payoff transform, common NumPy mean, array release",
                        "warmup": "JIT/build excluded; all implementations warmed; randomized timing order; >=100ms target per sample",
                        "optimization": "NumPy in-place ufuncs; Numba nopython serial fastmath=False; Rust serial opt-level=3 target-cpu=native",
                        "scope": "Additional local workload, not existing pe_finance kernel, not a reproduction of FinanceBench or NVIDIA GPU timings",
                        "correctness": "Pathwise rtol=1e-12 atol=1e-12; analytical price within five sample SE; zero-volatility and expiry tests"},
        "reference": "https://www.optionseducation.org/advancedconcepts/black-scholes-formula",
        "build_command": build_command,
        "source_hashes": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [Path(__file__), DIRECTORY / "option_kernel.rs"]},
        "validation": diagnostics, "results": results,
    }
    arguments.json.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Saved {arguments.json}", flush=True)


if __name__ == "__main__":
    main()