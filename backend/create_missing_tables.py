#!/usr/bin/env python3
"""
Script to create missing database tables for Cognitive Assessment System
Ensures all required fields are present: autotranscribe, user name, age, education, email, audio files
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_missing_tables():
    """Create all missing tables with required fields"""

    # Load environment variables
    load_dotenv('config.env')
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print('❌ DATABASE_URL not found in config.env')
        return False

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        print('🔧 Creating missing database tables...')

        # 1. Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id TEXT,
                mode VARCHAR(20) NOT NULL DEFAULT 'personal'
                    CHECK (mode IN ('personal', 'community')),
                status VARCHAR(20) DEFAULT 'in_progress'
                    CHECK (status IN ('in_progress', 'completed', 'error')),
                start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                end_time TIMESTAMP WITH TIME ZONE,
                total_score REAL,
                mmse_score INTEGER,
                cognitive_level VARCHAR(20)
                    CHECK (cognitive_level IN ('mild', 'moderate', 'severe', 'normal')),
                email_sent INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        ''')
        print('✅ Created sessions table')

        # 2. Create questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_content TEXT NOT NULL,
                audio_file TEXT,
                auto_transcript TEXT,  -- autotranscribe field
                manual_transcript TEXT,
                linguistic_analysis JSONB,
                audio_features JSONB,
                evaluation TEXT,
                feedback TEXT,
                score REAL,
                processed_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                -- Additional user info fields
                user_name TEXT,        -- tên người dùng
                user_age INTEGER,      -- tuổi người dùng
                user_education INTEGER, -- số năm học
                user_email TEXT        -- email
            );
        ''')
        print('✅ Created questions table with user info fields')

        # 3. Create stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_id TEXT,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                mode VARCHAR(20) NOT NULL
                    CHECK (mode IN ('personal', 'community')),
                summary JSONB,
                detailed_results JSONB,
                chart_data JSONB,
                exercise_recommendations JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

                -- Additional user info
                user_name TEXT,
                user_age INTEGER,
                user_education INTEGER,
                user_email TEXT,
                audio_files JSONB
            );
        ''')
        print('✅ Created stats table')

        # 4. Create temp_questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temp_questions (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_content TEXT NOT NULL,
                audio_file TEXT,       -- file ghi âm
                auto_transcript TEXT,  -- autotranscribe field
                raw_audio_features JSONB,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                expires_at TIMESTAMP WITH TIME ZONE,

                -- User information fields
                user_name TEXT,        -- tên người dùng
                user_age INTEGER,      -- tuổi người dùng
                user_education INTEGER, -- số năm học
                user_email TEXT        -- email
            );
        ''')
        print('✅ Created temp_questions table with user info fields')

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_mode ON sessions(mode);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_session_id ON questions(session_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_question_id ON questions(question_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_user_email ON questions(user_email);')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_session_id ON stats(session_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_user_id ON stats(user_id);')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_questions_session_id ON temp_questions(session_id);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_questions_status ON temp_questions(status);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_questions_expires_at ON temp_questions(expires_at);')

        print('✅ Created database indexes')

        # Verify table creation
        cursor.execute('''
            SELECT schemaname, tablename, tableowner
            FROM pg_tables
            WHERE schemaname = 'public' AND tablename IN ('sessions', 'questions', 'stats', 'temp_questions')
            ORDER BY tablename;
        ''')

        tables = cursor.fetchall()
        print('\n📋 VERIFICATION - Newly created tables:')
        print('=' * 40)

        for schema, table, owner in tables:
            print(f'✅ {table}')

            # Check table structure
            cursor.execute(f'''
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table}'
                ORDER BY ordinal_position;
            ''')

            columns = cursor.fetchall()
            print(f'   Columns: {len(columns)}')

            # Show key columns
            key_columns = [col[0] for col in columns if col[0] in
                          ['auto_transcript', 'user_name', 'user_age', 'user_education', 'user_email', 'audio_file']]
            if key_columns:
                print(f'   Key fields: {", ".join(key_columns)}')

        cursor.close()
        conn.close()

        print('\n🎉 SUCCESS: All missing tables created successfully!')
        return True

    except Exception as e:
        print(f'❌ Error creating tables: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_missing_tables()
    sys.exit(0 if success else 1)
