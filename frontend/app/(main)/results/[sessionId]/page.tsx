"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Download, Share2, ArrowLeft, TrendingUp, Brain, MessageSquare, Volume2 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface AssessmentResult {
  sessionId: string;
  comprehensiveReport: {
    totalScore: number;
    mmseScore: number;
    cognitiveLevel: 'normal' | 'mild' | 'moderate' | 'severe';
    questions: Array<{
      questionId: string;
      score: number;
      evaluation: string;
      feedback: string;
      linguisticAnalysis?: {
        fluency: number;
        vocabulary: number;
        grammar: number;
        coherence: number;
      };
      audioFeatures?: {
        duration: number;
        pauses: number;
        volume: number;
        clarity: number;
      };
    }>;
  };
  chartData: {
    scoreProgression: Array<{ question: string; score: number }>;
    languageBreakdown: Array<{
      question: string;
      vocabulary: number;
      coherence: number;
      completeness: number;
    }>;
    audioQuality: Array<{
      question: string;
      energy: number;
      speakingRate: number;
    }>;
    cognitiveIndicators: {
      memory: number;
      attention: number;
      language: number;
      executive: number;
    };
  };
  exerciseRecommendations: Array<{
    type: string;
    name: string;
    frequency: string;
    difficulty: string;
  }>;
}

const ResultsPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const sessionId = (params as { sessionId: string }).sessionId;

  const [result] = useState<AssessmentResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Redirect to main results page with sessionId parameter
    // since this old route doesn't have a working API endpoint
    const redirectToMainResults = () => {
      router.push(`/results?sessionId=${sessionId}`);
    };

    if (sessionId) {
      redirectToMainResults();
    } else {
      setLoading(false);
      setError('Session ID không hợp lệ');
    }
  }, [sessionId, router]);

  const getCognitiveLevelColor = (level: string) => {
    switch (level) {
      case 'normal': return 'bg-green-100 text-green-800';
      case 'mild': return 'bg-yellow-100 text-yellow-800';
      case 'moderate': return 'bg-orange-100 text-orange-800';
      case 'severe': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getCognitiveLevelText = (level: string) => {
    switch (level) {
      case 'normal': return 'Nhận thức bình thường';
      case 'mild': return 'Suy giảm nhẹ';
      case 'moderate': return 'Suy giảm trung bình';
      case 'severe': return 'Suy giảm nặng';
      default: return level;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-gray-600">Đang tải kết quả...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="text-center p-6">
            <p className="text-red-600 mb-4">{error || 'Không thể tải kết quả'}</p>
            <Button onClick={() => router.push('/')} variant="ghost">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Về trang chủ
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { comprehensiveReport, chartData, exerciseRecommendations } = result;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                onClick={() => router.push('/')}
                variant="ghost"
                size="sm"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Về trang chủ
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Kết quả đánh giá</h1>
                <p className="text-sm text-gray-600">Session ID: {sessionId}</p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Tải PDF
              </Button>
              <Button variant="ghost" size="sm">
                <Share2 className="w-4 h-4 mr-2" />
                Chia sẻ
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Results */}
          <div className="lg:col-span-2 space-y-6">
            {/* Overall Score */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="w-5 h-5" />
                  Kết quả tổng thể
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-600">
                      {comprehensiveReport.mmseScore}
                    </div>
                    <div className="text-sm text-gray-600">Điểm MMSE</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-600">
                      {Number(comprehensiveReport.totalScore).toFixed(2)}
                    </div>
                    <div className="text-sm text-gray-600">Tổng điểm</div>
                  </div>
                  <div className="text-center">
                    <Badge className={getCognitiveLevelColor(comprehensiveReport.cognitiveLevel)}>
                      {getCognitiveLevelText(comprehensiveReport.cognitiveLevel)}
                    </Badge>
                    <div className="text-sm text-gray-600 mt-1">Mức độ</div>
                  </div>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-600">
                      {comprehensiveReport.questions.length}
                    </div>
                    <div className="text-sm text-gray-600">Câu hỏi</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Score Progression Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Tiến trình điểm số</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={chartData.scoreProgression}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="question" />
                    <YAxis domain={[0, 10]} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Language Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Phân tích ngôn ngữ
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData.languageBreakdown}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="question" />
                    <YAxis domain={[0, 10]} />
                    <Tooltip />
                    <Bar dataKey="vocabulary" fill="#10b981" name="Từ vựng" />
                    <Bar dataKey="coherence" fill="#3b82f6" name="Mạch lạc" />
                    <Bar dataKey="completeness" fill="#f59e0b" name="Đầy đủ" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Detailed Question Results */}
            <Card>
              <CardHeader>
                <CardTitle>Kết quả chi tiết từng câu hỏi</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {comprehensiveReport.questions.map((question, index) => (
                    <div key={question.questionId} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-semibold">Câu hỏi {index + 1}</h4>
                        <Badge>{Number(question.score).toFixed(2)}/10</Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">{question.evaluation}</p>
                      <p className="text-sm text-blue-600">{question.feedback}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Cognitive Indicators */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Chỉ số nhận thức
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(chartData.cognitiveIndicators).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between">
                      <span className="text-sm capitalize">
                        {key === 'memory' && 'Bộ nhớ'}
                        {key === 'attention' && 'Chú ý'}
                        {key === 'language' && 'Ngôn ngữ'}
                        {key === 'executive' && 'Chức năng điều hành'}
                      </span>
                      <div className="flex items-center gap-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${value * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium w-8">
                          {Math.round(value * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Audio Quality */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Volume2 className="w-5 h-5" />
                  Chất lượng âm thanh
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={chartData.audioQuality}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="question" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="energy" fill="#8b5cf6" name="Năng lượng" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Exercise Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Gợi ý bài tập</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {exerciseRecommendations.slice(0, 3).map((exercise, index) => (
                    <div key={index} className="border rounded-lg p-3">
                      <h4 className="font-medium text-sm">{exercise.name}</h4>
                      <p className="text-xs text-gray-600">{exercise.frequency}</p>
                      <Badge
                        className={`text-xs mt-1 ${
                          exercise.difficulty === 'Dễ' ? 'border-green-500 text-green-700' :
                          exercise.difficulty === 'Trung bình' ? 'border-yellow-500 text-yellow-700' :
                          'border-red-500 text-red-700'
                        }`}
                      >
                        {exercise.difficulty}
                      </Badge>
                    </div>
                  ))}
                </div>
                {exerciseRecommendations.length > 3 && (
                  <p className="text-xs text-gray-500 text-center mt-2">
                    Và {exerciseRecommendations.length - 3} gợi ý khác...
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Actions */}
            <Card>
              <CardHeader>
                <CardTitle>Thao tác</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button className="w-full" variant="ghost">
                  <Download className="w-4 h-4 mr-2" />
                  Tải báo cáo PDF
                </Button>
                <Button className="w-full" variant="ghost">
                  Lịch sử đánh giá
                </Button>
                <Button className="w-full" variant="ghost">
                  Chia sẻ kết quả
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;
