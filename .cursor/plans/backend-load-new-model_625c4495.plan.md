---
name: backend-load-new-model
overview: Make backend load the new spec-compliant model bundle in models/ and bypass legacy imports that block startup.
todos:
  - id: relax-imports
    content: Bọc/guard import pipeline_api & modules phụ để không chặn startup
    status: completed
  - id: model-path
    content: Đảm bảo load_model_bundle dùng models/ và feature_names json/pkl
    status: completed
  - id: startup-check
    content: Thêm log/health check xác nhận model mới load được
    status: completed
---

## Goal

Backend khởi động dùng model mới (bundle trong `models/`), không bị chặn bởi import/pipeline cũ.

## Plan

1) Relax legacy imports: bọc/ghi chú các import không cần thiết (pipeline_api, clinical_ml_models, VietnameseTranscriber, language packs) để không chặn startup khi thiếu.

2) Load bundle path: giữ `models/` làm default, hỗ trợ feature_names json/pkl (đã có), và log rõ ràng khi load thành công.