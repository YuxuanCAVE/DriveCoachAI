"use client";

import { useState } from "react";
import { CoachTab } from "@/components/CoachTab";
import { DriveDataTab } from "@/components/DriveDataTab";
import { HistoryTab } from "@/components/HistoryTab";
import { SummaryTab } from "@/components/SummaryTab";
import type { Locale } from "@/lib/i18n";
import type { SampleTrip } from "@/types/driving";

const tabs = ["Summary", "Drive Data", "Coach", "History"] as const;
type Tab = (typeof tabs)[number];

const tabLabels: Record<Locale, Record<Tab, string>> = {
  en: {
    Summary: "Summary",
    "Drive Data": "Drive Data",
    Coach: "Coach",
    History: "History",
  },
  zh: {
    Summary: "概览",
    "Drive Data": "行车数据",
    Coach: "AI 教练",
    History: "历史",
  },
};

const phoneCopy: Record<Locale, { title: string; badge: string }> = {
  en: {
    title: "Post-drive review",
    badge: "Demo",
  },
  zh: {
    title: "行程复盘",
    badge: "Demo",
  },
};

export function PhoneDemo({ trip, locale }: { trip: SampleTrip; locale: Locale }) {
  const [activeTab, setActiveTab] = useState<Tab>("Summary");
  const copy = phoneCopy[locale];

  return (
    <div className="mx-auto w-full max-w-[430px] rounded-[52px] border-[10px] border-ink bg-ink p-3 shadow-phone">
      <div className="phone-safe-gradient h-[780px] overflow-hidden rounded-[38px] border border-white/70">
        <header className="flex items-center justify-between px-5 pb-3 pt-5">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">DriveCoach AI</p>
            <h2 className="mt-1 text-lg font-semibold text-ink">{copy.title}</h2>
          </div>
          <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-forest-700 shadow-sm">
            {copy.badge}
          </div>
        </header>

        <nav className="mx-4 grid grid-cols-4 rounded-2xl bg-white p-1 shadow-sm">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-xl px-2 py-2 text-[11px] font-semibold transition ${
                activeTab === tab ? "bg-forest-700 text-white shadow-sm" : "text-slate-500 hover:bg-forest-50"
              }`}
            >
              {tabLabels[locale][tab]}
            </button>
          ))}
        </nav>

        <main className="no-scrollbar h-[680px] overflow-y-auto px-4 py-4">
          {activeTab === "Summary" ? <SummaryTab trip={trip} locale={locale} /> : null}
          {activeTab === "Drive Data" ? <DriveDataTab trip={trip} locale={locale} /> : null}
          {activeTab === "Coach" ? <CoachTab trip={trip} locale={locale} /> : null}
          {activeTab === "History" ? <HistoryTab trip={trip} locale={locale} /> : null}
        </main>
      </div>
    </div>
  );
}
