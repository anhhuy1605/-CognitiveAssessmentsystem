"use client";

import React, { useRef, useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Eraser, Undo2, Redo2, Check, X, Palette, Minus, Plus } from 'lucide-react';
import { motion } from 'framer-motion';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog';

interface ClockDrawingModalProps {
  /**
   * Whether modal is open
   */
  isOpen: boolean;
  
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
   * Callback when user cancels or closes
   */
  onClose?: () => void;
  
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
 * Modal whiteboard component for clock drawing test
 * Full-featured drawing interface with colors, brush sizes, etc.
 */
export default function ClockDrawingModal({
  isOpen,
  targetTime,
  onSubmit,
  onClose,
  elderlyFriendly = true,
  canvasSize = 500
}: ClockDrawingModalProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [history, setHistory] = useState<ImageData[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [brushSize, setBrushSize] = useState(elderlyFriendly ? 4 : 2);
  const [brushColor, setBrushColor] = useState('#000000');
  const [hasDrawn, setHasDrawn] = useState(false);
  
  // Color palette
  const colors = [
    '#000000', // Black
    '#FF0000', // Red
    '#0000FF', // Blue
    '#008000', // Green
    '#FFA500', // Orange
    '#800080', // Purple
  ];
  
  // Initialize canvas
  useEffect(() => {
    if (!isOpen) return;
    
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size
    canvas.width = canvasSize;
    canvas.height = canvasSize;
    
    // Set drawing styles
    ctx.strokeStyle = brushColor;
    ctx.lineWidth = brushSize;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // Draw initial circle guide (light gray, optional)
    ctx.beginPath();
    ctx.arc(canvasSize / 2, canvasSize / 2, canvasSize / 2 - 30, 0, 2 * Math.PI);
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // Reset drawing state
    ctx.strokeStyle = brushColor;
    ctx.lineWidth = brushSize;
    
    // Save initial state
    saveState();
  }, [isOpen, canvasSize, brushColor, brushSize]);
  
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
    setHasDrawn(true);
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
    // Redraw guide circle
    ctx.beginPath();
    ctx.arc(canvasSize / 2, canvasSize / 2, canvasSize / 2 - 30, 0, 2 * Math.PI);
    ctx.strokeStyle = '#e0e0e0';
    ctx.lineWidth = 1;
    ctx.stroke();
    ctx.strokeStyle = brushColor;
    ctx.lineWidth = brushSize;
    
    saveState();
    setHasDrawn(false);
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
  
  // Update brush color
  const updateBrushColor = (color: string) => {
    setBrushColor(color);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.strokeStyle = color;
      }
    }
  };
  
  // Update brush size
  const updateBrushSize = (delta: number) => {
    const newSize = Math.max(1, Math.min(20, brushSize + delta));
    setBrushSize(newSize);
    const canvas = canvasRef.current;
    if (canvas) {
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.lineWidth = newSize;
      }
    }
  };
  
  // Submit drawing
  const handleSubmit = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const imageData = canvas.toDataURL('image/png');
    onSubmit?.(imageData);
    onClose?.();
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose?.()}>
      <DialogContent className="max-w-4xl w-[95vw] max-h-[95vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className={elderlyFriendly ? 'text-2xl' : 'text-xl'}>
            Vẽ Đồng Hồ
          </DialogTitle>
          <DialogDescription className={elderlyFriendly ? 'text-lg' : 'text-base'}>
            {targetTime ? (
              <>Vẽ một mặt đồng hồ với đầy đủ các số từ 1 đến 12, rồi vẽ kim đồng hồ chỉ thời gian: <strong>{targetTime}</strong></>
            ) : (
              <>Vẽ một mặt đồng hồ với đầy đủ các số từ 1 đến 12, rồi vẽ kim đồng hồ chỉ một giờ nào đó.</>
            )}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* Canvas */}
          <div className="flex justify-center">
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
          <div className="space-y-4">
            {/* Color Picker */}
            <div className="flex items-center gap-3">
              <label className={`${elderlyFriendly ? 'text-lg' : 'text-base'} font-medium`}>
                Màu vẽ:
              </label>
              <div className="flex gap-2">
                {colors.map((color) => (
                  <button
                    key={color}
                    onClick={() => updateBrushColor(color)}
                    className={`w-10 h-10 rounded-full border-2 transition-all ${
                      brushColor === color
                        ? 'border-blue-500 scale-110'
                        : 'border-gray-300 hover:scale-105'
                    }`}
                    style={{ backgroundColor: color }}
                    title={color}
                  />
                ))}
              </div>
            </div>
            
            {/* Brush Size */}
            <div className="flex items-center gap-3">
              <label className={`${elderlyFriendly ? 'text-lg' : 'text-base'} font-medium`}>
                Độ dày:
              </label>
              <div className="flex items-center gap-2">
                <Button
                  variant="secondaryOutline"
                  size={elderlyFriendly ? "lg" : "default"}
                  onClick={() => updateBrushSize(-1)}
                  disabled={brushSize <= 1}
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <span className={`${elderlyFriendly ? 'text-lg' : 'text-base'} font-mono w-12 text-center`}>
                  {brushSize}px
                </span>
                <Button
                  variant="secondaryOutline"
                  size={elderlyFriendly ? "lg" : "default"}
                  onClick={() => updateBrushSize(1)}
                  disabled={brushSize >= 20}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            {/* Tools */}
            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondaryOutline"
                size={elderlyFriendly ? "lg" : "default"}
                onClick={handleClear}
                className="gap-2"
              >
                <Eraser className="h-4 w-4" />
                Xóa tất cả
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
            </div>
          </div>
        </div>
        
        <DialogFooter>
          <Button
            variant="secondaryOutline"
            size={elderlyFriendly ? "lg" : "default"}
            onClick={onClose}
            className="gap-2"
          >
            <X className="h-4 w-4" />
            Hủy
          </Button>
          
          <Button
            size={elderlyFriendly ? "lg" : "default"}
            onClick={handleSubmit}
            disabled={!hasDrawn}
            className="gap-2"
          >
            <Check className="h-4 w-4" />
            Hoàn thành
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}





