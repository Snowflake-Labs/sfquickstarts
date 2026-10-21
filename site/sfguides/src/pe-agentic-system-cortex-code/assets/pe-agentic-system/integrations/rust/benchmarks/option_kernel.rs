#[no_mangle]
pub unsafe extern "C" fn option_payoffs(
    normals: *const f64,
    output: *mut f64,
    count: usize,
    spot: f64,
    strike: f64,
    rate: f64,
    volatility: f64,
    maturity: f64,
) {
    let normals = std::slice::from_raw_parts(normals, count);
    let output = std::slice::from_raw_parts_mut(output, count);
    let drift = (rate - 0.5 * volatility * volatility) * maturity;
    let diffusion = volatility * maturity.sqrt();
    let discount = (-rate * maturity).exp();
    for (normal, payoff) in normals.iter().zip(output.iter_mut()) {
        let terminal = spot * (drift + diffusion * normal).exp();
        *payoff = discount * (terminal - strike).max(0.0);
    }
}