import React, { createContext, useContext, useState } from 'react'


export type Language = 'en' | 'hi'

export const STRINGS: Record<Language, Record<string, string>> = {
  en: {
    app_title: 'Civic Complaint Tracker',
    app_description: 'Hyper-local civic complaint tracker with SLA escalation',
    page_citizen: 'Complaint',
    page_admin: 'Admin',
    page_dashboard: 'Dashboard',
    file_complaint: 'File a complaint',
    check_status: 'Check status',
    category: 'Category',
    select_category: 'Select a category',
    description: 'Describe the problem',
    description_help: 'What is wrong? Where exactly? Be specific.',
    locality: 'Locality (colony / ward / landmark)',
    photo: 'Photo (optional)',
    photo_warning: 'Avoid including faces, number plates, or house numbers.',
    name: 'Your name (optional)',
    phone: 'Phone number (optional, 10 digits)',
    consent: 'Name and phone are optional and only used by the area admin to follow up.',
    send_complaint: 'Send complaint',
    submitting: 'Submitting complaint...',
    complaint_saved: 'Your complaint has been sent!',
    tracking_id_label: 'Your tracking ID',
    tracking_id_instruction: 'Save this ID to check your complaint status later.',
    file_another: 'File another complaint',
    enter_tracking_id: 'Enter your tracking ID',
    tracking_id_placeholder: 'e.g. CT-261008-A7K2',
    check: 'Check status',
    status: 'Status',
    due_date: 'Due date',
    filed_on: 'Filed on',
    resolved_on: 'Resolved on',
    history: 'History',
    no_complaint_found: "We couldn't find that ID. Check it and try again.",
    overdue: 'Overdue',
    overdue_alert: 'Deadline has passed.',
    cat_pothole: 'Pothole / Road damage',
    cat_water: 'Water supply',
    cat_streetlight: 'Streetlight',
    cat_garbage: 'Garbage / Sanitation',
    cat_other: 'Other',
    status_submitted: 'Submitted',
    status_assigned: 'Assigned',
    status_in_progress: 'In progress',
    status_resolved: 'Resolved',
    error_cooldown: 'Please wait {seconds} seconds before filing another complaint.',
    error_session_limit: 'You have reached the limit of {limit} complaints for this session.',
    admin_title: 'Admin Dashboard',
    admin_login_prompt: 'Admin password',
    admin_login_btn: 'Log in',
    admin_logout_btn: 'Log out',
    admin_password_error: 'Incorrect password.',
    admin_tab_complaints: 'Complaints',
    admin_tab_analytics: 'Analytics',
    admin_filter_all: 'All',
    admin_filter_overdue: 'Show overdue only',
    admin_update_status: 'Update status',
    admin_status_note: 'Admin note (optional)',
    admin_select_complaint: 'Select a complaint to manage',
    admin_escalation_level_1: 'Overdue (Level 1)',
    admin_escalation_level_2: 'Severely Overdue (Level 2)',
    admin_no_complaints: 'No complaints match the selected filters.',
    admin_total_complaints: 'Total complaints',
    admin_open_count: 'Open',
    admin_overdue_count: 'Overdue',
    admin_avg_resolution: 'Avg resolution time',
    admin_hours: 'hours',
    admin_next_status: 'Next status',
    admin_already_resolved: 'This complaint is resolved (final state).',
    admin_reporter_info: 'Reporter details',
    admin_unlink_photo: 'Remove attached photo',
    dashboard_title: 'Public Accountability Dashboard',
    dashboard_subtitle: 'Transparent tracking of local municipal response times, resolution rates, and overdue civic issues.',
    dashboard_intro: 'How fast does each department resolve complaints in our area?',
    dashboard_rank: 'Rank',
    dashboard_updated_at: 'Updated at',
    empty_chart_message: 'No complaints recorded yet to analyze.',
    dashboard_explainer_title: 'Understanding these numbers',
    dashboard_explainer_body: "This public dashboard tracks municipal accountability without exposing citizen names, phone numbers, or private details. 'Total' is all complaints filed. 'Resolved' represents completed fixes. 'Open' complaints are currently assigned or in progress. 'Overdue' highlights complaints that have exceeded their official SLA deadline.",
    dashboard_total_filed: 'Total filed',
    dashboard_resolved: 'Resolved',
    dashboard_open: 'Open',
    dashboard_overdue: 'Overdue',
    dashboard_dept_breakdown: 'Department-wise performance',
    dashboard_chart_resolution_time: 'Average resolution time (hours)',
    dashboard_chart_status_breakdown: 'Open vs. resolved by department',
  },
  hi: {
    app_title: 'नागरिक शिकायत ट्रैकर',
    app_description: 'SLA समय-सीमा के साथ स्थानीय नागरिक शिकायत ट्रैकर',
    page_citizen: 'शिकायत',
    page_admin: 'प्रशासक',
    page_dashboard: 'डैशबोर्ड',
    file_complaint: 'शिकायत दर्ज करें',
    check_status: 'स्थिति जांचें',
    category: 'श्रेणी',
    select_category: 'श्रेणी चुनें',
    description: 'समस्या का विवरण दें',
    description_help: 'क्या समस्या है? ठीक कहाँ? कृपया स्पष्ट विवरण दें।',
    locality: 'स्थान (कॉलोनी / वार्ड / लैंडमार्क)',
    photo: 'फोटो (वैकल्पिक)',
    photo_warning: 'फोटो में चेहरे, नंबर प्लेट या घर के नंबर शामिल न करें।',
    name: 'आपका नाम (वैकल्पिक)',
    phone: 'फोन नंबर (वैकल्पिक, 10 अंक)',
    consent: 'नाम और फोन वैकल्पिक हैं और केवल क्षेत्र प्रशासक द्वारा संपर्क के लिए उपयोग किए जाएंगे।',
    send_complaint: 'शिकायत भेजें',
    submitting: 'शिकायत भेजी जा रही है...',
    complaint_saved: 'आपकी शिकायत भेज दी गई है!',
    tracking_id_label: 'आपका ट्रैकिंग आईडी',
    tracking_id_instruction: 'बाद में शिकायत की स्थिति जांचने के लिए यह आईडी सहेजें।',
    file_another: 'एक और शिकायत दर्ज करें',
    enter_tracking_id: 'अपना ट्रैकिंग आईडी दर्ज करें',
    tracking_id_placeholder: 'उदा. CT-261008-A7K2',
    check: 'स्थिति जांचें',
    status: 'स्थिति',
    due_date: 'नियत तिथि',
    filed_on: 'दर्ज की गई',
    resolved_on: 'हल की गई',
    history: 'इतिहास',
    no_complaint_found: 'यह आईडी नहीं मिली। कृपया जांचें और पुनः प्रयास करें।',
    overdue: 'विलंबित',
    overdue_alert: 'समय-सीमा समाप्त हो चुकी है।',
    cat_pothole: 'गड्ढा / सड़क टूटी',
    cat_water: 'पानी की आपूर्ति',
    cat_streetlight: 'स्ट्रीटलाइट',
    cat_garbage: 'कूड़ा / सफाई',
    cat_other: 'अन्य',
    status_submitted: 'प्रस्तुत',
    status_assigned: 'सौंपा गया',
    status_in_progress: 'प्रगति में',
    status_resolved: 'हल किया गया',
    error_cooldown: 'कृपया दूसरी शिकायत दर्ज करने से पहले {seconds} सेकंड प्रतीक्षा करें।',
    error_session_limit: 'आप इस सत्र के लिए {limit} शिकायतों की सीमा तक पहुँच चुके हैं।',
    admin_title: 'प्रशासक डैशबोर्ड',
    admin_login_prompt: 'प्रशासक पासवर्ड',
    admin_login_btn: 'लॉग इन',
    admin_logout_btn: 'लॉग आउट',
    admin_password_error: 'गलत पासवर्ड।',
    admin_tab_complaints: 'शिकायतें',
    admin_tab_analytics: 'विश्लेषण',
    admin_filter_all: 'सभी',
    admin_filter_overdue: 'केवल विलंबित दिखाएं',
    admin_update_status: 'स्थिति अपडेट करें',
    admin_status_note: 'प्रशासक नोट (वैकल्पिक)',
    admin_select_complaint: 'प्रबंधित करने के लिए शिकायत चुनें',
    admin_escalation_level_1: 'विलंबित (स्तर 1)',
    admin_escalation_level_2: 'गंभीर विलंबित (स्तर 2)',
    admin_no_complaints: 'चयनित फिल्टर से कोई शिकायत मेल नहीं खाती।',
    admin_total_complaints: 'कुल शिकायतें',
    admin_open_count: 'प्रगति में',
    admin_overdue_count: 'विलंबित',
    admin_avg_resolution: 'औसत समाधान समय',
    admin_hours: 'घंटे',
    admin_next_status: 'अगली स्थिति',
    admin_already_resolved: 'यह शिकायत हल हो चुकी है (अंतिम स्थिति)।',
    admin_reporter_info: 'शिकायतकर्ता का विवरण',
    admin_unlink_photo: 'संलग्न फोटो हटाएं',
    dashboard_title: 'सार्वजनिक जवाबदेही डैशबोर्ड',
    dashboard_subtitle: 'स्थानीय नगरपालिका प्रतिक्रिया समय, समाधान दर और विलंबित समस्याओं का पारदर्शी रिकॉर्ड।',
    dashboard_intro: 'हमारे क्षेत्र में प्रत्येक विभाग कितनी तेजी से शिकायतों का समाधान करता है?',
    dashboard_rank: 'स्थान',
    dashboard_updated_at: 'अंतिम अपडेट',
    empty_chart_message: 'विश्लेषण के लिए अभी कोई शिकायत दर्ज नहीं है।',
    dashboard_explainer_title: 'इन आंकड़ों को कैसे समझें',
    dashboard_explainer_body: "यह सार्वजनिक डैशबोर्ड बिना किसी नागरिक का नाम, फोन या निजी विवरण दिखाए नगरपालिका के प्रदर्शन को ट्रैक करता है। 'कुल' दर्ज की गई सभी शिकायतें हैं। 'हल किया गया' पूरा हुआ काम है। 'प्रगति में' वर्तमान में चालू शिकायतें हैं। 'विलंबित' वे शिकायतें हैं जो अपनी तय समय-सीमा (SLA) पार कर चुकी हैं।",
    dashboard_total_filed: 'कुल दर्ज',
    dashboard_resolved: 'हल की गई',
    dashboard_open: 'प्रगति में',
    dashboard_overdue: 'विलंबित',
    dashboard_dept_breakdown: 'विभाग-वार प्रदर्शन',
    dashboard_chart_resolution_time: 'औसत समाधान समय (घंटे)',
    dashboard_chart_status_breakdown: 'विभाग-वार स्थिति (प्रगति में बनाम हल)',
  },
}

export const CATEGORY_STRING_KEYS: Record<string, string> = {
  pothole: 'cat_pothole',
  water: 'cat_water',
  streetlight: 'cat_streetlight',
  garbage: 'cat_garbage',
  other: 'cat_other',
}

export const STATUS_STRING_KEYS: Record<string, string> = {
  submitted: 'status_submitted',
  assigned: 'status_assigned',
  in_progress: 'status_in_progress',
  resolved: 'status_resolved',
}

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string, replacements?: Record<string, string | number>) => string
}

const I18nContext = createContext<I18nContextType | null>(null)

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    return (localStorage.getItem('civic_lang') as Language) || 'en'
  })

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('civic_lang', lang)
  }

  const t = (key: string, replacements?: Record<string, string | number>): string => {
    const langDict = STRINGS[language] || STRINGS.en
    let str = langDict[key] || STRINGS.en[key] || key

    if (replacements) {
      for (const [k, v] of Object.entries(replacements)) {
        str = str.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v))
      }
    }
    return str
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (!context) {
    throw new Error('useI18n must be used within an I18nProvider')
  }
  return context
}
