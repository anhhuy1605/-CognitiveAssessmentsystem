"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  TrendingUp,
  Target,
  CheckCircle,
  Clock,
  BarChart3,
  Zap,
  Users
} from "lucide-react";

export default function ResultsMetrics() {
  const currentMetrics = [
    {
      metric: "Accuracy",
      value: 81.7,
      target: 85,
      status: "near-target",
      description: "Độ chính xác tổng thể của hệ thống AI (dựa trên 237 samples thực tế)",
      icon: Target
    },
    {
      metric: "MAE",
      value: 3.83,
      target: 4.0,
      status: "target-met",
      description: "Sai số tuyệt đối trung bình (điểm MMSE) từ Random Forest Regressor",
      icon: TrendingUp
    },
    {
      metric: "Completion Rate",
      value: 95.8,
      target: 90,
      status: "target-met",
      description: "Tỷ lệ hoàn thành đánh giá thành công",
      icon: CheckCircle
    },
    {
      metric: "Processing Time",
      value: 32.0,
      target: 30,
      status: "near-target",
      description: "Thời gian xử lý trung bình (giây) bao gồm AI inference",
      icon: Clock
    }
  ];

  const processingTime = {
    current: 32,
    target: 25,
    improvement: "21% faster"
  };

  const roadmapPhases = [
    {
      phase: "Phase A",
      name: "Datasets công khai",
      status: "completed",
      description: "DementiaBank, ADReSS Challenge 2020-2021",
      datasets: ["DementiaBank", "ADReSS 2020", "ADReSS 2021"],
      completion: 100
    },
    {
      phase: "Phase B",
      name: "Thu thập dữ liệu Việt Nam",
      status: "completed",
      description: "Pilot study: 237 samples thực tế từ người Việt",
      target: "100-250 người",
      completion: 100 // 237 samples đã thu thập
    },
    {
      phase: "Phase C",
      name: "Validation đa trung tâm",
      status: "in-progress",
      description: "Hợp tác với bệnh viện >500 người (6-12 tháng)",
      target: ">500 người",
      completion: 15
    }
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800";
      case "in-progress":
        return "bg-blue-100 text-blue-800";
      case "planned":
        return "bg-gray-100 text-gray-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getMetricStatusColor = (status: string) => {
    switch (status) {
      case "near-target":
        return "text-amber-700";
      case "improving":
        return "text-blue-700";
      case "target-met":
        return "text-green-700";
      default:
        return "text-gray-700";
    }
  };

  const getMetricBadgeClass = (status: string) => {
    switch (status) {
      case "near-target":
        return "bg-amber-100 text-amber-800 border border-amber-200";
      case "improving":
        return "bg-blue-100 text-blue-800 border border-blue-200";
      case "target-met":
        return "bg-green-100 text-green-800 border border-green-200";
      default:
        return "bg-gray-100 text-gray-800 border border-gray-200";
    }
  };

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
          <Badge  className="mb-4 bg-green-100 text-green-800">
            Kết quả và Độ tin cậy
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
            Kết quả thực tế từ dữ liệu Việt Nam
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Hệ thống AI đạt độ chính xác 81.7% trên 237 samples thực tế từ người Việt, MAE 3.83 điểm MMSE, completion rate 95.8%
          </p>
        </motion.div>

        {/* Current Performance Metrics */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          viewport={{ once: true }}
          className="mb-16"
        >
          <h3 className="text-2xl md:text-3xl font-bold text-center text-gray-900 mb-8 md:mb-12">
            Hiệu năng hiện tại
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {currentMetrics.map((metric, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
              >
                <Card className="p-4 md:p-5 hover:shadow-xl transition-all duration-300 border border-gray-200 bg-white">
                  <div className="flex items-center justify-between mb-3 md:mb-4">
                    <metric.icon className={`w-6 h-6 md:w-8 md:h-8 ${getMetricStatusColor(metric.status)}`} />
                    <Badge className={getMetricBadgeClass(metric.status)}>
                      {metric.status === "near-target" ? "Gần đạt" : "Đang cải thiện"}
                    </Badge>
                  </div>

                  <h4 className="text-base md:text-lg font-semibold text-gray-900 mb-1 md:mb-2">{metric.metric}</h4>
                  <p className="text-gray-600 text-xs md:text-sm mb-3 md:mb-4">{metric.description}</p>

                  <div className="space-y-2">
                    <div className="flex justify-between text-xs md:text-sm">
                      <span>Hiện tại</span>
                      <span className="font-semibold">{metric.value}{metric.metric === "MAE" ? "" : "%"}</span>
                    </div>
                    <Progress value={(metric.value / metric.target) * 100} className="h-1.5 md:h-2" />

                    <div className="flex justify-between text-xs md:text-sm text-gray-500">
                      <span>Mục tiêu</span>
                      <span>{metric.target}{metric.metric === "MAE" ? "" : "%"}</span>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>


        {/* Validation Roadmap */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          viewport={{ once: true }}
        >
          <h3 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Lộ trình Validation
          </h3>

          <div className="space-y-8">
            {roadmapPhases.map((phase, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: index % 2 === 0 ? -100 : 100 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                viewport={{ once: true }}
              >
                <Card className="p-6 hover:shadow-lg transition-shadow">
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between">
                    <div className="flex-1 mb-4 lg:mb-0">
                      <div className="flex items-center mb-3">
                        <Badge className={`mr-3 ${getStatusColor(phase.status)}`}>
                          {phase.status === "completed" ? "✅" :
                           phase.status === "in-progress" ? "🔄" : "📋"} {phase.phase}
                        </Badge>
                        <h4 className="text-xl font-semibold text-gray-900">{phase.name}</h4>
                      </div>

                      <p className="text-gray-600 mb-4">{phase.description}</p>

                      {phase.datasets && (
                        <div className="flex flex-wrap gap-2">
                          {phase.datasets.map((dataset, datasetIndex) => (
                            <Badge key={datasetIndex}  className="bg-blue-50 text-blue-700">
                              {dataset}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {phase.target && (
                        <div className="text-sm text-gray-600">
                          Mục tiêu: <span className="font-semibold text-gray-900">{phase.target}</span>
                        </div>
                      )}
                    </div>

                    <div className="lg:w-64">
                      <div className="flex justify-between text-sm text-gray-600 mb-2">
                        <span>Tiến độ</span>
                        <span>{phase.completion}%</span>
                      </div>
                      <Progress value={phase.completion} className="h-3" />

                      <div className="mt-2 text-xs text-gray-500 text-center">
                        {phase.status === "completed" ? "Hoàn thành" :
                         phase.status === "in-progress" ? "Đang thực hiện" : "Kế hoạch"}
                      </div>
                    </div>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Trust Signals */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          className="mt-16"
        >
          <Card className="p-8 bg-gradient-to-r from-green-50 to-blue-50 border-2 border-green-200">
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-2xl font-bold text-gray-900 mb-4">
                Độ tin cậy dựa trên dữ liệu Việt Nam thực tế
              </h3>
              <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto text-left">
                <div className="text-center">
                  <Users className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                  <h4 className="font-semibold text-gray-900 mb-1">Dữ liệu thực tế</h4>
                  <p className="text-sm text-gray-600">237 samples từ người Việt (122 MCI/115 Healthy), độ tuổi 60-89</p>
                </div>
                <div className="text-center">
                  <BarChart3 className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                  <h4 className="font-semibold text-gray-900 mb-1">Hiệu năng lâm sàng</h4>
                  <p className="text-sm text-gray-600">MAE 3.83 điểm MMSE (trong phạm vi chấp nhận được), R² = 0.942</p>
                </div>
                <div className="text-center">
                  <Target className="w-8 h-8 text-green-600 mx-auto mb-2" />
                  <h4 className="font-semibold text-gray-900 mb-1">Sẵn sàng triển khai</h4>
                  <p className="text-sm text-gray-600">Đã qua validation với dữ liệu Việt Nam, sẵn sàng pilot deployment</p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </section>
  );
}
