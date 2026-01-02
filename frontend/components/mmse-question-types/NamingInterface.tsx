"use client";

import React, { useState } from 'react';
import Image from 'next/image';
import { ZoomIn, ZoomOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface NamingInterfaceProps {
  questionId: string;
  imageUrl?: string;
  imageAlt?: string;
  objectName?: string; // For fallback icon
  onAnswer?: (answer: string) => void;
}

const OBJECT_ICONS: Record<string, string> = {
  'đồng hồ': '🕐',
  'bút': '✏️',
  'bút chì': '✏️',
  'bút bi': '✏️',
  'cây bút': '✏️',
  default: '❓'
};

export default function NamingInterface({
  questionId,
  imageUrl,
  imageAlt = 'Object to name',
  objectName,
  onAnswer
}: NamingInterfaceProps) {
  const [isZoomed, setIsZoomed] = useState(false);
  const [imageError, setImageError] = useState(false);
  
  const icon = objectName 
    ? (OBJECT_ICONS[objectName.toLowerCase()] || OBJECT_ICONS.default)
    : OBJECT_ICONS.default;

  return (
    <div className="w-full space-y-4">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-gray-800 mb-2">
          🏷️ Đây là vật gì?
        </h3>
      </div>

      {/* Image display */}
      <div className="bg-gradient-to-r from-blue-50 to-cyan-50 rounded-xl p-6 border-2 border-blue-200">
        <div className="flex justify-center">
          <div
            className={`relative bg-white rounded-lg shadow-lg overflow-hidden cursor-pointer transition-all duration-300 ${
              isZoomed ? 'w-full max-w-2xl' : 'w-64 h-64'
            }`}
            onClick={() => setIsZoomed(!isZoomed)}
          >
            {imageUrl && !imageError ? (
              <Image
                src={imageUrl}
                alt={imageAlt}
                fill
                className="object-contain"
                onError={() => setImageError(true)}
              />
            ) : (
              // Fallback: Large icon
              <div className="w-full h-full flex items-center justify-center">
                <span className="text-9xl">{icon}</span>
              </div>
            )}
            
            {/* Zoom indicator */}
            <div className="absolute bottom-2 right-2 bg-black/50 text-white px-2 py-1 rounded text-xs flex items-center gap-1">
              {isZoomed ? (
                <>
                  <ZoomOut className="w-3 h-3" />
                  Click để thu nhỏ
                </>
              ) : (
                <>
                  <ZoomIn className="w-3 h-3" />
                  Click để phóng to
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="text-center text-sm text-gray-500">
        Nhìn vào hình ảnh và cho biết đây là vật gì
      </div>
    </div>
  );
}



