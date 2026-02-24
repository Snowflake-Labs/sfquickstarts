# MONAI Medical Image Registration on Snowflake

Train and deploy a MONAI deep learning model for 3D CT lung registration using Snowflake's ML infrastructure.

## Overview

| Component | Description |
|-----------|-------------|
| **Model** | MONAI LocalNet - deformable image registration |
| **Data** | Paired lung CT scans from [Zenodo](https://zenodo.org/record/3835682) |
| **Training** | GPU-accelerated on Snowflake Container Runtime |
| **Inference** | Distributed batch processing on GPU compute pools |

## Files

| File | Description |
|------|-------------|
| `01_setup.sql` | Snowflake infrastructure setup |
| `02_ingest_data.ipynb` | Download and upload medical images |
| `03_train_and_register.ipynb` | Train model on GPU, log to registry |
| `04_batch_inference.ipynb` | Run distributed batch inference |

## Quick Start

### 1. Setup Infrastructure

Run `01_setup.sql` in Snowsight as ACCOUNTADMIN (copy/paste or use SnowSQL).

### 2. Run Notebooks in Order

```
02_ingest_data.ipynb → 03_train_and_register.ipynb → 04_batch_inference.ipynb
```

## Prerequisites

### Snowflake
- Account with ACCOUNTADMIN access (for initial setup)
- GPU compute pool (e.g., `GPU_NV_S` instance family)

### Python
```bash
pip install monai nibabel torch snowflake-ml-python snowflake-snowpark-python
```

### Snowflake Connection
Configure your connection in `~/.snowflake/connections.toml`:
```toml
[default]
account = "your_account"
user = "your_user"
authenticator = "externalbrowser"  # or use password/key-pair
```

## Model Details

**LocalNet** predicts a deformation displacement field (DDF) to align moving images to fixed images:

```
Moving Image ──┐
               ├── LocalNet ──► DDF ──► Aligned Image
Fixed Image ───┘
```

- **Input**: 2 channels (moving + fixed CT scans)
- **Output**: 3 channels (DDF x, y, z displacement components)
- **Loss**: Mutual Information + Bending Energy regularization

## Configuration

Default training settings (adjustable in notebook):

| Parameter | Value | Description |
|-----------|-------|-------------|
| `spatial_size` | (96, 96, 96) | Volume dimensions after resize |
| `batch_size` | 2 | Samples per batch |
| `max_epochs` | 15 | Training iterations |
| `learning_rate` | 1e-4 | Optimizer step size |

## Resources

- [MONAI Documentation](https://docs.monai.io/)
- [Snowflake Model Registry](https://docs.snowflake.com/en/developer-guide/snowflake-ml/model-registry/overview)
- [Paired CT Lung Dataset](https://zenodo.org/record/3835682)
