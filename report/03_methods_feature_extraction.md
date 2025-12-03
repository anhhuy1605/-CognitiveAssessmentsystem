# PHẦN III: PHƯƠNG PHÁP TRÍCH XUẤT ĐẶC TRƯNG

## 1. Xử lý Fundamental Frequency (F0)

### 1.1 Vấn đề với tiếng Việt

Tiếng Việt là ngôn ngữ thanh điệu với 6 thanh (ngang, sắc, huyền, hỏi, ngã, nặng). Điều này khiến F0 (fundamental frequency) – đặc trưng nền của cao độ – biến thiên một cách có hệ thống theo nội dung ngôn ngữ, không chỉ theo sắc thái ngữ điệu hay trạng thái bệnh lý. Cụ thể: thanh ngang có đường F0 tương đối ổn định ở mức trung, thanh sắc tăng dần, thanh huyền giảm dần, thanh hỏi có dạng nhúng xuống rồi tăng (dip–rise), thanh ngã thường có pha tăng kèm tắt nghẽn glottal, và thanh nặng rơi mạnh với chất giọng khàn (creaky). Vì vậy, ngay cả người khỏe mạnh cũng có biến thiên F0 lớn khi phát âm các chuỗi âm tiết khác thanh nhau. Bài toán của chúng ta là tách biệt biến thiên F0 “ngôn ngữ học” (linguistic tone variation) với biến thiên F0 “bệnh lý/ngữ điệu” (pathological prosody), để các chỉ số phản ánh được chức năng nhận thức thay vì chỉ phản ánh kiểu thanh điệu.

### 1.2 Giải pháp: F0 residual

Ý tưởng là mô hình hóa đường F0 kỳ vọng theo từng thanh điệu (F0_expected_for_tone) và trừ khỏi đường F0 quan sát (F0_observed) để thu được phần dư (residual) – chính là biến thiên F0 không do thanh điệu chi phối:  
F0_residual = F0_observed − F0_expected_for_tone.  
F0_expected_for_tone có thể học từ corpus tiếng Việt có gán nhãn thanh điệu ở cấp âm tiết, tạo các “mẫu đường chuẩn” theo từng thanh và chuẩn hóa độ dài theo đơn vị âm tiết. Phần dư sau đó được tổng hợp thành các đặc trưng thống kê (mean, std, coefficient of variation, range, IQR) dùng trong mô hình nhận thức.

```python
def extract_f0_residual(audio_file):
    """
    Trích xuất F0 residual: biến động F0 không do thanh điệu
    Input: audio_file (.wav)
    Output: dict of F0 residual features
    """
    import numpy as np
    import librosa

    # Bước 1: Load audio
    y, sr = librosa.load(audio_file, sr=16000)

    # Bước 2: Trích xuất F0 thô bằng pYIN
    f0_raw, voiced_flag, voiced_prob = librosa.pyin(
        y,
        fmin=75,
        fmax=400,
        sr=sr
    )

    # Smoothing đơn giản để giảm nhiễu đo
    def median_filter(x, k=5):
        x = np.array(x, dtype=float)
        pad = k // 2
        x_pad = np.pad(x, (pad, pad), mode='edge')
        return np.array([np.median(x_pad[i:i+k]) for i in range(len(x))])

    f0_raw_smoothed = median_filter(f0_raw, k=5)

    # Bước 3: Phân đoạn âm tiết và nhận diện thanh điệu (giả định có hàm sẵn)
    syllables = segment_syllables_vietnamese(y, sr)  # [(start_idx, end_idx), ...] trên trục frame
    tone_labels = [classify_tone(seg, y, sr) for seg in syllables]  # 1..6

    # Bước 4: Tải các mẫu F0 baseline theo thanh (từ corpus)
    tone_templates = load_vietnamese_tone_templates()  # dict: tone -> 1D array

    # Bước 5: Tính residual theo từng âm tiết
    f0_residual_values = []
    for (start_idx, end_idx), tone in zip(syllables, tone_labels):
        f0_syllable = f0_raw_smoothed[start_idx:end_idx]
        if f0_syllable.size == 0 or np.all(np.isnan(f0_syllable)):
            continue

        baseline = tone_templates.get(tone)
        if baseline is None or len(baseline) == 0:
            continue

        # Chuẩn hóa độ dài baseline theo số điểm F0 của âm tiết
        t_src = np.linspace(0, 1, num=len(baseline))
        t_dst = np.linspace(0, 1, num=len(f0_syllable))
        baseline_interp = np.interp(t_dst, t_src, baseline)

        residual = f0_syllable - baseline_interp
        residual = residual[~np.isnan(residual)]
        if residual.size:
            f0_residual_values.extend(residual)

    f0_residual_values = np.array(f0_residual_values)
    if f0_residual_values.size == 0:
        return {
            'f0_residual_mean': np.nan,
            'f0_residual_std': np.nan,
            'f0_residual_cv': np.nan,
            'f0_residual_range': np.nan,
            'f0_residual_iqr': np.nan
        }

    # Bước 6: Đặc trưng thống kê
    mean = float(np.mean(f0_residual_values))
    std = float(np.std(f0_residual_values))
    iqr = float(np.percentile(f0_residual_values, 75) - np.percentile(f0_residual_values, 25))
    cv = float(std / mean) if mean != 0 else np.nan
    value_range = float(np.max(f0_residual_values) - np.min(f0_residual_values))

    return {
        'f0_residual_mean': mean,
        'f0_residual_std': std,
        'f0_residual_cv': cv,
        'f0_residual_range': value_range,
        'f0_residual_iqr': iqr
    }
```

### 1.3 Tham số đề xuất

- Hop length: ~10 ms (ví dụ 160 mẫu @16 kHz hoặc 512 mẫu với khung 2048).  
- Frame size: ~50 ms để ổn định ước lượng F0.  
- F0 range: 75–400 Hz bao phủ nam và nữ; có thể điều chỉnh động theo giới.  
- Smoothing: median filter 5 khung để giảm outlier từ pYIN.

## 2. Các đặc trưng acoustic bổ sung

### 2.1 Formants (F1, F2, F3)

```python
def extract_formants_vietnamese(audio_file):
    """
    Trích xuất formant frequencies bằng Praat/parselmouth
    Formants phản ánh cấu trúc vocal tract và chất lượng phát âm
    """
    import numpy as np
    import parselmouth

    sound = parselmouth.Sound(audio_file)
    formants = sound.to_formant_burg(
        time_step=0.01,         # 10 ms
        max_num_formants=5,
        max_formant=5500,       # Hz
        window_length=0.025,    # 25 ms
        pre_emphasis_from=50
    )

    f1_values, f2_values, f3_values = [], [], []
    t = 0.0
    while t < sound.get_total_duration():
        f1 = formants.get_value_at_time(1, t)
        f2 = formants.get_value_at_time(2, t)
        f3 = formants.get_value_at_time(3, t)
        if not np.isnan(f1): f1_values.append(f1)
        if not np.isnan(f2): f2_values.append(f2)
        if not np.isnan(f3): f3_values.append(f3)
        t += 0.01

    def safe_mean(x):
        return float(np.mean(x)) if len(x) else np.nan

    return {
        'f1_mean': safe_mean(f1_values),
        'f1_std': float(np.std(f1_values)) if len(f1_values) else np.nan,
        'f2_mean': safe_mean(f2_values),
        'f2_std': float(np.std(f2_values)) if len(f2_values) else np.nan,
        'f3_mean': safe_mean(f3_values),
        'formant_dispersion': (safe_mean(f2_values) - safe_mean(f1_values))
    }
```

Giải thích nhanh: F1 tương ứng độ mở nguyên âm (vowel height), F2 tương ứng vị trí trước–sau (frontness). Ở người suy giảm nhận thức, sự kém ổn định vận động–phối hợp có thể làm phân bố formant kém rõ nét, tăng phương sai.

### 2.2 Jitter & Shimmer (voice quality)

```python
def extract_voice_quality(audio_file):
    """
    Jitter: biến thiên chu kỳ F0; Shimmer: biến thiên biên độ
    HNR: Harmonics-to-Noise Ratio
    """
    import parselmouth
    sound = parselmouth.Sound(audio_file)
    pitch = sound.to_pitch()
    point_process = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")

    jitter_local = parselmouth.praat.call(point_process, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    shimmer_local = parselmouth.praat.call([sound, point_process], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    harmonicity = sound.to_harmonicity_cc()
    hnr_mean = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)

    return {
        'jitter_local': float(jitter_local),
        'shimmer_local': float(shimmer_local),
        'hnr_mean': float(hnr_mean)
    }
```

Ý nghĩa lâm sàng: jitter cao → F0 không ổn định; shimmer cao → biên độ không đều; HNR thấp → nhiều nhiễu; các thay đổi này có thể liên quan suy giảm điều hành/điều tiết prosody.

## 3. Pause patterns & speech rate

### 3.1 Phát hiện pause

```python
def analyze_pauses(audio_file):
    """
    Pause = khoảng lặng trong lời nói; chỉ dấu của processing speed
    """
    import numpy as np
    import librosa

    y, sr = librosa.load(audio_file, sr=16000)

    # RMS energy và ngưỡng VAD đơn giản ở -40 dB
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    is_speech = rms_db > -40

    hop_time = 512 / sr
    speech_segments, pause_segments = [], []
    state = 'pause'
    seg_start = 0.0
    for i, flag in enumerate(is_speech):
        t = i * hop_time
        if flag and state == 'pause':
            # kết thúc một pause, bắt đầu speech
            if i > 0:
                pause_segments.append({'start': seg_start, 'end': t})
            state = 'speech'
            seg_start = t
        elif (not flag) and state == 'speech':
            speech_segments.append({'start': seg_start, 'end': t})
            state = 'pause'
            seg_start = t

    # khép segment cuối
    total_duration = len(y) / sr
    if state == 'speech':
        speech_segments.append({'start': seg_start, 'end': total_duration})
    else:
        pause_segments.append({'start': seg_start, 'end': total_duration})

    pause_durs = [seg['end'] - seg['start'] for seg in pause_segments]
    total_pause = float(sum(pause_durs))
    long_pauses = [d for d in pause_durs if d > 2.0]

    return {
        'pause_frequency': len(pause_segments) / (total_duration / 60.0) if total_duration > 0 else 0.0,
        'pause_mean_duration': float(np.mean(pause_durs)) if pause_durs else 0.0,
        'pause_ratio': (total_pause / total_duration) if total_duration > 0 else 0.0,
        'long_pause_count': len(long_pauses),
        'speech_time': total_duration - total_pause
    }
```

### 3.2 Speech rate

```python
def calculate_speech_rate(audio_file, transcript):
    """
    Speech rate = số âm tiết/giây (xấp xỉ bằng số token tiếng Việt/giây)
    Bình thường: 3–5 syll/s
    """
    import numpy as np
    from underthesea import word_tokenize

    tokens = word_tokenize(transcript)
    num_syllables = len(tokens)

    pause_info = analyze_pauses(audio_file)
    speech_time = max(pause_info['speech_time'], 1e-6)

    speech_rate = num_syllables / speech_time
    articulation_rate = num_syllables / (speech_time + max(pause_info['pause_mean_duration'], 1e-6))

    return {
        'speech_rate': float(speech_rate),
        'articulation_rate': float(articulation_rate),
        'num_syllables': int(num_syllables)
    }
```

Diễn giải lâm sàng: 3–5 syll/s thường coi là bình thường; <3 gợi ý chậm xử lý hoặc rối loạn vận động lời nói; >6 có thể gặp trong lo âu/hưng cảm (không đặc hiệu cho sa sút).

## 4. Linguistic features

### 4.1 Lexical diversity

```python
def compute_lexical_diversity(transcript):
    """
    Đa dạng từ vựng: TTR, MATTR, MTLD; chỉ báo semantic memory
    """
    import numpy as np
    from underthesea import word_tokenize
    import lexicalrichness

    tokens = word_tokenize(transcript, format="text").split()
    fillers = ['ừ', 'à', 'ờ', 'ể', 'hử', 'uhm']
    tokens_clean = [t for t in tokens if t.lower() not in fillers]

    types = len(set(tokens_clean))
    total = len(tokens_clean)
    ttr = (types / total) if total > 0 else 0.0

    window = 50
    mattr_scores = []
    for i in range(0, max(len(tokens_clean) - window + 1, 0)):
        w = tokens_clean[i:i+window]
        mattr_scores.append(len(set(w)) / window)
    mattr = float(np.mean(mattr_scores)) if mattr_scores else ttr

    lex = lexicalrichness.LexicalRichness(' '.join(tokens_clean))
    mtld = float(lex.mtld(threshold=0.72)) if total > 0 else 0.0

    compound_count = sum(1 for t in tokens_clean if '_' in t or ' ' in t)
    compound_ratio = (compound_count / total) if total > 0 else 0.0

    return {
        'ttr': float(ttr),
        'mattr': float(mattr),
        'mtld': float(mtld),
        'compound_ratio': float(compound_ratio),
        'unique_words': int(types),
        'total_words': int(total)
    }
```

Benchmarks gợi ý: bình thường TTR > 0.65, MTLD > 80; MCI thường 0.50–0.65 và 50–80; sa sút <0.50 và <50.

### 4.2 Syntactic complexity

```python
def compute_syntactic_complexity(transcript):
    """
    Độ phức tạp cú pháp: MLU và tỷ lệ mệnh đề phụ (proxy)
    """
    from underthesea import sent_tokenize, word_tokenize

    sentences = sent_tokenize(transcript)
    total_words = 0
    for s in sentences:
        total_words += len(word_tokenize(s))
    mlu = (total_words / len(sentences)) if sentences else 0.0

    markers = ['mà', 'nếu', 'vì', 'khi', 'tuy', 'nhưng', 'để']
    dep_count = sum(transcript.lower().count(m) for m in markers)
    dep_ratio = (dep_count / len(sentences)) if sentences else 0.0

    return {
        'mlu': float(mlu),
        'dependent_clause_ratio': float(dep_ratio),
        'num_sentences': int(len(sentences))
    }
```

### 4.3 Disfluencies (tiếng Việt)

```python
def detect_disfluencies_vietnamese(transcript):
    """
    Disfluency: filled pauses, repetitions, revisions, incomplete phrases
    """
    from underthesea import word_tokenize

    tokens = word_tokenize(transcript, format="text").split()
    filled = ['ừ', 'à', 'ờ', 'ể', 'hử', 'ơ', 'ô']
    filled_count = sum(1 for t in tokens if t.lower() in filled)

    reps = sum(1 for i in range(len(tokens)-1) if tokens[i].lower() == tokens[i+1].lower())

    markers = ['ý tôi là', 'tức là', 'hay là', 'không không']
    text_lower = transcript.lower()
    rev_count = sum(text_lower.count(m) for m in markers)

    inc_count = transcript.count('...')

    total_words = sum(1 for t in tokens if t.lower() not in filled)
    total_words = max(total_words, 1)

    return {
        'filled_pause_rate': filled_count / total_words,
        'repetition_rate': reps / total_words,
        'revision_count': int(rev_count),
        'incomplete_count': int(inc_count),
        'total_disfluencies': int(filled_count + reps + rev_count)
    }
```

## 5. Quality control & parameter settings

### 5.1 Quality control pipeline

```python
def quality_control_pipeline(audio_file):
    """
    Kiểm tra chất lượng audio trước khi trích xuất features
    """
    import numpy as np
    import librosa

    y, sr = librosa.load(audio_file, sr=16000)

    # 1) SNR > 15 dB
    noise_std = np.std(y[: int(0.5 * sr)]) if len(y) > int(0.5 * sr) else max(np.std(y), 1e-6)
    signal_std = max(np.std(y), 1e-6)
    snr = 20 * np.log10(signal_std / max(noise_std, 1e-6))
    if snr < 15:
        return {'status': 'REJECT', 'reason': f'SNR {snr:.1f} dB < 15', 'snr': float(snr)}

    # 2) Clipping
    max_amp = float(np.max(np.abs(y)))
    clipped = np.sum(np.abs(y) > 0.95)
    clip_ratio = clipped / max(len(y), 1)
    if clip_ratio > 0.01:
        return {'status': 'REJECT', 'reason': f'Clipping {clip_ratio*100:.2f}%', 'clipping_ratio': float(clip_ratio)}

    # 3) Speech ratio (VAD đơn giản theo RMS)
    rms = librosa.feature.rms(y=y)[0]
    rms_db = librosa.amplitude_to_db(rms, ref=np.max)
    speech_frames = int(np.sum(rms_db > -40))
    speech_ratio = speech_frames / max(len(rms_db), 1)
    if speech_ratio < 0.3:
        return {'status': 'REJECT', 'reason': f'Speech ratio {speech_ratio*100:.1f}% < 30%', 'speech_ratio': float(speech_ratio)}

    # 4) Duration >= 30 s
    duration = len(y) / sr
    if duration < 30.0:
        return {'status': 'REJECT', 'reason': f'Duration {duration:.1f}s < 30s', 'duration': float(duration)}

    return {'status': 'PASS', 'snr': float(snr), 'clipping_ratio': float(clip_ratio), 'speech_ratio': float(speech_ratio), 'duration': float(duration)}
```

### 5.2 Handling missing data

- F0: nếu khung không voicing hoặc pYIN fail <10% → nội suy; >30% → loại đoạn hoặc loại bản ghi.  
- Formant: chỉ tính trên đoạn voiced; bỏ khung vô thanh.  
- Mức đặc trưng: <10% thiếu → multiple imputation; >10% → cân nhắc loại bỏ phiên.

### 5.3 Normalization và tham số tóm tắt

```python
def normalize_features(features, age, gender):
    """
    Điều chỉnh theo tuổi/giới; thêm biến chuẩn hóa khi cần
    """
    f = dict(features)
    if 'f0_mean' in f and f['f0_mean'] is not None:
        baseline = 120.0 if gender == 'male' else 220.0
        f['f0_mean_rel'] = f['f0_mean'] / baseline
    f['age'] = age
    f['gender'] = gender
    return f
```

#### Bảng tham số đề xuất

| Feature Type | Tool/Library | Key Parameters |
|--------------|--------------|----------------|
| F0 extraction | librosa.pyin | fmin=75Hz, fmax=400Hz, hop≈10ms, median k=5 |
| Formants | Praat/parselmouth | time_step=10ms, window=25ms, max_formant=5.5kHz |
| VAD threshold | RMS-based | −40 dB |
| Speech rate | underthesea | syllable-based tokenization |
| Lexical diversity | lexicalrichness | MTLD threshold=0.72, window=50 |
| Jitter/Shimmer | Praat | jitter 0.0001–0.02s; shimmer 1.3–1.6 params |


