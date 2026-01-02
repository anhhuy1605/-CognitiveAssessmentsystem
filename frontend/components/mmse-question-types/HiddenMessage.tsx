"use client";

import React, { useState, useEffect } from 'react';
import { Eye, EyeOff, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';

interface HiddenMessageProps {
  /**
   * Main visible message text
   */
  visibleText: string;
  
  /**
   * Array of strings that should be hidden
   * These will be replaced with [HIDDEN] placeholders
   */
  hiddenContent?: string[];
  
  /**
   * Whether hidden content should be revealed
   * Controlled by parent component
   */
  isRevealed?: boolean;
  
  /**
   * Callback when user wants to reveal content
   */
  onReveal?: () => void;
  
  /**
   * Whether to show reveal button
   */
  showRevealButton?: boolean;
  
  /**
   * Custom placeholder for hidden content
   */
  placeholder?: string;
  
  /**
   * Size of text (for accessibility)
   */
  textSize?: 'sm' | 'md' | 'lg' | 'xl';
  
  /**
   * Whether this is for elderly users (larger text, simpler UI)
   */
  elderlyFriendly?: boolean;
}

/**
 * Component to display messages with hidden content support
 * Designed for MMSE chatbot to prevent exposing answers
 */
export default function HiddenMessage({
  visibleText,
  hiddenContent = [],
  isRevealed = false,
  onReveal,
  showRevealButton = false,
  placeholder = '[...]',
  textSize = 'md',
  elderlyFriendly = true
}: HiddenMessageProps) {
  const [localRevealed, setLocalRevealed] = useState(isRevealed);
  
  // Sync with parent control
  useEffect(() => {
    setLocalRevealed(isRevealed);
  }, [isRevealed]);
  
  /**
   * Process text to hide sensitive content
   * Only hides [HIDDEN: ...] patterns, preserves rest of text
   */
  const processText = (text: string): string => {
    if (!hiddenContent || hiddenContent.length === 0 || localRevealed) {
      return text;
    }
    
    let processed = text;
    hiddenContent.forEach((hidden) => {
      // Remove markdown bold if present
      const cleanHidden = hidden.replace(/\*\*/g, '').trim();
      if (!cleanHidden) return;
      
      // Only replace exact matches, use word boundaries when possible
      try {
        const escaped = cleanHidden.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        // Try word boundary first
        let regex = new RegExp(`\\b${escaped}\\b`, 'gi');
        if (!regex.test(processed)) {
          // If no match with word boundaries, try without
          regex = new RegExp(escaped, 'gi');
        }
        processed = processed.replace(regex, placeholder);
      } catch (e) {
        // If regex fails, do simple string replace
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
  
  // Text size classes for elderly-friendly design
  const textSizeClasses = {
    sm: 'text-base',
    md: elderlyFriendly ? 'text-lg' : 'text-base',
    lg: elderlyFriendly ? 'text-xl' : 'text-lg',
    xl: elderlyFriendly ? 'text-2xl' : 'text-xl'
  };
  
  return (
    <div className="hidden-message-container w-full">
      <div className={`message-content ${textSizeClasses[textSize]} leading-relaxed`}>
        {/* Split by newlines to preserve formatting */}
        {processedText.split('\n').map((line, index) => (
          <p key={index} className="mb-2 last:mb-0">
            {line || '\u00A0'} {/* Non-breaking space for empty lines */}
          </p>
        ))}
      </div>
      
      {/* Reveal button (if needed) */}
      {showRevealButton && !localRevealed && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-3"
        >
          <Button
            variant="outline"
            size={elderlyFriendly ? "lg" : "default"}
            onClick={handleReveal}
            className="w-full sm:w-auto"
          >
            <Eye className="mr-2 h-4 w-4" />
            Hiển thị nội dung
          </Button>
        </motion.div>
      )}
      
      {/* Hidden indicator */}
      {!localRevealed && hiddenContent && hiddenContent.length > 0 && (
        <div className="mt-2 flex items-center gap-2 text-sm text-muted-foreground">
          <Lock className="h-3 w-3" />
          <span>Một số nội dung đã được ẩn</span>
        </div>
      )}
    </div>
  );
}

