# Copy Original MMSE Chatbot Structure to V2

## Strategy

Since original file is large (~2200 lines), we'll:
1. Copy the original page.tsx directly as base
2. Update imports to use new structure
3. Keep all functionality intact

## Steps

1. Copy frontend/app/(main)/mmse-chatbot/page.tsx → frontend/app/(main)/mmse-chatbot-v2/page.tsx
2. Update imports to use existing components (they're already in the right place)
3. Test that it works

This is better than recreating from scratch since the original has all the logic we need.

