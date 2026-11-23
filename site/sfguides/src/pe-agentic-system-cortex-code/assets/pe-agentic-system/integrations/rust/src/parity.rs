// Parity evaluator — string in, string out.
//
// Exists because the existing PyO3 entry points in lib.rs all take `f64`, which
// destroys precision before this crate's decimal arithmetic ever runs. Measured:
// 9 of 11 realistic money literals do not survive an f64 round-trip (see
// tests/test_decimal_parity.py, class 1). No amount of internal exactness can
// recover a value that was already corrupted at the boundary.
//
// So every function here accepts and returns strings. That is the only signature
// shape for which cross-implementation parity against Python's `Decimal` is even
// expressible.
//
// The op names and semantics mirror tests/fixtures/decimal_parity_golden.json.

use rust_decimal::prelude::*;
use rust_decimal::{Decimal, RoundingStrategy};
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct ParityCase {
    pub id: String,
    pub op: String,
    pub inputs: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct ParityResult {
    pub id: String,
    pub actual: Option<String>,
    pub error: Option<String>,
}

fn dec(v: &serde_json::Value, key: &str) -> Result<Decimal, String> {
    let s = v
        .get(key)
        .and_then(|x| x.as_str())
        .ok_or_else(|| format!("missing or non-string input '{key}'"))?;
    Decimal::from_str(s).map_err(|e| format!("cannot parse '{s}' as Decimal: {e}"))
}

fn int(v: &serde_json::Value, key: &str) -> Result<u64, String> {
    v.get(key)
        .and_then(|x| x.as_u64())
        .ok_or_else(|| format!("missing or non-integer input '{key}'"))
}

/// Number of decimal places implied by an exponent string like "0.01" -> 2.
fn scale_of(exponent: &str) -> Result<u32, String> {
    let d = Decimal::from_str(exponent).map_err(|e| format!("bad exponent: {e}"))?;
    Ok(d.scale())
}

fn eval_case(case: &ParityCase) -> Result<String, String> {
    let i = &case.inputs;

    let out = match case.op.as_str() {
        // Round-trip a literal unchanged. Catches any parse/format asymmetry.
        "identity" => dec(i, "value")?,

        "divide" => {
            let a = dec(i, "a")?;
            let b = dec(i, "b")?;
            if b.is_zero() {
                return Err("division by zero".to_string());
            }
            a.checked_div(b).ok_or("division overflowed")?
        }

        // Python: Decimal(value).quantize(Decimal(exponent), rounding=ROUND_HALF_UP)
        // rust_decimal equivalent is MidpointAwayFromZero (NOT the default,
        // which is MidpointNearestEven / banker's).
        "quantize_half_up" => {
            let v = dec(i, "value")?;
            let scale = scale_of(
                i.get("exponent")
                    .and_then(|x| x.as_str())
                    .ok_or("missing exponent")?,
            )?;
            v.round_dp_with_strategy(scale, RoundingStrategy::MidpointAwayFromZero)
        }

        // Python: hwm * (1 + annual_rate/12) ** months
        //
        // Deliberately the pow form, not an accumulating loop. Those two disagree
        // in the final digit (133.8654676952387217216506905 vs ...906), so the
        // contract has to name which one. bench_equalization.py uses pow.
        "compound_hurdle" => {
            let hwm = dec(i, "hwm")?;
            let annual = dec(i, "annual_rate")?;
            let months = int(i, "months")?;
            let monthly = annual
                .checked_div(Decimal::from(12u32))
                .ok_or("rate/12 overflowed")?;
            let base = Decimal::ONE
                .checked_add(monthly)
                .ok_or("1+rate overflowed")?;
            let factor = base
                .checked_powu(months)
                .ok_or("compounding overflowed")?;
            hwm.checked_mul(factor).ok_or("hwm*factor overflowed")?
        }

        // Gordon Growth: fcf * (1 + g) / (wacc - g)
        // Guarded because wacc <= g yields a non-positive denominator and a
        // confidently negative terminal value — the silent DCF failure the
        // assurance boundary blocks upstream. Guard here too, defensively.
        "terminal_value" => {
            let fcf = dec(i, "fcf")?;
            let g = dec(i, "terminal_growth")?;
            let wacc = dec(i, "wacc")?;
            let denom = wacc.checked_sub(g).ok_or("wacc-g overflowed")?;
            if denom <= Decimal::ZERO {
                return Err(format!(
                    "wacc ({wacc}) must exceed terminal_growth ({g}); denominator \
                     is non-positive and terminal value is meaningless"
                ));
            }
            let numer = fcf
                .checked_mul(Decimal::ONE.checked_add(g).ok_or("1+g overflowed")?)
                .ok_or("fcf*(1+g) overflowed")?;
            numer.checked_div(denom).ok_or("division overflowed")?
        }

        other => return Err(format!("unknown op '{other}'")),
    };

    Ok(out.to_string())
}

/// Evaluate every case in the golden fixture. Errors are captured per case rather
/// than aborting, so one unsupported op cannot hide the rest of the comparison.
pub fn evaluate_all(cases_json: &str) -> Result<String, String> {
    let cases: Vec<ParityCase> =
        serde_json::from_str(cases_json).map_err(|e| format!("bad cases JSON: {e}"))?;

    let results: Vec<ParityResult> = cases
        .iter()
        .map(|c| match eval_case(c) {
            Ok(actual) => ParityResult {
                id: c.id.clone(),
                actual: Some(actual),
                error: None,
            },
            Err(e) => ParityResult {
                id: c.id.clone(),
                actual: None,
                error: Some(e),
            },
        })
        .collect();

    serde_json::to_string(&results).map_err(|e| format!("cannot serialize results: {e}"))
}

/// Exact DCF taking string inputs. Mirrors calculate_dcf but without the f64 gate.
#[allow(clippy::too_many_arguments)]
pub fn dcf_exact_from_strings(
    initial_revenue: &str,
    growth_rate: &str,
    ebitda_margin: &str,
    tax_rate: &str,
    capex_pct: &str,
    nwc_pct: &str,
    wacc: &str,
    terminal_growth: &str,
    years: usize,
) -> Result<String, String> {
    let parse = |s: &str, name: &str| {
        Decimal::from_str(s).map_err(|e| format!("cannot parse {name}='{s}': {e}"))
    };

    let mut revenue = parse(initial_revenue, "initial_revenue")?;
    let growth = parse(growth_rate, "growth_rate")?;
    let margin = parse(ebitda_margin, "ebitda_margin")?;
    let tax = parse(tax_rate, "tax_rate")?;
    let capex_r = parse(capex_pct, "capex_pct")?;
    let nwc_r = parse(nwc_pct, "nwc_pct")?;
    let wacc_d = parse(wacc, "wacc")?;
    let g = parse(terminal_growth, "terminal_growth")?;

    if wacc_d <= g {
        return Err(format!(
            "wacc ({wacc_d}) must exceed terminal_growth ({g})"
        ));
    }

    let one = Decimal::ONE;
    let mut total_pv = Decimal::ZERO;
    let mut fcf = Decimal::ZERO;

    // Statement order matches dcf.rs:76-119 exactly. Order affects the final digit
    // once quotients are truncated, so it is part of the parity contract.
    for year in 1..=years {
        revenue *= one + growth;
        let ebitda = revenue * margin;
        let nopat = ebitda * (one - tax);
        let capex = revenue * capex_r;
        let nwc = revenue * nwc_r * growth / (one + growth);
        fcf = nopat - capex - nwc;
        let discount = (one + wacc_d)
            .checked_powu(year as u64)
            .ok_or("discount factor overflowed")?;
        total_pv += fcf / discount;
    }

    let terminal = fcf * (one + g) / (wacc_d - g);
    let pv_terminal = terminal
        / (one + wacc_d)
            .checked_powu(years as u64)
            .ok_or("terminal discount overflowed")?;

    Ok((total_pv + pv_terminal).to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_round_trips_without_f64() {
        // The whole point: these are the literals that f64 destroys.
        for lit in ["0.1", "0.0775", "1234567.89", "0.07"] {
            let d = Decimal::from_str(lit).unwrap();
            assert_eq!(d.to_string(), lit, "literal {lit} must round-trip exactly");
        }
    }

    #[test]
    fn f64_path_is_lossy_and_string_path_is_not() {
        // Demonstrates in Rust what the Python test asserts from the other side.
        let via_f64 = Decimal::from_f64_retain(0.0775_f64).unwrap();
        let via_str = Decimal::from_str("0.0775").unwrap();
        assert_ne!(
            via_f64, via_str,
            "from_f64_retain should NOT equal the exact literal — if this passes, \
             the f64 hazard has changed and the parity contract needs revisiting"
        );
    }

    #[test]
    fn half_up_is_not_the_default_strategy() {
        let v = Decimal::from_str("2.5").unwrap();
        assert_eq!(
            v.round_dp_with_strategy(0, RoundingStrategy::MidpointAwayFromZero)
                .to_string(),
            "3"
        );
        assert_eq!(
            v.round_dp_with_strategy(0, RoundingStrategy::MidpointNearestEven)
                .to_string(),
            "2"
        );
    }

    #[test]
    fn terminal_value_rejects_wacc_below_growth() {
        let case = ParityCase {
            id: "guard".into(),
            op: "terminal_value".into(),
            inputs: serde_json::json!({
                "fcf": "1000000", "terminal_growth": "0.05", "wacc": "0.03"
            }),
        };
        assert!(eval_case(&case).is_err());
    }
}
