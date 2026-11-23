// DCF (Discounted Cash Flow) Model
// High-performance implementation using Decimal for precision

use rust_decimal::Decimal;
use rust_decimal::MathematicalOps;  // brings powi() into scope
use rust_decimal_macros::dec;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DCFInputs {
    pub initial_revenue: Decimal,
    pub revenue_growth_rates: Vec<Decimal>,  // Year-by-year or constant
    pub ebitda_margin: Decimal,
    pub tax_rate: Decimal,
    pub capex_pct_revenue: Decimal,
    pub nwc_pct_revenue: Decimal,
    pub wacc: Decimal,
    pub terminal_growth: Decimal,
    pub projection_years: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DCFProjection {
    pub year: usize,
    pub revenue: Decimal,
    pub ebitda: Decimal,
    pub ebitda_margin: Decimal,
    pub nopat: Decimal,
    pub capex: Decimal,
    pub nwc_investment: Decimal,
    pub free_cash_flow: Decimal,
    pub discount_factor: Decimal,
    pub pv_fcf: Decimal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DCFResult {
    pub projections: Vec<DCFProjection>,
    pub total_pv_fcf: Decimal,
    pub terminal_value: Decimal,
    pub pv_terminal: Decimal,
    pub enterprise_value: Decimal,
}

impl DCFInputs {
    /// Create a simple DCF with constant growth
    pub fn new_constant_growth(
        initial_revenue: f64,
        growth_rate: f64,
        ebitda_margin: f64,
        tax_rate: f64,
        wacc: f64,
        terminal_growth: f64,
        years: usize,
    ) -> Self {
        let growth_rates = vec![Decimal::from_f64_retain(growth_rate).unwrap(); years];
        
        DCFInputs {
            initial_revenue: Decimal::from_f64_retain(initial_revenue).unwrap(),
            revenue_growth_rates: growth_rates,
            ebitda_margin: Decimal::from_f64_retain(ebitda_margin).unwrap(),
            tax_rate: Decimal::from_f64_retain(tax_rate).unwrap(),
            capex_pct_revenue: dec!(0.05),  // Default 5%
            nwc_pct_revenue: dec!(0.10),    // Default 10%
            wacc: Decimal::from_f64_retain(wacc).unwrap(),
            terminal_growth: Decimal::from_f64_retain(terminal_growth).unwrap(),
            projection_years: years,
        }
    }
}

pub fn calculate_dcf(inputs: &DCFInputs) -> DCFResult {
    let mut projections = Vec::with_capacity(inputs.projection_years);
    let mut revenue = inputs.initial_revenue;
    let mut total_pv_fcf = dec!(0);
    
    for year in 1..=inputs.projection_years {
        // Get growth rate for this year
        let growth_idx = (year - 1).min(inputs.revenue_growth_rates.len() - 1);
        let growth_rate = inputs.revenue_growth_rates[growth_idx];
        
        // Revenue projection
        revenue = revenue * (dec!(1) + growth_rate);
        
        // EBITDA
        let ebitda = revenue * inputs.ebitda_margin;
        let ebitda_margin = inputs.ebitda_margin;
        
        // NOPAT (simplified - no D&A detail for this version)
        let nopat = ebitda * (dec!(1) - inputs.tax_rate);
        
        // CapEx
        let capex = revenue * inputs.capex_pct_revenue;
        
        // Change in NWC (simplified incremental approach)
        let nwc_investment = revenue * inputs.nwc_pct_revenue * growth_rate / (dec!(1) + growth_rate);
        
        // Unlevered Free Cash Flow
        let fcf = nopat - capex - nwc_investment;
        
        // Discount factor
        let discount_factor = (dec!(1) + inputs.wacc).powi(year as i64);
        
        // Present value of FCF
        let pv_fcf = fcf / discount_factor;
        total_pv_fcf += pv_fcf;
        
        projections.push(DCFProjection {
            year,
            revenue,
            ebitda,
            ebitda_margin,
            nopat,
            capex,
            nwc_investment,
            free_cash_flow: fcf,
            discount_factor,
            pv_fcf,
        });
    }
    
    // Terminal value (Gordon Growth Model)
    let last_fcf = projections.last().unwrap().free_cash_flow;
    let terminal_value = last_fcf * (dec!(1) + inputs.terminal_growth) 
        / (inputs.wacc - inputs.terminal_growth);
    
    // PV of terminal value
    let pv_terminal = terminal_value / (dec!(1) + inputs.wacc).powi(inputs.projection_years as i64);
    
    // Enterprise value
    let enterprise_value = total_pv_fcf + pv_terminal;
    
    DCFResult {
        projections,
        total_pv_fcf,
        terminal_value,
        pv_terminal,
        enterprise_value,
    }
}

/// Sensitivity analysis - vary two parameters
pub fn dcf_sensitivity_2d(
    base_inputs: &DCFInputs,
    param1_name: &str,
    param1_values: &[f64],
    param2_name: &str,
    param2_values: &[f64],
) -> Vec<Vec<Decimal>> {
    use rayon::prelude::*;
    
    param1_values.par_iter().map(|&p1| {
        param2_values.iter().map(|&p2| {
            let mut inputs = base_inputs.clone();
            
            // Update parameter 1
            match param1_name {
                "wacc" => inputs.wacc = Decimal::from_f64_retain(p1).unwrap(),
                "terminal_growth" => inputs.terminal_growth = Decimal::from_f64_retain(p1).unwrap(),
                "ebitda_margin" => inputs.ebitda_margin = Decimal::from_f64_retain(p1).unwrap(),
                _ => {}
            }
            
            // Update parameter 2
            match param2_name {
                "wacc" => inputs.wacc = Decimal::from_f64_retain(p2).unwrap(),
                "terminal_growth" => inputs.terminal_growth = Decimal::from_f64_retain(p2).unwrap(),
                "ebitda_margin" => inputs.ebitda_margin = Decimal::from_f64_retain(p2).unwrap(),
                "growth_rate" => {
                    inputs.revenue_growth_rates = vec![Decimal::from_f64_retain(p2).unwrap(); inputs.projection_years];
                }
                _ => {}
            }
            
            calculate_dcf(&inputs).enterprise_value
        }).collect()
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_simple_dcf() {
        let inputs = DCFInputs::new_constant_growth(
            100_000_000.0,  // $100M revenue
            0.10,           // 10% growth
            0.25,           // 25% EBITDA margin
            0.25,           // 25% tax rate
            0.12,           // 12% WACC
            0.03,           // 3% terminal growth
            5               // 5 years
        );
        
        let result = calculate_dcf(&inputs);
        
        assert!(result.enterprise_value > dec!(0));
        assert_eq!(result.projections.len(), 5);
        
        // Revenue should grow
        assert!(result.projections[4].revenue > result.projections[0].revenue);
        
        println!("DCF Test - Enterprise Value: ${}", result.enterprise_value);
    }
    
    #[test]
    fn test_sensitivity() {
        let inputs = DCFInputs::new_constant_growth(
            100_000_000.0, 0.10, 0.25, 0.25, 0.12, 0.03, 5
        );
        
        let wacc_range: Vec<f64> = (10..=14).map(|x| x as f64 / 100.0).collect();
        let growth_range: Vec<f64> = (8..=12).map(|x| x as f64 / 100.0).collect();
        
        let results = dcf_sensitivity_2d(&inputs, "wacc", &wacc_range, "growth_rate", &growth_range);
        
        assert_eq!(results.len(), wacc_range.len());
        assert_eq!(results[0].len(), growth_range.len());
        
        println!("Sensitivity test completed: {} x {} matrix", results.len(), results[0].len());
    }
}
