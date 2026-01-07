# -*- coding: utf-8 -*-
"""
View Comprehensive Results
==========================
Pretty print comprehensive results from JSON file
"""

import json
import sys

def view_results(json_file):
    """View comprehensive results from JSON file"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        results = json.load(f)
    
    print("=" * 80)
    print("COMPREHENSIVE RESULTS VIEWER")
    print("=" * 80)
    
    # 1. Assessment Result
    if 'assessment_result' in results:
        ar = results['assessment_result']
        print("\n1. ASSESSMENT RESULT")
        print("-" * 80)
        print(f"  MMSE Score: {ar.get('mmse_score', 'N/A')}/35")
        print(f"  Risk Level: {ar.get('risk_level', 'N/A')}")
        print(f"  Classification: {ar.get('classification', 'N/A')}")
    
    # 2. SHAP Explanation
    if 'shap_explanation' in results:
        shap = results['shap_explanation']
        print("\n2. SHAP EXPLANATION")
        print("-" * 80)
        print(f"  Total feature contributions: {len(shap.get('feature_contributions', {}))}")
        
        # Overall interpretation
        if 'overall_interpretation' in shap:
            print("\n  Overall Interpretation:")
            interp = shap['overall_interpretation']
            # Print first 500 chars
            print(f"    {interp[:500]}...")
        
        # Top risk factors
        if 'top_risk_factors' in shap:
            print(f"\n  Top Risk Factors ({len(shap['top_risk_factors'])}):")
            for i, factor in enumerate(shap['top_risk_factors'][:5], 1):
                print(f"    {i}. {factor.get('feature', 'N/A')}")
                print(f"       Contribution: {factor.get('contribution', 'N/A')}")
                print(f"       Value: {factor.get('value', 'N/A')} {factor.get('unit', '')}")
                if 'explanation' in factor:
                    exp = factor['explanation'][:200] if isinstance(factor['explanation'], str) else str(factor['explanation'])[:200]
                    print(f"       {exp}...")
        
        # Key concerns
        if 'key_concerns' in shap:
            print(f"\n  Key Concerns ({len(shap['key_concerns'])}):")
            for concern in shap['key_concerns'][:5]:
                print(f"    - {concern.get('feature', 'N/A')}: {concern.get('range', 'N/A')}")
    
    # 3. Recommendations
    if 'recommendations' in results:
        recs = results['recommendations']
        print("\n3. RECOMMENDATIONS")
        print("-" * 80)
        print(f"  Total: {len(recs)} recommendations")
        for i, rec in enumerate(recs[:10], 1):
            if isinstance(rec, dict):
                print(f"\n  {i}. [{rec.get('priority', 'N/A').upper()}] {rec.get('title', 'N/A')}")
                print(f"     Category: {rec.get('category', 'N/A')}")
                if 'description' in rec:
                    desc = rec['description'][:150] if isinstance(rec['description'], str) else str(rec['description'])[:150]
                    print(f"     {desc}...")
                if 'actions' in rec and rec['actions']:
                    print(f"     Actions: {len(rec['actions'])} items")
            else:
                print(f"  {i}. {rec}")
    
    # 4. Multimodal Analysis
    if 'multimodal_analysis' in results:
        ma = results['multimodal_analysis']
        print("\n4. MULTIMODAL ANALYSIS")
        print("-" * 80)
        print(f"  Combined Risk Score: {ma.get('combined_risk_score', 'N/A')}")
        print(f"  Risk Level: {ma.get('risk_level', 'N/A')}")
        print(f"  Acoustic features: {len(ma.get('acoustic_features', {}))}")
        print(f"  Linguistic features: {len(ma.get('linguistic_features', {}))}")
    
    print("\n" + "=" * 80)
    print(f"Full results saved in: {json_file}")
    print("=" * 80)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # Find latest test file
        import glob
        files = glob.glob('test_clinical_results_*.json')
        if files:
            json_file = max(files, key=os.path.getctime)
        else:
            print("No test file found. Please specify JSON file.")
            sys.exit(1)
    
    view_results(json_file)

