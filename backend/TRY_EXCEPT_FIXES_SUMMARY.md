# Try-Except Fixes Summary

## Nguyên tắc
**"Nếu hệ thống đã import cái nào là xác định sẽ dùng cái đó, nên không thể None được"**

## Thay đổi chính

### 1. `backend/modules/__init__.py`
**Trước:** Try-except với set None khi import fail
**Sau:** Import trực tiếp, không try-except (nếu import fail → raise error)

```python
# TRƯỚC:
try:
    from .acoustic_analyzer import AcousticAnalyzer
except ImportError:
    AcousticAnalyzer = None

# SAU:
from .acoustic_analyzer import AcousticAnalyzer
```

### 2. `backend/modules/integration_service.py`
**Trước:** Try-except với flag `*_AVAILABLE` và check None
**Sau:** Import trực tiếp, không check None

```python
# TRƯỚC:
try:
    from .acoustic_analyzer import AcousticAnalyzer
    ACOUSTIC_AVAILABLE = True
except ImportError:
    ACOUSTIC_AVAILABLE = False
    # ...
if ACOUSTIC_AVAILABLE:
    self.acoustic_analyzer = AcousticAnalyzer()

# SAU:
from .acoustic_analyzer import AcousticAnalyzer
# ...
try:
    self.acoustic_analyzer = AcousticAnalyzer()
except Exception as e:
    raise  # If import succeeded but init failed, raise error
```

### 3. `backend/app.py`

#### 3.1. VietnameseTranscriber
**Trước:** Try-except với set None
**Sau:** Import trực tiếp

```python
# TRƯỚC:
try:
    from vietnamese_transcriber import VietnameseTranscriber
except ImportError:
    VietnameseTranscriber = None

# SAU:
from vietnamese_transcriber import VietnameseTranscriber
```

#### 3.2. MMSE Inference Pipeline
**Trước:** Try-except với set None
**Sau:** Import trực tiếp

```python
# TRƯỚC:
try:
    from inference_pipeline import InferenceConfig, MMSEInferencePipeline
    mmse_pipeline = MMSEInferencePipeline(...)
except ImportError:
    mmse_pipeline = None

# SAU:
from inference_pipeline import InferenceConfig, MMSEInferencePipeline
mmse_pipeline = MMSEInferencePipeline(...)
```

#### 3.3. MCI Screening Modules
**Trước:** Try-except với set None và flag `MCI_MODULES_AVAILABLE`
**Sau:** Import trực tiếp, chỉ set flag khi thành công

```python
# TRƯỚC:
try:
    from modules.integration_service import MCIScreeningService
    mci_service = MCIScreeningService(...)
    MCI_MODULES_AVAILABLE = True
except ImportError:
    mci_service = None
    MCI_MODULES_AVAILABLE = False

# SAU:
from modules.integration_service import MCIScreeningService
mci_service = MCIScreeningService(...)
MCI_MODULES_AVAILABLE = True
```

#### 3.4. Language Management
**Trước:** Try-except với set None
**Sau:** Import trực tiếp

```python
# TRƯỚC:
try:
    from languages import t, language_manager
except ImportError:
    t = lambda x: x
    language_manager = None

# SAU:
from languages import t, language_manager
```

#### 3.5. Loại bỏ các check None
**Trước:** Check `if mci_service is None:` hoặc `if mmse_pipeline is None:`
**Sau:** Chỉ check flag `MCI_MODULES_AVAILABLE` hoặc không check gì

```python
# TRƯỚC:
if mci_service is None:
    return error

# SAU:
if not MCI_MODULES_AVAILABLE:
    return error
```

## Kết quả

### ✅ Đã sửa
1. `modules/__init__.py` - Loại bỏ try-except, import trực tiếp
2. `modules/integration_service.py` - Loại bỏ flag `*_AVAILABLE`, import trực tiếp
3. `app.py` - Loại bỏ try-except cho các module chính, import trực tiếp
4. `app.py` - Loại bỏ các check `is None` sau khi import thành công
5. `app.py` - Sửa `initialize_model()` để không check `VietnameseTranscriber` là None

### ⚠️ Lưu ý
- Nếu import fail → raise ImportError (không set None)
- Nếu import thành công nhưng init fail → raise error (không set None)
- Chỉ check flag `MCI_MODULES_AVAILABLE` để biết module có sẵn không
- Không check `is None` cho các module đã import thành công

## Files Modified
1. `backend/modules/__init__.py`
2. `backend/modules/integration_service.py`
3. `backend/app.py`

## Testing
- Server sẽ raise error nếu import fail (thay vì set None)
- Server sẽ raise error nếu init fail sau khi import thành công
- Không còn check None cho các module đã import thành công













