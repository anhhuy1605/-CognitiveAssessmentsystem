// INTEGRATION CODE for mmse-chatbot/page.tsx
// ===========================================
// Replace ChatInterface với ChatInterfaceWithTracker

// 1. Update import:
// OLD:
// import ChatInterface from '@/components/mmse-chatbot/ChatInterface';

// NEW:
import ChatInterfaceWithTracker from '@/components/mmse-chatbot/ChatInterfaceWithTracker';

// 2. In return statement, replace:
// OLD:
// <ChatInterface
//   messages={session.messages}
//   ...
// />

// NEW:
<ChatInterfaceWithTracker
  messages={session.messages}
  currentTranscript={currentTranscript}
  isRecording={isRecording}
  isProcessing={isProcessing}
  voiceEnabled={voiceEnabled}
  onSendMessage={handleUserInput}
  onStartRecording={startRecording}
  onStopRecording={stopRecording}
  onFileUpload={handleFileUpload}
  onToggleVoice={toggleVoice}
  elderlyFriendly={true}
/>

// ✅ That's it! Tracker will automatically sync with messages
// and render special interfaces only when questions are active

