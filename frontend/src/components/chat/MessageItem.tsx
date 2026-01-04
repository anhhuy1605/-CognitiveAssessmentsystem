/**
 * MessageItem Component - Displays a single chat message
 */

import React from 'react';
import { ChatMessage } from '../../services/chatService';
import HiddenMessage from '../../components/ui/HiddenMessage';
import { User, Brain, CheckCircle } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
  elderlyFriendly?: boolean;
}

export default function MessageItem({ message, elderlyFriendly = true }: MessageItemProps) {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
      {/* Avatar */}
      <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-md ${
        isUser
          ? 'bg-gradient-to-br from-green-500 to-teal-600'
          : isSystem
          ? 'bg-gradient-to-br from-yellow-400 to-orange-500'
          : 'bg-gradient-to-br from-blue-500 to-indigo-600'
      }`}>
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : isSystem ? (
          <CheckCircle className="w-5 h-5 text-white" />
        ) : (
          <Brain className="w-5 h-5 text-white" />
        )}
      </div>

      {/* Message Bubble */}
      <div className={`flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-3 rounded-2xl shadow-sm max-w-[80%] ${
          isUser
            ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-tr-sm'
            : isSystem
            ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 text-gray-800 rounded-tl-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'
        }`}>
          {/* Message Content */}
          <HiddenMessage
            visibleText={message.content}
            hiddenContent={message.hiddenContent}
            isRevealed={message.isRevealed}
            textSize={elderlyFriendly ? 'lg' : 'md'}
            elderlyFriendly={elderlyFriendly}
          />

          {/* Score Badge */}
          {message.score && (
            <div className={`mt-3 px-3 py-2 rounded-lg ${
              message.score.is_correct
                ? 'bg-green-100 text-green-800 border border-green-300'
                : 'bg-red-100 text-red-800 border border-red-300'
            }`}>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">
                  {message.score.points_earned}/{message.score.points_possible} điểm
                </span>
              </div>
              {message.score.feedback && (
                <p className="text-xs mt-1">{message.score.feedback}</p>
              )}
            </div>
          )}

          {/* Timestamp */}
          <div className="mt-2 text-xs opacity-60">
            {message.timestamp.toLocaleTimeString('vi-VN', {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </div>
        </div>
      </div>
    </div>
  );
}





