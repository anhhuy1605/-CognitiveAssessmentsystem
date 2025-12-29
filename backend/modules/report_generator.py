# -*- coding: utf-8 -*-
"""
SHAP Report Generator
=====================

Generate comprehensive PDF/HTML reports with SHAP explanations.

Author: Cognitive Assessment System
Version: 1.0
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import io
import base64

logger = logging.getLogger(__name__)

# Try to import report generation libraries
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available. PDF generation will be limited.")


class SHAPReportGenerator:
    """
    Generate comprehensive PDF/HTML reports
    
    Report structure:
    1. Cover page: Summary, MMSE score, risk level
    2. Executive summary: 1-page plain language explanation
    3. Detailed analysis:
       - Feature contributions (waterfall plot)
       - Domain scores (radar chart)
       - Comparison to baseline
       - Historical trend (if available)
    4. Recommendations: Actionable steps
    5. Appendix: Technical details, feature values
    
    Support both Vietnamese and English
    """
    
    def __init__(self, language: str = 'vi'):
        """
        Initialize report generator
        
        Args:
            language: 'vi' for Vietnamese, 'en' for English
        """
        self.language = language
        self._setup_fonts()
    
    def _setup_fonts(self):
        """Setup fonts for Vietnamese support"""
        if REPORTLAB_AVAILABLE:
            try:
                # Try to register Vietnamese fonts (if available)
                # Default to built-in fonts
                pass
            except Exception as e:
                logger.warning(f"Could not setup custom fonts: {e}")
    
    def generate_pdf_report(self,
                           shap_result: Dict[str, Any],
                           explanations: Dict[str, Any],
                           visualizations: Dict[str, str],
                           output_path: Optional[str] = None) -> bytes:
        """
        Generate professional PDF report using reportlab
        
        Requirements:
        - Include all visualizations as high-res images
        - Use clear Vietnamese fonts (Arial Unicode MS, Segoe UI)
        - Color-coded sections
        - QR code linking to online dashboard (optional)
        - Timestamp and version info
        
        Args:
            shap_result: SHAP computation results
            explanations: Human-readable explanations
            visualizations: Dict of base64-encoded images
            output_path: Optional file path to save PDF
        
        Returns:
            PDF bytes
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot generate PDF.")
            return b""
        
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            # Container for PDF elements
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            # 1. Cover Page
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(
                'Cognitive Assessment Report' if self.language == 'en' else 'Báo Cáo Đánh Giá Nhận Thức',
                title_style
            ))
            story.append(Spacer(1, 0.5*inch))
            
            # Summary info
            mmse_score = explanations.get('mmse_score', 0)
            risk_level = explanations.get('risk_level', 'low')
            
            summary_text = f"""
            <b>MMSE Score:</b> {mmse_score}/30<br/>
            <b>Risk Level:</b> {risk_level.upper()}<br/>
            <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br/>
            """
            story.append(Paragraph(summary_text, styles['Normal']))
            story.append(PageBreak())
            
            # 2. Executive Summary
            story.append(Paragraph(
                'Executive Summary' if self.language == 'en' else 'Tóm Tắt Điều Hành',
                styles['Heading1']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            summary = explanations.get('summary', '')
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 0.3*inch))
            
            # Risk explanation
            risk_explanation = explanations.get('risk_explanation', '')
            story.append(Paragraph(
                '<b>Risk Assessment:</b><br/>' + risk_explanation,
                styles['Normal']
            ))
            story.append(PageBreak())
            
            # 3. Main Contributing Factors
            story.append(Paragraph(
                'Main Contributing Factors' if self.language == 'en' else 'Các Yếu Tố Ảnh Hưởng Chính',
                styles['Heading1']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Positive factors
            positive_factors = explanations.get('positive_factors', [])
            if positive_factors:
                story.append(Paragraph(
                    '<b>Strengths:</b>' if self.language == 'en' else '<b>Điểm Mạnh:</b>',
                    styles['Heading2']
                ))
                for factor in positive_factors[:5]:
                    factor_text = f"""
                    • <b>{factor.get('feature_display_name', '')}</b>: {factor.get('interpretation', '')}
                    """
                    story.append(Paragraph(factor_text, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            # Negative factors
            negative_factors = explanations.get('negative_factors', [])
            if negative_factors:
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(
                    '<b>Areas of Concern:</b>' if self.language == 'en' else '<b>Vấn Đề Cần Chú Ý:</b>',
                    styles['Heading2']
                ))
                for factor in negative_factors[:5]:
                    factor_text = f"""
                    • <b>{factor.get('feature_display_name', '')}</b>: {factor.get('interpretation', '')}
                    """
                    story.append(Paragraph(factor_text, styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            story.append(PageBreak())
            
            # 4. Visualizations
            story.append(Paragraph(
                'Detailed Analysis' if self.language == 'en' else 'Phân Tích Chi Tiết',
                styles['Heading1']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            # Waterfall plot
            if 'waterfall' in visualizations:
                story.append(Paragraph(
                    'Feature Contributions' if self.language == 'en' else 'Đóng Góp Của Các Đặc Trưng',
                    styles['Heading2']
                ))
                try:
                    img_data = base64.b64decode(visualizations['waterfall'])
                    img = Image(io.BytesIO(img_data), width=6*inch, height=4*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    logger.warning(f"Could not add waterfall plot: {e}")
            
            # Radar chart
            if 'radar_chart' in visualizations:
                story.append(Paragraph(
                    'Domain Assessment' if self.language == 'en' else 'Đánh Giá Các Lĩnh Vực',
                    styles['Heading2']
                ))
                try:
                    img_data = base64.b64decode(visualizations['radar_chart'])
                    img = Image(io.BytesIO(img_data), width=5*inch, height=5*inch)
                    story.append(img)
                    story.append(Spacer(1, 0.3*inch))
                except Exception as e:
                    logger.warning(f"Could not add radar chart: {e}")
            
            story.append(PageBreak())
            
            # 5. Recommendations
            story.append(Paragraph(
                'Recommendations' if self.language == 'en' else 'Khuyến Nghị',
                styles['Heading1']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            recommendations = explanations.get('recommendations', [])
            for rec_group in recommendations:
                category = rec_group.get('category', '')
                story.append(Paragraph(f'<b>{category}</b>', styles['Heading2']))
                
                items = rec_group.get('items', [])
                for item in items:
                    title = item.get('title', '')
                    suggestions = item.get('suggestions', [])
                    
                    story.append(Paragraph(f'<b>{title}</b>', styles['Normal']))
                    for suggestion in suggestions:
                        story.append(Paragraph(f'  • {suggestion}', styles['Normal']))
                    story.append(Spacer(1, 0.1*inch))
            
            story.append(PageBreak())
            
            # 6. Technical Details (Appendix)
            story.append(Paragraph(
                'Technical Details' if self.language == 'en' else 'Chi Tiết Kỹ Thuật',
                styles['Heading1']
            ))
            story.append(Spacer(1, 0.2*inch))
            
            confidence = explanations.get('confidence', {})
            tech_info = f"""
            <b>Confidence Level:</b> {confidence.get('level', 'unknown')}<br/>
            <b>Explanation Method:</b> SHAP TreeExplainer<br/>
            <b>Base Value:</b> {shap_result.get('base_value', 0):.2f}<br/>
            <b>Prediction:</b> {shap_result.get('prediction', 0):.2f}<br/>
            <b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
            """
            story.append(Paragraph(tech_info, styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            buffer.seek(0)
            pdf_bytes = buffer.read()
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(pdf_bytes)
            
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}", exc_info=True)
            return b""
    
    def generate_html_report(self,
                            shap_result: Dict[str, Any],
                            explanations: Dict[str, Any],
                            visualizations: Dict[str, str],
                            output_path: Optional[str] = None) -> str:
        """
        Generate interactive HTML report
        
        Features:
        - Embedded interactive plotly charts
        - Collapsible sections
        - Print-friendly CSS
        - Share via link or email
        
        Returns:
            HTML string
        """
        try:
            mmse_score = explanations.get('mmse_score', 0)
            risk_level = explanations.get('risk_level', 'low')
            summary = explanations.get('summary', '')
            
            # Risk level colors
            risk_colors = {
                'low': '#2ecc71',
                'mild': '#f39c12',
                'moderate': '#e67e22',
                'severe': '#e74c3c'
            }
            risk_color = risk_colors.get(risk_level, '#95a5a6')
            
            html = f"""
<!DOCTYPE html>
<html lang="{self.language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cognitive Assessment Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #2c3e50;
            background: #ecf0f1;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid {risk_color};
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #2c3e50;
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .summary-card {{
            background: {risk_color}15;
            border-left: 4px solid {risk_color};
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }}
        .summary-card h2 {{
            color: {risk_color};
            margin-bottom: 10px;
        }}
        .section {{
            margin: 40px 0;
        }}
        .section h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .factor-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .factor-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }}
        .factor-card.positive {{
            border-left-color: #2ecc71;
        }}
        .factor-card.negative {{
            border-left-color: #e74c3c;
        }}
        .factor-card h3 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .visualization {{
            text-align: center;
            margin: 30px 0;
        }}
        .visualization img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .recommendations {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .recommendations h3 {{
            color: #856404;
            margin-bottom: 15px;
        }}
        .recommendations ul {{
            margin-left: 20px;
        }}
        .recommendations li {{
            margin: 10px 0;
        }}
        .technical-details {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-top: 40px;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 12px;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{"Cognitive Assessment Report" if self.language == 'en' else "Báo Cáo Đánh Giá Nhận Thức"}</h1>
            <p>{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>
        
        <div class="summary-card">
            <h2>{"Summary" if self.language == 'en' else "Tóm Tắt"}</h2>
            <p><strong>{"MMSE Score:" if self.language == 'en' else "Điểm MMSE:"}</strong> {mmse_score}/30</p>
            <p><strong>{"Risk Level:" if self.language == 'en' else "Mức Độ Nguy Cơ:"}</strong> {risk_level.upper()}</p>
            <p>{summary}</p>
        </div>
        
        <div class="section">
            <h2>{"Main Contributing Factors" if self.language == 'en' else "Các Yếu Tố Ảnh Hưởng Chính"}</h2>
            
            <h3>{"Strengths" if self.language == 'en' else "Điểm Mạnh"}</h3>
            <div class="factor-list">
"""
            
            # Positive factors
            positive_factors = explanations.get('positive_factors', [])
            for factor in positive_factors[:5]:
                html += f"""
                <div class="factor-card positive">
                    <h3>{factor.get('feature_display_name', '')}</h3>
                    <p>{factor.get('interpretation', '')}</p>
                    <p><small>{factor.get('comparison', {}).get('interpretation', '')}</small></p>
                </div>
"""
            
            html += """
            </div>
            
            <h3>Areas of Concern</h3>
            <div class="factor-list">
"""
            
            # Negative factors
            negative_factors = explanations.get('negative_factors', [])
            for factor in negative_factors[:5]:
                html += f"""
                <div class="factor-card negative">
                    <h3>{factor.get('feature_display_name', '')}</h3>
                    <p>{factor.get('interpretation', '')}</p>
                    <p><small>{factor.get('comparison', {}).get('interpretation', '')}</small></p>
                </div>
"""
            
            html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Detailed Analysis</h2>
"""
            
            # Visualizations
            if 'waterfall' in visualizations:
                html += f"""
            <div class="visualization">
                <h3>{"Feature Contributions" if self.language == 'en' else "Đóng Góp Của Các Đặc Trưng"}</h3>
                <img src="data:image/png;base64,{visualizations['waterfall']}" alt="Waterfall Plot">
            </div>
"""
            
            if 'radar_chart' in visualizations:
                html += f"""
            <div class="visualization">
                <h3>{"Domain Assessment" if self.language == 'en' else "Đánh Giá Các Lĩnh Vực"}</h3>
                <img src="data:image/png;base64,{visualizations['radar_chart']}" alt="Radar Chart">
            </div>
"""
            
            html += """
        </div>
        
        <div class="section">
            <div class="recommendations">
                <h2>Recommendations</h2>
"""
            
            # Recommendations
            recommendations = explanations.get('recommendations', [])
            for rec_group in recommendations:
                category = rec_group.get('category', '')
                html += f"<h3>{category}</h3><ul>"
                
                items = rec_group.get('items', [])
                for item in items:
                    title = item.get('title', '')
                    suggestions = item.get('suggestions', [])
                    html += f"<li><strong>{title}</strong><ul>"
                    for suggestion in suggestions:
                        html += f"<li>{suggestion}</li>"
                    html += "</ul></li>"
                
                html += "</ul>"
            
            html += """
            </div>
        </div>
        
        <div class="technical-details">
            <h3>Technical Details</h3>
            <p><strong>Confidence:</strong> {explanations.get('confidence', {}).get('level', 'unknown')}</p>
            <p><strong>Method:</strong> SHAP TreeExplainer</p>
            <p><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="footer">
            <p>Generated by Cognitive Assessment System</p>
            <p>This report is for informational purposes only and should not replace professional medical advice.</p>
        </div>
    </div>
</body>
</html>
"""
            
            # Save to file if path provided
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html)
            
            return html
            
        except Exception as e:
            logger.error(f"Error generating HTML report: {e}", exc_info=True)
            return ""
    
    def generate_summary_card(self,
                             shap_result: Dict[str, Any],
                             explanations: Dict[str, Any],
                             format: str = 'html') -> str:
        """
        Generate shareable summary card (like health app screenshots)
        
        Format: PNG or SVG
        Size: 1080x1920 (mobile-friendly)
        Content:
        - MMSE score in large font
        - Risk level with icon
        - Top 3 factors (bullet points)
        - Simple gauge visualization
        - Footer: "Generated by [App Name] on [Date]"
        
        Use case: Easy sharing with family/doctor via messaging apps
        
        Args:
            shap_result: SHAP results
            explanations: Explanations
            format: 'html' or 'svg'
        
        Returns:
            HTML string or SVG string
        """
        try:
            mmse_score = explanations.get('mmse_score', 0)
            risk_level = explanations.get('risk_level', 'low')
            
            # Risk level colors and icons
            risk_info = {
                'low': {'color': '#2ecc71', 'icon': '✓', 'text': 'Normal'},
                'mild': {'color': '#f39c12', 'icon': '⚠', 'text': 'MCI Risk'},
                'moderate': {'color': '#e67e22', 'icon': '⚠', 'text': 'Moderate'},
                'severe': {'color': '#e74c3c', 'icon': '✗', 'text': 'Severe'}
            }
            risk = risk_info.get(risk_level, risk_info['low'])
            
            # Top factors
            positive_factors = explanations.get('positive_factors', [])[:2]
            negative_factors = explanations.get('negative_factors', [])[:2]
            
            if format == 'html':
                html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #ecf0f1;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .card {{
            width: 400px;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid {risk['color']};
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .mmse-score {{
            font-size: 72px;
            font-weight: bold;
            color: {risk['color']};
            margin: 20px 0;
        }}
        .risk-level {{
            font-size: 24px;
            color: {risk['color']};
            margin: 10px 0;
        }}
        .factors {{
            margin: 20px 0;
        }}
        .factor {{
            padding: 10px;
            margin: 10px 0;
            border-left: 4px solid #3498db;
            background: #f8f9fa;
        }}
        .factor.positive {{
            border-left-color: #2ecc71;
        }}
        .factor.negative {{
            border-left-color: #e74c3c;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            font-size: 12px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="header">
            <div class="mmse-score">{mmse_score}/30</div>
            <div class="risk-level">{risk['icon']} {risk['text']}</div>
        </div>
        
        <div class="factors">
"""
                
                for factor in positive_factors:
                    html += f"""
            <div class="factor positive">
                <strong>✓ {factor.get('feature_display_name', '')}</strong><br/>
                <small>{factor.get('interpretation', '')[:50]}...</small>
            </div>
"""
                
                for factor in negative_factors:
                    html += f"""
            <div class="factor negative">
                <strong>⚠ {factor.get('feature_display_name', '')}</strong><br/>
                <small>{factor.get('interpretation', '')[:50]}...</small>
            </div>
"""
                
                html += f"""
        </div>
        
        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d')}</p>
            <p>Cognitive Assessment System</p>
        </div>
    </div>
</body>
</html>
"""
                return html
            else:
                # SVG format (simplified)
                svg = f"""
<svg width="400" height="600" xmlns="http://www.w3.org/2000/svg">
    <rect width="400" height="600" fill="white" rx="20"/>
    <text x="200" y="100" font-size="72" font-weight="bold" fill="{risk['color']}" text-anchor="middle">{mmse_score}/30</text>
    <text x="200" y="150" font-size="24" fill="{risk['color']}" text-anchor="middle">{risk['icon']} {risk['text']}</text>
    <text x="200" y="580" font-size="12" fill="#7f8c8d" text-anchor="middle">Generated on {datetime.now().strftime('%Y-%m-%d')}</text>
</svg>
"""
                return svg
                
        except Exception as e:
            logger.error(f"Error generating summary card: {e}", exc_info=True)
            return ""


def generate_complete_report(audio_features: Dict[str, Any],
                            linguistic_features: Dict[str, Any],
                            mmse_score: int,
                            risk_level: str = 'low',
                            language: str = 'vi',
                            output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to generate complete report package
    
    Returns:
        {
            'pdf': bytes,
            'html': str,
            'summary_card': str,
            'visualizations': dict
        }
    """
    try:
        # Import modules
        from modules.shap_explainer import compute_shap_for_assessment
        from modules.explanation_generator import generate_explanation_for_assessment
        from modules.shap_visualizations import create_all_visualizations
        
        # Compute SHAP
        shap_result = compute_shap_for_assessment(audio_features, linguistic_features, mmse_score)
        
        # Generate explanations
        explanations = generate_explanation_for_assessment(
            audio_features, linguistic_features, mmse_score, risk_level, language
        )
        
        # Create visualizations
        grouped_contributions = shap_result.get('grouped_contributions', {})
        visualizations = create_all_visualizations(
            shap_result, grouped_contributions, mmse_score, language
        )
        
        # Generate reports
        generator = SHAPReportGenerator(language=language)
        
        pdf_bytes = generator.generate_pdf_report(
            shap_result, explanations, visualizations
        )
        
        html_report = generator.generate_html_report(
            shap_result, explanations, visualizations
        )
        
        summary_card = generator.generate_summary_card(
            shap_result, explanations, format='html'
        )
        
        # Save files if output_dir provided
        if output_dir:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save PDF
            pdf_path = os.path.join(output_dir, f'report_{timestamp}.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(pdf_bytes)
            
            # Save HTML
            html_path = os.path.join(output_dir, f'report_{timestamp}.html')
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
            
            # Save summary card
            card_path = os.path.join(output_dir, f'summary_card_{timestamp}.html')
            with open(card_path, 'w', encoding='utf-8') as f:
                f.write(summary_card)
        
        return {
            'pdf': pdf_bytes,
            'html': html_report,
            'summary_card': summary_card,
            'visualizations': visualizations,
            'shap_result': shap_result,
            'explanations': explanations
        }
        
    except Exception as e:
        logger.error(f"Error generating complete report: {e}", exc_info=True)
        return {}

