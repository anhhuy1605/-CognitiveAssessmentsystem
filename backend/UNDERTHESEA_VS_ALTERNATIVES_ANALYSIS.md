# So Sánh Underthesea vs Alternatives & Đề Xuất Feature Extraction

## 📋 TỔNG QUAN

Hệ thống hiện tại sử dụng **underthesea** cho tokenization và POS tagging. Tài liệu này phân tích:
1. Tại sao chọn underthesea
2. Underthesea có thể làm thêm gì
3. So sánh với các alternatives (nếu có)

---

## 🔍 TẠI SAO DÙNG UNDERTHESEA?

### **Lý do hiện tại:**

1. **Pure Python, dễ cài đặt**
   - `pip install underthesea` - không cần Java như VnCoreNLP
   - Không cần server riêng
   - Tích hợp dễ dàng vào Python codebase

2. **Đủ cho nhu cầu hiện tại**
   - Tokenization: ✅ `underthesea.word_tokenize()`
   - POS tagging: ✅ `underthesea.pos_tag()`
   - Đây là 2 tính năng chính cần cho lexical features

3. **Thay thế VnCoreNLP**
   - VnCoreNLP yêu cầu Java server
   - Khó deploy, phức tạp hơn
   - Underthesea đơn giản hơn nhiều

### **Nhược điểm hiện tại:**

1. **Chưa tận dụng hết tính năng**
   - Underthesea có NER, dependency parsing, sentiment
   - Code hiện tại chỉ dùng tokenization + POS tagging
   - Dependency parsing bị bỏ qua (comment: "required VnCoreNLP")

2. **Parse depth = 0.0**
   - Code có `mean_parse_depth` nhưng luôn = 0.0
   - Đây là feature quan trọng cho MCI detection
   - MCI patients có cấu trúc câu đơn giản hơn

---

## 🚀 UNDERTHESEA CÓ THỂ LÀM THÊM GÌ?

### **1. Dependency Parsing (Phân tích cú pháp phụ thuộc)**

**Tính năng:**
```python
import underthesea

# Dependency parsing
result = underthesea.dependency_parse("Tôi đi học hôm nay")
# Returns: List of tuples with (word, head, relation)
```

**Features có thể extract:**

#### **A. Parse Tree Depth** (Hiện tại = 0.0)
```python
def extract_parse_depth(text):
    """Calculate maximum depth of dependency parse tree"""
    parse_result = underthesea.dependency_parse(text)
    # Build tree and calculate max depth
    # MCI patients: shallower trees (simpler syntax)
    return max_depth
```

**Clinical significance:**
- MCI patients: **Shallower parse trees** (câu đơn giản hơn)
- Normal aging: Có thể dùng câu phức tạp hơn
- Feature: `syn_mean_parse_depth`, `syn_max_parse_depth`

#### **B. Dependency Relations**
```python
def extract_dependency_features(text):
    """Extract dependency relation statistics"""
    parse_result = underthesea.dependency_parse(text)
    
    # Count relation types
    relations = {
        'nsubj': 0,      # Nominal subject
        'obj': 0,        # Object
        'amod': 0,       # Adjectival modifier
        'advmod': 0,     # Adverbial modifier
        'conj': 0,       # Conjunct
        'acl': 0,        # Adjectival clause
        # ... more relations
    }
    
    # MCI patients: Fewer complex relations (acl, conj)
    return relations
```

**Features:**
- `syn_nsubj_ratio`: Subject usage
- `syn_obj_ratio`: Object usage
- `syn_acl_ratio`: Relative clauses (complexity indicator)
- `syn_conj_ratio`: Coordination (complexity indicator)

#### **C. Long-distance Dependencies**
```python
def extract_long_distance_deps(text):
    """Count long-distance dependencies (head-child distance)"""
    parse_result = underthesea.dependency_parse(text)
    
    # Calculate distance between head and dependent
    # MCI patients: Shorter dependencies (simpler structure)
    return {
        'mean_dependency_distance': float,
        'max_dependency_distance': int,
        'long_distance_ratio': float  # Dependencies > 3 words
    }
```

---

### **2. Named Entity Recognition (NER)**

**Tính năng:**
```python
import underthesea

# NER
result = underthesea.ner("Tôi tên là Nguyễn Văn A, sống ở Hà Nội")
# Returns: List of (word, entity_type)
# Types: PERSON, LOCATION, ORGANIZATION, etc.
```

**Features có thể extract:**

#### **A. Entity Density**
```python
def extract_ner_features(text):
    """Extract NER-based features"""
    entities = underthesea.ner(text)
    
    # Count entities
    person_count = sum(1 for _, etype in entities if etype == 'PERSON')
    location_count = sum(1 for _, etype in entities if etype == 'LOCATION')
    
    # MCI patients: May use fewer specific entities (word-finding difficulty)
    return {
        'ner_total_entities': len(entities),
        'ner_person_ratio': person_count / total_words,
        'ner_location_ratio': location_count / total_words,
        'ner_entity_density': len(entities) / total_words
    }
```

**Clinical significance:**
- MCI patients: **Fewer specific entities** (dùng "người đó" thay vì tên)
- Word-finding difficulty → generic references
- Feature: `sem_ner_density`, `sem_specificity_score`

#### **B. Entity Repetition**
```python
def extract_entity_repetition(text):
    """Check if same entity mentioned multiple times"""
    entities = underthesea.ner(text)
    
    # Count unique vs total entities
    # MCI patients: May repeat same entity (perseveration)
    unique_entities = set(entities)
    repetition_ratio = 1 - (len(unique_entities) / len(entities))
    
    return {
        'ner_repetition_ratio': repetition_ratio,
        'ner_unique_entities': len(unique_entities)
    }
```

---

### **3. Sentiment Analysis**

**Tính năng:**
```python
import underthesea

# Sentiment
result = underthesea.sentiment("Tôi cảm thấy rất vui")
# Returns: 'positive', 'negative', 'neutral'
```

**Features có thể extract:**

#### **A. Emotional Content**
```python
def extract_sentiment_features(text):
    """Extract sentiment-based features"""
    sentences = split_sentences(text)
    
    sentiments = []
    for sent in sentences:
        sentiment = underthesea.sentiment(sent)
        sentiments.append(sentiment)
    
    # MCI patients: May have different emotional patterns
    return {
        'sentiment_positive_ratio': sentiments.count('positive') / len(sentiments),
        'sentiment_negative_ratio': sentiments.count('negative') / len(sentiments),
        'sentiment_neutral_ratio': sentiments.count('neutral') / len(sentences),
        'sentiment_variability': calculate_variability(sentiments)
    }
```

**Clinical significance:**
- MCI patients: Có thể có **emotional blunting** hoặc **apathy**
- Feature: `prag_sentiment_score`, `prag_emotional_range`

---

### **4. Chunking (Noun/Verb Phrases)**

**Tính năng:**
```python
import underthesea

# Chunking
result = underthesea.chunk("Tôi đi học hôm nay")
# Returns: Noun phrases, verb phrases
```

**Features có thể extract:**

#### **A. Phrase Complexity**
```python
def extract_chunking_features(text):
    """Extract phrase-level features"""
    chunks = underthesea.chunk(text)
    
    # Count phrase types
    np_count = sum(1 for chunk in chunks if chunk.type == 'NP')
    vp_count = sum(1 for chunk in chunks if chunk.type == 'VP')
    
    # Average phrase length
    np_lengths = [len(chunk.words) for chunk in chunks if chunk.type == 'NP']
    mean_np_length = np.mean(np_lengths) if np_lengths else 0
    
    # MCI patients: Shorter phrases, fewer modifiers
    return {
        'chunk_np_count': np_count,
        'chunk_vp_count': vp_count,
        'chunk_mean_np_length': mean_np_length,
        'chunk_np_vp_ratio': np_count / vp_count if vp_count > 0 else 0
    }
```

---

## 📊 SO SÁNH VỚI ALTERNATIVES

### **1. VnCoreNLP (Đã loại bỏ)**

| Feature | Underthesea | VnCoreNLP |
|---------|-------------|-----------|
| Tokenization | ✅ | ✅ |
| POS Tagging | ✅ | ✅ |
| Dependency Parsing | ✅ | ✅ |
| NER | ✅ | ✅ |
| Installation | `pip install` | Java server required |
| Performance | Medium | Fast |
| Maintenance | Active | Less active |

**Kết luận:** Underthesea đủ tốt, dễ dùng hơn VnCoreNLP.

---

### **2. PhoNLP (VinAI Research)**

**PhoNLP** là một BERT-based multi-task learning model từ VinAI Research, được publish tại NAACL 2021.

**GitHub:** https://github.com/VinAIResearch/PhoNLP

**Tính năng:**
- ✅ **POS Tagging** (Part-of-Speech)
- ✅ **NER** (Named Entity Recognition)
- ✅ **Dependency Parsing**
- ✅ **Multi-task learning** (3 tasks trong 1 model)
- ✅ **State-of-the-art results** trên Vietnamese benchmark datasets

**Installation:**
```bash
pip3 install phonlp
```

**Usage:**
```python
import phonlp

# Load pre-trained model
model = phonlp.load(save_dir='/path/to/pretrained_phonlp')

# Annotate sentence (word-segmented)
result = model.annotate(text="Tôi đang làm_việc tại VinAI .")
# Output: 6 columns (word index, word form, POS, NER, head index, dependency relation)
```

**Yêu cầu:**
- Input phải là **word-segmented** (đã tách từ)
- Có thể dùng VnCoreNLP để word segmentation trước
- Dựa trên PhoBERT (Vietnamese BERT)

**So sánh với Underthesea:**

| Feature | Underthesea | PhoNLP |
|---------|-------------|--------|
| POS Tagging | ✅ | ✅ (Better accuracy) |
| NER | ✅ | ✅ (Better accuracy) |
| Dependency Parsing | ✅ | ✅ (Better accuracy) |
| Multi-task | ❌ (Separate models) | ✅ (Joint model) |
| Accuracy | Good | **State-of-the-art** |
| Installation | `pip install underthesea` | `pip install phonlp` |
| Word Segmentation | Built-in | Requires VnCoreNLP |
| Speed | Fast | Slower (BERT-based) |
| Model Size | Small | Large (BERT model) |
| Maintenance | Active | Active (VinAI) |

**Ưu điểm PhoNLP:**
1. ✅ **Better accuracy** - State-of-the-art results
2. ✅ **Joint model** - 3 tasks trong 1 model (consistency)
3. ✅ **BERT-based** - Leverage pre-trained PhoBERT
4. ✅ **Research-backed** - Published tại NAACL 2021

**Nhược điểm PhoNLP:**
1. ❌ **Cần word segmentation trước** - Phải dùng VnCoreNLP
2. ❌ **Chậm hơn** - BERT model lớn hơn
3. ❌ **Model size lớn** - Cần download pre-trained model
4. ❌ **Phức tạp hơn** - Cần setup VnCoreNLP

**Kết luận:**
- **PhoNLP tốt hơn về accuracy** nhưng phức tạp hơn
- **Underthesea đơn giản hơn** và đủ tốt cho nhiều use cases
- **Nếu cần accuracy cao nhất** → Dùng PhoNLP
- **Nếu cần đơn giản, nhanh** → Dùng Underthesea

---

### **3. spaCy Vietnamese (Nếu có)**

| Feature | Underthesea | spaCy (if available) |
|---------|-------------|---------------------|
| Tokenization | ✅ | ✅ |
| POS Tagging | ✅ | ✅ |
| Dependency Parsing | ✅ | ✅ |
| NER | ✅ | ✅ |
| Language Support | Vietnamese-focused | Multi-language |
| Vietnamese-specific | Better | May be less optimized |

**Kết luận:** Underthesea tốt hơn cho tiếng Việt.

---

## 🎯 ĐỀ XUẤT CẢI THIỆN

### **Priority 1: Dependency Parsing (HIGH)**

**Lý do:**
- Parse depth hiện tại = 0.0 (bỏ qua)
- Đây là feature quan trọng cho MCI detection
- Underthesea đã hỗ trợ sẵn

**Implementation:**
```python
def extract_syntactic_features_with_parsing(self, transcript: str):
    """Enhanced syntactic features with dependency parsing"""
    # ... existing code ...
    
    # ADD: Dependency parsing
    if UNDERTHESEA_AVAILABLE:
        try:
            parse_result = underthesea.dependency_parse(transcript)
            
            # Calculate parse depth
            mean_parse_depth = self._calculate_parse_depth_from_deps(parse_result)
            
            # Extract dependency relations
            dep_features = self._extract_dependency_relations(parse_result)
            
            # Update features
            features['mean_parse_depth'] = mean_parse_depth
            features.update(dep_features)
            
        except Exception as e:
            logger.warning(f"Dependency parsing failed: {e}")
```

**New features:**
- `syn_mean_parse_depth` (thay vì 0.0)
- `syn_max_parse_depth`
- `syn_nsubj_ratio`
- `syn_obj_ratio`
- `syn_acl_ratio` (complexity indicator)
- `syn_mean_dependency_distance`

---

### **Priority 2: NER Features (MEDIUM)**

**Lý do:**
- Có thể phát hiện word-finding difficulty
- Entity specificity là indicator tốt

**Implementation:**
```python
def extract_semantic_features_with_ner(self, transcript: str):
    """Enhanced semantic features with NER"""
    # ... existing code ...
    
    # ADD: NER
    if UNDERTHESEA_AVAILABLE:
        try:
            entities = underthesea.ner(transcript)
            
            ner_features = {
                'ner_total_entities': len(entities),
                'ner_entity_density': len(entities) / total_words,
                'ner_person_ratio': ...,
                'ner_location_ratio': ...,
                'ner_repetition_ratio': ...
            }
            
            features.update(ner_features)
            
        except Exception as e:
            logger.warning(f"NER failed: {e}")
```

**New features:**
- `sem_ner_density`
- `sem_ner_person_ratio`
- `sem_ner_location_ratio`
- `sem_ner_repetition_ratio` (perseveration indicator)

---

### **Priority 3: Chunking Features (LOW)**

**Lý do:**
- Phrase-level analysis có thể bổ sung
- Nhưng ít quan trọng hơn dependency parsing

**New features:**
- `chunk_mean_np_length`
- `chunk_np_vp_ratio`
- `chunk_phrase_complexity`

---

## 📈 TÁC ĐỘNG ĐẾN FEATURE COUNT

**Hiện tại:**
- Lexical: 14 features
- Syntactic: 9 features (nhưng parse_depth = 0.0)
- Semantic: 6 features
- Vietnamese-specific: 15 features
- **Total: ~42 features**

**Sau khi thêm:**
- Lexical: 14 features (không đổi)
- Syntactic: **15 features** (+6 từ dependency parsing)
- Semantic: **10 features** (+4 từ NER)
- Vietnamese-specific: 15 features (không đổi)
- **Total: ~54 features** (+12 features mới)

---

## ✅ KẾT LUẬN & RECOMMENDATION

### **Tại sao hiện tại dùng underthesea:**
1. ✅ Pure Python, dễ cài đặt (`pip install underthesea`)
2. ✅ Đủ tính năng cơ bản (tokenization, POS)
3. ✅ Có thêm NER, dependency parsing, sentiment
4. ✅ Tốt hơn VnCoreNLP về mặt deployment (không cần Java)
5. ✅ **Đơn giản, nhanh** - Phù hợp cho real-time processing

### **PhoNLP vs Underthesea:**

**Khi nào dùng Underthesea:**
- ✅ Cần **đơn giản, nhanh**
- ✅ Real-time processing (chatbot)
- ✅ Không cần accuracy cao nhất
- ✅ Muốn tránh phụ thuộc VnCoreNLP

**Khi nào nên xem xét PhoNLP:**
- ✅ Cần **accuracy cao nhất** (research, evaluation)
- ✅ Batch processing (không cần real-time)
- ✅ Có thể setup VnCoreNLP cho word segmentation
- ✅ Cần joint model (consistency giữa POS, NER, dependency)

### **Có thể làm thêm với Underthesea:**
1. **Dependency Parsing** (Priority 1) ⭐
   - Parse depth (hiện tại = 0.0)
   - Dependency relations
   - Long-distance dependencies

2. **NER** (Priority 2)
   - Entity density
   - Entity specificity
   - Repetition detection

3. **Sentiment & Chunking** (Priority 3)
   - Emotional content
   - Phrase complexity

### **Có thể làm thêm với PhoNLP:**
1. **Thay thế hoàn toàn** underthesea nếu cần accuracy cao
2. **Joint features** - Tận dụng consistency giữa POS, NER, dependency
3. **Better dependency parsing** - State-of-the-art results

---

## 🎯 RECOMMENDATION

### **Option 1: Giữ Underthesea + Tận dụng hết tính năng (RECOMMENDED)**

**Lý do:**
- ✅ Đơn giản, đã tích hợp sẵn
- ✅ Đủ tốt cho MCI detection
- ✅ Real-time processing
- ✅ Không cần thay đổi architecture

**Action items:**
1. **Implement dependency parsing** với underthesea (Priority 1)
2. **Add NER features** với underthesea (Priority 2)
3. **Test và so sánh** accuracy với baseline

**Code changes:**
- Update `linguistic_analyzer.py` để dùng `underthesea.dependency_parse()`
- Update `linguistic_analyzer.py` để dùng `underthesea.ner()`
- Tính `mean_parse_depth` từ dependency parse results

---

### **Option 2: Migrate sang PhoNLP (Nếu cần accuracy cao hơn)**

**Lý do:**
- ✅ State-of-the-art accuracy
- ✅ Joint model (consistency)
- ✅ Better cho research/evaluation

**Action items:**
1. **Setup PhoNLP** + VnCoreNLP (word segmentation)
2. **Replace underthesea** trong `linguistic_analyzer.py`
3. **Test performance** và accuracy improvement
4. **Evaluate trade-off** giữa accuracy và complexity

**Code changes:**
```python
# Thay vì:
import underthesea
tokens = underthesea.word_tokenize(text)
pos_tags = underthesea.pos_tag(text)

# Dùng:
import phonlp
model = phonlp.load(save_dir='/path/to/pretrained_phonlp')
result = model.annotate(text=word_segmented_text)
# Extract: POS, NER, dependency từ result
```

**Trade-offs:**
- ✅ Better accuracy
- ❌ Phức tạp hơn (cần VnCoreNLP)
- ❌ Chậm hơn (BERT model)
- ❌ Model size lớn hơn

---

### **Option 3: Hybrid Approach (Best of both worlds)**

**Lý do:**
- ✅ Underthesea cho real-time (chatbot)
- ✅ PhoNLP cho batch processing (evaluation, research)

**Implementation:**
```python
class VietnameseLinguisticAnalyzer:
    def __init__(self, use_phonlp=False):
        if use_phonlp:
            # Use PhoNLP for high accuracy
            self.phonlp_model = phonlp.load(...)
            self.use_phonlp = True
        else:
            # Use underthesea for speed
            self.use_phonlp = False
    
    def extract_features(self, text):
        if self.use_phonlp:
            return self._extract_with_phonlp(text)
        else:
            return self._extract_with_underthesea(text)
```

---

## 📊 FINAL RECOMMENDATION

**Cho hệ thống hiện tại (MMSE Chatbot):**

✅ **Option 1: Giữ Underthesea + Implement dependency parsing**

**Lý do:**
1. Chatbot cần **real-time processing** → Underthesea nhanh hơn
2. Accuracy hiện tại đã **đủ tốt** cho MCI detection
3. **Đơn giản hơn** → Dễ maintain
4. **Parse depth = 0.0** là vấn đề lớn nhất → Có thể fix với underthesea

**Action plan:**
1. ✅ Implement `underthesea.dependency_parse()` trong `linguistic_analyzer.py`
2. ✅ Tính `mean_parse_depth` từ parse results
3. ✅ Extract dependency relation features
4. ✅ Test và so sánh với baseline

**Nếu sau này cần accuracy cao hơn:**
- Có thể migrate sang PhoNLP sau
- Hoặc dùng hybrid approach (PhoNLP cho batch, underthesea cho real-time)

---

**References:**
- PhoNLP GitHub: https://github.com/VinAIResearch/PhoNLP
- PhoNLP Paper: NAACL 2021 - "PhoNLP: A joint multi-task learning model for Vietnamese part-of-speech tagging, named entity recognition and dependency parsing"

