/**
 * HiddenMessage Component - Displays text with hidden content support
 */

import React, { useState, useEffect } from 'react';
import { Eye, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface HiddenMessageProps {
  visibleText: string;
  hiddenContent?: string[];
  isRevealed?: boolean;
  showRevealButton?: boolean;
  placeholder?: string;
  textSize?: 'sm' | 'md' | 'lg' | 'xl';
  elderlyFriendly?: boolean;
  onReveal?: () => void;
}

export default function HiddenMessage({
  visibleText,
  hiddenContent = [],
  isRevealed = false,
  showRevealButton = false,
  placeholder = '[...]',
  textSize = 'md',
  elderlyFriendly = true,
  onReveal,
}: HiddenMessageProps) {
  const [localRevealed, setLocalRevealed] = useState(isRevealed);

  useEffect(() => {
    setLocalRevealed(isRevealed);
  }, [isRevealed]);

  /**
   * Process text to hide sensitive content
   */
  const processText = (text: string): string => {
    if (!hiddenContent || hiddenContent.length === 0 || localRevealed) {
      return text;
    }

    let processed = text;
    hiddenContent.forEach((hidden) => {
      const cleanHidden = hidden.replace(/\*\*/g, '').trim();
      if (!cleanHidden) return;

      try {
        const escaped = cleanHidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let regex = new RegExp(`\\b${escaped}\\b`, 'gi');
        if (!regex.test(processed)) {
          regex = new RegExp(escaped, 'gi');
        }
        processed = processed.replace(regex, placeholder);
      } catch (e) {
        processed = processed.replace(cleanHidden, placeholder);
      }
    });

    return processed;
  };

  const handleReveal = () => {
    setLocalRevealed(true);
    onReveal?.();
  };

  const processedText = processText(visibleText);

  const textSizeClasses = {
    sm: 'text-base',
    md: elderlyFriendly ? 'text-lg' : 'text-base',
    lg: elderlyFriendly ? 'text-xl' : 'text-lg',
    xl: elderlyFriendly ? 'text-2xl' : 'text-xl',
  };

  return (
    <div className="hidden-message-container w-full">
      <div className={`message-content ${textSizeClasses[textSize]} leading-relaxed`}>
        {processedText.split('\n').map((line, index) => (
          <p key={index} className="mb-2 last:mb-0">
            {line || '\u00A0'}
          </p>
        ))}
      </div>

      {showRevealButton && !localRevealed && (
        <div className="mt-3">
          <Button
            variant="outline"
            size={elderlyFriendly ? 'lg' : 'default'}
            onClick={handleReveal}
            className="w-full sm:w-auto"
          >
            <Eye className="mr-2 h-4 w-4" />
            Hiển thị nội dung
          </Button>
        </div>
      )}

      {!localRevealed && hiddenContent && hiddenContent.length > 0 && (
        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <Lock className="h-3 w-3" />
          <span>Một số nội dung đã được ẩn</span>
        </div>
      )}
    </div>
  );
}





