import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";

export type Language = "en" | "ar";

const translations = {
  // Brand & Navigation
  "brand.name": { en: "IT Hub", ar: "مركز تكنولوجيا المعلومات" },
  "nav.overview": { en: "Overview", ar: "نظرة عامة" },
  "nav.servers": { en: "Servers", ar: "الخوادم" },
  "nav.network": { en: "Network", ar: "الشبكة" },
  "nav.helpdesk": { en: "Helpdesk", ar: "الدعم الفني" },
  "nav.settings": { en: "Settings", ar: "الإعدادات" },
  "nav.signout": { en: "Sign out", ar: "تسجيل الخروج" },
  "nav.skip": { en: "Skip to content", ar: "الانتقال إلى المحتوى" },
  "nav.back": { en: "Back", ar: "رجوع" },

  // Roles
  "role.executive": { en: "Executive", ar: "إداري" },
  "role.it_manager": { en: "IT Manager", ar: "مدير تكنولوجيا المعلومات" },
  "role.system_admin": { en: "System Admin", ar: "مدير أنظمة" },
  "role.network_admin": { en: "Network Admin", ar: "مدير شبكات" },
  "role.helpdesk": { en: "Helpdesk", ar: "دعم فني" },

  // Common Statuses & Messages
  "status.up": { en: "Up", ar: "يعمل" },
  "status.running": { en: "Running", ar: "يعمل" },
  "status.degraded": { en: "Degraded", ar: "أداء منخفض" },
  "status.down": { en: "Down", ar: "متوقف" },
  "status.unknown": { en: "Unknown", ar: "غير معروف" },
  "status.any": { en: "Any status", ar: "جميع الحالات" },
  "status.configured": { en: "Configured", ar: "متصل" },
  "status.not_configured": { en: "Not configured", ar: "غير مهيأ" },
  "empty.no_data": { en: "No data connected yet", ar: "لم يتم ربط أي بيانات بعد" },
  "empty.none_reported": { en: "None reported.", ar: "لا يوجد بيانات مسجلة." },
  "empty.no_devices_match": { en: "No devices match these filters.", ar: "لا توجد أجهزة مطابقة لهذه الفلاتر." },
  "empty.select_device": { en: "Select a device.", ar: "اختر جهازاً لعرض التفاصيل." },
  "loading.default": { en: "Loading IT Hub.", ar: "جاري التحميل..." },
  "loading.checking": { en: "Checking the connected sources.", ar: "جاري فحص المصادر المتصلة..." },
  "time.last_updated": { en: "Last updated", ar: "آخر تحديث" },
  "time.checked": { en: "Checked", ar: "تم الفحص" },
  "error.could_not_load": { en: "Could not load this data.", ar: "تعذر تحميل هذه البيانات." },

  // Executive Dashboard
  "exec.title": { en: "Overview", ar: "نظرة عامة" },
  "exec.monthly_report": { en: "Monthly report", ar: "التقرير الشهري" },
  "exec.preparing_report": { en: "Preparing report", ar: "جاري تجهيز التقرير..." },
  "exec.service_health": { en: "Service health", ar: "حالة الخدمات الحيوية" },
  "exec.tickets": { en: "Tickets", ar: "إحصائيات التذاكر" },
  "exec.assets": { en: "Assets", ar: "الأصول والأجهزة" },
  "exec.top_problems": { en: "Most frequent problems", ar: "المشاكل الأكثر تكراراً" },
  "exec.open_now": { en: "Open now", ar: "المفتوحة الآن" },
  "exec.closed_this_month": { en: "Closed this month", ar: "المغلقة هذا الشهر" },
  "exec.closed_last_month": { en: "Closed last month", ar: "المغلقة الشهر الماضي" },
  "exec.avg_resolution": { en: "Average resolution", ar: "متوسط وقت الحل" },
  "exec.trend.up": { en: "Up from last month", ar: "ارتفاع عن الشهر الماضي" },
  "exec.trend.down": { en: "Down from last month", ar: "انخفاض عن الشهر الماضي" },
  "exec.trend.same": { en: "Same as last month", ar: "مماثل للشهر الماضي" },
  "exec.devices": { en: "Devices", ar: "الأجهزة" },
  "exec.servers": { en: "Servers", ar: "الخوادم" },
  "exec.warranty_end": { en: "Nearing end of warranty", ar: "قريبة من انتهاء الضمان" },
  "exec.availability_30d": { en: "over the last 30 days", ar: "خلال آخر 30 يوماً" },
  "exec.sources_unconnected": {
    en: "Sources are not connected yet. Figures appear when those systems are configured.",
    ar: "الأنظمة الخارجية غير متصلة بعد. ستظهر الأرقام فور ربط تلك الأنظمة.",
  },

  // Technical Dashboards
  "tech.servers_noun": { en: "Servers", ar: "الخوادم" },
  "tech.network_noun": { en: "Network devices", ar: "أجهزة الشبكة" },
  "tech.helpdesk_noun": { en: "End-user devices", ar: "أجهزة المستخدمين" },
  "tech.issues": { en: "Issues", ar: "البلاغات" },
  "tech.search_placeholder": { en: "Search by name, hostname, or IP…", ar: "بحث بالاسم أو المضيف أو IP…" },
  "tech.all_statuses": { en: "All statuses", ar: "جميع الحالات" },
  "tech.active_filters": { en: "active filters", ar: "فلاتر نشطة" },
  "tech.hostname": { en: "Hostname", ar: "اسم المضيف" },
  "tech.ip_address": { en: "IP address", ar: "عنوان IP" },
  "tech.not_provided": { en: "Not provided", ar: "غير متوفر" },
  "tech.open_ticketing": { en: "Open in ticketing system", ar: "فتح في نظام التذاكر" },
  "tech.open_assets": { en: "Open in assets", ar: "فتح في نظام الأصول" },
  "tech.no_deep_link": { en: "No deep link is configured.", ar: "لم يتم تهيئة رابط مباشر." },

  // Settings
  "settings.title": { en: "Settings", ar: "الإعدادات" },
  "settings.connections": { en: "Connections", ar: "الاتصالات والأنظمة المتصلة" },
  "settings.loading_connections": { en: "Loading connections.", ar: "جاري تحميل الاتصالات." },
  "settings.ad_accounts_notice": {
    en: "Accounts are managed in Active Directory. Map their groups above.",
    ar: "تُدار الحسابات عبر Active Directory. قم بربط مجموعاتها أعلاه.",
  },
  "settings.no_audit": { en: "No audit events yet.", ar: "لا توجد أحداث تدقيق حتى الآن." },
  "settings.mappings": { en: "Active Directory Group Mappings", ar: "ربط مجموعات Active Directory" },
  "settings.services": { en: "Critical Services", ar: "الخدمات الحيوية" },
  "settings.accounts": { en: "Accounts", ar: "الحسابات المحلية" },
  "settings.audit": { en: "Audit log", ar: "سجل التدقيق والعمليات" },
  "settings.save": { en: "Save", ar: "حفظ" },
  "settings.add": { en: "Add", ar: "إضافة" },
  "settings.delete": { en: "Delete", ar: "حذف" },
  "settings.ad_group": { en: "Active Directory Group", ar: "مجموعة Active Directory" },
  "settings.role": { en: "Role", ar: "الدور" },
  "settings.service_name": { en: "Service name", ar: "اسم الخدمة" },
  "settings.external_key": { en: "Monitor external key", ar: "مفتاح الربط مع المراقب" },
  "settings.username": { en: "Username", ar: "اسم المستخدم" },
  "settings.display_name": { en: "Display name", ar: "الاسم المعروض" },
  "settings.password": { en: "Password", ar: "كلمة المرور" },
  "settings.active": { en: "Active", ar: "نشط" },
  "settings.disabled": { en: "Disabled", ar: "معطل" },

  // Login
  "login.title": { en: "Sign in to IT Hub", ar: "تسجيل الدخول إلى IT Hub" },
  "login.subtitle": {
    en: "Centralized operational overview and launcher for IT staff and executives.",
    ar: "منصة مركزية لإدارة ومتابعة العمليات التقنية لفرق تكنولوجيا المعلومات والإدارة.",
  },
  "login.username": { en: "Username", ar: "اسم المستخدم" },
  "login.password": { en: "Password", ar: "كلمة المرور" },
  "login.button": { en: "Sign in", ar: "تسجيل الدخول" },
  "login.signing_in": { en: "Signing in…", ar: "جاري الدخول…" },
} as const;

export type TranslationKey = keyof typeof translations;

interface I18nContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  toggleLang: () => void;
  t: (key: TranslationKey) => string;
  isRtl: boolean;
}

const I18nContext = createContext<I18nContextValue | null>(null);

const STORAGE_KEY = "it_hub_lang";

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Language>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === "ar" || saved === "en") return saved;
    } catch {}
    return "en";
  });

  const isRtl = lang === "ar";

  useEffect(() => {
    document.documentElement.setAttribute("lang", lang);
    document.documentElement.setAttribute("dir", isRtl ? "rtl" : "ltr");
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {}
  }, [lang, isRtl]);

  function setLang(next: Language) {
    setLangState(next);
  }

  function toggleLang() {
    setLangState((prev) => (prev === "en" ? "ar" : "en"));
  }

  function t(key: TranslationKey): string {
    const entry = translations[key];
    if (!entry) return key;
    return entry[lang] || entry.en || key;
  }

  return (
    <I18nContext.Provider value={{ lang, setLang, toggleLang, t, isRtl }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return ctx;
}

