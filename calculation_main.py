"""
Master Thesis – Complete Matrix-Based Statistical Analysis
Data source: ThesisResponses(AB)_tones.xlsx

All computations rely ONLY on the provided XLSX.
"""

import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime
pd.set_option('future.no_silent_downcasting', True)


# =============================================================================
# LOAD DATA
# =============================================================================

FILE_PATH = "ThesisResponses(AB)_tones.xlsx"
OUTPUT_PATH = "matrix_analysis_results.txt"

df = pd.read_excel(FILE_PATH, sheet_name=0)

NUM_QUESTIONS = 21

ENG_Q = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 17]
GER_Q = [3, 4, 5, 6, 7, 16, 18, 19, 20, 21]
ENG_IDX = [q - 1 for q in ENG_Q]
GER_IDX = [q - 1 for q in GER_Q]

# =============================================================================
# 1. PREFERENCE MATRIX
# =============================================================================

P = (
    df.iloc[:, 1:1 + NUM_QUESTIONS]
    .replace({'A': 1, 'B': 0})
    .infer_objects(copy=False)
    .astype(float)
)
P_matrix = P.values

preference_vector = P.mean(axis=0)
preference_variance = P.var(axis=0)

# =============================================================================
# 2. RATING MATRICES
# =============================================================================

def rating_matrix(keyword):
    return df[[c for c in df.columns if keyword in c]].astype(float)

R_clarity = rating_matrix("Clarity")
R_helpfulness = rating_matrix("Helpfulness")
R_empathy = rating_matrix("Empathy")
R_personalization = rating_matrix("Personalization")

R_aggregated = pd.DataFrame({
    "Clarity": R_clarity.mean(axis=1),
    "Helpfulness": R_helpfulness.mean(axis=1),
    "Empathy": R_empathy.mean(axis=1),
    "Personalization": R_personalization.mean(axis=1),
})

rating_correlation = R_aggregated.corr()

# =============================================================================
# 3. AGREEMENT & RELIABILITY
# =============================================================================

def fleiss_kappa(matrix):
    N, k = matrix.shape
    n = matrix.sum(axis=1)[0]
    p = matrix.sum(axis=0) / (N * n)
    P_i = (np.sum(matrix ** 2, axis=1) - n) / (n * (n - 1))
    return (P_i.mean() - np.sum(p ** 2)) / (1 - np.sum(p ** 2))

fleiss_input = np.array([
    [(P.iloc[:, q] == 1).sum(), (P.iloc[:, q] == 0).sum()]
    for q in range(NUM_QUESTIONS)
])

fleiss_k = fleiss_kappa(fleiss_input)

def krippendorff_alpha_nominal(data):
    categories = [0, 1]
    Do = 0
    for row in data:
        row = row[~np.isnan(row)]
        for a, b in combinations(row, 2):
            Do += int(a != b)

    freqs = {c: np.sum(data == c) for c in categories}
    n = sum(freqs.values())
    De = freqs[0] * freqs[1]

    return 1 - (Do / De) if De != 0 else 1.0

kripp_alpha = krippendorff_alpha_nominal(P_matrix)

# =============================================================================
# 4. CONFUSION / TRANSITION MATRIX
# =============================================================================

confusion_matrix = np.array([
    [(P.iloc[:, ENG_IDX] == 1).sum().sum(), (P.iloc[:, ENG_IDX] == 0).sum().sum()],
    [(P.iloc[:, GER_IDX] == 1).sum().sum(), (P.iloc[:, GER_IDX] == 0).sum().sum()]
])

language_bias = P.iloc[:, ENG_IDX].mean().mean() - P.iloc[:, GER_IDX].mean().mean()

# =============================================================================
# 5. PCA (SVD)
# =============================================================================

X = R_aggregated.values
Xc = X - X.mean(axis=0)
_, S, _ = np.linalg.svd(Xc, full_matrices=False)
explained_variance = (S ** 2) / np.sum(S ** 2)

# =============================================================================
# SAVE RESULTS
# =============================================================================

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("MASTER THESIS – MATRIX ANALYSIS RESULTS\n")
    f.write(f"Generated: {datetime.now()}\n")
    f.write("=" * 70 + "\n\n")

    f.write("Preference Vector:\n")
    f.write(preference_vector.to_string() + "\n\n")

    f.write("Preference Variance:\n")
    f.write(preference_variance.to_string() + "\n\n")

    f.write("Rating Correlation Matrix:\n")
    f.write(rating_correlation.to_string() + "\n\n")

    f.write(f"Fleiss' Kappa: {fleiss_k:.4f}\n")
    f.write(f"Krippendorff’s Alpha: {kripp_alpha:.4f}\n\n")

    f.write("Confusion Matrix (EN/DE × A/B):\n")
    f.write(str(confusion_matrix) + "\n\n")

    f.write(f"Language Bias (EN − DE): {language_bias:.4f}\n\n")

    f.write("PCA Explained Variance:\n")
    f.write(np.array2string(explained_variance, precision=4))

print("All results computed and saved to:", OUTPUT_PATH)
