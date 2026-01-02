# Kế hoạch Enhance Results Page với SHAP

## Yêu cầu

1. Results page phải extract TẤT CẢ thông tin:
   - Acoustic features (f0, jitter, shimmer, formants, etc.)
   - Linguistic features (word count, pause duration, etc.)
   - SHAP explanations (feature importance, contributions)
   - MCI prediction scores và breakdowns

2. TSX Results page:
   - Đầy đủ, thân thiện, dễ hiểu
   - Visualizations cho features
   - SHAP explanations với charts
   - Export PDF đầy đủ

3. PDF Export:
   - Tất cả features
   - SHAP explanations
   - Charts và visualizations
   - Professional formatting

## Các bước

1. Đọc SHAP output file để hiểu cấu trúc
2. Tích hợp SHAP vào backend API
3. Extract all features từ session state
4. Build comprehensive results page TSX
5. Implement PDF export với jsPDF hoặc react-pdf

