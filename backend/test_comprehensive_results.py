#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Comprehensive Results Generation
================================================
Creates a complete test session with:
- Mock acoustic features (per question)
- Mock linguistic features
- Complete MMSE scores
- SHAP explanations
- All features populated for debugging comprehensive results

Usage:
    python backend/test_comprehensive_results.py
"""

import sys
import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
try:
    from services.mmse_chatbot_service import MMSEChatbotService, SessionState, TestDomain
    from services.comprehensive_results_generator import generate_comprehensive_results
    from services.mmse_scoring_v21 import calculate_multimodal_risk
except ImportError as e:
    logger.error(f"❌ Import error: {e}")
    logger.error("Make sure you're running from the backend directory")
    sys.exit(1)


def create_test_session_with_features(service_instance=None):
    """Create a test session with complete features for comprehensive results
    
    Args:
        service_instance: Optional MMSEChatbotService instance to use (for API endpoint)
    """
    
    logger.info("=" * 80)
    logger.info("🧪 Creating test session with complete features")
    logger.info("=" * 80)
    
    # Initialize service (use provided instance or create new)
    if service_instance:
        chatbot_service = service_instance
    else:
        chatbot_service = MMSEChatbotService()
    
    # Create session ID
    session_id = f"test_comprehensive_{int(datetime.now().timestamp())}"
    
    # Create user info
    user_info = {
        'name': 'Nguyễn Văn Test',
        'age': 75,
        'gender': 'male',
        'education_years': 12,
        'city': 'Hà Nội',
        'district': 'Quận Hoàn Kiếm'
    }
    
    # Create session
    logger.info(f"📝 Creating session: {session_id}")
    state = chatbot_service.create_session(session_id, user_info)
    
    if not state:
        logger.error("❌ Failed to create session")
        return None
    
    logger.info("✅ Session created")
    
    # ✅ STEP 1: Add mock acoustic features (per question)
    logger.info("\n📊 Adding mock acoustic features...")
    
    # Sample acoustic features based on real feature names
    mock_acoustic_features = {
        'f0_mean': 180.5,
        'f0_std': 25.3,
        'f0_range': 120.0,
        'f0_cv': 0.14,
        'jitter': 0.015,
        'shimmer': 0.035,
        'hnr': 18.5,
        'pause_rate': 0.28,
        'pause_duration_mean': 0.45,
        'speaking_rate': 4.2,
        'articulation_rate': 5.1,
        'egemaps_f0_mean': 175.2,
        'egemaps_f0_std': 22.8,
        'egemaps_jitter': 0.016,
        'egemaps_shimmer': 0.038,
        'egemaps_hnr': 17.8,
        'vq_f0_mean': 182.1,
        'vq_f0_std': 24.5,
        'tone_flattening_score': 0.32,
        'vowel_duration_mean': 0.12,
        'consonant_duration_mean': 0.08,
        'phone_duration_std': 0.04,
        'energy_mean': 0.65,
        'energy_std': 0.15,
        'spectral_centroid_mean': 1200.5,
        'spectral_rolloff_mean': 2800.3
    }
    
    # Add acoustic features for multiple questions
    question_ids = [
        'orientation_0',
        'orientation_1', 
        'registration_0',
        'attention_calculation_0',
        'language_0',
        'language_1',
        'language_2',
        'recall_0'
    ]
    
    for q_id in question_ids:
        # Add slight variation to features
        features = {k: v * (1 + (hash(q_id) % 10 - 5) * 0.01) for k, v in mock_acoustic_features.items()}
        state.acoustic_features[q_id] = features
        logger.info(f"   ✅ Added {len(features)} acoustic features for {q_id}")
    
    logger.info(f"✅ Total acoustic features: {len(state.acoustic_features)} questions")
    
    # ✅ STEP 2: Add mock linguistic features
    logger.info("\n📝 Adding mock linguistic features...")
    
    mock_linguistic_features = {
        'TTR': 0.68,  # Type-Token Ratio
        'MATTR': 0.72,  # Moving Average Type-Token Ratio
        'word_count': 245,
        'unique_words': 156,
        'pronoun_ratio': 0.18,
        'concrete_noun_rate': 0.42,
        'MLU': 8.5,  # Mean Length of Utterance
        'incomplete_sentence_ratio': 0.08,
        'semantic_coherence': 0.75,
        'idea_density': 0.62,
        'function_word_ratio': 0.35,
        'content_word_ratio': 0.65,
        'sentence_count': 28,
        'average_sentence_length': 8.75
    }
    
    state.linguistic_features = mock_linguistic_features
    logger.info(f"✅ Added {len(mock_linguistic_features)} linguistic features")
    
    # ✅ STEP 3: Add domain scores
    logger.info("\n📊 Adding domain scores...")
    
    state.domain_scores = {
        'orientation': 8,
        'registration': 3,
        'attention_calculation': 4,
        'recall': 2,
        'language': 6,
        'visuospatial': 2,
        'executive_function': 2
    }
    
    state.total_score = sum(state.domain_scores.values())
    logger.info(f"✅ Total MMSE score: {state.total_score}/35")
    
    # ✅ STEP 4: Add question scores
    logger.info("\n📋 Adding question scores...")
    
    state.question_scores = {
        'ori_time_weekday': 3,
        'ori_time_date': 2,
        'ori_location': 3,
        'reg_01': 3,
        'attn_serial_sub': 4,
        'recall_01': 2,
        'lang_repetition': 1,
        'lang_comprehension_3step': 2,
        'lang_comprehension_listening': 1,
        'lang_sentence_production': 1,
        'exec_verbal_fluency': 1,
        'vis_clock_drawing': 2
    }
    
    logger.info(f"✅ Added {len(state.question_scores)} question scores")
    
    # ✅ STEP 5: Calculate multimodal risk
    logger.info("\n🧬 Calculating multimodal risk...")
    
    # Aggregate acoustic features
    all_acoustic = {}
    for q_id, features in state.acoustic_features.items():
        for key, value in features.items():
            if key not in all_acoustic:
                all_acoustic[key] = []
            if isinstance(value, (int, float)):
                all_acoustic[key].append(float(value))
    
    avg_acoustic = {
        k: sum(v) / len(v) if v else 0.0
        for k, v in all_acoustic.items()
    }
    
    # Calculate multimodal risk
    mmse_data = {
        'raw_score': float(state.total_score),
        'adjusted_score': 22.5,  # Mock adjusted score
        'education_years': user_info['education_years'],
        'age': user_info['age']
    }
    
    multimodal_result = calculate_multimodal_risk(
        mmse_data=mmse_data,
        acoustic_features=avg_acoustic,
        linguistic_features=state.linguistic_features
    )
    
    # Store MCI result
    state.mci_result = {
        'version': 'v2.1',
        'raw_mmse_score': mmse_data['raw_score'],
        'adjusted_mmse_score': mmse_data['adjusted_score'],
        'age_penalty': 3.0,
        'education_bonus': 1.0,
        'education_group': 'medium_education',
        'acoustic_feature_count': len(avg_acoustic),
        'linguistic_feature_count': len(state.linguistic_features),
        'combined_risk_score': multimodal_result.combined_risk_score,
        'risk_level': multimodal_result.risk_level,
        'risk_components': {
            'mmse': multimodal_result.mmse_risk_score,
            'acoustic': multimodal_result.acoustic_risk_score,
            'linguistic': multimodal_result.linguistic_risk_score
        },
        'risk_weights': {
            'mmse': 0.3,
            'acoustic': 0.3,
            'linguistic': 0.4
        }
    }
    
    logger.info(f"✅ Multimodal risk calculated:")
    logger.info(f"   - Combined risk: {multimodal_result.combined_risk_score:.3f}")
    logger.info(f"   - Risk level: {multimodal_result.risk_level}")
    
    # ✅ STEP 6: Set completion
    state.completed_at = datetime.now().isoformat()
    state.current_domain = TestDomain.COMPLETED
    
    # ✅ CRITICAL: The state is already stored when we created the session
    # All modifications to state are done in-place, so the service already has the updated state
    # No need to manually save - the state object is the same reference
    logger.info("✅ Session state updated (in-place modifications)")
    
    logger.info("\n" + "=" * 80)
    logger.info("✅ Test session created successfully!")
    logger.info("=" * 80)
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Total Score: {state.total_score}/35")
    logger.info(f"Acoustic Features: {len(state.acoustic_features)} questions")
    logger.info(f"Linguistic Features: {len(state.linguistic_features)} features")
    logger.info(f"Risk Level: {state.mci_result['risk_level']}")
    
    return session_id, state


def generate_and_save_results(session_id: str, state: SessionState):
    """Generate comprehensive results and save to file"""
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 Generating comprehensive results...")
    logger.info("=" * 80)
    
    try:
        # Generate SHAP explanations
        shap_explanations = None
        if state.mci_result:
            shap_explanations = {
                'feature_contributions': {},
                'grouped_contributions': state.mci_result.get('risk_components', {})
            }
        
        # Generate comprehensive results
        comprehensive_results = generate_comprehensive_results(
            session_state=state,
            shap_explanations=shap_explanations
        )
        
        logger.info("✅ Comprehensive results generated!")
        logger.info(f"   Sections: {list(comprehensive_results.keys())}")
        
        # Check multimodal_analysis
        if 'multimodal_analysis' in comprehensive_results:
            ma = comprehensive_results['multimodal_analysis']
            logger.info(f"   Multimodal Analysis:")
            logger.info(f"      - Acoustic features: {len(ma.get('acoustic_features', {}))}")
            logger.info(f"      - Linguistic features: {len(ma.get('linguistic_features', {}))}")
            logger.info(f"      - Combined risk: {ma.get('combined_risk_score', 'N/A')}")
        
        # Check detailed_analysis
        if 'detailed_analysis' in comprehensive_results:
            da = comprehensive_results['detailed_analysis']
            logger.info(f"   Detailed Analysis:")
            logger.info(f"      - Acoustic: {len(da.get('acoustic', {}))}")
            logger.info(f"      - Linguistic: {len(da.get('linguistic', {}))}")
        
        # Check SHAP
        if 'shap_explanation' in comprehensive_results:
            se = comprehensive_results['shap_explanation']
            logger.info(f"   SHAP Explanation:")
            logger.info(f"      - Risk factors: {len(se.get('top_risk_factors', []))}")
            logger.info(f"      - Protective factors: {len(se.get('top_protective_factors', []))}")
        
        # Save to file
        output_file = backend_path / f"test_comprehensive_results_{session_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        
        # Also save a summary
        summary_file = backend_path / f"test_comprehensive_summary_{session_id}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("COMPREHENSIVE RESULTS SUMMARY\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Session ID: {session_id}\n")
            f.write(f"Total Score: {state.total_score}/35\n")
            f.write(f"Risk Level: {state.mci_result['risk_level']}\n")
            f.write(f"Combined Risk: {state.mci_result['combined_risk_score']:.3f}\n\n")
            
            f.write("Sections in comprehensive_results:\n")
            for section in comprehensive_results.keys():
                f.write(f"  - {section}\n")
            
            f.write("\n" + "=" * 80 + "\n")
            f.write("MULTIMODAL ANALYSIS\n")
            f.write("=" * 80 + "\n")
            if 'multimodal_analysis' in comprehensive_results:
                ma = comprehensive_results['multimodal_analysis']
                f.write(f"Acoustic Features: {len(ma.get('acoustic_features', {}))}\n")
                f.write(f"Linguistic Features: {len(ma.get('linguistic_features', {}))}\n")
                f.write(f"Combined Risk Score: {ma.get('combined_risk_score', 'N/A')}\n")
                f.write(f"Risk Level: {ma.get('risk_level', 'N/A')}\n")
        
        logger.info(f"✅ Summary saved to: {summary_file}")
        
        return comprehensive_results
        
    except Exception as e:
        logger.error(f"❌ Error generating comprehensive results: {e}", exc_info=True)
        return None


def main():
    """Main function"""
    try:
        # Create test session
        result = create_test_session_with_features()
        if not result:
            logger.error("❌ Failed to create test session")
            return
        
        session_id, state = result
        
        # Generate comprehensive results
        comprehensive_results = generate_and_save_results(session_id, state)
        
        if comprehensive_results:
            logger.info("\n" + "=" * 80)
            logger.info("✅ TEST COMPLETE!")
            logger.info("=" * 80)
            logger.info(f"\n📁 Check the output files:")
            logger.info(f"   - test_comprehensive_results_{session_id}.json")
            logger.info(f"   - test_comprehensive_summary_{session_id}.txt")
            logger.info(f"\n🔍 You can also query the API:")
            logger.info(f"   GET /api/mmse/chatbot/results/{session_id}")
        else:
            logger.error("❌ Failed to generate comprehensive results")
            
    except Exception as e:
        logger.error(f"❌ Error in main: {e}", exc_info=True)


if __name__ == '__main__':
    main()

