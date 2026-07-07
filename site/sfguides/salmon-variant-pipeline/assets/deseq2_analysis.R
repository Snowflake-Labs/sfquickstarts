#!/usr/bin/env Rscript
# =============================================================================
# Downstream analysis of Salmon 2.0 output
#
# Part A: Gene-level differential expression with DESeq2
# Part B: Transcript-level differential expression with fishpond/swish
#         (uses bootstrap inferential replicates from --numBootstraps)
#
# Dataset: Airway SMC, dexamethasone vs untreated (PMID: 24926665)
# =============================================================================
suppressPackageStartupMessages({
    library(tximeta)      # import quant.sf + auto tx-annotation
    library(DESeq2)
    library(fishpond)     # swish: transcript-level testing
    library(GenomicFeatures)
    library(org.Hs.eg.db)
    library(ggplot2)
    library(pheatmap)
    library(dplyr)
})

dir.create("results/downstream", showWarnings = FALSE, recursive = TRUE)

# ---------------------------------------------------------------------------
# 1. Sample metadata
# ---------------------------------------------------------------------------
samples <- read.table("samples.tsv", header = TRUE, sep = "\t",
                      stringsAsFactors = FALSE)
samples$files <- file.path("results/quant", samples$sample, "quant.sf")
samples$names <- samples$sample
stopifnot(all(file.exists(samples$files)))

# ---------------------------------------------------------------------------
# 2. Import with tximeta (reads quant.sf + inferential replicates)
#    tximeta auto-annotates transcript coordinates from the index hash.
#    Set GENCODE = TRUE because we built the index with --gencode.
# ---------------------------------------------------------------------------
se <- tximeta(samples)                          # transcript-level SummarizedExperiment
gse <- summarizeToGene(se)                      # gene-level summary

cat(sprintf("[INFO] %d transcripts / %d genes loaded\n",
            nrow(se), nrow(gse)))

# ---------------------------------------------------------------------------
# Part A: Gene-level DESeq2 (standard DE analysis)
# ---------------------------------------------------------------------------
cat("\n=== Part A: DESeq2 (gene level) ===\n")

dds <- DESeqDataSet(gse, design = ~ cell_line + condition)
dds <- DESeq(dds)

res_lfc <- lfcShrink(dds,
                     contrast = c("condition", "dexamethasone", "untreated"),
                     type = "ashr")

summary(res_lfc, alpha = 0.05)

sig <- as.data.frame(res_lfc) %>%
    filter(!is.na(padj), padj < 0.05, abs(log2FoldChange) > 1) %>%
    arrange(padj)

sig$symbol <- mapIds(org.Hs.eg.db,
                     keys    = rownames(sig),
                     column  = "SYMBOL",
                     keytype = "ENSEMBL",
                     multiVals = "first")

cat(sprintf("[INFO] Significant genes (padj<0.05, |LFC|>1): %d\n", nrow(sig)))
write.csv(as.data.frame(res_lfc),  "results/downstream/deseq2_all_genes.csv")
write.csv(sig,                     "results/downstream/deseq2_significant.csv")

# MA plot
pdf("results/downstream/ma_plot.pdf", width = 8, height = 5)
plotMA(res_lfc, main = "DESeq2 MA: dexamethasone vs untreated", ylim = c(-4, 4))
dev.off()

# Volcano
res_df <- as.data.frame(res_lfc) %>%
    mutate(sig = case_when(
        padj < 0.05 & log2FoldChange >  1 ~ "Up",
        padj < 0.05 & log2FoldChange < -1 ~ "Down",
        TRUE                               ~ "NS"
    ))

ggplot(res_df, aes(log2FoldChange, -log10(pvalue), color = sig)) +
    geom_point(alpha = 0.4, size = 0.7) +
    scale_color_manual(values = c(Up = "red3", Down = "steelblue", NS = "grey70")) +
    theme_bw(base_size = 13) +
    labs(title = "Volcano: dexamethasone vs untreated",
         x = "log2 Fold Change", y = "-log10(p-value)", color = NULL)
ggsave("results/downstream/volcano.pdf", width = 8, height = 5)

# Heatmap of top 30 DE genes
top30 <- head(sig, 30)
mat   <- assay(vst(dds))[rownames(top30), ]
rownames(mat) <- coalesce(top30$symbol, rownames(top30))
ann   <- data.frame(condition = dds$condition, row.names = colnames(mat))
pheatmap(mat, annotation_col = ann, scale = "row",
         filename = "results/downstream/heatmap_top30.pdf",
         width = 8, height = 9)

# ---------------------------------------------------------------------------
# Part B: Transcript-level testing with fishpond / swish
#         swish uses the bootstrap inferential replicates (--numBootstraps 100)
#         to account for quantification uncertainty — appropriate for isoform
#         variant analysis where transcripts share reads.
# ---------------------------------------------------------------------------
cat("\n=== Part B: swish (transcript / isoform level) ===\n")

# Label samples and scale inferential replicates
se$condition <- factor(se$condition, levels = c("untreated", "dexamethasone"))
se$cell_line <- factor(se$cell_line)

se <- scaleInfReps(se)         # normalize inferential replicates
se <- labelKeep(se)            # filter low-count transcripts
se <- se[mcols(se)$keep, ]

set.seed(42)
se <- swish(se, x = "condition", pair = "cell_line")

swish_res <- as.data.frame(mcols(se)) %>%
    arrange(qvalue) %>%
    select(gene_id, tx_name = "tx_id", log2FC, qvalue, pvalue)

sig_tx <- filter(swish_res, qvalue < 0.05)
cat(sprintf("[INFO] Significant transcripts (qvalue<0.05): %d\n", nrow(sig_tx)))

write.csv(swish_res, "results/downstream/swish_all_transcripts.csv",
          row.names = FALSE)
write.csv(sig_tx,    "results/downstream/swish_significant_transcripts.csv",
          row.names = FALSE)

# Isoform usage plot for the most significant gene
top_gene <- sig_tx$gene_id[1]
plotInfReps(se, idx = which(mcols(se)$gene_id == top_gene)[1],
            x = "condition", main = paste("Isoform:", top_gene))
dev.copy(pdf, "results/downstream/top_isoform_infreps.pdf"); dev.off()

cat("\n[DONE] All results written to results/downstream/\n")
cat("  Gene-level  : deseq2_all_genes.csv, deseq2_significant.csv\n")
cat("  Transcript  : swish_all_transcripts.csv, swish_significant_transcripts.csv\n")
cat("  Plots       : ma_plot.pdf, volcano.pdf, heatmap_top30.pdf\n")
