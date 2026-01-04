# Fix KeyError 'completed' và TypeError questionResults.map

## Vấn đề

1. **KeyError: 'completed'** (dòng 999)
   - Khi test hoàn thành, `domain.value` = 'completed'
   - Nhưng `state.responses` không có key 'completed'
   - Code: `state.responses[domain.value].append(response)` fail

2. **TypeError: questionResults.map is not a function** (frontend)
   - Frontend expect `questionResults` là array
   - Backend có thể trả về object hoặc null

## Giải pháp

### 1. Fix KeyError 'completed'
- Check nếu domain là COMPLETED thì không append vào responses
- Hoặc initialize `state.responses['completed'] = []` khi test complete

### 2. Fix questionResults.map
- Backend: Đảm bảo trả về array `[]` nếu không có data
- Frontend: Thêm check `Array.isArray()` trước khi map





