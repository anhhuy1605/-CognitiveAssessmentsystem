"""
Vietnamese language translations for backend
"""

TRANSLATIONS = {
    # General
    "success": "Thành công",
    "error": "Lỗi",
    "loading": "Đang tải...",
    "processing": "Đang xử lý...",
    "completed": "Hoàn thành",
    "failed": "Thất bại",
    "unknown_error": "Lỗi không xác định",
    
    # Transcription
    "transcribing": "Đang chuyển đổi âm thanh...",
    "transcription_completed": "Chuyển đổi hoàn thành",
    "transcription_failed": "Chuyển đổi thất bại",
    "audio_file_not_found": "Không tìm thấy file âm thanh",
    "openai_api_key_not_configured": "Chưa cấu hình OpenAI API key",
    "openai_transcription_failed": "Chuyển đổi OpenAI thất bại",
    "improving_transcript": "Đang cải thiện chất lượng transcript...",
    "transcript_improvement_completed": "Cải thiện transcript hoàn thành",
    "transcript_improvement_failed": "Cải thiện transcript thất bại",
    
    # Cognitive Assessment
    "cognitive_assessment": "Đánh giá nhận thức",
    "memory_test": "Bài kiểm tra trí nhớ",
    "attention_test": "Bài kiểm tra sự chú ý",
    "language_test": "Bài kiểm tra ngôn ngữ",
    "processing_speed_test": "Bài kiểm tra tốc độ xử lý",
    "executive_function_test": "Bài kiểm tra chức năng điều hành",
    
    # Assessment Questions
    "question_1": "Bạn tên gì?",
    "question_2": "Bạn bao nhiêu tuổi?",
    "question_3": "Hôm nay là thứ mấy?",
    "question_4": "Bây giờ là tháng mấy?",
    "question_5": "Bây giờ là năm nào?",
    "question_6": "Bạn đang ở đâu?",
    "question_7": "Tổng thống hiện tại là ai?",
    "question_8": "Bạn có thể đếm ngược từ 20 không?",
    "question_9": "100 trừ 7 bằng bao nhiêu?",
    "question_10": "Bạn có thể đánh vần ngược từ 'THẾ GIỚI' không?",
    
    # Memory Test
    "memory_instructions": "Tôi sẽ cho bạn xem một số từ. Hãy nhớ chúng vì tôi sẽ yêu cầu bạn nhắc lại sau.",
    "memory_recall_instructions": "Bây giờ hãy nhắc lại các từ tôi đã cho bạn xem trước đó.",
    "memory_words": ["táo", "nhà", "xe", "sách", "cây"],
    
    # Attention Test
    "attention_instructions": "Tôi sẽ đọc một chuỗi số. Hãy nhắc lại chúng.",
    "attention_sequence_1": "3, 7, 1, 9",
    "attention_sequence_2": "8, 2, 5, 4, 1",
    "attention_sequence_3": "6, 9, 2, 7, 3, 1",
    
    # Language Test
    "language_instructions": "Hãy mô tả những gì bạn thấy trong bức tranh này.",
    "language_prompt": "Hãy kể về ngày hôm qua của bạn.",
    
    # Processing Speed
    "speed_instructions": "Hãy hoàn thành bài tập này càng nhanh càng tốt.",
    "speed_counting": "Đếm từ 1 đến 20 càng nhanh càng tốt.",
    
    # Executive Function
    "executive_instructions": "Hãy làm theo hướng dẫn này một cách cẩn thận.",
    "executive_task": "Chạm vào mũi bằng tay phải, sau đó chạm vào tai trái bằng tay trái.",
    
    # Results
    "assessment_results": "Kết quả đánh giá",
    "score": "Điểm số",
    "performance": "Hiệu suất",
    "excellent": "Xuất sắc",
    "good": "Tốt",
    "average": "Trung bình",
    "below_average": "Dưới trung bình",
    "poor": "Kém",
    
    # Analysis
    "cognitive_analysis": "Phân tích nhận thức",
    "memory_score": "Điểm trí nhớ",
    "attention_score": "Điểm sự chú ý",
    "language_score": "Điểm ngôn ngữ",
    "processing_speed_score": "Điểm tốc độ xử lý",
    "executive_function_score": "Điểm chức năng điều hành",
    "overall_score": "Điểm tổng thể",
    
    # Recommendations
    "recommendations": "Khuyến nghị",
    "memory_recommendation": "Hãy xem xét các bài tập trí nhớ và hoạt động rèn luyện não bộ.",
    "attention_recommendation": "Thực hành các bài tập tập trung và kỹ thuật chánh niệm.",
    "language_recommendation": "Tham gia các hoạt động đọc sách và trò chuyện.",
    "speed_recommendation": "Thử các hoạt động có thời gian và bài tập dựa trên tốc độ.",
    "executive_recommendation": "Thực hành các nhiệm vụ lập kế hoạch và tổ chức.",
    
    # System Messages
    "system_ready": "Hệ thống sẵn sàng",
    "system_initializing": "Đang khởi tạo hệ thống...",
    "system_error": "Lỗi hệ thống",
    "api_health_check": "Kiểm tra sức khỏe API",
    "model_loaded": "Đã tải model thành công",
    "model_loading": "Đang tải model...",
    "model_error": "Lỗi tải model",
    
    # File Operations
    "file_uploaded": "Đã tải file thành công",
    "file_processing": "Đang xử lý file...",
    "file_error": "Lỗi xử lý file",
    "file_too_large": "File quá lớn",
    "invalid_file_type": "Loại file không hợp lệ",
    
    # Time
    "seconds": "giây",
    "minutes": "phút",
    "processing_time": "Thời gian xử lý",
    "total_time": "Tổng thời gian",
    
    # Quality Metrics
    "confidence": "Độ tin cậy",
    "accuracy": "Độ chính xác",
    "quality": "Chất lượng",
    "high_quality": "Chất lượng cao",
    "medium_quality": "Chất lượng trung bình",
    "low_quality": "Chất lượng thấp",
    
    # Models
    "openai_whisper": "OpenAI Whisper",
    "gpt4o": "GPT-4o",
    "whisper_1": "Whisper-1",
    "model_used": "Model được sử dụng",
    
    # Status
    "status": "Trạng thái",
    "ready": "Sẵn sàng",
    "busy": "Bận",
    "offline": "Ngoại tuyến",
    "online": "Trực tuyến",
    
    # User Interface
    "start_recording": "Bắt đầu ghi âm",
    "stop_recording": "Dừng ghi âm",
    "submit": "Gửi",
    "cancel": "Hủy",
    "retry": "Thử lại",
    "save": "Lưu",
    "export": "Xuất",
    "download": "Tải xuống",
    "print": "In",
    
    # Navigation
    "home": "Trang chủ",
    "assessment": "Đánh giá",
    "results": "Kết quả",
    "settings": "Cài đặt",
    "help": "Trợ giúp",
    "about": "Giới thiệu",
    
    # Settings
    "language": "Ngôn ngữ",
    "english": "Tiếng Anh",
    "vietnamese": "Tiếng Việt",
    "theme": "Giao diện",
    "light": "Sáng",
    "dark": "Tối",
    "auto": "Tự động",
    "notifications": "Thông báo",
    "sound": "Âm thanh",
    "volume": "Âm lượng",
    "language_settings": "Cài đặt ngôn ngữ",
    "language_description": "Chọn ngôn ngữ bạn muốn sử dụng cho giao diện và đánh giá nhận thức.",
    "current_language": "Ngôn ngữ hiện tại",
    "full_name": "Họ và tên",
    "age": "Tuổi",
    "gender": "Giới tính",
    "email": "Email",
    "phone": "Số điện thoại",
    "edit_profile": "Chỉnh sửa thông tin",
    "logout": "Đăng xuất",
    "logout_confirmation": "Bạn muốn đăng xuất khỏi tài khoản hiện tại?",
    
    # Help
    "help_title": "Trợ giúp & Hỗ trợ",
    "how_to_use": "Cách sử dụng",
    "faq": "Câu hỏi thường gặp",
    "contact": "Liên hệ hỗ trợ",
    "documentation": "Tài liệu",
    
    # About
    "about_title": "Về Hệ thống Đánh giá Nhận thức",
    "version": "Phiên bản",
    "developer": "Nhà phát triển",
    "license": "Giấy phép",
    "privacy_policy": "Chính sách bảo mật",
    "terms_of_service": "Điều khoản dịch vụ",
}
