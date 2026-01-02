"""
Complete Thesis Metrics Verification Tool
Calculates ALL missing metrics from thesis document
"""

import pandas as pd
import numpy as np
from scipy import stats
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

class CompleteThesisMetrics:
    """Calculate all thesis metrics with proper methodology"""
    
    def __init__(self, csv_path='ThesisResponses(AB)_tones.xlsx'):
        """Load and prepare data"""
        print("="*80)
        print("COMPLETE THESIS METRICS VERIFICATION")
        print("="*80)
        
        # Load data
        self.df = pd.read_excel(csv_path)
        print(f"\n✅ Loaded {len(self.df)} responses")
        
        # Prepare data
        self._prepare_data()
        
    def _prepare_data(self):
        """Prepare and validate data"""
        # Get all question columns
        self.questions = [col for col in self.df.columns if col.startswith('Q')]
        
        # Map dimensions
        self.dimensions = {
            'Clarity': [col for col in self.questions if 'Clarity' in col],
            'Helpfulness': [col for col in self.questions if 'Helpfulness' in col],
            'Empathy': [col for col in self.questions if 'Empathy' in col],
            'Personalization': [col for col in self.questions if 'Personalization' in col]
        }
        
        # Extract language info (Q1-Q13 English, Q14-Q21 German)
        self.english_cols = [col for col in self.questions if int(col.split('_')[0][1:]) <= 13]
        self.german_cols = [col for col in self.questions if int(col.split('_')[0][1:]) > 13]
        
        print(f"Found {len(self.questions)} rating columns")
        print(f"  English questions: {len(set([c.split('_')[0] for c in self.english_cols]))//4}")
        print(f"  German questions: {len(set([c.split('_')[0] for c in self.german_cols]))//4}")
    
    def calculate_all_metrics(self):
        """Calculate all thesis metrics"""
        results = {}
        
        print("\n" + "="*80)
        print("1. OVERALL USER PREFERENCES (Section 4.3)")
        print("="*80)
        results['overall'] = self._calculate_overall_preferences()
        
        print("\n" + "="*80)
        print("2. DIMENSION-SPECIFIC PREFERENCES")
        print("="*80)
        results['dimensions'] = self._calculate_dimension_preferences()
        
        print("\n" + "="*80)
        print("3. CROSS-LANGUAGE ANALYSIS")
        print("="*80)
        results['language'] = self._calculate_language_preferences()
        
        print("\n" + "="*80)
        print("4. INTENT CATEGORY ANALYSIS")
        print("="*80)
        results['intent'] = self._calculate_intent_preferences()
        
        print("\n" + "="*80)
        print("5. STATISTICAL VALIDATION")
        print("="*80)
        results['statistics'] = self._calculate_statistical_tests()
        
        print("\n" + "="*80)
        print("6. AVERAGE RATINGS BY DIMENSION")
        print("="*80)
        results['ratings'] = self._calculate_average_ratings()
        
        return results
    
    def _calculate_overall_preferences(self):
        """Calculate overall preference statistics"""
        # Count A vs B preferences across all questions
        total_a = 0
        total_b = 0
        total_comparisons = 0
        
        for col in self.questions:
            responses = self.df[col].dropna()
            a_count = (responses == 'A').sum()
            b_count = (responses == 'B').sum()
            
            total_a += a_count
            total_b += b_count
            total_comparisons += (a_count + b_count)
        
        pref_rate = total_a / total_comparisons if total_comparisons > 0 else 0
        
        # McNemar's test
        chi_square = ((abs(total_b - total_a) - 1) ** 2) / (total_b + total_a)
        
        # Cohen's h
        p1 = pref_rate
        p2 = 1 - p1
        cohens_h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
        
        # 95% CI
        se = np.sqrt(pref_rate * (1 - pref_rate) / total_comparisons)
        ci_lower = pref_rate - 1.96 * se
        ci_upper = pref_rate + 1.96 * se
        
        print(f"\nTotal comparisons: {total_comparisons}")
        print(f"Prototype (A) wins: {total_a} ({pref_rate*100:.2f}%)")
        print(f"Baseline (B) wins: {total_b} ({(1-pref_rate)*100:.2f}%)")
        print(f"\nThesis expectation: 69.65% (746/1071)")
        print(f"Your result: {pref_rate*100:.2f}% ({total_a}/{total_comparisons})")
        print(f"\nMcNemar's χ²: {chi_square:.2f} (Thesis: 164.71)")
        print(f"Cohen's h: {cohens_h:.2f} (Thesis: 0.81)")
        print(f"95% CI: {ci_lower*100:.1f}% – {ci_upper*100:.1f}%")
        
        return {
            'total_comparisons': total_comparisons,
            'prototype_wins': total_a,
            'baseline_wins': total_b,
            'preference_rate': pref_rate,
            'mcnemar_chi2': chi_square,
            'cohens_h': cohens_h,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }
    
    def _calculate_dimension_preferences(self):
        """Calculate preferences by dimension"""
        dim_results = {}
        
        print("\n" + "-"*80)
        print(f"{'Dimension':<20} {'Prototype %':<15} {'Thesis %':<15} {'Match'}")
        print("-"*80)
        
        thesis_values = {
            'Clarity': 78,
            'Helpfulness': 81,
            'Empathy': 74,
            'Personalization': 86
        }
        
        for dim_name, cols in self.dimensions.items():
            a_count = 0
            b_count = 0
            
            for col in cols:
                responses = self.df[col].dropna()
                a_count += (responses == 'A').sum()
                b_count += (responses == 'B').sum()
            
            total = a_count + b_count
            pref_rate = (a_count / total * 100) if total > 0 else 0
            thesis_val = thesis_values[dim_name]
            match = "✅" if abs(pref_rate - thesis_val) < 5 else "⚠️"
            
            print(f"{dim_name:<20} {pref_rate:>6.1f}%        {thesis_val:>6}%        {match}")
            
            dim_results[dim_name] = {
                'preference_rate': pref_rate,
                'prototype_wins': a_count,
                'baseline_wins': b_count,
                'thesis_expected': thesis_val
            }
        
        return dim_results
    
    def _calculate_language_preferences(self):
        """Calculate cross-language preferences"""
        # English
        en_a = sum((self.df[col] == 'A').sum() for col in self.english_cols)
        en_b = sum((self.df[col] == 'B').sum() for col in self.english_cols)
        en_total = en_a + en_b
        en_pref = (en_a / en_total * 100) if en_total > 0 else 0
        
        # German
        de_a = sum((self.df[col] == 'A').sum() for col in self.german_cols)
        de_b = sum((self.df[col] == 'B').sum() for col in self.german_cols)
        de_total = de_a + de_b
        de_pref = (de_a / de_total * 100) if de_total > 0 else 0
        
        gap = abs(en_pref - de_pref)
        
        print(f"\nEnglish preference: {en_pref:.2f}% (Thesis: 83%)")
        print(f"German preference: {de_pref:.2f}% (Thesis: 75%)")
        print(f"Language gap: {gap:.2f}% (Thesis: 8%)")
        
        # Cohen's h for each language
        en_h = 2 * (np.arcsin(np.sqrt(en_pref/100)) - np.arcsin(np.sqrt(1-en_pref/100)))
        de_h = 2 * (np.arcsin(np.sqrt(de_pref/100)) - np.arcsin(np.sqrt(1-de_pref/100)))
        
        print(f"\nEnglish Cohen's h: {en_h:.2f}")
        print(f"German Cohen's h: {de_h:.2f}")
        
        return {
            'english': {'pref': en_pref, 'wins': en_a, 'total': en_total, 'cohens_h': en_h},
            'german': {'pref': de_pref, 'wins': de_a, 'total': de_total, 'cohens_h': de_h},
            'gap': gap
        }
    
    def _calculate_intent_preferences(self):
        """Calculate preferences by intent category"""
        # Map questions to intent categories (from thesis)
        intent_mapping = {
            'Enrollment & Admissions': [1, 2, 14, 15],
            'Course Information': [3, 4, 5, 16],
            'IT Support': [6, 17],
            'Finance & Tuition': [7, 18],
            'Academic Calendar': [8, 9, 19],
            'Student Services': [10, 11, 20],
            'General Queries': [12, 13, 21]
        }
        
        thesis_expected = {
            'Enrollment & Admissions': 89,
            'IT Support': 85,
            'Finance & Tuition': 87,
            'Course Information': 78,
            'Academic Calendar': 76,
            'Student Services': 75,
            'General Queries': 68
        }
        
        intent_results = {}
        
        print("\n" + "-"*80)
        print(f"{'Intent Category':<30} {'Prototype %':<15} {'Thesis %':<15} {'Match'}")
        print("-"*80)
        
        for intent, questions in intent_mapping.items():
            a_count = 0
            b_count = 0
            
            for q_num in questions:
                q_cols = [col for col in self.questions if col.startswith(f'Q{q_num}_')]
                for col in q_cols:
                    responses = self.df[col].dropna()
                    a_count += (responses == 'A').sum()
                    b_count += (responses == 'B').sum()
            
            total = a_count + b_count
            pref_rate = (a_count / total * 100) if total > 0 else 0
            expected = thesis_expected.get(intent, 0)
            match = "✅" if abs(pref_rate - expected) < 10 else "⚠️"
            
            print(f"{intent:<30} {pref_rate:>6.1f}%        {expected:>6}%        {match}")
            
            intent_results[intent] = {
                'preference_rate': pref_rate,
                'prototype_wins': a_count,
                'baseline_wins': b_count,
                'thesis_expected': expected
            }
        
        return intent_results
    
    def _calculate_statistical_tests(self):
        """Perform statistical tests"""
        # Get all preferences
        all_prefs = []
        for col in self.questions:
            prefs = self.df[col].dropna()
            all_prefs.extend(prefs.tolist())
        
        a_count = all_prefs.count('A')
        b_count = all_prefs.count('B')
        total = a_count + b_count
        
        # Binomial test (H0: p = 0.5)
        try:
            # Try new API (SciPy >= 1.7)
            binom_result = stats.binomtest(a_count, total, 0.5, alternative='two-sided').pvalue
            binom_60 = stats.binomtest(a_count, total, 0.6, alternative='greater').pvalue
        except AttributeError:
            # Fall back to old API
            binom_result = stats.binom_test(a_count, total, 0.5, alternative='two-sided')
            binom_60 = stats.binom_test(a_count, total, 0.6, alternative='greater')
        
        print(f"\nBinomial test (vs 50%): p = {binom_result:.6f}")
        print(f"Binomial test (vs 60%): p = {binom_60:.6f}")
        
        # McNemar test
        chi2 = ((abs(b_count - a_count) - 1) ** 2) / (b_count + a_count)
        p_value = 1 - stats.chi2.cdf(chi2, 1)
        
        print(f"\nMcNemar's test:")
        print(f"  χ²(1) = {chi2:.2f}")
        print(f"  p < 0.001" if p_value < 0.001 else f"  p = {p_value:.4f}")
        
        return {
            'binomial_50': binom_result,
            'binomial_60': binom_60,
            'mcnemar_chi2': chi2,
            'mcnemar_p': p_value
        }
    
    def _calculate_average_ratings(self):
        """Calculate average ratings by dimension"""
        dim_ratings = {}
        
        print("\n" + "-"*60)
        print(f"{'Dimension':<20} {'Avg Rating':<15} {'Percentage':<15}")
        print("-"*60)
        
        for dim_name, cols in self.dimensions.items():
            ratings = []
            for col in cols:
                ratings.extend(self.df[col].dropna().tolist())
            
            # Convert to numeric
            numeric_ratings = []
            for r in ratings:
                if isinstance(r, (int, float)):
                    numeric_ratings.append(r)
                elif r in ['A', 'B']:
                    continue  # Skip A/B responses
            
            if numeric_ratings:
                avg = np.mean(numeric_ratings)
                pct = (avg / 4) * 100  # Assuming 0-4 scale
                
                print(f"{dim_name:<20} {avg:>6.2f}        {pct:>6.1f}%")
                
                dim_ratings[dim_name] = {
                    'average': avg,
                    'percentage': pct,
                    'count': len(numeric_ratings)
                }
        
        return dim_ratings
    
    def generate_summary_report(self, results):
        """Generate comprehensive summary"""
        print("\n" + "="*80)
        print("COMPREHENSIVE THESIS METRICS SUMMARY")
        print("="*80)
        
        print("\n📊 SECTION 4.3 - USER PREFERENCE EVALUATION")
        print("-"*80)
        overall = results['overall']
        print(f"Overall Prototype Preference: {overall['preference_rate']*100:.2f}%")
        print(f"  Thesis Value: 69.65%")
        print(f"  Difference: {abs(overall['preference_rate']*100 - 69.65):.2f} percentage points")
        print(f"\nMcNemar's χ²: {overall['mcnemar_chi2']:.2f} (Thesis: 164.71)")
        print(f"Cohen's h: {overall['cohens_h']:.2f} (Thesis: 0.81)")
        
        print("\n📈 DIMENSION-SPECIFIC RESULTS")
        print("-"*80)
        for dim, data in results['dimensions'].items():
            print(f"{dim}: {data['preference_rate']:.1f}% (Thesis: {data['thesis_expected']}%)")
        
        print("\n🌍 CROSS-LANGUAGE COMPARISON")
        print("-"*80)
        lang = results['language']
        print(f"English: {lang['english']['pref']:.2f}% (Thesis: 83%)")
        print(f"German: {lang['german']['pref']:.2f}% (Thesis: 75%)")
        print(f"Gap: {lang['gap']:.2f}% (Thesis: 8%)")
        
        print("\n🎯 INTENT CATEGORY PREFERENCES")
        print("-"*80)
        for intent, data in results['intent'].items():
            print(f"{intent}: {data['preference_rate']:.1f}% (Thesis: {data['thesis_expected']}%)")
        
        print("\n" + "="*80)

# Run analysis
if __name__ == "__main__":
    analyzer = CompleteThesisMetrics('ThesisResponses(AB)_tones.xlsx')
    results = analyzer.calculate_all_metrics()
    analyzer.generate_summary_report(results)
    
    print("\n✅ Analysis complete!")