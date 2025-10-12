#!/usr/bin/env python3
"""
Test script to verify database tables and required fields are working correctly
"""

import os
import psycopg2
from dotenv import load_dotenv

def test_database_tables():
    """Test that all required tables and fields exist"""

    # Load environment
    load_dotenv('config.env')
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print('❌ DATABASE_URL not found')
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        print('🧪 Testing Database Tables and Required Fields')
        print('=' * 50)

        # Required fields to check
        required_fields = {
            'questions': ['auto_transcript', 'user_name', 'user_age', 'user_education', 'user_email', 'audio_file'],
            'temp_questions': ['auto_transcript', 'user_name', 'user_age', 'user_education', 'user_email', 'audio_file'],
            'stats': ['user_name', 'user_age', 'user_education', 'user_email'],
            'sessions': []  # Sessions gets user info from users table
        }

        success = True

        for table, fields in required_fields.items():
            print(f'\n📋 Testing table: {table}')

            # Check if table exists
            cursor.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            ''', (table,))

            if not cursor.fetchone()[0]:
                print(f'❌ Table {table} does not exist')
                success = False
                continue

            print(f'✅ Table {table} exists')

            # Check required fields
            for field in fields:
                cursor.execute('''
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_name = %s AND column_name = %s
                    );
                ''', (table, field))

                if cursor.fetchone()[0]:
                    print(f'   ✅ Field {field} exists')
                else:
                    print(f'   ❌ Field {field} missing')
                    success = False

        # Test inserting sample data
        print(f'\n🧪 Testing data insertion...')

        # Insert sample session (using existing user email)
        cursor.execute('''
            INSERT INTO sessions (user_id, mode, status, mmse_score, cognitive_level)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        ''', ('existing_user@example.com', 'personal', 'completed', 25, 'normal'))

        session_result = cursor.fetchone()
        session_id = session_result[0] if session_result else None

        if session_id:
            # Insert sample question with all required fields
            cursor.execute('''
                INSERT INTO questions (
                    session_id, question_id, question_content, audio_file,
                    auto_transcript, user_name, user_age, user_education, user_email, score
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            ''', (
                str(session_id), 'q1', 'Hôm nay là ngày nào?',
                '/audio/test.wav', 'Hôm nay là thứ hai',
                'Nguyễn Văn Test', 70, 16, 'test@example.com', 5.0
            ))

            # Insert sample temp question
            cursor.execute('''
                INSERT INTO temp_questions (
                    session_id, question_id, question_content, audio_file,
                    auto_transcript, user_name, user_age, user_education, user_email
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            ''', (
                str(session_id), 'temp_q1', 'Câu hỏi tạm thời',
                '/audio/temp.wav', 'Transcript tạm thời',
                'Nguyễn Văn Test', 70, 16, 'test@example.com'
            ))

            # Insert sample stats
            cursor.execute('''
                INSERT INTO stats (
                    session_id, user_id, mode, summary,
                    user_name, user_age, user_education, user_email, audio_files
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            ''', (
                str(session_id), 'test@example.com', 'personal',
                '{"total_score": 25, "mmse_score": 25}',
                'Nguyễn Văn Test', 70, 16, 'test@example.com',
                '["/audio/q1.wav", "/audio/q2.wav"]'
            ))

            print('✅ Sample data inserted successfully')

            # Verify data
            cursor.execute('SELECT COUNT(*) FROM questions WHERE session_id = %s;', (str(session_id),))
            q_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM temp_questions WHERE session_id = %s;', (str(session_id),))
            tq_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM stats WHERE session_id = %s;', (str(session_id),))
            s_count = cursor.fetchone()[0]

            print(f'✅ Verification: {q_count} questions, {tq_count} temp questions, {s_count} stats records')

        conn.commit()

        cursor.close()
        conn.close()

        if success:
            print(f'\n🎉 ALL TESTS PASSED!')
            print('✅ Database schema is complete and functional')
            return True
        else:
            print(f'\n❌ SOME TESTS FAILED!')
            return False

    except Exception as e:
        print(f'❌ Database test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_database_tables()
    exit(0 if success else 1)
