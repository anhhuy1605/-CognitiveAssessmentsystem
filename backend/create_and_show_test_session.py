#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Test Session and Show Session ID for Viewing
====================================================
Creates a test session and displays the URL to view it
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from test_comprehensive_results import create_test_session_with_features, generate_and_save_results
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Create test session and show viewing URL"""
    try:
        logger.info("=" * 80)
        logger.info("🧪 Creating test session with comprehensive results...")
        logger.info("=" * 80)
        
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
            logger.info("✅ TEST SESSION CREATED SUCCESSFULLY!")
            logger.info("=" * 80)
            logger.info(f"\n📊 Session ID: {session_id}")
            logger.info(f"📁 Results saved to: test_comprehensive_results_{session_id}.json")
            logger.info(f"\n🌐 To view on frontend page:")
            logger.info(f"   http://localhost:3000/results/comprehensive?sessionId={session_id}")
            logger.info(f"\n📋 Session Summary:")
            logger.info(f"   - Total Score: {state.total_score}/35")
            logger.info(f"   - Acoustic Features: {len(state.acoustic_features)} questions")
            logger.info(f"   - Linguistic Features: {len(state.linguistic_features)} features")
            logger.info(f"   - Risk Level: {state.mci_result['risk_level'] if state.mci_result else 'N/A'}")
            logger.info(f"   - Combined Risk: {state.mci_result['combined_risk_score'] if state.mci_result else 'N/A'}")
            logger.info(f"\n✅ Session is ready to view!")
            logger.info("=" * 80)
        else:
            logger.error("❌ Failed to generate comprehensive results")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)

if __name__ == '__main__':
    main()

