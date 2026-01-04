"use client";

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Eraser, Undo2, Redo2, Check, X, Download } from 'lucide-react';
import { motion } from 'framer-motion';

interface ClockDrawingWhiteboardProps {
  /**
   * Target time to draw (e.g., "11:10")
   */
  targetTime?: string;
  
  /**
   * Callback when drawing is submitted
   * Returns base64 image data
   */
  onSubmit?: (imageData: string) => void;
  
  /**
   * Callback when user cancels
   */
  onCancel?: () => void;
  
  /**
   * Whether this is for elderly users (larger controls)
   */
  elderlyFriendly?: boolean;
  
  /**
   * Canvas size
   */
  canvasSize?: number;
}

/**
 * Whiteboard component for clock drawing test
 * Allows users to draw a clock face with numbers and hands
 */
export default function ClockDrawingWhiteboard({
  targetTime,
  onSubmit,
  onCancel,
  elderlyFriendly = true,
  canvasSize = 400
}: ClockDrawingWhiteboardProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [brushSize, setBrushSize] = useState(elderlyFriendly ? 4 : 2);
  const [showNumbers, setShowNumbers] = useState(false); // Helper: show number positions
  
  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size
    canvas.width = canvasSize;
    canvas.height = canvasSize;
    
    // Set drawing styles
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Draw initial circle guide (optional, can be removed)
    ctx.beginPath();
    ctx.arc(canvasSize / 2, canvasSize / 2, canvasSize / 2 - 20, 0, 2 * Math.PI);
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // Save initial state
    saveState();
  }, [canvasSize, brushSize]);
  
  // Save current canvas state to history
  const saveState = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(imageData);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [history, historyIndex]);
  
  // Start drawing
  const startDrawing = useCallback((e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e 
      ? e.touches[0].clientX - rect.left
      : e.clientX - rect.left;
    const y = 'touches' in e
      ? e.touches[0].clientY - rect.top
      : e.clientY - rect.top;
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    setIsDrawing(true);
    saveState();
  }, [saveState]);
  
  // Draw
  const draw = useCallback((e: React.MouseEvent<HTMLCanvasElement> | React.TouchEvent<HTMLCanvasElement>) => {
    if (!isDrawing) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const rect = canvas.getBoundingClientRect();
    const x = 'touches' in e
      ? e.touches[0].clientX - rect.left
      : e.clientX - rect.left;
    const y = 'touches' in e
      ? e.touches[0].clientY - rect.top
      : e.clientY - rect.top;
    
    ctx.lineTo(x, y);
    ctx.stroke();
  }, [isDrawing]);
  
  // Stop drawing
  const stopDrawing = useCallback(() => {
    if (isDrawing) {
      saveState();
    }
    setIsDrawing(false);
  }, [isDrawing, saveState]);
  
  // Clear canvas
  const handleClear = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    saveState();
  };
  
  // Undo
  const handleUndo = () => {
    if (historyIndex > 0) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      setHistoryIndex(historyIndex - 1);
      ctx.putImageData(history[historyIndex - 1], 0, 0);
    }
  };
  
  // Redo
  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      const canvas = canvasRef.current;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      
      setHistoryIndex(historyIndex + 1);
      ctx.putImageData(history[historyIndex + 1], 0, 0);
    }
  };
  
  // Submit drawing
  const handleSubmit = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const imageData = canvas.toDataURL('image/png');
    onSubmit?.(imageData);
  };
  
  return (
    <div className="clock-drawing-whiteboard w-full max-w-2xl mx-auto">
      {/* Instructions */}
      <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
        <p className={`${elderlyFriendly ? 'text-lg' : 'text-base'} text-gray-700 dark:text-gray-300 mb-2`}>
          <strong>Hướng dẫn:</strong> Vẽ một mặt đồng hồ với đầy đủ các số từ 1 đến 12.
        </p>
        {targetTime && (
          <p className={`${elderlyFriendly ? 'text-lg' : 'text-base'} text-gray-700 dark:text-gray-300`}>
            Vẽ kim đồng hồ chỉ thời gian: <strong>{targetTime}</strong>
          </p>
        )}
      </div>
      
      {/* Canvas */}
      <div className="flex justify-center mb-4">
        <div className="relative border-2 border-gray-300 dark:border-gray-600 rounded-lg shadow-lg bg-white dark:bg-gray-800">
          <canvas
            ref={canvasRef}
            className="cursor-crosshair touch-none"
            onMouseDown={startDrawing}
            onMouseMove={draw}
            onMouseUp={stopDrawing}
            onMouseLeave={stopDrawing}
            onTouchStart={startDrawing}
            onTouchMove={draw}
            onTouchEnd={stopDrawing}
            style={{
              display: 'block',
              width: '100%',
              maxWidth: `${canvasSize}px`,
              height: 'auto'
            }}
          />
        </div>
      </div>
      
      {/* Controls */}
      <div className="flex flex-wrap gap-2 justify-center items-center">
        {/* Brush size */}
        <div className="flex items-center gap-2">
          <label className={`${elderlyFriendly ? 'text-base' : 'text-sm'} text-gray-700 dark:text-gray-300`}>
            Độ dày:
          </label>
          <input
            type="range"
            min="2"
            max="8"
            value={brushSize}
            onChange={(e) => {
              setBrushSize(Number(e.target.value));
              const canvas = canvasRef.current;
              if (canvas) {
                const ctx = canvas.getContext('2d');
                if (ctx) {
                  ctx.lineWidth = Number(e.target.value);
                }
              }
            }}
            className="w-24"
          />
        </div>
        
        {/* Tools */}
        <Button
          variant="secondaryOutline"
          size={elderlyFriendly ? "lg" : "default"}
          onClick={handleClear}
          className="gap-2"
        >
          <Eraser className="h-4 w-4" />
          Xóa
        </Button>
        
        <Button
          variant="secondaryOutline"
          size={elderlyFriendly ? "lg" : "default"}
          onClick={handleUndo}
          disabled={historyIndex <= 0}
          className="gap-2"
        >
          <Undo2 className="h-4 w-4" />
          Hoàn tác
        </Button>
        
        <Button
          variant="secondaryOutline"
          size={elderlyFriendly ? "lg" : "default"}
          onClick={handleRedo}
          disabled={historyIndex >= history.length - 1}
          className="gap-2"
        >
          <Redo2 className="h-4 w-4" />
          Làm lại
        </Button>
        
        {/* Submit/Cancel */}
        <div className="flex gap-2 ml-auto">
          <Button
            variant="secondaryOutline"
            size={elderlyFriendly ? "lg" : "default"}
            onClick={onCancel}
            className="gap-2"
          >
            <X className="h-4 w-4" />
            Hủy
          </Button>
          
          <Button
            size={elderlyFriendly ? "lg" : "default"}
            onClick={handleSubmit}
            className="gap-2"
          >
            <Check className="h-4 w-4" />
            Hoàn thành
          </Button>
        </div>
      </div>
      
      {/* Helper: Show number positions (optional) */}
      {showNumbers && (
        <div className="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
          <p>Gợi ý: Các số nên được đặt đều quanh vòng tròn</p>
        </div>
      )}
    </div>
  );
}

