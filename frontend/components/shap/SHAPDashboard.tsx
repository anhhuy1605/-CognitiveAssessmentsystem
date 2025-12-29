'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle2, AlertTriangle, XCircle, Info, Download, Play } from 'lucide-react';

interface SHAPData {
  summary: string;
  risk_level: 'low' | 'mild' | 'moderate' | 'severe';
  risk_explanation: string;
  mmse_score: number;
  positive_factors: Factor[];
  negative_factors: Factor[];
  feature_interactions: string[];
  grouped_contributions: Record<string, any>;
  recommendations: Recommendation[];
  confidence: Confidence;
  next_steps: string;
  visualizations?: {
    waterfall?: string;
    importance_bar?: string;
    radar_chart?: string;
    risk_gauge?: string;
  };
}

interface Factor {
  feature: string;
  feature_display_name: string;
  contribution: number;
  value: number;
  interpretation: string;
  comparison: {
    percentile: number;
    interpretation: string;
    in_normal_range: boolean;
  };
  recommendation: string;
  severity: string;
}

interface Recommendation {
  category: string;
  items: Array<{
    title: string;
    suggestions: string[];
  }>;
}

interface Confidence {
  level: 'high' | 'moderate' | 'low';
  explanation: string;
  uncertainty_factors: string[];
}

interface SHAPDashboardProps {
  sessionId: string;
  shapData?: SHAPData;
}

const SHAPDashboard: React.FC<SHAPDashboardProps> = ({ sessionId, shapData: initialData }) => {
  const [shapData, setShapData] = useState<SHAPData | null>(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [activeTab, setActiveTab] = useState('summary');
  const [showDetails, setShowDetails] = useState(false);
  const [animationPlaying, setAnimationPlaying] = useState(false);

  useEffect(() => {
    if (!initialData && sessionId) {
      fetchSHAPData();
    }
  }, [sessionId]);

  const fetchSHAPData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/shap-explanations/${sessionId}`);
      if (!response.ok) throw new Error('Failed to fetch SHAP data');
      const data = await response.json();
      setShapData(data);
    } catch (error) {
      console.error('Error fetching SHAP data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return 'bg-green-500';
      case 'mild': return 'bg-yellow-500';
      case 'moderate': return 'bg-orange-500';
      case 'severe': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getRiskIcon = (risk: string) => {
    switch (risk) {
      case 'low': return <CheckCircle2 className="w-6 h-6 text-green-500" />;
      case 'mild': return <AlertTriangle className="w-6 h-6 text-yellow-500" />;
      case 'moderate': return <AlertTriangle className="w-6 h-6 text-orange-500" />;
      case 'severe': return <XCircle className="w-6 h-6 text-red-500" />;
      default: return <Info className="w-6 h-6 text-gray-500" />;
    }
  };

  const downloadReport = async () => {
    try {
      const response = await fetch(`/api/shap-report/${sessionId}?format=pdf`);
      if (!response.ok) throw new Error('Failed to generate report');
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cognitive-assessment-${sessionId}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!shapData) {
    return (
      <Alert>
        <AlertDescription>No SHAP explanation data available for this session.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6 p-6">
      {/* Summary Card */}
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl">Kết quả Đánh giá Nhận thức</CardTitle>
            <Button onClick={downloadReport} variant="primaryOutline" size="sm">
              <Download className="w-4 h-4 mr-2" />
              Tải báo cáo
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* MMSE Score */}
            <div className="text-center">
              <div className="text-5xl font-bold text-blue-600 mb-2">
                {shapData.mmse_score}/30
              </div>
              <div className="text-sm text-gray-600">Điểm MMSE</div>
            </div>

            {/* Risk Level */}
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                {getRiskIcon(shapData.risk_level)}
              </div>
              <Badge className={`${getRiskColor(shapData.risk_level)} text-white`}>
                {shapData.risk_level.toUpperCase()}
              </Badge>
              <div className="text-sm text-gray-600 mt-2">Mức độ nguy cơ</div>
            </div>

            {/* Confidence */}
            <div className="text-center">
              <div className="text-2xl font-semibold mb-2">
                {shapData.confidence.level === 'high' ? 'Cao' : 
                 shapData.confidence.level === 'moderate' ? 'Trung bình' : 'Thấp'}
              </div>
              <div className="text-sm text-gray-600">Độ tin cậy</div>
            </div>
          </div>

          <div className="mt-6">
            <p className="text-gray-700">{shapData.summary}</p>
            <Button
              onClick={() => setShowDetails(!showDetails)}
              variant="ghost"
              size="sm"
              className="mt-4"
            >
              {showDetails ? 'Ẩn chi tiết' : 'Xem chi tiết'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Main Contributing Factors */}
      {showDetails && (
        <Card>
          <CardHeader>
            <CardTitle>Các yếu tố chính ảnh hưởng đến kết quả</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Positive Factors */}
              <div>
                <h3 className="text-lg font-semibold text-green-700 mb-4 flex items-center">
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  Điểm mạnh
                </h3>
                <div className="space-y-4">
                  {shapData.positive_factors.map((factor, idx) => (
                    <div key={idx} className="p-4 bg-green-50 border-l-4 border-green-500 rounded">
                      <h4 className="font-semibold text-green-800">{factor.feature_display_name}</h4>
                      <p className="text-sm text-gray-700 mt-1">{factor.interpretation}</p>
                      <p className="text-xs text-gray-600 mt-2">
                        {factor.comparison.interpretation}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Negative Factors */}
              <div>
                <h3 className="text-lg font-semibold text-red-700 mb-4 flex items-center">
                  <AlertTriangle className="w-5 h-5 mr-2" />
                  Vấn đề cần chú ý
                </h3>
                <div className="space-y-4">
                  {shapData.negative_factors.map((factor, idx) => (
                    <div key={idx} className="p-4 bg-red-50 border-l-4 border-red-500 rounded">
                      <h4 className="font-semibold text-red-800">{factor.feature_display_name}</h4>
                      <p className="text-sm text-gray-700 mt-1">{factor.interpretation}</p>
                      <p className="text-xs text-gray-600 mt-2">
                        {factor.comparison.interpretation}
                      </p>
                      {factor.recommendation && (
                        <p className="text-xs text-blue-600 mt-2">
                          💡 {factor.recommendation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Visualizations */}
      <Card>
        <CardHeader>
          <CardTitle>Phân tích chi tiết</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="waterfall">Phân tích</TabsTrigger>
              <TabsTrigger value="radar">Tổng quan</TabsTrigger>
              <TabsTrigger value="importance">Quan trọng</TabsTrigger>
              <TabsTrigger value="animation">Minh họa</TabsTrigger>
            </TabsList>

            <TabsContent value="waterfall" className="mt-4">
              {shapData.visualizations?.waterfall ? (
                <img
                  src={`data:image/png;base64,${shapData.visualizations.waterfall}`}
                  alt="Waterfall Plot"
                  className="w-full rounded-lg"
                />
              ) : (
                <p className="text-gray-500">Waterfall plot not available</p>
              )}
            </TabsContent>

            <TabsContent value="radar" className="mt-4">
              {shapData.visualizations?.radar_chart ? (
                <img
                  src={`data:image/png;base64,${shapData.visualizations.radar_chart}`}
                  alt="Radar Chart"
                  className="w-full rounded-lg"
                />
              ) : (
                <p className="text-gray-500">Radar chart not available</p>
              )}
            </TabsContent>

            <TabsContent value="importance" className="mt-4">
              {shapData.visualizations?.importance_bar ? (
                <img
                  src={`data:image/png;base64,${shapData.visualizations.importance_bar}`}
                  alt="Feature Importance"
                  className="w-full rounded-lg"
                />
              ) : (
                <p className="text-gray-500">Importance bar chart not available</p>
              )}
            </TabsContent>

            <TabsContent value="animation" className="mt-4">
              <div className="text-center">
                <Button
                  onClick={() => setAnimationPlaying(!animationPlaying)}
                  disabled={!shapData.visualizations?.animation_html}
                >
                  <Play className="w-4 h-4 mr-2" />
                  {animationPlaying ? 'Dừng' : 'Xem giải thích động'}
                </Button>
                {animationPlaying && shapData.visualizations?.animation_html && (
                  <div
                    className="mt-4"
                    dangerouslySetInnerHTML={{
                      __html: shapData.visualizations.animation_html
                    }}
                  />
                )}
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Recommendations */}
      <Card>
        <CardHeader>
          <CardTitle>💡 Khuyến nghị</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {shapData.recommendations.map((recGroup, idx) => (
              <div key={idx}>
                <h3 className="text-lg font-semibold mb-3">{recGroup.category}</h3>
                <div className="space-y-4">
                  {recGroup.items.map((item, itemIdx) => (
                    <div key={itemIdx} className="p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-semibold text-yellow-800 mb-2">{item.title}</h4>
                      <ul className="list-disc list-inside space-y-1 ml-4">
                        {item.suggestions.map((suggestion, sugIdx) => (
                          <li key={sugIdx} className="text-sm text-gray-700">
                            {suggestion}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Next Steps */}
      <Alert>
        <Info className="h-4 w-4" />
        <AlertDescription>
          <strong>Bước tiếp theo:</strong> {shapData.next_steps}
        </AlertDescription>
      </Alert>

      {/* Technical Details (Collapsible) */}
      <details className="bg-gray-50 p-4 rounded-lg">
        <summary className="cursor-pointer font-semibold text-gray-700">
          Thông tin kỹ thuật (dành cho bác sĩ)
        </summary>
        <div className="mt-4 space-y-2 text-sm text-gray-600">
          <p><strong>Model:</strong> Ensemble (SHAP TreeExplainer)</p>
          <p><strong>Confidence:</strong> {shapData.confidence.level} - {shapData.confidence.explanation}</p>
          {shapData.confidence.uncertainty_factors.length > 0 && (
            <p><strong>Yếu tố không chắc chắn:</strong> {shapData.confidence.uncertainty_factors.join(', ')}</p>
          )}
        </div>
      </details>
    </div>
  );
};

export default SHAPDashboard;

