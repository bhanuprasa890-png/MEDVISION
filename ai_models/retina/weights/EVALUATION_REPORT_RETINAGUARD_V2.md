# RetinaGuard — Model Evaluation Report

**Evaluation Timestamp**: `2026-10-17T13:25:23.314747+00:00`  
**Model Checkpoint**: `ai_models\retina\weights\retinaguard_v2.pt`  
**Training Epoch**: `8`  
**Dataset Split Evaluated**: `datasets\aptos\processed\val_manifest.csv` (`VALIDATION`)  
**Total Samples Evaluated**: `733`  

---

## 1. Dataset Split & Data Leakage Disclosure

> [!IMPORTANT]
> **Dataset Split Transparency Notice**:
> This evaluation was performed on the **validation split** (`733` images), which was used during Step 3 model training for checkpoint selection and loss monitoring.
> **No separate, independent labelled test dataset** (e.g., held-out competition test set with ground truth) currently exists in the workspace.
> These metrics reflect validation performance on held-out training partitions and **must not be misrepresented as independent test set metrics**.

### Data Disjointness Verification
- **Train Manifest**: `C:\Users\bhanu\OneDrive\Desktop\MEDVISION\datasets\aptos\processed\train_manifest.csv` (2929 samples)
- **Evaluation Manifest**: `C:\Users\bhanu\OneDrive\Desktop\MEDVISION\datasets\aptos\processed\val_manifest.csv` (733 samples)
- **ID Overlap**: `0` IDs
- **Strict Disjointness**: `PASSED (Zero Overlap)`

---

## 2. Global Performance Summary

| Metric | Score | Clinical Context |
| :--- | :---: | :--- |
| **Overall Accuracy** | **81.72%** (599/733) | Proportion of exact grade matches across all 5 categories. |
| **Macro-averaged F1** | **0.6931** | Unweighted average of per-class F1 scores (primary metric for class imbalance). |
| **Weighted-averaged F1** | **0.8186** | Sample-weighted average F1 across classes. |
| **Validation Cross-Entropy Loss** | **0.53** | Uncalibrated Cross-Entropy loss on evaluation split. |

---

## 3. Per-Class Diagnostic Performance

| Class ID | Clinical Diagnosis | Support | Predicted | TP | FP | FN | Precision | Recall | F1-Score |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | No Diabetic Retinopathy | 362 | 359 | 353 | 6 | 9 | 0.9833 | 0.9751 | **0.9792** |
| **1** | Mild Non-Proliferative DR | 73 | 89 | 51 | 38 | 22 | 0.5730 | 0.6986 | **0.6296** |
| **2** | Moderate Non-Proliferative DR | 201 | 189 | 140 | 49 | 61 | 0.7407 | 0.6965 | **0.7179** |
| **3** | Severe Non-Proliferative DR | 39 | 46 | 24 | 22 | 15 | 0.5217 | 0.6154 | **0.5647** |
| **4** | Proliferative Diabetic Retinopathy | 58 | 50 | 31 | 19 | 27 | 0.6200 | 0.5345 | **0.5741** |

---

## 4. Multi-Class Confusion Matrix

| True \ Pred | Pred C0 (No Diabetic Retinopathy) | Pred C1 (Mild Non-Proliferative DR) | Pred C2 (Moderate Non-Proliferative DR) | Pred C3 (Severe Non-Proliferative DR) | Pred C4 (Proliferative Diabetic Retinopathy) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **True C0 (No Diabetic Retinopathy)** | **353** | 7 | 2 | 0 | 0 |
| **True C1 (Mild Non-Proliferative DR)** | 3 | **51** | 19 | 0 | 0 |
| **True C2 (Moderate Non-Proliferative DR)** | 3 | 27 | **140** | 16 | 15 |
| **True C3 (Severe Non-Proliferative DR)** | 0 | 1 | 10 | **24** | 4 |
| **True C4 (Proliferative Diabetic Retinopathy)** | 0 | 3 | 18 | 6 | **31** |

```text

Confusion Matrix (Rows: Ground Truth, Cols: Predicted):
True \ Pred | C0 | C1 | C2 | C3 | C4
------------------------------------
Class 0    |  353 |    7 |    2 |    0 |    0
Class 1    |    3 |   51 |   19 |    0 |    0
Class 2    |    3 |   27 |  140 |   16 |   15
Class 3    |    0 |    1 |   10 |   24 |    4
Class 4    |    0 |    3 |   18 |    6 |   31
```

---

## 5. Clinical Observations & Error Analysis

1. **Class-Imbalance Dynamics**: Classes 1 (Mild NPDR, 73 samples) and 3 (Severe NPDR, 39 samples) represent minority clinical stages compared to Class 0 (No DR, 362 samples).
2. **Adjacent Grade Confusion**: Most misclassifications occur between contiguous severity grades (e.g., Grade 0 vs. Grade 1, or Grade 2 vs. Grade 3), which clinically reflects subtle progression of microvascular lesions.
3. **Zero Predictions Guard**: All metrics safely handle zero-prediction scenarios without numeric instability.
4. **Development Benchmark Limitation**: Current validation metrics reflect internal development results on a held-out training partition, not independent clinical validation on prospective patient cohorts.

---

> [!CAUTION]
> **Medical Research Prototype Notice**:
> This evaluation report is generated for educational and machine learning research benchmarking only.
> Current validation metrics represent internal development results, not independent clinical validation.
> MedVision AI RetinaGuard is not certified as a medical device or diagnostic system. These metrics must not be used to justify clinical reliability, screening efficacy, or patient care decisions.