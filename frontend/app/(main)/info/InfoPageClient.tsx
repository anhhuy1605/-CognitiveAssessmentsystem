"use client";

import { motion } from "framer-motion";
import HeroSection from "@/components/info/HeroSection";
import AboutProject from "@/components/info/AboutProject";
import MCIExplanation from "@/components/info/MCIExplanation";
import AITechnology from "@/components/info/AITechnology";
import ResultsMetrics from "@/components/info/ResultsMetrics";
import ComprehensiveResultsReport from "@/components/info/ComprehensiveResultsReport";
import TeamSection from "@/components/info/TeamSection";
import ContactSection from "@/components/info/ContactSection";
import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function InfoPageClient() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50">
      {/* Skip to main content for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded z-50"
      >
        Bỏ qua và chuyển đến nội dung chính
      </a>

      <main id="main-content">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <HeroSection />
          <AboutProject />
          <MCIExplanation />
          <AITechnology />
          <ResultsMetrics />
          <ComprehensiveResultsReport />
          <TeamSection />
          {/* News moved to dedicated page to keep /info concise */}
          <div className="py-8">
            <div className="max-w-7xl mx-auto px-4 text-center">
              <div className="inline-flex flex-col items-center gap-3 bg-white/70 border border-blue-200 rounded-2xl p-5">
                <p className="text-gray-700 text-sm md:text-base">Xem Tin tức & Nghiên cứu mới nhất</p>
                <Button variant="primaryOutline" asChild>
                  <Link href="/info/news">Mở trang Tin tức & Nghiên cứu</Link>
                </Button>
              </div>
            </div>
          </div>
          <ContactSection />
        </motion.div>
      </main>

      {/* Structured Data for SEO */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": "Cá Vàng: Thắp Sáng Ký Ức",
            "description": "Hệ thống AI tiên tiến phân tích giọng nói để sàng lọc sa sút trí tuệ tại nhà",
            "url": "https://cavang.info/info",
            "publisher": {
              "@type": "Organization",
              "name": "THPT Chuyên Lê Quý Đôn",
              "url": "https://thpt-lequydon-tphcm.edu.vn"
            },
            "about": [
              {
                "@type": "MedicalCondition",
                "name": "Sa sút trí tuệ",
                "alternateName": ["Dementia", "Alzheimer's disease", "MCI"]
              },
              {
                "@type": "SoftwareApplication",
                "name": "Cá Vàng AI System",
                "description": "AI system for speech analysis and dementia screening",
                "applicationCategory": "HealthcareApplication"
              }
            ],
            "mainEntity": {
              "@type": "Project",
              "name": "Cá Vàng: Thắp Sáng Ký Ức",
              "description": "AI-powered speech analysis system for dementia screening",
              "founder": {
                "@type": "Organization",
                "name": "THPT Chuyên Lê Quý Đôn"
              },
              "member": [
                {
                  "@type": "Person",
                  "name": "Trần Đức Thanh",
                  "jobTitle": "Giáo viên hướng dẫn"
                },
                {
                  "@type": "Person",
                  "name": "Lê Đình Phúc",
                  "jobTitle": "Thành viên chính"
                },
                {
                  "@type": "Person",
                  "name": "Phan Nguyễn Trà Ly",
                  "jobTitle": "Thành viên"
                }
              ]
            }
          })
        }}
      />
    </div>
  );
}
