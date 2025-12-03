// scripts/test-transcribe.js - Test script for transcription API

const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const fetch = require('node-fetch');

// Configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_APP_URL || 'http://localhost:3000';
const TRANSCRIBE_ENDPOINT = `${API_BASE_URL}/api/transcribe`;

// Test function
async function testTranscribeAPI() {
  console.log('🧪 Testing Transcribe API...\n');
  
  try {
    // Step 1: Check API status
    console.log('1️⃣ Checking API status...');
    const statusResponse = await fetch(TRANSCRIBE_ENDPOINT);
    const statusData = await statusResponse.json();
    
    console.log('📊 API Status:', {
      status: statusData.status,
      service: statusData.service,
      apiKeyConfigured: statusData.apiKey?.configured,
      apiKeyStatus: statusData.apiKey?.status,
      method: statusData.usage?.method
    });
    
    if (!statusData.apiKey?.configured) {
      console.log('⚠️  OpenAI API key not configured - will use fallback mode');
    }
    
    if (statusData.apiKey?.status !== 'valid' && statusData.apiKey?.configured) {
      console.log('❌ OpenAI API key is configured but invalid');
    }
    
    console.log('\n2️⃣ Testing with sample audio file...');
    
    // Step 2: Create a test audio file (you can replace this with actual file)
    const testAudioPath = createTestAudioFile();
    
    if (!fs.existsSync(testAudioPath)) {
      console.log('❌ No test audio file found. Please provide a test file.');
      console.log('💡 Place an audio file (wav, mp3, webm) in the project root as "test-audio.wav"');
      return;
    }
    
    // Step 3: Test transcription
    const formData = new FormData();
    formData.append('audio', fs.createReadStream(testAudioPath));
    
    console.log('📁 Uploading audio file:', {
      file: path.basename(testAudioPath),
      size: `${Math.round(fs.statSync(testAudioPath).size / 1024)}KB`
    });
    
    const transcribeResponse = await fetch(TRANSCRIBE_ENDPOINT, {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders()
    });
    
    const transcribeData = await transcribeResponse.json();
    
    console.log('\n📝 Transcription Result:');
    console.log('Success:', transcribeData.success);
    
    if (transcribeData.success) {
      console.log('Method:', transcribeData.processingInfo?.method);
      console.log('Cost:', transcribeData.processingInfo?.cost ? `$${transcribeData.processingInfo.cost.toFixed(4)}` : 'Free');
      console.log('Transcription:', transcribeData.transcription);
      console.log('Audio Info:', transcribeData.audioInfo);
    } else {
      console.log('❌ Error:', transcribeData.error);
      console.log('Details:', transcribeData.details);
    }
    
    // Cleanup
    if (testAudioPath.includes('test-sample')) {
      fs.unlinkSync(testAudioPath);
    }
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    console.log('\n🔧 Troubleshooting:');
    console.log('1. Make sure the Next.js server is running (npm run dev)');
    console.log('2. Check if .env.local contains OPENAI_API_KEY');
    console.log('3. Verify API endpoint is accessible');
  }
}

// Create a dummy test file (you should replace with real audio file)
function createTestAudioFile() {
  const realTestFile = path.join(process.cwd(), 'test-audio.wav');
  if (fs.existsSync(realTestFile)) {
    return realTestFile;
  }
  
  const realTestFile2 = path.join(process.cwd(), 'test-audio.mp3');
  if (fs.existsSync(realTestFile2)) {
    return realTestFile2;
  }
  
  const realTestFile3 = path.join(process.cwd(), 'test-audio.webm');
  if (fs.existsSync(realTestFile3)) {
    return realTestFile3;
  }
  
  // Create a dummy file for testing (not a real audio file)
  const dummyFile = path.join(process.cwd(), 'test-sample.webm');
  const dummyData = Buffer.from('RIFF....WEBM', 'ascii'); // Minimal dummy data
  fs.writeFileSync(dummyFile, dummyData);
  
  console.log('ℹ️  Created dummy test file (not real audio)');
  return dummyFile;
}

// Performance test
async function performanceTest() {
  console.log('\n🏃‍♂️ Performance Test...');
  
  const start = typeof window !== 'undefined' ? Date.now() : 0;
  await testTranscribeAPI();
  const duration = typeof window !== 'undefined' ? (Date.now() - start) : 0;
  
  console.log(`\n⏱️  Total test duration: ${duration}ms`);
}

// Run the test
if (require.main === module) {
  performanceTest().catch(console.error);
}

module.exports = { testTranscribeAPI };


