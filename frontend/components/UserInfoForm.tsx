'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { User, Calendar, GraduationCap, FileText, AlertCircle, CheckCircle } from "lucide-react";

export interface UserInfo {
  name: string;
  age: string;
  gender: string;
  education_years: string;
  notes: string;
  address_term?: 'Ông' | 'Bà'; // Auto-determined based on age and gender
}

interface UserInfoFormProps {
  userInfo: UserInfo;
  onUserInfoChange: (userInfo: UserInfo) => void;
  onNext: () => void;
  onBack?: () => void;
  errors?: Partial<UserInfo>;
  isSubmitting?: boolean;
  title?: string;
  description?: string;
  showAddressTerm?: boolean;
}

export default function UserInfoForm({
  userInfo,
  onUserInfoChange,
  onNext,
  onBack,
  errors = {},
  isSubmitting = false,
  title = "Thông tin cá nhân",
  description = "Vui lòng nhập thông tin của bạn để chúng tôi có thể đánh giá chính xác hơn.",
  showAddressTerm = true
}: UserInfoFormProps) {
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  // Auto-determine address term based on age and gender
  const getAddressTerm = (): 'Ông' | 'Bà' => {
    const age = parseInt(userInfo.age);
    if (isNaN(age)) return 'Ông';

    // For elderly (65+), use traditional terms
    if (age >= 65) {
      return userInfo.gender === 'male' ? 'Ông' : 'Bà';
    }

    // For younger people, use Ông/Bà based on gender
    return userInfo.gender === 'male' ? 'Ông' : 'Bà';
  };

  const addressTerm = getAddressTerm();

  // Update address term when age or gender changes
  React.useEffect(() => {
    if (userInfo.age && userInfo.gender) {
      const newAddressTerm = getAddressTerm();
      if (newAddressTerm !== userInfo.address_term) {
        onUserInfoChange({ ...userInfo, address_term: newAddressTerm });
      }
    }
  }, [userInfo.age, userInfo.gender]);

  const handleFieldChange = (field: keyof UserInfo, value: string) => {
    onUserInfoChange({ ...userInfo, [field]: value });
    setTouched({ ...touched, [field]: true });
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<UserInfo> = {};

    if (!userInfo.name.trim()) {
      newErrors.name = 'Vui lòng nhập họ và tên';
    } else if (userInfo.name.trim().length < 2) {
      newErrors.name = 'Họ và tên phải có ít nhất 2 ký tự';
    }

    if (!userInfo.age.trim()) {
      newErrors.age = 'Vui lòng nhập tuổi';
    } else {
      const age = parseInt(userInfo.age);
      if (isNaN(age) || age < 1 || age > 120) {
        newErrors.age = 'Tuổi phải từ 1 đến 120';
      }
    }

    if (!userInfo.gender) {
      newErrors.gender = 'Vui lòng chọn giới tính';
    }

    if (!userInfo.education_years.trim()) {
      newErrors.education_years = 'Vui lòng nhập số năm học';
    } else {
      const years = parseInt(userInfo.education_years);
      if (isNaN(years) || years < 0 || years > 30) {
        newErrors.education_years = 'Số năm học phải từ 0 đến 30';
      }
    }

    // Update errors in parent component
    if (Object.keys(newErrors).length > 0) {
      // This would normally be passed from parent, but we'll assume parent handles validation
    }

    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateForm()) {
      onNext();
    }
  };

  const isFormValid = () => {
    return userInfo.name.trim() &&
           userInfo.age.trim() &&
           userInfo.gender &&
           userInfo.education_years.trim() &&
           !Object.keys(errors).length;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-2xl mx-auto"
    >
      <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
        <CardHeader className="text-center pb-6">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
            className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <User className="w-8 h-8 text-white" />
          </motion.div>
          <CardTitle className="text-2xl font-bold text-gray-800 mb-2">
            {title}
          </CardTitle>
          <p className="text-gray-600 text-lg">
            {description}
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Name Field */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="space-y-2"
          >
            <Label htmlFor="name" className="text-lg font-medium text-gray-700 flex items-center gap-2">
              <User className="w-5 h-5" />
              Họ và tên *
            </Label>
            <Input
              id="name"
              type="text"
              placeholder="Ví dụ: Nguyễn Văn An"
              value={userInfo.name}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              className={`text-lg py-3 px-4 border-2 rounded-xl transition-all ${
                errors.name ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-400'
              }`}
            />
            {errors.name && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-red-600 text-sm flex items-center gap-1"
              >
                <AlertCircle className="w-4 h-4" />
                {errors.name}
              </motion.p>
            )}
          </motion.div>

          {/* Age and Gender Row */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4"
          >
            {/* Age */}
            <div className="space-y-2">
              <Label htmlFor="age" className="text-lg font-medium text-gray-700 flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Tuổi *
              </Label>
              <Input
                id="age"
                type="number"
                min="1"
                max="120"
                placeholder="65"
                value={userInfo.age}
                onChange={(e) => handleFieldChange('age', e.target.value)}
                className={`text-lg py-3 px-4 border-2 rounded-xl transition-all ${
                  errors.age ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-400'
                }`}
              />
              {errors.age && (
                <p className="text-red-600 text-sm flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.age}
                </p>
              )}
            </div>

            {/* Gender */}
            <div className="space-y-2">
              <Label htmlFor="gender" className="text-lg font-medium text-gray-700">
                Giới tính *
              </Label>
              <Select value={userInfo.gender} onValueChange={(value) => handleFieldChange('gender', value)}>
                <SelectTrigger className={`text-lg py-3 px-4 border-2 rounded-xl transition-all ${
                  errors.gender ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-400'
                }`}>
                  <SelectValue placeholder="Chọn giới tính" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="male" className="text-lg py-2">Nam</SelectItem>
                  <SelectItem value="female" className="text-lg py-2">Nữ</SelectItem>
                  <SelectItem value="other" className="text-lg py-2">Khác</SelectItem>
                </SelectContent>
              </Select>
              {errors.gender && (
                <p className="text-red-600 text-sm flex items-center gap-1">
                  <AlertCircle className="w-4 h-4" />
                  {errors.gender}
                </p>
              )}
            </div>
          </motion.div>

          {/* Address Term Display */}
          {showAddressTerm && userInfo.age && userInfo.gender && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.5 }}
              className="bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200 rounded-xl p-4"
            >
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6 text-green-600" />
                <div>
                  <p className="text-lg font-semibold text-gray-800">
                    Xin chào {addressTerm} {userInfo.name.split(' ').pop()}!
                  </p>
                  <p className="text-sm text-gray-600">
                    Chúng tôi sẽ xưng hô với {addressTerm.toLowerCase()} trong suốt bài kiểm tra.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Education Years */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="space-y-2"
          >
            <Label htmlFor="education_years" className="text-lg font-medium text-gray-700 flex items-center gap-2">
              <GraduationCap className="w-5 h-5" />
              Số năm học (năm) *
            </Label>
            <Input
              id="education_years"
              type="number"
              min="0"
              max="30"
              placeholder="12"
              value={userInfo.education_years}
              onChange={(e) => handleFieldChange('education_years', e.target.value)}
              className={`text-lg py-3 px-4 border-2 rounded-xl transition-all ${
                errors.education_years ? 'border-red-400 focus:border-red-500' : 'border-gray-200 focus:border-blue-400'
              }`}
            />
            <p className="text-sm text-gray-500">Ví dụ: 12 năm (từ lớp 1 đến lớp 12)</p>
            {errors.education_years && (
              <p className="text-red-600 text-sm flex items-center gap-1">
                <AlertCircle className="w-4 h-4" />
                {errors.education_years}
              </p>
            )}
          </motion.div>

          {/* Notes */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="space-y-2"
          >
            <Label htmlFor="notes" className="text-lg font-medium text-gray-700 flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Ghi chú thêm (tùy chọn)
            </Label>
            <textarea
              id="notes"
              placeholder="Ví dụ: Đang dùng thuốc điều trị huyết áp, có vấn đề về thính giác..."
              value={userInfo.notes}
              onChange={(e) => handleFieldChange('notes', e.target.value)}
              rows={3}
              className="w-full text-lg py-3 px-4 border-2 border-gray-200 rounded-xl focus:border-blue-400 focus:ring-2 focus:ring-blue-200 outline-none transition-all resize-none"
            />
            <p className="text-sm text-gray-500">
              Thông tin này sẽ giúp chúng tôi đánh giá chính xác hơn về tình trạng nhận thức của bạn.
            </p>
          </motion.div>

          {/* Action Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="flex gap-4 pt-6"
          >
            {onBack && (
              <Button
                onClick={onBack}
                variant="ghost"
                size="lg"
                className="flex-1 py-4 text-lg font-semibold border-2 border-gray-300 hover:bg-gray-50"
                disabled={isSubmitting}
              >
                Quay lại
              </Button>
            )}
            <Button
              onClick={handleNext}
              size="lg"
              className="flex-1 py-4 text-lg font-semibold bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg hover:shadow-xl transition-all"
              disabled={isSubmitting || !isFormValid()}
            >
              {isSubmitting ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-5 h-5 border-2 border-white border-t-transparent rounded-full mr-2"
                  />
                  Đang xử lý...
                </>
              ) : (
                'Tiếp tục'
              )}
            </Button>
          </motion.div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
