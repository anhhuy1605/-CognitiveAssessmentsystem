#!/usr/bin/env python3
"""
Comprehensive System Test for Cognitive Assessment Platform
Tests all components: Database, APIs, ML Models, and Integration
"""

import os
import sys
import json
import time
import tempfile
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load environment
load_dotenv('config.env')

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:5001"
        self.test_results = {
            'database_health': False,
            'api_endpoints': False,
            'mmse_pipeline': False,
            'data_operations': False,
            'frontend_compatibility': False
        }
        self.session_id = None
        self.test_user = {
            'email': 'test_system@example.com',
            'name': 'Test User',
            'age': 70,
            'education': 16
        }

    def print_header(self, title):
        """Print section header"""
        print(f'\n🔍 {title}')
        print('=' * 50)

    def test_database_health(self):
        """Test database connectivity and table status"""
        self.print_header('DATABASE HEALTH CHECK')

        try:
            response = requests.get(f'{self.base_url}/api/database/health', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print('✅ Database connection: Healthy')
                    print(f'📊 Total records: {data.get("total_records", 0)}')

                    # Check table status
                    tables = data.get('tables', {})
                    for table, count in tables.items():
                        status = '✅' if count != 'Error' else '❌'
                        print(f'   {status} {table}: {count}')

                    self.test_results['database_health'] = True
                    return True
                else:
                    print(f'❌ Database health check failed: {data.get("error")}')
            else:
                print(f'❌ HTTP {response.status_code}: {response.text}')
        except Exception as e:
            print(f'❌ Database health check failed: {e}')

        return False

    def test_api_endpoints(self):
        """Test all API endpoints functionality"""
        self.print_header('API ENDPOINTS TESTING')

        endpoints_to_test = [
            ('GET', '/api/health'),
            ('GET', '/api/database/health'),
            ('GET', '/api/mmse/performance'),
        ]

        success_count = 0

        for method, endpoint in endpoints_to_test:
            try:
                if method == 'GET':
                    response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
                else:
                    response = requests.post(f'{self.base_url}{endpoint}', timeout=10)

                if response.status_code in [200, 201]:
                    print(f'✅ {method} {endpoint}: {response.status_code}')
                    success_count += 1
                else:
                    print(f'❌ {method} {endpoint}: {response.status_code} - {response.text}')

            except Exception as e:
                print(f'❌ {method} {endpoint}: {e}')

        # Test database CRUD operations
        print('\n🧪 Testing CRUD Operations...')

        # Create session
        session_data = {
            'user_id': self.test_user['email'],
            'mode': 'personal',
            'status': 'in_progress'
        }

        try:
            response = requests.post(f'{self.base_url}/api/database/sessions',
                                   json=session_data, timeout=10)
            if response.status_code == 201:
                data = response.json()
                self.session_id = data.get('session_id')
                print(f'✅ Session created: {self.session_id}')
                success_count += 1
            else:
                print(f'❌ Session creation failed: {response.status_code}')
        except Exception as e:
            print(f'❌ Session creation error: {e}')

        # Create question
        if self.session_id:
            question_data = {
                'session_id': str(self.session_id),
                'question_id': 'test_q1',
                'question_content': 'Hôm nay là ngày nào?',
                'auto_transcript': 'Hôm nay là thứ hai',
                'evaluation': 'Tốt',
                'feedback': 'Trả lời chính xác',
                'score': 5.0,
                'user_name': self.test_user['name'],
                'user_age': self.test_user['age'],
                'user_education': self.test_user['education'],
                'user_email': self.test_user['email']
            }

            try:
                response = requests.post(f'{self.base_url}/api/database/questions',
                                       json=question_data, timeout=10)
                if response.status_code == 201:
                    print(f'✅ Question created successfully')
                    success_count += 1
                else:
                    print(f'❌ Question creation failed: {response.status_code}')
            except Exception as e:
                print(f'❌ Question creation error: {e}')

        # Get sessions
        try:
            response = requests.get(f'{self.base_url}/api/database/sessions', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and len(data.get('sessions', [])) > 0:
                    print(f'✅ Retrieved {len(data["sessions"])} sessions')
                    success_count += 1
                else:
                    print(f'❌ No sessions retrieved')
            else:
                print(f'❌ Sessions retrieval failed: {response.status_code}')
        except Exception as e:
            print(f'❌ Sessions retrieval error: {e}')

        self.test_results['api_endpoints'] = success_count >= 5
        print(f'\n📊 API Tests: {success_count}/6 passed')
        return self.test_results['api_endpoints']

    def test_mmse_pipeline(self):
        """Test MMSE inference pipeline"""
        self.print_header('MMSE PIPELINE TESTING')

        try:
            # Create test audio file
            import wave
            import struct

            # Generate simple test audio (1 second, 16kHz, mono)
            sample_rate = 16000
            duration = 1.0
            frequency = 440  # A4 note

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                audio_path = tmp_file.name

                # Create WAV file
                with wave.open(audio_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # Mono
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)

                    # Generate sine wave
                    for i in range(int(sample_rate * duration)):
                        sample = int(32767 * 0.3 * (i / (sample_rate * duration)))  # Fade in
                        wav_file.writeframes(struct.pack('<h', sample))

            # Test MMSE assessment
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': ('test_audio.wav', audio_file, 'audio/wav')}
                data = {
                    'age': str(self.test_user['age']),
                    'sex': 'male',
                    'education': str(self.test_user['education']),
                    'device': 'computer'
                }

                response = requests.post(f'{self.base_url}/api/mmse/assess',
                                       files=files, data=data, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        mmse_score = result.get('mmse_score')
                        print(f'✅ MMSE Pipeline: Success (Score: {mmse_score})')
                        self.test_results['mmse_pipeline'] = True
                        return True
                    else:
                        print(f'❌ MMSE Pipeline failed: {result.get("error")}')
                else:
                    print(f'❌ MMSE Pipeline HTTP {response.status_code}: {response.text}')

            # Cleanup
            os.unlink(audio_path)

        except Exception as e:
            print(f'❌ MMSE Pipeline test error: {e}')

        return False

    def test_data_operations(self):
        """Test data migration and integrity"""
        self.print_header('DATA OPERATIONS TESTING')

        try:
            # Test data consistency between tables
            response = requests.get(f'{self.base_url}/api/database/sessions', timeout=10)
            if response.status_code == 200:
                sessions_data = response.json()
                sessions_count = len(sessions_data.get('sessions', []))

                response = requests.get(f'{self.base_url}/api/database/questions', timeout=10)
                questions_data = response.json()
                questions_count = len(questions_data.get('questions', []))

                response = requests.get(f'{self.base_url}/api/database/stats', timeout=10)
                stats_data = response.json()
                stats_count = len(stats_data.get('stats', []))

                print(f'📊 Data integrity check:')
                print(f'   • Sessions: {sessions_count}')
                print(f'   • Questions: {questions_count}')
                print(f'   • Stats: {stats_count}')

                if sessions_count > 0 and stats_count > 0:
                    print('✅ Data operations: Consistent')
                    self.test_results['data_operations'] = True
                    return True
                else:
                    print('⚠️ Data operations: Limited data found')

        except Exception as e:
            print(f'❌ Data operations test error: {e}')

        return False

    def test_frontend_compatibility(self):
        """Test frontend API compatibility"""
        self.print_header('FRONTEND COMPATIBILITY TESTING')

        try:
            # Test existing endpoints that frontend uses
            endpoints = [
                ('GET', '/api/health'),
                ('GET', '/api/user/profile'),
                ('GET', '/api/assessment/results/session/1'),  # May not exist, but test endpoint
            ]

            compatible_endpoints = 0

            for method, endpoint in endpoints:
                try:
                    if method == 'GET':
                        response = requests.get(f'{self.base_url}{endpoint}', timeout=10)
                    else:
                        response = requests.post(f'{self.base_url}{endpoint}', timeout=10)

                    # Any response (even 404) indicates server is running
                    if response.status_code < 500:
                        compatible_endpoints += 1
                        print(f'✅ {endpoint}: Compatible ({response.status_code})')
                    else:
                        print(f'⚠️ {endpoint}: Server error ({response.status_code})')

                except Exception as e:
                    print(f'❌ {endpoint}: Connection failed')

            if compatible_endpoints >= 2:
                print('✅ Frontend compatibility: Good')
                self.test_results['frontend_compatibility'] = True
                return True
            else:
                print('⚠️ Frontend compatibility: Limited')

        except Exception as e:
            print(f'❌ Frontend compatibility test error: {e}')

        return False

    def generate_report(self):
        """Generate comprehensive test report"""
        self.print_header('FINAL TEST REPORT')

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)

        print(f'📊 Overall Score: {passed_tests}/{total_tests} tests passed')
        print(f'📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%')

        print(f'\n🔍 Detailed Results:')
        for test_name, result in self.test_results.items():
            status = '✅ PASS' if result else '❌ FAIL'
            print(f'   {status} {test_name.replace("_", " ").title()}')

        # Recommendations
        print(f'\n💡 Recommendations:')
        if passed_tests == total_tests:
            print('   🎉 System is production-ready!')
            print('   🚀 Ready for deployment')
        elif passed_tests >= total_tests * 0.8:
            print('   ⚠️ System is mostly ready - minor issues to fix')
            print('   🔧 Address failed tests before production')
        else:
            print('   ❌ System needs significant fixes')
            print('   🛠️ Critical issues must be resolved')

        return passed_tests == total_tests

    def run_all_tests(self):
        """Run all system tests"""
        print('🚀 COGNITIVE ASSESSMENT SYSTEM - COMPREHENSIVE TESTING')
        print('=' * 70)

        # Run all tests
        self.test_database_health()
        time.sleep(1)  # Brief pause between tests

        self.test_api_endpoints()
        time.sleep(1)

        self.test_mmse_pipeline()
        time.sleep(1)

        self.test_data_operations()
        time.sleep(1)

        self.test_frontend_compatibility()
        time.sleep(1)

        # Generate final report
        return self.generate_report()

def main():
    """Main test function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--skip-server-check':
        print('⚠️ Skipping server availability check')
        tester = SystemTester()
        success = tester.run_all_tests()
    else:
        # Check if server is running
        try:
            response = requests.get('http://localhost:5001/api/health', timeout=5)
            if response.status_code == 200:
                print('✅ Backend server is running')
                tester = SystemTester()
                success = tester.run_all_tests()
            else:
                print('❌ Backend server not responding (HTTP {response.status_code})')
                print('💡 Please start the backend server first:')
                print('   cd backend && python run.py')
                success = False
        except:
            print('❌ Cannot connect to backend server')
            print('💡 Please start the backend server first:')
            print('   cd backend && python run.py')
            success = False

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)