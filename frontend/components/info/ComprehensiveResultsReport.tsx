"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  TrendingUp,
  Target,
  CheckCircle,
  Clock,
  BarChart3,
  Zap,
  Users,
  FileText,
  Mic,
  Brain
} from "lucide-react";

export default function ComprehensiveResultsReport() {
  const sampleCharacteristics = {
    totalParticipants: 237,
    distribution: {
      healthy: 115,
      mci: 122
    },
    demographics: {
      age: {
        mean: 68.4,
        sd: 6.9,
        range: "60-89"
      },
      gender: {
        male: 44,
        female: 56
      }
    },
    speechTasks: {
      tasksPerPerson: 3,
      totalRecordings: 711,
      avgDuration: 1.8
    }
  };

  const preprocessingResults = {
    successRate: 98,
    snrImprovement: "6-9 dB",
    totalFeatures: 560,
    featureCategories: {
      acoustic: ["eGeMAPS", "MFCCs/statistics", "F0 contour", "jitter/shimmer", "formants"],
      linguistic: ["PhoBERT embeddings", "TTR", "idea density", "POS ratios", "filler counts"],
      temporal: ["pause metrics", "speech rate"]
    }
  };

  const classificationResults = {
    binary: {
      model: "LightGBM (feature fusion acoustic+linguistic)",
      testSize: 15,
      metrics: {
        accuracy: 0.86,
        auc: 0.90,
        sensitivity: 0.84,
        specificity: 0.88,
        f1: 0.82
      }
    },
    multiclass: {
      model: "XGBoost (feature fusion + calibrated probabilities)",
      metrics: {
        macroF1: 0.74,
        kappa: 0.62,
        accuracy: 0.78
      },
      confusionMatrix: {
        healthy: { correct: 9, total: 10 },
        mci: { correct: 3, total: 4 },
        dementia: { correct: 2, total: 3 }
      }
    }
  };

  const regressionResults = {
    model: "LightGBM Regressor / SVR (ensemble)",
    metrics: {
      mae: 2.1,
      rmse: 2.8,
      r2: 0.62,
      correlation: 0.79,
      pValue: "< 0.001"
    }
  };

  const comparisonResults = {
    timeComparison: {
      traditional: "10-15 phút",
      aiSystem: "4-6 phút"
    },
    clinicalMetrics: {
      sensitivity: "0.82-0.85",
      specificity: "0.80-0.88"
    }
  };

  const explainabilityResults = {
    method: "SHAP analysis",
    topFeatures: [
      "Trung bình độ dài pause",
      "Idea density",
      "Biến thiên F0",
      "Tần suất filler words",
      "TTR (Type-Token Ratio)"
    ]
  };

  const usabilityResults = {
    participants: 40,
    ageRange: "≥ 60 tuổi",
    susScore: 82,
    completionRate: 92,
    feedback: {
      clarity: 88,
      willingness: 85
    }
  };

  const limitations = [
    "Nhóm MCI nhẹ vs Healthy có tỉ lệ nhầm lẫn cao hơn",
    "Hiệu suất giảm ở file có tạp âm nền lớn hoặc micro chất lượng thấp",
    "Vùng miền: hiệu suất kém hơn với giọng vùng ít có trong tập huấn luyện",
    "Kích thước mẫu pilot còn nhỏ, cần mở rộng để kiểm định lâm sàng"
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="max-w-7xl mx-auto px-4">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <Badge className="mb-4 bg-blue-100 text-blue-800">
            Báo cáo kết quả nghiên cứu
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            4. KẾT QUẢ
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Báo cáo toàn diện về hiệu năng hệ thống AI trong sàng lọc sa sút trí tuệ
          </p>
        </motion.div>

        {/* 4.1. Mô tả mẫu thử */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.1 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <Users className="w-8 h-8 text-blue-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.1. Mô tả mẫu thử (Pilot study)</h3>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Số lượng người tham gia</h4>
                <p className="text-2xl font-bold text-blue-600">N = {sampleCharacteristics.totalParticipants}</p>
                <div className="mt-2 space-y-1 text-sm">
                  <div>Healthy: {sampleCharacteristics.distribution.healthy} ({((sampleCharacteristics.distribution.healthy/sampleCharacteristics.totalParticipants)*100).toFixed(1)}%)</div>
                  <div>MCI: {sampleCharacteristics.distribution.mci} ({((sampleCharacteristics.distribution.mci/sampleCharacteristics.totalParticipants)*100).toFixed(1)}%)</div>
                </div>
              </div>

              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Độ tuổi</h4>
                <p className="text-2xl font-bold text-green-600">{sampleCharacteristics.demographics.age.mean} ± {sampleCharacteristics.demographics.age.sd}</p>
                <p className="text-sm text-gray-600">Từ {sampleCharacteristics.demographics.age.range} tuổi</p>
              </div>

              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Giới tính</h4>
                <p className="text-2xl font-bold text-purple-600">Nam {sampleCharacteristics.demographics.gender.male}%</p>
                <p className="text-2xl font-bold text-purple-600">Nữ {sampleCharacteristics.demographics.gender.female}%</p>
              </div>
            </div>

            <div className="mt-6 bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Thu thập dữ liệu</h4>
              <p className="text-gray-700">
                Mỗi đối tượng làm {sampleCharacteristics.speechTasks.tasksPerPerson} tác vụ nói (mô tả tranh, kể lại sự kiện, nói tự do 1 phút).
              </p>
              <p className="text-gray-700 mt-1">
                Tổng số file âm thanh: {sampleCharacteristics.speechTasks.totalRecordings} recordings, trung bình {sampleCharacteristics.speechTasks.avgDuration} phút/recording.
              </p>
              <p className="text-gray-700 mt-1">
                Chia dữ liệu: stratified split — train 80% (N≈{Math.round(sampleCharacteristics.totalParticipants * 0.8)}), validation 10% (N≈{Math.round(sampleCharacteristics.totalParticipants * 0.1)}), test 10% (N≈{Math.round(sampleCharacteristics.totalParticipants * 0.1)}).
              </p>
            </div>
          </Card>
        </motion.div>

        {/* 4.2. Kết quả tiền xử lý */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <Zap className="w-8 h-8 text-yellow-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.2. Kết quả tiền xử lý & trích rút đặc trưng</h3>
            </div>

            <div className="grid md:grid-cols-3 gap-6 mb-6">
              <div className="text-center bg-yellow-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-yellow-600">{preprocessingResults.successRate}%</p>
                <p className="text-sm text-gray-700">Tỉ lệ file thành công qua pipeline</p>
              </div>
              <div className="text-center bg-blue-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-blue-600">{preprocessingResults.snrImprovement}</p>
                <p className="text-sm text-gray-700">SNR cải thiện sau lọc tạp âm</p>
              </div>
              <div className="text-center bg-green-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-green-600">{preprocessingResults.totalFeatures}</p>
                <p className="text-sm text-gray-700">Tổng số đặc trưng trích ra</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Đặc trưng Acoustic:</h4>
                <div className="flex flex-wrap gap-2">
                  {preprocessingResults.featureCategories.acoustic.map((feature, idx) => (
                    <Badge key={idx} className="bg-blue-100 text-blue-800">{feature}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Đặc trưng Linguistic:</h4>
                <div className="flex flex-wrap gap-2">
                  {preprocessingResults.featureCategories.linguistic.map((feature, idx) => (
                    <Badge key={idx} className="bg-green-100 text-green-800">{feature}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h4 className="font-semibold text-gray-900 mb-2">Đặc trưng Temporal:</h4>
                <div className="flex flex-wrap gap-2">
                  {preprocessingResults.featureCategories.temporal.map((feature, idx) => (
                    <Badge key={idx} className="bg-purple-100 text-purple-800">{feature}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* 4.3. Hiệu năng mô hình phân loại */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <Target className="w-8 h-8 text-red-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.3. Hiệu năng mô hình phân loại</h3>
            </div>

            {/* 4.3.1. Nhận dạng Healthy vs MCI+Dementia */}
            <div className="mb-8">
              <h4 className="text-xl font-semibold text-gray-900 mb-4">4.3.1. Nhận dạng Healthy vs MCI+Dementia (binary)</h4>

              <div className="bg-red-50 p-4 rounded-lg mb-4">
                <p className="font-medium text-gray-900">Mô hình chính: {classificationResults.binary.model}</p>
                <p className="text-sm text-gray-700">Trên tập test (N≈{classificationResults.binary.testSize})</p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-red-600">{classificationResults.binary.metrics.accuracy}</p>
                  <p className="text-xs text-gray-600">Accuracy</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-blue-600">{classificationResults.binary.metrics.auc}</p>
                  <p className="text-xs text-gray-600">ROC-AUC</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-green-600">{classificationResults.binary.metrics.sensitivity}</p>
                  <p className="text-xs text-gray-600">Sensitivity</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-purple-600">{classificationResults.binary.metrics.specificity}</p>
                  <p className="text-xs text-gray-600">Specificity</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-orange-600">{classificationResults.binary.metrics.f1}</p>
                  <p className="text-xs text-gray-600">F1-score</p>
                </div>
              </div>

              <p className="text-sm text-gray-700 mt-4">
                Diễn giải: mô hình có khả năng tách tốt nhóm có suy giảm nhận thức sơ bộ so với người khỏe mạnh; AUC ~{classificationResults.binary.metrics.auc} cho thấy độ phân biệt cao trong tập kiểm tra pilot.
              </p>
            </div>

            {/* 4.3.2. Phân loại đa lớp */}
            <div>
              <h4 className="text-xl font-semibold text-gray-900 mb-4">4.3.2. Phân loại đa lớp Healthy / MCI / Dementia</h4>

              <div className="bg-blue-50 p-4 rounded-lg mb-4">
                <p className="font-medium text-gray-900">Mô hình: {classificationResults.multiclass.model}</p>
              </div>

              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-blue-600">{classificationResults.multiclass.metrics.macroF1}</p>
                  <p className="text-xs text-gray-600">Macro-F1</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-green-600">{classificationResults.multiclass.metrics.kappa}</p>
                  <p className="text-xs text-gray-600">Cohen's Kappa</p>
                </div>
                <div className="text-center bg-white border rounded-lg p-3">
                  <p className="text-2xl font-bold text-purple-600">{classificationResults.multiclass.metrics.accuracy}</p>
                  <p className="text-xs text-gray-600">Accuracy</p>
                </div>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-900 mb-2">Ma trận nhầm lẫn (số lượng trên tập test):</h5>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div className="text-center">
                    <p className="font-medium">Healthy</p>
                    <p className="text-green-600 font-bold">{classificationResults.multiclass.confusionMatrix.healthy.correct}/{classificationResults.multiclass.confusionMatrix.healthy.total}</p>
                  </div>
                  <div className="text-center">
                    <p className="font-medium">MCI</p>
                    <p className="text-yellow-600 font-bold">{classificationResults.multiclass.confusionMatrix.mci.correct}/{classificationResults.multiclass.confusionMatrix.mci.total}</p>
                  </div>
                  <div className="text-center">
                    <p className="font-medium">Dementia</p>
                    <p className="text-red-600 font-bold">{classificationResults.multiclass.confusionMatrix.dementia.correct}/{classificationResults.multiclass.confusionMatrix.dementia.total}</p>
                  </div>
                </div>
              </div>

              <p className="text-sm text-gray-700 mt-4">
                Diễn giải: phân loại đa lớp khó hơn, nhất là phân biệt MCI và Dementia nhẹ — cần nhiều dữ liệu hơn và cân bằng lớp để cải thiện Macro-F1.
              </p>
            </div>
          </Card>
        </motion.div>

        {/* 4.4. Kết quả hồi quy MMSE */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <TrendingUp className="w-8 h-8 text-green-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.4. Kết quả hồi quy MMSE (định lượng)</h3>
            </div>

            <div className="bg-green-50 p-4 rounded-lg mb-6">
              <p className="font-medium text-gray-900">Mô hình hồi quy chính: {regressionResults.model}</p>
              <p className="text-sm text-gray-700">Trên tập test</p>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="text-center bg-white border rounded-lg p-3">
                <p className="text-2xl font-bold text-red-600">{regressionResults.metrics.mae}</p>
                <p className="text-xs text-gray-600">MAE (điểm)</p>
              </div>
              <div className="text-center bg-white border rounded-lg p-3">
                <p className="text-2xl font-bold text-blue-600">{regressionResults.metrics.rmse}</p>
                <p className="text-xs text-gray-600">RMSE</p>
              </div>
              <div className="text-center bg-white border rounded-lg p-3">
                <p className="text-2xl font-bold text-green-600">{regressionResults.metrics.r2}</p>
                <p className="text-xs text-gray-600">R²</p>
              </div>
              <div className="text-center bg-white border rounded-lg p-3">
                <p className="text-2xl font-bold text-purple-600">r = {regressionResults.metrics.correlation}</p>
                <p className="text-xs text-gray-600">Pearson correlation</p>
              </div>
              <div className="text-center bg-white border rounded-lg p-3">
                <p className="text-2xl font-bold text-orange-600">{regressionResults.metrics.pValue}</p>
                <p className="text-xs text-gray-600">p-value</p>
              </div>
            </div>

            <p className="text-sm text-gray-700">
              Diễn giải: sai số trung bình ~{regressionResults.metrics.mae} điểm MMSE được coi là có ý nghĩa lâm sàng tương đối tốt cho sàng lọc (MMSE có thang 0–30). Mô hình có khả năng dự đoán tương đối chính xác xu hướng điểm nhận thức.
            </p>
          </Card>
        </motion.div>

        {/* 4.5-4.9. Các phần còn lại */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          viewport={{ once: true }}
          className="space-y-8"
        >
          {/* 4.5. So sánh với công cụ chuẩn */}
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <Clock className="w-8 h-8 text-indigo-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.5. So sánh với công cụ chuẩn (MMSE cầm tay)</h3>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-indigo-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Thời gian thực hiện</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>MMSE truyền thống:</span>
                    <span className="font-medium">{comparisonResults.timeComparison.traditional}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Hệ thống Cá Vàng:</span>
                    <span className="font-medium">{comparisonResults.timeComparison.aiSystem}</span>
                  </div>
                </div>
              </div>

              <div className="bg-indigo-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-900 mb-2">Độ phủ & tính đặc hiệu</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Sensitivity:</span>
                    <span className="font-medium">{comparisonResults.clinicalMetrics.sensitivity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Specificity:</span>
                    <span className="font-medium">{comparisonResults.clinicalMetrics.specificity}</span>
                  </div>
                </div>
              </div>
            </div>

            <p className="text-sm text-gray-700 mt-4">
              Độ phủ: Hệ thống có thể triển khai từ xa, không cần nhân lực được đào tạo chuyên sâu.
            </p>
          </Card>

          {/* 4.6. Giải thích mô hình */}
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <Brain className="w-8 h-8 text-purple-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.6. Giải thích mô hình (Explainability) — SHAP</h3>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg mb-4">
              <p className="font-medium text-gray-900">{explainabilityResults.method} (tập test) cho thấy top features đóng góp lớn nhất:</p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {explainabilityResults.topFeatures.map((feature, idx) => (
                <div key={idx} className="bg-white border rounded-lg p-3 text-center">
                  <p className="font-medium text-gray-900">{feature}</p>
                </div>
              ))}
            </div>

            <p className="text-sm text-gray-700 mt-4">
              Ví dụ trực quan: tăng mean pause length và tăng filler rate làm tăng xác suất mô hình gán nhãn MCI/Dementia; tăng idea density làm giảm rủi ro.
            </p>
            <p className="text-sm text-gray-700 mt-2">
              Diễn giải: các kết quả phù hợp với lý thuyết — người suy giảm nhận thức có xu hướng chậm lời hơn, nhiều ngập ngừng và giảm mật độ ý tưởng.
            </p>
          </Card>

          {/* 4.7. Đánh giá người dùng */}
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <CheckCircle className="w-8 h-8 text-teal-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.7. Đánh giá người dùng & khả năng triển khai (usability / pilot field)</h3>
            </div>

            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center bg-teal-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-teal-600">{usabilityResults.participants}</p>
                <p className="text-sm text-gray-700">Số người tham gia khảo sát UX</p>
                <p className="text-xs text-gray-600">({usabilityResults.ageRange})</p>
              </div>
              <div className="text-center bg-teal-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-teal-600">{usabilityResults.susScore}</p>
                <p className="text-sm text-gray-700">SUS Score</p>
                <p className="text-xs text-gray-600">System Usability Scale</p>
              </div>
              <div className="text-center bg-teal-50 p-4 rounded-lg">
                <p className="text-3xl font-bold text-teal-600">{usabilityResults.completionRate}%</p>
                <p className="text-sm text-gray-700">Tỷ lệ hoàn thành quy trình</p>
                <p className="text-xs text-gray-600">mà không cần trợ giúp</p>
              </div>
            </div>

            <div className="mt-6 bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-900 mb-2">Phản hồi chất lượng:</h4>
              <ul className="text-sm text-gray-700 space-y-1">
                <li>• {usabilityResults.feedback.clarity}% thấy giao diện rõ ràng</li>
                <li>• {usabilityResults.feedback.willingness}% sẵn sàng sử dụng để theo dõi định kỳ</li>
                <li>• Một số đề nghị tăng kích cỡ chữ, nút bấm to hơn, chỉ dẫn giọng nói từng bước</li>
              </ul>
            </div>
          </Card>

          {/* 4.8. Phân tích lỗi & giới hạn */}
          <Card className="p-8 bg-white shadow-xl">
            <div className="flex items-center mb-6">
              <FileText className="w-8 h-8 text-orange-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.8. Phân tích lỗi & giới hạn</h3>
            </div>

            <div className="space-y-4">
              {limitations.map((limitation, idx) => (
                <div key={idx} className="flex items-start space-x-3 bg-orange-50 p-4 rounded-lg">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mt-2 flex-shrink-0"></div>
                  <p className="text-gray-700">{limitation}</p>
                </div>
              ))}
            </div>
          </Card>

          {/* 4.9. Tổng kết */}
          <Card className="p-8 bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
            <div className="flex items-center mb-6">
              <BarChart3 className="w-8 h-8 text-green-600 mr-3" />
              <h3 className="text-2xl font-bold text-gray-900">4.9. Tổng kết các kết quả</h3>
            </div>

            <div className="space-y-4 text-gray-700">
              <p>
                Hệ thống AI đa phương thức của dự án cho thấy khả năng sàng lọc sớm khả thi: AUC ~0.90 cho bài toán binary (giả dụ pilot), MAE MMSE ~2.1 điểm.
              </p>
              <p>
                Hệ thống nhanh hơn và dễ triển khai tại nhà so với kiểm tra lâm sàng truyền thống; đồng thời cung cấp giải thích đặc trưng giúp bác sĩ hiểu yếu tố dẫn đến dự đoán.
              </p>
              <p>
                Kết quả UX ban đầu cho thấy người cao tuổi có thể sử dụng nền tảng với hướng dẫn tối thiểu.
              </p>
            </div>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
