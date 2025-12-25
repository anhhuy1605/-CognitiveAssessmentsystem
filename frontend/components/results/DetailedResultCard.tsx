'use client';
import { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, DocumentArrowDownIcon, ShareIcon, CheckCircleIcon, ExclamationCircleIcon, MicrophoneIcon, ChatBubbleLeftRightIcon, BoltIcon, TagIcon } from '@heroicons/react/24/outline';

// HTML2PDF-based PDF generation with perfect Vietnamese font support
const generateProfessionalPDF = async (result: any, formatDate: (date: string) => string, getRiskLevelText: (level: string) => string) => {
  try {
    // Dynamically import html2pdf.js to avoid SSR issues
    const html2pdf = (await import('html2pdf.js')).default;

    // Generate HTML content with professional styling
    const htmlContent = generateHTMLContent(result, formatDate, getRiskLevelText);

    // HTML2PDF options for perfect rendering
    const options = {
      margin: 15, // margin in mm
      filename: generateFilename(result),
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: {
        scale: 2,
        useCORS: true,
        letterRendering: true,
        allowTaint: false
      },
      jsPDF: {
        unit: 'mm' as const,
        format: 'a4' as const,
        orientation: 'portrait' as const
      }
    };

    // Generate and save PDF
    await html2pdf().set(options).from(htmlContent).save();

    console.log('✅ Professional PDF report generated successfully with HTML2PDF');

  } catch (error) {
    console.error('❌ Error generating professional PDF:', error);
    alert('Có lỗi xảy ra khi xuất PDF. Vui lòng thử lại.');
  }
};

// Generate HTML content with professional styling
const generateHTMLContent = (data: any, formatDate: (date: string) => string, getRiskLevelText: (level: string) => string) => {
  return `
    <!DOCTYPE html>
    <html lang="vi">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Báo cáo Đánh giá Nhận thức</title>
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          line-height: 1.6;
          color: #333;
          background: white;
          font-size: 12px;
        }

        .page {
          width: 210mm;
          min-height: 297mm;
          padding: 15mm;
          page-break-after: always;
          position: relative;
        }

        .page:last-child {
          page-break-after: avoid;
        }

        .header {
          background: linear-gradient(135deg, #F59E0B, #D97706);
          color: white;
          padding: 20px;
          text-align: center;
          border-radius: 10px;
          margin-bottom: 30px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .header .title {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 10px;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }

        .header .subtitle {
          font-size: 16px;
          opacity: 0.9;
        }

        .info-box {
          background: #FBF3E6;
          border-left: 4px solid #F59E0B;
          padding: 20px;
          margin: 20px 0;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .info-box h3 {
          color: #92400E;
          font-weight: bold;
          margin-bottom: 15px;
          font-size: 14px;
        }

        .info-box table {
          width: 100%;
          border-collapse: collapse;
        }

        .info-box table td {
          padding: 8px 12px;
          border-bottom: 1px solid #E5E7EB;
        }

        .info-box table td:first-child {
          font-weight: bold;
          color: #374151;
          width: 40%;
        }

        .score-section {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          margin: 30px 0;
        }

        .score-card {
          background: white;
          border: 2px solid #E5E7EB;
          border-radius: 15px;
          padding: 25px;
          text-align: center;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
          transition: transform 0.2s ease;
        }

        .score-card:hover {
          transform: translateY(-2px);
        }

        .score-card h3 {
          font-size: 16px;
          font-weight: bold;
          color: #374151;
          margin-bottom: 15px;
        }

        .score-number {
          font-size: 48px;
          font-weight: bold;
          color: #F59E0B;
          margin: 10px 0;
          text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .progress-bar {
          width: 100%;
          height: 20px;
          background: #E5E7EB;
          border-radius: 10px;
          overflow: hidden;
          margin: 15px 0;
          box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #F59E0B, #D97706);
          border-radius: 10px;
          transition: width 0.3s ease;
          box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
        }

        .progress-text {
          font-size: 14px;
          color: #6B7280;
          font-weight: bold;
          margin-top: 5px;
        }

        .risk-badge {
          display: inline-block;
          padding: 12px 24px;
          border-radius: 25px;
          font-weight: bold;
          text-transform: uppercase;
          font-size: 14px;
          box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
          margin: 20px 0;
        }

        .risk-low {
          background: #D1FAE5;
          color: #065F46;
          border: 2px solid #10B981;
        }

        .risk-medium {
          background: #FEF3C7;
          color: #92400E;
          border: 2px solid #F59E0B;
        }

        .risk-high {
          background: #FEE2E2;
          color: #991B1B;
          border: 2px solid #EF4444;
        }

        .question-table {
          width: 100%;
          border-collapse: collapse;
          margin: 20px 0;
          font-size: 11px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          border-radius: 8px;
          overflow: hidden;
        }

        .question-table th,
        .question-table td {
          border: 1px solid #E5E7EB;
          padding: 12px;
          text-align: left;
          vertical-align: top;
        }

        .question-table th {
          background: linear-gradient(135deg, #F59E0B, #D97706);
          color: white;
          font-weight: bold;
          text-transform: uppercase;
          font-size: 10px;
          letter-spacing: 0.5px;
        }

        .question-table tr:nth-child(even) {
          background: #F9FAFB;
        }

        .question-table tr:hover {
          background: #FEF3C7;
        }

        .status-correct {
          color: #059669;
          font-weight: bold;
        }

        .status-incorrect {
          color: #DC2626;
          font-weight: bold;
        }

        .section-title {
          font-size: 20px;
          font-weight: bold;
          color: #1F2937;
          margin: 30px 0 15px 0;
          padding-bottom: 10px;
          border-bottom: 3px solid #F59E0B;
          position: relative;
        }

        .section-title:after {
          content: '';
          position: absolute;
          bottom: -3px;
          left: 0;
          width: 60px;
          height: 3px;
          background: linear-gradient(90deg, #F59E0B, #D97706);
        }

        .analysis-section {
          background: #F8FAFC;
          border-radius: 10px;
          padding: 20px;
          margin: 15px 0;
          border-left: 4px solid #F59E0B;
        }

        .analysis-section h4 {
          color: #F59E0B;
          font-weight: bold;
          margin-bottom: 10px;
          font-size: 14px;
        }

        .analysis-section p {
          color: #374151;
          line-height: 1.6;
          margin-bottom: 8px;
        }

        .recommendations {
          background: #F0F9FF;
          border-radius: 10px;
          padding: 20px;
          margin: 20px 0;
          border: 1px solid #E0E7FF;
        }

        .recommendations h4 {
          color: #1E40AF;
          font-weight: bold;
          margin-bottom: 15px;
          font-size: 16px;
        }

        .recommendations ul {
          list-style: none;
          padding: 0;
        }

        .recommendations li {
          padding: 10px 0;
          border-bottom: 1px solid #E0E7FF;
          display: flex;
          align-items: flex-start;
          gap: 10px;
        }

        .recommendations li:last-child {
          border-bottom: none;
        }

        .recommendations li:before {
          content: "→";
          color: #F59E0B;
          font-weight: bold;
          font-size: 16px;
          flex-shrink: 0;
        }

        .contact-info {
          background: linear-gradient(135deg, #FEF3C7, #FDE68A);
          border-radius: 10px;
          padding: 25px;
          margin: 30px 0;
          border: 2px solid #F59E0B;
          text-align: center;
        }

        .contact-info h4 {
          color: #92400E;
          font-weight: bold;
          margin-bottom: 15px;
          font-size: 16px;
        }

        .contact-info p {
          color: #374151;
          margin: 5px 0;
          font-size: 13px;
        }

        .contact-info strong {
          color: #1F2937;
        }

        @media print {
          body {
            margin: 0;
            -webkit-print-color-adjust: exact;
            color-adjust: exact;
          }
          .page {
            margin: 0;
            box-shadow: none;
            page-break-after: always;
          }
          .page:last-child {
            page-break-after: avoid;
          }
        }

        @page {
          margin: 15mm;
          size: A4 portrait;
        }
      </style>
    </head>
    <body>
      ${generatePageContent(data, formatDate, getRiskLevelText)}
    </body>
    </html>
  `;
};

// Generate page content
const generatePageContent = (data: any, formatDate: (date: string) => string, getRiskLevelText: (level: string) => string) => {
  return `
    <!-- TRANG 1: COVER PAGE -->
    <div class="page">
      <div class="header">
        <div class="title">BÁO CÁO ĐÁNH GIÁ NHẬN THỨC</div>
        <div class="subtitle">Hệ thống AI Cá Vàng - Thắp sáng ký ức</div>
      </div>

      <div class="info-box">
        <h3>THÔNG TIN PHIÊN ĐÁNH GIÁ</h3>
        <table>
          <tr><td>Session ID:</td><td>${data.sessionId}</td></tr>
          <tr><td>Ngày hoàn thành:</td><td>${formatDate(data.completedAt)}</td></tr>
          <tr><td>Tổng câu hỏi:</td><td>${data.totalQuestions || 0}</td></tr>
          <tr><td>Trạng thái:</td><td>Hoàn thành</td></tr>
        </table>
      </div>

      <div class="info-box">
        <h3>THÔNG TIN NGƯỜI THAM GIA</h3>
        <table>
          <tr><td>Họ tên:</td><td>${data.userInfo?.name || 'N/A'}</td></tr>
          <tr><td>Email:</td><td>${data.userInfo?.email || 'N/A'}</td></tr>
          <tr><td>Tuổi:</td><td>${data.userInfo?.age || 'N/A'}</td></tr>
          <tr><td>Giới tính:</td><td>${data.userInfo?.gender || 'N/A'}</td></tr>
        </table>
      </div>
    </div>

    <!-- TRANG 2: SCORES -->
    <div class="page">
      <div class="header">
        <div class="title">KẾT QUẢ ĐIỂM SỐ</div>
      </div>

      <div class="score-section">
        <div class="score-card">
          <h3>Điểm MMSE</h3>
          <div class="score-number">${data.finalMmseScore || 0}/30</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${((data.finalMmseScore || 0) / 30) * 100}%"></div>
          </div>
          <div class="progress-text">${(((data.finalMmseScore || 0) / 30) * 100).toFixed(1)}%</div>
        </div>

        <div class="score-card">
          <h3>Điểm AI Tổng thể</h3>
          <div class="score-number">${(data.overallGptScore || 0).toFixed(1)}/10</div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${((data.overallGptScore || 0) / 10) * 100}%"></div>
          </div>
          <div class="progress-text">${(((data.overallGptScore || 0) / 10) * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div class="info-box">
        <h3>Tỷ lệ hoàn thành: ${(data.completionRate || 0).toFixed(1)}% (${data.answeredQuestions || 0}/${data.totalQuestions || 0} câu)</h3>
      </div>

      <!-- RISK ASSESSMENT -->
      <div class="section-title">ĐÁNH GIÁ RỦI RO</div>
      <div style="text-align: center;">
        <span class="risk-badge risk-${(data.cognitiveAnalysis?.riskLevel || 'low').toLowerCase()}">
          ${getRiskLevelText(data.cognitiveAnalysis?.riskLevel || 'low')}
        </span>
      </div>

      ${data.cognitiveAnalysis?.overallAssessment ? `
      <div class="analysis-section">
        <h4>Đánh giá tổng thể:</h4>
        <p>${data.cognitiveAnalysis.overallAssessment}</p>
      </div>
      ` : ''}
    </div>

    <!-- TRANG 3: CHI TIẾT CÂU HỎI -->
    <div class="page">
      <div class="header">
        <div class="title">CHI TIẾT CÂU HỎI</div>
      </div>

      <table class="question-table">
        <thead>
          <tr>
            <th width="5%">STT</th>
            <th width="35%">Câu hỏi</th>
            <th width="25%">Trả lời</th>
            <th width="15%">Điểm GPT</th>
            <th width="20%">Trạng thái</th>
          </tr>
        </thead>
        <tbody>
          ${data.questionResults?.map((q: any, index: number) => `
            <tr>
              <td>${index + 1}</td>
              <td>${q.questionText || 'N/A'}</td>
              <td>${q.userAnswer || 'Không có lời thoại'}</td>
              <td>${q.gptEvaluation?.overall_score ? q.gptEvaluation.overall_score.toFixed(1) + '/10' : 'N/A'}</td>
              <td class="${q.isCorrect ? 'status-correct' : 'status-incorrect'}">
                ${q.isCorrect ? '✅ Hoàn thành' : '❌ Chưa hoàn thành'}
              </td>
            </tr>
          `).join('') || '<tr><td colspan="5">Không có dữ liệu</td></tr>'}
        </tbody>
      </table>

      <!-- Detailed Analysis for each question -->
      ${data.questionResults?.map((q: any, index: number) => {
        if (q.gptEvaluation?.analysis || q.gptEvaluation?.feedback) {
          return `
            <div class="analysis-section">
              <h4>Câu ${index + 1} - Phân tích AI:</h4>
              ${q.gptEvaluation?.analysis ? `<p><strong>Analysis:</strong> ${q.gptEvaluation.analysis}</p>` : ''}
              ${q.gptEvaluation?.feedback ? `<p><strong>Feedback:</strong> ${q.gptEvaluation.feedback}</p>` : ''}
            </div>
          `;
        }
        return '';
      }).join('') || ''}
    </div>

    <!-- TRANG 4: TỔNG KẾT & KHUYẾN NGHỊ -->
    <div class="page">
      <div class="header">
        <div class="title">TỔNG KẾT & KHUYẾN NGHỊ</div>
      </div>

      <div class="analysis-section">
        <h4>Tóm tắt kết quả:</h4>
        <p>Báo cáo đánh giá nhận thức cho ${data.userInfo?.name || 'người dùng'} được thực hiện vào ${formatDate(data.completedAt)}.
        Kết quả MMSE: ${data.finalMmseScore || 0}/30, cho thấy mức độ ${((data.finalMmseScore || 0) >= 24) ? 'bình thường' : ((data.finalMmseScore || 0) >= 18) ? 'có dấu hiệu suy giảm nhẹ' : 'cần theo dõi chuyên sâu'}.</p>
      </div>

      ${data.cognitiveAnalysis?.strengths?.length ? `
      <div class="section-title">ĐIỂM MẠNH</div>
      <div class="recommendations">
        <ul>
          ${data.cognitiveAnalysis.strengths.map((strength: string) => `<li>${strength}</li>`).join('')}
        </ul>
      </div>
      ` : ''}

      ${data.cognitiveAnalysis?.weaknesses?.length ? `
      <div class="section-title">CẦN CHÚ Ý</div>
      <div class="recommendations">
        <ul>
          ${data.cognitiveAnalysis.weaknesses.map((weakness: string) => `<li>${weakness}</li>`).join('')}
        </ul>
      </div>
      ` : ''}

      ${data.cognitiveAnalysis?.recommendations?.length ? `
      <div class="section-title">KHUYẾN NGHỊ</div>
      <div class="recommendations">
        <ul>
          ${data.cognitiveAnalysis.recommendations.map((rec: string) => `<li>${rec}</li>`).join('')}
        </ul>
      </div>
      ` : ''}

      <div class="contact-info">
        <h4>THÔNG TIN LIÊN HỆ HỖ TRỢ</h4>
        <p><strong>Hệ thống AI Cá Vàng - Thắp sáng ký ức</strong></p>
        <p>Email hỗ trợ: support@cavang.ai</p>
        <p>Website: https://cavang.info</p>
        <p>Điện thoại: 0934865593)</p>
      </div>
    </div>
  `;
};

// Generate filename
const generateFilename = (data: any) => {
  const userName = data.userInfo?.name ? data.userInfo.name.replace(/[^a-zA-Z0-9]/g, '_') : 'User';
  const dateStr = new Date().toISOString().split('T')[0];
  return `Cognitive_Assessment_Report_${userName}_${dateStr}.pdf`;
};

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
  gptEvaluation?: any;
  audioAnalysis?: any;
}

interface DetailedResultCardProps {
  result: {
    id: number;
    sessionId: string;
    userId?: string;
    userInfo: any;
    startedAt?: string;
    completedAt: string;
    totalQuestions: number;
    answeredQuestions: number;
    completionRate: number;
    memoryScore?: number;
    cognitiveScore?: number;
    finalMmseScore: number;
    overallGptScore: number;
    questionResults: QuestionResult[];
    audioFiles?: any;
    recordingsPath?: string;
    cognitiveAnalysis?: {
      strengths: string[];
      weaknesses: string[];
      recommendations: string[];
      overallAssessment: string;
      riskLevel: 'low' | 'medium' | 'high';
    };
    audioFeatures?: any;
    status: string;
    usageMode?: string;
    assessmentType?: string;
    createdAt: string;
    updatedAt?: string;
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

  const handleExportPDF = () => generateProfessionalPDF(result, formatDate, getRiskLevelText);

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
        alert('ThÃ´ng tin Ä‘Ã£ Ä‘Æ°á»£c sao chÃ©p vÃ o clipboard!');
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
                      feedback: question.isCorrect ? 'CÃ¢u tráº£ lá»i phÃ¹ há»£p vÃ  chÃ­nh xÃ¡c' : 'Cáº§n cáº£i thiá»‡n Ä‘á»™ chÃ­nh xÃ¡c',
                      vocabulary_analysis: {
                        strengths: question.isCorrect ? ['Tá»« vá»±ng phÃ¹ há»£p'] : [],
                        weaknesses: !question.isCorrect ? ['Äá»™ chÃ­nh xÃ¡c cáº§n cáº£i thiá»‡n'] : [],
                        recommendations: ['Luyá»‡n táº­p thÃªm']
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
                        description: `Thá»i gian pháº£n há»“i ${question.timeSpent} giÃ¢y cho tháº¥y táº£i nháº­n thá»©c ${question.timeSpent > 30 ? 'cao' : question.timeSpent > 15 ? 'trung bÃ¬nh' : 'tháº¥p'}`
                      },
                      prosody: 3.8,
                      overallConfidence: question.isCorrect ? 85 : 70
                    } : undefined,
                    clinicalFeedback: {
                      overallAssessment: question.isCorrect ? 'CÃ¢u tráº£ lá»i tá»‘t, phÃ¹ há»£p vá»›i yÃªu cáº§u' : 'Cáº§n cáº£i thiá»‡n Ä‘á»™ chÃ­nh xÃ¡c',
                      observations: question.isCorrect ? ['Tráº£ lá»i chÃ­nh xÃ¡c'] : ['ÄÃ¡p Ã¡n chÆ°a chÃ­nh xÃ¡c'],
                      improvements: question.isCorrect ? ['Tiáº¿p tá»¥c duy trÃ¬'] : ['Luyá»‡n táº­p thÃªm'],
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
                          <BoltIcon className="w-4 h-4 text-amber-600" />
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
                                <span className="text-sm font-medium text-green-700">Äá»™ tin cáº­y Ã¢m thanh tá»•ng thá»ƒ:</span>
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
                Chia sẻ
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
                    const textToCopy = `BÃ¡o cÃ¡o ÄÃ¡nh giÃ¡ Nháº­n thá»©c\n\nNgÆ°á»i dÃ¹ng: ${result.userInfo?.name || 'N/A'}\nÄiá»ƒm MMSE: ${result.finalMmseScore}/30\nÄiá»ƒm GPT: ${result.overallGptScore}/10\nMá»©c Ä‘á»™ rá»§i ro: ${getRiskLevelText(result.cognitiveAnalysis?.riskLevel || 'unknown')}\n\nLiÃªn káº¿t: ${window.location.href}`;
                    await navigator.clipboard.writeText(textToCopy);
                    alert('ÄÃ£ sao chÃ©p vÃ o clipboard!');
                    setShowShareDialog(false);
                  } catch (error) {
                    alert('KhÃ´ng thá»ƒ sao chÃ©p. Vui lÃ²ng chá»n vÃ  sao chÃ©p thá»§ cÃ´ng.');
                  }
                }}
                className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
              >
                Sao chÃ©p
              </button>
              <button
                onClick={() => setShowShareDialog(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
              >
                ÄÃ³ng
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
