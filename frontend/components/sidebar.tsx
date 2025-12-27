'use client';

import {cn} from "@/lib/utils"
import Image from "next/image";
import Link from "next/link";
import { SidebarItem } from "./sidebar-item";
import { useLanguage } from "@/contexts/LanguageContext";

type Props = {
    className?: string;
}

export const Sidebar = ({ className }: Props) => {
  const { t } = useLanguage();

  return (
  <div
    className={cn(
      "flex h-screen lg:w-[256px] lg:fixed lg:left-0 lg:top-0 px-3 py-5 border-r-0 flex-col items-start justify-start rounded-3xl bg-gradient-to-b from-amber-50 via-orange-50 to-yellow-50 backdrop-blur-md shadow-xl gap-3 z-40",
      className
    )}
  >
    <Link href="/menu" className="text-lg font-semibold mb-4 w-full">
      <div className="pt-3 pl-2 pb-4 flex items-center gap-x-3">
        <Image src="/mascot.svg" alt="Mascot" width={44} height={44} className="rounded-2xl shadow" />
        <h1 className="text-2xl font-extrabold text-amber-700 tracking-wide">
          {t('app_title')}
        </h1>
      </div>
    </Link>
    <div className="flex flex-col w-full divide-y divide-amber-100/70 rounded-3xl overflow-hidden">
      <SidebarItem label={t('home')} iconSrc="/hero.svg" href="/menu" />
      <SidebarItem label={t('cognitive_assessment')} iconSrc="/brain.svg" href="/cognitive-assessment" />
      <SidebarItem label="🐟 Cá Vàng MMSE" iconSrc="/brain.svg" href="/mmse-chatbot" />
      <SidebarItem label={t('results')} iconSrc="/leaderboard.svg" href="/stats" />
      <SidebarItem label={t('about')} iconSrc="/info.svg" href="/info" />
      <SidebarItem label={t('news_research')} iconSrc="/newspaper.svg" href="/info/news" />
      <SidebarItem label={t('profile')} iconSrc="/profile.svg" href="/user-profile" />
      <SidebarItem label={t('settings')} iconSrc="/set.svg" href="/settings" />
    </div>
  </div>
);
};

