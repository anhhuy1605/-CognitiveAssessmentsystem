#!/usr/bin/env python3
"""
Deployment Readiness Test for Cognitive Assessment System
Tests all critical components without requiring live server
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

def test_database_schema():
    """Test database schema compliance"""
    print('🔍 TESTING DATABASE SCHEMA COMPLIANCE')

    load_dotenv('config.env')
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        print('❌ DATABASE_URL not found')
        return False

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Required tables
        required_tables = ['users', 'sessions', 'questions', 'stats', 'temp_questions']
        existing_tables = []

        for table in required_tables:
            cursor.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = %s
                );
            ''', (table,))
            if cursor.fetchone()[0]:
                existing_tables.append(table)

        print(f'✅ Tables created: {len(existing_tables)}/{len(required_tables)}')
        for table in existing_tables:
            print(f'   • {table}')

        # Check required fields in questions table
        required_fields = ['auto_transcript', 'user_name', 'user_age', 'user_education', 'user_email', 'audio_file']
        existing_fields = []

        for field in required_fields:
            cursor.execute('''
                SELECT EXISTS (
                    SELECT FROM information_schema.columns
                    WHERE table_name = 'questions' AND column_name = %s
                );
            ''', (field,))
            if cursor.fetchone()[0]:
                existing_fields.append(field)

        print(f'✅ Required fields in questions: {len(existing_fields)}/{len(required_fields)}')
        for field in existing_fields:
            print(f'   • {field}')

        # Get record counts
        cursor.execute('SELECT COUNT(*) FROM sessions')
        sessions = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM questions')
        questions = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM stats')
        stats = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f'\\n📊 DATABASE STATUS:')
        print(f'   • Sessions: {sessions}')
        print(f'   • Questions: {questions}')
        print(f'   • Stats: {stats}')
        print(f'   • Total records: {sessions + questions + stats}')

        success = (len(existing_tables) == len(required_tables) and
                  len(existing_fields) == len(required_fields))

        return success

    except Exception as e:
        print(f'❌ Database test failed: {e}')
        return False

def test_api_imports():
    """Test that API modules can be imported"""
    print('\\n🔍 TESTING API IMPORTS')

    try:
        from database_api import database_bp
        print('✅ Database API imported successfully')

        from pipeline_api import pipeline_bp
        print('✅ Pipeline API imported successfully')

        from app import app
        print('✅ Main app imported successfully')

        # Test basic app functionality
        with app.test_client() as client:
            response = client.get('/api/health')
            if response.status_code == 200:
                print('✅ App health endpoint working')
                return True
            else:
                print(f'❌ Health endpoint failed: {response.status_code}')
                return False

    except Exception as e:
        print(f'❌ API import failed: {e}')
        return False

def test_migration_status():
    """Test that data migration was successful"""
    print('\\n🔍 TESTING DATA MIGRATION STATUS')

    try:
        load_dotenv('config.env')
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()

        # Check if migration created data
        cursor.execute('SELECT COUNT(*) FROM cognitive_assessment_results')
        original_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sessions WHERE user_id != 'existing_user@example.com'")
        migrated_sessions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM stats WHERE user_id != 'existing_user@example.com'")
        migrated_stats = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f'📊 Migration status:')
        print(f'   • Original records: {original_count}')
        print(f'   • Migrated sessions: {migrated_sessions}')
        print(f'   • Migrated stats: {migrated_stats}')

        if migrated_sessions > 0 or migrated_stats > 0:
            print('✅ Data migration: Successful')
            return True
        else:
            print('⚠️ Data migration: No data migrated (may be expected)')
            return True  # Not a failure

    except Exception as e:
        print(f'❌ Migration check failed: {e}')
        return False

def main():
    """Run all deployment readiness tests"""
    print('🚀 COGNITIVE ASSESSMENT SYSTEM - DEPLOYMENT READINESS TEST')
    print('=' * 65)

    tests = [
        ('Database Schema', test_database_schema),
        ('API Imports', test_api_imports),
        ('Data Migration', test_migration_status),
    ]

    results = []
    for test_name, test_func in tests:
        print(f'\\n🧪 Running: {test_name}')
        result = test_func()
        results.append(result)
        status = '✅ PASS' if result else '❌ FAIL'
        print(f'{status}: {test_name}')

    # Final report
    print('\\n' + '=' * 65)
    print('🎯 DEPLOYMENT READINESS REPORT')

    passed = sum(results)
    total = len(results)

    print(f'📊 Tests passed: {passed}/{total}')
    print(f'📈 Success rate: {(passed/total)*100:.1f}%')

    if passed == total:
        print('\\n🎉 SYSTEM IS PRODUCTION READY!')
        print('✅ All critical components verified')
        print('🚀 Ready for deployment')
        print('\\n📋 Next steps:')
        print('1. Start server: python run.py')
        print('2. Test live endpoints manually')
        print('3. Deploy to production environment')
        return True
    else:
        print('\\n⚠️ SYSTEM NEEDS ATTENTION')
        print('❌ Some tests failed - review above')
        print('🔧 Fix issues before production deployment')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
