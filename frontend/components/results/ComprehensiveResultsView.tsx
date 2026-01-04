"use client";

import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Brain, TrendingUp, BarChart3, FileText, Download, 
  BookOpen, AlertCircle, CheckCircle, Info, ChevronDown, ChevronUp,
  Activity, Mic, MessageSquare, Target, Award, Shield
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ComprehensiveResultsData {
  assessment_result: {
    mmse_score: number;
    mmse_estimate: number;
    adjusted_score?: number;
    raw_score: number;
    converted_mmse30?: number;  // ✅ NEW: Converted MMSE 30 score
    max_score_35?: number;  // ✅ NEW: 35-point scale max
    max_score_30?: number;  // ✅ NEW: 30-point scale max
    age: number;
    education_years: number;
    mci_probability: number;
    risk_level: string;
    risk_level_label: string;
    classification: string;
    confidence: number;
    thresholds: any;
    education_specific_thresholds: any;
    scale_info?: {  // ✅ NEW: Information about the scale
      scale_type?: string;
      description?: string;
      citation?: string;
      differences?: {
        visuospatial?: string;
        executive_function?: string;
        total_questions?: string;
      };
    };
  };
  feature_summary: {
    acoustic_feature_count: number;
    linguistic_feature_count: number;
    total_features: number;
    total_abnormal_features: number;
    abnormal_acoustic: number;
    abnormal_linguistic: number;
    abnormal_percentage: number;
  };
  detailed_analysis: {
    acoustic: Record<string, any>;
    linguistic: Record<string, any>;
  };
  shap_explanation: {
    top_risk_factors: Array<{
      feature: string;
      feature_name_vi?: string;
      feature_name_en?: string;
      shap_value: number;
      absolute_importance?: number;
      value: number;
      unit?: string;  // ✅ NEW: Unit for feature value
      normal_range?: number[] | { display?: string };  // ✅ UPDATED: Can be object with display
      comparison?: string;
      interpretation?: string | { description?: string };
      explanation_vi?: string;
      recommendation?: string | { title?: string; description?: string };
      citation?: string;
    }>;
    top_protective_factors: Array<any>;
    grouped_contributions: Record<string, number>;
    total_contribution: number;
    citation: string;
  };
  recommendations: Array<string | {
    category?: string;
    priority?: string;
    title?: string;
    description?: string;
    actions?: string[];
    rationale?: string;
    citation?: string;
  }>;
  citations: Array<{
    title: string;
    authors: string;
    year: number;
    journal?: string;
    volume?: string;
    pages?: string;
    doi?: string;
    description: string;
  }>;
  clinical_interpretation: {
    score_interpretation: string | { description?: string };
    risk_interpretation: string | { description?: string };
    domain_breakdown: Record<string, any>;
    feature_highlights: Array<any>;
  };
  metadata: {
    session_id: string;
    timestamp: string;
    version: string;
    model_version: string;
  };
}

interface ComprehensiveResultsViewProps {
  data: ComprehensiveResultsData;
  onExportPDF?: () => void;
}

export default function ComprehensiveResultsView({ 
  data, 
  onExportPDF 
}: ComprehensiveResultsViewProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['summary', 'interpretation']));
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);

  const toggleSection = (section: string) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'on':
        return 'bg-green-50 border-green-200 text-green-800';
      case 'nguy_co_nhe':
        return 'bg-yellow-50 border-yellow-200 text-yellow-800';
      case 'nguy_co_cao':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-800';
    }
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'on':
        return <CheckCircle className="w-6 h-6 text-green-600" />;
      case 'nguy_co_nhe':
        return <AlertCircle className="w-6 h-6 text-yellow-600" />;
      case 'nguy_co_cao':
        return <AlertCircle className="w-6 h-6 text-red-600" />;
      default:
        return <Info className="w-6 h-6 text-gray-600" />;
    }
  };

  return (
    <div className="space-y-6 p-6 bg-gray-50 min-h-screen">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-blue-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <Brain className="w-10 h-10 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Kết Quả Đánh Giá Nhận Thức Toàn Diện
              </h1>
              <p className="text-gray-600 mt-1">
                Comprehensive Cognitive Assessment Results
              </p>
            </div>
          </div>
          {onExportPDF && (
            <Button onClick={onExportPDF} size="lg" className="gap-2">
              <Download className="w-5 h-5" />
              Xuất PDF
            </Button>
          )}
        </div>
        
        <div className="mt-4 p-4 rounded-lg border border-gray-200 bg-gray-50">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600">Session ID:</span>
              <p className="font-mono font-semibold">{data.metadata.session_id}</p>
            </div>
            <div>
              <span className="text-gray-600">Ngày đánh giá:</span>
              <p className="font-semibold">
                {new Date(data.metadata.timestamp).toLocaleDateString('vi-VN')}
              </p>
            </div>
            <div>
              <span className="text-gray-600">Phiên bản:</span>
              <p className="font-semibold">{data.metadata.model_version}</p>
            </div>
            <div>
              <span className="text-gray-600">Tuổi:</span>
              <p className="font-semibold">{data.assessment_result.age} tuổi</p>
            </div>
          </div>
        </div>
      </div>

      {/* Assessment Summary */}
      <Card className="p-6 shadow-lg">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('summary')}
        >
          <div className="flex items-center gap-3">
            <Award className="w-6 h-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Tóm Tắt Đánh Giá
            </h2>
          </div>
          {expandedSections.has('summary') ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </div>

        <AnimatePresence>
          {expandedSections.has('summary') && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 space-y-4"
            >
              {/* MMSE Score */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Target className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium text-gray-600">Điểm MMSE Thô (MEC 35)</span>
                  </div>
                  <p className="text-3xl font-bold text-blue-700">
                    {(data.assessment_result.raw_score ?? 0).toFixed(1)}
                    <span className="text-lg text-gray-600">/35</span>
                  </p>
                  {data.assessment_result.converted_mmse30 && (
                    <p className="text-sm text-gray-600 mt-1">
                      Tương đương MMSE chuẩn: <span className="font-semibold">{(data.assessment_result.converted_mmse30 ?? 0).toFixed(1)}/30</span>
                    </p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    Thang điểm MEC 35 (Lobo et al. 1979)
                  </p>
                </div>

                {data.assessment_result.adjusted_score && (
                  <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-600">Điểm Điều Chỉnh</span>
                    </div>
                    <p className="text-3xl font-bold text-purple-700">
                      {(data.assessment_result.adjusted_score ?? 0).toFixed(1)}
                      <span className="text-lg text-gray-600">/35</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Điều chỉnh theo tuổi ({data.assessment_result.age}) và học vấn ({data.assessment_result.education_years} năm)
                    </p>
                    <p className="text-xs text-gray-500">
                      Citation: Murden et al. (1991), Vietnamese JINS 2025
                    </p>
                  </div>
                )}

                {data.assessment_result.scale_info && (
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Info className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-gray-600">Về Thang Điểm MEC 35</span>
                    </div>
                    <div className="text-xs text-gray-700 leading-relaxed space-y-2">
                      <p>
                        Bài kiểm tra sử dụng thang điểm <strong>MEC 35 điểm</strong> (Mini-Examen-Cognoscivo), 
                        mở rộng từ MMSE 30 điểm chuẩn (Folstein et al. 1975) để đánh giá toàn diện hơn.
                      </p>
                      <div className="mt-2">
                        <p className="font-semibold mb-1">Khác biệt so với MMSE chuẩn:</p>
                        <ul className="list-disc list-inside space-y-1 ml-2">
                          <li>{data.assessment_result.scale_info.differences?.visuospatial || 'Visuospatial: 3 điểm (thay vì 1) - Clock Drawing Test đầy đủ'}</li>
                          <li>{data.assessment_result.scale_info.differences?.executive_function || 'Executive Function: 3 điểm (mới thêm) - Verbal fluency + Abstraction'}</li>
                          <li>{data.assessment_result.scale_info.differences?.total_questions || 'Tổng: 28 câu chấm điểm + 4 câu mở (tổng 32 câu)'}</li>
                        </ul>
                      </div>
                      <p className="text-xs text-gray-500 mt-2 italic">
                        {data.assessment_result.scale_info.citation || 'Lobo et al. (1979), Modrego et al. (2005, 2013)'}
                      </p>
                    </div>
                  </div>
                )}

                <div className={`p-4 rounded-lg border-2 ${getRiskColor(data.assessment_result.risk_level)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {getRiskIcon(data.assessment_result.risk_level)}
                    <span className="text-sm font-medium">Mức Độ Nguy Cơ</span>
                  </div>
                  <p className="text-xl font-bold mt-1">
                    {data.assessment_result.risk_level_label}
                  </p>
                  <p className="text-sm mt-2">
                    Xác suất MCI: {((data.assessment_result.mci_probability ?? 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              {/* Clinical Thresholds */}
              <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <BookOpen className="w-4 h-4" />
                  Ngưỡng Lâm Sàng (Clinical Thresholds)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-green-700">Bình thường</p>
                    <p className="text-gray-600">≥ {data.assessment_result.thresholds?.normal?.min ?? 24} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-yellow-700">MCI nhẹ</p>
                    <p className="text-gray-600">{data.assessment_result.thresholds?.mild_mci?.min ?? 18}-{data.assessment_result.thresholds?.mild_mci?.max ?? 23} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-orange-700">Sa sút trí tuệ vừa</p>
                    <p className="text-gray-600">{data.assessment_result.thresholds?.moderate?.min ?? 10}-{data.assessment_result.thresholds?.moderate?.max ?? 17} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-red-700">Sa sút trí tuệ nặng</p>
                    <p className="text-gray-600">&lt; {((data.assessment_result.thresholds?.severe?.max ?? 9) + 1)} điểm</p>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                  Citation: Folstein et al. (1975), Petersen et al. (1999)
                </p>
              </div>

              {/* Score Interpretation */}
              <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                <h3 className="font-semibold text-gray-900 mb-2">Diễn Giải Điểm Số</h3>
                <p className="text-gray-700 leading-relaxed">
                  {typeof data.clinical_interpretation.score_interpretation === 'string' 
                    ? data.clinical_interpretation.score_interpretation 
                    : (data.clinical_interpretation.score_interpretation?.description || 'N/A')}
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* Feature Analysis */}
      <Card className="p-6 shadow-lg">
        <div 
          className="flex items-center justify-between cursor-pointer"
          onClick={() => toggleSection('features')}
        >
          <div className="flex items-center gap-3">
            <Activity className="w-6 h-6 text-green-600" />
            <h2 className="text-2xl font-bold text-gray-900">
              Phân Tích Đặc Trưng
            </h2>
            <span className="text-sm bg-gray-200 px-2 py-1 rounded">
              {data.feature_summary.total_features} features
            </span>
          </div>
          {expandedSections.has('features') ? (
            <ChevronUp className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          )}
        </div>

        <AnimatePresence>
          {expandedSections.has('features') && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 space-y-4"
            >
              {/* Feature Summary */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Mic className="w-5 h-5 text-blue-600" />
                    <span className="text-sm font-medium">Đặc trưng Âm thanh</span>
                  </div>
                  <p className="text-2xl font-bold text-blue-700">
                    {data.feature_summary.acoustic_feature_count}
                  </p>
                  {data.feature_summary.abnormal_acoustic > 0 && (
                    <p className="text-xs text-red-600 mt-1">
                      {data.feature_summary.abnormal_acoustic} bất thường
                    </p>
                  )}
                </div>

                <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                    <span className="text-sm font-medium">Đặc trưng Ngôn ngữ</span>
                  </div>
                  <p className="text-2xl font-bold text-purple-700">
                    {data.feature_summary.linguistic_feature_count}
                  </p>
                  {data.feature_summary.abnormal_linguistic > 0 && (
                    <p className="text-xs text-red-600 mt-1">
                      {data.feature_summary.abnormal_linguistic} bất thường
                    </p>
                  )}
                </div>

                <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <span className="text-sm font-medium text-gray-600">Tổng Features</span>
                  <p className="text-2xl font-bold text-gray-700">
                    {data.feature_summary.total_features}
                  </p>
                </div>

                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <span className="text-sm font-medium text-gray-600">Bất thường</span>
                  <p className="text-2xl font-bold text-red-700">
                    {data.feature_summary.total_abnormal_features}
                  </p>
                  <p className="text-xs text-gray-600 mt-1">
                    ({data.feature_summary.abnormal_percentage}%)
                  </p>
                </div>
              </div>

              {/* Detailed Features - Acoustic */}
              {data.detailed_analysis?.acoustic && Object.keys(data.detailed_analysis.acoustic).length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Mic className="w-5 h-5 text-blue-600" />
                    Đặc Trưng Âm Thanh Chi Tiết
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(data.detailed_analysis.acoustic).map(([key, feature]) => {
                      const severity: 'normal' | 'borderline' | 'mild' | 'moderate' | 'severe' = 
                        (feature.severity as any) || (feature.is_abnormal ? 'moderate' : 'normal');
                      const severityColors: Record<string, string> = {
                        'normal': 'bg-green-50 border-green-200 text-green-700',
                        'borderline': 'bg-yellow-50 border-yellow-200 text-yellow-700',
                        'mild': 'bg-orange-50 border-orange-200 text-orange-700',
                        'moderate': 'bg-red-50 border-red-200 text-red-700',
                        'severe': 'bg-red-100 border-red-300 text-red-800'
                      };
                      const severityLabels: Record<string, string> = {
                        'normal': 'Bình thường',
                        'borderline': 'Ranh giới',
                        'mild': 'Nhẹ',
                        'moderate': 'Trung bình',
                        'severe': 'Nghiêm trọng'
                      };
                      
                      return (
                        <div
                          key={key}
                          className={`p-4 rounded-lg border-2 ${severityColors[severity] || 'bg-white border-gray-200'}`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <span className="text-sm font-semibold text-gray-900 block mb-1">
                                {feature.description || feature.name_vi || key}
                              </span>
                              {feature.category && (
                                <span className="text-xs text-gray-500 italic">
                                  {feature.category}
                                </span>
                              )}
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className={`text-xs px-2 py-1 rounded font-semibold ${
                                severity === 'normal' ? 'bg-green-200 text-green-800' :
                                severity === 'borderline' ? 'bg-yellow-200 text-yellow-800' :
                                severity === 'mild' ? 'bg-orange-200 text-orange-800' :
                                severity === 'moderate' ? 'bg-red-200 text-red-800' :
                                'bg-red-300 text-red-900'
                              }`}>
                                {severityLabels[severity] || 'N/A'}
                              </span>
                              {feature.deviation_pct && feature.deviation_pct > 0 && (
                                <span className="text-xs text-gray-600">
                                  Lệch {feature.deviation_pct.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="mt-3 space-y-2">
                            <div>
                              <p className="text-lg font-bold text-gray-900">
                                {(feature.value ?? 0).toFixed(3)} <span className="text-sm font-normal text-gray-600">{feature.unit || ''}</span>
                              </p>
                            </div>
                            
                            {feature.normal_range && (
                              <div className="text-xs">
                                {typeof feature.normal_range === 'string' ? (
                                  <p className="text-gray-600">Khoảng bình thường: {feature.normal_range}</p>
                                ) : (
                                  <p className="text-gray-600">
                                    Khoảng bình thường: {Array.isArray(feature.normal_range) 
                                      ? `${feature.normal_range[0]}-${feature.normal_range[1]}` 
                                      : feature.normal_range.display || 'N/A'} {feature.unit || ''}
                                  </p>
                                )}
                              </div>
                            )}
                            
                            {feature.interpretation && (
                              <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                                <p className="text-xs font-medium text-gray-700 mb-1">Giải thích:</p>
                                <p className="text-xs text-gray-600 leading-relaxed">
                                  {typeof feature.interpretation === 'string' 
                                    ? feature.interpretation 
                                    : feature.interpretation.description || 'N/A'}
                                </p>
                              </div>
                            )}
                            
                            {feature.clinical_significance && (
                              <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                                <p className="text-xs font-medium text-blue-700 mb-1">Ý nghĩa lâm sàng:</p>
                                <p className="text-xs text-blue-600 leading-relaxed">
                                  {feature.clinical_significance}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Detailed Features - Linguistic */}
              {data.detailed_analysis?.linguistic && Object.keys(data.detailed_analysis.linguistic).length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                    Đặc Trưng Ngôn Ngữ Chi Tiết
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {Object.entries(data.detailed_analysis.linguistic).map(([key, feature]) => {
                      const severity: 'normal' | 'borderline' | 'mild' | 'moderate' | 'severe' = 
                        (feature.severity as any) || (feature.is_abnormal ? 'moderate' : 'normal');
                      const severityColors: Record<string, string> = {
                        'normal': 'bg-green-50 border-green-200 text-green-700',
                        'borderline': 'bg-yellow-50 border-yellow-200 text-yellow-700',
                        'mild': 'bg-orange-50 border-orange-200 text-orange-700',
                        'moderate': 'bg-red-50 border-red-200 text-red-700',
                        'severe': 'bg-red-100 border-red-300 text-red-800'
                      };
                      const severityLabels: Record<string, string> = {
                        'normal': 'Bình thường',
                        'borderline': 'Ranh giới',
                        'mild': 'Nhẹ',
                        'moderate': 'Trung bình',
                        'severe': 'Nghiêm trọng'
                      };
                      
                      return (
                        <div
                          key={key}
                          className={`p-4 rounded-lg border-2 ${severityColors[severity] || 'bg-white border-gray-200'}`}
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <span className="text-sm font-semibold text-gray-900 block mb-1">
                                {feature.description || feature.name_vi || key}
                              </span>
                              {feature.category && (
                                <span className="text-xs text-gray-500 italic">
                                  {feature.category}
                                </span>
                              )}
                            </div>
                            <div className="flex flex-col items-end gap-1">
                              <span className={`text-xs px-2 py-1 rounded font-semibold ${
                                severity === 'normal' ? 'bg-green-200 text-green-800' :
                                severity === 'borderline' ? 'bg-yellow-200 text-yellow-800' :
                                severity === 'mild' ? 'bg-orange-200 text-orange-800' :
                                severity === 'moderate' ? 'bg-red-200 text-red-800' :
                                'bg-red-300 text-red-900'
                              }`}>
                                {severityLabels[severity] || 'N/A'}
                              </span>
                              {feature.deviation_pct && feature.deviation_pct > 0 && (
                                <span className="text-xs text-gray-600">
                                  Lệch {feature.deviation_pct.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="mt-3 space-y-2">
                            <div>
                              <p className="text-lg font-bold text-gray-900">
                                {(feature.value ?? 0).toFixed(3)} <span className="text-sm font-normal text-gray-600">{feature.unit || ''}</span>
                              </p>
                            </div>
                            
                            {feature.normal_range && (
                              <div className="text-xs">
                                {typeof feature.normal_range === 'string' ? (
                                  <p className="text-gray-600">Khoảng bình thường: {feature.normal_range}</p>
                                ) : (
                                  <p className="text-gray-600">
                                    Khoảng bình thường: {Array.isArray(feature.normal_range) 
                                      ? `${feature.normal_range[0]}-${feature.normal_range[1]}` 
                                      : feature.normal_range.display || 'N/A'} {feature.unit || ''}
                                  </p>
                                )}
                              </div>
                            )}
                            
                            {feature.interpretation && (
                              <div className="mt-2 p-2 bg-white rounded border border-gray-200">
                                <p className="text-xs font-medium text-gray-700 mb-1">Giải thích:</p>
                                <p className="text-xs text-gray-600 leading-relaxed">
                                  {typeof feature.interpretation === 'string' 
                                    ? feature.interpretation 
                                    : feature.interpretation.description || 'N/A'}
                                </p>
                              </div>
                            )}
                            
                            {feature.clinical_significance && (
                              <div className="mt-2 p-2 bg-blue-50 rounded border border-blue-200">
                                <p className="text-xs font-medium text-blue-700 mb-1">Ý nghĩa lâm sàng:</p>
                                <p className="text-xs text-blue-600 leading-relaxed">
                                  {feature.clinical_significance}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* SHAP Explanations */}
      {data.shap_explanation && data.shap_explanation.top_risk_factors.length > 0 && (
        <Card className="p-6 shadow-lg">
          <div 
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('shap')}
          >
            <div className="flex items-center gap-3">
              <BarChart3 className="w-6 h-6 text-orange-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                Giải Thích SHAP (Feature Importance)
              </h2>
              <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">
                Citation: Lundberg & Lee (2017)
              </span>
            </div>
            {expandedSections.has('shap') ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>

          <AnimatePresence>
            {expandedSections.has('shap') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 space-y-4"
              >
                {/* Top Risk Factors */}
                {data.shap_explanation.top_risk_factors.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-red-700 mb-3 flex items-center gap-2">
                      <AlertCircle className="w-5 h-5" />
                      Top {data.shap_explanation.top_risk_factors.length} Yếu Tố Nguy Cơ
                    </h3>
                    <div className="space-y-4">
                      {data.shap_explanation.top_risk_factors.map((factor, idx) => (
                        <div
                          key={idx}
                          className="bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-300 rounded-lg p-5 shadow-sm"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-lg font-bold text-red-700">#{idx + 1}</span>
                                <p className="text-lg font-bold text-red-900">
                                  {factor.feature_name_vi || factor.feature || 'Đặc trưng không xác định'}
                                </p>
                              </div>
                              {factor.feature_name_en && (
                                <p className="text-sm text-gray-600 italic">
                                  {factor.feature_name_en}
                                </p>
                              )}
                            </div>
                            <div className="text-right bg-white px-3 py-2 rounded-lg border border-red-200">
                              <p className="text-xl font-bold text-red-700">
                                +{(factor.shap_value ?? 0).toFixed(3)}
                              </p>
                              <p className="text-xs text-gray-600 mt-1">
                                SHAP Value
                              </p>
                              {factor.absolute_importance && (
                                <p className="text-xs text-gray-500 mt-1">
                                  Importance: {((factor.absolute_importance ?? 0) * 100).toFixed(1)}%
                                </p>
                              )}
                            </div>
                          </div>
                          
                          <div className="mt-4 space-y-3">
                            <div className="grid grid-cols-2 gap-3">
                              <div className="bg-white p-3 rounded-lg border border-gray-200">
                                <p className="text-xs font-medium text-gray-600 mb-1">Giá trị đo được</p>
                                <p className="text-lg font-bold text-gray-900">
                                  {(factor.value ?? 0).toFixed(3)}
                                  {factor.unit && <span className="text-sm font-normal text-gray-600 ml-1">{factor.unit}</span>}
                                </p>
                                {factor.comparison && (
                                  <p className="text-xs text-gray-500 mt-1">
                                    {factor.comparison}
                                  </p>
                                )}
                              </div>
                              
                              <div className="bg-white p-3 rounded-lg border border-gray-200">
                                <p className="text-xs font-medium text-gray-600 mb-1">Khoảng bình thường</p>
                                {factor.normal_range ? (
                                  Array.isArray(factor.normal_range) ? (
                                    <p className="text-sm font-semibold text-gray-900">
                                      {factor.normal_range[0]}-{factor.normal_range[1]}
                                      {factor.unit && <span className="text-xs font-normal text-gray-600 ml-1">{factor.unit}</span>}
                                    </p>
                                  ) : (
                                    <p className="text-sm font-semibold text-gray-900">
                                      {typeof factor.normal_range === 'object' && factor.normal_range !== null && 'display' in factor.normal_range
                                        ? (factor.normal_range as { display?: string }).display || 'N/A'
                                        : String(factor.normal_range)}
                                    </p>
                                  )
                                ) : (
                                  <p className="text-sm text-gray-500">N/A</p>
                                )}
                              </div>
                            </div>
                            
                            {factor.interpretation && (
                              <div className="bg-white p-3 rounded-lg border-2 border-red-200">
                                <p className="text-sm font-semibold text-gray-900 mb-2 flex items-center gap-2">
                                  <AlertCircle className="w-4 h-4 text-red-600" />
                                  Ảnh hưởng đến nguy cơ
                                </p>
                                <p className="text-sm text-gray-700 leading-relaxed">
                                  {typeof factor.interpretation === 'string' 
                                    ? factor.interpretation 
                                    : (factor.interpretation?.description || factor.explanation_vi || 'N/A')}
                                </p>
                              </div>
                            )}
                            
                            {factor.recommendation && (
                              <div className="bg-blue-50 p-3 rounded-lg border-2 border-blue-200">
                                <p className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
                                  <CheckCircle className="w-4 h-4 text-blue-600" />
                                  Khuyến nghị
                                </p>
                                <p className="text-sm text-blue-700 leading-relaxed">
                                  {typeof factor.recommendation === 'string' 
                                    ? factor.recommendation 
                                    : (factor.recommendation?.title || factor.recommendation?.description || 'N/A')}
                                </p>
                              </div>
                            )}
                            
                            {factor.citation && (
                              <p className="text-xs text-gray-500 italic text-right">
                                {factor.citation}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Top Protective Factors */}
                {data.shap_explanation.top_protective_factors.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-green-700 mb-3 flex items-center gap-2">
                      <Shield className="w-5 h-5" />
                      Top {data.shap_explanation.top_protective_factors.length} Yếu Tố Bảo Vệ
                    </h3>
                    <div className="space-y-3">
                      {data.shap_explanation.top_protective_factors.map((factor, idx) => (
                        <div
                          key={idx}
                          className="bg-green-50 border-2 border-green-200 rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="font-semibold text-green-900">
                                #{idx + 1}. {factor.feature_name_vi}
                              </p>
                              <p className="text-sm text-gray-600 italic">
                                {factor.feature_name_en}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-green-700">
                                SHAP: {(factor.shap_value ?? 0).toFixed(3)}
                              </p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 mt-2">
                            {typeof factor.interpretation === 'string' 
                              ? factor.interpretation 
                              : (factor.interpretation?.description || 'N/A')}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Grouped Contributions */}
                {data.shap_explanation?.grouped_contributions && Object.keys(data.shap_explanation.grouped_contributions).length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      Đóng Góp Theo Nhóm
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      {Object.entries(data.shap_explanation.grouped_contributions).map(([group, value]) => (
                        <div key={group} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                          <p className="font-medium text-gray-700 capitalize">
                            {group.replace('_', ' ')}
                          </p>
                          <p className="text-2xl font-bold text-gray-900 mt-2">
                            {typeof value === 'number' && value != null ? value.toFixed(3) : 'N/A'}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      )}

      {/* Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <Card className="p-6 shadow-lg">
          <div 
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('recommendations')}
          >
            <div className="flex items-center gap-3">
              <Target className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                Khuyến Nghị
              </h2>
            </div>
            {expandedSections.has('recommendations') ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>

          <AnimatePresence>
            {expandedSections.has('recommendations') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6"
              >
                <ul className="space-y-3">
                  {data.recommendations.map((rec, idx) => {
                    // Handle both string and object recommendations
                    if (typeof rec === 'string') {
                      return (
                        <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                          <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-700">{rec}</span>
                        </li>
                      );
                    } else if (typeof rec === 'object' && rec !== null) {
                      // Render structured recommendation object
                      return (
                        <li key={idx} className="p-4 bg-white rounded-lg border-2 border-blue-200 shadow-sm">
                          <div className="flex items-start gap-3 mb-2">
                            <CheckCircle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                              rec.priority === 'urgent' ? 'text-red-600' :
                              rec.priority === 'high' ? 'text-orange-600' :
                              'text-blue-600'
                            }`} />
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 mb-1">{rec.title || 'Khuyến nghị'}</h4>
                              {rec.description && (
                                <p className="text-sm text-gray-600 mb-2">{rec.description}</p>
                              )}
                              {rec.actions && Array.isArray(rec.actions) && rec.actions.length > 0 && (
                                <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 ml-2">
                                  {rec.actions.map((action: string, actionIdx: number) => (
                                    <li key={actionIdx}>{action}</li>
                                  ))}
                                </ul>
                              )}
                              {rec.rationale && (
                                <p className="text-xs text-gray-500 mt-2 italic">{rec.rationale}</p>
                              )}
                            </div>
                          </div>
                        </li>
                      );
                    }
                    return null;
                  })}
                </ul>
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      )}

      {/* Citations */}
      {data.citations && data.citations.length > 0 && (
        <Card className="p-6 shadow-lg">
          <div 
            className="flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection('citations')}
          >
            <div className="flex items-center gap-3">
              <BookOpen className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                Tài Liệu Tham Khảo
              </h2>
              <span className="text-sm bg-purple-100 text-purple-700 px-2 py-1 rounded">
                {data.citations.length} citations
              </span>
            </div>
            {expandedSections.has('citations') ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </div>

          <AnimatePresence>
            {expandedSections.has('citations') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-6 space-y-3"
              >
                {data.citations.map((citation, idx) => (
                  <div key={idx} className="bg-gray-50 p-4 rounded-lg border border-gray-200">
                    <p className="font-semibold text-gray-900">
                      {citation.authors} ({citation.year})
                    </p>
                    <p className="text-gray-700 italic mt-1">
                      {citation.title}
                    </p>
                    {citation.journal && (
                      <p className="text-sm text-gray-600 mt-1">
                        {citation.journal}
                        {citation.volume && `, ${citation.volume}`}
                        {citation.pages && `, pp. ${citation.pages}`}
                      </p>
                    )}
                    {citation.doi && (
                      <p className="text-xs text-blue-600 mt-1">
                        DOI: {citation.doi}
                      </p>
                    )}
                    <p className="text-sm text-gray-600 mt-2">
                      {citation.description}
                    </p>
                  </div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </Card>
      )}
    </div>
  );
}



