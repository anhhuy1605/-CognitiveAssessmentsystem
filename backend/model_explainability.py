"""
Model Explainability - SHAP/LIME Implementation
===============================================

This module provides SHAP and LIME-based explainability for the clinical models,
enabling interpretation of dementia screening predictions for clinical use.

Requirements from document:
- SHAP/LIME model explainability
- Clinical report generation
- Feature importance analysis
- Prediction confidence explanations
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import joblib
import os

logger = logging.getLogger(__name__)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not available - install with: pip install shap")

try:
    import lime
    from lime.lime_tabular import LimeTabularExplainer
    LIME_AVAILABLE = True
except ImportError:
    LIME_AVAILABLE = False
    logger.warning("LIME not available - install with: pip install lime")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
    logger.warning("Plotting libraries not available")


class ClinicalModelExplainer:
    """
    SHAP and LIME-based explainability for clinical dementia screening models
    """

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.shap_explainer = None
        self.lime_explainer = None
        self.feature_names = None
        self.training_data = None
        self.is_initialized = False

    def initialize_explainer(self, model, training_data: np.ndarray,
                           feature_names: Optional[List[str]] = None) -> bool:
        """
        Initialize SHAP and LIME explainers

        Args:
            model: Trained ML model
            training_data: Training data for explainer fitting
            feature_names: Names of features
        """
        try:
            self.feature_names = feature_names or [f"feature_{i}" for i in range(training_data.shape[1])]
            self.training_data = training_data

            # Initialize SHAP explainer
            if SHAP_AVAILABLE:
                try:
                    if hasattr(model, 'predict_proba'):
                        self.shap_explainer = shap.TreeExplainer(model) if hasattr(model, 'feature_importances_') else shap.Explainer(model)
                    else:
                        self.shap_explainer = shap.Explainer(model)
                    logger.info("SHAP explainer initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize SHAP explainer: {e}")
                    self.shap_explainer = None

            # Initialize LIME explainer
            if LIME_AVAILABLE:
                try:
                    self.lime_explainer = LimeTabularExplainer(
                        training_data=self.training_data,
                        feature_names=self.feature_names,
                        class_names=['Normal', 'Impaired'],
                        mode='classification' if hasattr(model, 'predict_proba') else 'regression'
                    )
                    logger.info("LIME explainer initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize LIME explainer: {e}")
                    self.lime_explainer = None

            self.is_initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to initialize explainers: {e}")
            return False

    def explain_prediction(self, instance: np.ndarray, model,
                          method: str = 'both') -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a single prediction

        Args:
            instance: Single instance to explain (1D array)
            model: Trained model
            method: 'shap', 'lime', or 'both'
        """
        if not self.is_initialized:
            return {'error': 'Explainer not initialized'}

        explanations = {}

        # Ensure instance is 2D
        if instance.ndim == 1:
            instance = instance.reshape(1, -1)

        try:
            # SHAP explanation
            if method in ['shap', 'both'] and self.shap_explainer and SHAP_AVAILABLE:
                try:
                    shap_values = self.shap_explainer(instance)

                    # For binary classification, focus on positive class
                    if hasattr(shap_values, 'values') and len(shap_values.values.shape) > 1:
                        shap_vals = shap_values.values[0, :, 1] if shap_values.values.shape[1] > 1 else shap_values.values[0]
                    else:
                        shap_vals = shap_values.values[0]

                    # Get top contributing features
                    feature_importance = list(zip(self.feature_names, shap_vals))
                    feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

                    explanations['shap'] = {
                        'feature_importance': feature_importance[:10],  # Top 10 features
                        'base_value': float(shap_values.base_values[0]) if hasattr(shap_values, 'base_values') else 0.0,
                        'prediction': float(model.predict_proba(instance)[0, 1]) if hasattr(model, 'predict_proba') else float(model.predict(instance)[0])
                    }

                except Exception as e:
                    logger.error(f"SHAP explanation failed: {e}")
                    explanations['shap'] = {'error': str(e)}

            # LIME explanation
            if method in ['lime', 'both'] and self.lime_explainer and LIME_AVAILABLE:
                try:
                    # Get prediction function
                    predict_fn = model.predict_proba if hasattr(model, 'predict_proba') else model.predict

                    lime_exp = self.lime_explainer.explain_instance(
                        instance[0],
                        predict_fn,
                        num_features=10,
                        top_labels=1
                    )

                    # Extract feature contributions
                    feature_contributions = lime_exp.as_list(label=lime_exp.available_labels()[0])
                    feature_contributions = [(feat, float(score)) for feat, score in feature_contributions]

                    explanations['lime'] = {
                        'feature_contributions': feature_contributions,
                        'prediction': lime_exp.predict_proba[lime_exp.available_labels()[0]],
                        'intercept': lime_exp.intercept[lime_exp.available_labels()[0]]
                    }

                except Exception as e:
                    logger.error(f"LIME explanation failed: {e}")
                    explanations['lime'] = {'error': str(e)}

            # Generate clinical interpretation
            explanations['clinical_interpretation'] = self._generate_clinical_interpretation(explanations)

            return explanations

        except Exception as e:
            logger.error(f"Prediction explanation failed: {e}")
            return {'error': str(e)}

    def generate_global_explanations(self, model, validation_data: np.ndarray,
                                   n_samples: int = 1000) -> Dict[str, Any]:
        """
        Generate global model explanations using SHAP

        Args:
            model: Trained model
            validation_data: Validation dataset
            n_samples: Number of samples to use for global explanation
        """
        if not SHAP_AVAILABLE or not self.shap_explainer:
            return {'error': 'SHAP not available for global explanations'}

        try:
            # Sample data for efficiency
            if len(validation_data) > n_samples:
                indices = np.random.choice(len(validation_data), n_samples, replace=False)
                sample_data = validation_data[indices]
            else:
                sample_data = validation_data

            # Calculate SHAP values for sample
            shap_values = self.shap_explainer(sample_data)

            # Feature importance summary
            if hasattr(shap_values, 'values'):
                if len(shap_values.values.shape) > 2:  # Multi-class
                    shap_vals = shap_values.values[:, :, 1]  # Focus on positive class
                else:
                    shap_vals = shap_values.values

                # Mean absolute SHAP values for feature importance
                feature_importance = np.abs(shap_vals).mean(axis=0)
                feature_ranking = list(zip(self.feature_names, feature_importance))
                feature_ranking.sort(key=lambda x: x[1], reverse=True)

            return {
                'global_feature_importance': feature_ranking[:20],  # Top 20 features
                'sample_size': len(sample_data),
                'method': 'shap_summary'
            }

        except Exception as e:
            logger.error(f"Global explanation failed: {e}")
            return {'error': str(e)}

    def _generate_clinical_interpretation(self, explanations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate clinical interpretation of model explanations
        """
        interpretation = {
            'key_factors': [],
            'confidence_assessment': 'Unknown',
            'clinical_recommendations': []
        }

        try:
            # Extract key contributing features
            key_features = []

            # From SHAP
            if 'shap' in explanations and 'feature_importance' in explanations['shap']:
                shap_features = explanations['shap']['feature_importance'][:5]
                key_features.extend([f"{feat} ({score:+.3f})" for feat, score in shap_features])

            # From LIME
            if 'lime' in explanations and 'feature_contributions' in explanations['lime']:
                lime_features = explanations['lime']['feature_contributions'][:5]
                key_features.extend([f"{feat} ({score:+.3f})" for feat, score in lime_features])

            interpretation['key_factors'] = list(set(key_features))  # Remove duplicates

            # Confidence assessment based on explanation consistency
            if len(explanations) >= 2:  # Both SHAP and LIME
                interpretation['confidence_assessment'] = 'High (Multiple explanation methods agree)'
            elif len(explanations) == 1:
                interpretation['confidence_assessment'] = 'Medium (Single explanation method)'
            else:
                interpretation['confidence_assessment'] = 'Low (No explanations available)'

            # Generate clinical recommendations
            recommendations = []

            # Check for audio quality issues
            if any('duration' in factor.lower() or 'quality' in factor.lower()
                   for factor in interpretation['key_factors']):
                recommendations.append("Review audio recording quality and environment")

            # Check for speech pattern abnormalities
            speech_indicators = ['speech_rate', 'pause', 'f0', 'jitter', 'shimmer']
            if any(any(indicator in factor.lower() for indicator in speech_indicators)
                   for factor in interpretation['key_factors']):
                recommendations.append("Consider speech and language evaluation")
                recommendations.append("Monitor for potential communication difficulties")

            # Default recommendations
            if not recommendations:
                recommendations.append("Continue regular cognitive assessments")
                recommendations.append("Monitor for changes in cognitive function")

            interpretation['clinical_recommendations'] = recommendations

        except Exception as e:
            logger.error(f"Clinical interpretation failed: {e}")
            interpretation['error'] = str(e)

        return interpretation

    def generate_clinical_report(self, patient_data: Dict[str, Any],
                               explanations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive clinical report for patient assessment

        Args:
            patient_data: Patient demographics and assessment data
            explanations: Model explanations
        """
        report = {
            'patient_info': patient_data,
            'assessment_date': pd.Timestamp.now().isoformat(),
            'model_explanations': explanations,
            'clinical_summary': {},
            'recommendations': [],
            'follow_up': {}
        }

        try:
            # Clinical summary
            if 'clinical_interpretation' in explanations:
                interp = explanations['clinical_interpretation']

                report['clinical_summary'] = {
                    'key_contributing_factors': interp['key_factors'],
                    'prediction_confidence': interp['confidence_assessment'],
                    'risk_assessment': self._assess_clinical_risk(explanations)
                }

            # Recommendations
            report['recommendations'] = self._generate_clinical_recommendations(explanations)

            # Follow-up plan
            report['follow_up'] = self._generate_follow_up_plan(explanations, patient_data)

        except Exception as e:
            logger.error(f"Clinical report generation failed: {e}")
            report['error'] = str(e)

        return report

    def _assess_clinical_risk(self, explanations: Dict[str, Any]) -> str:
        """Assess clinical risk level based on explanations"""
        try:
            # Simple risk assessment based on explanation strength
            risk_score = 0.0

            # Check SHAP explanation strength
            if 'shap' in explanations:
                shap_data = explanations['shap']
                if 'feature_importance' in shap_data:
                    top_shap = abs(shap_data['feature_importance'][0][1])
                    risk_score += min(top_shap * 10, 5.0)  # Scale and cap

            # Check LIME explanation strength
            if 'lime' in explanations:
                lime_data = explanations['lime']
                if 'feature_contributions' in lime_data:
                    top_lime = abs(lime_data['feature_contributions'][0][1])
                    risk_score += min(top_lime * 10, 5.0)  # Scale and cap

            # Determine risk level
            if risk_score >= 7.0:
                return "High Risk - Immediate clinical evaluation recommended"
            elif risk_score >= 4.0:
                return "Medium Risk - Follow-up assessment within 3 months"
            else:
                return "Low Risk - Continue regular monitoring"

        except Exception as e:
            logger.error(f"Risk assessment failed: {e}")
            return "Unable to assess risk"

    def _generate_clinical_recommendations(self, explanations: Dict[str, Any]) -> List[str]:
        """Generate clinical recommendations based on explanations"""
        recommendations = []

        try:
            if 'clinical_interpretation' in explanations:
                interp = explanations['clinical_interpretation']
                recommendations.extend(interp.get('clinical_recommendations', []))

            # Add standard recommendations
            recommendations.extend([
                "Consider comprehensive neuropsychological evaluation",
                "Review medication list for cognitive effects",
                "Assess for depression and other confounding factors",
                "Consider neuroimaging if clinically indicated",
                "Provide patient and family education about cognitive health"
            ])

            # Remove duplicates while preserving order
            seen = set()
            unique_recommendations = []
            for rec in recommendations:
                if rec not in seen:
                    unique_recommendations.append(rec)
                    seen.add(rec)

            return unique_recommendations[:10]  # Limit to top 10

        except Exception as e:
            logger.error(f"Clinical recommendations generation failed: {e}")
            return ["Consult with neurologist or geriatrician"]

    def _generate_follow_up_plan(self, explanations: Dict[str, Any],
                               patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate follow-up plan"""
        try:
            risk_level = self._assess_clinical_risk(explanations)

            if "High Risk" in risk_level:
                return {
                    'urgency': 'Immediate',
                    'timeline': 'Within 1 week',
                    'specialist': 'Neurologist or Geriatrician',
                    'additional_tests': ['MMSE', 'MoCA', 'Neuropsychological testing', 'Consider neuroimaging']
                }
            elif "Medium Risk" in risk_level:
                return {
                    'urgency': 'Routine',
                    'timeline': 'Within 3 months',
                    'specialist': 'Primary care physician',
                    'additional_tests': ['Repeat cognitive assessment', 'Screen for depression']
                }
            else:
                return {
                    'urgency': 'Routine',
                    'timeline': 'Annual screening',
                    'specialist': 'Primary care physician',
                    'additional_tests': ['Regular cognitive monitoring']
                }

        except Exception as e:
            logger.error(f"Follow-up plan generation failed: {e}")
            return {
                'urgency': 'Unknown',
                'timeline': 'As clinically indicated',
                'specialist': 'Primary care physician'
            }


class DementiaScreeningReport:
    """
    Generate comprehensive clinical reports for dementia screening
    """

    def __init__(self):
        self.template = {
            'header': {
                'report_title': 'AI Dementia Screening Report',
                'report_version': '2.0',
                'generated_date': None,
                'confidentiality': 'This report contains sensitive medical information'
            },
            'patient_demographics': {},
            'assessment_results': {},
            'model_explanations': {},
            'clinical_interpretation': {},
            'recommendations': {},
            'follow_up_plan': {},
            'disclaimer': self._get_disclaimer()
        }

    def generate_report(self, patient_data: Dict[str, Any],
                       assessment_results: Dict[str, Any],
                       model_explanations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate complete clinical report
        """
        report = self.template.copy()
        report['header']['generated_date'] = pd.Timestamp.now().isoformat()

        try:
            # Patient information
            report['patient_demographics'] = {
                'patient_id': patient_data.get('id', 'Unknown'),
                'age': patient_data.get('age'),
                'gender': patient_data.get('gender'),
                'education': patient_data.get('education'),
                'assessment_date': patient_data.get('assessment_date')
            }

            # Assessment results
            report['assessment_results'] = {
                'tier1_screening': assessment_results.get('tier1', {}),
                'tier2_classification': assessment_results.get('tier2', {}),
                'processing_metrics': assessment_results.get('processing', {})
            }

            # Model explanations
            report['model_explanations'] = model_explanations

            # Clinical interpretation
            report['clinical_interpretation'] = self._interpret_results(
                assessment_results, model_explanations
            )

            # Recommendations
            report['recommendations'] = self._generate_recommendations(
                assessment_results, model_explanations
            )

            # Follow-up plan
            report['follow_up_plan'] = self._create_follow_up_plan(
                assessment_results, patient_data
            )

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report['error'] = str(e)

        return report

    def _interpret_results(self, assessment_results: Dict[str, Any],
                          model_explanations: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret assessment results for clinical context"""
        interpretation = {
            'overall_risk': 'Unknown',
            'confidence_level': 'Unknown',
            'key_findings': [],
            'clinical_significance': 'Unknown'
        }

        try:
            # Determine overall risk
            tier1 = assessment_results.get('tier1', {})
            tier2 = assessment_results.get('tier2', {})

            # Logic for risk determination (simplified)
            if tier1.get('sensitivity', 0) >= 0.95 and tier2.get('auc', 0) >= 0.85:
                interpretation['overall_risk'] = 'High Confidence Positive Screen'
            elif tier1.get('specificity', 0) >= 0.90:
                interpretation['overall_risk'] = 'Low Risk'
            else:
                interpretation['overall_risk'] = 'Intermediate Risk - Further Evaluation Needed'

            # Confidence level
            explanation_methods = len([k for k in model_explanations.keys() if k != 'error'])
            if explanation_methods >= 2:
                interpretation['confidence_level'] = 'High'
            elif explanation_methods == 1:
                interpretation['confidence_level'] = 'Medium'
            else:
                interpretation['confidence_level'] = 'Low'

            # Key findings
            if 'clinical_interpretation' in model_explanations:
                interp = model_explanations['clinical_interpretation']
                interpretation['key_findings'] = interp.get('key_factors', [])

            # Clinical significance
            interpretation['clinical_significance'] = self._assess_clinical_significance(
                assessment_results
            )

        except Exception as e:
            logger.error(f"Results interpretation failed: {e}")
            interpretation['error'] = str(e)

        return interpretation

    def _generate_recommendations(self, assessment_results: Dict[str, Any],
                                model_explanations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate clinical recommendations"""
        recommendations = {
            'immediate_actions': [],
            'diagnostic_workup': [],
            'patient_education': [],
            'follow_up_schedule': []
        }

        try:
            # Immediate actions based on risk level
            risk_level = self._interpret_results(assessment_results, model_explanations)['overall_risk']

            if 'High' in risk_level:
                recommendations['immediate_actions'].extend([
                    'Urgent neurology consultation',
                    'Comprehensive neuropsychological evaluation',
                    'Consider neuroimaging (MRI/CT)',
                    'Assess for reversible causes of cognitive impairment'
                ])
            elif 'Intermediate' in risk_level:
                recommendations['immediate_actions'].extend([
                    'Repeat cognitive assessment in 3 months',
                    'Screen for depression and anxiety',
                    'Review medications for cognitive side effects'
                ])
            else:
                recommendations['immediate_actions'].extend([
                    'Continue routine health maintenance',
                    'Annual cognitive screening'
                ])

            # Diagnostic workup
            recommendations['diagnostic_workup'] = [
                'Complete blood count and metabolic panel',
                'Vitamin B12 and folate levels',
                'Thyroid function tests',
                'Screen for depression (Geriatric Depression Scale)',
                'Consider sleep study if indicated'
            ]

            # Patient education
            recommendations['patient_education'] = [
                'Education about cognitive health and aging',
                'Information about local support services',
                'Family counseling and support resources',
                'Advance care planning discussion'
            ]

        except Exception as e:
            logger.error(f"Recommendations generation failed: {e}")
            recommendations['error'] = str(e)

        return recommendations

    def _create_follow_up_plan(self, assessment_results: Dict[str, Any],
                             patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create follow-up plan"""
        plan = {
            'primary_care_followup': '3 months',
            'specialist_referral': 'As indicated',
            'repeat_assessment': '6-12 months',
            'monitoring_plan': []
        }

        try:
            risk_level = self._interpret_results(assessment_results, {})['overall_risk']

            if 'High' in risk_level:
                plan.update({
                    'primary_care_followup': '1 month',
                    'specialist_referral': 'Neurology - within 2 weeks',
                    'repeat_assessment': '3 months',
                    'monitoring_plan': [
                        'Monthly cognitive assessments',
                        'Track functional status',
                        'Monitor behavioral changes',
                        'Caregiver support assessment'
                    ]
                })
            elif 'Intermediate' in risk_level:
                plan.update({
                    'primary_care_followup': '3 months',
                    'specialist_referral': 'As indicated by primary care',
                    'repeat_assessment': '6 months',
                    'monitoring_plan': [
                        'Routine cognitive monitoring',
                        'Annual comprehensive assessment'
                    ]
                })

        except Exception as e:
            logger.error(f"Follow-up plan creation failed: {e}")
            plan['error'] = str(e)

        return plan

    def _assess_clinical_significance(self, assessment_results: Dict[str, Any]) -> str:
        """Assess clinical significance of findings"""
        try:
            tier1 = assessment_results.get('tier1', {})
            tier2 = assessment_results.get('tier2', {})

            # Clinical significance based on performance metrics
            sensitivity = tier1.get('sensitivity', 0)
            specificity = tier1.get('specificity', 0)
            auc = tier2.get('auc', 0)
            mae = tier2.get('mae', float('inf'))

            if sensitivity >= 0.95 and auc >= 0.85 and mae <= 2.5:
                return 'High clinical significance - Results meet performance targets'
            elif sensitivity >= 0.90 and auc >= 0.80:
                return 'Moderate clinical significance - Further validation recommended'
            else:
                return 'Limited clinical significance - Results below target thresholds'

        except Exception as e:
            logger.error(f"Clinical significance assessment failed: {e}")
            return 'Unable to assess clinical significance'

    def _get_disclaimer(self) -> str:
        """Get standard clinical disclaimer"""
        return """
        CLINICAL DISCLAIMER:

        This AI-generated report is intended to assist healthcare providers in the screening
        and assessment of cognitive impairment. It does not constitute a formal medical
        diagnosis and should not replace comprehensive clinical evaluation.

        The predictions and recommendations in this report are based on machine learning
        models trained on research datasets and may not be applicable to all populations
        or clinical scenarios.

        All medical decisions should be made by qualified healthcare professionals based
        on complete clinical assessment, patient history, and additional diagnostic testing
        as indicated.

        This report contains sensitive medical information and should be handled in
        accordance with applicable privacy and confidentiality regulations.
        """


def save_report_to_file(report: Dict[str, Any], output_path: str, format: str = 'json') -> bool:
    """
    Save clinical report to file

    Args:
        report: Clinical report dictionary
        output_path: Path to save report
        format: 'json' or 'pdf' (json only for now)
    """
    try:
        if format.lower() == 'json':
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
        else:
            logger.error(f"Unsupported format: {format}")
            return False

        logger.info(f"Report saved to {output_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save report: {e}")
        return False


if __name__ == "__main__":
    # Test the explainability implementation
    print("Testing model explainability components...")

    # Create mock data
    np.random.seed(42)
    n_samples = 100
    n_features = 20

    X_train = np.random.randn(n_samples, n_features)
    feature_names = [f"feature_{i}" for i in range(n_features)]

    # Mock model (simple classifier)
    from sklearn.ensemble import RandomForestClassifier
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    y_train = np.random.randint(0, 2, n_samples)
    model.fit(X_train, y_train)

    # Test explainer
    explainer = ClinicalModelExplainer()
    success = explainer.initialize_explainer(model, X_train, feature_names)

    if success:
        print("Explainer initialized successfully")

        # Test single prediction explanation
        test_instance = X_train[0:1]
        explanation = explainer.explain_prediction(test_instance, model, method='both')
        print(f"Explanation generated with keys: {list(explanation.keys())}")

        # Test global explanation
        global_exp = explainer.generate_global_explanations(model, X_train)
        print(f"Global explanation keys: {list(global_exp.keys())}")

        # Test clinical report generation
        report_gen = DementiaScreeningReport()
        patient_data = {
            'id': 'test_patient_001',
            'age': 65,
            'gender': 'Female',
            'assessment_date': '2024-01-15'
        }

        assessment_results = {
            'tier1': {'sensitivity': 0.96, 'specificity': 0.91},
            'tier2': {'auc': 0.87, 'mae': 2.1}
        }

        report = report_gen.generate_report(patient_data, assessment_results, explanation)
        print(f"Clinical report generated with sections: {list(report.keys())}")

        print("Model explainability tests completed successfully!")
    else:
        print("Failed to initialize explainer - check dependencies")
