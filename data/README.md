# LegalLens — Data Directory & CUAD Dataset Guide

This directory manages dataset resources for LegalLens.

## CUAD (Contract Understanding Atticus Dataset)
The project fine-tunes InLegalBERT on the CUAD dataset (41 types of legal clauses annotated across 510 contracts).

### Downloading the Dataset
1. You can fetch CUAD directly using Hugging Face Datasets:
   ```python
   from datasets import load_dataset
   dataset = load_dataset("TheAtticusProject/cuad")
   ```
2. Or download the original CUAD v1 release from:
   - Official Atticus Project website: [https://www.atticusprojectai.org/cuad](https://www.atticusprojectai.org/cuad)
   - Zenodo: [https://zenodo.org/record/4595826](https://zenodo.org/record/4595826)

### Data Folder Structure
Place any downloaded local raw files in:
```
data/
  raw/                  # gitignored raw JSON / PDF files
  processed/            # filtered splits for the 15 selected categories
  README.md
```

Raw data and checkpoints are ignored by git in `.gitignore`.
