# RetinaGuard — Model Evaluation Report

**Evaluation Timestamp**: `2026-10-17T09:37:17.812236+00:00`  
**Model Checkpoint**: `ai_models\retina\weights\best_model.pt`  
**Training Epoch**: `1`  
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
| **Overall Accuracy** | **14.87%** (109/733) | Proportion of exact grade matches across all 5 categories. |
| **Macro-averaged F1** | **0.1317** | Unweighted average of per-class F1 scores (primary metric for class imbalance). |
| **Weighted-averaged F1** | **0.1492** | Sample-weighted average F1 across classes. |
| **Validation Cross-Entropy Loss** | **1.6162** | Uncalibrated Cross-Entropy loss on evaluation split. |

---

## 3. Per-Class Diagnostic Performance

| Class ID | Clinical Diagnosis | Support | Predicted | TP | FP | FN | Precision | Recall | F1-Score |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0** | No Diabetic Retinopathy | 361 | 32 | 29 | 3 | 332 | 0.9062 | 0.0803 | **0.1476** |
| **1** | Mild Non-Proliferative DR | 74 | 274 | 32 | 242 | 42 | 0.1168 | 0.4324 | **0.1839** |
| **2** | Moderate Non-Proliferative DR | 200 | 77 | 25 | 52 | 175 | 0.3247 | 0.1250 | **0.1805** |
| **3** | Severe Non-Proliferative DR | 39 | 349 | 22 | 327 | 17 | 0.0630 | 0.5641 | **0.1134** |
| **4** | Proliferative Diabetic Retinopathy | 59 | 1 | 1 | 0 | 58 | 1.0000 | 0.0169 | **0.0333** |

---

## 4. Multi-Class Confusion Matrix

| True \ Pred | Pred C0 (No Diabetic Retinopathy) | Pred C1 (Mild Non-Proliferative DR) | Pred C2 (Moderate Non-Proliferative DR) | Pred C3 (Severe Non-Proliferative DR) | Pred C4 (Proliferative Diabetic Retinopathy) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **True C0 (No Diabetic Retinopathy)** | **29** | 115 | 22 | 195 | 0 |
| **True C1 (Mild Non-Proliferative DR)** | 1 | **32** | 15 | 26 | 0 |
| **True C2 (Moderate Non-Proliferative DR)** | 2 | 92 | **25** | 81 | 0 |
| **True C3 (Severe Non-Proliferative DR)** | 0 | 13 | 4 | **22** | 0 |
| **True C4 (Proliferative Diabetic Retinopathy)** | 0 | 22 | 11 | 25 | **1** |

```text

Confusion Matrix (Rows: Ground Truth, Cols: Predicted):
True \ Pred | C0 | C1 | C2 | C3 | C4
------------------------------------
Class 0    |   29 |  115 |   22 |  195 |    0
Class 1    |    1 |   32 |   15 |   26 |    0
Class 2    |    2 |   92 |   25 |   81 |    0
Class 3    |    0 |   13 |    4 |   22 |    0
Class 4    |    0 |   22 |   11 |   25 |    1
```

---

## 5. Clinical Observations & Error Analysis

1. **Class-Imbalance Dynamics**: Classes 1 (Mild NPDR, 74 samples) and 3 (Severe NPDR, 39 samples) represent minority clinical stages compared to Class 0 (No DR, 361 samples).
2. **Adjacent Grade Confusion**: Most misclassifications occur between contiguous severity grades (e.g., Grade 0 vs. Grade 1, or Grade 2 vs. Grade 3), which clinically reflects subtle progression of microvascular lesions.
3. **Zero Predictions Guard**: All metrics safely handle zero-prediction scenarios without numeric instability.

---

> [!CAUTION]
> **Medical Research Prototype Notice**:
> This evaluation report is generated for educational and machine learning research benchmarking only.
> MedVision AI RetinaGuard is not certified as a medical device or diagnostic system. These metrics must not be used to justify clinical reliability, screening efficacy, or patient care decisions.