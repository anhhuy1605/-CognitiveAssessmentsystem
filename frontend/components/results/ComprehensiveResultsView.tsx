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
    age: number;
    education_years: number;
    mci_probability: number;
    risk_level: string;
    risk_level_label: string;
    classification: string;
    confidence: number;
    thresholds: any;
    education_specific_thresholds: any;
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
      feature_name_vi: string;
      feature_name_en: string;
      shap_value: number;
      absolute_importance: number;
      value: number;
      normal_range: number[];
      comparison: string;
      interpretation: string;
      explanation_vi: string;
      recommendation: string;
      citation: string;
    }>;
    top_protective_factors: Array<any>;
    grouped_contributions: Record<string, number>;
    total_contribution: number;
    citation: string;
  };
  recommendations: string[];
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
    score_interpretation: string;
    risk_interpretation: string;
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
                    <span className="text-sm font-medium text-gray-600">Điểm MMSE Thô</span>
                  </div>
                  <p className="text-3xl font-bold text-blue-700">
                    {data.assessment_result.raw_score.toFixed(1)}
                    <span className="text-lg text-gray-600">/35</span>
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Citation: Folstein et al. (1975)
                  </p>
                </div>

                {data.assessment_result.adjusted_score && (
                  <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <TrendingUp className="w-5 h-5 text-purple-600" />
                      <span className="text-sm font-medium text-gray-600">Điểm Điều Chỉnh</span>
                    </div>
                    <p className="text-3xl font-bold text-purple-700">
                      {data.assessment_result.adjusted_score.toFixed(1)}
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

                <div className={`p-4 rounded-lg border-2 ${getRiskColor(data.assessment_result.risk_level)}`}>
                  <div className="flex items-center gap-2 mb-2">
                    {getRiskIcon(data.assessment_result.risk_level)}
                    <span className="text-sm font-medium">Mức Độ Nguy Cơ</span>
                  </div>
                  <p className="text-xl font-bold mt-1">
                    {data.assessment_result.risk_level_label}
                  </p>
                  <p className="text-sm mt-2">
                    Xác suất MCI: {(data.assessment_result.mci_probability * 100).toFixed(1)}%
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
                    <p className="text-gray-600">≥ {data.assessment_result.thresholds.normal.min} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-yellow-700">MCI nhẹ</p>
                    <p className="text-gray-600">{data.assessment_result.thresholds.mild_mci.min}-{data.assessment_result.thresholds.mild_mci.max} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-orange-700">Sa sút trí tuệ vừa</p>
                    <p className="text-gray-600">{data.assessment_result.thresholds.moderate.min}-{data.assessment_result.thresholds.moderate.max} điểm</p>
                  </div>
                  <div className="bg-white p-3 rounded border">
                    <p className="font-semibold text-red-700">Sa sút trí tuệ nặng</p>
                    <p className="text-gray-600">&lt; {data.assessment_result.thresholds.severe.max + 1} điểm</p>
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
                  {data.clinical_interpretation.score_interpretation}
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
              {Object.keys(data.detailed_analysis.acoustic).length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Mic className="w-5 h-5 text-blue-600" />
                    Đặc Trưng Âm Thanh Chi Tiết
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(data.detailed_analysis.acoustic).map(([key, feature]) => (
                      <div
                        key={key}
                        className={`p-3 rounded-lg border ${
                          feature.is_abnormal 
                            ? 'bg-red-50 border-red-200' 
                            : 'bg-white border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            {feature.description || key}
                          </span>
                          {feature.is_abnormal && (
                            <AlertCircle className="w-4 h-4 text-red-600" />
                          )}
                        </div>
                        <p className="text-lg font-bold text-gray-900">
                          {feature.value.toFixed(3)} {feature.unit}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Bình thường: {feature.normal_range[0]}-{feature.normal_range[1]} {feature.unit}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Features - Linguistic */}
              {Object.keys(data.detailed_analysis.linguistic).length > 0 && (
                <div className="mt-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-purple-600" />
                    Đặc Trưng Ngôn Ngữ Chi Tiết
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(data.detailed_analysis.linguistic).map(([key, feature]) => (
                      <div
                        key={key}
                        className={`p-3 rounded-lg border ${
                          feature.is_abnormal 
                            ? 'bg-red-50 border-red-200' 
                            : 'bg-white border-gray-200'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            {feature.description || key}
                          </span>
                          {feature.is_abnormal && (
                            <AlertCircle className="w-4 h-4 text-red-600" />
                          )}
                        </div>
                        <p className="text-lg font-bold text-gray-900">
                          {feature.value.toFixed(3)} {feature.unit}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Bình thường: {feature.normal_range[0]}-{feature.normal_range[1]} {feature.unit}
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
                    <div className="space-y-3">
                      {data.shap_explanation.top_risk_factors.map((factor, idx) => (
                        <div
                          key={idx}
                          className="bg-red-50 border-2 border-red-200 rounded-lg p-4"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div>
                              <p className="font-semibold text-red-900">
                                #{idx + 1}. {factor.feature_name_vi}
                              </p>
                              <p className="text-sm text-gray-600 italic">
                                {factor.feature_name_en}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-lg font-bold text-red-700">
                                SHAP: +{factor.shap_value.toFixed(3)}
                              </p>
                              <p className="text-xs text-gray-600">
                                Importance: {factor.absolute_importance.toFixed(3)}
                              </p>
                            </div>
                          </div>
                          
                          <div className="mt-3 space-y-2 text-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">Giá trị:</span>
                              <span>{factor.value.toFixed(3)}</span>
                              <span className="text-gray-500">({factor.comparison})</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium">Khoảng bình thường:</span>
                              <span>{factor.normal_range[0]}-{factor.normal_range[1]}</span>
                            </div>
                            <div className="bg-white p-2 rounded border border-red-200">
                              <p className="font-medium text-gray-900">Ảnh hưởng:</p>
                              <p className="text-gray-700">{factor.interpretation}</p>
                            </div>
                            <div className="bg-white p-2 rounded border border-blue-200">
                              <p className="font-medium text-gray-900">Khuyến nghị:</p>
                              <p className="text-gray-700">{factor.recommendation}</p>
                            </div>
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
                                SHAP: {factor.shap_value.toFixed(3)}
                              </p>
                            </div>
                          </div>
                          <p className="text-sm text-gray-700 mt-2">
                            {factor.interpretation}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Grouped Contributions */}
                {Object.keys(data.shap_explanation.grouped_contributions).length > 0 && (
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
                            {typeof value === 'number' ? value.toFixed(3) : 'N/A'}
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
                <ul className="space-y-2">
                  {data.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{rec}</span>
                    </li>
                  ))}
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

