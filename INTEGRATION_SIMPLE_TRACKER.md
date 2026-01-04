# Simple Question Tracker Integration

## 🎯 Simple Approach

Sử dụng utility function thay vì complex state management.

## 📋 Files

1. ✅ `frontend/utils/questionTracker.ts` - Simple utility functions
2. ✅ `frontend/hooks/useQuestionTracker.ts` - Full hook (optional)
3. ✅ `frontend/components/mmse-chatbot/ChatInterfaceWithTracker.tsx` - Enhanced component

## 🔧 Simple Integration

### Option 1: Use Utility Function (Recommended)

**File**: `frontend/components/mmse-chatbot/ChatInterface.tsx`

**Add import:**
```typescript
import { getCurrentQuestion, isQuestionActive } from '@/utils/questionTracker';
```

**In message rendering, use:**
```typescript
const currentQuestion = getCurrentQuestion(messages);

// When rendering QuestionTypeRenderer:
{message.type === "bot" && message.questionId && message.questionCategory &&
 requiresSpecialInterface(message.questionId, message.questionCategory) &&
 isQuestionActive(message.questionId, currentQuestion) && (
  <QuestionTypeRenderer
    questionId={message.questionId}
    ...
  />
)}
```

### Option 2: Use ChatInterfaceWithTracker (Full Solution)

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

**Replace:**
```typescript
// OLD
import ChatInterface from '@/components/mmse-chatbot/ChatInterface';

// NEW
import ChatInterfaceWithTracker from '@/components/mmse-chatbot/ChatInterfaceWithTracker';
```

**And:**
```typescript
// OLD
<ChatInterface ... />

// NEW
<ChatInterfaceWithTracker ... />
```

## ✅ Benefits of Simple Approach

- ✅ No context provider needed
- ✅ No state management overhead
- ✅ Direct function calls
- ✅ Easy to understand
- ✅ Works with existing code

## 🚀 Recommendation

**Use Option 1** (utility functions) if you want:
- Simple integration
- No breaking changes
- Minimal code changes

**Use Option 2** (ChatInterfaceWithTracker) if you want:
- Automatic tracking
- Context-based solution
- Future extensibility





