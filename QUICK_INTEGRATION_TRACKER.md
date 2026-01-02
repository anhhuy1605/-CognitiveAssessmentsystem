# Quick Integration - Question Tracker

## 🚀 2-Step Integration

### Step 1: Update Import (1 line)

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

```typescript
// Replace this:
import ChatInterface from '@/components/mmse-chatbot/ChatInterface';

// With this:
import ChatInterfaceWithTracker from '@/components/mmse-chatbot/ChatInterfaceWithTracker';
```

### Step 2: Update Component (1 line)

**File**: `frontend/app/(main)/mmse-chatbot/page.tsx`

```typescript
// Replace this:
<ChatInterface

// With this:
<ChatInterfaceWithTracker
```

**✅ DONE!** Tracker will automatically handle the rest.

## 🎯 What This Does

- ✅ Automatically tracks current question from messages
- ✅ Only renders special interfaces for active question
- ✅ Hides previous question interfaces automatically
- ✅ No manual state management needed

## 🧪 Test

1. Complete test với special questions (Serial 7s, Clock Drawing, etc.)
2. ✅ Verify: Only current question's interface shows
3. ✅ Verify: Previous interfaces are hidden
4. ✅ Verify: Clock drawing modal only appears for clock question

**Xem chi tiết: INTEGRATION_QUESTION_TRACKER.md**

