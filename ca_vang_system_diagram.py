import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch
import numpy as np

# Set up the figure
fig, ax = plt.subplots(1, 1, figsize=(20, 12))
ax.set_xlim(0, 20)
ax.set_ylim(0, 12)
ax.axis('off')

# Define colors
colors = {
    'input': '#5DADE2',      # Blue
    'frontend': '#58D68D',   # Green
    'backend': '#F39C12',    # Orange
    'processing': '#AF7AC5', # Purple/Magenta
    'ai_screening': '#52D1AB', # Teal
    'decision': '#F4D03F',   # Yellow
    'low_risk': '#9B59B6',   # Purple
    'high_risk': '#EC7063',  # Coral/Red
    'output_clinician': '#9B59B6', # Purple for clinician notifications
    'output_user': '#9B59B6',       # Purple for user notifications
    'explainability': '#EC7063',    # Red for explainability
    'pdf_report': '#EC7063'         # Red for PDF report
}

# Function to create rounded boxes
def create_box(x, y, width, height, color, text, fontsize=10, fontweight='bold'):
    box = FancyBboxPatch((x, y), width, height,
                        boxstyle="round,pad=0.1",
                        facecolor=color,
                        edgecolor='black',
                        linewidth=1)
    ax.add_patch(box)

    # Add text
    ax.text(x + width/2, y + height/2, text,
           ha='center', va='center',
           fontsize=fontsize, fontweight=fontweight,
           color='white')

    return box

# Function to create stage labels
def create_stage_label(x, y, text):
    label_box = FancyBboxPatch((x, y), 1.5, 0.4,
                              boxstyle="round,pad=0.05",
                              facecolor='white',
                              edgecolor='gray',
                              linewidth=1)
    ax.add_patch(label_box)
    ax.text(x + 0.75, y + 0.2, text,
           ha='center', va='center',
           fontsize=8, fontweight='bold',
           color='black')

# Function to create arrows
def create_arrow(x1, y1, x2, y2, connectionstyle="arc3,rad=0"):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                           arrowstyle='->',
                           color='gray',
                           linewidth=2,
                           connectionstyle=connectionstyle)
    ax.add_patch(arrow)

# Function to create decision labels
def create_decision_label(x, y, text, color):
    ax.text(x, y, text,
           ha='center', va='center',
           fontsize=12, fontweight='bold',
           color=color,
           bbox=dict(boxstyle="round,pad=0.3",
                    facecolor='white',
                    edgecolor=color,
                    linewidth=2))

# STAGE 1 - INPUT (Blue)
create_stage_label(0.5, 10.5, "STAGE 1")
box_input1 = create_box(0.2, 8.5, 2.5, 1.5, colors['input'], "User Device\nBrowser/Mobile", fontsize=9)
box_input2 = create_box(0.2, 6.5, 2.5, 1.5, colors['input'], "Audio Record\nWebM/MP3/MP4", fontsize=9)

# STAGE 2 - FRONTEND (Green)
create_stage_label(3.5, 10.5, "STAGE 2")
box_frontend = create_box(3.0, 7.0, 2.5, 2.0, colors['frontend'], "Next.js\nFrontend API", fontsize=10)

# STAGE 3 - BACKEND (Orange)
create_stage_label(6.5, 10.5, "STAGE 3")
box_backend = create_box(5.8, 7.0, 2.5, 2.0, colors['backend'], "Flask Backend\nPython API", fontsize=10)

# STAGE 4 - PROCESSING (Purple) - Vertical flow
create_stage_label(9.5, 10.5, "STAGE 4")
box_convert = create_box(8.5, 8.0, 3.0, 1.0, colors['processing'], "Convert\nFFmpeg→WAV", fontsize=9)
box_preprocess = create_box(8.5, 6.5, 3.0, 1.0, colors['processing'], "Preprocess\nVAD+Denoise", fontsize=9)
box_features = create_box(8.5, 5.0, 3.0, 1.0, colors['processing'], "Features\nMFCC+NLP", fontsize=9)
box_database = create_box(8.5, 3.5, 3.0, 1.0, colors['processing'], "Database\nPostgreSQL", fontsize=9)

# STAGE 5 - AI SCREENING (Teal)
create_stage_label(12.5, 10.5, "STAGE 5")
box_ai_model = create_box(12.0, 6.5, 2.5, 2.0, colors['ai_screening'], "AI Model\nTier 1\nSVM/LightGBM", fontsize=9)

# STAGE 6 - DECISION (Yellow)
create_stage_label(15.5, 10.5, "STAGE 6")
box_decision = create_box(15.0, 7.0, 2.0, 1.5, colors['decision'], "Risk Assessment\nDecision Point", fontsize=8)

# Low Risk Direct Result
box_low_risk = create_box(15.0, 4.5, 2.0, 1.5, colors['low_risk'], "Low Risk\nDirect Result", fontsize=9)

# STAGE 7 - OUTPUT paths
create_stage_label(18.5, 10.5, "STAGE 7")

# High Risk path - Cloud AI
box_cloud_ai = create_box(17.5, 8.0, 2.5, 1.5, colors['high_risk'], "Cloud AI\nDeep Learning", fontsize=9)

# Explainability and PDF Report
box_explainability = create_box(17.5, 6.0, 2.5, 1.0, colors['explainability'], "Explainability\nSHAP/LIME", fontsize=8)
box_pdf_report = create_box(17.5, 4.5, 2.5, 1.0, colors['pdf_report'], "PDF Report\nGeneration", fontsize=8)

# Notifications
box_notify_clinician = create_box(17.5, 2.5, 2.5, 1.0, colors['output_clinician'], "Notify\nClinician", fontsize=8)
box_notify_user = create_box(17.5, 1.0, 2.5, 1.0, colors['output_user'], "Notify\nUser", fontsize=8)

# Create arrows for the main flow

# Input to Frontend
create_arrow(2.7, 8.0, 3.0, 8.0)  # Audio Record to Frontend
create_arrow(2.7, 7.5, 3.0, 8.0)  # Browser to Frontend

# Frontend to Backend
create_arrow(5.5, 8.0, 5.8, 8.0)

# Backend to Processing (Convert)
create_arrow(8.3, 8.0, 8.5, 8.5)

# Processing vertical flow
create_arrow(9.75, 7.5, 9.75, 7.0)  # Convert to Preprocess
create_arrow(9.75, 6.0, 9.75, 5.5)  # Preprocess to Features
create_arrow(9.75, 4.5, 9.75, 4.0)  # Features to Database

# Features to AI Model
create_arrow(11.5, 5.5, 12.0, 7.0)

# AI Model to Decision
create_arrow(14.5, 7.5, 15.0, 7.5)

# Decision to Low Risk
create_arrow(16.0, 6.0, 16.0, 5.5)
create_decision_label(15.5, 5.8, "LOW", "green")

# Decision to Cloud AI (High Risk)
create_arrow(16.5, 7.5, 17.5, 8.5)
create_decision_label(16.8, 8.2, "HIGH RISK", "red")

# Cloud AI to Explainability
create_arrow(18.25, 7.5, 18.25, 6.5)

# Explainability to PDF Report
create_arrow(18.25, 5.5, 18.25, 5.0)

# PDF Report to Notify Clinician
create_arrow(18.25, 4.0, 18.25, 3.0)

# Notify Clinician to Notify User
create_arrow(18.25, 2.0, 18.25, 1.5)

# Add title and subtitle
ax.text(10, 11.5, "Cá Vàng - Tháp sáng Ký ức: Workflow phân tích giọng nói",
       ha='center', va='center', fontsize=16, fontweight='bold')
ax.text(10, 11.2, "System Architecture: 7-Stage Processing Pipeline with AI-Driven Risk Assessment",
       ha='center', va='center', fontsize=12, color='gray')

# Create legend
legend_elements = [
    mpatches.Patch(facecolor=colors['input'], label='Input', edgecolor='black'),
    mpatches.Patch(facecolor=colors['frontend'], label='Frontend', edgecolor='black'),
    mpatches.Patch(facecolor=colors['backend'], label='Backend', edgecolor='black'),
    mpatches.Patch(facecolor=colors['processing'], label='Processing', edgecolor='black'),
    mpatches.Patch(facecolor=colors['ai_screening'], label='AI Screening', edgecolor='black'),
    mpatches.Patch(facecolor=colors['decision'], label='Decision Point', edgecolor='black'),
    mpatches.Patch(facecolor=colors['low_risk'], label='Low Risk Output', edgecolor='black'),
    mpatches.Patch(facecolor=colors['high_risk'], label='High Risk/Cloud AI', edgecolor='black'),
]

ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, -0.05),
         ncol=4, fontsize=10, frameon=True)

# Save the diagram
plt.savefig('ca_vang_system_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.close()

print("System architecture diagram saved as 'ca_vang_system_diagram.png'")