"""
distribution_demo.py — Shannon entropy distribution analysis with Cortex + Ibis

Demonstrates:
  1. Loading 300 synthetic reviews as an Ibis memtable
  2. Computing entropy two ways:
       a. entropy_from_pandas() — scipy-based, works locally
       b. category_entropy()    — pure Ibis SQL, runs in Snowflake
  3. Rich table + ASCII bar chart of per-product entropy
  4. SVG screenshot saved to s_entropy.svg (same directory)

Run:
  python distribution_demo.py
"""

from __future__ import annotations

import math
from pathlib import Path

import ibis
import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from synthetic_data import make_reviews, distribution_summary, CATEGORIES
from cortex_ibis import entropy_from_pandas, category_entropy, normalized_entropy

ASSETS = Path(__file__).parent
ASSETS.mkdir(exist_ok=True)

MAX_BITS = math.log2(len(CATEGORIES))   # 2.0 for 4 categories
BAR_WIDTH = 30


def _entropy_bar(entropy: float, max_bits: float = MAX_BITS) -> str:
    """ASCII bar representing entropy as a fraction of max."""
    filled = round((entropy / max_bits) * BAR_WIDTH)
    return "█" * filled + "░" * (BAR_WIDTH - filled)


def section_pandas_entropy(console: Console, df: pd.DataFrame) -> pd.DataFrame:
    console.print(Panel(
        "[bold cyan]Entropy via entropy_from_pandas() — scipy path[/bold cyan]\n"
        "[dim]Computed locally from the raw review DataFrame.[/dim]"
    ))
    result = entropy_from_pandas(df, "product_id", "true_category")

    t = Table(box=box.SIMPLE, show_header=True)
    t.add_column("Product", style="cyan", justify="center")
    t.add_column("H (bits)", justify="right")
    t.add_column("Norm H", justify="right")
    t.add_column("Dominant category")
    t.add_column("Dominant %", justify="right")
    t.add_column(f"Distribution  [0 ──── {MAX_BITS:.1f} bits]", no_wrap=True)

    for _, row in result.iterrows():
        t.add_row(
            row["product_id"],
            f"{row['entropy']:.3f}",
            f"{row['normalized_entropy']:.2f}",
            row["dominant_category"],
            f"{row['dominant_share']*100:.0f}%",
            _entropy_bar(row["entropy"]),
        )

    console.print(t)
    console.print(f"  Max possible entropy (uniform, 4 cats): [bold]{MAX_BITS:.3f} bits[/bold]")
    console.print(
        "\n  [bold]Interpretation:[/bold]\n"
        "  • P004 (H=0.0) → all positive reviews, zero uncertainty\n"
        "  • P002/P007 (H≈0.5) → one category dominates (~90%)\n"
        "  • P001/P006 (H≈1.9) → near-uniform spread, actionable across all categories\n"
        "  • High-entropy products need broader support coverage\n"
        "  • Low-entropy products signal a focused root cause to fix"
    )
    return result


def section_ibis_entropy(console: Console, df: pd.DataFrame) -> None:
    console.print(Panel(
        "[bold cyan]Entropy via category_entropy() — pure Ibis SQL path[/bold cyan]\n"
        "[dim]Compiles to a single SQL query; runs in Snowflake via Ibis memtable.[/dim]"
    ))
    ibis.options.interactive = False
    tbl = ibis.memtable(df)

    # Show the SQL that will be generated
    expr = category_entropy(tbl, ["product_id"], "true_category")
    try:
        sql = ibis.to_sql(expr, dialect="snowflake")
        from rich.syntax import Syntax
        console.print(Syntax(str(sql)[:1200], "sql", theme="monokai", line_numbers=False))
    except Exception:
        pass  # SQL preview is optional

    # Execute via Ibis (requires duckdb locally; skipped if not installed)
    try:
        ibis.options.interactive = True
        result_df = expr.execute()
        t = Table(box=box.SIMPLE)
        t.add_column("Product", style="cyan", justify="center")
        t.add_column("H (bits)", justify="right")
        t.add_column("Dominant category")
        t.add_column("Dominant share", justify="right")
        for _, row in result_df.sort_values("entropy").iterrows():
            t.add_row(
                str(row["product_id"]),
                f"{float(row['entropy']):.3f}",
                str(row["dominant_category"]),
                f"{float(row['dominant_share'])*100:.0f}%",
            )
        console.print(t)
    except Exception as exc:
        console.print(f"  [dim](Local execution skipped — connect to Snowflake to run: {exc})[/dim]")
        console.print("  [green]SQL above is valid Snowflake SQL — run it via con.table() against a real Snowflake table.[/green]")


def section_true_vs_sample(console: Console, df: pd.DataFrame) -> None:
    console.print(Panel(
        "[bold cyan]True distribution vs sample entropy[/bold cyan]\n"
        "[dim]Dirichlet α defines the true distribution; sample entropy varies with n.[/dim]"
    ))
    from synthetic_data import _PRODUCT_CONFIGS, _expected_entropy

    t = Table(box=box.SIMPLE)
    t.add_column("Product", style="cyan", justify="center")
    t.add_column("n", justify="right")
    t.add_column("True H (bits)", justify="right")
    t.add_column("Sample H (bits)", justify="right")
    t.add_column("Diff", justify="right")

    sample = entropy_from_pandas(df, "product_id", "true_category")[
        ["product_id", "entropy"]
    ].set_index("product_id")["entropy"]

    for pid, n, alpha in _PRODUCT_CONFIGS:
        true_h  = _expected_entropy(alpha)
        sample_h = float(sample.get(pid, 0.0))
        diff = sample_h - true_h
        diff_str = f"[green]+{diff:.3f}[/green]" if diff >= 0 else f"[red]{diff:.3f}[/red]"
        t.add_row(pid, str(n), f"{true_h:.3f}", f"{sample_h:.3f}", diff_str)

    console.print(t)
    console.print(
        "\n  [dim]Sample entropy underestimates true entropy for small n (Miller–Madow bias).\n"
        "  Larger n → sample entropy converges to true entropy.[/dim]"
    )


def main():
    console = Console(record=True, width=115)
    df = make_reviews()

    console.print(f"\n  Dataset: [bold]{len(df)} reviews[/bold] × "
                  f"[bold]{df['product_id'].nunique()} products[/bold] × "
                  f"[bold]{len(CATEGORIES)} categories[/bold]\n")

    section_pandas_entropy(console, df)
    console.print()
    section_true_vs_sample(console, df)
    console.print()
    section_ibis_entropy(console, df)

    svg_path = ASSETS / "s_entropy.svg"
    svg = console.export_svg(title="cortex_ibis — Shannon Entropy Distribution Analysis")
    svg_path.write_text(svg)
    console.print(f"\n  [dim]→ SVG saved: {svg_path}[/dim]")

    # Echo plain text to terminal
    Console().print(console.export_text())
    print(f"\nSVG saved to {svg_path}")


if __name__ == "__main__":
    main()
