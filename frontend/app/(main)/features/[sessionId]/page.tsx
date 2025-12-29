"use client";

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, ArrowLeft, TrendingUp, Brain, Volume2, FileText, BarChart3 } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

interface F0Contour {
  question_id: string;
  f0_contour: {
    f0_values: number[];
    timestamps: number[];
    f0_mean: number;
    f0_std: number;
    f0_range: number;
    f0_cv: number;
    voiced_frames: number;
    voiced_ratio: number;
  };
}

interface FeaturesData {
  success: boolean;
  session_id: string;
  summary: {
    total_questions: number;
    audio_features_count: number;
    linguistic_features_count: number;
    f0_contours_count: number;
  };
  averaged_features: {
    audio_features: Record<string, number>;
    linguistic_features: Record<string, number>;
  };
  f0_contours: F0Contour[];
  per_question_features: Array<{
    question_id: string;
    question_text: string;
    audio_features: Record<string, any>;
    linguistic_features: Record<string, any>;
    gpt_evaluation: Record<string, any>;
    transcript: string;
  }>;
}

export default function FeaturesPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params?.sessionId as string;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [features, setFeatures] = useState<FeaturesData | null>(null);

  useEffect(() => {
    if (sessionId) {
      fetchFeatures();
    }
  }, [sessionId]);

  const fetchFeatures = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/features/${sessionId}`);
      const data = await response.json();
      
      if (data.success) {
        setFeatures(data);
      } else {
        setError(data.error || 'Không thể tải features');
      }
    } catch (err) {
      setError('Lỗi khi tải features');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

  if (error || !features) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-2xl">
          <CardContent className="p-6">
            <p className="text-red-500">{error || 'Không tìm thấy features'}</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="w-4 h-4 mr-2" />
              Quay lại
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Prepare F0 contour chart data
  const f0ChartData = features.f0_contours.map(contour => {
    const data = contour.f0_contour.f0_values.map((f0, idx) => ({
      time: contour.f0_contour.timestamps[idx] || idx * 0.01,
      f0: f0
    }));
    return {
      question_id: contour.question_id,
      data: data
    };
  });

  return (
    <div className="min-h-screen p-4 md:p-8 bg-gradient-to-br from-amber-50 to-orange-50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button onClick={() => router.back()} variant="ghost" className="mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Quay lại
          </Button>
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            Chi tiết Features - Session: {sessionId}
          </h1>
          <p className="text-gray-600">
            Acoustic & Linguistic Features cho SHAP Analysis
          </p>
        </div>

        {/* Summary */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              Tổng quan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600">Tổng số câu hỏi</p>
                <p className="text-2xl font-bold">{features.summary.total_questions}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Acoustic Features</p>
                <p className="text-2xl font-bold">{features.summary.audio_features_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Linguistic Features</p>
                <p className="text-2xl font-bold">{features.summary.linguistic_features_count}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">F0 Contours</p>
                <p className="text-2xl font-bold">{features.summary.f0_contours_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* F0 Contours Visualization */}
        {features.f0_contours.length > 0 && (
          <Card className="mb-6">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Volume2 className="w-5 h-5" />
                F0 Contours (Pitch Analysis)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {features.f0_contours.map((contour, idx) => (
                  <div key={idx} className="border rounded-lg p-4">
                    <h3 className="font-semibold mb-2">Câu hỏi: {contour.question_id}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-gray-600">F0 Mean</p>
                        <p className="text-lg font-bold">{contour.f0_contour.f0_mean.toFixed(2)} Hz</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">F0 Std</p>
                        <p className="text-lg font-bold">{contour.f0_contour.f0_std.toFixed(2)} Hz</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">F0 Range</p>
                        <p className="text-lg font-bold">{contour.f0_contour.f0_range.toFixed(2)} Hz</p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Voiced Ratio</p>
                        <p className="text-lg font-bold">{(contour.f0_contour.voiced_ratio * 100).toFixed(1)}%</p>
                      </div>
                    </div>
                    {contour.f0_contour.f0_values.length > 0 && (
                      <ResponsiveContainer width="100%" height={200}>
                        <LineChart data={f0ChartData[idx].data}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="time" label={{ value: 'Time (s)', position: 'insideBottom' }} />
                          <YAxis label={{ value: 'F0 (Hz)', angle: -90, position: 'insideLeft' }} />
                          <Tooltip />
                          <Line type="monotone" dataKey="f0" stroke="#F4A261" strokeWidth={2} dot={false} />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Averaged Features */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Acoustic Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Volume2 className="w-5 h-5" />
                Acoustic Features (Averaged)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {Object.entries(features.averaged_features.audio_features).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                    <span className="text-sm font-mono">{key}</span>
                    <Badge variant="outline">{typeof value === 'number' ? value.toFixed(4) : String(value)}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Linguistic Features */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Linguistic Features (Averaged)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {Object.entries(features.averaged_features.linguistic_features).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-2 hover:bg-gray-50 rounded">
                    <span className="text-sm font-mono">{key}</span>
                    <Badge variant="outline">{typeof value === 'number' ? value.toFixed(4) : String(value)}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Per-Question Features */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Per-Question Features
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {features.per_question_features.map((question, idx) => (
                <div key={idx} className="border rounded-lg p-4">
                  <h3 className="font-semibold mb-2">{question.question_id}: {question.question_text}</h3>
                  <p className="text-sm text-gray-600 mb-2">Transcript: {question.transcript}</p>
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm font-semibold mb-1">Audio Features:</p>
                      <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
                        {Object.entries(question.audio_features || {}).slice(0, 10).map(([k, v]) => (
                          <div key={k} className="flex justify-between">
                            <span>{k}</span>
                            <span>{typeof v === 'number' ? v.toFixed(3) : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-semibold mb-1">Linguistic Features:</p>
                      <div className="text-xs space-y-1 max-h-32 overflow-y-auto">
                        {Object.entries(question.linguistic_features || {}).slice(0, 10).map(([k, v]) => (
                          <div key={k} className="flex justify-between">
                            <span>{k}</span>
                            <span>{typeof v === 'number' ? v.toFixed(3) : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

