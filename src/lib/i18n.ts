export type Locale = "en" | "zh";

export const localeNames: Record<Locale, string> = {
  en: "English",
  zh: "中文",
};

const eventTypeLabels: Record<Locale, Record<string, string>> = {
  en: {
    harsh_braking: "Harsh braking",
    harsh_acceleration: "Harsh acceleration",
    high_lateral_acceleration: "High lateral acceleration",
    sharp_yaw_motion: "Sharp yaw motion",
    unstable_speed_control: "Unstable speed control",
    late_braking_before_curve: "Late braking before curve",
    high_speed_in_curve: "High speed in curve",
    unstable_cornering: "Unstable cornering",
  },
  zh: {
    harsh_braking: "急刹车",
    harsh_acceleration: "急加速",
    high_lateral_acceleration: "横向加速度偏高",
    sharp_yaw_motion: "横摆变化过快",
    unstable_speed_control: "速度控制不稳定",
    late_braking_before_curve: "弯道前制动偏晚",
    high_speed_in_curve: "入弯速度偏高",
    unstable_cornering: "过弯稳定性不足",
  },
};

const severityLabels: Record<Locale, Record<string, string>> = {
  en: {
    low: "Low",
    medium: "Medium",
    high: "High",
  },
  zh: {
    low: "低",
    medium: "中",
    high: "高",
  },
};

const sourceLabels: Record<Locale, Record<string, string>> = {
  en: {
    loading: "Loading",
    backend: "Backend",
    fallback: "Fallback",
    sqlite: "SQLite",
    ready: "Ready",
    thinking: "Thinking",
    active: "Active",
    completed: "Completed",
    continue: "Continue",
    connected: "Connected",
    notConnected: "Not connected",
  },
  zh: {
    loading: "加载中",
    backend: "后端",
    fallback: "本地备用",
    sqlite: "SQLite",
    ready: "就绪",
    thinking: "思考中",
    active: "进行中",
    completed: "已完成",
    continue: "继续关注",
    connected: "已连接",
    notConnected: "未连接",
  },
};

export function eventTypeLabel(type: string, locale: Locale) {
  return eventTypeLabels[locale][type] ?? type.replaceAll("_", " ");
}

export function severityLabel(severity: string, locale: Locale) {
  return severityLabels[locale][severity] ?? severity;
}

export function sourceLabel(source: string, locale: Locale) {
  return sourceLabels[locale][source] ?? source;
}
