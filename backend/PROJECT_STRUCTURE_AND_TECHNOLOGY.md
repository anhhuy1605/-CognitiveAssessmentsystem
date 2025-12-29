# PHẦN 1: CẤU TRÚC DỰ ÁN & CÔNG NGHỆ

## 1. Cấu Trúc Thư Mục Dự Án

### 1.1. Tree Structure

```
CognitiveAssessmentSystem/
├── frontend/                    # Next.js Frontend Application
│   ├── app/                     # Next.js App Router
│   │   ├── (main)/             # Main application routes
│   │   │   ├── cognitive-assessment/
│   │   │   ├── diagrams/
│   │   │   ├── features/
│   │   │   ├── info/
│   │   │   ├── mmse-chatbot/
│   │   │   ├── results/
│   │   │   └── stats/
│   │   ├── (marketing)/         # Marketing pages
│   │   ├── api/                 # API routes (33 endpoints)
│   │   ├── hooks/               # Custom React hooks
│   │   ├── providers/           # Context providers
│   │   └── types/               # TypeScript type definitions
│   ├── components/              # React components
│   │   ├── diagrams/            # System diagram components (6 files)
│   │   ├── info/                # Information page components (10 files)
│   │   ├── memory-test/         # Memory test components (3 files)
│   │   ├── results/             # Result display components (2 files)
│   │   ├── shap/                # SHAP explainability dashboard
│   │   └── ui/                   # UI components (17 files)
│   ├── lib/                     # Utility libraries
│   │   ├── languages/           # Language support
│   │   └── api-config.ts        # API configuration
│   ├── db/                      # Database configuration
│   │   ├── drizzle.ts           # Drizzle ORM setup
│   │   └── schema.ts             # Database schema
│   ├── public/                  # Static assets
│   └── scripts/                 # Utility scripts
│
├── backend/                     # Flask Backend Application
│   ├── modules/                 # Core modules (12 Python files)
│   │   ├── acoustic_analyzer.py      # Acoustic feature extraction
│   │   ├── linguistic_analyzer.py    # Linguistic feature extraction
│   │   ├── multimodal_fusion.py      # Feature fusion
│   │   ├── mci_predictor.py          # MCI prediction
│   │   ├── shap_explainer.py         # SHAP explainability
│   │   ├── explanation_generator.py  # Human-readable explanations
│   │   ├── report_generator.py       # Report generation
│   │   └── integration_service.py    # Service integration
│   ├── routes/                  # API route handlers
│   │   ├── audio.py             # Audio processing routes
│   │   └── session.py           # Session management routes
│   ├── services/                # Business logic services
│   ├── middleware/              # Middleware components
│   ├── models/                  # ML models storage
│   ├── prompts/                 # Prompt templates
│   └── app.py                   # Main Flask application
│
├── deploy/                      # Deployment configuration
│   ├── docker-compose.prod.yml
│   └── Dockerfile
│
└── docs/                        # Documentation
```

### 1.2. Frontend Structure (Next.js)

#### App Router Structure
```
frontend/app/
├── (main)/                      # Main application (authenticated)
│   ├── cognitive-assessment/    # Cognitive assessment pages
│   ├── diagrams/                # System diagrams visualization
│   ├── features/                # Feature pages
│   ├── info/                    # Information pages
│   ├── mmse-chatbot/            # MMSE chatbot interface
│   ├── results/                  # Results display
│   └── stats/                    # Statistics dashboard
│
├── (marketing)/                 # Public marketing pages
│   ├── footer.tsx
│   ├── layout.tsx
│   └── page.tsx
│
└── api/                         # API routes (33 endpoints)
    ├── analyze-audio/
    ├── audio/process/
    ├── cognitive-assessment/
    ├── community/
    ├── gpt/evaluate/
    ├── news/
    ├── profile/
    ├── save-cognitive-assessment-results/
    └── text-to-speech/
```

#### Components Structure
```
frontend/components/
├── diagrams/                    # System visualization (6 components)
│   ├── Diagram1_SystemOverview.tsx
│   ├── Diagram2_DataFlow.tsx
│   ├── Diagram3_AcousticFeatures.tsx
│   ├── Diagram4_ASRLinguistic.tsx
│   ├── Diagram5_GPT4oEvaluation.tsx
│   └── Diagram6_ModelIntegration.tsx
│
├── info/                        # Information components (10 files)
│   ├── AboutProject.tsx
│   ├── AITechnology.tsx
│   ├── ComprehensiveResultsReport.tsx
│   ├── ContactSection.tsx
│   ├── HeroSection.tsx
│   ├── MCIExplanation.tsx
│   ├── NewsDetail.tsx
│   ├── NewsResearch.tsx
│   ├── ResultsMetrics.tsx
│   └── TeamSection.tsx
│
├── memory-test/                 # Memory test components (3 files)
│   ├── QuestionCard.tsx
│   ├── RecordingControls.tsx
│   └── TTSStatusIndicator.tsx
│
├── results/                     # Result display (2 files)
│   ├── DetailedResultCard.tsx
│   └── DetailedResultCardNew.tsx
│
├── shap/                        # SHAP explainability
│   └── SHAPDashboard.tsx
│
├── ui/                          # UI components (17 files)
│   ├── alert.tsx
│   ├── avatar.tsx
│   ├── badge.tsx
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── label.tsx
│   ├── progress.tsx
│   ├── select.tsx
│   ├── separator.tsx
│   ├── sheet.tsx
│   ├── tabs.tsx
│   └── ...
│
└── [Other components]
    ├── CognitiveAssessmentRecorder.tsx
    ├── CognitiveAssessmentResult.tsx
    ├── MMSETrendChart.tsx
    ├── MMSEUnifiedResultCard.tsx
    └── ...
```

### 1.3. Backend Structure (Flask)

#### Modules Structure
```
backend/modules/
├── acoustic_analyzer.py         # Acoustic feature extraction (117 features)
│   └── Purpose: Extract eGeMAPS + Vietnamese tone features
│
├── linguistic_analyzer.py       # Linguistic feature extraction (42 features)
│   └── Purpose: Extract lexical, syntactic, semantic features
│
├── multimodal_fusion.py         # Multimodal feature fusion
│   └── Purpose: Combine acoustic + linguistic features
│
├── mci_predictor.py            # MCI prediction model
│   └── Purpose: Rule-based + ML-based MCI prediction
│
├── shap_explainer.py           # SHAP explainability
│   └── Purpose: Compute SHAP values for feature importance
│
├── explanation_generator.py    # Human-readable explanations
│   └── Purpose: Generate Vietnamese explanations
│
├── report_generator.py         # Report generation
│   └── Purpose: Generate PDF/HTML reports
│
└── integration_service.py      # Service integration
    └── Purpose: Orchestrate all modules
```

#### Routes Structure
```
backend/routes/
├── audio.py                    # Audio processing endpoints
│   └── Endpoints: /api/audio/process, /api/audio/analyze
│
└── session.py                  # Session management endpoints
    └── Endpoints: /api/session/create, /api/session/update
```

#### Main Application
```
backend/app.py                  # Main Flask application
├── API Endpoints: ~47 routes
├── Services initialization
├── Middleware setup
└── Error handling
```

## 2. Frontend Technologies (package.json)

### 2.1. Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 15.2.3 | React framework with App Router |
| **React** | 18.2.0 | UI library |
| **React DOM** | 18.2.0 | React DOM renderer |
| **TypeScript** | ^5 | Type-safe JavaScript |

### 2.2. UI Libraries & Components

| Library | Version | Purpose |
|---------|---------|---------|
| **@radix-ui/react-dialog** | ^1.1.14 | Dialog component |
| **@radix-ui/react-label** | ^2.1.7 | Label component |
| **@radix-ui/react-select** | ^2.2.5 | Select dropdown |
| **@radix-ui/react-slot** | ^1.2.3 | Slot component |
| **lucide-react** | ^0.536.0 | Icon library |
| **tailwindcss** | ^4 | CSS framework |
| **framer-motion** | ^12.23.12 | Animation library |

### 2.3. Form Management

| Library | Version | Purpose |
|---------|---------|---------|
| **class-variance-authority** | ^0.7.1 | Component variants |
| **clsx** | ^2.1.1 | Class name utility |
| **tailwind-merge** | ^3.3.1 | Tailwind class merging |

> **Note**: React Hook Form và Zod không được tìm thấy trong package.json hiện tại, có thể đã được thay thế bằng form handling tự xây dựng.

### 2.4. Data Visualization

| Library | Version | Purpose |
|---------|---------|---------|
| **chart.js** | ^4.5.0 | Chart library |
| **react-chartjs-2** | ^5.3.0 | React wrapper for Chart.js |
| **recharts** | ^3.1.2 | Alternative chart library |

### 2.5. Database & ORM

| Library | Version | Purpose |
|---------|---------|---------|
| **drizzle-orm** | ^0.44.5 | TypeScript ORM |
| **drizzle-kit** | ^0.31.4 | Drizzle migration tool |
| **@neondatabase/serverless** | ^1.0.1 | Neon database client |
| **@vercel/postgres** | ^0.10.0 | Vercel Postgres client |
| **pg** | ^8.16.3 | PostgreSQL client |
| **postgres** | ^3.4.7 | PostgreSQL driver |
| **better-sqlite3** | ^12.4.1 | SQLite for local dev |

### 2.6. Authentication

| Library | Version | Purpose |
|---------|---------|---------|
| **@clerk/nextjs** | ^6.31.10 | Clerk authentication |
| **@clerk/backend** | ^2.13.0 | Clerk backend SDK |

### 2.7. AI/ML Integration

| Library | Version | Purpose |
|---------|---------|---------|
| **@google/generative-ai** | ^0.24.1 | Google Gemini API |
| **openai** | ^5.15.0 | OpenAI API client |
| **@huggingface/transformers** | ^3.7.2 | Hugging Face models |

### 2.8. File & Media Processing

| Library | Version | Purpose |
|---------|---------|---------|
| **@vercel/blob** | ^1.1.1 | Vercel Blob storage |
| **formidable** | ^3.5.4 | File upload handling |
| **form-data** | ^4.0.4 | Form data encoding |

### 2.9. Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| **date-fns** | ^4.1.0 | Date manipulation |
| **papaparse** | ^5.5.3 | CSV parsing |
| **gtts** | ^0.2.1 | Google Text-to-Speech |
| **node-gtts** | ^2.0.2 | TTS alternative |
| **jspdf** | ^3.0.2 | PDF generation |
| **jspdf-autotable** | ^5.0.2 | PDF tables |
| **html2pdf.js** | ^0.12.1 | HTML to PDF |

### 2.10. Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **eslint** | ^9 | Linting |
| **eslint-config-next** | 15.2.3 | Next.js ESLint config |
| **cross-env** | ^7.0.3 | Cross-platform env vars |
| **@types/node** | ^20 | Node.js types |
| **@types/react** | ^18.2.79 | React types |

## 3. Backend Technologies (requirements.txt)

### 3.1. Core Framework

| Technology | Version | Purpose |
|------------|---------|---------|
| **Flask** | >=2.0.0 | Web framework |
| **Flask-CORS** | >=3.0.0 | Cross-origin resource sharing |
| **Python** | 3.8+ | Programming language |

### 3.2. AI/ML Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **openai** | >=1.0.0 | OpenAI GPT-4o API |
| **google-generativeai** | >=0.8.0 | Google Gemini API |
| **scikit-learn** | >=1.0.0 | Machine learning |
| **xgboost** | >=1.5.0 | Gradient boosting |
| **torch** | >=1.9.0 | PyTorch |
| **transformers** | >=4.15.0 | Hugging Face transformers |
| **shap** | >=0.42.0 | SHAP explainability |
| **lime** | >=0.2.0 | LIME explainability |

### 3.3. Audio Processing

| Library | Version | Purpose |
|---------|---------|---------|
| **librosa** | >=0.10.0 | Audio analysis |
| **soundfile** | >=0.12.1 | Audio I/O |
| **pydub** | >=0.25.0 | Audio manipulation |
| **praat-parselmouth** | >=0.4.3 | Praat integration (F0, jitter, shimmer) |
| **openai-whisper** | >=20230124 | Speech-to-text |

### 3.4. NLP Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| **underthesea** | >=6.6.0 | Vietnamese NLP (tokenization, POS tagging) |

> **Note**: VnCoreNLP đã được loại bỏ, thay thế bằng underthesea + PhoBERT.

### 3.5. Data Processing

| Library | Version | Purpose |
|---------|---------|---------|
| **numpy** | >=1.21.0 | Numerical computing |
| **pandas** | >=1.3.0 | Data manipulation |
| **scipy** | (implicit) | Scientific computing |

### 3.6. Database

| Library | Version | Purpose |
|---------|---------|---------|
| **pg** | >=0.0.0 | PostgreSQL adapter |
| **psycopg2** | (implicit) | PostgreSQL driver |

### 3.7. Development & Utilities

| Library | Version | Purpose |
|---------|---------|---------|
| **matplotlib** | >=3.5.0 | Plotting |
| **joblib** | >=1.1.0 | Parallel processing |
| **python-dotenv** | >=1.0.0 | Environment variables |

## 4. Thống Kê Dự Án

### 4.1. File Statistics

| Metric | Frontend | Backend | Total |
|--------|----------|---------|-------|
| **TypeScript/TSX Files** | ~152 files | - | ~152 files |
| **Python Files** | - | ~101 files | ~101 files |
| **Total Source Files** | ~152 | ~101 | **~253 files** |

### 4.2. Lines of Code

| Metric | Frontend | Backend | Total |
|--------|----------|---------|-------|
| **TypeScript/TSX Lines** | ~961,750 lines | - | ~961,750 lines |
| **Python Lines** | - | ~144,200 lines | ~144,200 lines |
| **Total Lines of Code** | ~961,750 | ~144,200 | **~1,105,950 lines** |

> **Note**: Số dòng code frontend có thể bao gồm node_modules hoặc các file generated. Số thực tế có thể thấp hơn.

### 4.3. Components & Modules

| Type | Count | Description |
|------|-------|-------------|
| **React Components** | ~59 | UI components trong `frontend/components/` |
| **Next.js Pages** | ~26 | Pages trong `frontend/app/(main)/` |
| **API Routes (Frontend)** | 33 | API endpoints trong `frontend/app/api/` |
| **Backend Modules** | 12 | Core modules trong `backend/modules/` |
| **Backend API Endpoints** | ~47 | Routes trong `backend/app.py` và `backend/routes/` |

### 4.4. Component Breakdown

#### Frontend Components by Category

| Category | Count | Files |
|----------|-------|-------|
| **UI Components** | 17 | `components/ui/*.tsx` |
| **Info Components** | 10 | `components/info/*.tsx` |
| **Diagram Components** | 6 | `components/diagrams/*.tsx` |
| **Memory Test** | 3 | `components/memory-test/*.tsx` |
| **Results** | 2 | `components/results/*.tsx` |
| **Other Components** | ~21 | Various utility components |

#### Backend Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `acoustic_analyzer.py` | Acoustic feature extraction | 117 features (eGeMAPS + Vietnamese tone) |
| `linguistic_analyzer.py` | Linguistic feature extraction | 42 features (lexical, syntactic, semantic) |
| `multimodal_fusion.py` | Feature fusion | Early/late/hybrid fusion |
| `mci_predictor.py` | MCI prediction | Rule-based + ML-based |
| `shap_explainer.py` | SHAP explainability | TreeSHAP, KernelSHAP, Rule-based |
| `explanation_generator.py` | Human-readable explanations | Vietnamese/English explanations |
| `report_generator.py` | Report generation | PDF/HTML reports |
| `integration_service.py` | Service orchestration | Pipeline coordination |

### 4.5. API Endpoints Summary

#### Frontend API Routes (Next.js App Router)

| Category | Count | Examples |
|----------|-------|----------|
| **Audio Processing** | 2 | `/api/audio/process`, `/api/analyze-audio` |
| **Cognitive Assessment** | 3 | `/api/cognitive-assessment`, `/api/save-cognitive-assessment-results` |
| **Community** | 4 | `/api/community`, `/api/community/finalize` |
| **GPT Evaluation** | 1 | `/api/gpt/evaluate` |
| **News** | 3 | `/api/news/feeds`, `/api/news/summarize` |
| **Profile** | 2 | `/api/profile`, `/api/profile/user` |
| **Text-to-Speech** | 1 | `/api/text-to-speech` |
| **Other** | 17 | Various utility endpoints |

**Total Frontend API Routes: 33**

#### Backend API Endpoints (Flask)

| Category | Count | Examples |
|----------|-------|----------|
| **Audio Processing** | ~10 | `/api/audio/upload`, `/api/audio/analyze` |
| **Feature Extraction** | ~8 | `/api/features/acoustic`, `/api/features/linguistic` |
| **MCI Prediction** | ~5 | `/api/mci/predict`, `/api/mci/explain` |
| **SHAP Explainability** | ~3 | `/api/shap-explanations`, `/api/shap-report` |
| **Session Management** | ~5 | `/api/session/create`, `/api/session/update` |
| **Results** | ~8 | `/api/results/save`, `/api/results/get` |
| **Other** | ~8 | Health check, configuration, etc. |

**Total Backend API Endpoints: ~47**

**Grand Total API Endpoints: ~80**

## 5. Technology Stack Summary

### 5.1. Frontend Stack

```
┌─────────────────────────────────────┐
│         Next.js 15.2.3              │
│      (React 18.2.0 + TypeScript)     │
├─────────────────────────────────────┤
│  UI: Tailwind CSS + Radix UI         │
│  Icons: Lucide React                 │
│  Charts: Chart.js + Recharts         │
│  Animation: Framer Motion            │
├─────────────────────────────────────┤
│  Database: Drizzle ORM + Neon        │
│  Auth: Clerk                         │
│  Storage: Vercel Blob                │
├─────────────────────────────────────┤
│  AI: Google Gemini + OpenAI          │
│  TTS: Google TTS                     │
└─────────────────────────────────────┘
```

### 5.2. Backend Stack

```
┌─────────────────────────────────────┐
│         Flask 2.0+                  │
│         Python 3.8+                 │
├─────────────────────────────────────┤
│  AI/ML: scikit-learn, xgboost        │
│  NLP: underthesea, transformers      │
│  Audio: librosa, parselmouth         │
│  Explainability: SHAP, LIME           │
├─────────────────────────────────────┤
│  APIs: OpenAI GPT-4o, Gemini         │
│  Database: PostgreSQL (Neon)         │
│  Storage: Vercel Blob                │
└─────────────────────────────────────┘
```

## 6. Key File Purposes

### 6.1. Frontend Key Files

| File | Purpose |
|------|---------|
| `frontend/app/layout.tsx` | Root layout with providers |
| `frontend/app/page.tsx` | Home page |
| `frontend/components/CognitiveAssessmentRecorder.tsx` | Main assessment recorder |
| `frontend/components/CognitiveAssessmentResult.tsx` | Result display |
| `frontend/components/shap/SHAPDashboard.tsx` | SHAP explainability UI |
| `frontend/db/schema.ts` | Database schema definition |
| `frontend/lib/api-config.ts` | API configuration |

### 6.2. Backend Key Files

| File | Purpose |
|------|---------|
| `backend/app.py` | Main Flask application (~6,500 lines) |
| `backend/main_pipeline.py` | Main MCI screening pipeline |
| `backend/modules/acoustic_analyzer.py` | Acoustic feature extraction |
| `backend/modules/linguistic_analyzer.py` | Linguistic feature extraction |
| `backend/modules/multimodal_fusion.py` | Feature fusion logic |
| `backend/modules/mci_predictor.py` | MCI prediction model |
| `backend/modules/shap_explainer.py` | SHAP explainability |

## 7. Architecture Highlights

### 7.1. Frontend Architecture

- **Framework**: Next.js 15 với App Router
- **Styling**: Tailwind CSS 4 với custom components
- **State Management**: React Context API + Hooks
- **Database**: Drizzle ORM với Neon PostgreSQL
- **Authentication**: Clerk với Next.js integration
- **File Storage**: Vercel Blob cho audio files

### 7.2. Backend Architecture

- **Framework**: Flask với modular structure
- **Feature Extraction**: Parallel processing (acoustic + linguistic)
- **ML Pipeline**: Rule-based + ML-based prediction
- **Explainability**: SHAP values với human-readable explanations
- **API Design**: RESTful API với error handling

### 7.3. Integration Points

- **Frontend ↔ Backend**: REST API calls
- **Audio Processing**: FFmpeg preprocessing → Feature extraction
- **ASR**: Google Gemini API → Transcript → Linguistic analysis
- **ML Pipeline**: Features → Fusion → Prediction → Explanation
- **Database**: Neon PostgreSQL cho persistent storage

## Notes

1. **Code Statistics**: Số dòng code frontend có thể bao gồm generated files hoặc dependencies. Số thực tế của source code có thể thấp hơn.

2. **API Endpoints**: Một số endpoints có thể được chia sẻ giữa frontend và backend, tổng số unique endpoints có thể thấp hơn 80.

3. **Dependencies**: Một số dependencies có thể không được sử dụng trực tiếp nhưng được yêu cầu bởi các dependencies khác.

4. **Module Count**: Backend modules có thể được mở rộng với các utility modules trong `backend/services/` và `backend/utils/`.


