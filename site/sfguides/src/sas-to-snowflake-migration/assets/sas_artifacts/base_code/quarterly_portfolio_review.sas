/* =========================================================================
   Quarterly Insurance Portfolio Review
   -------------------------------------------------------------------------
   Author : J. Whitaker, Portfolio Analytics

   Ad-hoc report run every quarter against the LDEMO insurance tables.
   Covers headline KPIs, policy mix, risk profiling, adjuster workload,
   and a regional premium vs claims summary.

   TO RUN: update the four %let parameters below and submit.
   ========================================================================= */

%let reporting_year    = 2025;
%let reporting_quarter = 4;
%let q_start           = 01OCT2025;
%let q_end             = 31DEC2025;
%let q_label           = Q4 2025;

/* -------------------------------------------------------------------------
   Build the working table: customers + their in-quarter claim activity
   ------------------------------------------------------------------------- */
proc sql;
    create table work.quarter_claims as
    select customer_id,
           count(*)                                               as claim_count,
           sum(claim_amount)                                      as claim_total,
           max(claim_amount)                                      as claim_max,
           sum(case when status = 'Open'         then 1 else 0 end) as open_claims,
           sum(case when status = 'Under Review' then 1 else 0 end) as review_claims
    from LDEMO.INSURANCE_CLAIMS
    where claim_date between "&q_start"d and "&q_end"d
    group by customer_id;
quit;

proc sql;
    create table work.portfolio as
    select c.customer_id,
           c.first_name,
           c.last_name,
           c.state,
           c.policy_type,
           c.annual_premium,
           c.risk_score,
           c.policy_start_date,
           year("&q_end"d) - year(c.policy_start_date)  as tenure_years,
           coalesce(q.claim_count,   0)                  as claim_count,
           coalesce(q.claim_total,   0)                  as claim_total,
           coalesce(q.claim_max,     0)                  as claim_max,
           coalesce(q.open_claims,   0)                  as open_claims,
           coalesce(q.review_claims, 0)                  as review_claims,
           coalesce(q.claim_total,   0) / c.annual_premium as loss_ratio
    from LDEMO.INSURANCE_CUSTOMERS c
         left join work.quarter_claims q on c.customer_id = q.customer_id;
quit;

/* Sort portfolio by loss ratio descending for downstream sections */
proc sort data=work.portfolio out=work.portfolio;
    by descending loss_ratio;
run;

/* Enrich portfolio with risk-adjusted premium, loss category, and review flag */
data work.portfolio_enriched;
    set work.portfolio;

    /* Risk-adjusted premium varies by policy type */
    if policy_type = 'Auto' then
        risk_adj_premium = annual_premium * (1.00 + risk_score / 100);
    else if policy_type = 'Home' then
        risk_adj_premium = annual_premium * (1.20 + risk_score / 100);
    else
        risk_adj_premium = annual_premium * (0.80 + risk_score / 150);

    /* Bucket loss ratio into Low / Medium / High */
    if loss_ratio < 0.40 then
        loss_category = 'Low';
    else if loss_ratio < 0.75 then
        loss_category = 'Medium';
    else
        loss_category = 'High';

    /* Flag policies that warrant underwriter review */
    if loss_ratio >= 0.75 and claim_count > 0 then
        review_flag = 1;
    else
        review_flag = 0;
run;

ods pdf file="/tmp/portfolio_review_&reporting_year._Q&reporting_quarter..pdf"
        style=journal startpage=yes;
ods escapechar='^';

title1 j=c "Quarterly Portfolio Review";
title2 j=c "&q_label";
footnote j=r "Generated %sysfunc(datetime(), datetime16.)";

/* ---- Section 1: Portfolio headline numbers ---- */
ods pdf startpage=now;
title3 j=l "1. Portfolio at a glance";
proc sql;
    select count(*)                               as active_customers,
           sum(annual_premium)                    as total_premium,
           mean(annual_premium)                   as avg_premium,
           sum(claim_total)                       as claims_paid,
           sum(claim_total) / sum(annual_premium) as portfolio_loss_ratio
    from work.portfolio_enriched;
quit;

/* ---- Section 2a: Mix by policy type ---- */
proc sql;
    select policy_type,
           count(*)            as customers,
           sum(annual_premium) as premium,
           sum(claim_total)    as claims
    from work.portfolio_enriched
    group by policy_type
    order by premium desc;
quit;

/* ---- Section 2b: Top 10 states by premium ---- */
proc sql outobs=10;
    select state,
           count(*)                             as customers,
           sum(annual_premium)                  as premium,
           sum(claim_total)                     as claims,
           sum(claim_total)/sum(annual_premium) as loss_ratio
    from work.portfolio_enriched
    group by state
    order by premium desc;
quit;

/* ---- Section 3: Risk band x policy type ---- */
proc sql;
    select case
               when risk_score < 30  then 'Low (<30)'
               when risk_score <= 60 then 'Medium (30-60)'
               else 'High (>60)'
           end as risk_band,
           case
               when policy_type in ('Auto', 'Home') then 'Personal Lines'
               when policy_type = 'Life'            then 'Life & Health'
               else 'Other'
           end as policy_group,
           count(*) as customers
    from work.portfolio_enriched
    group by risk_band, policy_group
    order by risk_band, policy_group;
quit;

/* ---- Section 4: Top 25 customers by loss ratio ---- */
proc sql outobs=25;
    select customer_id,
           cats(first_name, ' ', last_name) as full_name,
           state,
           policy_type,
           annual_premium,
           claim_count,
           claim_total,
           loss_ratio
    from work.portfolio_enriched
    where annual_premium > 500 and claim_count > 0
    order by loss_ratio desc;
quit;

/* ---- Section 5: Claims activity by tenure band ---- */
proc sql;
    select case
               when tenure_years < 1 then '< 1 yr'
               when tenure_years < 3 then '1-3 yrs'
               when tenure_years < 7 then '3-7 yrs'
               else '7+ yrs'
           end as tenure_band,
           policy_type,
           sum(annual_premium) as premium,
           sum(claim_total)    as claims,
           sum(claim_count)    as claim_count
    from work.portfolio_enriched
    group by tenure_band, policy_type
    order by tenure_band, policy_type;
quit;

/* ---- Section 6: Adjuster workload for the quarter ---- */
proc sql;
    create table work.adj_workload as
    select adjuster_id, adjuster_name, department, region,
           claims_handled, claim_value, closed_ct,
           closed_ct / claims_handled as closure_rate
    from (
        select a.adjuster_id,
               a.adjuster_name,
               a.department,
               a.region,
               count(cl.claim_id)                                    as claims_handled,
               sum(cl.claim_amount)                                   as claim_value,
               sum(case when cl.status = 'Closed' then 1 else 0 end) as closed_ct
        from LDEMO.INSURANCE_ADJUSTERS a
             left join LDEMO.INSURANCE_CLAIMS cl
                  on a.adjuster_id = cl.adjuster_id
                 and cl.claim_date between "&q_start"d and "&q_end"d
        group by a.adjuster_id, a.adjuster_name, a.department, a.region
        having count(cl.claim_id) > 0
    )
    order by claims_handled desc;
quit;

proc sql outobs=30;
    select adjuster_name, department, region,
           claims_handled, claim_value, closure_rate
    from work.adj_workload;
quit;

/* ---- Section 7: Premium vs claims by region ---- */
proc sql;
    create table work.region_summary as
    select a.region,
           sum(p.annual_premium) as premium,
           sum(p.claim_total)    as claims
    from work.portfolio_enriched p
         inner join LDEMO.INSURANCE_ADJUSTERS a
              on p.customer_id = a.adjuster_id
    group by a.region;
quit;

proc sql;
    select region, premium, claims
    from work.region_summary
    order by premium desc;
quit;

ods pdf close;
title; footnote;
