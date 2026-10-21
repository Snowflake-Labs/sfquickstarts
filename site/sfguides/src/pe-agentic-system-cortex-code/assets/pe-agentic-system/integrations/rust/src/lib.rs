// PE Finance - High-Performance Financial Modeling
// Python bindings via PyO3 and WebAssembly support

pub mod dcf;
pub mod lbo;
pub mod monte_carlo;
pub mod parity;

// Re-export main types
pub use dcf::{DCFInputs, DCFResult, calculate_dcf, dcf_sensitivity_2d};
pub use lbo::{LBOInputs, LBOResult, calculate_lbo, lbo_scenarios, WaterfallTier, calculate_waterfall};
pub use monte_carlo::{MonteCarloInputs, MonteCarloResult, monte_carlo_dcf, Scenario, scenario_analysis};
pub use parity::{evaluate_all, dcf_exact_from_strings};

// Python bindings
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn pe_finance(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(py_calculate_dcf, m)?)?;
    m.add_function(wrap_pyfunction!(py_dcf_sensitivity, m)?)?;
    m.add_function(wrap_pyfunction!(py_calculate_lbo, m)?)?;
    m.add_function(wrap_pyfunction!(py_lbo_scenarios, m)?)?;
    m.add_function(wrap_pyfunction!(py_monte_carlo, m)?)?;
    m.add_function(wrap_pyfunction!(py_scenario_analysis, m)?)?;
    // String-based entry points. Prefer these for anything monetary — the f64
    // signatures below corrupt inputs before the decimal engine runs.
    m.add_function(wrap_pyfunction!(py_parity_evaluate, m)?)?;
    m.add_function(wrap_pyfunction!(py_dcf_exact, m)?)?;
    Ok(())
}

/// Evaluate the golden parity fixture. Strings in, strings out.
#[cfg(feature = "python")]
#[pyfunction]
fn py_parity_evaluate(cases_json: String) -> PyResult<String> {
    parity::evaluate_all(&cases_json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
}

/// Exact DCF from string inputs — no f64 anywhere in the path.
#[cfg(feature = "python")]
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn py_dcf_exact(
    initial_revenue: String,
    growth_rate: String,
    ebitda_margin: String,
    tax_rate: String,
    capex_pct: String,
    nwc_pct: String,
    wacc: String,
    terminal_growth: String,
    years: usize,
) -> PyResult<String> {
    parity::dcf_exact_from_strings(
        &initial_revenue, &growth_rate, &ebitda_margin, &tax_rate,
        &capex_pct, &nwc_pct, &wacc, &terminal_growth, years,
    )
    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e))
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_calculate_dcf(
    initial_revenue: f64,
    growth_rate: f64,
    ebitda_margin: f64,
    tax_rate: f64,
    wacc: f64,
    terminal_growth: f64,
    years: usize,
) -> PyResult<String> {
    let inputs = DCFInputs::new_constant_growth(
        initial_revenue,
        growth_rate,
        ebitda_margin,
        tax_rate,
        wacc,
        terminal_growth,
        years,
    );
    
    let result = calculate_dcf(&inputs);
    let json = serde_json::to_string_pretty(&result)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    Ok(json)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_dcf_sensitivity(
    initial_revenue: f64,
    growth_rate: f64,
    ebitda_margin: f64,
    tax_rate: f64,
    wacc: f64,
    terminal_growth: f64,
    years: usize,
    param1_name: String,
    param1_values: Vec<f64>,
    param2_name: String,
    param2_values: Vec<f64>,
) -> PyResult<String> {
    let base_inputs = DCFInputs::new_constant_growth(
        initial_revenue,
        growth_rate,
        ebitda_margin,
        tax_rate,
        wacc,
        terminal_growth,
        years,
    );
    
    let results = dcf_sensitivity_2d(
        &base_inputs,
        &param1_name,
        &param1_values,
        &param2_name,
        &param2_values,
    );
    
    let json = serde_json::to_string_pretty(&results)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    Ok(json)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_calculate_lbo(
    purchase_price: f64,
    debt_pct: f64,
    entry_metric: f64,
    exit_multiple: f64,
    metric_cagr: f64,
    hold_years: usize,
) -> PyResult<String> {
    let inputs = LBOInputs::new(
        purchase_price,
        debt_pct,
        entry_metric,
        exit_multiple,
        metric_cagr,
        hold_years,
    );
    
    let result = calculate_lbo(&inputs);
    let json = serde_json::to_string_pretty(&result)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    Ok(json)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_lbo_scenarios(scenarios_json: String) -> PyResult<String> {
    let scenarios: Vec<LBOInputs> = serde_json::from_str(&scenarios_json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    let results = lbo_scenarios(&scenarios);
    let json = serde_json::to_string_pretty(&results)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    Ok(json)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_monte_carlo(
    base_revenue: f64,
    revenue_volatility: f64,
    ebitda_margin_mean: f64,
    ebitda_margin_std: f64,
    wacc_mean: f64,
    wacc_std: f64,
    terminal_growth: f64,
    years: usize,
    simulations: usize,
) -> PyResult<String> {
    let inputs = MonteCarloInputs {
        base_revenue,
        revenue_volatility,
        ebitda_margin_mean,
        ebitda_margin_std,
        wacc_mean,
        wacc_std,
        terminal_growth,
        years,
        simulations,
    };
    
    let result = monte_carlo_dcf(&inputs);
    
    // Return summary statistics (not all valuations - too large)
    let summary = serde_json::json!({
        "mean": result.mean,
        "median": result.median,
        "std_dev": result.std_dev,
        "percentile_5": result.percentile_5,
        "percentile_25": result.percentile_25,
        "percentile_75": result.percentile_75,
        "percentile_95": result.percentile_95,
        "simulations": result.valuations.len(),
        // How many paths had the terminal discount rate raised to its floor.
        // Surfaced so a clamp is auditable rather than invisible.
        "paths_clamped": result.paths_clamped,
    });
    
    Ok(serde_json::to_string_pretty(&summary)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?)
}

#[cfg(feature = "python")]
#[pyfunction]
fn py_scenario_analysis(base_revenue: f64, scenarios_json: String) -> PyResult<String> {
    let scenarios: Vec<Scenario> = serde_json::from_str(&scenarios_json)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    let results = scenario_analysis(base_revenue, &scenarios);
    let json = serde_json::to_string_pretty(&results)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
    
    Ok(json)
}

// WebAssembly bindings
#[cfg(feature = "wasm")]
use wasm_bindgen::prelude::*;

#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_calculate_dcf(
    initial_revenue: f64,
    growth_rate: f64,
    ebitda_margin: f64,
    tax_rate: f64,
    wacc: f64,
    terminal_growth: f64,
    years: usize,
) -> String {
    console_error_panic_hook::set_once();
    
    let inputs = DCFInputs::new_constant_growth(
        initial_revenue,
        growth_rate,
        ebitda_margin,
        tax_rate,
        wacc,
        terminal_growth,
        years,
    );
    
    let result = calculate_dcf(&inputs);
    serde_json::to_string_pretty(&result).unwrap_or_else(|_| "{}".to_string())
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_calculate_lbo(
    purchase_price: f64,
    debt_pct: f64,
    entry_metric: f64,
    exit_multiple: f64,
    metric_cagr: f64,
    hold_years: usize,
) -> String {
    console_error_panic_hook::set_once();
    
    let inputs = LBOInputs::new(
        purchase_price,
        debt_pct,
        entry_metric,
        exit_multiple,
        metric_cagr,
        hold_years,
    );
    
    let result = calculate_lbo(&inputs);
    serde_json::to_string_pretty(&result).unwrap_or_else(|_| "{}".to_string())
}

#[cfg(feature = "wasm")]
#[wasm_bindgen]
pub fn wasm_monte_carlo(
    base_revenue: f64,
    revenue_volatility: f64,
    ebitda_margin_mean: f64,
    ebitda_margin_std: f64,
    wacc_mean: f64,
    wacc_std: f64,
    terminal_growth: f64,
    years: usize,
    simulations: usize,
) -> String {
    console_error_panic_hook::set_once();
    
    let inputs = MonteCarloInputs {
        base_revenue,
        revenue_volatility,
        ebitda_margin_mean,
        ebitda_margin_std,
        wacc_mean,
        wacc_std,
        terminal_growth,
        years,
        simulations,
    };
    
    let result = monte_carlo_dcf(&inputs);
    
    let summary = serde_json::json!({
        "mean": result.mean,
        "median": result.median,
        "std_dev": result.std_dev,
        "percentile_5": result.percentile_5,
        "percentile_25": result.percentile_25,
        "percentile_75": result.percentile_75,
        "percentile_95": result.percentile_95,
        "simulations": result.valuations.len(),
    });
    
    serde_json::to_string_pretty(&summary).unwrap_or_else(|_| "{}".to_string())
}
