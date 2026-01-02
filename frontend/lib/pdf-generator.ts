/**
 * PDF Generator for Comprehensive Results
 * Uses jsPDF and html2canvas for professional PDF export
 */

export async function generatePDF(resultsData: any, sessionId: string) {
  try {
    // Dynamic import to avoid SSR issues
    const jsPDF = (await import('jspdf')).default;
    const html2canvas = (await import('html2canvas')).default;

    // Create PDF
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    });

    const pageWidth = pdf.internal.pageSize.getWidth();
    const pageHeight = pdf.internal.pageSize.getHeight();
    const margin = 15;
    let yPos = margin;

    // Helper function to add new page if needed
    const checkNewPage = (requiredHeight: number) => {
      if (yPos + requiredHeight > pageHeight - margin) {
        pdf.addPage();
        yPos = margin;
        return true;
      }
      return false;
    };

    // Title
    pdf.setFontSize(20);
    pdf.setFont('helvetica', 'bold');
    pdf.text('Kết Quả Đánh Giá Nhận Thức Toàn Diện', pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;

    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'normal');
    pdf.text('Comprehensive Cognitive Assessment Results', pageWidth / 2, yPos, { align: 'center' });
    yPos += 10;

    // Session Info
    pdf.setFontSize(10);
    pdf.text(`Session ID: ${sessionId}`, margin, yPos);
    yPos += 5;
    pdf.text(`Ngày đánh giá: ${new Date(resultsData.metadata.timestamp).toLocaleDateString('vi-VN')}`, margin, yPos);
    yPos += 5;
    pdf.text(`Tuổi: ${resultsData.assessment_result.age} tuổi`, margin, yPos);
    yPos += 5;
    pdf.text(`Học vấn: ${resultsData.assessment_result.education_years} năm`, margin, yPos);
    yPos += 10;

    // Assessment Summary
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.text('1. Tóm Tắt Đánh Giá', margin, yPos);
    yPos += 8;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Điểm MMSE thô: ${resultsData.assessment_result.raw_score.toFixed(1)}/35`, margin, yPos);
    yPos += 5;

    if (resultsData.assessment_result.adjusted_score) {
      pdf.text(`Điểm điều chỉnh: ${resultsData.assessment_result.adjusted_score.toFixed(1)}/35`, margin, yPos);
      yPos += 5;
    }

    pdf.text(`Mức độ nguy cơ: ${resultsData.assessment_result.risk_level_label}`, margin, yPos);
    yPos += 5;
    pdf.text(`Xác suất MCI: ${(resultsData.assessment_result.mci_probability * 100).toFixed(1)}%`, margin, yPos);
    yPos += 10;

    // Clinical Thresholds
    pdf.setFontSize(12);
    pdf.setFont('helvetica', 'bold');
    pdf.text('Ngưỡng Lâm Sàng:', margin, yPos);
    yPos += 6;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    const thresholds = resultsData.assessment_result.thresholds;
    pdf.text(`• Bình thường: ≥ ${thresholds.normal.min} điểm`, margin + 5, yPos);
    yPos += 5;
    pdf.text(`• MCI nhẹ: ${thresholds.mild_mci.min}-${thresholds.mild_mci.max} điểm`, margin + 5, yPos);
    yPos += 5;
    pdf.text(`• Sa sút trí tuệ vừa: ${thresholds.moderate.min}-${thresholds.moderate.max} điểm`, margin + 5, yPos);
    yPos += 5;
    pdf.text(`• Sa sút trí tuệ nặng: < ${thresholds.severe.max + 1} điểm`, margin + 5, yPos);
    yPos += 10;

    // Feature Summary
    checkNewPage(20);
    pdf.setFontSize(14);
    pdf.setFont('helvetica', 'bold');
    pdf.text('2. Phân Tích Đặc Trưng', margin, yPos);
    yPos += 8;

    pdf.setFontSize(10);
    pdf.setFont('helvetica', 'normal');
    pdf.text(`Tổng số đặc trưng: ${resultsData.feature_summary.total_features}`, margin, yPos);
    yPos += 5;
    pdf.text(`• Đặc trưng âm thanh: ${resultsData.feature_summary.acoustic_feature_count}`, margin + 5, yPos);
    yPos += 5;
    pdf.text(`• Đặc trưng ngôn ngữ: ${resultsData.feature_summary.linguistic_feature_count}`, margin + 5, yPos);
    yPos += 5;
    pdf.text(`• Số đặc trưng bất thường: ${resultsData.feature_summary.total_abnormal_features} (${resultsData.feature_summary.abnormal_percentage}%)`, margin + 5, yPos);
    yPos += 10;

    // SHAP Explanations
    if (resultsData.shap_explanation && resultsData.shap_explanation.top_risk_factors.length > 0) {
      checkNewPage(30);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('3. Giải Thích SHAP (Feature Importance)', margin, yPos);
      yPos += 8;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      pdf.text('Citation: Lundberg & Lee (2017) - A Unified Approach to Interpreting Model Predictions', margin, yPos);
      yPos += 8;

      pdf.setFontSize(12);
      pdf.setFont('helvetica', 'bold');
      pdf.text('Top Yếu Tố Nguy Cơ:', margin, yPos);
      yPos += 6;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      resultsData.shap_explanation.top_risk_factors.forEach((factor: any, idx: number) => {
        checkNewPage(15);
        pdf.setFont('helvetica', 'bold');
        pdf.text(`${idx + 1}. ${factor.feature_name_vi} (${factor.feature_name_en})`, margin, yPos);
        yPos += 5;
        pdf.setFont('helvetica', 'normal');
        pdf.text(`   SHAP Value: +${factor.shap_value.toFixed(3)}`, margin + 5, yPos);
        yPos += 4;
        pdf.text(`   Giá trị: ${factor.value.toFixed(3)} (${factor.comparison})`, margin + 5, yPos);
        yPos += 4;
        pdf.text(`   Ảnh hưởng: ${factor.interpretation}`, margin + 5, yPos);
        yPos += 4;
        pdf.text(`   Khuyến nghị: ${factor.recommendation}`, margin + 5, yPos);
        yPos += 6;
      });
    }

    // Recommendations
    if (resultsData.recommendations && resultsData.recommendations.length > 0) {
      checkNewPage(20);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('4. Khuyến Nghị', margin, yPos);
      yPos += 8;

      pdf.setFontSize(10);
      pdf.setFont('helvetica', 'normal');
      resultsData.recommendations.forEach((rec: string) => {
        checkNewPage(5);
        pdf.text(`• ${rec}`, margin + 5, yPos);
        yPos += 5;
      });
      yPos += 5;
    }

    // Citations
    if (resultsData.citations && resultsData.citations.length > 0) {
      checkNewPage(30);
      pdf.setFontSize(14);
      pdf.setFont('helvetica', 'bold');
      pdf.text('5. Tài Liệu Tham Khảo', margin, yPos);
      yPos += 8;

      pdf.setFontSize(9);
      pdf.setFont('helvetica', 'normal');
      resultsData.citations.forEach((citation: any) => {
        checkNewPage(15);
        pdf.setFont('helvetica', 'bold');
        pdf.text(`${citation.authors} (${citation.year})`, margin, yPos);
        yPos += 4;
        pdf.setFont('helvetica', 'italic');
        pdf.text(citation.title, margin, yPos);
        yPos += 4;
        pdf.setFont('helvetica', 'normal');
        if (citation.journal) {
          pdf.text(`${citation.journal}${citation.volume ? `, ${citation.volume}` : ''}${citation.pages ? `, pp. ${citation.pages}` : ''}`, margin, yPos);
          yPos += 4;
        }
        if (citation.doi) {
          pdf.text(`DOI: ${citation.doi}`, margin, yPos);
          yPos += 4;
        }
        pdf.text(citation.description, margin, yPos);
        yPos += 6;
      });
    }

    // Footer
    const totalPages = pdf.getNumberOfPages();
    for (let i = 1; i <= totalPages; i++) {
      pdf.setPage(i);
      pdf.setFontSize(8);
      pdf.setFont('helvetica', 'normal');
      pdf.text(
        `Trang ${i} / ${totalPages} - Generated by Cognitive Assessment System`,
        pageWidth / 2,
        pageHeight - 10,
        { align: 'center' }
      );
    }

    // Save PDF
    pdf.save(`cognitive_assessment_${sessionId}_${new Date().toISOString().split('T')[0]}.pdf`);
  } catch (error) {
    console.error('Error generating PDF:', error);
    throw error;
  }
}

