# Fix TTS và Hidden Content Issues

## Vấn đề

1. **Registration words bị lộ**: "Ba từ đó là: Con mèo, Chiếc xe, Cây lúa." đang hiển thị trong question text
2. **TTS không đọc được**: Khi content bị ẩn bằng HiddenMessage, TTS không đọc được full content
3. **Clock Drawing**: Cần modal/popup với đầy đủ tính năng vẽ

## Giải pháp

### 1. Fix Registration Words Bị Lộ
- Backend: Đảm bảo `words_announcement` không được include trong question text nếu đã có `hidden_content`
- Frontend: HiddenMessage sẽ ẩn words trong text

### 2. Fix TTS để đọc Full Content
- TTS cần đọc `originalContent` (chưa bị ẩn) thay vì `visibleText` (đã bị ẩn)
- Thêm prop `originalContent` vào HiddenMessage
- TTS sẽ dùng `originalContent` để đọc

### 3. Cải thiện ClockDrawingWhiteboard
- Chuyển thành Modal/Dialog component
- Thêm color picker
- Thêm brush size control
- Thêm save/export functionality
- Submit image để validate bằng GPT





