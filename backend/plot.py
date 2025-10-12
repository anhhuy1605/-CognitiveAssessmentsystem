"""
Hệ thống vẽ biểu đồ thống kê cho Cognitive Assessment System
Tạo các biểu đồ phân tích hiệu suất mô hình, phân phối dữ liệu, và metrics đánh giá
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc, mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler
import os
from pathlib import Path

# Set style cho plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12

class CognitiveStatsPlotter:
    """Class để tạo các biểu đồ thống kê cho hệ thống nhận thức"""

    def __init__(self, output_dir="plots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def load_test_data(self, file_path="test_data.csv"):
        """Load dữ liệu test từ CSV"""
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            print(f"Loaded data shape: {df.shape}")
            return df
        else:
            print(f"File {file_path} not found, using sample data")
            return None

    def load_dx_mmse_data(self, file_path="dx-mmse.csv"):
        """Load dữ liệu dx-mmse từ CSV"""
        if os.path.exists(file_path):
            df = pd.read_csv(file_path, skiprows=1)  # Skip header row
            df.columns = ['index', 'id', 'sid', 'vis', 'age', 'gender', 'mmse', 'dur.mean', 'dur.sd',
                         'dur.median', 'srate.mean', 'srate.max', 'srate.min', 'srate.sd', 'number.utt',
                         'sildur.mean', 'sildur.sd', 'sildur.median', 'dur.max', 'sildur.max', 'dur.min',
                         'sildur.min', 'filename', 'dx', 'dataset', 'adressfname', 'distance', 'weights', 'subclass', 'test']
            print(f"Loaded dx-mmse data shape: {df.shape}")
            return df
        else:
            print(f"File {file_path} not found")
            return None

    def create_model_performance_plots(self, model_results, test_data):
        """Tạo biểu đồ hiệu suất mô hình"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Confusion Matrix
        if 'pred' in model_results and 'true' in test_data:
            cm = confusion_matrix(test_data['true'], model_results['pred'])
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0,0])
            axes[0,0].set_title('Ma Trận Nhầm Lẫn (Confusion Matrix)')
            axes[0,0].set_xlabel('Dự đoán')
            axes[0,0].set_ylabel('Thực tế')

        # 2. ROC Curve
        if 'proba' in model_results and 'true' in test_data:
            fpr, tpr, _ = roc_curve(test_data['true'], model_results['proba'])
            auc_score = auc(fpr, tpr)
            axes[0,1].plot(fpr, tpr, label=f'AUC = {auc_score:.3f}')
            axes[0,1].plot([0,1], [0,1], 'k--', alpha=0.7)
            axes[0,1].set_xlabel('Tỷ lệ Dương tính Sai (FPR)')
            axes[0,1].set_ylabel('Tỷ lệ Dương tính Đúng (TPR)')
            axes[0,1].set_title('Đường Cong ROC')
            axes[0,1].legend()
            axes[0,1].grid(True, alpha=0.3)

        # 3. Metrics Bar Chart
        metrics = ['RMSE', 'MAE', 'R²', 'Accuracy']
        values = [
            model_results.get('rmse', 0),
            model_results.get('mae', 0),
            model_results.get('r2', 0),
            model_results.get('acc', 0)
        ]
        bars = axes[1,0].bar(metrics, values, alpha=0.8, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        axes[1,0].set_title('Chỉ Số Hiệu Suất Mô Hình')
        axes[1,0].set_ylabel('Giá trị')
        axes[1,0].grid(True, alpha=0.3)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            axes[1,0].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                          f'{val:.3f}', ha='center', va='bottom')

        # 4. Prediction vs True Scatter
        if 'predictions' in model_results and 'mmse_true' in test_data:
            axes[1,1].scatter(test_data['mmse_true'], model_results['predictions'], alpha=0.6, s=50)
            axes[1,1].plot([0, 30], [0, 30], 'r--', alpha=0.8)
            axes[1,1].set_xlabel('Điểm MMSE Thực tế')
            axes[1,1].set_ylabel('Điểm MMSE Dự đoán')
            axes[1,1].set_title('Dự đoán vs Thực tế')
            axes[1,1].grid(True, alpha=0.3)
            axes[1,1].set_xlim(0, 30)
            axes[1,1].set_ylim(0, 30)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'model_performance_overview.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_data_distribution_plots(self, data_df):
        """Tạo biểu đồ phân phối dữ liệu"""
        if data_df is None:
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # 1. MMSE Distribution
        if 'mmse' in data_df.columns:
            sns.histplot(data_df['mmse'], kde=True, ax=axes[0,0])
            axes[0,0].set_title('Phân phối Điểm MMSE')
            axes[0,0].set_xlabel('Điểm MMSE')
            axes[0,0].axvline(data_df['mmse'].mean(), color='red', linestyle='--', label=f'Trung bình: {data_df["mmse"].mean():.1f}')
            axes[0,0].legend()

        # 2. Age Distribution
        if 'age' in data_df.columns:
            sns.histplot(data_df['age'], kde=True, ax=axes[0,1])
            axes[0,1].set_title('Phân phối Tuổi')
            axes[0,1].set_xlabel('Tuổi')
            axes[0,1].axvline(data_df['age'].mean(), color='red', linestyle='--', label=f'Trung bình: {data_df["age"].mean():.1f}')
            axes[0,1].legend()

        # 3. Gender Distribution
        if 'gender' in data_df.columns:
            gender_counts = data_df['gender'].value_counts()
            axes[0,2].pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%')
            axes[0,2].set_title('Phân phối Giới tính')

        # 4. MMSE by Diagnosis
        if 'mmse' in data_df.columns and 'dx' in data_df.columns:
            sns.boxplot(x='dx', y='mmse', data=data_df, ax=axes[1,0])
            axes[1,0].set_title('Điểm MMSE theo Chẩn đoán')
            axes[1,0].set_xlabel('Chẩn đoán')
            axes[1,0].set_ylabel('Điểm MMSE')

        # 5. Age by Diagnosis
        if 'age' in data_df.columns and 'dx' in data_df.columns:
            sns.boxplot(x='dx', y='age', data=data_df, ax=axes[1,1])
            axes[1,1].set_title('Tuổi theo Chẩn đoán')
            axes[1,1].set_xlabel('Chẩn đoán')
            axes[1,1].set_ylabel('Tuổi')

        # 6. Education Distribution
        if 'education' in data_df.columns:
            sns.histplot(data_df['education'], kde=True, ax=axes[1,2])
            axes[1,2].set_title('Phân phối Trình độ Học vấn')
            axes[1,2].set_xlabel('Năm học')
            axes[1,2].axvline(data_df['education'].mean(), color='red', linestyle='--', label=f'Trung bình: {data_df["education"].mean():.1f}')
            axes[1,2].legend()

        plt.tight_layout()
        plt.savefig(self.output_dir / 'data_distribution_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_acoustic_feature_analysis(self, data_df):
        """Tạo biểu đồ phân tích đặc trưng âm học"""
        if data_df is None:
            return

        # Select acoustic features
        acoustic_cols = [col for col in data_df.columns if any(x in col.lower() for x in ['dur', 'srate', 'sil', 'utt'])]

        if not acoustic_cols:
            print("Không tìm thấy đặc trưng âm học")
            return

        # Select up to 6 features for plotting
        acoustic_cols = acoustic_cols[:6]

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        for i, col in enumerate(acoustic_cols):
            if i < 6:
                if data_df[col].dtype in ['int64', 'float64']:
                    sns.histplot(data_df[col].dropna(), kde=True, ax=axes[i])
                    axes[i].set_title(f'Phân phối {col}')
                    axes[i].set_xlabel(col)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'acoustic_features_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_correlation_heatmap(self, data_df):
        """Tạo heatmap tương quan"""
        if data_df is None:
            return

        # Select numeric columns
        numeric_cols = data_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) < 2:
            return

        # Calculate correlation
        corr_matrix = data_df[numeric_cols].corr()

        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=False, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5)
        plt.title('Ma Trận Tương Quan Các Đặc Trưng')
        plt.tight_layout()
        plt.savefig(self.output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_feature_importance_plot(self, feature_names, importance_scores):
        """Tạo biểu đồ tầm quan trọng của đặc trưng"""
        plt.figure(figsize=(12, 8))

        # Sort by importance
        sorted_idx = np.argsort(importance_scores)
        pos = np.arange(len(feature_names))

        plt.barh(pos, np.array(importance_scores)[sorted_idx])
        plt.yticks(pos, np.array(feature_names)[sorted_idx])
        plt.xlabel('Tầm Quan Trọng')
        plt.title('Tầm Quan Trọng Các Đặc Trưng (Feature Importance)')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_error_analysis_plots(self, y_true, y_pred):
        """Tạo biểu đồ phân tích lỗi"""
        errors = y_pred - y_true

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1. Residuals vs Predicted
        axes[0,0].scatter(y_pred, errors, alpha=0.6, s=50)
        axes[0,0].axhline(y=0, color='red', linestyle='--', alpha=0.8)
        axes[0,0].set_xlabel('Giá Trị Dự Đoán')
        axes[0,0].set_ylabel('Sai Số (Residuals)')
        axes[0,0].set_title('Residuals vs Predicted Values')
        axes[0,0].grid(True, alpha=0.3)

        # 2. Distribution of Errors
        axes[0,1].hist(errors, bins=30, alpha=0.7, edgecolor='black')
        axes[0,1].axvline(x=0, color='red', linestyle='--', alpha=0.8)
        axes[0,1].set_xlabel('Sai Số')
        axes[0,1].set_ylabel('Tần Suất')
        axes[0,1].set_title('Phân Phối Sai Số')
        axes[0,1].grid(True, alpha=0.3)

        # 3. Error vs True Values
        axes[1,0].scatter(y_true, errors, alpha=0.6, s=50)
        axes[1,0].axhline(y=0, color='red', linestyle='--', alpha=0.8)
        axes[1,0].set_xlabel('Giá Trị Thực Tế')
        axes[1,0].set_ylabel('Sai Số (Residuals)')
        axes[1,0].set_title('Error vs True Values')
        axes[1,0].grid(True, alpha=0.3)

        # 4. Q-Q Plot for normality check
        from scipy import stats
        stats.probplot(errors, dist="norm", plot=axes[1,1])
        axes[1,1].set_title('Q-Q Plot (Kiểm tra Phân Phối Chuẩn)')
        axes[1,1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'error_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_demographic_analysis(self, data_df):
        """Phân tích nhân khẩu học chi tiết"""
        if data_df is None:
            return

        fig, axes = plt.subplots(2, 3, figsize=(18, 12))

        # 1. Age distribution by diagnosis
        if 'age' in data_df.columns and 'dx' in data_df.columns:
            sns.violinplot(x='dx', y='age', data=data_df, ax=axes[0,0])
            axes[0,0].set_title('Tuổi theo Chẩn Đoán')
            axes[0,0].set_xlabel('Chẩn Đoán')
            axes[0,0].set_ylabel('Tuổi')

        # 2. MMSE by age groups
        if 'age' in data_df.columns and 'mmse' in data_df.columns:
            data_df['age_group'] = pd.cut(data_df['age'], bins=[0, 60, 70, 80, 100],
                                        labels=['<60', '60-70', '70-80', '80+'])
            sns.boxplot(x='age_group', y='mmse', data=data_df, ax=axes[0,1])
            axes[0,1].set_title('MMSE theo Nhóm Tuổi')
            axes[0,1].set_xlabel('Nhóm Tuổi')
            axes[0,1].set_ylabel('Điểm MMSE')

        # 3. Gender differences in MMSE
        if 'gender' in data_df.columns and 'mmse' in data_df.columns:
            sns.boxplot(x='gender', y='mmse', data=data_df, ax=axes[0,2])
            axes[0,2].set_title('MMSE theo Giới Tính')
            axes[0,2].set_xlabel('Giới Tính')
            axes[0,2].set_ylabel('Điểm MMSE')

        # 4. Education vs MMSE correlation
        if 'education' in data_df.columns and 'mmse' in data_df.columns:
            sns.scatterplot(x='education', y='mmse', data=data_df, ax=axes[1,0])
            # Add trend line
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                data_df['education'].dropna(), data_df['mmse'].dropna())
            x_line = np.linspace(data_df['education'].min(), data_df['education'].max(), 100)
            y_line = slope * x_line + intercept
            axes[1,0].plot(x_line, y_line, color='red', linestyle='--',
                          label=f'r = {r_value:.2f}, p = {p_value:.3f}')
            axes[1,0].legend()
            axes[1,0].set_title('Trình Độ Học Vấn vs MMSE')
            axes[1,0].set_xlabel('Năm Học')
            axes[1,0].set_ylabel('Điểm MMSE')

        # 5. Diagnosis distribution
        if 'dx' in data_df.columns:
            dx_counts = data_df['dx'].value_counts()
            axes[1,1].pie(dx_counts.values, labels=dx_counts.index, autopct='%1.1f%%')
            axes[1,1].set_title('Phân Bố Chẩn Đoán')

        # 6. Summary statistics table
        axes[1,2].axis('off')
        summary_text = ".1f"".1f"f"""
        THỐNG KÊ TÓM TẮT

        Số mẫu: {len(data_df)}

        MMSE:
        - Trung bình: {data_df['mmse'].mean():.1f} ± {data_df['mmse'].std():.1f}
        - Min: {data_df['mmse'].min():.1f}, Max: {data_df['mmse'].max():.1f}

        Tuổi:
        - Trung bình: {data_df['age'].mean():.1f} ± {data_df['age'].std():.1f}
        - Min: {data_df['age'].min():.0f}, Max: {data_df['age'].max():.0f}
        """
        axes[1,2].text(0.1, 0.8, summary_text, transform=axes[1,2].transAxes,
                      fontsize=10, verticalalignment='top', fontfamily='monospace')

        plt.tight_layout()
        plt.savefig(self.output_dir / 'demographic_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_acoustic_feature_correlations(self, data_df):
        """Phân tích tương quan đặc trưng acoustic với MMSE"""
        if data_df is None:
            return

        # Select acoustic features
        acoustic_cols = [col for col in data_df.columns if any(x in col.lower() for x in ['dur', 'srate', 'sil', 'utt'])]

        if not acoustic_cols or 'mmse' not in data_df.columns:
            return

        # Calculate correlations with MMSE
        correlations = {}
        for col in acoustic_cols:
            if data_df[col].dtype in ['int64', 'float64']:
                corr = data_df[col].corr(data_df['mmse'])
                correlations[col] = abs(corr)  # Use absolute correlation

        # Sort by correlation strength
        sorted_features = sorted(correlations.items(), key=lambda x: x[1], reverse=True)
        top_features = sorted_features[:8]  # Top 8 most correlated

        fig, axes = plt.subplots(2, 4, figsize=(20, 10))
        axes = axes.flatten()

        for i, (feature, corr) in enumerate(top_features):
            if i < 8:
                sns.scatterplot(x=feature, y='mmse', data=data_df, ax=axes[i], alpha=0.6)
                axes[i].set_title('.3f')
                axes[i].set_xlabel(feature)
                axes[i].set_ylabel('MMSE Score')
                axes[i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'acoustic_mmse_correlations.png', dpi=300, bbox_inches='tight')
        plt.close()

        # Save correlation results
        corr_df = pd.DataFrame(sorted_features, columns=['Feature', 'Correlation_with_MMSE'])
        corr_df.to_csv(self.output_dir / 'acoustic_correlations.csv', index=False)

    def create_model_comparison_plots(self, model_results_dict):
        """So sánh hiệu suất giữa các mô hình"""
        if not model_results_dict:
            return

        models = list(model_results_dict.keys())
        metrics = ['rmse', 'mae', 'r2', 'accuracy']
        metric_names = ['RMSE', 'MAE', 'R²', 'Accuracy']

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        axes = axes.flatten()

        for i, (metric, name) in enumerate(zip(metrics, metric_names)):
            values = []
            for model in models:
                if 'regression_metrics' in model_results_dict[model]:
                    val = model_results_dict[model]['regression_metrics'].get(metric, 0)
                else:
                    val = model_results_dict[model].get(metric, 0)
                values.append(val)

            bars = axes[i].bar(models, values, alpha=0.8, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F7DC6F'])
            axes[i].set_title(f'So Sánh {name} Giữa Các Mô Hình')
            axes[i].set_ylabel(name)
            axes[i].tick_params(axis='x', rotation=45)

            # Add value labels
            for bar, val in zip(bars, values):
                axes[i].text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                           '.3f', ha='center', va='bottom')

            axes[i].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(self.output_dir / 'model_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()

    def create_longitudinal_analysis(self, longitudinal_data):
        """Phân tích dữ liệu theo thời gian nếu có"""
        if longitudinal_data is None or longitudinal_data.empty:
            print("Không có dữ liệu longitudinal để phân tích")
            return

        # Assuming longitudinal data has columns: patient_id, date, mmse_score
        if 'date' not in longitudinal_data.columns or 'mmse_score' not in longitudinal_data.columns:
            print("Dữ liệu longitudinal thiếu cột date hoặc mmse_score")
            return

        # Convert date to datetime if needed
        longitudinal_data['date'] = pd.to_datetime(longitudinal_data['date'])

        # Group by patient and calculate trends
        plt.figure(figsize=(14, 8))

        # Plot individual patient trajectories
        for patient_id in longitudinal_data['patient_id'].unique()[:10]:  # Show first 10 patients
            patient_data = longitudinal_data[longitudinal_data['patient_id'] == patient_id].sort_values('date')
            plt.plot(patient_data['date'], patient_data['mmse_score'],
                    marker='o', alpha=0.7, label=f'Patient {patient_id}')

        plt.xlabel('Thời Gian')
        plt.ylabel('Điểm MMSE')
        plt.title('Xu Hướng MMSE Theo Thời Gian (10 Bệnh Nhân Đầu Tiên)')
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(self.output_dir / 'longitudinal_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()

    def generate_detailed_report(self, data_df, model_results=None):
        """Tạo báo cáo chi tiết với tất cả phân tích"""
        report_path = self.output_dir / 'detailed_analysis_report.txt'

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("BÁO CÁO PHÂN TÍCH CHI TIẾT - HỆ THỐNG COGNITIVE ASSESSMENT\n")
            f.write("=" * 80 + "\n\n")

            # Dataset Overview
            f.write("1. TỔNG QUAN DỮ LIỆU\n")
            f.write("-" * 40 + "\n")
            f.write(f"Số mẫu: {len(data_df)}\n")

            if 'mmse' in data_df.columns:
                f.write("MMSE Statistics:\n")
                f.write(f"  - Trung bình: {data_df['mmse'].mean():.1f}\n")
                f.write(f"  - Độ lệch chuẩn: {data_df['mmse'].std():.1f}\n")
                f.write(f"  - Min: {data_df['mmse'].min():.1f}, Max: {data_df['mmse'].max():.1f}\n")
            if 'age' in data_df.columns:
                f.write("Age Statistics:\n")
                f.write(f"  - Trung bình: {data_df['age'].mean():.1f}\n")
                f.write(f"  - Độ lệch chuẩn: {data_df['age'].std():.1f}\n")
                f.write(f"  - Min: {data_df['age'].min():.0f}, Max: {data_df['age'].max():.0f}\n")
            if 'dx' in data_df.columns:
                f.write("Diagnosis Distribution:\n")
                for dx, count in data_df['dx'].value_counts().items():
                    f.write(f"  - {dx}: {count} ({count/len(data_df)*100:.1f}%)\n")

            # Acoustic Features Analysis
            f.write("\n\n2. PHÂN TÍCH ĐẶC TRƯNG ACOUSTIC\n")
            f.write("-" * 40 + "\n")

            acoustic_cols = [col for col in data_df.columns if any(x in col.lower() for x in ['dur', 'srate', 'sil', 'utt'])]
            f.write(f"Số đặc trưng acoustic: {len(acoustic_cols)}\n")
            f.write("Các đặc trưng:\n")
            for col in acoustic_cols:
                f.write(f"  - {col}\n")

            # Correlation Analysis
            if 'mmse' in data_df.columns and acoustic_cols:
                f.write("\nTương quan với MMSE:\n")
                for col in acoustic_cols[:10]:  # Top 10
                    if data_df[col].dtype in ['int64', 'float64']:
                        corr = data_df[col].corr(data_df['mmse'])
                        f.write(f"  - {col}: r = {corr:.3f}\n")

            # Model Performance
            if model_results:
                f.write("\n\n3. HIỆU SUẤT MÔ HÌNH\n")
                f.write("-" * 40 + "\n")

                for model_name, results in model_results.items():
                    f.write(f"\nMô hình: {model_name}\n")
                    if 'regression_metrics' in results:
                        reg_metrics = results['regression_metrics']
                        f.write(f"  - RMSE: {reg_metrics.get('rmse', 0):.3f}\n")
                        f.write(f"  - MAE: {reg_metrics.get('mae', 0):.3f}\n")
                        f.write(f"  - R²: {reg_metrics.get('r2', 0):.3f}\n")
                    if 'classification_metrics' in results:
                        cls_metrics = results['classification_metrics']
                        f.write(f"  - Sensitivity: {cls_metrics.get('sensitivity', 0):.3f}\n")
                        f.write(f"  - Specificity: {cls_metrics.get('specificity', 0):.3f}\n")
                        f.write(f"  - F1-Score: {cls_metrics.get('f1_score', 0):.3f}\n")            # Recommendations
            f.write("\n\n4. KHUYẾN NGHỊ\n")
            f.write("-" * 40 + "\n")

            if 'mmse' in data_df.columns:
                mmse_mean = data_df['mmse'].mean()
                if mmse_mean < 24:
                    f.write("⚠️  Trung bình MMSE thấp - cần cải thiện độ chính xác mô hình\n")
                else:
                    f.write("✅ Trung bình MMSE trong khoảng bình thường\n")

            if model_results:
                best_model = max(model_results.items(), key=lambda x: x[1].get('regression_metrics', {}).get('r2', 0))
                f.write(f"🏆 Mô hình tốt nhất: {best_model[0]}\n")

            f.write("\n📊 Các biểu đồ đã được tạo:\n")
            f.write("  - model_performance_overview.png\n")
            f.write("  - data_distribution_analysis.png\n")
            f.write("  - acoustic_features_analysis.png\n")
            f.write("  - correlation_heatmap.png\n")
            f.write("  - error_analysis.png\n")
            f.write("  - demographic_analysis.png\n")
            f.write("  - acoustic_mmse_correlations.png\n")
            f.write("  - model_comparison.png\n")

        print(f"✓ Báo cáo chi tiết đã được lưu tại: {report_path}")

    def generate_comprehensive_stats_report(self):
        """Tạo báo cáo thống kê toàn diện với nhiều biểu đồ chi tiết"""
        print("=== Báo Cáo Thống Kê Hệ Thống Cognitive Assessment ===")
        print("Đang tạo phân tích chi tiết với nhiều biểu đồ...")

        # Load data
        test_data = self.load_test_data()
        dx_mmse_data = self.load_dx_mmse_data()

        # Print basic statistics
        if test_data is not None:
            print("\n--- Thống kê dữ liệu Test ---")
            print(f"Số mẫu: {len(test_data)}")
            if 'mmse' in test_data.columns:
                print(f"MMSE - Trung bình: {test_data['mmse'].mean():.2f}, STD: {test_data['mmse'].std():.2f}")
            if 'age' in test_data.columns:
                print(f"Tuổi - Trung bình: {test_data['age'].mean():.2f}, STD: {test_data['age'].std():.2f}")
            if 'dx' in test_data.columns:
                print(f"Chẩn đoán: {test_data['dx'].value_counts().to_dict()}")

        if dx_mmse_data is not None:
            print("\n--- Thống kê dữ liệu DX-MMSE ---")
            print(f"Số mẫu: {len(dx_mmse_data)}")
            if 'mmse' in dx_mmse_data.columns:
                print(f"MMSE - Trung bình: {dx_mmse_data['mmse'].mean():.2f}, STD: {dx_mmse_data['mmse'].std():.2f}")
            if 'age' in dx_mmse_data.columns:
                print(f"Tuổi - Trung bình: {dx_mmse_data['age'].mean():.2f}, STD: {dx_mmse_data['age'].std():.2f}")
            if 'dx' in dx_mmse_data.columns:
                print(f"Chẩn đoán: {dx_mmse_data['dx'].value_counts().to_dict()}")

        # Create plots
        print("\n--- Tạo biểu đồ chi tiết ---")

        # Sample model results for demonstration
        sample_model_results = {
            'rmse': 2.5,
            'mae': 2.0,
            'r2': 0.85,
            'acc': 0.88,
            'pred': np.random.randint(0, 2, 100) if test_data is None else None,
            'proba': np.random.rand(100) if test_data is None else None,
            'predictions': np.random.normal(20, 5, 100) if test_data is None else None
        }

        sample_test_data = pd.DataFrame({
            'true': np.random.randint(0, 2, 100),
            'mmse_true': np.random.normal(20, 5, 100)
        }) if test_data is None else test_data

        # Multiple model comparison (sample data)
        model_comparison_data = {
            'Random Forest': {'rmse': 2.3, 'mae': 1.8, 'r2': 0.87, 'acc': 0.90},
            'XGBoost': {'rmse': 2.5, 'mae': 2.0, 'r2': 0.85, 'acc': 0.88},
            'SVM': {'rmse': 2.7, 'mae': 2.2, 'r2': 0.83, 'acc': 0.85},
            'LightGBM': {'rmse': 2.4, 'mae': 1.9, 'r2': 0.86, 'acc': 0.89}
        }

        data_for_plots = dx_mmse_data if dx_mmse_data is not None else test_data

        # Core plots
        self.create_model_performance_plots(sample_model_results, sample_test_data)
        print("✓ Biểu đồ hiệu suất mô hình")

        self.create_data_distribution_plots(data_for_plots)
        print("✓ Biểu đồ phân phối dữ liệu")

        self.create_acoustic_feature_analysis(data_for_plots)
        print("✓ Biểu đồ đặc trưng âm học")

        self.create_correlation_heatmap(data_for_plots)
        print("✓ Heatmap tương quan")

        # Advanced plots
        self.create_demographic_analysis(data_for_plots)
        print("✓ Phân tích nhân khẩu học")

        self.create_acoustic_feature_correlations(data_for_plots)
        print("✓ Tương quan acoustic vs MMSE")

        self.create_model_comparison_plots(model_comparison_data)
        print("✓ So sánh mô hình")

        # Error analysis if we have predictions
        if 'predictions' in sample_model_results and 'mmse_true' in sample_test_data:
            self.create_error_analysis_plots(
                sample_test_data['mmse_true'].values,
                sample_model_results['predictions']
            )
            print("✓ Phân tích lỗi")

        # Feature importance (sample data)
        feature_names = ['speech_rate', 'pause_duration', 'f0_mean', 'f0_std', 'mfcc_0', 'mfcc_1', 'jitter', 'shimmer']
        importance_scores = np.random.rand(len(feature_names))
        self.create_feature_importance_plot(feature_names, importance_scores)
        print("✓ Tầm quan trọng đặc trưng")

        # Generate detailed text report
        self.generate_detailed_report(data_for_plots, model_comparison_data)
        print("✓ Báo cáo văn bản chi tiết")

        print("\n🎉 HOÀN THÀNH! Đã tạo tổng cộng:")
        print(f"   📊 {len(list(self.output_dir.glob('*.png')))} biểu đồ PNG chất lượng cao")
        print("   📝 1 báo cáo văn bản chi tiết")
        print("   📈 1 file CSV tương quan acoustic")
        print(f"\n💾 Tất cả đã được lưu vào thư mục: {self.output_dir}")
        print("\n📋 DANH SÁCH BIỂU ĐỒ ĐÃ TẠO:")
        for png_file in sorted(self.output_dir.glob('*.png')):
            print(f"   • {png_file.name}")

# Main execution
if __name__ == "__main__":
    plotter = CognitiveStatsPlotter()
    plotter.generate_comprehensive_stats_report()
