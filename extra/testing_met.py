import pandas as pd
import numpy as np
from math import asin, sqrt
from scipy.stats import chi2

# ────────────────────────────────────────────────────────────────
# 1. Load the Excel file
# ────────────────────────────────────────────────────────────────
file_path = "ThesisResponses(AB)_tones.xlsx"
df = pd.read_excel(file_path, sheet_name=0)

# Choices are in columns 1 to 21 (0-indexed 1:22), after Timestamp
choices = df.iloc[:, 1:22].copy()                          # Rows 0+ are data
choices.columns = [f'Q{i+1}' for i in range(21)]           # Rename for clarity

# ────────────────────────────────────────────────────────────────
# 2. Overall preference statistics
# ────────────────────────────────────────────────────────────────
a_count = (choices == 'A').sum().sum()
b_count = (choices == 'B').sum().sum()
total_valid = a_count + b_count

# Assume majority vote determines prototype (as in thesis)
prototype = 'A' if a_count > b_count else 'B'
preference_rate = (a_count / total_valid) * 100 if total_valid > 0 else 0.0

print(f"Total valid preferences: {total_valid}")
print(f"A: {a_count} ({a_count/total_valid:.1%})")
print(f"B: {b_count} ({b_count/total_valid:.1%})")
print(f"Assumed Prototype = {prototype}")
print(f"Preference rate for prototype: {preference_rate:.2f}%")

# Cohen's h
def cohens_h(p):
    if p <= 0 or p >= 1:
        return 0.0
    return 2 * (asin(sqrt(p)) - asin(sqrt(1 - p)))

h_overall = cohens_h(a_count / total_valid)
print(f"Cohen's h: {h_overall:.2f}")

# McNemar test (continuity corrected)
diff = abs(a_count - b_count) - 1
chi2_stat = diff**2 / total_valid if total_valid > 0 else 0
p_value = chi2.sf(chi2_stat, 1) if chi2_stat > 0 else 1.0
print(f"McNemar's χ²(1) = {chi2_stat:.2f}, p = {p_value:.4f}")

# 95% Confidence Interval (normal approximation)
p = a_count / total_valid
se = np.sqrt(p * (1 - p) / total_valid)
ci_lower = (p - 1.96 * se) * 100
ci_upper = (p + 1.96 * se) * 100
print(f"95% CI for preference rate: {ci_lower:.1f}% – {ci_upper:.1f}%\n")

# ────────────────────────────────────────────────────────────────
# 3. Language-specific breakdown
# ────────────────────────────────────────────────────────────────
eng_queries = [1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 17]   # 11 English
ger_queries = [3, 4, 5, 6, 7, 16, 18, 19, 20, 21]        # 10 German

eng_idx = [q-1 for q in eng_queries]   # 0-based
ger_idx = [q-1 for q in ger_queries]

# English
eng_a = (choices.iloc[:, eng_idx] == 'A').sum().sum()
eng_total = choices.iloc[:, eng_idx].notna().sum().sum()
eng_rate = (eng_a / eng_total * 100) if eng_total > 0 else 0.0
eng_h = cohens_h(eng_a / eng_total)

# German
ger_a = (choices.iloc[:, ger_idx] == 'A').sum().sum()
ger_total = choices.iloc[:, ger_idx].notna().sum().sum()
ger_rate = (ger_a / ger_total * 100) if ger_total > 0 else 0.0
ger_h = cohens_h(ger_a / ger_total)

abs_bias = abs(eng_rate - ger_rate)

print("Language breakdown:")
print(f"  English ({eng_total} prefs): {eng_rate:5.2f}%   Cohen's h = {eng_h:.2f}")
print(f"  German  ({ger_total} prefs): {ger_rate:5.2f}%   Cohen's h = {ger_h:.2f}")
print(f"  Absolute bias: {abs_bias:.2f}%\n")

# ────────────────────────────────────────────────────────────────
# 4. Dimension ratings (Clarity, Helpfulness, Empathy, Personalization)
# ────────────────────────────────────────────────────────────────
# Find all rating columns (they follow pattern Qx_Clarity, etc.)
rating_cols = [c for c in df.columns if any(d in c for d in ['Clarity','Helpfulness','Empathy','Personalization'])]

if rating_cols:
    ratings = df[rating_cols].copy()
    
    # Compute mean per dimension across all questions
    clarity_mean   = ratings.filter(like='Clarity').mean().mean()
    helpful_mean   = ratings.filter(like='Helpfulness').mean().mean()
    empathy_mean   = ratings.filter(like='Empathy').mean().mean()
    persona_mean   = ratings.filter(like='Personalization').mean().mean()
    
    print("Average dimension ratings (0–4 scale):")
    print(f"  Clarity:       {clarity_mean:.2f}  → {clarity_mean/4*100:5.1f}%")
    print(f"  Helpfulness:   {helpful_mean:.2f}  → {helpful_mean/4*100:5.1f}%")
    print(f"  Empathy:       {empathy_mean:.2f}  → {empathy_mean/4*100:5.1f}%")
    print(f"  Personalization: {persona_mean:.2f}  → {persona_mean/4*100:5.1f}%")
else:
    print("No rating columns found in this version of the file.")