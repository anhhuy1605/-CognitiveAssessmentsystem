"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Mic, CheckCircle2 } from 'lucide-react';

interface LocationCollectionProps {
  initialData?: {
    city?: string;
    district?: string;
    ward?: string;
  };
  onComplete: (location: {
    city: string;
    district: string;
    ward?: string;
  }) => void;
  onSkip?: () => void;
}

export default function LocationCollection({
  initialData,
  onComplete,
  onSkip
}: LocationCollectionProps) {
  const [city, setCity] = useState(initialData?.city || '');
  const [district, setDistrict] = useState(initialData?.district || '');
  const [ward, setWard] = useState(initialData?.ward || '');
  const [errors, setErrors] = useState<{ city?: string; district?: string }>({});

  const handleSubmit = () => {
    const newErrors: { city?: string; district?: string } = {};
    
    if (!city.trim()) {
      newErrors.city = 'Vui lòng nhập thành phố/tỉnh';
    }
    if (!district.trim()) {
      newErrors.district = 'Vui lòng nhập quận/huyện';
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setErrors({});
    onComplete({
      city: city.trim(),
      district: district.trim(),
      ward: ward.trim() || undefined
    });
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          📍 Thông tin địa điểm
        </h2>
        <p className="text-gray-600">
          Trước khi bắt đầu, vui lòng cho biết địa điểm hiện tại của bạn
        </p>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-md space-y-6 border border-gray-200">
        {/* City */}
        <div className="space-y-2">
          <Label htmlFor="city" className="text-base font-semibold">
            Thành phố/Tỉnh <span className="text-red-500">*</span>
          </Label>
          <div className="relative">
            <Input
              id="city"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Ví dụ: Hà Nội, Hồ Chí Minh, Đà Nẵng..."
              className={`pr-10 ${errors.city ? 'border-red-500' : ''}`}
            />
            <Mic className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
          {errors.city && (
            <p className="text-sm text-red-500">{errors.city}</p>
          )}
        </div>

        {/* District */}
        <div className="space-y-2">
          <Label htmlFor="district" className="text-base font-semibold">
            Quận/Huyện <span className="text-red-500">*</span>
          </Label>
          <div className="relative">
            <Input
              id="district"
              value={district}
              onChange={(e) => setDistrict(e.target.value)}
              placeholder="Ví dụ: Quận 1, Quận Ba Đình, Huyện Củ Chi..."
              className={`pr-10 ${errors.district ? 'border-red-500' : ''}`}
            />
            <Mic className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
          {errors.district && (
            <p className="text-sm text-red-500">{errors.district}</p>
          )}
        </div>

        {/* Ward (Optional) */}
        <div className="space-y-2">
          <Label htmlFor="ward" className="text-base font-semibold">
            Phường/Xã <span className="text-gray-400 text-sm">(Không bắt buộc)</span>
          </Label>
          <div className="relative">
            <Input
              id="ward"
              value={ward}
              onChange={(e) => setWard(e.target.value)}
              placeholder="Ví dụ: Phường Điện Biên, Xã An Phú..."
              className="pr-10"
            />
            <Mic className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex gap-3 pt-4">
          <Button
            onClick={handleSubmit}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            size="lg"
          >
            <CheckCircle2 className="w-5 h-5 mr-2" />
            Tiếp tục
          </Button>
          {onSkip && (
            <Button
              onClick={onSkip}
              variant="secondaryOutline"
              className="flex-1"
              size="lg"
            >
              Bỏ qua
            </Button>
          )}
        </div>
      </div>

      <p className="text-center text-sm text-gray-500">
        Thông tin này sẽ được sử dụng để đánh giá câu trả lời về địa điểm trong bài test
      </p>
    </div>
  );
}

