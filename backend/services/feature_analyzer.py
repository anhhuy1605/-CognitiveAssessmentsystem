# -*- coding: utf-8 -*-
"""
Enhanced Feature Analyzer for Cognitive Assessment
==================================================
Comprehensive feature analysis with severity calculation and clinical interpretation

Based on:
- eGeMAPS acoustic features (88 features)
- Linguistic features for Vietnamese (42 features)
- Clinical ranges from comprehensive_results_clinical_ranges.py
- Research: Fraser et al. 2016, Luz et al. 2020, Snowdon (Nun Study)
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import existing clinical ranges
try:
    from services.comprehensive_results_clinical_ranges import (
        ACOUSTIC_CLINICAL_RANGES,
        LINGUISTIC_CLINICAL_RANGES,
        FEATURE_IMPORTANCE_WEIGHTS
    )
except ImportError:
    logger.warning("⚠️ Clinical ranges not available - using minimal defaults")
    ACOUSTIC_CLINICAL_RANGES = {}
    LINGUISTIC_CLINICAL_RANGES = {}
    FEATURE_IMPORTANCE_WEIGHTS = {}


def calculate_feature_severity(
    feature_value: float,
    feature_config: Dict[str, Any],
    user_gender: str = "male"
) -> Dict[str, Any]:
    """
    Calculate severity of abnormality for a feature
    
    Args:
        feature_value: The feature value to analyze
        feature_config: Feature configuration from clinical ranges
        user_gender: User gender for gender-specific ranges
        
    Returns:
        Dictionary with:
        - status: "normal", "borderline_low/high", "mild_low/high", "moderate_low/high", "severe_low/high"
        - severity: "normal", "borderline", "mild", "moderate", "severe"
        - deviation_pct: Percentage deviation from optimal
        - interpretation: Human-readable interpretation
    """
    
    # Get ranges based on gender
    if 'optimal' in feature_config:
        if isinstance(feature_config['optimal'], dict):
            # Gender-specific ranges
            if user_gender in feature_config['optimal']:
                optimal_range = feature_config['optimal'][user_gender]
            else:
                # Use first available gender or universal
                optimal_range = list(feature_config['optimal'].values())[0]
        else:
            optimal_range = feature_config['optimal']
    else:
        optimal_range = None
    
    if 'normal' in feature_config:
        if isinstance(feature_config['normal'], dict):
            if user_gender in feature_config['normal']:
                normal_range = feature_config['normal'][user_gender]
            else:
                normal_range = list(feature_config['normal'].values())[0]
        else:
            normal_range = feature_config['normal']
    else:
        normal_range = None
    
    # If no ranges defined, return unknown
    if optimal_range is None and normal_range is None:
        return {
            "status": "unknown",
            "severity": "unknown",
            "deviation_pct": 0,
            "interpretation": "Không có dữ liệu tham chiếu"
        }
    
    # Use optimal range if available, otherwise use normal range
    if optimal_range:
        if isinstance(optimal_range, tuple) and len(optimal_range) == 2:
            optimal_min, optimal_max = optimal_range
        else:
            optimal_min = optimal_max = None
    else:
        optimal_min = optimal_max = None
    
    if normal_range:
        if isinstance(normal_range, tuple) and len(normal_range) == 2:
            normal_min, normal_max = normal_range
        else:
            normal_min = normal_max = None
    else:
        normal_min = normal_max = None
    
    # Determine which range to use
    if optimal_min is not None and optimal_max is not None:
        range_min, range_max = optimal_min, optimal_max
        is_optimal = True
    elif normal_min is not None and normal_max is not None:
        range_min, range_max = normal_min, normal_max
        is_optimal = False
    else:
        return {
            "status": "unknown",
            "severity": "unknown",
            "deviation_pct": 0,
            "interpretation": "Không có dữ liệu tham chiếu"
        }
    
    # Check if within optimal/normal range
    if range_min <= feature_value <= range_max:
        interpretation = "Bình thường"
        if 'clinical_meaning' in feature_config:
            if isinstance(feature_config['clinical_meaning'], dict):
                interpretation = feature_config['clinical_meaning'].get('normal', interpretation)
            else:
                interpretation = feature_config['clinical_meaning']
        
        return {
            "status": "normal",
            "severity": "normal",
            "deviation_pct": 0,
            "interpretation": interpretation
        }
    
    # Calculate deviation
    if feature_value < range_min:
        deviation = range_min - feature_value
        deviation_pct = (deviation / range_min * 100) if range_min > 0 else 0
        
        # Check severity thresholds
        if 'severe' in feature_config:
            severe_range = feature_config['severe']
            if isinstance(severe_range, tuple) and len(severe_range) == 2:
                if feature_value <= severe_range[0]:
                    severity = "severe"
                    status = "severe_low"
                elif feature_value <= severe_range[1]:
                    severity = "moderate"
                    status = "moderate_low"
                else:
                    severity = "mild"
                    status = "mild_low"
            else:
                if deviation_pct > 50:
                    severity = "severe"
                    status = "severe_low"
                elif deviation_pct > 20:
                    severity = "moderate"
                    status = "moderate_low"
                else:
                    severity = "mild"
                    status = "mild_low"
        else:
            if deviation_pct > 50:
                severity = "severe"
                status = "severe_low"
            elif deviation_pct > 20:
                severity = "moderate"
                status = "moderate_low"
            else:
                severity = "mild"
                status = "mild_low"
        
        # Get interpretation
        interpretation_key = 'too_low' if 'interpretation' not in feature_config else None
        if 'clinical_meaning' in feature_config:
            if isinstance(feature_config['clinical_meaning'], dict):
                interpretation = feature_config['clinical_meaning'].get(severity, 
                    feature_config['clinical_meaning'].get('concerning', 'Giá trị thấp bất thường'))
            else:
                interpretation = feature_config['clinical_meaning']
        else:
            interpretation = f"Giá trị thấp ({deviation_pct:.1f}% dưới mức tối ưu)"
        
        return {
            "status": status,
            "severity": severity,
            "deviation_pct": deviation_pct,
            "interpretation": interpretation
        }
    
    else:  # feature_value > range_max
        deviation = feature_value - range_max
        deviation_pct = (deviation / range_max * 100) if range_max > 0 else 0
        
        # Check severity thresholds
        if 'severe' in feature_config:
            severe_range = feature_config['severe']
            if isinstance(severe_range, tuple) and len(severe_range) == 2:
                if feature_value >= severe_range[1]:
                    severity = "severe"
                    status = "severe_high"
                elif feature_value >= severe_range[0]:
                    severity = "moderate"
                    status = "moderate_high"
                else:
                    severity = "mild"
                    status = "mild_high"
            else:
                if deviation_pct > 50:
                    severity = "severe"
                    status = "severe_high"
                elif deviation_pct > 20:
                    severity = "moderate"
                    status = "moderate_high"
                else:
                    severity = "mild"
                    status = "mild_high"
        else:
            if deviation_pct > 50:
                severity = "severe"
                status = "severe_high"
            elif deviation_pct > 20:
                severity = "moderate"
                status = "moderate_high"
            else:
                severity = "mild"
                status = "mild_high"
        
        # Get interpretation
        if 'clinical_meaning' in feature_config:
            if isinstance(feature_config['clinical_meaning'], dict):
                interpretation = feature_config['clinical_meaning'].get(severity,
                    feature_config['clinical_meaning'].get('concerning', 'Giá trị cao bất thường'))
            else:
                interpretation = feature_config['clinical_meaning']
        else:
            interpretation = f"Giá trị cao ({deviation_pct:.1f}% trên mức tối ưu)"
        
        return {
            "status": status,
            "severity": severity,
            "deviation_pct": deviation_pct,
            "interpretation": interpretation
        }


class FeatureAnalyzer:
    """
    Comprehensive feature analyzer with severity calculation and clinical interpretation
    """
    
    def __init__(self):
        self.acoustic_ranges = ACOUSTIC_CLINICAL_RANGES
        self.linguistic_ranges = LINGUISTIC_CLINICAL_RANGES
        self.importance_weights = FEATURE_IMPORTANCE_WEIGHTS
    
    def analyze_all_features(
        self,
        acoustic_features: Dict[str, float],
        linguistic_features: Dict[str, float],
        user_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze all features and return comprehensive report
        
        Args:
            acoustic_features: Dictionary of acoustic feature values
            linguistic_features: Dictionary of linguistic feature values
            user_info: User information (gender, age, etc.)
            
        Returns:
            Comprehensive analysis dictionary
        """
        gender = user_info.get('gender', 'male')
        
        results = {
            "acoustic_analysis": self.analyze_acoustic_features(acoustic_features, gender),
            "linguistic_analysis": self.analyze_linguistic_features(linguistic_features),
            "summary": {}
        }
        
        # Generate summary
        results["summary"] = self.generate_summary(results)
        
        return results
    
    def analyze_acoustic_features(
        self,
        features: Dict[str, float],
        gender: str = "male"
    ) -> Dict[str, Any]:
        """
        Analyze acoustic features against normal ranges
        
        Args:
            features: Dictionary of feature_name -> feature_value
            gender: User gender for gender-specific ranges
            
        Returns:
            Analyzed features with severity and interpretation
        """
        analyzed = {
            "features": [],
            "abnormal_count": 0,
            "by_category": defaultdict(list),
            "by_severity": defaultdict(list)
        }
        
        for feature_key, feature_value in features.items():
            if not isinstance(feature_value, (int, float, np.number)):
                continue
            
            feature_value = float(feature_value)
            
            # Find feature config
            feature_config = self.find_feature_config(feature_key, self.acoustic_ranges)
            if not feature_config:
                # Try normalized key
                normalized_key = self.normalize_feature_key(feature_key)
                feature_config = self.find_feature_config(normalized_key, self.acoustic_ranges)
            
            if not feature_config:
                # Skip if no config found
                logger.debug(f"No config found for acoustic feature: {feature_key}")
                continue
            
            # Calculate severity
            severity_info = calculate_feature_severity(feature_value, feature_config, gender)
            
            # Get feature name
            feature_name_vi = feature_config.get('name_vi', feature_key)
            category = feature_config.get('category', 'Khác')
            unit = feature_config.get('unit', '')
            
            # Build comprehensive feature analysis
            feature_analysis = {
                "key": feature_key,
                "name_vi": feature_name_vi,
                "category": category,
                "value": feature_value,
                "unit": unit,
                "status": severity_info["status"],
                "severity": severity_info["severity"],
                "deviation_pct": severity_info["deviation_pct"],
                "interpretation": severity_info["interpretation"],
                "clinical_significance": feature_config.get('mci_relevance', ''),
                "citation": feature_config.get('citation', ''),
                "importance_weight": self.importance_weights.get(feature_key, 1.0),
                "normal_range": self.format_ranges(feature_config, gender)
            }
            
            analyzed["features"].append(feature_analysis)
            
            # Count abnormalities
            if severity_info["severity"] not in ["normal", "borderline"]:
                analyzed["abnormal_count"] += 1
            
            # Group by category
            analyzed["by_category"][category].append(feature_analysis)
            
            # Group by severity
            analyzed["by_severity"][severity_info["severity"]].append(feature_analysis)
        
        return analyzed
    
    def analyze_linguistic_features(
        self,
        features: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Analyze linguistic features (similar to acoustic)
        """
        analyzed = {
            "features": [],
            "abnormal_count": 0,
            "by_category": defaultdict(list),
            "by_severity": defaultdict(list)
        }
        
        for feature_key, feature_value in features.items():
            if not isinstance(feature_value, (int, float, np.number)):
                continue
            
            feature_value = float(feature_value)
            
            # Find feature config
            feature_config = self.find_feature_config(feature_key, self.linguistic_ranges)
            if not feature_config:
                normalized_key = self.normalize_feature_key(feature_key)
                feature_config = self.find_feature_config(normalized_key, self.linguistic_ranges)
            
            if not feature_config:
                continue
            
            # Calculate severity (linguistic features typically not gender-specific)
            severity_info = calculate_feature_severity(feature_value, feature_config, "universal")
            
            feature_name_vi = feature_config.get('name_vi', feature_key)
            category = feature_config.get('category', 'Khác')
            unit = feature_config.get('unit', '')
            
            feature_analysis = {
                "key": feature_key,
                "name_vi": feature_name_vi,
                "category": category,
                "value": feature_value,
                "unit": unit,
                "status": severity_info["status"],
                "severity": severity_info["severity"],
                "deviation_pct": severity_info["deviation_pct"],
                "interpretation": severity_info["interpretation"],
                "clinical_significance": feature_config.get('mci_relevance', ''),
                "citation": feature_config.get('citation', ''),
                "importance_weight": self.importance_weights.get(feature_key, 1.0),
                "normal_range": self.format_ranges(feature_config, "universal")
            }
            
            analyzed["features"].append(feature_analysis)
            
            if severity_info["severity"] not in ["normal", "borderline"]:
                analyzed["abnormal_count"] += 1
            
            analyzed["by_category"][category].append(feature_analysis)
            analyzed["by_severity"][severity_info["severity"]].append(feature_analysis)
        
        return analyzed
    
    def generate_summary(self, full_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate executive summary of findings
        """
        acoustic = full_analysis["acoustic_analysis"]
        linguistic = full_analysis["linguistic_analysis"]
        
        total_features = len(acoustic["features"]) + len(linguistic["features"])
        total_abnormal = acoustic["abnormal_count"] + linguistic["abnormal_count"]
        
        # Categorize by severity
        severe_features = []
        moderate_features = []
        mild_features = []
        
        for feature in acoustic["features"] + linguistic["features"]:
            if feature["severity"] == "severe":
                severe_features.append(feature)
            elif feature["severity"] == "moderate":
                moderate_features.append(feature)
            elif feature["severity"] == "mild":
                mild_features.append(feature)
        
        # Sort by importance weight
        severe_features.sort(key=lambda x: x.get("importance_weight", 0), reverse=True)
        moderate_features.sort(key=lambda x: x.get("importance_weight", 0), reverse=True)
        mild_features.sort(key=lambda x: x.get("importance_weight", 0), reverse=True)
        
        return {
            "total_features_analyzed": total_features,
            "total_acoustic": len(acoustic["features"]),
            "total_linguistic": len(linguistic["features"]),
            "abnormality_count": total_abnormal,
            "abnormality_percentage": (total_abnormal / total_features * 100) if total_features > 0 else 0,
            "severity_breakdown": {
                "severe": len(severe_features),
                "moderate": len(moderate_features),
                "mild": len(mild_features)
            },
            "top_concerns": severe_features[:5],  # Top 5 severe issues
            "categories_affected": self.identify_affected_categories(full_analysis)
        }
    
    def find_feature_config(self, feature_key: str, ranges_dict: Dict) -> Optional[Dict]:
        """
        Recursively search for feature config in nested dict
        """
        # Direct match
        if feature_key in ranges_dict:
            return ranges_dict[feature_key]
        
        # Search in nested structures
        for key, value in ranges_dict.items():
            if isinstance(value, dict):
                if feature_key in value:
                    return value[feature_key]
                # Recurse
                result = self.find_feature_config(feature_key, value)
                if result:
                    return result
        
        return None
    
    def normalize_feature_key(self, feature_key: str) -> str:
        """
        Normalize feature key to match config keys
        Examples:
        - "egemaps_jitterLocal_sma3nz_amean" -> "jitter"
        - "pause_pause_rate" -> "pause_rate"
        - "lex_ttr" -> "ttr"
        """
        key_lower = feature_key.lower()
        
        # Common mappings
        if 'jitter' in key_lower:
            return 'jitter'
        elif 'shimmer' in key_lower:
            return 'shimmer'
        elif 'hnr' in key_lower or 'harmonic' in key_lower:
            return 'hnr'
        elif 'pause' in key_lower and 'rate' in key_lower:
            return 'pause_rate'
        elif 'f0' in key_lower and ('mean' in key_lower or 'amean' in key_lower):
            return 'f0_mean'
        elif 'f0' in key_lower and ('cv' in key_lower or 'variability' in key_lower):
            return 'f0_cv'
        elif 'ttr' in key_lower or 'type_token' in key_lower:
            return 'ttr'
        elif 'mattr' in key_lower:
            return 'mattr'
        elif 'mlu' in key_lower:
            return 'mlu'
        elif 'idea' in key_lower and 'density' in key_lower:
            return 'idea_density'
        elif 'semantic' in key_lower and 'coherence' in key_lower:
            return 'semantic_coherence'
        elif 'pronoun' in key_lower:
            return 'pronoun_ratio'
        elif 'rate' in key_lower and ('word' in key_lower or 'speech' in key_lower):
            return 'speaking_rate'
        elif 'tone' in key_lower and 'flatten' in key_lower:
            return 'tone_flattening'
        
        return feature_key
    
    def format_ranges(self, feature_config: Dict, gender: str) -> Dict[str, Any]:
        """
        Format ranges for display
        """
        result = {}
        
        if 'optimal' in feature_config:
            optimal = feature_config['optimal']
            if isinstance(optimal, dict):
                if gender in optimal:
                    opt_range = optimal[gender]
                    if isinstance(opt_range, tuple) and len(opt_range) == 2:
                        result['optimal_min'] = opt_range[0]
                        result['optimal_max'] = opt_range[1]
            elif isinstance(optimal, tuple) and len(optimal) == 2:
                result['optimal_min'] = optimal[0]
                result['optimal_max'] = optimal[1]
        
        if 'normal' in feature_config:
            normal = feature_config['normal']
            if isinstance(normal, dict):
                if gender in normal:
                    norm_range = normal[gender]
                    if isinstance(norm_range, tuple) and len(norm_range) == 2:
                        result['normal_min'] = norm_range[0]
                        result['normal_max'] = norm_range[1]
            elif isinstance(normal, tuple) and len(normal) == 2:
                result['normal_min'] = normal[0]
                result['normal_max'] = normal[1]
        
        # Format display string
        if 'optimal_min' in result and 'optimal_max' in result:
            if 'normal_min' in result and 'normal_max' in result:
                result['display'] = f"{result['optimal_min']}-{result['optimal_max']} (Tối ưu), {result['normal_min']}-{result['normal_max']} (Chấp nhận được)"
            else:
                result['display'] = f"{result['optimal_min']}-{result['optimal_max']} (Tối ưu)"
        elif 'normal_min' in result and 'normal_max' in result:
            result['display'] = f"{result['normal_min']}-{result['normal_max']} (Bình thường)"
        else:
            result['display'] = "Không có dữ liệu"
        
        return result
    
    def identify_affected_categories(self, full_analysis: Dict[str, Any]) -> List[str]:
        """
        Identify which categories have abnormal features
        """
        affected = set()
        
        for feature in full_analysis["acoustic_analysis"]["features"] + full_analysis["linguistic_analysis"]["features"]:
            if feature["severity"] not in ["normal", "borderline"]:
                affected.add(feature["category"])
        
        return sorted(list(affected))


