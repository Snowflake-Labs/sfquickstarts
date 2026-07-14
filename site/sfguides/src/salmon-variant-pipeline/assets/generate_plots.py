"""
generate_plots.py
=================
Generates example pipeline visualisation figures using synthetic data that
mirrors realistic Salmon / DESeq2 / swish output for the airway dataset
(Himes et al. 2014, PMID 24926665).

Produces (all saved to results/figures/):
  01_pipeline_dag.png         — Snakemake-style DAG
  02_ma_plot.png              — DESeq2 MA plot  (gene level)
  03_volcano_plot.png         — Volcano plot    (gene level)
  04_heatmap_top30.png        — Z-score heatmap of top 30 DE genes
  05_mapping_rates.png        — Per-sample mapping rate bar chart
  06_pca_plot.png             — PCA of VST-normalised counts
  07_swish_lfc.png            — fishpond/swish transcript-level LFC plot
  08_code_structure.png       — Annotated file-tree diagram

Each section prints the equivalent R / bash code that would produce the same
plot from real Salmon output.
"""

import os
import textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUTDIR = os.path.join(os.path.dirname(__file__), "..", "assets")
os.makedirs(OUTDIR, exist_ok=True)

RNG = np.random.default_rng(42)

SAMPLES = ["SRR1039508", "SRR1039509", "SRR1039512", "SRR1039513",
           "SRR1039516", "SRR1039517", "SRR1039520", "SRR1039521"]
CONDITIONS = ["untreated", "dexamethasone"] * 4
CELL_LINES = ["N61311"] * 2 + ["N052611"] * 2 + ["N080611"] * 2 + ["N061011"] * 2

PALETTE = {"untreated": "#4C9BE8", "dexamethasone": "#E8624C"}
RUST_COL  = "#CE422B"
CPP_COL   = "#6B6FCF"

# ── known dexamethasone-regulated genes (from Himes 2014) ──────────────────
KNOWN_UP   = ["DUSP1", "KLF15", "PER1", "ZBTB16", "CRISPLD2",
               "FKBP5",  "TSC22D3", "GLUL",   "SLC19A2", "ANGPTL4"]
KNOWN_DOWN = ["CXCL10", "CCL2",  "IL6",   "CXCL8",   "TNFSF10",
               "ICAM1",  "MMP1",  "IL1A",  "CXCL2",   "SERPINE1"]

# ═══════════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════════

def savefig(fig, name, dpi=150):
    path = os.path.join(OUTDIR, name)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"  saved → {path}")


def code_box(ax, code: str, title: str = "R code"):
    """Draw a syntax-highlighted-style code box inside an axes."""
    # Escape $ so matplotlib does not treat them as math-mode delimiters
    code_esc = code.replace("$", r"\$")
    ax.set_facecolor("#1e1e2e")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.01, 0.97, title, transform=ax.transAxes,
            color="#cdd6f4", fontsize=7, fontfamily="monospace",
            va="top", style="italic")
    ax.text(0.01, 0.89, code_esc, transform=ax.transAxes,
            color="#a6e3a1", fontsize=6.2, fontfamily="monospace",
            va="top", linespacing=1.6,
            wrap=False, clip_on=True)


# ═══════════════════════════════════════════════════════════════════════════
# 01 — Pipeline DAG
# ═══════════════════════════════════════════════════════════════════════════

def plot_dag():
    print("[01] Pipeline DAG")

    nodes = [
        ("download_transcriptome",  0.15, 0.92, "#74c7ec"),
        ("download_genome",         0.50, 0.92, "#74c7ec"),
        ("download_gtf",            0.85, 0.92, "#74c7ec"),
        ("make_gentrome",           0.32, 0.73, "#89dceb"),
        ("salmon_index\n(rust / cpp)", 0.32, 0.54, "#f38ba8"),
        ("download_reads",          0.75, 0.54, "#74c7ec"),
        ("salmon_quant ×8",         0.54, 0.35, "#a6e3a1"),
        ("multiqc",                 0.54, 0.16, "#fab387"),
    ]
    edges = [
        (0, 3), (1, 3), (3, 4), (4, 5), (2, 6),
        (4, 6), (5, 6), (6, 7),
    ]
    # fix: download_reads → salmon_quant
    edges = [(0,3),(1,3),(3,4),(4,6),(5,6),(6,7),(2,6)]

    fig, ax = plt.subplots(figsize=(8, 6), facecolor="#181825")
    ax.set_facecolor("#181825")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.set_title("Snakemake DAG — Salmon Variant Pipeline",
                 color="#cdd6f4", fontsize=11, pad=10)

    pos = {n[0]: (n[1], n[2]) for n in nodes}

    for src_i, dst_i in edges:
        sx, sy = nodes[src_i][1], nodes[src_i][2]
        dx, dy = nodes[dst_i][1], nodes[dst_i][2]
        ax.annotate("", xy=(dx, dy+0.045), xytext=(sx, sy-0.045),
                    arrowprops=dict(arrowstyle="-|>", color="#585b70",
                                   lw=1.4, mutation_scale=12))

    for label, x, y, col in nodes:
        bbox = FancyBboxPatch((x-0.14, y-0.040), 0.28, 0.080,
                              boxstyle="round,pad=0.01",
                              facecolor=col, edgecolor="#313244", linewidth=1.2)
        ax.add_patch(bbox)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=7.5, color="#1e1e2e", fontweight="bold",
                fontfamily="monospace")

    # version callout
    ax.text(0.02, 0.08,
            "rust → results/index_rust/  results/quant_rust/\n"
            "cpp  → results/index_cpp/   results/quant_cpp/",
            color="#cba6f7", fontsize=7, fontfamily="monospace",
            transform=ax.transAxes,
            bbox=dict(facecolor="#313244", edgecolor="#585b70", boxstyle="round,pad=0.4"))

    savefig(fig, "01_pipeline_dag.png")


# ═══════════════════════════════════════════════════════════════════════════
# 02 — MA Plot
# ═══════════════════════════════════════════════════════════════════════════

def make_deseq2_results(n=18000):
    baseMean = np.exp(RNG.normal(4, 2, n)).clip(1)
    lfc = RNG.normal(0, 0.4, n)
    # add DE signal
    n_up = 120; n_dn = 95
    lfc[:n_up] += RNG.uniform(1.2, 3.5, n_up)
    lfc[n_up:n_up+n_dn] -= RNG.uniform(1.2, 3.0, n_dn)
    se = 0.3 / np.sqrt(np.log1p(baseMean) / 5 + 0.1)
    pval = 2 * (1 - 0.5 * (1 + np.sign(lfc) *
               (1 - np.exp(-np.abs(lfc) / se))))
    pval = np.clip(np.abs(RNG.normal(pval, 0.15)), 1e-50, 1)
    padj = np.minimum(pval * n / np.maximum(
              np.argsort(np.argsort(pval)) + 1, 1), 1)
    genes = [f"ENSG{str(i).zfill(11)}" for i in range(n)]
    df = pd.DataFrame(dict(gene=genes, baseMean=baseMean,
                           log2FC=lfc, pvalue=pval, padj=padj))
    # label known genes
    for i, g in enumerate(KNOWN_UP):
        df.loc[i, "gene"] = g
        df.loc[i, "log2FC"] = RNG.uniform(1.5, 3.0)
        df.loc[i, "padj"] = RNG.uniform(1e-10, 0.01)
    for i, g in enumerate(KNOWN_DOWN):
        df.loc[n_up+i, "gene"] = g
        df.loc[n_up+i, "log2FC"] = -RNG.uniform(1.4, 2.8)
        df.loc[n_up+i, "padj"] = RNG.uniform(1e-8, 0.01)
    df["sig"] = "NS"
    df.loc[(df.padj < 0.05) & (df.log2FC > 1),  "sig"] = "Up"
    df.loc[(df.padj < 0.05) & (df.log2FC < -1), "sig"] = "Down"
    return df


def plot_ma(df):
    print("[02] MA plot")
    fig, (ax, cax) = plt.subplots(1, 2, figsize=(9, 4.5),
                                   gridspec_kw={"width_ratios": [3, 1.8]},
                                   facecolor="#1e1e2e")
    fig.subplots_adjust(wspace=0.35)
    ax.set_facecolor("#181825")

    col_map = {"NS": "#585b70", "Up": "#f38ba8", "Down": "#89b4fa"}
    for sig, grp in df.groupby("sig"):
        ax.scatter(np.log2(grp.baseMean + 1), grp.log2FC,
                   c=col_map[sig], s=3 if sig == "NS" else 6,
                   alpha=0.5 if sig == "NS" else 0.85,
                   rasterized=True, label=sig, zorder=3 if sig != "NS" else 1)

    # label known genes
    for _, row in df[df.gene.isin(KNOWN_UP[:5] + KNOWN_DOWN[:5])].iterrows():
        ax.annotate(row.gene, (np.log2(row.baseMean+1), row.log2FC),
                    fontsize=6, color="#cdd6f4",
                    xytext=(6, 0), textcoords="offset points")

    ax.axhline(0, color="#cba6f7", lw=0.8, ls="--")
    ax.axhline(1, color="#f38ba8", lw=0.6, ls=":")
    ax.axhline(-1, color="#89b4fa", lw=0.6, ls=":")
    ax.set_xlabel("log2(mean normalised count)", color="#cdd6f4")
    ax.set_ylabel("log2 Fold Change  (dex / untreated)", color="#cdd6f4")
    ax.set_title("DESeq2 MA Plot — Gene Level", color="#cdd6f4", fontsize=10)
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    ax.tick_params(colors="#cdd6f4")
    n_up  = (df.sig == "Up").sum()
    n_dn  = (df.sig == "Down").sum()
    ax.legend(handles=[mpatches.Patch(color=col_map[s], label=f"{s} (n={n})")
                        for s, n in [("Up", n_up), ("Down", n_dn), ("NS", len(df)-n_up-n_dn)]],
              facecolor="#313244", edgecolor="#585b70", labelcolor="#cdd6f4", fontsize=8)

    r_code = textwrap.dedent("""\
        # R — DESeq2 MA plot
        library(DESeq2); library(tximeta)

        se  <- tximeta(coldata)      # import quant.sf
        gse <- summarizeToGene(se)
        dds <- DESeqDataSet(gse,
          design = ~ cell_line + condition)
        dds <- DESeq(dds)

        res <- lfcShrink(dds,
          contrast = c("condition",
            "dexamethasone","untreated"),
          type = "ashr")

        plotMA(res, ylim = c(-4,4),
          main = "dex vs untreated")
    """)
    code_box(cax, r_code, "R code (DESeq2 MA)")
    savefig(fig, "02_ma_plot.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 03 — Volcano Plot
# ═══════════════════════════════════════════════════════════════════════════

def plot_volcano(df):
    print("[03] Volcano plot")
    fig, (ax, cax) = plt.subplots(1, 2, figsize=(9, 4.5),
                                   gridspec_kw={"width_ratios": [3, 1.8]},
                                   facecolor="#1e1e2e")
    ax.set_facecolor("#181825")
    col_map = {"NS": "#585b70", "Up": "#f38ba8", "Down": "#89b4fa"}
    for sig, grp in df.groupby("sig"):
        ax.scatter(grp.log2FC, -np.log10(grp.pvalue.clip(1e-40)),
                   c=col_map[sig], s=3 if sig == "NS" else 6,
                   alpha=0.5 if sig == "NS" else 0.85,
                   rasterized=True, zorder=3 if sig != "NS" else 1)

    for _, row in df[df.gene.isin(KNOWN_UP[:5] + KNOWN_DOWN[:5])].iterrows():
        ax.annotate(row.gene, (row.log2FC, -np.log10(max(row.pvalue, 1e-40))),
                    fontsize=6, color="#cdd6f4",
                    xytext=(5, 2), textcoords="offset points")

    ax.axvline(1,  color="#f38ba8", lw=0.7, ls=":")
    ax.axvline(-1, color="#89b4fa", lw=0.7, ls=":")
    ax.axhline(-np.log10(0.05), color="#a6e3a1", lw=0.7, ls="--", label="padj=0.05")
    ax.set_xlabel("log2 Fold Change", color="#cdd6f4")
    ax.set_ylabel("-log10(p-value)", color="#cdd6f4")
    ax.set_title("Volcano Plot — Gene Level  (dex vs untreated)", color="#cdd6f4", fontsize=10)
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    ax.tick_params(colors="#cdd6f4")
    n_up = (df.sig=="Up").sum(); n_dn = (df.sig=="Down").sum()
    ax.legend(handles=[
        mpatches.Patch(color="#f38ba8", label=f"Up-regulated ({n_up})"),
        mpatches.Patch(color="#89b4fa", label=f"Down-regulated ({n_dn})"),
        mpatches.Patch(color="#a6e3a1", label="padj = 0.05 threshold"),
    ], facecolor="#313244", edgecolor="#585b70", labelcolor="#cdd6f4", fontsize=8)

    r_code = textwrap.dedent("""\
        # R — Volcano plot
        library(ggplot2)

        res_df <- as.data.frame(res) |>
          dplyr::mutate(sig = dplyr::case_when(
            padj < 0.05 & log2FC >  1 ~ "Up",
            padj < 0.05 & log2FC < -1 ~ "Down",
            TRUE ~ "NS"))

        ggplot(res_df,
          aes(log2FC, -log10(pvalue),
              color = sig)) +
          geom_point(alpha=0.4, size=0.8) +
          scale_color_manual(values=c(
            Up="red3", Down="steelblue",
            NS="grey70")) +
          theme_bw()
    """)
    code_box(cax, r_code, "R code (volcano)")
    savefig(fig, "03_volcano_plot.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 04 — Heatmap top 30
# ═══════════════════════════════════════════════════════════════════════════

def plot_heatmap(df):
    print("[04] Heatmap top 30 DE genes")
    sig = df[df.sig != "NS"].nsmallest(30, "padj").copy()
    sig["label"] = sig.gene.apply(lambda g: g if g[:4] != "ENSG" else g[:12])

    # simulate VST expression matrix
    n = len(sig)
    mat = np.zeros((n, 8))
    for i, (_, row) in enumerate(sig.iterrows()):
        base = RNG.normal(8, 1.5)
        untreated_vals = RNG.normal(base, 0.4, 4)
        treated_vals   = RNG.normal(base + row.log2FC, 0.4, 4)
        mat[i, [0,2,4,6]] = untreated_vals
        mat[i, [1,3,5,7]] = treated_vals
    # z-score per gene
    mat = (mat - mat.mean(axis=1, keepdims=True)) / (mat.std(axis=1, keepdims=True) + 1e-9)

    cmap = LinearSegmentedColormap.from_list("rdbu",
        ["#89b4fa","#1e1e2e","#f38ba8"], N=256)

    col_labels = [f"{s}\n{c[:4]}" for s, c in zip(
        ["U","D","U","D","U","D","U","D"],
        ["N613","N613","N052","N052","N080","N080","N061","N061"])]
    col_colors = [PALETTE[c] for c in CONDITIONS]

    fig = plt.figure(figsize=(11, 7), facecolor="#1e1e2e")
    # 3 columns: heatmap | dedicated colorbar | code box
    gs  = gridspec.GridSpec(1, 3, width_ratios=[2.2, 0.08, 1.5], wspace=0.35)
    ax   = fig.add_subplot(gs[0])   # heatmap
    cbax = fig.add_subplot(gs[1])   # colorbar — own column, well clear of title
    cax  = fig.add_subplot(gs[2])   # R code box

    im = ax.imshow(mat, aspect="auto", cmap=cmap, vmin=-2.5, vmax=2.5)
    ax.set_xticks(range(8)); ax.set_xticklabels(col_labels, fontsize=6.5, color="#cdd6f4")
    ax.set_yticks(range(n));  ax.set_yticklabels(sig.label, fontsize=6.5, color="#cdd6f4")
    for j, cc in enumerate(col_colors):
        ax.add_patch(plt.Rectangle((j-0.5, -1.6), 1, 0.6,
                                   color=cc, clip_on=False, zorder=2))
    ax.set_facecolor("#181825")
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    # pad=22 pushes the title above the annotation colour bars
    ax.set_title("Top 30 DE Genes — Z-score (VST)", color="#cdd6f4", fontsize=9, pad=22)

    # Colorbar in its own axes — no overlap with heatmap title
    cb = fig.colorbar(im, cax=cbax)
    cb.set_label("Z-score", color="#cdd6f4", fontsize=7)
    cbax.yaxis.set_tick_params(color="#cdd6f4")
    plt.setp(cbax.yaxis.get_ticklabels(), color="#cdd6f4", fontsize=6)
    cbax.set_facecolor("#181825")

    r_code = textwrap.dedent("""\
        # R — Heatmap (pheatmap)
        library(pheatmap); library(DESeq2)

        vsd <- vst(dds, blind=FALSE)
        top30 <- head(sig_genes, 30)
        mat   <- assay(vsd)[
          rownames(top30), ]
        rownames(mat) <- coalesce(
          top30$symbol,
          rownames(top30))

        ann <- data.frame(
          condition = dds$condition,
          row.names = colnames(mat))

        pheatmap(mat,
          annotation_col = ann,
          scale = "row",
          color = colorRampPalette(
            c("navy","white","red3")
          )(100))
    """)
    code_box(cax, r_code, "R code (pheatmap)")
    savefig(fig, "04_heatmap_top30.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 05 — Mapping Rate Bar Chart
# ═══════════════════════════════════════════════════════════════════════════

def plot_mapping_rates():
    print("[05] Mapping rates")
    rust_rates = RNG.uniform(87.2, 92.5, 8)
    cpp_rates  = RNG.uniform(85.0, 90.8, 8)

    fig, (ax, cax) = plt.subplots(1, 2, figsize=(10, 4.2),
                                   gridspec_kw={"width_ratios": [3, 1.5]},
                                   facecolor="#1e1e2e")
    ax.set_facecolor("#181825")
    x = np.arange(8); w = 0.38
    ax.bar(x - w/2, rust_rates, w, label="Salmon 2.0 (Rust)", color=RUST_COL, alpha=0.85)
    ax.bar(x + w/2, cpp_rates,  w, label="Salmon 1.12.0 (C++)", color=CPP_COL, alpha=0.85)
    ax.set_ylim(80, 97)
    ax.set_xticks(x); ax.set_xticklabels(
        [f"{s}\n({c[:3]})" for s, c in zip(SAMPLES, CONDITIONS)],
        fontsize=6.5, color="#cdd6f4")
    ax.set_ylabel("Mapping rate (%)", color="#cdd6f4")
    ax.set_title("Salmon Mapping Rates — Rust vs C++  (simulated)", color="#cdd6f4", fontsize=10)
    ax.legend(facecolor="#313244", edgecolor="#585b70", labelcolor="#cdd6f4", fontsize=8)
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    ax.tick_params(colors="#cdd6f4")
    ax.yaxis.grid(True, color="#313244", linewidth=0.5)

    bash_code = textwrap.dedent("""\
        # bash — extract mapping rates
        for LOG in results/logs/*_quant_rust.log; do
          SAMPLE=$(basename $LOG _quant_rust.log)
          RATE=$(grep "Mapping rate" $LOG \\
                 | awk '{print $NF}')
          echo "$SAMPLE $RATE"
        done

        # Rust: selective alignment is
        # the default in 2.0.
        # C++:  requires --validateMappings
        # to activate selective alignment.
        # Both use decoy-aware index for
        # cleaner mapping rates.
    """)
    code_box(cax, bash_code, "bash code")
    savefig(fig, "05_mapping_rates.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 06 — PCA plot
# ═══════════════════════════════════════════════════════════════════════════

def plot_pca():
    print("[06] PCA plot")
    # simulate VST PC1/PC2 scores (condition separates on PC1, cell line on PC2)
    pc1 = np.array([-8, 8, -7, 9, -8.5, 7.5, -7.8, 8.2]) + RNG.normal(0, 0.8, 8)
    pc2 = np.array([-4,-4,  4, 4,  0,    0,  -2,  -2])    + RNG.normal(0, 0.8, 8)

    fig, (ax, cax) = plt.subplots(1, 2, figsize=(9, 4.5),
                                   gridspec_kw={"width_ratios": [2.5, 1.8]},
                                   facecolor="#1e1e2e")
    ax.set_facecolor("#181825")
    markers = {"N61311": "o", "N052611": "s", "N080611": "^", "N061011": "D"}
    for i, (s, cond, cl) in enumerate(zip(SAMPLES, CONDITIONS, CELL_LINES)):
        ax.scatter(pc1[i], pc2[i], s=90,
                   c=PALETTE[cond], marker=markers[cl],
                   edgecolors="#cdd6f4", linewidths=0.6, zorder=4)
        ax.annotate(s, (pc1[i], pc2[i]), fontsize=5.5, color="#cdd6f4",
                    xytext=(5, 4), textcoords="offset points")

    ax.set_xlabel("PC1  (var explained ≈ 62%)", color="#cdd6f4")
    ax.set_ylabel("PC2  (var explained ≈ 18%)", color="#cdd6f4")
    ax.set_title("PCA — VST-normalised counts", color="#cdd6f4", fontsize=10)
    ax.axhline(0, color="#585b70", lw=0.5); ax.axvline(0, color="#585b70", lw=0.5)
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    ax.tick_params(colors="#cdd6f4")
    handles = [mpatches.Patch(color=PALETTE[c], label=c) for c in ["untreated","dexamethasone"]]
    handles += [plt.Line2D([0],[0], marker=m, color="w",
                           markerfacecolor="#cdd6f4", markersize=7, label=cl)
                for cl, m in markers.items()]
    ax.legend(handles=handles, facecolor="#313244", edgecolor="#585b70",
              labelcolor="#cdd6f4", fontsize=7, ncol=2)

    r_code = textwrap.dedent("""\
        # R — PCA plot
        library(DESeq2)

        vsd <- vst(dds, blind=FALSE)
        pcaData <- plotPCA(vsd,
          intgroup = c("condition",
                       "cell_line"),
          returnData = TRUE)
        pvar <- round(100 *
          attr(pcaData,"percentVar"))

        ggplot(pcaData,
          aes(PC1, PC2,
            color=condition,
            shape=cell_line)) +
          geom_point(size=3) +
          xlab(paste0("PC1: ",pvar[1],"%")) +
          ylab(paste0("PC2: ",pvar[2],"%"))
    """)
    code_box(cax, r_code, "R code (PCA)")
    savefig(fig, "06_pca_plot.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 07 — Swish transcript-level LFC
# ═══════════════════════════════════════════════════════════════════════════

def plot_swish():
    print("[07] Swish transcript-level LFC")
    n_tx = 5000
    lfc_tx = RNG.normal(0, 0.5, n_tx)
    qval   = np.clip(RNG.exponential(0.3, n_tx), 0, 1)
    n_sig  = 180
    lfc_tx[:n_sig] += RNG.choice([-1,1], n_sig) * RNG.uniform(1, 2.5, n_sig)
    qval[:n_sig] = RNG.uniform(1e-8, 0.04, n_sig)
    sig_mask = qval < 0.05

    fig, (ax, cax) = plt.subplots(1, 2, figsize=(9, 4.5),
                                   gridspec_kw={"width_ratios": [3, 1.8]},
                                   facecolor="#1e1e2e")
    ax.set_facecolor("#181825")
    ax.scatter(lfc_tx[~sig_mask], -np.log10(qval[~sig_mask]+1e-40),
               s=2, c="#585b70", alpha=0.4, rasterized=True, label="NS")
    ax.scatter(lfc_tx[sig_mask],  -np.log10(qval[sig_mask]+1e-40),
               s=5, c="#cba6f7", alpha=0.9, rasterized=True,
               label=f"Sig. transcripts (n={sig_mask.sum()})")
    ax.axvline(1,  color="#f38ba8", lw=0.7, ls=":"); ax.axvline(-1, color="#89b4fa", lw=0.7, ls=":")
    ax.axhline(-np.log10(0.05), color="#a6e3a1", lw=0.7, ls="--", label="q=0.05")
    ax.set_xlabel("log2 Fold Change (transcript level)", color="#cdd6f4")
    ax.set_ylabel("-log10(q-value)", color="#cdd6f4")
    ax.set_title("fishpond / swish — Transcript Isoform Variants", color="#cdd6f4", fontsize=10)
    for spine in ax.spines.values(): spine.set_edgecolor("#585b70")
    ax.tick_params(colors="#cdd6f4")
    ax.legend(facecolor="#313244", edgecolor="#585b70", labelcolor="#cdd6f4", fontsize=8)

    r_code = textwrap.dedent("""\
        # R — fishpond/swish
        library(fishpond)

        # se = transcript-level SE
        # from tximeta (includes
        # bootstrap inferential reps)
        se$condition <- factor(
          se$condition,
          levels=c("untreated",
                   "dexamethasone"))

        se <- scaleInfReps(se)
        se <- labelKeep(se)
        se <- se[mcols(se)$keep, ]

        set.seed(42)
        se <- swish(se,
          x = "condition",
          pair = "cell_line")

        # q-value < 0.05 → isoform
        # variant is DE
    """)
    code_box(cax, r_code, "R code (swish)")
    savefig(fig, "07_swish_lfc.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 08 — Code structure diagram
# ═══════════════════════════════════════════════════════════════════════════

def plot_code_structure():
    print("[08] Code structure")
    fig, ax = plt.subplots(figsize=(10, 6), facecolor="#1e1e2e")
    ax.set_facecolor("#1e1e2e"); ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_title("salmon-variant-pipeline — File Structure & Data Flow",
                 color="#cdd6f4", fontsize=11, pad=10)

    tree = [
        (0.3, 9.3,  "📁 salmon-variant-pipeline/",        "#cba6f7", 11),
        (0.8, 8.7,  "├── pipeline.sh",                    "#a6e3a1",  9),
        (0.8, 8.2,  "│     SALMON_VERSION=rust|cpp",       "#6c7086",  8),
        (0.8, 7.7,  "├── Snakefile",                       "#a6e3a1",  9),
        (0.8, 7.2,  "│     salmon_version: rust|cpp",      "#6c7086",  8),
        (0.8, 6.7,  "├── config.yaml",                     "#fab387",  9),
        (0.8, 6.2,  "├── samples.tsv",                     "#fab387",  9),
        (0.8, 5.7,  "├── envs/salmon.yaml",                "#74c7ec",  9),
        (0.8, 5.2,  "└── scripts/",                        "#cba6f7",  9),
        (1.3, 4.7,  "    ├── deseq2_analysis.R",           "#f38ba8",  9),
        (1.3, 4.2,  "    └── generate_plots.py",           "#f38ba8",  9),
    ]
    results = [
        (5.5, 9.3,  "📁 results/",                         "#cba6f7", 11),
        (6.0, 8.7,  "├── references/   (shared)",          "#74c7ec",  8.5),
        (6.0, 8.2,  "│     transcriptome.fa  genome.fa",   "#6c7086",  7.5),
        (6.0, 7.7,  "├── index_rust/   ← Rust 2.0 only",  "#f38ba8",  8.5),
        (6.0, 7.2,  "├── index_cpp/    ← C++ 1.12 only",  "#89b4fa",  8.5),
        (6.0, 6.7,  "│     ⚠ formats NOT interchangeable", "#eba0ac",  7.5),
        (6.0, 6.2,  "├── reads/        (shared SRA)",      "#74c7ec",  8.5),
        (6.0, 5.7,  "├── quant_rust/   ← quant.sf (Rust)", "#f38ba8",  8.5),
        (6.0, 5.2,  "├── quant_cpp/    ← quant.sf (C++)",  "#89b4fa",  8.5),
        (6.0, 4.7,  "└── downstream/   (R analysis)",      "#a6e3a1",  8.5),
        (6.5, 4.2,  "    deseq2_*.csv  swish_*.csv",       "#6c7086",  7.5),
        (6.5, 3.7,  "    *.pdf  figures/*.png",             "#6c7086",  7.5),
    ]
    for x, y, txt, col, fs in tree + results:
        ax.text(x, y, txt, color=col, fontsize=fs,
                fontfamily="monospace", va="center")

    # version comparison callout
    for bx, bc, label, fc in [(0.2, 1.6, "Rust 2.0", RUST_COL), (5.1, 1.6, "C++ 1.12.0", CPP_COL)]:
        rect = FancyBboxPatch((bx, 0.6), 4.5, 2.2, boxstyle="round,pad=0.15",
                               facecolor="#181825", edgecolor=fc, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(bx+2.25, 2.55, label, ha="center", color=fc,
                fontsize=9, fontweight="bold", fontfamily="monospace")
        lines = ([
            "Binary  : prebuilt Rust (no deps)",
            "Install : curl …installer.sh | sh",
            "Selec.aln: ON by default",
            "--validateMappings: no-op (ignored)",
            "--sketch: NEW (faster pseudoaln)",
            "alevin  : removed → use alevin-fry",
        ] if "Rust" in label else [
            "Binary  : conda install salmon-cpp",
            "Install : conda -c bioconda salmon-cpp",
            "Selec.aln: OFF by default",
            "--validateMappings: required flag",
            "--mimicBT2: available",
            "alevin  : available",
        ])
        for li, line in enumerate(lines):
            ax.text(bx+0.2, 2.15 - li*0.27, line,
                    color="#cdd6f4", fontsize=7, fontfamily="monospace")

    # Updated tree now includes cortex_ai.py skill
    results_updated = [
        (5.5, 9.3,  "📁 results/",                         "#cba6f7", 11),
        (6.0, 8.7,  "├── references/   (shared)",          "#74c7ec",  8.5),
        (6.0, 8.2,  "│     transcriptome.fa  genome.fa",   "#6c7086",  7.5),
        (6.0, 7.7,  "├── index_rust/   ← Rust 2.0 only",  "#f38ba8",  8.5),
        (6.0, 7.2,  "├── index_cpp/    ← C++ 1.12 only",  "#89b4fa",  8.5),
        (6.0, 6.7,  "│     ⚠ NOT interchangeable",         "#eba0ac",  7.5),
        (6.0, 6.2,  "├── reads/        (shared SRA)",      "#74c7ec",  8.5),
        (6.0, 5.7,  "├── quant_rust/   quant.sf (Rust)",   "#f38ba8",  8.5),
        (6.0, 5.2,  "├── quant_cpp/    quant.sf (C++)",    "#89b4fa",  8.5),
        (6.0, 4.7,  "└── downstream/   (R + Cortex AI)",   "#a6e3a1",  8.5),
        (6.5, 4.2,  "    deseq2_*.csv  swish_*.csv",       "#6c7086",  7.5),
        (6.5, 3.7,  "    cortex_analysis_*_*.md",          "#cba6f7",  7.5),
    ]
    for x, y, txt, col, fs in results_updated:
        ax.text(x, y, txt, color=col, fontsize=fs,
                fontfamily="monospace", va="center")

    savefig(fig, "08_code_structure.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# 09 — Cortex REST API Integration
# ═══════════════════════════════════════════════════════════════════════════

def plot_cortex_api():
    print("[09] Cortex REST API integration")
    fig = plt.figure(figsize=(13, 7), facecolor="#1e1e2e")
    gs  = gridspec.GridSpec(1, 2, width_ratios=[1.6, 1.4], wspace=0.08)
    ax_left  = fig.add_subplot(gs[0])
    ax_right = fig.add_subplot(gs[1])
    for ax in (ax_left, ax_right):
        ax.set_facecolor("#181825"); ax.axis("off")
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

    fig.suptitle("Cortex REST API Integration — salmon-cortex-ai skill",
                 color="#cdd6f4", fontsize=11, y=0.97)

    # ── Left panel: 3 endpoints ──────────────────────────────────────────
    ax_left.text(0.03, 0.93, "Three API endpoints  (all → Bearer PAT from config.toml)",
                 color="#cba6f7", fontsize=8.5, fontweight="bold", va="top")
    ax_left.text(0.03, 0.86,
                 "X-Snowflake-Authorization-Token-Type: PROGRAMMATIC_ACCESS_TOKEN",
                 color="#fab387", fontsize=7, fontfamily="monospace", va="top")

    endpoints = [
        ("chat",      "#a6e3a1", "/api/v2/cortex/v1/chat/completions",
         "OpenAI-compat · all models · openai SDK",
         ["from openai import OpenAI",
          "client = OpenAI(api_key=PAT,",
          "  base_url=BASE+'/api/v2/cortex/v1')",
          "resp = client.chat.completions.create(",
          "  model='claude-sonnet-4-6',",
          "  messages=[...], stream=True)"]),
        ("messages",  "#89b4fa", "/api/v2/cortex/anthropic/v1/messages",
         "Anthropic-compat · Claude only · anthropic SDK",
         ["from anthropic import Anthropic",
          "client = Anthropic(",
          "  base_url=BASE+'/api/v2/cortex/anthropic',",
          "  auth_token=PAT,",
          "  default_headers={TOKEN_HEADER})",
          "resp = client.messages.create(...)"]),
        ("inference", "#f38ba8", "/api/v2/cortex/inference:complete",
         "Legacy · tools support · raw SSE stream",
         ["# raw requests + SSE parsing",
          "r = requests.post(URL,",
          "  headers={AUTH + TOKEN_HEADER},",
          "  json={model, messages, tools})",
          "# parse data: lines for",
          "# finish_reason / tool_use deltas"]),
    ]
    y0 = 0.77
    for name, col, path, desc, code in endpoints:
        rect = FancyBboxPatch((0.02, y0-0.175), 0.95, 0.185,
                              boxstyle="round,pad=0.01",
                              facecolor="#1e1e2e", edgecolor=col, linewidth=1.3)
        ax_left.add_patch(rect)
        ax_left.text(0.05, y0-0.01, f"--api {name}", color=col,
                     fontsize=8, fontweight="bold", fontfamily="monospace", va="top")
        ax_left.text(0.25, y0-0.01, path, color="#cdd6f4",
                     fontsize=7, fontfamily="monospace", va="top")
        ax_left.text(0.05, y0-0.055, desc, color="#6c7086",
                     fontsize=6.5, va="top")
        for li, line in enumerate(code):
            ax_left.text(0.07, y0-0.085 - li*0.018, line,
                         color="#a6e3a1", fontsize=6, fontfamily="monospace", va="top")
        y0 -= 0.215

    # ── Right panel: 5 analysis modes ───────────────────────────────────
    ax_right.text(0.04, 0.93, "Five analysis modes  (cortex_ai.py)",
                  color="#cba6f7", fontsize=8.5, fontweight="bold", va="top")

    modes = [
        ("summarize",     "#a6e3a1",
         "Top DE genes → biological summary",
         "deseq2_significant.csv"),
        ("explain",       "#89dceb",
         "Single gene biology + GC context",
         "deseq2_all_genes.csv  --gene DUSP1"),
        ("interpret-qc",  "#fab387",
         "Mapping rates QA + Rust vs C++ diff",
         "logs/*_quant_*.log"),
        ("compare",       "#f38ba8",
         "Spearman corr + divergent transcripts",
         "quant_rust/ + quant_cpp/"),
        ("swish",         "#cba6f7",
         "Isoform switching + DTU analysis",
         "swish_significant_transcripts.csv"),
    ]
    y0 = 0.82
    for mode, col, desc, src in modes:
        ax_right.text(0.04, y0, f"--mode {mode}", color=col,
                      fontsize=8, fontweight="bold", fontfamily="monospace", va="top")
        ax_right.text(0.04, y0-0.038, desc, color="#cdd6f4", fontsize=7, va="top")
        ax_right.text(0.04, y0-0.068, src,  color="#6c7086",
                      fontsize=6.5, fontfamily="monospace", va="top")
        ax_right.axhline(y0-0.092, color="#313244", linewidth=0.5, xmin=0.04, xmax=0.96)
        y0 -= 0.12

    # Auth callout
    auth_box = FancyBboxPatch((0.04, 0.04), 0.92, 0.17,
                              boxstyle="round,pad=0.02",
                              facecolor="#313244", edgecolor="#fab387", linewidth=1.2)
    ax_right.add_patch(auth_box)
    ax_right.text(0.07, 0.20, "Auth  (zero extra setup)",
                  color="#fab387", fontsize=7.5, fontweight="bold", va="top")
    auth_lines = [
        "PAT  ← ~/.snowflake/config.toml",
        "      connections.myaccount.password",
        "Header: X-Snowflake-Authorization-Token-Type:",
        "        PROGRAMMATIC_ACCESS_TOKEN",
    ]
    for li, line in enumerate(auth_lines):
        ax_right.text(0.07, 0.170 - li*0.026, line,
                      color="#cdd6f4", fontsize=6.5, fontfamily="monospace", va="top")

    savefig(fig, "09_cortex_api.png", dpi=160)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Writing figures to {OUTDIR}/")
    df = make_deseq2_results()
    plot_dag()
    plot_ma(df)
    plot_volcano(df)
    plot_heatmap(df)
    plot_mapping_rates()
    plot_pca()
    plot_swish()
    plot_code_structure()
    plot_cortex_api()
    print("\nDone. All 9 figures generated.")
