"use client";

import { useState } from "react";
import { CoachTab } from "@/components/CoachTab";
import { DriveDataTab } from "@/components/DriveDataTab";
import { HistoryTab } from "@/components/HistoryTab";
import { SummaryTab } from "@/components/SummaryTab";
import type { SampleTrip } from "@/types/driving";

const tabs = [
  { key: "Summary", label: "Summary" },
  { key: "Drive Data", label: "Drive Data" },
  { key: "Coach", label: "Coach" },
  { key: "History", label: "History" },
] as const;
type Tab = (typeof tabs)[number]["key"];

export function PhoneDemo({ trip }: { trip: SampleTrip }) {
  const [activeTab, setActiveTab] = useState<Tab>("Summary");

  return (
    <div className="mx-auto w-full max-w-[430px] rounded-[52px] border-[10px] border-ink bg-ink p-3 shadow-phone">
      <div className="phone-safe-gradient h-[780px] overflow-hidden rounded-[38px] border border-white/70">
        <header className="flex items-center justify-between px-5 pb-3 pt-5">
          <div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-forest-700">DriveCoach AI</p>
            <h2 className="mt-1 text-lg font-semibold text-ink">Post-drive review</h2>
          </div>
          <div className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-forest-700 shadow-sm">
            Demo
          </div>
        </header>

        <nav className="mx-4 grid grid-cols-4 rounded-2xl bg-white p-1 shadow-sm">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-xl px-2 py-2 text-[11px] font-semibold transition ${
                activeTab === tab.key ? "bg-forest-700 text-white shadow-sm" : "text-slate-500 hover:bg-forest-50"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <main className="no-scrollbar h-[680px] overflow-y-auto px-4 py-4">
          {activeTab === "Summary" ? <SummaryTab trip={trip} /> : null}
          {activeTab === "Drive Data" ? <DriveDataTab trip={trip} /> : null}
          {activeTab === "Coach" ? <CoachTab trip={trip} /> : null}
          {activeTab === "History" ? <HistoryTab trip={trip} /> : null}
        </main>
      </div>
    </div>
  );
}
