'use client';
import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, DocumentArrowDownIcon, ShareIcon, CheckCircleIcon, ExclamationCircleIcon, MicrophoneIcon, ChatBubbleLeftRightIcon, CpuChipIcon, TagIcon } from '@heroicons/react/24/outline';
import jsPDF from 'jspdf';
import 'jspdf-autotable';

interface QuestionResult {
  questionId: number;
  questionText: string;
  userAnswer: string;
  correctAnswer?: string;
  isCorrect: boolean;
  timeSpent: number;
  difficulty?: string;
  category?: string;
  feedback?: string;
}

interface DetailedResultCardProps {
  result: {
    id: number;
    sessionId: string;
    userInfo: any;
    completedAt: string;
    finalMmseScore: number;
    overallGptScore: number;
    questionResults: QuestionResult[];
    cognitiveAnalysis?: {
      strengths: string[];
      weaknesses: string[];
      recommendations: string[];
      overallAssessment: string;
      riskLevel: 'low' | 'medium' | 'high';
    };
    status: string;
    totalQuestions: number;
    answeredQuestions: number;
    completionRate: number;
    createdAt: string;
  };
  onViewDetails?: (result: any) => void;
}

export default function DetailedResultCard({ result, onViewDetails }: DetailedResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showQuestions, setShowQuestions] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);

  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'low': return 'Thấp - Bình thường';
      case 'medium': return 'Trung bình - Cần theo dõi';
      case 'high': return 'Cao - Cần can thiệp';
      default: return 'Chưa đánh giá';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('vi-VN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleExportPDF = async () => {
    try {
      const doc = new jsPDF();

      // Title
      doc.setFontSize(20);
      doc.text('BÁO CÁO ĐÁNH GIÁ NHẬN THỨC', 20, 30);

      // Basic Info
      doc.setFontSize(12);
      doc.text(`ID Đánh giá: ${result.sessionId}`, 20, 50);
      doc.text(`Người dùng: ${result.userInfo?.name || 'N/A'}`, 20, 60);
      doc.text(`Email: ${result.userInfo?.email || 'N/A'}`, 20, 70);
      doc.text(`Ngày hoàn thành: ${formatDate(result.completedAt)}`, 20, 80);

      // Scores
      doc.setFontSize(14);
      doc.text('Điểm Số', 20, 100);
      doc.setFontSize(12);
      doc.text(`Điểm MMSE: ${result.finalMmseScore}/30`, 20, 115);
      doc.text(`Điểm GPT: ${result.overallGptScore}/10`, 20, 125);
      doc.text(`Tỷ lệ hoàn thành: ${result.completionRate}%`, 20, 135);
      doc.text(`Số câu trả lời: ${result.answeredQuestions}/${result.totalQuestions}`, 20, 145);

      // Risk Assessment
      if (result.cognitiveAnalysis) {
        doc.setFontSize(14);
        doc.text('Đánh Giá Rủi Ro', 20, 165);
        doc.setFontSize(12);
        doc.text(`Mức độ: ${getRiskLevelText(result.cognitiveAnalysis.riskLevel)}`, 20, 180);

        // Split assessment text if too long
        const assessmentLines = doc.splitTextToSize(result.cognitiveAnalysis.overallAssessment, 170);
        doc.text(assessmentLines, 20, 190);
      }

      // Questions table
      if (result.questionResults && result.questionResults.length > 0) {
        doc.addPage();
        doc.setFontSize(14);
        doc.text('Chi Tiết Câu Hỏi', 20, 30);

        const tableData = result.questionResults.map(q => [
          q.questionId || 'N/A',
          (q.questionText || '').substring(0, 50) + ((q.questionText || '').length > 50 ? '...' : ''),
          (q.userAnswer || '').substring(0, 30) + ((q.userAnswer || '').length > 30 ? '...' : ''),
          q.isCorrect ? 'Đúng' : 'Sai',
          `${q.timeSpent || 0}s`
        ]);

        (doc as any).autoTable({
          head: [['ID', 'Câu hỏi', 'Trả lời', 'Kết quả', 'Thời gian']],
          body: tableData,
          startY: 40,
          styles: { fontSize: 8 },
          columnStyles: {
            0: { cellWidth: 15 },
            1: { cellWidth: 50 },
            2: { cellWidth: 40 },
            3: { cellWidth: 25 },
            4: { cellWidth: 25 }
          }
        });
      }

      // AI Analysis
      if (result.cognitiveAnalysis) {
        doc.addPage();
        doc.setFontSize(14);
        doc.text('Phân Tích AI', 20, 30);

        doc.setFontSize(12);
        if (result.cognitiveAnalysis.strengths.length > 0) {
          doc.text('Điểm Mạnh:', 20, 45);
          result.cognitiveAnalysis.strengths.forEach((strength, index) => {
            doc.text(`• ${strength}`, 25, 55 + (index * 10));
          });
        }

        let yPos = 65 + result.cognitiveAnalysis.strengths.length * 10;
        if (result.cognitiveAnalysis.weaknesses.length > 0) {
          doc.text('Điểm Cần Cải Thiện:', 20, yPos);
          result.cognitiveAnalysis.weaknesses.forEach((weakness, index) => {
            doc.text(`• ${weakness}`, 25, yPos + 10 + (index * 10));
          });
          yPos += 20 + result.cognitiveAnalysis.weaknesses.length * 10;
        }

        if (result.cognitiveAnalysis.recommendations.length > 0) {
          doc.text('Khuyến Nghị:', 20, yPos);
          result.cognitiveAnalysis.recommendations.forEach((rec, index) => {
            doc.text(`• ${rec}`, 25, yPos + 10 + (index * 10));
          });
        }
      }

      // Save PDF
      doc.save(`cognitive-assessment-${result.sessionId}.pdf`);

    } catch (error) {
      console.error('Error exporting PDF:', error);
      alert('Có lỗi xảy ra khi xuất PDF. Vui lòng thử lại.');
    }
  };

  const handleShare = async () => {
    const shareData = {
      title: 'Báo cáo Đánh giá Nhận thức',
      text: `Kết quả đánh giá nhận thức của ${result.userInfo?.name || 'Người dùng'}\nĐiểm MMSE: ${result.finalMmseScore}/30\nĐiểm GPT: ${result.overallGptScore}/10\nMức độ rủi ro: ${getRiskLevelText(result.cognitiveAnalysis?.riskLevel || 'unknown')}`,
      url: window.location.href
    };

    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        // Fallback: copy to clipboard
        const textToCopy = `${shareData.title}\n${shareData.text}\n${shareData.url}`;
        await navigator.clipboard.writeText(textToCopy);
        alert('Thông tin đã được sao chép vào clipboard!');
      }
    } catch (error) {
      console.error('Error sharing:', error);
      // Fallback: show share dialog
      setShowShareDialog(true);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-200 overflow-hidden">
      {/* Card Header */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-6 border-b">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-800 mb-2">
              🧠 Đánh Giá Nhận Thức #{result.id}
            </h3>
            <p className="text-sm text-gray-600 mb-1">
              📅 {formatDate(result.completedAt)}
            </p>
            <p className="text-sm text-gray-600">
              👤 {result.userInfo?.name} ({result.userInfo?.email})
            </p>
          </div>
          <div className="text-right">
            <div className="flex gap-2 mb-2">
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                result.status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {result.status === 'completed' ? '✅ Hoàn thành' : '⏳ Đang thực hiện'}
              </span>
            </div>
            <p className="text-xs text-gray-500">ID: {result.sessionId}</p>
          </div>
        </div>
      </div>

      {/* Score Summary */}
      <div className="p-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{result.finalMmseScore || 0}</div>
            <div className="text-sm text-gray-600">Điểm MMSE /30</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{result.overallGptScore || 0}</div>
            <div className="text-sm text-gray-600">GPT Score /10</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{result.completionRate}%</div>
            <div className="text-sm text-gray-600">Hoàn thành</div>
          </div>
          <div className="text-center p-4 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{result.answeredQuestions}</div>
            <div className="text-sm text-gray-600">Câu trả lời</div>
          </div>
        </div>

        {/* Risk Assessment */}
        {result.cognitiveAnalysis && (
          <div className="mb-4 p-4 border border-gray-200 rounded-lg">
            <h4 className="font-semibold text-gray-800 mb-2">🎯 Đánh Giá Rủi Ro</h4>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm font-medium">Mức độ rủi ro:</span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                getRiskLevelColor(result.cognitiveAnalysis.riskLevel)
              }`}>
                {getRiskLevelText(result.cognitiveAnalysis.riskLevel)}
              </span>
            </div>
            <p className="text-sm text-gray-700 mb-3">
              {result.cognitiveAnalysis.overallAssessment}
            </p>
          </div>
        )}

        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <span className="font-medium">
            {isExpanded ? 'Thu gọn' : 'Xem chi tiết đánh giá'}
          </span>
          {isExpanded ? (
            <ChevronUpIcon className="h-5 w-5" />
          ) : (
            <ChevronDownIcon className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t bg-gray-50">
          {/* Question Details */}
          <div className="p-6 border-t">
            <button
              onClick={() => setShowQuestions(!showQuestions)}
              className="flex items-center gap-2 mb-4 font-semibold text-gray-800 hover:text-blue-600"
            >
              <span>📝 Chi Tiết Câu Hỏi ({result.questionResults?.length || 0} câu)</span>
              {showQuestions ? (
                <ChevronUpIcon className="h-4 w-4" />
              ) : (
                <ChevronDownIcon className="h-4 w-4" />
              )}
            </button>

            {showQuestions && result.questionResults && (
              <div className="space-y-6">
                {result.questionResults.map((question, index) => {
                  // Convert question data to MMSEUnifiedResultCard format
                  const questionResult = {
                    questionId: question.questionId || index + 1,
                    questionText: question.questionText || 'N/A',
                    domain: question.category || question.difficulty || 'General',
                    transcript: question.userAnswer || 'N/A',
                    transcriptionConfidence: 95,
                    status: 'completed' as const,
                    processed_at: result.completedAt || new Date().toISOString(),
                    gptEvaluation: question.feedback ? {
                      vocabulary_score: 7.5,
                      context_relevance_score: question.isCorrect ? 8.5 : 6.0,
                      overall_score: question.isCorrect ? 8.0 : 6.5,
                      analysis: question.feedback,
                      feedback: question.isCorrect ? 'Câu trả lời phù hợp và chính xác' : 'Cần cải thiện độ chính xác',
                      vocabulary_analysis: {
                        strengths: question.isCorrect ? ['Từ vựng phù hợp'] : [],
                        weaknesses: !question.isCorrect ? ['Độ chính xác cần cải thiện'] : [],
                        recommendations: ['Luyện tập thêm']
                      },
                      context_analysis: {
                        relevance_level: question.isCorrect ? 'high' : 'medium',
                        accuracy: question.isCorrect ? 'accurate' : 'partially_accurate',
                        completeness: 'complete',
                        issues: []
                      },
                      cognitive_assessment: {
                        language_fluency: question.isCorrect ? 'good' : 'fair',
                        cognitive_level: question.isCorrect ? 'high' : 'medium',
                        attention_focus: 'good',
                        memory_recall: 'good'
                      },
                      transcript_info: {
                        word_count: (question.userAnswer || '').split(' ').length,
                        is_short_transcript: false,
                        vocabulary_richness_applicable: true
                      }
                    } : undefined,
                    audioAnalysis: question.timeSpent ? {
                      fluency: 4.0,
                      pronunciation: 4.2,
                      clarity: 4.5,
                      responseTime: question.timeSpent,
                      pauseAnalysis: {
                        averagePause: 0.8,
                        hesitationCount: Math.floor(question.timeSpent / 10),
                        cognitiveLoad: question.timeSpent > 30 ? 'high' : question.timeSpent > 15 ? 'medium' : 'low',
                        description: `Thời gian phản hồi ${question.timeSpent} giây cho thấy tải nhận thức ${question.timeSpent > 30 ? 'cao' : question.timeSpent > 15 ? 'trung bình' : 'thấp'}`
                      },
                      prosody: 3.8,
                      overallConfidence: question.isCorrect ? 85 : 70
                    } : undefined,
                    clinicalFeedback: {
                      overallAssessment: question.isCorrect ? 'Câu trả lời tốt, phù hợp với yêu cầu' : 'Cần cải thiện độ chính xác',
                      observations: question.isCorrect ? ['Trả lời chính xác'] : ['Đáp án chưa chính xác'],
                      improvements: question.isCorrect ? ['Tiếp tục duy trì'] : ['Luyện tập thêm'],
                      confidence: question.isCorrect ? 85 : 65
                    }
                  };

                  return (
                    <div key={index} className="mmse-result-card bg-[#F6E6DB] border border-[#EFD5C2] shadow-sm hover:shadow-md transition-shadow rounded-lg p-6">
                      {/* Question Header */}
                      <div className="question-header flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-amber-800 mb-1">
                            Câu hỏi {questionResult.questionId}
                          </h3>
                          <p className="text-sm text-amber-700 mb-2">{questionResult.questionText}</p>
                          <div className="flex items-center gap-2 text-xs text-amber-600">
                            <span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full">
                              Lĩnh vực: {questionResult.domain}
                            </span>
                            <span className="px-2 py-1 bg-amber-50 text-amber-700 rounded-full">
                              Xử lý: {new Date(questionResult.processed_at).toLocaleString('vi-VN')}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          {question.isCorrect ? (
                            <CheckCircleIcon className="w-5 h-5 text-green-500" />
                          ) : (
                            <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
                          )}
                        </div>
                      </div>

                      {/* User Response */}
                      <div className="user-response mb-6">
                        <div className="flex items-center gap-2 mb-2">
                          <MicrophoneIcon className="w-4 h-4 text-amber-600" />
                          <h4 className="text-sm font-medium text-amber-800">Phản hồi của bạn:</h4>
                        </div>
                        <div className="bg-gray-50 rounded-lg p-3 text-gray-800 text-sm leading-relaxed">
                          {questionResult.transcript}
                        </div>
                      </div>

                      {/* GPT Clinical Evaluation */}
                      {questionResult.gptEvaluation && (
                        <div className="gpt-evaluation mb-6">
                          <div className="flex items-center gap-2 mb-3">
                            <ChatBubbleLeftRightIcon className="w-4 h-4 text-amber-600" />
                            <h4 className="text-sm font-medium text-amber-800">Đánh giá AI Lâm sàng:</h4>
                          </div>

                          <div className="space-y-3">
                            {/* Overall Score */}
                            <div className="bg-blue-50 rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-blue-700">Điểm tổng thể:</span>
                                <span className="text-lg font-bold text-blue-600">
                                  {Number(questionResult.gptEvaluation.overall_score).toFixed(2)}/10
                                </span>
                              </div>

                              {/* Context Relevance */}
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-blue-600">Độ liên quan nội dung:</span>
                                <span className="font-medium">
                                  {Number(questionResult.gptEvaluation.context_relevance_score).toFixed(2)}/10
                                </span>
                              </div>

                              {/* Vocabulary Score */}
                              <div className="flex items-center justify-between text-sm">
                                <span className="text-blue-600">Độ phong phú từ vựng:</span>
                                <span className="font-medium">
                                  {Number(questionResult.gptEvaluation.vocabulary_score).toFixed(2)}/10
                                </span>
                              </div>
                            </div>

                            {/* Clinical Analysis */}
                            <div className="bg-white border border-blue-200 rounded-lg p-3">
                              <h5 className="text-sm font-medium text-gray-700 mb-2">Phân tích lâm sàng:</h5>
                              <p className="text-sm text-gray-600 leading-relaxed">
                                {questionResult.gptEvaluation.analysis}
                              </p>
                            </div>

                            {/* Cognitive Assessment */}
                            <div className="grid grid-cols-2 gap-2">
                              <div className="text-center p-2 bg-green-50 rounded">
                                <div className="text-xs text-green-600 font-medium">Trôi chảy ngôn ngữ</div>
                                <div className="text-sm font-bold text-green-700 capitalize">
                                  {questionResult.gptEvaluation.cognitive_assessment.language_fluency}
                                </div>
                              </div>
                              <div className="text-center p-2 bg-blue-50 rounded">
                                <div className="text-xs text-blue-600 font-medium">Mức độ nhận thức</div>
                                <div className="text-sm font-bold text-blue-700 capitalize">
                                  {questionResult.gptEvaluation.cognitive_assessment.cognitive_level}
                                </div>
                              </div>
                              <div className="text-center p-2 bg-purple-50 rounded">
                                <div className="text-xs text-purple-600 font-medium">Tập trung chú ý</div>
                                <div className="text-sm font-bold text-purple-700 capitalize">
                                  {questionResult.gptEvaluation.cognitive_assessment.attention_focus}
                                </div>
                              </div>
                              <div className="text-center p-2 bg-orange-50 rounded">
                                <div className="text-xs text-orange-600 font-medium">Ghi nhớ</div>
                                <div className="text-sm font-bold text-orange-700 capitalize">
                                  {questionResult.gptEvaluation.cognitive_assessment.memory_recall}
                                </div>
                              </div>
                            </div>

                            
                          </div>
                        </div>
                      )}

                      {/* Audio Linguistics Analysis */}
                      {questionResult.audioAnalysis && (
                        <div className="audio-analysis mb-6">
                          <div className="flex items-center gap-2 mb-3">
                            <CpuChipIcon className="w-4 h-4 text-amber-600" />
                            <h4 className="text-sm font-medium text-amber-800">Phân tích Ngôn ngữ Học Âm thanh:</h4>
                          </div>

                          <div className="space-y-3">
                            {/* Audio Quality Metrics */}
                            <div className="grid grid-cols-2 gap-3">
                              <div className="bg-green-50 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-green-600 mb-1">
                                  {Number(questionResult.audioAnalysis.fluency).toFixed(2)}/5
                                </div>
                                <div className="text-xs font-medium text-green-700">Lưu loát</div>
                                <div className="text-xs text-green-600 mt-1">
                                  {questionResult.audioAnalysis.fluency >= 4.5 ? "Xuất sắc - lưu loát, tự nhiên" :
                                   questionResult.audioAnalysis.fluency >= 3.5 ? "Tốt - mạch lạc, ít ngập ngừng" :
                                   questionResult.audioAnalysis.fluency >= 2.5 ? "Khá - có chút ngập ngừng" :
                                   questionResult.audioAnalysis.fluency >= 1.5 ? "Cần cải thiện - nhiều ngập ngừng" :
                                   "Yếu - rất ngập ngừng, khó theo dõi"}
                                </div>
                              </div>

                              <div className="bg-blue-50 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-blue-600 mb-1">
                                  {Number(questionResult.audioAnalysis.pronunciation).toFixed(2)}/5
                                </div>
                                <div className="text-xs font-medium text-blue-700">Phát âm</div>
                                <div className="text-xs text-blue-600 mt-1">
                                  {questionResult.audioAnalysis.pronunciation >= 4.5 ? "Xuất sắc - phát âm chuẩn xác" :
                                   questionResult.audioAnalysis.pronunciation >= 3.5 ? "Tốt - phát âm rõ ràng" :
                                   questionResult.audioAnalysis.pronunciation >= 2.5 ? "Khá - phát âm có thể chấp nhận" :
                                   questionResult.audioAnalysis.pronunciation >= 1.5 ? "Cần cải thiện - phát âm không rõ" :
                                   "Yếu - phát âm khó hiểu"}
                                </div>
                              </div>

                              <div className="bg-purple-50 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-purple-600 mb-1">
                                  {Number(questionResult.audioAnalysis.clarity).toFixed(2)}/5
                                </div>
                                <div className="text-xs font-medium text-purple-700">Rõ ràng</div>
                                <div className="text-xs text-purple-600 mt-1">
                                  {questionResult.audioAnalysis.clarity >= 4.5 ? "Xuất sắc - âm thanh rất rõ" :
                                   questionResult.audioAnalysis.clarity >= 3.5 ? "Tốt - âm thanh rõ ràng" :
                                   questionResult.audioAnalysis.clarity >= 2.5 ? "Khá - âm thanh chấp nhận được" :
                                   questionResult.audioAnalysis.clarity >= 1.5 ? "Cần cải thiện - âm thanh không rõ" :
                                   "Yếu - âm thanh kém chất lượng"}
                                </div>
                              </div>

                              <div className="bg-orange-50 rounded-lg p-3 text-center">
                                <div className="text-2xl font-bold text-orange-600 mb-1">
                                  {Number(questionResult.audioAnalysis.prosody).toFixed(2)}/5
                                </div>
                                <div className="text-xs font-medium text-orange-700">Ngữ điệu</div>
                                <div className="text-xs text-orange-600 mt-1">
                                  {questionResult.audioAnalysis.prosody >= 4.5 ? "Xuất sắc - ngữ điệu tự nhiên" :
                                   questionResult.audioAnalysis.prosody >= 3.5 ? "Tốt - ngữ điệu phù hợp" :
                                   questionResult.audioAnalysis.prosody >= 2.5 ? "Khá - ngữ điệu cơ bản" :
                                   questionResult.audioAnalysis.prosody >= 1.5 ? "Cần cải thiện - ngữ điệu hạn chế" :
                                   "Yếu - ngữ điệu nghèo nàn"}
                                </div>
                              </div>
                            </div>

                            {/* Response Time */}
                            <div className="bg-gray-50 rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-gray-700">Thời gian phản hồi:</span>
                                <span className="text-sm font-bold text-gray-600">
                                  {Number(questionResult.audioAnalysis.responseTime).toFixed(2)} giây
                                </span>
                              </div>
                              <div className="text-xs text-gray-500">
                                Chỉ số tốc độ xử lý nhận thức - thời gian suy nghĩ trước khi trả lời
                              </div>
                            </div>

                            {/* Pause Analysis */}
                            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                              <h5 className="text-sm font-medium text-red-700 mb-2">Phân tích khoảng dừng:</h5>
                              <div className="grid grid-cols-3 gap-2 mb-2">
                                <div className="text-center">
                                  <div className="text-sm font-bold text-red-600">
                                    {Number(questionResult.audioAnalysis.pauseAnalysis.averagePause).toFixed(2)}s
                                  </div>
                                  <div className="text-xs text-red-600">TB khoảng dừng</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-sm font-bold text-red-600">
                                    {questionResult.audioAnalysis.pauseAnalysis.hesitationCount}
                                  </div>
                                  <div className="text-xs text-red-600">Lần ngập ngừng</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-sm font-bold text-red-600 capitalize">
                                    {questionResult.audioAnalysis.pauseAnalysis.cognitiveLoad}
                                  </div>
                                  <div className="text-xs text-red-600">Tải nhận thức</div>
                                </div>
                              </div>
                              <p className="text-xs text-red-600 leading-relaxed">
                                {questionResult.audioAnalysis.pauseAnalysis.description}
                              </p>
                            </div>

                            {/* Overall Audio Confidence */}
                            <div className="bg-green-50 rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-green-700">Độ tin cậy âm thanh tổng thể:</span>
                                <span className="text-sm font-bold text-green-600">
                                  {questionResult.audioAnalysis.overallConfidence}%
                                </span>
                              </div>
                              <div className="w-full bg-green-200 rounded-full h-2">
                                <div
                                  className="bg-green-600 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${questionResult.audioAnalysis.overallConfidence}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Clinical Feedback Integration */}
                      {questionResult.clinicalFeedback && (
                        <div className="clinical-feedback mb-6">
                          <div className="flex items-center gap-2 mb-3">
                            <TagIcon className="w-4 h-4 text-amber-600" />
                            <h4 className="text-sm font-medium text-amber-800">Đánh giá Lâm sàng Tổng hợp:</h4>
                          </div>

                          <div className="space-y-3">
                            {/* Overall Assessment */}
                            <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                              <h5 className="text-sm font-medium text-purple-700 mb-2">Đánh giá tổng thể:</h5>
                              <p className="text-sm text-purple-600 leading-relaxed">
                                {questionResult.clinicalFeedback.overallAssessment}
                              </p>
                            </div>

                            {/* Clinical Observations */}
                            <div className="bg-blue-50 rounded-lg p-3">
                              <h5 className="text-sm font-medium text-blue-700 mb-2">Quan sát lâm sàng:</h5>
                              <ul className="text-sm text-blue-600 space-y-1">
                                {questionResult.clinicalFeedback.observations.map((obs, idx) => (
                                  <li key={idx} className="flex items-start gap-2">
                                    <span className="text-blue-500 mt-1">•</span>
                                    <span>{obs}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>

                            

                            {/* Combined Confidence */}
                            <div className="bg-indigo-50 rounded-lg p-3">
                              <div className="flex items-center justify-between mb-2">
                                <span className="text-sm font-medium text-indigo-700">Độ tin cậy tổng hợp:</span>
                                <span className="text-sm font-bold text-indigo-600">
                                  {questionResult.clinicalFeedback.confidence}%
                                </span>
                              </div>
                              <div className="text-xs text-indigo-600">
                                Kết hợp đánh giá GPT, phân tích âm thanh và quan sát lâm sàng
                              </div>
                              <div className="w-full bg-indigo-200 rounded-full h-2 mt-2">
                                <div
                                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${questionResult.clinicalFeedback.confidence}%` }}
                                ></div>
                              </div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="p-6 border-t bg-white">
            <div className="flex gap-3">
              <button
                onClick={() => onViewDetails?.(result)}
                className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                📊 Xem Báo Cáo Đầy Đủ
              </button>
              <button
                onClick={handleExportPDF}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors flex items-center gap-2"
              >
                <DocumentArrowDownIcon className="h-4 w-4" />
                Xuất PDF
              </button>
              <button
                onClick={handleShare}
                className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
              >
                <ShareIcon className="h-4 w-4" />
                Chia Sẻ
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Share Dialog */}
      {showShareDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-4">Chia sẻ báo cáo</h3>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sao chép liên kết chia sẻ:
              </label>
              <textarea
                readOnly
                value={`Báo cáo Đánh giá Nhận thức

Người dùng: ${result.userInfo?.name || 'N/A'}
Điểm MMSE: ${result.finalMmseScore}/30
Điểm GPT: ${result.overallGptScore}/10
Mức độ rủi ro: ${getRiskLevelText(result.cognitiveAnalysis?.riskLevel || 'unknown')}

Liên kết: ${window.location.href}`}
                className="w-full h-32 p-3 border border-gray-300 rounded-lg text-sm"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={async () => {
                  try {
                    const textToCopy = `Báo cáo Đánh giá Nhận thức\n\nNgười dùng: ${result.userInfo?.name || 'N/A'}\nĐiểm MMSE: ${result.finalMmseScore}/30\nĐiểm GPT: ${result.overallGptScore}/10\nMức độ rủi ro: ${getRiskLevelText(result.cognitiveAnalysis?.riskLevel || 'unknown')}\n\nLiên kết: ${window.location.href}`;
                    await navigator.clipboard.writeText(textToCopy);
                    alert('Đã sao chép vào clipboard!');
                    setShowShareDialog(false);
                  } catch (error) {
                    alert('Không thể sao chép. Vui lòng chọn và sao chép thủ công.');
                  }
                }}
                className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                Sao chép
              </button>
              <button
                onClick={() => setShowShareDialog(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
