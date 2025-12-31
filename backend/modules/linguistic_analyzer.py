# -*- coding: utf-8 -*-
"""
Linguistic Feature Extraction Module for Vietnamese MCI Screening
Fixes and enhances the existing linguistic analysis pipeline

Author: Cognitive Assessment System
Version: 1.0

Key References:
- Fraser et al. (2016) - Linguistic features for dementia detection
- Pakhomov et al. (2011) - Computerized analysis in Alzheimer's
"""

import re
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
# NOTE: Using PhoNLP + VnCoreNLP + PhoBERT pipeline
try:
    import phonlp
    PHONLP_AVAILABLE = True
except ImportError:
    PHONLP_AVAILABLE = False
    logger.warning("phonlp not available. Vietnamese NLP will be limited.")

try:
    import py_vncorenlp
    VNCORENLP_AVAILABLE = True
except ImportError:
    VNCORENLP_AVAILABLE = False
    logger.warning("py_vncorenlp not available. Word segmentation will be limited.")

try:
    import underthesea
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False
    underthesea = None
    logger.warning("underthesea not available. Tokenization/POS tagging will be limited.")

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logger.warning("transformers not available. Semantic features will be limited.")

try:
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class VietnameseLinguisticAnalyzer:
    """
    Comprehensive Linguistic Analysis for Vietnamese MCI Screening
    
    Features extracted:
    - Lexical features (TTR, MATTR, word frequency, POS distribution)
    - Syntactic features (MLU, clause complexity, parse depth)
    - Semantic features (coherence, idea density)
    - Vietnamese-specific features (classifiers, reduplications, tone markers)
    - Task-specific features (verbal fluency, picture description, Q&A)
    
    Key MCI Indicators:
    - Reduced lexical diversity (lower TTR)
    - Increased pronoun usage (word-finding difficulty)
    - Shorter utterances (MLU decline)
    - Lower idea density
    - Reduced semantic coherence
    """
    
    # Vietnamese POS tags (underthesea format)
    # underthesea uses Universal Dependencies tags: NOUN, VERB, ADJ, ADV, PRON, DET, NUM, ADP, CONJ, PART, INTJ
    POS_CATEGORIES = {
        'NOUN': ['NOUN', 'N', 'Np', 'Nc', 'Nu', 'Ny'],  # Nouns (including VnCoreNLP format for compatibility)
        'VERB': ['VERB', 'V'],                           # Verbs
        'ADJ': ['ADJ', 'A'],                            # Adjectives
        'ADV': ['ADV', 'R'],                            # Adverbs
        'PRON': ['PRON', 'P'],                           # Pronouns
        'DET': ['DET', 'L'],                            # Determiners
        'NUM': ['NUM', 'M'],                            # Numbers
        'PREP': ['ADP', 'E'],                           # Prepositions (ADP in UD)
        'CONJ': ['CONJ', 'CCONJ', 'SCONJ', 'C', 'CC'], # Conjunctions
        'PART': ['PART', 'T'],                           # Particles
        'INTERJ': ['INTJ', 'I'],                         # Interjections
        'CLASSIFIER': ['Nc', 'L'],                       # Classifiers (can be Nc or L in underthesea)
    }
    
    # Vietnamese tense markers
    TENSE_MARKERS = ['đã', 'sẽ', 'đang', 'vừa', 'sắp', 'hãy', 'chưa', 'rồi']
    
    # Aspect markers
    ASPECT_MARKERS = ['xong', 'được', 'hết', 'mất', 'ra', 'vào', 'lên', 'xuống']
    
    def __init__(self, use_phobert: bool = True):
        """
        Initialize Vietnamese Linguistic Analyzer
        
        Uses underthesea for tokenization/POS tagging and PhoBERT for semantic analysis.
        VnCoreNLP is no longer used.
        
        Args:
            use_phobert: Whether to use PhoBERT for semantic analysis
        """
        self.phobert_tokenizer = None
        self.phobert_model = None
        
        # Initialize PhoBERT for semantic analysis
        if use_phobert and TRANSFORMERS_AVAILABLE:
            try:
                self.phobert_tokenizer = AutoTokenizer.from_pretrained("vinai/phobert-base")
                self.phobert_model = AutoModel.from_pretrained("vinai/phobert-base")
                self.phobert_model.eval()
                logger.info("✅ PhoBERT initialized")
            except Exception as e:
                logger.warning(f"PhoBERT initialization failed: {e}")
        
        if not UNDERTHESEA_AVAILABLE:
            logger.warning("⚠️ underthesea not available. Tokenization/POS tagging will be limited.")
        
        logger.info("VietnameseLinguisticAnalyzer initialized (using underthesea + PhoBERT)")
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize Vietnamese text using underthesea
        
        Args:
            text: Raw Vietnamese text
        
        Returns:
            list: List of word tokens
        """
        if not text or not text.strip():
            return []
        
        if UNDERTHESEA_AVAILABLE:
            try:
                return underthesea.word_tokenize(text)
            except Exception as e:
                logger.warning(f"underthesea tokenization failed: {e}")
        
        # Fallback: simple whitespace tokenization
        return text.split()
    
    def pos_tag(self, text: str) -> List[Tuple[str, str]]:
        """
        POS tagging for Vietnamese using underthesea
        
        Args:
            text: Vietnamese text
        
        Returns:
            list: List of (word, pos_tag) tuples
        """
        if not text or not text.strip():
            return []
        
        if UNDERTHESEA_AVAILABLE:
            try:
                # underthesea.pos_tag returns list of tuples
                return underthesea.pos_tag(text)
            except Exception as e:
                logger.warning(f"underthesea POS tagging failed: {e}")
        
        # Fallback: no POS tags
        tokens = text.split()
        return [(token, 'UNK') for token in tokens]
    
    def extract_lexical_features(self, transcript: str) -> Dict[str, float]:
        """
        Extract lexical diversity features
        
        KEY FEATURES for MCI:
        - Type-Token Ratio (TTR): Vocabulary richness - DECREASES in MCI
        - Moving-Average TTR (MATTR): More stable measure
        - Brunet's Index: Another vocabulary richness measure
        - Pronoun ratio: INCREASES in MCI (word-finding difficulty)
        - Content word density: DECREASES in MCI
        
        Args:
            transcript: Text transcript
        
        Returns:
            dict: Lexical features
        """
        if not transcript or not transcript.strip():
            return self._empty_lexical_result()
        
        tokens = self.tokenize(transcript)
        pos_tags = self.pos_tag(transcript)
        
        if len(tokens) == 0:
            return self._empty_lexical_result()
        
        # Basic counts
        total_words = len(tokens)
        unique_words = len(set([t.lower() for t in tokens]))
        
        # 1. Type-Token Ratio (TTR)
        ttr = unique_words / total_words
        
        # 2. Moving-Average TTR (MATTR) - window=50
        # More robust than simple TTR for varying text lengths
        mattr_window = min(50, total_words)
        if total_words >= mattr_window:
            mattr_values = []
            for i in range(total_words - mattr_window + 1):
                window_tokens = [t.lower() for t in tokens[i:i + mattr_window]]
                window_ttr = len(set(window_tokens)) / mattr_window
                mattr_values.append(window_ttr)
            mattr = np.mean(mattr_values)
        else:
            mattr = ttr
        
        # 3. Brunet's Index: W = N^(V^(-0.165))
        # Lower = richer vocabulary
        brunet_index = total_words ** (unique_words ** (-0.165)) if unique_words > 0 else 0
        
        # 4. Honore's Statistic: R = (100 * log(N)) / (1 - (V1/V))
        # V1 = words occurring only once (hapax legomena)
        word_counts = {}
        for token in tokens:
            t = token.lower()
            word_counts[t] = word_counts.get(t, 0) + 1
        
        hapax = sum(1 for count in word_counts.values() if count == 1)
        if unique_words > hapax:
            honore_stat = (100 * np.log(total_words)) / (1 - hapax / unique_words)
        else:
            honore_stat = 0
        
        # POS-based features
        pos_counts = {}
        for word, pos in pos_tags:
            pos_counts[pos] = pos_counts.get(pos, 0) + 1
        
        # Pronouns (P): MCI patients use MORE pronouns (word-finding difficulty)
        pronouns = sum(pos_counts.get(p, 0) for p in self.POS_CATEGORIES.get('PRON', ['P']))
        pronoun_ratio = pronouns / total_words
        
        # Nouns: MCI patients use FEWER specific nouns
        nouns = sum(pos_counts.get(p, 0) for p in self.POS_CATEGORIES.get('NOUN', []))
        noun_ratio = nouns / total_words
        
        # Verbs
        verbs = sum(pos_counts.get(p, 0) for p in self.POS_CATEGORIES.get('VERB', []))
        verb_ratio = verbs / total_words
        
        # Adjectives
        adjectives = sum(pos_counts.get(p, 0) for p in self.POS_CATEGORIES.get('ADJ', []))
        adj_ratio = adjectives / total_words
        
        # Content words (Nouns, Verbs, Adjectives, Adverbs) vs function words
        # Support both underthesea (NOUN, VERB, ADJ, ADV) and VnCoreNLP (N, V, A, R) formats
        content_pos = ['NOUN', 'N', 'Np', 'Nc', 'VERB', 'V', 'ADJ', 'A', 'ADV', 'R']
        content_words = sum(pos_counts.get(p, 0) for p in content_pos)
        content_word_ratio = content_words / total_words
        
        # Noun-to-verb ratio
        noun_verb_ratio = nouns / verbs if verbs > 0 else 0
        
        # Word length statistics
        word_lengths = [len(token) for token in tokens]
        mean_word_length = np.mean(word_lengths)
        
        return {
            'total_words': total_words,
            'unique_words': unique_words,
            'ttr': float(ttr),
            'mattr': float(mattr),
            'brunet_index': float(brunet_index),
            'honore_stat': float(honore_stat),
            'hapax_ratio': float(hapax / total_words),
            'pronoun_ratio': float(pronoun_ratio),
            'noun_ratio': float(noun_ratio),
            'verb_ratio': float(verb_ratio),
            'adj_ratio': float(adj_ratio),
            'content_word_ratio': float(content_word_ratio),
            'noun_verb_ratio': float(noun_verb_ratio),
            'mean_word_length': float(mean_word_length)
        }
    
    def _empty_lexical_result(self) -> Dict[str, float]:
        """Return empty lexical feature structure"""
        return {
            'total_words': 0,
            'unique_words': 0,
            'ttr': 0.0,
            'mattr': 0.0,
            'brunet_index': 0.0,
            'honore_stat': 0.0,
            'hapax_ratio': 0.0,
            'pronoun_ratio': 0.0,
            'noun_ratio': 0.0,
            'verb_ratio': 0.0,
            'adj_ratio': 0.0,
            'content_word_ratio': 0.0,
            'noun_verb_ratio': 0.0,
            'mean_word_length': 0.0
        }
    
    def extract_syntactic_features(self, transcript: str) -> Dict[str, float]:
        """
        Extract syntactic complexity features
        
        KEY FEATURES:
        - Mean Length of Utterance (MLU): SHORTER in MCI
        - Incomplete sentence ratio: HIGHER in MCI
        - Syntactic complexity: LOWER in MCI
        
        Args:
            transcript: Text transcript
        
        Returns:
            dict: Syntactic features
        """
        if not transcript or not transcript.strip():
            return self._empty_syntactic_result()
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            return self._empty_syntactic_result()
        
        # Calculate MLU (Mean Length of Utterance)
        sentence_lengths_words = []
        sentence_lengths_chars = []
        incomplete_sentences = 0
        
        for sent in sentences:
            tokens = self.tokenize(sent)
            sentence_lengths_words.append(len(tokens))
            sentence_lengths_chars.append(len(sent))
            
            # Detect incomplete sentences (heuristics)
            # - Very short sentences
            # - Ends with conjunction
            # - Contains hesitation markers
            if len(tokens) < 3:
                incomplete_sentences += 1
            elif tokens and tokens[-1].lower() in ['và', 'hoặc', 'nhưng', 'mà', 'rồi', 'thì', 'nên']:
                incomplete_sentences += 1
        
        mlu_words = np.mean(sentence_lengths_words)
        mlu_chars = np.mean(sentence_lengths_chars)
        std_sentence_length = np.std(sentence_lengths_words)
        incomplete_ratio = incomplete_sentences / len(sentences)
        
        # Parse tree depth calculation removed (required VnCoreNLP)
        # Using clause density as alternative complexity measure
        mean_parse_depth = 0.0
        
        # Clause indicators (conjunctions, relative markers)
        tokens = self.tokenize(transcript)
        clause_markers = ['mà', 'khi', 'nếu', 'vì', 'do', 'để', 'tuy', 'dù', 'nên', 'cho']
        clause_count = sum(1 for t in tokens if t.lower() in clause_markers)
        clause_density = clause_count / len(sentences) if len(sentences) > 0 else 0
        
        return {
            'total_sentences': len(sentences),
            'mlu_words': float(mlu_words),
            'mlu_chars': float(mlu_chars),
            'std_sentence_length': float(std_sentence_length),
            'incomplete_sentence_ratio': float(incomplete_ratio),
            'mean_parse_depth': float(mean_parse_depth),
            'clause_density': float(clause_density),
            'max_sentence_length': int(max(sentence_lengths_words)),
            'min_sentence_length': int(min(sentence_lengths_words))
        }
    
    def _empty_syntactic_result(self) -> Dict[str, float]:
        """Return empty syntactic feature structure"""
        return {
            'total_sentences': 0,
            'mlu_words': 0.0,
            'mlu_chars': 0.0,
            'std_sentence_length': 0.0,
            'incomplete_sentence_ratio': 0.0,
            'mean_parse_depth': 0.0,
            'clause_density': 0.0,
            'max_sentence_length': 0,
            'min_sentence_length': 0
        }
    
    def _calculate_parse_depth(self, sentence: List[Dict]) -> int:
        """
        Calculate maximum depth of dependency parse tree
        
        Args:
            sentence: List of word dictionaries with 'head' and 'id' fields
        
        Returns:
            int: Maximum parse tree depth
        """
        if not sentence:
            return 0
        
        def get_depth(word_id: int, words: List[Dict], visited: set, depth: int = 0) -> int:
            if word_id in visited:
                return depth
            visited.add(word_id)
            
            children = [w for w in words if w.get('head', -1) == word_id]
            if not children:
                return depth
            return max(get_depth(child['id'], words, visited, depth + 1) for child in children)
        
        max_depth = 0
        for word in sentence:
            visited = set()
            depth = get_depth(word['id'], sentence, visited, 0)
            max_depth = max(max_depth, depth)
        
        return max_depth
    
    def extract_semantic_features(self, transcript: str) -> Dict[str, float]:
        """
        Extract semantic and discourse features
        
        KEY FEATURES:
        - Idea density: Propositions per 10 words - STRONGEST predictor (Fraser 2016)
        - Semantic coherence: Cosine similarity between sentences
        - Topic consistency
        
        Args:
            transcript: Text transcript
        
        Returns:
            dict: Semantic features
        """
        if not transcript or not transcript.strip():
            return self._empty_semantic_result()
        
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 1. Idea Density (simplified)
        # Count content words as proxy for propositions
        tokens = self.tokenize(transcript)
        pos_tags = self.pos_tag(transcript)
        
        # Support both underthesea (NOUN, VERB, ADJ) and VnCoreNLP (N, V, A) formats
        content_pos = ['NOUN', 'N', 'Np', 'Nc', 'VERB', 'V', 'ADJ', 'A']
        propositions = sum(1 for word, pos in pos_tags 
                         if any(pos == p or pos.startswith(p) for p in content_pos))
        
        # Propositions per 10 words
        idea_density = (propositions / len(tokens)) * 10 if len(tokens) > 0 else 0
        
        # 2. Semantic Coherence using PhoBERT embeddings
        mean_coherence = 0.0
        coherence_std = 0.0
        mean_embedding_norm = 0.0
        
        if self.phobert_model and self.phobert_tokenizer and len(sentences) >= 2:
            try:
                sentence_embeddings = []
                
                for sent in sentences:
                    inputs = self.phobert_tokenizer(
                        sent, 
                        return_tensors="pt", 
                        padding=True, 
                        truncation=True, 
                        max_length=256
                    )
                    
                    with torch.no_grad():
                        outputs = self.phobert_model(**inputs)
                        # Use [CLS] token embedding as sentence representation
                        embedding = outputs.last_hidden_state[:, 0, :].squeeze().numpy()
                        sentence_embeddings.append(embedding)
                
                # Calculate cosine similarity between consecutive sentences
                if SKLEARN_AVAILABLE:
                    coherence_scores = []
                    for i in range(len(sentence_embeddings) - 1):
                        sim = cosine_similarity(
                            sentence_embeddings[i].reshape(1, -1),
                            sentence_embeddings[i + 1].reshape(1, -1)
                        )[0][0]
                        coherence_scores.append(sim)
                    
                    mean_coherence = float(np.mean(coherence_scores)) if coherence_scores else 0.0
                    coherence_std = float(np.std(coherence_scores)) if coherence_scores else 0.0
                
                # Mean embedding norm (semantic richness)
                embedding_norms = [np.linalg.norm(emb) for emb in sentence_embeddings]
                mean_embedding_norm = float(np.mean(embedding_norms))
            
            except Exception as e:
                logger.warning(f"Semantic feature extraction failed: {e}")
        
        # 3. Information content estimate
        # Based on word frequency (rarer words = more information)
        word_counts = {}
        for token in tokens:
            t = token.lower()
            word_counts[t] = word_counts.get(t, 0) + 1
        
        # Entropy as information measure
        total = sum(word_counts.values())
        probs = [count / total for count in word_counts.values()]
        entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        
        return {
            'idea_density': float(idea_density),
            'semantic_coherence': float(mean_coherence),
            'coherence_std': float(coherence_std),
            'mean_embedding_norm': float(mean_embedding_norm),
            'information_entropy': float(entropy),
            'total_sentences_semantic': len(sentences)
        }
    
    def _empty_semantic_result(self) -> Dict[str, float]:
        """Return empty semantic feature structure"""
        return {
            'idea_density': 0.0,
            'semantic_coherence': 0.0,
            'coherence_std': 0.0,
            'mean_embedding_norm': 0.0,
            'information_entropy': 0.0,
            'total_sentences_semantic': 0
        }
    
    def extract_vietnamese_specific_features(self, transcript: str) -> Dict[str, float]:
        """
        Extract features specific to Vietnamese language
        
        Vietnamese-specific indicators:
        - Classifier usage (cái, con, chiếc, etc.) - proper usage may decline
        - Reduplication (đỏ đỏ, nhanh nhanh) - expressive feature
        - Tense/aspect markers (đã, sẽ, đang) - temporal reference
        - Sentence-final particles (à, ạ, nhé) - pragmatic markers
        
        Args:
            transcript: Text transcript
        
        Returns:
            dict: Vietnamese-specific features
        """
        if not transcript or not transcript.strip():
            return self._empty_vietnamese_result()
        
        tokens = self.tokenize(transcript)
        pos_tags = self.pos_tag(transcript)
        
        if len(tokens) == 0:
            return self._empty_vietnamese_result()
        
        total_words = len(tokens)
        
        # 1. Classifiers (using underthesea POS tags)
        # Common classifiers: cái, con, chiếc, quyển, tờ, bức
        # underthesea uses 'L' for classifiers/determiners, or we can check by word
        classifier_words = ['cái', 'con', 'chiếc', 'quyển', 'tờ', 'bức', 'người', 'cây', 'bông', 'viên']
        classifiers = [word for word, pos in pos_tags 
                      if pos == 'L' or word.lower() in classifier_words]
        classifier_count = len(classifiers)
        classifier_ratio = classifier_count / total_words
        
        # 2. Reduplications (word repetition for emphasis)
        # e.g., "đỏ đỏ", "nhanh nhanh", "từ từ"
        reduplications = 0
        for i in range(len(tokens) - 1):
            if tokens[i].lower() == tokens[i + 1].lower():
                reduplications += 1
        reduplication_ratio = reduplications / total_words
        
        # 3. Tense markers
        tense_marker_count = sum(1 for token in tokens if token.lower() in self.TENSE_MARKERS)
        tense_marker_ratio = tense_marker_count / total_words
        
        # 4. Aspect markers
        aspect_marker_count = sum(1 for token in tokens if token.lower() in self.ASPECT_MARKERS)
        aspect_marker_ratio = aspect_marker_count / total_words
        
        # 5. Sentence-final particles (pragmatic markers)
        # Common: à, ạ, nhé, nhỉ, đấy, đâu, chứ, mà
        final_particles = ['à', 'ạ', 'nhé', 'nhỉ', 'đấy', 'đâu', 'chứ', 'mà', 'sao', 'vậy']
        particle_count = sum(1 for token in tokens if token.lower() in final_particles)
        particle_ratio = particle_count / total_words
        
        # 6. Question words
        question_words = ['gì', 'ai', 'đâu', 'nào', 'sao', 'tại', 'bao', 'mấy', 'bằng']
        question_count = sum(1 for token in tokens if token.lower() in question_words)
        question_ratio = question_count / total_words
        
        # 7. Negation
        negation_words = ['không', 'chẳng', 'chưa', 'đừng', 'không phải', 'chẳng phải']
        negation_count = sum(1 for token in tokens if token.lower() in negation_words)
        negation_ratio = negation_count / total_words
        
        # 8. Filler words / hesitation markers
        fillers = ['ừ', 'ờ', 'à', 'um', 'ơ', 'thì', 'là', 'cái']
        filler_count = sum(1 for token in tokens if token.lower() in fillers)
        filler_ratio = filler_count / total_words
        
        return {
            'classifier_count': classifier_count,
            'classifier_ratio': float(classifier_ratio),
            'reduplication_count': reduplications,
            'reduplication_ratio': float(reduplication_ratio),
            'tense_marker_count': tense_marker_count,
            'tense_marker_ratio': float(tense_marker_ratio),
            'aspect_marker_count': aspect_marker_count,
            'aspect_marker_ratio': float(aspect_marker_ratio),
            'particle_count': particle_count,
            'particle_ratio': float(particle_ratio),
            'question_ratio': float(question_ratio),
            'negation_ratio': float(negation_ratio),
            'filler_ratio': float(filler_ratio)
        }
    
    def _empty_vietnamese_result(self) -> Dict[str, float]:
        """Return empty Vietnamese-specific feature structure"""
        return {
            'classifier_count': 0,
            'classifier_ratio': 0.0,
            'reduplication_count': 0,
            'reduplication_ratio': 0.0,
            'tense_marker_count': 0,
            'tense_marker_ratio': 0.0,
            'aspect_marker_count': 0,
            'aspect_marker_ratio': 0.0,
            'particle_count': 0,
            'particle_ratio': 0.0,
            'question_ratio': 0.0,
            'negation_ratio': 0.0,
            'filler_ratio': 0.0
        }
    
    def analyze_task_specific_features(self, transcript: str, 
                                        task_type: str) -> Dict[str, float]:
        """
        Extract features specific to cognitive task type
        
        Different tasks reveal different cognitive domains:
        - verbal_fluency: Semantic memory, executive function
        - picture_description: Narrative ability, visual processing
        - spontaneous_speech: General cognition
        - qa: Orientation, memory recall
        
        Args:
            transcript: Text transcript
            task_type: One of ['verbal_fluency', 'picture_description', 
                               'spontaneous_speech', 'qa']
        
        Returns:
            dict: Task-specific features
        """
        if not transcript or not transcript.strip():
            return {}
        
        if task_type == 'verbal_fluency':
            return self._analyze_verbal_fluency(transcript)
        elif task_type == 'picture_description':
            return self._analyze_picture_description(transcript)
        elif task_type == 'spontaneous_speech':
            return self._analyze_spontaneous_speech(transcript)
        elif task_type == 'qa':
            return self._analyze_qa(transcript)
        else:
            logger.warning(f"Unknown task type: {task_type}")
            return {}
    
    def _analyze_verbal_fluency(self, transcript: str) -> Dict[str, float]:
        """
        Analyze verbal fluency task (e.g., animal naming, category fluency)
        
        Key metrics:
        - Total valid responses
        - Unique responses
        - Repetitions (perseverations)
        - Clustering (semantic grouping)
        - Switching (between semantic clusters)
        """
        tokens = self.tokenize(transcript)
        
        if len(tokens) == 0:
            return {
                'vf_total_responses': 0,
                'vf_unique_responses': 0,
                'vf_repetitions': 0,
                'vf_repetition_rate': 0.0,
                'vf_cluster_size': 0.0
            }
        
        # Count unique and total responses
        unique_tokens = set([t.lower() for t in tokens])
        repetitions = len(tokens) - len(unique_tokens)
        
        # Estimate clustering (consecutive similar items)
        # This is a simplified version - ideally would use semantic categories
        cluster_sizes = []
        current_cluster = 1
        for i in range(1, len(tokens)):
            # Simple heuristic: same first character = same cluster
            if tokens[i][0].lower() == tokens[i - 1][0].lower():
                current_cluster += 1
            else:
                cluster_sizes.append(current_cluster)
                current_cluster = 1
        cluster_sizes.append(current_cluster)
        
        return {
            'vf_total_responses': len(tokens),
            'vf_unique_responses': len(unique_tokens),
            'vf_repetitions': repetitions,
            'vf_repetition_rate': float(repetitions / len(tokens)) if len(tokens) > 0 else 0.0,
            'vf_mean_cluster_size': float(np.mean(cluster_sizes)) if cluster_sizes else 0.0,
            'vf_num_clusters': len(cluster_sizes)
        }
    
    def _analyze_picture_description(self, transcript: str) -> Dict[str, float]:
        """
        Analyze picture description task (e.g., Cookie Theft picture)
        
        Key metrics:
        - Total entities mentioned
        - Actions described
        - Spatial/relational terms
        - Information units coverage (if ground truth available)
        """
        tokens = self.tokenize(transcript)
        pos_tags = self.pos_tag(transcript)
        
        if len(tokens) == 0:
            return {
                'pd_total_entities': 0,
                'pd_unique_entities': 0,
                'pd_total_actions': 0,
                'pd_spatial_terms': 0,
                'pd_entity_action_ratio': 0.0
            }
        
        # Count entities (nouns)
        entities = [word for word, pos in pos_tags if pos.startswith('N')]
        unique_entities = set([e.lower() for e in entities])
        
        # Count actions (verbs)
        actions = [word for word, pos in pos_tags if pos == 'V']
        
        # Spatial/relational terms
        spatial_words = ['trên', 'dưới', 'trong', 'ngoài', 'bên', 'cạnh', 'giữa', 
                        'trước', 'sau', 'phải', 'trái', 'gần', 'xa']
        spatial_count = sum(1 for t in tokens if t.lower() in spatial_words)
        
        return {
            'pd_total_entities': len(entities),
            'pd_unique_entities': len(unique_entities),
            'pd_total_actions': len(actions),
            'pd_spatial_terms': spatial_count,
            'pd_entity_action_ratio': float(len(entities) / len(actions)) if len(actions) > 0 else 0.0,
            'pd_words_per_entity': float(len(tokens) / len(unique_entities)) if len(unique_entities) > 0 else 0.0
        }
    
    def _analyze_spontaneous_speech(self, transcript: str) -> Dict[str, float]:
        """
        Analyze spontaneous speech (open-ended response)
        
        Focus on discourse coherence and flow
        """
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            return {
                'ss_total_sentences': 0,
                'ss_mean_sentence_length': 0.0,
                'ss_topic_continuity': 0.0
            }
        
        sentence_lengths = [len(self.tokenize(s)) for s in sentences]
        
        return {
            'ss_total_sentences': len(sentences),
            'ss_mean_sentence_length': float(np.mean(sentence_lengths)),
            'ss_std_sentence_length': float(np.std(sentence_lengths)) if len(sentence_lengths) > 1 else 0.0,
            'ss_topic_continuity': 0.0  # Would need semantic analysis
        }
    
    def _analyze_qa(self, transcript: str) -> Dict[str, float]:
        """
        Analyze Q&A responses (orientation, recall questions)
        
        Focus on response directness and accuracy
        """
        tokens = self.tokenize(transcript)
        
        if len(tokens) == 0:
            return {
                'qa_response_length': 0,
                'qa_conciseness_score': 0.0,
                'qa_has_answer': False
            }
        
        # Heuristic: concise, direct answers are better for Q&A
        # Too short = might be incomplete
        # Too long = might be rambling
        optimal_length = 5  # Words
        length_deviation = abs(len(tokens) - optimal_length)
        conciseness_score = max(0, 1.0 - length_deviation / 20)
        
        # Check if response contains answer indicators
        answer_indicators = ['là', 'tên', 'tuổi', 'năm', 'ngày', 'tháng']
        has_answer = any(t.lower() in answer_indicators for t in tokens)
        
        return {
            'qa_response_length': len(tokens),
            'qa_conciseness_score': float(conciseness_score),
            'qa_has_answer': has_answer
        }
    
    def extract_all_features(self, transcript: str, 
                              task_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Master function: Extract ALL linguistic features
        
        This is the main entry point for linguistic analysis.
        
        Args:
            transcript: Text transcript
            task_type: Optional task type for task-specific features
        
        Returns:
            dict: Comprehensive linguistic feature dictionary with ~50+ features
        """
        logger.info("📝 Starting comprehensive linguistic analysis...")
        features = {}
        
        # 1. Lexical Features
        logger.info("📚 Extracting lexical features...")
        lexical = self.extract_lexical_features(transcript)
        features.update({f"lex_{k}": v for k, v in lexical.items()})
        
        # 2. Syntactic Features
        logger.info("🔤 Extracting syntactic features...")
        syntactic = self.extract_syntactic_features(transcript)
        features.update({f"syn_{k}": v for k, v in syntactic.items()})
        
        # 3. Semantic Features
        logger.info("🧠 Extracting semantic features...")
        semantic = self.extract_semantic_features(transcript)
        features.update({f"sem_{k}": v for k, v in semantic.items()})
        
        # 4. Vietnamese-specific Features
        logger.info("🇻🇳 Extracting Vietnamese-specific features...")
        vietnamese = self.extract_vietnamese_specific_features(transcript)
        features.update({f"vi_{k}": v for k, v in vietnamese.items()})
        
        # 5. Task-specific Features
        if task_type:
            logger.info(f"📋 Extracting {task_type} task features...")
            task_features = self.analyze_task_specific_features(transcript, task_type)
            features.update(task_features)
        
        logger.info(f"✅ Extracted {len(features)} total linguistic features")
        return features


# Convenience function for direct use
def extract_linguistic_features(transcript: str, 
                                 task_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to extract all linguistic features
    
    Args:
        transcript: Text transcript
        task_type: Optional task type
    
    Returns:
        dict: All linguistic features
    """
    analyzer = VietnameseLinguisticAnalyzer()
    return analyzer.extract_all_features(transcript, task_type)

