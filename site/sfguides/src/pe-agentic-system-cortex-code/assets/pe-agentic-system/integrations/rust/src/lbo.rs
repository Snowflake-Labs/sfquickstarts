// LBO (Leveraged Buyout) Model
// High-performance returns calculation

use rust_decimal::Decimal;
use rust_decimal::MathematicalOps;  // brings powi() into scope
use rust_decimal_macros::dec;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LBOInputs {
    pub purchase_price: Decimal,
    pub debt_percentage: Decimal,
    pub entry_metric: Decimal,  // EBITDA or Revenue
    pub entry_multiple: Decimal,
    pub exit_multiple: Decimal,
    pub metric_growth_cagr: Decimal,
    pub debt_paydown_rate: Decimal,  // Annual % of original debt paid down
    pub hold_period: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LBOResult {
    pub entry_equity: Decimal,
    pub entry_debt: Decimal,
    pub exit_metric: Decimal,
    pub exit_enterprise_value: Decimal,
    pub exit_debt: Decimal,
    pub exit_equity_value: Decimal,
    pub moic: Decimal,  // Multiple of Invested Capital
    pub irr: Decimal,   // Internal Rate of Return
    pub annual_returns: Vec<AnnualReturn>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnnualReturn {
    pub year: usize,
    pub metric_value: Decimal,
    pub debt_balance: Decimal,
}

impl LBOInputs {
    pub fn new(
        purchase_price: f64,
        debt_pct: f64,
        entry_metric: f64,
        exit_multiple: f64,
        metric_cagr: f64,
        hold_years: usize,
    ) -> Self {
        LBOInputs {
            purchase_price: Decimal::from_f64_retain(purchase_price).unwrap(),
            debt_percentage: Decimal::from_f64_retain(debt_pct).unwrap(),
            entry_metric: Decimal::from_f64_retain(entry_metric).unwrap(),
            entry_multiple: Decimal::from_f64_retain(purchase_price / entry_metric).unwrap(),
            exit_multiple: Decimal::from_f64_retain(exit_multiple).unwrap(),
            metric_growth_cagr: Decimal::from_f64_retain(metric_cagr).unwrap(),
            debt_paydown_rate: dec!(0.10),  // Default 10% per year
            hold_period: hold_years,
        }
    }
}

pub fn calculate_lbo(inputs: &LBOInputs) -> LBOResult {
    // Entry capital structure
    let entry_debt = inputs.purchase_price * inputs.debt_percentage;
    let entry_equity = inputs.purchase_price - entry_debt;
    
    // Project metric forward
    let exit_metric = inputs.entry_metric * (dec!(1) + inputs.metric_growth_cagr).powi(inputs.hold_period as i64);
    
    // Calculate annual returns
    let mut annual_returns = Vec::with_capacity(inputs.hold_period);
    let mut current_metric = inputs.entry_metric;
    let mut current_debt = entry_debt;
    
    for year in 1..=inputs.hold_period {
        current_metric = current_metric * (dec!(1) + inputs.metric_growth_cagr);
        current_debt = current_debt * (dec!(1) - inputs.debt_paydown_rate);
        
        annual_returns.push(AnnualReturn {
            year,
            metric_value: current_metric,
            debt_balance: current_debt,
        });
    }
    
    // Exit valuation
    let exit_enterprise_value = exit_metric * inputs.exit_multiple;
    let exit_debt = annual_returns.last().unwrap().debt_balance;
    let exit_equity_value = exit_enterprise_value - exit_debt;
    
    // Returns
    let moic = exit_equity_value / entry_equity;
    
    // IRR calculation (Newton-Raphson method)
    let irr = calculate_irr(entry_equity, exit_equity_value, inputs.hold_period);
    
    LBOResult {
        entry_equity,
        entry_debt,
        exit_metric,
        exit_enterprise_value,
        exit_debt,
        exit_equity_value,
        moic,
        irr,
        annual_returns,
    }
}

/// Calculate IRR using Newton-Raphson
fn calculate_irr(initial_investment: Decimal, final_value: Decimal, years: usize) -> Decimal {
    // Simple approximation: (FV/PV)^(1/n) - 1
    let ratio = final_value / initial_investment;
    let exp = dec!(1) / Decimal::from(years);
    
    // Use iterative method for better precision
    let mut rate = dec!(0.15);  // Initial guess: 15%
    let epsilon = dec!(0.00001);
    let max_iterations = 100;
    
    for _ in 0..max_iterations {
        let pv = final_value / (dec!(1) + rate).powi(years as i64);
        let diff = pv - initial_investment;
        
        if diff.abs() < epsilon {
            break;
        }
        
        // Derivative
        let dpv = -final_value * Decimal::from(years) / (dec!(1) + rate).powi(years as i64 + 1);
        
        // Newton-Raphson update
        rate = rate - diff / dpv;
        
        // Bounds check
        if rate < dec!(-0.99) {
            rate = dec!(-0.99);
        } else if rate > dec!(5.0) {
            rate = dec!(5.0);
        }
    }
    
    rate
}

/// Calculate LBO scenarios in parallel
pub fn lbo_scenarios(scenarios: &[LBOInputs]) -> Vec<LBOResult> {
    use rayon::prelude::*;
    
    scenarios.par_iter()
        .map(|inputs| calculate_lbo(inputs))
        .collect()
}

/// Waterfall analysis - calculate equity distribution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaterfallTier {
    pub name: String,
    pub ownership_pct: Decimal,
    pub preference_multiple: Decimal,  // 1x, 2x, etc.
    pub participation: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaterfallResult {
    pub tier_name: String,
    pub capital_invested: Decimal,
    pub preference_amount: Decimal,
    pub distribution: Decimal,
    pub moic: Decimal,
}

pub fn calculate_waterfall(
    exit_proceeds: Decimal,
    tiers: &[WaterfallTier],
    total_invested: Decimal,
) -> Vec<WaterfallResult> {
    // BUGFIX: pro-rata must be computed against TOTAL exit proceeds, not against
    // the balance left after senior tiers have been paid.
    //
    // The previous implementation used an eroding `remaining` as the pro-rata base,
    // so on the crate's own test case (2 tiers at 30%/70%, $300M proceeds, $100M
    // invested, both non-participating) the Common tier received 70% of the
    // remaining $210M = $147M instead of 70% of $300M = $210M. Result:
    // **$63,000,000 of $300,000,000 — 21% of the exit — was never distributed.**
    //
    // The crate's own `test_waterfall` asserts that all proceeds are distributed
    // and caught this immediately. It had simply never been run: the crate did not
    // compile (5 errors, `powi` needing MathematicalOps in scope) so no test in it
    // had ever executed.
    //
    // Correct semantics for non-participating preferred: each tier takes the
    // greater of its liquidation preference or its pro-rata share of the *whole*
    // exit. For participating preferred: preference plus a pro-rata share of
    // proceeds remaining after ALL preferences are satisfied — which requires
    // knowing the aggregate preference up front, not just the senior ones.
    let total_preference: Decimal = tiers
        .iter()
        .map(|t| total_invested * t.ownership_pct * t.preference_multiple)
        .sum();

    // Pool shared by participating tiers after every preference is met.
    let participation_pool = if exit_proceeds > total_preference {
        exit_proceeds - total_preference
    } else {
        dec!(0)
    };

    let mut remaining = exit_proceeds;
    let mut results = Vec::new();

    for tier in tiers {
        let invested = total_invested * tier.ownership_pct;
        let preference = invested * tier.preference_multiple;

        let distribution = if exit_proceeds >= total_preference {
            if tier.participation {
                // Preference, then share the post-preference pool
                preference + participation_pool * tier.ownership_pct
            } else {
                // Greater of preference or pro-rata of the FULL exit
                preference.max(exit_proceeds * tier.ownership_pct)
            }
        } else {
            // Shortfall: preferences cannot all be met, so distribute pro-rata to
            // preference claims rather than by ownership.
            if total_preference > dec!(0) {
                exit_proceeds * (preference / total_preference)
            } else {
                dec!(0)
            }
        };

        // Never pay out more than is actually left.
        let distribution = distribution.min(remaining);
        remaining -= distribution;

        let moic = if invested > dec!(0) {
            distribution / invested
        } else {
            dec!(0)
        };

        results.push(WaterfallResult {
            tier_name: tier.name.clone(),
            capital_invested: invested,
            preference_amount: preference,
            distribution,
            moic,
        });
    }

    results
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_lbo() {
        let inputs = LBOInputs::new(
            250_000_000.0,  // $250M purchase
            0.60,           // 60% debt
            50_000_000.0,   // $50M EBITDA
            5.0,            // 5x exit multiple
            0.08,           // 8% EBITDA growth
            5               // 5 year hold
        );
        
        let result = calculate_lbo(&inputs);
        
        assert!(result.moic > dec!(1));
        assert!(result.irr > dec!(0));
        assert_eq!(result.annual_returns.len(), 5);
        
        println!("LBO Test - MOIC: {:.2}x, IRR: {:.1}%", 
                 result.moic, result.irr * dec!(100));
    }
    
    #[test]
    fn test_irr() {
        let invested = dec!(100);
        let returned = dec!(250);  // 2.5x
        let years = 5;
        
        let irr = calculate_irr(invested, returned, years);
        
        // Should be around 20%
        assert!(irr > dec!(0.19) && irr < dec!(0.21));
        
        println!("IRR test: {:.2}%", irr * dec!(100));
    }
    
    #[test]
    fn test_waterfall() {
        let tiers = vec![
            WaterfallTier {
                name: "Series A Preferred".to_string(),
                ownership_pct: dec!(0.30),
                preference_multiple: dec!(1.0),
                participation: false,
            },
            WaterfallTier {
                name: "Common".to_string(),
                ownership_pct: dec!(0.70),
                preference_multiple: dec!(1.0),
                participation: false,
            },
        ];
        
        let exit_proceeds = dec!(300_000_000);
        let total_invested = dec!(100_000_000);
        
        let results = calculate_waterfall(exit_proceeds, &tiers, total_invested);
        
        assert_eq!(results.len(), 2);
        
        let total_dist: Decimal = results.iter().map(|r| r.distribution).sum();
        assert!((total_dist - exit_proceeds).abs() < dec!(1));  // Should distribute all proceeds
        
        for result in &results {
            println!("{}: ${}, MOIC: {:.2}x", 
                     result.tier_name, result.distribution, result.moic);
        }
    }
}
