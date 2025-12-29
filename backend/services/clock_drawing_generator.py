# -*- coding: utf-8 -*-
"""
Clock Drawing Test Generator for MMSE v2.1
Generates clock images and validates user responses

Based on Shulman et al. (1993) Clock Drawing Test
"""

import logging
import math
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageFont
import io
import base64

logger = logging.getLogger(__name__)

@dataclass
class ClockDrawingResult:
    """Result of clock drawing validation"""
    hour_hand_angle: float  # Angle in degrees (0-360)
    minute_hand_angle: float
    hour_hand_position: Tuple[float, float]  # (x, y) coordinates
    minute_hand_position: Tuple[float, float]
    hour_number: int  # Which number the hour hand points to (1-12)
    minute_number: int  # Which number the minute hand points to (1-12)
    is_valid: bool
    shulman_score: int  # 0-6 based on Shulman scale
    mmse_score: int  # 0-3 converted from Shulman


class ClockDrawingGenerator:
    """Generate and validate clock drawings for MMSE test"""
    
    def __init__(self, clock_size: int = 400):
        """
        Initialize clock generator
        
        Args:
            clock_size: Size of clock image in pixels (default 400)
        """
        self.clock_size = clock_size
        self.center = (clock_size // 2, clock_size // 2)
        self.radius = clock_size // 2 - 20  # Leave margin
        
    def generate_clock_image(self, target_time: str = "11:10") -> Tuple[str, Dict]:
        """
        Generate a clock image showing the target time
        
        Args:
            target_time: Time in format "HH:MM" (e.g., "11:10")
        
        Returns:
            Tuple of (base64_image_string, clock_data_dict)
            clock_data contains:
            - hour_hand_angle: Angle of hour hand in degrees
            - minute_hand_angle: Angle of minute hand in degrees
            - hour_hand_position: (x, y) coordinates of hour hand tip
            - minute_hand_position: (x, y) coordinates of minute hand tip
            - hour_number: Number the hour hand points between (11-12)
            - minute_number: Number the minute hand points to (2)
        """
        # Parse time
        hour, minute = map(int, target_time.split(":"))
        
        # Calculate angles
        # Minute hand: 0 degrees = 12 o'clock, clockwise
        minute_angle = (minute / 60.0) * 360.0 - 90  # -90 to start at 12
        if minute_angle < 0:
            minute_angle += 360
        
        # Hour hand: moves with minutes too
        hour_angle = ((hour % 12) / 12.0) * 360.0 + (minute / 60.0) * 30.0 - 90
        if hour_angle < 0:
            hour_angle += 360
        
        # Create image
        img = Image.new('RGB', (self.clock_size, self.clock_size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw circle
        margin = 20
        draw.ellipse(
            [margin, margin, self.clock_size - margin, self.clock_size - margin],
            outline='black',
            width=3
        )
        
        # Draw numbers 1-12
        font_size = 30
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        for i in range(1, 13):
            angle = math.radians((i * 30) - 90)  # -90 to start at 12
            number_radius = self.radius - 30
            x = self.center[0] + number_radius * math.cos(angle)
            y = self.center[1] + number_radius * math.sin(angle)
            
            # Get text size for centering
            bbox = draw.textbbox((0, 0), str(i), font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            draw.text(
                (x - text_width/2, y - text_height/2),
                str(i),
                fill='black',
                font=font
            )
        
        # Draw hour hand (shorter)
        hour_hand_length = self.radius * 0.5
        hour_angle_rad = math.radians(hour_angle)
        hour_end_x = self.center[0] + hour_hand_length * math.cos(hour_angle_rad)
        hour_end_y = self.center[1] + hour_hand_length * math.sin(hour_angle_rad)
        draw.line(
            [self.center, (hour_end_x, hour_end_y)],
            fill='black',
            width=4
        )
        
        # Draw minute hand (longer)
        minute_hand_length = self.radius * 0.7
        minute_angle_rad = math.radians(minute_angle)
        minute_end_x = self.center[0] + minute_hand_length * math.cos(minute_angle_rad)
        minute_end_y = self.center[1] + minute_hand_length * math.sin(minute_angle_rad)
        draw.line(
            [self.center, (minute_end_x, minute_end_y)],
            fill='black',
            width=3
        )
        
        # Draw center circle
        center_radius = 8
        draw.ellipse(
            [
                self.center[0] - center_radius,
                self.center[1] - center_radius,
                self.center[0] + center_radius,
                self.center[1] + center_radius
            ],
            fill='black'
        )
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        # Calculate which numbers the hands point to
        hour_number = self._angle_to_hour_number(hour_angle)
        minute_number = self._angle_to_minute_number(minute_angle)
        
        clock_data = {
            'hour_hand_angle': hour_angle,
            'minute_hand_angle': minute_angle,
            'hour_hand_position': (float(hour_end_x), float(hour_end_y)),
            'minute_hand_position': (float(minute_end_x), float(minute_end_y)),
            'hour_number': hour_number,
            'minute_number': minute_number,
            'target_time': target_time,
            'center': self.center,
            'radius': self.radius
        }
        
        return img_base64, clock_data
    
    def _angle_to_hour_number(self, angle: float) -> int:
        """Convert angle to hour number (1-12)"""
        # Normalize angle to 0-360
        angle = angle % 360
        if angle < 0:
            angle += 360
        
        # Convert to hour (0 = 12, 1 = 1, ..., 11 = 11)
        hour = int((angle + 90) / 30) % 12
        if hour == 0:
            hour = 12
        return hour
    
    def _angle_to_minute_number(self, angle: float) -> int:
        """Convert angle to minute number (1-12)"""
        # Normalize angle to 0-360
        angle = angle % 360
        if angle < 0:
            angle += 360
        
        # Convert to minute number
        minute_num = int((angle + 90) / 30) % 12
        if minute_num == 0:
            minute_num = 12
        return minute_num
    
    def validate_clock_drawing(self, user_answer: str, clock_data: Dict) -> ClockDrawingResult:
        """
        Validate user's clock drawing answer (verbal or visual)
        
        Args:
            user_answer: User's description or coordinates
            clock_data: Clock data from generation
        
        Returns:
            ClockDrawingResult with validation
        """
        # For now, return basic validation
        # In production, this would use GPT-4 Vision or coordinate matching
        
        target_hour = clock_data['hour_number']
        target_minute = clock_data['minute_number']
        
        # Simple text matching for verbal answers
        answer_lower = user_answer.lower()
        
        # Check for hour hand position
        hour_correct = False
        if any(term in answer_lower for term in ['11', 'mười một', 'giữa 11 và 12', 'gần 11']):
            hour_correct = True
        
        # Check for minute hand position
        minute_correct = False
        if any(term in answer_lower for term in ['2', 'hai', 'số 2']):
            minute_correct = True
        
        # Calculate Shulman score (simplified)
        if hour_correct and minute_correct:
            shulman_score = 6  # Perfect
            mmse_score = 3
        elif hour_correct or minute_correct:
            shulman_score = 4  # Partial
            mmse_score = 2
        else:
            shulman_score = 2  # Wrong
            mmse_score = 1
        
        return ClockDrawingResult(
            hour_hand_angle=clock_data['hour_hand_angle'],
            minute_hand_angle=clock_data['minute_hand_angle'],
            hour_hand_position=clock_data['hour_hand_position'],
            minute_hand_position=clock_data['minute_hand_position'],
            hour_number=target_hour,
            minute_number=target_minute,
            is_valid=hour_correct and minute_correct,
            shulman_score=shulman_score,
            mmse_score=mmse_score
        )

