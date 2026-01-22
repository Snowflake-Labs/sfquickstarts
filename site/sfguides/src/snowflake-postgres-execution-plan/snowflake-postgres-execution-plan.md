author: Brian Pace
id: snowflake-postgres-execution-plan
categories: snowflake-site:taxonomy/solution-center/certification/quickstart, snowflake-site:taxonomy/product/platform
language: en
summary: Using Postgres EXPLAIN to understand query execution
environments: web
status: Published 
feedback link: https://github.com/Snowflake-Labs/sfguides/issues

# Postgres Execution Plan
<!-- ------------------------ -->
## Overview 

Have you ever wondered why a query runs slowly, or how the database decides which approach to use when fetching your data? PostgreSQL's `EXPLAIN` command answers these questions by revealing the **execution plan** — the step-by-step strategy the database uses to retrieve your results.

An execution plan is like a recipe that PostgreSQL follows to cook up your query results. Just as a chef might chop vegetables before sautéing them, the database performs operations in a specific order: scanning tables, filtering rows, joining data, and sorting results.

Understanding how to read an execution plan is crucial for SQL tuning. Plans are tree structures that execute **from the deepest indentation outward**, processing children before parents. You may hear this described as **"bottom up, inside out"** — where "bottom" refers to the leaves of the tree (most indented in text output), and "inside" refers to the innermost nested structures.

By the end of this guide, you'll be able to look at any execution plan and understand exactly what PostgreSQL is doing — and more importantly, spot opportunities to make your queries faster.

### What You'll Learn

- How to generate execution plans using `EXPLAIN` and its options
- How to read and interpret the tree structure of an execution plan
- What the cost estimates and timing information mean
- How different operations (scans, joins, aggregations) appear in plans
- Common patterns to look for when tuning queries

### Prerequisites

- A running Snowflake Postgres instance
- Basic familiarity with SQL SELECT, JOIN, and WHERE clauses
- Access to `psql` or another PostgreSQL client

<!-- ------------------------ -->
## Generating an Execution Plan

PostgreSQL provides the `EXPLAIN` command to show you how it plans to execute a query. Think of it as asking the database, "How would you approach this?" before actually doing the work.

There are two main ways to use EXPLAIN:
- **EXPLAIN** (without ANALYZE) — Shows the *plan* without executing the query. This is safe and fast, giving you the database's best guess based on table statistics.
- **EXPLAIN ANALYZE** — Actually *runs* the query and shows you what really happened. This gives you accurate numbers but takes time to execute.

Let's explore both approaches.

### Basic EXPLAIN

The simplest form shows the planner's chosen execution strategy without running the query. This is useful when you want a quick look at the plan without waiting for the query to complete.

```sql
EXPLAIN SELECT * FROM orders WHERE customer_id = 42;
```

**Output:**
```
Seq Scan on orders  (cost=0.00..2041.00 rows=10 width=52)
  Filter: (customer_id = 42)
```

Let's break down what this output tells us:

| Component | Meaning |
|-----------|---------|
| `Seq Scan on orders` | The operation type — a sequential (full table) scan of the orders table |
| `cost=0.00..2041.00` | Estimated cost: startup cost (0.00) to total cost (2041.00) in arbitrary units |
| `rows=10` | Estimated number of rows this step will return |
| `width=52` | Average size of each row in bytes |
| `Filter: (customer_id = 42)` | The condition applied to filter rows |

> **Note**: The cost values are in PostgreSQL's internal units — they're useful for comparing different plans, but don't represent actual time.

### EXPLAIN with Options

EXPLAIN supports many options that control what information is displayed. You can combine multiple options by separating them with commas inside parentheses.

```sql
EXPLAIN (option [, ...]) statement
```

Here are the available options:

| Option | Description | Notes |
|--------|-------------|-------|
| `ANALYZE` | Actually execute the query and show real statistics | ⚠️ Runs the query! |
| `VERBOSE` | Show additional details like output column lists | Useful for complex queries |
| `COSTS` | Show cost estimates (enabled by default) | Disable with `COSTS OFF` |
| `BUFFERS` | Show buffer/cache usage statistics | Requires ANALYZE |
| `TIMING` | Show actual time spent in each node | Requires ANALYZE |
| `SUMMARY` | Show planning and execution time totals | Helpful for overall timing |
| `FORMAT` | Output format: TEXT, JSON, YAML, or XML | TEXT is default |
| `SETTINGS` | Show any modified configuration settings | Useful for debugging |
| `WAL` | Show Write-Ahead Log usage | Requires ANALYZE |
| `MEMORY` | Show memory usage information | Useful for memory-intensive queries |

**Example combining options:**

```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT) 
SELECT * FROM orders WHERE customer_id = 42;
```

### EXPLAIN ANALYZE

While basic EXPLAIN shows estimates, `EXPLAIN ANALYZE` runs the query and shows what *actually* happened. This is invaluable when you suspect the planner's estimates are wrong.

```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 42;
```

**Output:**
```
Seq Scan on orders  (cost=0.00..2041.00 rows=10 width=52) (actual time=0.015..12.345 rows=8 loops=1)
  Filter: (customer_id = 42)
  Rows Removed by Filter: 99992
Planning Time: 0.089 ms
Execution Time: 12.367 ms
```

Notice the new information compared to basic EXPLAIN:

| Component | Meaning |
|-----------|---------|
| `actual time=0.015..12.345` | Real timing in milliseconds: time to first row (0.015ms) and time to all rows (12.345ms) |
| `rows=8` | Actual rows returned (compare to the estimate of 10) |
| `loops=1` | How many times this operation was executed |
| `Rows Removed by Filter: 99992` | How many rows were scanned but didn't match the filter |
| `Planning Time: 0.089 ms` | Time spent creating the execution plan |
| `Execution Time: 12.367 ms` | Total time to execute the query |

> **Tip**: Compare estimated rows to actual rows. If they differ significantly, your table statistics may be out of date. Run `ANALYZE table_name;` to refresh them.

⚠️ **Warning**: ANALYZE actually executes the query. For INSERT, UPDATE, or DELETE statements, always wrap in a transaction to prevent unintended changes:

```sql
BEGIN;
EXPLAIN ANALYZE DELETE FROM orders WHERE status = 'cancelled';
ROLLBACK;  -- Don't actually delete!
```

This lets you see the execution plan without committing the changes.

### Full Diagnostic Output

When troubleshooting a problematic query, use this comprehensive combination to get the most detailed information:

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, TIMING, SUMMARY, FORMAT TEXT)
SELECT * FROM orders WHERE customer_id = 42;
```

This shows:
- **ANALYZE**: Actual execution statistics
- **BUFFERS**: How many database pages were read from cache vs. disk
- **VERBOSE**: Extra details like schema-qualified table names and output columns
- **TIMING**: Precise timing for each operation
- **SUMMARY**: Planning and total execution time

> **When to use this**: Use full diagnostic output when a query is performing poorly and you need to understand exactly where time is being spent.

<!-- ------------------------ -->
## Plan Output Formats

EXPLAIN can output plans in several formats. Choose based on how you'll use the output.

### TEXT Format (Default)

The default format is human-readable with indentation showing the tree structure. This is what you'll use most often when analyzing queries interactively.

```sql
EXPLAIN (FORMAT TEXT) SELECT * FROM orders WHERE customer_id = 42;
```

```
Seq Scan on orders  (cost=0.00..2041.00 rows=10 width=52)
  Filter: (customer_id = 42)
```

### JSON Format

JSON is ideal for programmatic analysis, visualization tools like [explain.depesz.com](https://explain.depesz.com) or [explain.dalibo.com](https://explain.dalibo.com), and storing plans for later comparison.

```sql
EXPLAIN (ANALYZE, FORMAT JSON) SELECT * FROM orders WHERE customer_id = 42;
```

```json
[
  {
    "Plan": {
      "Node Type": "Seq Scan",
      "Relation Name": "orders",
      "Startup Cost": 0.00,
      "Total Cost": 2041.00,
      "Plan Rows": 10,
      "Plan Width": 52,
      "Actual Startup Time": 0.015,
      "Actual Total Time": 12.345,
      "Actual Rows": 8,
      "Actual Loops": 1
    }
  }
]
```

> **Tip**: Many online EXPLAIN visualization tools accept JSON format and render interactive, color-coded plan diagrams.

### YAML Format

YAML is also machine-readable and slightly more compact than JSON:

```sql
EXPLAIN (ANALYZE, FORMAT YAML) SELECT * FROM orders WHERE customer_id = 42;
```

### XML Format

XML format is available for integration with XML-based tools and workflows:

```sql
EXPLAIN (ANALYZE, FORMAT XML) SELECT * FROM orders WHERE customer_id = 42;
```

<!-- ------------------------ -->
## Reading the Execution Plan

Looking at an execution plan can seem overwhelming at first — there are nested operations, cost numbers, and unfamiliar terms. Don't worry! Once you understand the structure, it becomes much clearer.

An execution plan is a **tree structure**. Just like a family tree, it has a root at the top and branches down to leaves at the bottom. The key insight is that **data flows from the leaves up to the root**:

- **Leaf nodes** (most indented) are where data originates — typically table scans
- **Parent nodes** combine, filter, or transform data from their children
- **The root node** (least indented) produces the final result

### The Golden Rules

When reading any execution plan, follow these three simple rules:

1. **Start at the deepest indentation** — Find the most indented lines; these are the leaf nodes where execution begins
2. **Work your way up** — Follow the data as it flows upward through parent operations to the root
3. **For nodes at the same level** — Read from top to bottom (the first child is the "outer" side, which drives execution)

### A Visual Example

Let's see how these rules apply to a real query. Consider this query joining three tables:

```sql
EXPLAIN SELECT c.name, o.order_date, oi.product_name
        FROM customers c
             JOIN orders o ON c.id = o.customer_id
             JOIN order_items oi ON o.id = oi.order_id
        WHERE c.country = 'USA';
```

The execution plan might look like this (we've numbered the operations in execution order):

```
Nested Loop  (cost=0.87..1234.56 rows=100 ...)               -- [5] LAST: Final result
   ->  Nested Loop  (cost=0.58..890.12 rows=50 ...)          -- [3] Combine customers+orders
         ->  Index Scan on customers c  (...)                 -- [1] FIRST: Start here
               Index Cond: (country = 'USA')
         ->  Index Scan on orders o  (...)                    -- [2] For each customer
               Index Cond: (customer_id = c.id)
   ->  Index Scan on order_items oi  (...)                   -- [4] For each order
         Index Cond: (order_id = o.id)
```

Notice how the Index Scan on customers (the most deeply indented operation) executes first, even though it appears in the middle of the text output. The indentation shows nesting depth, not execution order.

### Execution Order Visualized

Here's the same plan shown as a tree diagram. Notice how data flows from the bottom (leaves) up to the top (root):

```
                    ┌─────────────────┐
            [5]     │  Nested Loop    │  ◄── Final output to client
                    │  (outer join)   │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
       ┌──────┴──────┐              ┌───────┴───────┐
 [3]   │ Nested Loop │              │  Index Scan   │  [4] For EACH row
       │(inner join) │              │ order_items   │      from [3]
       └──────┬──────┘              └───────────────┘
              │
    ┌─────────┴─────────┐
    │                   │
┌───┴─────┐       ┌─────┴─────┐
│ Index   │  [1]  │Index Scan │  [2] For EACH row
│ Scan    │ START │  orders   │      from [1]
│customers│ HERE  └───────────┘
└─────────┘
```

**Step-by-step execution:**

Here's exactly what happens when PostgreSQL runs this plan:

1. **[1] Index Scan on customers** — PostgreSQL finds customers where `country = 'USA'` using an index. This is where execution starts.
2. **[2] Index Scan on orders** — For **each** customer found in step 1, PostgreSQL looks up their orders using the `customer_id` index.
3. **[3] Nested Loop (inner)** — Combines each customer row with their matching order rows.
4. **[4] Index Scan on order_items** — For **each** customer+order combination from step 3, PostgreSQL finds the order items.
5. **[5] Nested Loop (outer)** — Combines everything and produces the final result rows.

> **Key insight**: In a Nested Loop join, the "inner" side (second child) executes *repeatedly* — once for each row from the outer side. This is why the number in `loops=N` matters so much.

### Understanding "Outer" and "Inner" Children

When you see a join operation with two children, each child has a specific role. The terms "outer" and "inner" refer to how the join algorithm uses each input:

- **Outer (first child)**: The driving side — typically scanned or iterated through
- **Inner (second child)**: The lookup side — accessed based on values from the outer side

Different join types use their children differently:

#### Hash Join

In a Hash Join, PostgreSQL builds a hash table from one input, then probes it with the other:

```
Hash Join  (cost=... rows=...)
   Hash Cond: (o.customer_id = c.id)
   ->  Seq Scan on orders o  (...)           -- OUTER: Scanned row-by-row (probe side)
   ->  Hash  (...)                           -- INNER: Built into hash table FIRST
         ->  Seq Scan on customers c  (...)
```

**How Hash Join executes:**
1. **Build phase** (inner side first): Read all customers and build a hash table in memory
2. **Probe phase** (outer side): For each order, look up the matching customer in the hash table

> **Performance tip**: Hash Joins work best when the inner (build) side fits in memory. If you see "Batches: 2" or higher in the output, the hash table spilled to disk, which slows things down.

#### Nested Loop

In a Nested Loop, PostgreSQL iterates through the outer side and, for each row, searches the inner side:

```
Nested Loop  (cost=... rows=...)
   ->  Index Scan on customers  (...)        -- OUTER: Drives the loop
   ->  Index Scan on orders  (...)           -- INNER: Executed for EACH outer row
         Index Cond: (customer_id = c.id)
```

**How Nested Loop executes:**
1. Get one row from the outer side (customers)
2. Search the inner side (orders) for all matching rows
3. Output the combined rows
4. Repeat steps 1-3 for each outer row

> **Performance tip**: Nested Loops are efficient when the outer side returns few rows and the inner side has a good index. They can be slow when the outer side is large, since the inner side runs once per outer row.

### Reading Complex Plans

Real-world queries often involve multiple operations: joins, filters, aggregations, and sorting. Let's work through a more complex example to see how all the pieces fit together.

Here's a query that joins tables, filters, aggregates, and sorts:

```sql
EXPLAIN SELECT c.country, COUNT(*), SUM(o.total_amount)
        FROM customers c
             JOIN orders o ON c.id = o.customer_id
        WHERE o.order_date >= '2023-01-01'
        GROUP BY c.country
        ORDER BY COUNT(*) DESC;
```

```
Sort  (cost=5678.90..5679.12 rows=7 ...)                     -- [6] Sort final results
   Sort Key: (count(*)) DESC
   ->  HashAggregate  (cost=5670.00..5678.50 rows=7 ...)     -- [5] Group and aggregate
         Group Key: c.country
         ->  Hash Join  (cost=350.00..5500.00 rows=50000)    -- [4] Combine results
               Hash Cond: (o.customer_id = c.id)
               ->  Seq Scan on orders o  (...)               -- [3] Scan filtered orders
                     Filter: (order_date >= '2023-01-01')
               ->  Hash  (cost=200.00..200.00 rows=10000)    -- [2] Build hash table
                     ->  Seq Scan on customers c  (...)      -- [1] START: Scan customers
```

**Execution order explained:**

| Step | Operation | What Happens |
|------|-----------|--------------|
| 1 | Seq Scan on customers | Read all customer rows from the table |
| 2 | Hash | Build a hash table keyed by customer.id |
| 3 | Seq Scan on orders | Read orders, keeping only those from 2023 onwards |
| 4 | Hash Join | For each order, find the matching customer in the hash table |
| 5 | HashAggregate | Group the joined rows by country; calculate COUNT and SUM for each group |
| 6 | Sort | Sort the aggregated results by count in descending order |

Notice how the data "flows" upward: raw table data → joined data → aggregated data → sorted results.

### The "loops" Multiplier

When using EXPLAIN ANALYZE, you'll see `loops=N` for each operation. This tells you how many times that operation was executed. This is crucial for understanding true costs because the reported time and row counts are **per execution**.

```
Nested Loop  (actual time=0.050..45.678 rows=5000 loops=1)
   ->  Seq Scan on customers  (actual time=0.010..1.234 rows=100 loops=1)
   ->  Index Scan on orders  (actual time=0.005..0.400 rows=50 loops=100)
                                                        ^^^^      ^^^^^^^^
                                                   50 rows × 100 loops = 5000 total
```

In this example, the Index Scan on orders shows `rows=50 loops=100`. This means:
- Each execution returned 50 rows
- It ran 100 times (once for each customer from the outer side)

**Calculating true totals:**

| Metric | Formula | Calculation | Result |
|--------|---------|-------------|--------|
| Total rows | rows × loops | 50 × 100 | 5,000 rows |
| Total time | time × loops | 0.400ms × 100 | 40ms |

> **Why this matters**: An operation showing "0.5ms" might seem fast, but if it runs 10,000 times, that's 5 seconds of total execution time! Always multiply by loops to understand the true cost.

### Understanding Cumulative Costs

One of the trickiest aspects of reading EXPLAIN output is understanding that costs are **cumulative** — each node's cost includes the costs of all its children. This means a high cost at a parent node doesn't necessarily mean that node is the problem; the issue might be in one of its children.

The key insight is that *which* child costs are included in a node's startup cost depends on **when that node can start producing output**. Some operations can begin producing output immediately (streaming), while others must wait for all input before producing anything (blocking).

#### How Different Nodes Include Child Costs

Understanding which nodes are "blocking" (must wait for all input) versus "streaming" (can start immediately) helps you interpret costs correctly:

| Node Type | Startup Cost Includes | Behavior | Why |
|-----------|----------------------|----------|-----|
| **Sort** | Child's **total** cost | Blocking | Must read ALL rows before producing any sorted output |
| **HashAggregate** | Child's **total** cost | Blocking | Must see ALL rows to compute aggregates correctly |
| **Hash** (build side) | Child's **total** cost | Blocking | Must build complete hash table before joins can start |
| **Nested Loop** | Sum of children's **startup** costs | Streaming | Can emit first row as soon as it finds a match |
| **Merge Join** | Sum of children's **startup** costs | Streaming | Can start merging once both sorted inputs begin |
| **GroupAggregate** | Child's **startup** cost | Streaming | Can output each group as soon as it's complete |
| **Limit** | Child's **startup** cost | Streaming | Passes through rows immediately, stops when limit reached |

#### Example: Sort Includes Child's Total Cost

Sort is a classic blocking operation. It cannot output the smallest (or largest) value until it has seen every input row.

```
Sort  (cost=5000.00..5100.00 rows=1000)
   ->  Seq Scan on orders (cost=0.00..5000.00 rows=100000)
```

Breaking down the costs:
- **Seq Scan**: startup=0, total=5000 (starts immediately, takes 5000 units to complete)
- **Sort**: startup=**5000**, total=5100 (must wait for child to finish before starting)

Notice that Sort's startup cost (5000) equals the Seq Scan's total cost. This makes sense: Sort cannot begin producing output until it has received all 100,000 rows from the scan.

The Sort's own work (comparing and sorting) adds only 100 cost units (5100 - 5000), but the startup cost reflects the waiting time.

#### Example: Nested Loop Sums Children's Startup Costs

Nested Loop is a streaming operation. It can output results as soon as it finds matches, without waiting for either input to complete.

```
Nested Loop  (cost=0.50..1234.00 rows=100)
   ->  Index Scan on customers (cost=0.29..50.00 rows=10)
   ->  Index Scan on orders (cost=0.21..10.00 rows=10)
```

Breaking down the costs:
- **Customers Index Scan**: startup=0.29 (time to position the index)
- **Orders Index Scan**: startup=0.21 (time to position the index)
- **Nested Loop**: startup=**0.50** (= 0.29 + 0.21)

The Nested Loop can produce its first output row as soon as:
1. The customers scan returns its first row (0.29)
2. The orders scan finds a match for that customer (0.21)

This is why Nested Loops often have low startup costs — they're excellent when you only need the first few results (like with LIMIT clauses).

#### Example: Hash Join (Asymmetric)

Hash Join is interesting because it's asymmetric — one side (the build side) must complete before the other side begins.

```
Hash Join  (cost=125.00..500.00 rows=1000)
   Hash Cond: (o.customer_id = c.id)
   ->  Seq Scan on orders o (cost=0.00..200.00 rows=10000)     -- Outer (probe side)
   ->  Hash  (cost=100.00..100.00 rows=1000)                   -- Inner (build side)
         ->  Seq Scan on customers c (cost=0.00..100.00)
```

The Hash Join startup cost (125.00) breaks down as:
- **Hash table build** (100.00): Must completely finish before any probing can start
- **Probe side startup** (0.00): Just needs to be ready to start
- **Join overhead** (25.00): Cost of the hash join operation itself

This reflects reality: PostgreSQL must read all customers and build the hash table before it can look up even a single order. The probe side (orders) can then stream through, with each row quickly finding its match in the hash table.

#### Why This Matters for Tuning

Understanding cumulative costs helps you make better optimization decisions:

**1. Find the real bottleneck**

A high cost at the top doesn't mean the top node is slow — it might just be accumulating costs from expensive children. Always drill down to find where the cost actually originates.

**2. Understand query responsiveness**

Blocking operations (Sort, HashAggregate, Hash) mean the user waits for everything to finish before seeing any results. Streaming operations (Nested Loop, Limit) can show results quickly even if the total time is the same.

**3. Optimize for your use case**

```
-- This plan can start returning rows quickly (low startup cost)
-- Good for: Interactive queries, pagination, LIMIT queries
Nested Loop  (cost=0.50..1000.00)   -- startup=0.50
   ->  Index Scan ...              -- startup=0.29
   ->  Index Scan ...              -- startup=0.21

-- This plan blocks until all data is processed (high startup cost)
-- Acceptable for: Batch reports, data exports
Sort  (cost=5000.00..5100.00)       -- startup=5000 (must wait for child)
   ->  Seq Scan ...                -- total=5000
```

> **Tip**: For interactive applications, look for plans with low startup costs. For batch processing, total cost matters more than startup cost.

### Quick Reference: Common Node Types

Here's a handy reference for understanding the most common operations you'll see in execution plans:

| Operation | What It Does | Performance Characteristics |
|-----------|--------------|----------------------------|
| **Seq Scan** | Reads entire table row by row | Fast for small tables or when reading most rows; slow for large tables with selective filters |
| **Index Scan** | Uses index to find specific rows | Fast for selective queries; returns rows in index order |
| **Index Only Scan** | Answers query entirely from index | Fastest option when all needed columns are in the index |
| **Bitmap Scan** | Combines multiple index lookups | Good for moderate selectivity; avoids random I/O |
| **Nested Loop** | For each outer row, scan inner | Best with small outer side + indexed inner side |
| **Hash Join** | Build hash table, probe with other side | Best for larger joins; requires memory |
| **Merge Join** | Merge two sorted inputs | Fast when inputs are already sorted |
| **Sort** | Sort rows in memory or on disk | Blocking; watch for "Sort Method: external" (disk spill) |
| **HashAggregate** | Hash-based grouping | Fast for many groups; uses memory |
| **GroupAggregate** | Stream-based grouping | Requires sorted input; low memory usage |
| **Limit** | Return only first N rows | Can dramatically speed up queries if combined with streaming operations |

<!-- ------------------------ -->
## Parallel Query Execution

For large tables and complex queries, PostgreSQL can use multiple CPU cores to speed up execution. When you see nodes like `Gather` or `Parallel Seq Scan` in your execution plan, the database is distributing work across multiple worker processes.

### How Parallel Queries Work

In a parallel query, PostgreSQL divides the work among:
- **Leader process**: The main backend process that coordinates the query
- **Worker processes**: Additional processes that handle portions of the work

The workers execute their portion of the plan, and the leader collects and combines their results.

### Identifying Parallel Operations

Here's what a parallel query plan looks like:

```sql
EXPLAIN ANALYZE SELECT COUNT(*) FROM large_orders WHERE amount > 100;
```

```
Finalize Aggregate  (actual time=245.89..247.12 rows=1 loops=1)
   ->  Gather  (actual time=245.12..247.05 rows=3 loops=1)
         Workers Planned: 2
         Workers Launched: 2
         ->  Partial Aggregate  (actual time=241.34..241.35 rows=1 loops=3)
               ->  Parallel Seq Scan on large_orders  (actual time=0.02..198.45 rows=166667 loops=3)
                     Filter: (amount > 100)
                     Rows Removed by Filter: 333333
Planning Time: 0.12 ms
Execution Time: 247.45 ms
```

### Key Parallel Nodes

| Node | Description |
|------|-------------|
| **Gather** | Collects rows from parallel workers into a single stream |
| **Gather Merge** | Like Gather, but preserves sort order from workers |
| **Parallel Seq Scan** | Sequential scan divided among workers |
| **Parallel Index Scan** | Index scan divided among workers |
| **Parallel Hash Join** | Hash join where workers collaborate |
| **Partial Aggregate** | Each worker computes a partial aggregate |
| **Finalize Aggregate** | Combines partial aggregates into final result |

### Reading Parallel Plan Statistics

The key to understanding parallel plans is the `loops` value:

```
Parallel Seq Scan on large_orders  (actual time=0.02..198.45 rows=166667 loops=3)
```

Here, `loops=3` means:
- **1 leader** + **2 workers** = 3 processes
- Each process scanned ~166,667 rows
- **Total rows scanned**: 166,667 × 3 = 500,000 rows

The timing shown (198.45 ms) is the average per process. Since they run in parallel, the wall-clock time is roughly the same as a single worker's time, not the sum.

### Understanding Worker Statistics

With `EXPLAIN ANALYZE`, you can see detailed worker statistics:

```
Gather  (actual time=245.12..247.05 rows=3 loops=1)
   Workers Planned: 2
   Workers Launched: 2
```

| Field | Meaning |
|-------|---------|
| **Workers Planned** | Number of workers the planner intended to use |
| **Workers Launched** | Number of workers actually started |

If `Workers Launched` is less than `Workers Planned`, the system may be under resource pressure (other queries using workers, or hitting `max_parallel_workers`).

### When PostgreSQL Uses Parallelism

PostgreSQL considers parallel execution when:

1. **Table size exceeds threshold**: The table must be larger than `min_parallel_table_scan_size` (default 8MB)
2. **Cost justifies it**: The parallel plan must be cheaper than the serial alternative
3. **Workers are available**: Must not exceed `max_parallel_workers_per_gather`
4. **Query type supports it**: Not all operations can be parallelized

Operations that **can** be parallelized:
- Sequential scans
- Index scans and index-only scans
- Hash joins (build and probe phases)
- Nested loop joins (inner side)
- Aggregates (with partial/finalize pattern)

Operations that **cannot** be parallelized:
- Writing data (INSERT, UPDATE, DELETE)
- Cursors
- Some procedural language functions

### Parallel Aggregation Pattern

Aggregates use a two-phase approach in parallel plans:

```
Finalize Aggregate          -- Combines partial results
   ->  Gather               -- Collects from workers
         ->  Partial Aggregate   -- Each worker computes partial result
               ->  Parallel Seq Scan
```

**Phase 1 (Partial)**: Each worker computes its own aggregate over its portion of data

**Phase 2 (Finalize)**: The leader combines partial results:
- `COUNT`: Sum the partial counts
- `SUM`: Sum the partial sums
- `AVG`: Combine (sum, count) pairs, then divide
- `MIN/MAX`: Take min/max of partial results

### Parallel Hash Join Example

Hash joins can also run in parallel:

```
Gather  (actual time=156.78..892.34 rows=50000 loops=1)
   Workers Planned: 2
   Workers Launched: 2
   ->  Parallel Hash Join  (actual time=152.12..845.67 rows=16667 loops=3)
         Hash Cond: (orders.customer_id = customers.id)
         ->  Parallel Seq Scan on orders  (actual time=0.03..123.45 rows=333333 loops=3)
         ->  Parallel Hash  (actual time=45.23..45.23 rows=3333 loops=3)
               Buckets: 16384  Batches: 1  Memory Usage: 512kB
               ->  Parallel Seq Scan on customers  (actual time=0.02..34.56 rows=3333 loops=3)
```

In a `Parallel Hash Join`:
- **Both sides** can be scanned in parallel
- Workers **collaborate** to build a shared hash table
- Each worker then probes the shared hash table with its portion of the outer side

### Performance Considerations

**When parallel queries help:**
- Large table scans (millions of rows)
- CPU-intensive operations (complex filters, aggregations)
- Sufficient CPU cores available

**When parallel queries may not help:**
- Small tables (overhead exceeds benefit)
- I/O-bound queries (parallelism doesn't help if waiting for disk)
- Already using many parallel workers from other queries

> **Tip**: If you see `Workers Planned: 4` but `Workers Launched: 2`, your system might be hitting the `max_parallel_workers` limit. Consider adjusting this setting or scheduling queries to avoid contention.

<!-- ------------------------ -->
## Practice: Trace This Plan

Now it's your turn! Look at this execution plan and try to trace the execution order before reading the answer.

```
Limit  (actual time=0.050..5.234 rows=10 loops=1)
   ->  Sort  (actual time=0.048..5.200 rows=10 loops=1)
         Sort Key: total_amount DESC
         ->  Hash Join  (actual time=2.345..4.567 rows=500 loops=1)
               Hash Cond: (o.customer_id = c.id)
               ->  Seq Scan on orders o  (actual time=0.010..1.234 rows=1000 loops=1)
                     Filter: (status = 'pending')
               ->  Hash  (actual time=1.234..1.234 rows=100 loops=1)
                     ->  Seq Scan on customers c  (actual time=0.008..0.890 rows=100 loops=1)
                           Filter: (country = 'USA')
```

**Hint**: Start at the deepest indentation (the Seq Scan on customers), then work your way up.

<details>
<summary>Click to reveal the answer</summary>

**Execution order:**

| Step | Operation | Result |
|------|-----------|--------|
| 1 | Seq Scan on customers | Find USA customers → **100 rows** (0.89ms) |
| 2 | Build Hash table | Create hash table from those 100 customers (1.23ms total) |
| 3 | Seq Scan on orders | Find pending orders → **1,000 rows** (1.23ms) |
| 4 | Hash Join | Match orders to customers → **500 matches** (4.57ms total) |
| 5 | Sort | Sort 500 rows by total_amount DESC (5.20ms total) |
| 6 | Limit | Return first 10 rows → **10 rows** (5.23ms total) |

**Observations:**
- The customers scan (100 rows) is much smaller than orders (1000 rows), making it a good choice for the hash build side
- Sort had to process all 500 joined rows even though Limit only needs 10 — this is a potential optimization opportunity (adding an index on total_amount could help)
- Total execution time was about 5.2ms, with most time spent in the Sort operation

</details>

<!-- ------------------------ -->
## Conclusion and Next Steps

Congratulations! You've learned how to use PostgreSQL's EXPLAIN command to understand and optimize query performance. These skills are essential for maintaining efficient database applications.

### What You Learned

1. How to generate execution plans using EXPLAIN and its various options
2. How to interpret cost estimates, row counts, and timing information
3. How to read execution plans from the inside out (deepest indentation first)
4. How to understand different node types including Seq Scan, Index Scan, and various join methods
5. How to identify blocking operations versus streaming operations
6. How to use the `loops` multiplier to calculate true execution totals

### Key Takeaways

- **Use EXPLAIN ANALYZE** when you need actual runtime statistics, but remember it executes the query
- **Wrap data-modifying statements** in BEGIN/ROLLBACK when using EXPLAIN ANALYZE
- **High startup costs** indicate blocking operations that must complete before producing output
- **Check the innermost nodes first** — they often reveal the root cause of performance issues
- **Compare estimated vs actual rows** — large discrepancies suggest outdated statistics

### Resources

- [PostgreSQL EXPLAIN Documentation](https://www.postgresql.org/docs/current/sql-explain.html)
- [PostgreSQL Query Planning](https://www.postgresql.org/docs/current/planner-optimizer.html)
- [Using EXPLAIN - PostgreSQL Wiki](https://wiki.postgresql.org/wiki/Using_EXPLAIN)
- [PostgreSQL Performance Tips](https://www.postgresql.org/docs/current/performance-tips.html)
- [Snowflake Postgres Tables Documentation](https://docs.snowflake.com/en/user-guide/tables-postgres)
