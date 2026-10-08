#!/usr/bin/env bash
# =============================================================================
# Salmon RNA-seq Variant (Isoform) Quantification — bash pipeline
#
# Dataset : Airway SMC cells, dexamethasone vs untreated
#           PMID 24926665 | SRA project PRJNA265491
# Ref     : GENCODE v44 (GRCh38)
#
# Supports both:
#   SALMON_VERSION=rust  → Salmon 2.0 (Rust rewrite, default)
#                          single portable binary, selective alignment is default
#   SALMON_VERSION=cpp   → Salmon 1.12.0 (final C++ release, conda: salmon-cpp)
#                          index format differs — indices are NOT interchangeable
#
# Usage   : THREADS=16 bash pipeline.sh
#           SALMON_VERSION=cpp THREADS=16 bash pipeline.sh
# =============================================================================
set -euo pipefail

THREADS=${THREADS:-8}
OUTDIR=${OUTDIR:-results}
SALMON_VERSION=${SALMON_VERSION:-rust}   # "rust" or "cpp"
GENCODE_VER="44"
TXOME_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_${GENCODE_VER}/gencode.v${GENCODE_VER}.transcripts.fa.gz"
GENOME_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_${GENCODE_VER}/GRCh38.primary_assembly.genome.fa.gz"
GTF_URL="https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_${GENCODE_VER}/gencode.v${GENCODE_VER}.annotation.gtf.gz"

# Paired-end airway samples (4 cell lines × 2 conditions)
declare -A CONDITION=(
    [SRR1039508]=untreated    [SRR1039509]=dexamethasone
    [SRR1039512]=untreated    [SRR1039513]=dexamethasone
    [SRR1039516]=untreated    [SRR1039517]=dexamethasone
    [SRR1039520]=untreated    [SRR1039521]=dexamethasone
)

REF="$OUTDIR/references"
# Each version has its own index directory — formats are NOT interchangeable
IDX="$OUTDIR/index_${SALMON_VERSION}"
READS="$OUTDIR/reads"
QUANT="$OUTDIR/quant_${SALMON_VERSION}"
LOGS="$OUTDIR/logs"

mkdir -p "$REF" "$IDX" "$READS" "$QUANT" "$LOGS"

log() { echo "[$(date '+%H:%M:%S')] [$SALMON_VERSION] $*"; }

# ---------------------------------------------------------------------------
# 1. Install / locate Salmon
#    rust → prebuilt binary from GitHub releases (no compiler needed)
#    cpp  → salmon-cpp conda package (final C++ release, 1.12.0)
# ---------------------------------------------------------------------------
install_salmon() {
    case "$SALMON_VERSION" in
      rust)
        if command -v salmon &>/dev/null && salmon --version 2>&1 | grep -q "^salmon 2"; then
            log "Salmon 2.x already installed: $(salmon --version 2>&1)"
            return
        fi
        log "Installing Salmon 2.0 (Rust)..."
        curl --proto '=https' --tlsv1.2 -LsSf \
            https://github.com/COMBINE-lab/salmon/releases/latest/download/salmon-cli-installer.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        ;;
      cpp)
        if command -v salmon &>/dev/null && salmon --version 2>&1 | grep -q "^salmon 1"; then
            log "Salmon 1.x already installed: $(salmon --version 2>&1)"
            return
        fi
        log "Installing Salmon 1.12.0 (C++) via conda..."
        # salmon-cpp is the conda package for the final C++ release
        conda install -y -c bioconda -c conda-forge salmon-cpp
        ;;
      *)
        echo "ERROR: SALMON_VERSION must be 'rust' or 'cpp' (got: $SALMON_VERSION)" >&2
        exit 1
        ;;
    esac
    log "Installed: $(salmon --version 2>&1)"
}

# ---------------------------------------------------------------------------
# 2. Download GENCODE v44 reference files
# ---------------------------------------------------------------------------
download_references() {
    log "Downloading GENCODE v${GENCODE_VER} transcriptome..."
    [[ -f "$REF/transcriptome.fa" ]] || {
        wget -q --show-progress -O "$REF/transcriptome.fa.gz" "$TXOME_URL"
        gunzip "$REF/transcriptome.fa.gz"
    }

    # Genome is only needed for decoy-aware indexing (~3 GB uncompressed)
    log "Downloading GRCh38 genome (for decoy-aware index)..."
    [[ -f "$REF/genome.fa" ]] || {
        wget -q --show-progress -O "$REF/genome.fa.gz" "$GENOME_URL"
        gunzip "$REF/genome.fa.gz"
    }

    log "Downloading GTF annotation (for tx2gene)..."
    [[ -f "$REF/annotation.gtf.gz" ]] || \
        wget -q --show-progress -O "$REF/annotation.gtf.gz" "$GTF_URL"
}

# ---------------------------------------------------------------------------
# 3. Build decoy-aware Salmon index
#    Index format changed in 2.0 — cpp and rust indexes are stored separately
#    and are NOT interchangeable. Both use the same gentrome/decoys source files.
# ---------------------------------------------------------------------------
build_index() {
    [[ -f "$IDX/info.json" ]] && { log "Index already exists, skipping."; return; }

    log "Building decoy list from genome headers..."
    grep "^>" "$REF/genome.fa" | cut -d " " -f 1 | sed 's/>//' > "$REF/decoys.txt"

    log "Concatenating gentrome (transcriptome + genome)..."
    # Transcriptome must come first; genome sequences become the decoy
    cat "$REF/transcriptome.fa" "$REF/genome.fa" > "$REF/gentrome.fa"

    log "Running salmon index (decoy-aware, GENCODE mode)..."
    # --gencode strips GENCODE version suffixes so ENST00…X.Y becomes ENST00…X
    salmon index \
        -t "$REF/gentrome.fa" \
        -d "$REF/decoys.txt" \
        -i "$IDX" \
        -p "$THREADS" \
        --gencode \
        2>"$LOGS/salmon_index_${SALMON_VERSION}.log"

    log "Index built at $IDX"
}

# ---------------------------------------------------------------------------
# 4. Download raw reads from SRA (requires sra-tools >= 3.0)
# ---------------------------------------------------------------------------
download_reads() {
    for SRR in "${!CONDITION[@]}"; do
        if [[ -f "$READS/${SRR}_1.fastq.gz" ]]; then
            log "$SRR reads already downloaded, skipping."
            continue
        fi
        log "Downloading $SRR (${CONDITION[$SRR]})..."
        fasterq-dump "$SRR" \
            -O "$READS" \
            -e "$THREADS" \
            --split-files \
            --progress \
            2>"$LOGS/${SRR}_download.log"
        gzip "$READS/${SRR}_1.fastq" "$READS/${SRR}_2.fastq"
    done
}

# ---------------------------------------------------------------------------
# 5. Salmon quantification
#
#  rust (2.0): selective alignment is the DEFAULT — --validateMappings is
#              accepted but silently ignored. New: --sketch for faster
#              alignment-free mode. Bias online (--numBiasSamples removed).
#
#  cpp (1.12.0): --validateMappings enables selective alignment (non-default).
#                Supports --mimicBT2, --minAssignedFrags, --numBiasSamples.
#
#  Both versions: --gcBias, --seqBias, --numBootstraps, --gencode, decoys
# ---------------------------------------------------------------------------

quantify() {
    local FLAGS
    case "$SALMON_VERSION" in
      rust)
        # Selective alignment is the DEFAULT in 2.0; --validateMappings is a no-op.
        # Use --sketch instead for faster alignment-free mode.
        FLAGS="--gcBias --seqBias --numBootstraps 100"
        ;;
      cpp)
        # --validateMappings upgrades C++ from quasi-mapping to selective alignment.
        FLAGS="--validateMappings --gcBias --seqBias --numBootstraps 100"
        ;;
    esac

    for SRR in "${!CONDITION[@]}"; do
        if [[ -f "$QUANT/$SRR/quant.sf" ]]; then
            log "$SRR already quantified, skipping."
            continue
        fi
        log "Quantifying $SRR (${CONDITION[$SRR]})..."
        # shellcheck disable=SC2086
        salmon quant \
            -i "$IDX" \
            -l A \
            -1 "$READS/${SRR}_1.fastq.gz" \
            -2 "$READS/${SRR}_2.fastq.gz" \
            -p "$THREADS" \
            $FLAGS \
            -o "$QUANT/$SRR" \
            2>"$LOGS/${SRR}_quant_${SALMON_VERSION}.log"
        log "  mapping rate: $(grep 'Mapping rate' "$LOGS/${SRR}_quant_${SALMON_VERSION}.log" | awk '{print $NF}')"
    done
}

# ---------------------------------------------------------------------------
# 6. Summary table of mapping rates
# ---------------------------------------------------------------------------
summarize() {
    log "=== Mapping Rate Summary (salmon $SALMON_VERSION) ==="
    printf "%-14s  %-14s  %s\n" "Sample" "Condition" "MappingRate"
    printf "%-14s  %-14s  %s\n" "------" "---------" "-----------"
    for SRR in $(echo "${!CONDITION[@]}" | tr ' ' '\n' | sort); do
        RATE=$(grep "Mapping rate" "$LOGS/${SRR}_quant_${SALMON_VERSION}.log" 2>/dev/null \
               | awk '{print $NF}' || echo "N/A")
        printf "%-14s  %-14s  %s\n" "$SRR" "${CONDITION[$SRR]}" "$RATE"
    done
    log "quant.sf files ready for tximport/tximeta in $QUANT/"
}

# ---------------------------------------------------------------------------
main() {
    install_salmon
    download_references
    build_index
    download_reads
    quantify
    summarize
}

main "$@"
