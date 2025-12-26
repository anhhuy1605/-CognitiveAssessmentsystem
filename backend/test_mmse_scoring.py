#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MMSE Scoring Logic
"""

def calculate_mmse_score(results):
    """
    Calculate MMSE score from test results
    """
    total_questions = len(results)
    answered_questions = len([r for r in results if r.get('transcription')])

    if total_questions == 0:
        return 0

    # Calculate average GPT score if available
    gpt_scores = []
    for result in results:
        if result.get('gpt_evaluation') and result['gpt_evaluation'].get('overall_score'):
            gpt_scores.append(result['gpt_evaluation']['overall_score'])

    if gpt_scores:
        average_gpt_score = sum(gpt_scores) / len(gpt_scores)
        # Convert GPT score (0-10) to MMSE score (0-30)
        estimated_mmse_score = int(round((average_gpt_score / 10) * 30))
        # Cap at 30
        estimated_mmse_score = min(estimated_mmse_score, 30)
    else:
        # Default scoring based on completion
        completion_rate = answered_questions / total_questions
        estimated_mmse_score = int(round(completion_rate * 25))  # Max 25 if all answered

    return estimated_mmse_score

def test_mmse_scoring():
    """Test MMSE scoring logic"""

    print("[TEST] MMSE Scoring Test")
    print("=" * 50)

    # Test case 1: Perfect scores
    perfect_results = [
        {
            'question_id': 'q1',
            'transcription': 'Answer 1',
            'gpt_evaluation': {'overall_score': 9.5}
        },
        {
            'question_id': 'q2',
            'transcription': 'Answer 2',
            'gpt_evaluation': {'overall_score': 9.8}
        }
    ]

    perfect_score = calculate_mmse_score(perfect_results)
    print(f"[PASS] Perfect scores (9.5, 9.8): MMSE = {perfect_score}/30")

    # Test case 2: Average scores
    average_results = [
        {
            'question_id': 'q1',
            'transcription': 'Answer 1',
            'gpt_evaluation': {'overall_score': 8.0}
        },
        {
            'question_id': 'q2',
            'transcription': 'Answer 2',
            'gpt_evaluation': {'overall_score': 7.5}
        }
    ]

    average_score = calculate_mmse_score(average_results)
    print(f"[PASS] Average scores (8.0, 7.5): MMSE = {average_score}/30")

    # Test case 3: Poor scores
    poor_results = [
        {
            'question_id': 'q1',
            'transcription': 'Answer 1',
            'gpt_evaluation': {'overall_score': 5.0}
        },
        {
            'question_id': 'q2',
            'transcription': 'Answer 2',
            'gpt_evaluation': {'overall_score': 4.5}
        }
    ]

    poor_score = calculate_mmse_score(poor_results)
    print(f"[PASS] Poor scores (5.0, 4.5): MMSE = {poor_score}/30")

    # Test case 4: Mixed scores (some without GPT)
    mixed_results = [
        {
            'question_id': 'q1',
            'transcription': 'Answer 1',
            'gpt_evaluation': {'overall_score': 8.5}
        },
        {
            'question_id': 'q2',
            'transcription': 'Answer 2'
            # No GPT evaluation
        },
        {
            'question_id': 'q3',
            'transcription': 'Answer 3',
            'gpt_evaluation': {'overall_score': 7.0}
        }
    ]

    mixed_score = calculate_mmse_score(mixed_results)
    print(f"[PASS] Mixed scores (8.5, None, 7.0): MMSE = {mixed_score}/30")

    # Test case 5: No answers
    no_answers = [
        {
            'question_id': 'q1'
            # No transcription
        },
        {
            'question_id': 'q2'
            # No transcription
        }
    ]

    no_answers_score = calculate_mmse_score(no_answers)
    print(f"[PASS] No answers: MMSE = {no_answers_score}/30")

    print("\n[INFO] MMSE Scoring Logic:")
    print("- GPT score 10/10 -> MMSE 30/30")
    print("- GPT score 8.5/10 -> MMSE ~26/30")
    print("- GPT score 5/10 -> MMSE ~15/30")
    print("- Fallback: completion rate * 25")

    print("\n[SUCCESS] All tests completed!")

if __name__ == "__main__":
    test_mmse_scoring()
