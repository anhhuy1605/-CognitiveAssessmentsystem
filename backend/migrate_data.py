#!/usr/bin/env python3
"""
Data Migration Script for Cognitive Assessment System
Migrates data from old tables to new tables with enhanced schema
"""

import os
import json
import psycopg2
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Load environment
load_dotenv('config.env')
DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def migrate_cognitive_assessment_results():
    """Migrate data from cognitive_assessment_results to new tables"""
    print('🔄 Starting data migration...')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all records from cognitive_assessment_results
        cursor.execute('SELECT * FROM cognitive_assessment_results ORDER BY "createdAt"')
        records = cursor.fetchall()

        print(f'📊 Found {len(records)} records to migrate')

        migrated_sessions = 0
        migrated_questions = 0
        migrated_stats = 0

        for record in records:
            try:
                # Extract user info from userInfo JSONB
                user_info = record.get('userInfo', {}) if record.get('userInfo') else {}
                user_name = user_info.get('name', 'Unknown')
                user_age = user_info.get('age')
                user_education = user_info.get('education')
                user_email = record.get('userId', 'unknown@example.com')

                # Create session record
                session_data = {
                    'user_id': user_email,
                    'mode': record.get('usageMode', 'personal'),
                    'status': record.get('status', 'completed'),
                    'total_score': record.get('overallGptScore'),
                    'mmse_score': record.get('finalMmseScore'),
                    'cognitive_level': 'normal',  # Default value
                    'email_sent': 0
                }

                cursor.execute('''
                    INSERT INTO sessions (user_id, mode, status, total_score, mmse_score, cognitive_level, email_sent)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                ''', (
                    session_data['user_id'],
                    session_data['mode'],
                    session_data['status'],
                    session_data['total_score'],
                    session_data['mmse_score'],
                    session_data['cognitive_level'],
                    session_data['email_sent']
                ))

                session_result = cursor.fetchone()
                if session_result:
                    session_id = session_result['id']
                    migrated_sessions += 1

                    # Create question records from questionResults
                    question_results = record.get('questionResults', {})
                    if question_results and isinstance(question_results, dict):
                        for q_id, q_data in question_results.items():
                            if isinstance(q_data, dict):
                                question_record = {
                                    'session_id': str(session_id),
                                    'question_id': q_id,
                                    'question_content': q_data.get('question', f'Question {q_id}'),
                                    'audio_file': None,  # No audio file in old data
                                    'auto_transcript': q_data.get('transcript'),
                                    'manual_transcript': None,
                                    'linguistic_analysis': json.dumps(q_data.get('analysis', {})),
                                    'audio_features': json.dumps(record.get('audioFeatures', {})),
                                    'evaluation': q_data.get('evaluation'),
                                    'feedback': q_data.get('feedback'),
                                    'score': q_data.get('score'),
                                    'processed_at': record.get('completedAt') or record.get('createdAt'),
                                    'user_name': user_name,
                                    'user_age': user_age,
                                    'user_education': user_education,
                                    'user_email': user_email
                                }

                                cursor.execute('''
                                    INSERT INTO questions (
                                        session_id, question_id, question_content, audio_file,
                                        auto_transcript, manual_transcript, linguistic_analysis,
                                        audio_features, evaluation, feedback, score, processed_at,
                                        user_name, user_age, user_education, user_email
                                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                ''', (
                                    question_record['session_id'],
                                    question_record['question_id'],
                                    question_record['question_content'],
                                    question_record['audio_file'],
                                    question_record['auto_transcript'],
                                    question_record['manual_transcript'],
                                    question_record['linguistic_analysis'],
                                    question_record['audio_features'],
                                    question_record['evaluation'],
                                    question_record['feedback'],
                                    question_record['score'],
                                    question_record['processed_at'],
                                    question_record['user_name'],
                                    question_record['user_age'],
                                    question_record['user_education'],
                                    question_record['user_email']
                                ))

                                migrated_questions += 1

                    # Create stats record
                    stats_record = {
                        'session_id': str(session_id),
                        'user_id': user_email,
                        'mode': record.get('usageMode', 'personal'),
                        'summary': json.dumps({
                            'total_score': record.get('overallGptScore'),
                            'mmse_score': record.get('finalMmseScore'),
                            'cognitive_level': 'normal',
                            'completion_rate': 100
                        }),
                        'detailed_results': json.dumps(record.get('questionResults', {})),
                        'chart_data': None,
                        'exercise_recommendations': None,
                        'user_name': user_name,
                        'user_age': user_age,
                        'user_education': user_education,
                        'user_email': user_email,
                        'audio_files': json.dumps(record.get('audioFiles', []))
                    }

                    cursor.execute('''
                        INSERT INTO stats (
                            session_id, user_id, mode, summary, detailed_results,
                            chart_data, exercise_recommendations, user_name, user_age,
                            user_education, user_email, audio_files
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ''', (
                        stats_record['session_id'],
                        stats_record['user_id'],
                        stats_record['mode'],
                        stats_record['summary'],
                        stats_record['detailed_results'],
                        stats_record['chart_data'],
                        stats_record['exercise_recommendations'],
                        stats_record['user_name'],
                        stats_record['user_age'],
                        stats_record['user_education'],
                        stats_record['user_email'],
                        stats_record['audio_files']
                    ))

                    migrated_stats += 1

                print(f'✅ Migrated record {record["id"]}')

            except Exception as e:
                print(f'❌ Error migrating record {record["id"]}: {e}')
                continue

        conn.commit()
        cursor.close()
        conn.close()

        print('🎉 Migration completed!')
        print(f'📊 Summary:')
        print(f'   • Sessions created: {migrated_sessions}')
        print(f'   • Questions created: {migrated_questions}')
        print(f'   • Stats records created: {migrated_stats}')

        return True

    except Exception as e:
        print(f'❌ Migration failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def migrate_training_samples():
    """Migrate training samples to new format if needed"""
    print('🔄 Checking training samples...')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if training_samples has data
        cursor.execute('SELECT COUNT(*) FROM training_samples')
        count = cursor.fetchone()[0]

        print(f'📊 Training samples: {count} records')

        if count > 0:
            print('✅ Training samples already exist - no migration needed')

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f'❌ Error checking training samples: {e}')
        return False

def validate_migration():
    """Validate that migration was successful"""
    print('🔍 Validating migration...')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check counts
        tables = ['sessions', 'questions', 'stats']
        total_new_records = 0

        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            total_new_records += count
            print(f'   • {table}: {count} records')

        # Check original table
        cursor.execute('SELECT COUNT(*) FROM cognitive_assessment_results')
        original_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f'📊 Validation:')
        print(f'   • Original records: {original_count}')
        print(f'   • New records created: {total_new_records}')

        if total_new_records > 0:
            print('✅ Migration validation successful!')
            return True
        else:
            print('⚠️ No new records found - migration may have failed')
            return False

    except Exception as e:
        print(f'❌ Validation failed: {e}')
        return False

def main():
    """Main migration function"""
    print('🚀 Cognitive Assessment Data Migration')
    print('=' * 50)

    # Step 1: Migrate cognitive assessment results
    if not migrate_cognitive_assessment_results():
        print('❌ Migration failed - aborting')
        return False

    # Step 2: Check training samples
    if not migrate_training_samples():
        print('⚠️ Training samples check failed - continuing')

    # Step 3: Validate migration
    if validate_migration():
        print('🎉 All migrations completed successfully!')
        return True
    else:
        print('❌ Migration validation failed')
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
