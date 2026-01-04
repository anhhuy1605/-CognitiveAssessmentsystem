# -*- coding: utf-8 -*-
"""
Test and View Clinical Interpretation Results
==============================================
Create test session and save comprehensive results to JSON file
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.mmse_chatbot_service import MMSEChatbotService
from services.comprehensive_results_generator import generate_comprehensive_results
from datetime import datetime

def create_test_session_with_clinical_features():
    """Create test session với acoustic và linguistic features để test clinical interpretation"""
    
    chatbot_service = MMSEChatbotService()
    
    # Create session
    session_id = f"test_clinical_view_{int(datetime.now().timestamp())}"
    user_info = {
        'age': 72,
        'gender': 'female',
        'education_years': 10
    }
    
    state = chatbot_service.create_session(session_id, user_info)
    
    # Set domain scores
    state.domain_scores = {
        'orientation': 8,
        'registration': 2,
        'attention_calculation': 3,
        'executive_function': 2,
        'recall': 1,
        'language': 6,
        'visuospatial': 2
    }
    state.total_score = 24  # MCI range
    
    # Add acoustic features (concerning values để test clinical interpretation)
    state.acoustic_features = {
        'q1': {
            'jitter': 0.025,  # Concerning (>0.020)
            'shimmer': 0.065,  # Concerning (>0.050)
            'hnr': 11.5,  # Concerning (<12.0)
            'pause_rate': 0.45,  # Concerning (>0.40) - strongest predictor!
            'speaking_rate': 95.0,  # Concerning (<100)
            'f0_mean': 185.0,
            'f0_cv': 0.08  # Concerning (<0.10)
        },
        'q2': {
            'jitter': 0.022,
            'shimmer': 0.060,
            'hnr': 12.5,
            'pause_rate': 0.42,
            'speaking_rate': 98.0,
            'f0_mean': 188.0,
            'f0_cv': 0.09
        }
    }
    
    # Add linguistic features (concerning values)
    state.linguistic_features = {
        'TTR': 0.42,  # Concerning (<0.50)
        'pronoun_ratio': 0.38,  # Concerning (>0.35)
        'idea_density': 0.38,  # Concerning (<0.40) - Nun Study!
        'MLU': 5.5  # Concerning (<6.0)
    }
    
    # Add MCI result
    state.mci_result = {
        'combined_risk_score': 0.65,
        'risk_level': 'nguy_co_nhe',
        'risk_components': {
            'mmse': 0.25,
            'acoustic': 0.22,
            'linguistic': 0.18
        }
    }
    
    state.completed_at = datetime.now().isoformat()
    
    # Save to service
    chatbot_service.sessions[session_id] = state
    
    return session_id, chatbot_service, state

def main():
    """Main function to create test and save results"""
    
    print("Creating test session...")
    session_id, chatbot_service, state = create_test_session_with_clinical_features()
    
    print(f"Session ID: {session_id}")
    print("Generating comprehensive results...")
    
    try:
        comprehensive_results = generate_comprehensive_results(
            session_state=state,
            shap_explanations=None
        )
        
        output_file = f"test_clinical_results_{session_id}.json"
        
        # Save to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\nResults saved to: {output_file}")
        print(f"\nSummary:")
        print(f"  - Session ID: {session_id}")
        print(f"  - MMSE Score: {state.total_score}/35")
        print(f"  - Risk Level: {state.mci_result.get('risk_level', 'N/A')}")
        print(f"  - Sections: {len(comprehensive_results)}")
        print(f"  - SHAP features: {len(comprehensive_results.get('shap_explanation', {}).get('feature_contributions', {}))}")
        print(f"  - Recommendations: {len(comprehensive_results.get('recommendations', []))}")
        
        return output_file
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    output_file = main()
    if output_file:
        print(f"\nOpen file to view: {output_file}")

