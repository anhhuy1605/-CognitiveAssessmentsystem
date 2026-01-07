"use client";

import React, { useEffect, useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Header } from "./header";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { ProgressBar } from "@/components/ui/progressbar";
import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { useLanguage } from "@/contexts/LanguageContext";
import { Fish, Waves, Shell } from "lucide-react";


interface MenuItem {
  href: string;
  bgColor?: string;
  color?: string;
  icon?: string;
  title: string;
  description?: string;
}

const getMenuItems = (t: (key: string) => string): MenuItem[] => [
  {
    href: "/cognitive-assessment",
    title: t("memory_test"),
    description: t("memory_test_desc"),
    icon: "/brain.svg",
    bgColor: "bg-white"
  },
  {
    href: "/results/comprehensive",
    title: "Báo Cáo Chi Tiết",
    description: "Xem kết quả đánh giá đầy đủ với SHAP, citations",
    icon: "/brain.svg",
    bgColor: "bg-white"
  },
  {
    href: "/stats",
    title: t("statistics"),
    description: t("statistics_desc"),
    icon: "/leaderboard.svg",
    bgColor: "bg-white"
  },
  {
    href: "/info",
    title: t("information"),
    description: t("information_desc"),
    icon: "/inf.svg",
    bgColor: "bg-white"
  },
  {
    href: "/profile",
    title: t("profile"),
    description: t("profile_desc"),
    icon: "/profile.svg",
    bgColor: "bg-white"
  },
  {
    href: "/settings",
    title: t("settings"),
    description: t("settings_desc"),
    icon: "/set.svg",
    bgColor: "bg-white"
  },
  {
    href: "/mmse-chatbot-v2",
    title: "MMSE Chatbot V2",
    description: "Phiên bản chatbot MMSE được cải tiến với architecture mới",
    icon: "/brain.svg",
    bgColor: "bg-white"
  }
];

// Xóa progress mẫu và dùng state từ API
// const progress = { avrg_mmsepoint: 28, points: 120, streak: 5 };

// Progress status based on 30 scale
const getProgressStatus30 = (score30: number, t: (key: string) => string) => {
  if (score30 >= 24) { // 80% of 30 = 24
    return { icon: "✅", text: t("memory_good"), bgClass: "bg-green-500", textClass: "text-green-700" };
  } else if (score30 >= 18) { // 60% of 30 = 18
    return { icon: "⚠️", text: t("needs_monitoring"), bgClass: "bg-yellow-400", textClass: "text-yellow-700" };
  } else if (score30 >= 12) { // 40% of 30 = 12
    return { icon: "❗", text: t("needs_intervention"), bgClass: "bg-orange-500", textClass: "text-orange-700" };
  } else {
    return { icon: "❌", text: t("needs_special_evaluation"), bgClass: "bg-red-500", textClass: "text-red-700" };
  }
};

interface NewsItem {
  id: string;
  title: string;
  url: string;
  source: string;
  publishedAt?: string;
  abstract?: string;
  category?: string;
}

export default function MenuPage() {
  const { t } = useLanguage();
  const menuItems = useMemo(() => getMenuItems(t), [t]);

  const [latestNews, setLatestNews] = useState<NewsItem | null>(null);
  const [newsLoading, setNewsLoading] = useState(true);
  const [newsSummary, setNewsSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  // Function to highlight health keywords
  const highlightKeywords = (text: string) => {
    const keywords = [
      'ung thư', 'tầm soát ung thư', 'sức khỏe phụ khoa', 'tim mạch', 'đái tháo đường',
      'huyết áp', 'cholesterol', 'béo phì', 'stress', 'trầm cảm', 'lo âu',
      'trí nhớ', 'suy giảm nhận thức', 'Alzheimer', 'Parkinson', 'đột quỵ',
      'vaccine', 'tiêm chủng', 'dinh dưỡng', 'tập thể dục', 'yoga', 'meditation'
    ];

    let highlightedText = text;
    keywords.forEach(keyword => {
      const regex = new RegExp(`(${keyword})`, 'gi');
      highlightedText = highlightedText.replace(regex, '<mark class="bg-yellow-100 text-red-600 px-1 rounded">$1</mark>');
    });

    return highlightedText;
  };

  useEffect(() => {
    const loadLatestNews = async () => {
      try {
        const response = await fetch('/api/news/feeds');
        if (response.ok) {
          const data = await response.json();
          if (data.success && data.items && data.items.length > 0) {
            // Get the latest news item
            const news = data.items[0];
            setLatestNews(news);

            // Fetch and summarize the article content
            await fetchAndSummarizeArticle(news);
          }
        }
      } catch (e) {
        console.warn('Failed to load latest news:', e);
      } finally {
        setNewsLoading(false);
      }
    };

    const fetchAndSummarizeArticle = async (news: NewsItem) => {
      try {
        setSummaryLoading(true);

        // First, fetch the article content
        const contentResponse = await fetch(`/api/news/fetch-content?url=${encodeURIComponent(news.url)}`);
        if (!contentResponse.ok) {
          console.warn('Failed to fetch article content');
          return;
        }

        const contentData = await contentResponse.json();
        if (!contentData.success || !contentData.content) {
          console.warn('No content available for summarization');
              return;
            }

        // Then, summarize the content using GPT-4o
        const summaryResponse = await fetch('/api/news/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            content: contentData.content,
            title: news.title,
            source: news.source
          })
        });

        if (summaryResponse.ok) {
          const summaryData = await summaryResponse.json();
          if (summaryData.success && summaryData.summary) {
            setNewsSummary(summaryData.summary);
          }
        }
      } catch (e) {
        console.warn('Failed to fetch and summarize article:', e);
      } finally {
        setSummaryLoading(false);
      }
    };

    loadLatestNews();
  }, []);


  return (
    <div className="min-h-screen max-h-[150vh] w-full overflow-auto relative" style={{
      background: 'linear-gradient(135deg, #FEF3E2 0%, #FAE6D0 50%, #F5D7BE 100%)'
    }}>
      {/* Underwater background decorations */}
      <div className="absolute inset-0">
        <div className="absolute top-20 right-20 animate-bounce" style={{ color: '#F4A261', opacity: 0.1 }}>
          <Fish className="w-16 h-16 rotate-12" />
        </div>
        <div className="absolute bottom-40 left-20 animate-pulse" style={{ color: '#E88D4D', opacity: 0.1 }}>
          <Shell className="w-12 h-12" />
        </div>
        <div className="absolute top-1/3 right-40" style={{ color: '#E67635', opacity: 0.08 }}>
          <Waves className="w-14 h-14 animate-pulse" />
        </div>
        <div className="absolute top-60 left-40 animate-bounce" style={{ color: '#D96B2F', opacity: 0.12 }}>
          <Fish className="w-8 h-8 -rotate-45" />
        </div>
        <div className="absolute bottom-60 right-60 animate-pulse" style={{ color: '#B8763E', opacity: 0.1 }}>
          <Shell className="w-10 h-10 rotate-180" />
        </div>
        {/* Floating bubbles */}
        <div className="absolute top-32 right-1/3 w-3 h-3 bg-white/30 rounded-full animate-bounce"></div>
        <div className="absolute top-1/2 left-1/4 w-2 h-2 bg-white/25 rounded-full animate-bounce" style={{animationDelay: '0.5s'}}></div>
        <div className="absolute bottom-1/3 right-1/4 w-4 h-4 bg-white/35 rounded-full animate-bounce" style={{animationDelay: '1s'}}></div>
        <div className="absolute top-3/4 left-1/2 w-2 h-2 bg-white/20 rounded-full animate-bounce" style={{animationDelay: '1.5s'}}></div>
      </div>

      <Header />

      <motion.div
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-5xl mx-auto mb-4 sm:mb-8 relative z-10 px-3 sm:px-4"
      >
        <div className="text-center mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold drop-shadow" style={{ color: '#B8763E' }}>Cá Vàng hihi</h2>
        </div>
        <Card variant="floating" className="flex flex-col sm:flex-row items-center gap-6 sm:gap-8 p-5 sm:p-6">
          <div className="flex flex-col items-center gap-2 relative">
            <div className="relative">
              <Avatar src="/mascot.svg" alt="Mascot" size={80} />
              {/* Glowing effect */}
              <div className="absolute inset-0 rounded-full opacity-30 animate-pulse" style={{
                background: 'linear-gradient(135deg, #F4A261 0%, #E88D4D 100%)'
              }}></div>
            </div>
          </div>

          <div className="flex-1 w-full flex flex-col gap-4">
            {newsLoading ? (
              <div className="text-center py-4">
                <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-amber-600"></div>
                <div className="text-sm mt-2" style={{ color: '#8B6D57' }}>Đang tải tin tức...</div>
              </div>
            ) : latestNews ? (
              <Link href={`/info/news?url=${encodeURIComponent(latestNews.url)}`} className="block space-y-3 hover:opacity-80 transition-opacity">
                <div className="text-center cursor-pointer">
                  <div className="text-sm font-medium mb-2" style={{ color: '#B8763E' }}>
                    {latestNews.source}
                  </div>
                  <div className="text-sm sm:text-base leading-tight overflow-hidden" style={{
                    color: '#8B6D57',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    maxHeight: '3rem'
                  }}>
                    {latestNews.title}
                  </div>
                  {latestNews.publishedAt && (
                    <div className="text-xs mt-2" style={{ color: '#8B6D57' }}>
                      {new Date(latestNews.publishedAt).toLocaleDateString('vi-VN')}
                    </div>
                  )}
                </div>
              </Link>
            ) : (
              <div className="text-center py-4">
                <div className="text-sm" style={{ color: '#8B6D57' }}>Không có tin tức mới</div>
            </div>
            )}

            {/* News Summary */}
            <div className="mt-6">
              {summaryLoading ? (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <div className="flex items-center justify-center space-x-3">
                    <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-500 border-t-transparent"></div>
                    <div className="text-gray-600">Đang phân tích tin tức...</div>
                  </div>
                </div>
              ) : newsSummary && latestNews ? (
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                  {/* Header with title and source */}
                  <div className="p-6 border-b border-gray-100">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-800 leading-tight mb-2">
                          {latestNews.title}
                        </h3>
                        <div className="flex items-center space-x-2">
                          <div className="flex items-center space-x-1 text-gray-600">
                            <svg className="w-4 h-4 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                            </svg>
                            <span className="text-sm font-medium">{latestNews.source}</span>
                          </div>
                          {latestNews.publishedAt && (
                            <span className="text-xs text-gray-500">
                              {new Date(latestNews.publishedAt).toLocaleDateString('vi-VN')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Summary content */}
                  <div className="p-6">
                    <div className="bg-[#E6F4F1] rounded-xl p-4 mb-4">
                      <div
                        className="text-base leading-relaxed text-gray-800"
                        dangerouslySetInnerHTML={{ __html: highlightKeywords(newsSummary) }}
                      />
                    </div>

                    {/* Read more button */}
                    <div className="flex justify-end">
                      <a
                        href={`/info/news?url=${encodeURIComponent(latestNews.url)}`}
                        className="inline-flex items-center space-x-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-full hover:bg-gray-100 transition-colors duration-200"
                      >
                        <span>Đọc thêm</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </a>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-white rounded-2xl shadow-lg p-6">
                  <div className="text-center">
                    <div className="text-gray-400 mb-3">
                      <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                    </div>
                    <div className="text-gray-600 font-medium">Không có tin tức</div>
                    <div className="text-sm text-gray-500 mt-1">Không thể tải tin tức mới</div>
                  </div>
                </div>
              )}
            </div>

          </div>
        </Card>
      </motion.div>

      {/* Menu Grid */}
      <div className="w-full max-w-6xl mx-auto px-2 sm:px-3 lg:px-4 pb-16 grid grid-cols-1 xs:grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2 sm:gap-3 lg:gap-4 relative z-10">
        {menuItems.map((item, index) => (
          <motion.div key={index} whileHover={{ scale: 1.05, y: -5 }} transition={{ type: "spring", stiffness: 200 }}>
            <Link href={item.href}>
              <Card variant="floating" className="h-full flex flex-col p-3 sm:p-4 lg:p-5">
                <div className="relative rounded-2xl overflow-hidden mb-3">
                  <div className="absolute inset-0" style={{
                    background: 'linear-gradient(135deg, #FAE6D0 0%, #F5D7BE 100%)'
                  }} />
                  <div className="relative z-10 flex items-center justify-center py-4 sm:py-6 lg:py-8">
                    <Image src={item.icon || "/mascot.svg"} alt={item.title} width={60} height={60} className="w-12 h-12 sm:w-16 sm:h-16 lg:w-20 lg:h-20" />
                  </div>
                </div>
                <h3 className="font-extrabold text-base sm:text-lg lg:text-xl mb-1 text-left" style={{ color: '#B8763E' }}>{item.title}</h3>
                <p className="text-xs sm:text-sm text-left flex-1" style={{ color: '#8B6D57' }}>{item.description}</p>
                <div className="mt-2 flex items-center gap-1">
                  <span className="inline-block w-3 h-3 sm:w-4 sm:h-4 rounded-full" style={{ backgroundColor: '#F4A261' }} />
                  <span className="inline-block w-3 h-3 sm:w-4 sm:h-4 rounded-full" style={{ backgroundColor: '#E88D4D' }} />
                  <span className="inline-block w-3 h-3 sm:w-4 sm:h-4 rounded-full" style={{ backgroundColor: '#E67635' }} />
                </div>
              </Card>
            </Link>
          </motion.div>
        ))}
      </div>

     
    </div>
  );
}
