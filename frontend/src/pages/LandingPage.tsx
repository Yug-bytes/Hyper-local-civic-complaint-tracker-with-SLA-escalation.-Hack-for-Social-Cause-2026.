import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Clock,
  Send,
  Search,
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Droplets,
  Lightbulb,
  Trash2,
  HelpCircle,
  TrendingUp,
  Layers,
  ChevronRight,
  ShieldCheck,
  Building,
} from 'lucide-react'
import { useI18n } from '../lib/i18n'

interface CategoryCard {
  key: string
  titleEn: string
  titleHi: string
  deptEn: string
  deptHi: string
  sla: string
  icon: React.ReactNode
  color: string
}

export const LandingPage: React.FC = () => {
  const { language, t } = useI18n()
  const navigate = useNavigate()
  const [quickTrackId, setQuickTrackId] = useState('')

  const handleQuickTrack = (e: React.FormEvent) => {
    e.preventDefault()
    if (quickTrackId.trim()) {
      navigate(`/track?id=${encodeURIComponent(quickTrackId.trim().toUpperCase())}`)
    } else {
      navigate('/track')
    }
  }

  const categoryCards: CategoryCard[] = [
    {
      key: 'pothole',
      titleEn: 'Roads & Potholes',
      titleHi: 'सड़क व गड्ढे',
      deptEn: 'Public Works Dept (PWD)',
      deptHi: 'लोक निर्माण विभाग (PWD)',
      sla: '7 Days',
      icon: <Layers className="w-6 h-6 text-amber-600" />,
      color: 'border-amber-200 bg-amber-50/50 hover:border-amber-300',
    },
    {
      key: 'water',
      titleEn: 'Water Supply & Leaks',
      titleHi: 'जल आपूर्ति व रिसाव',
      deptEn: 'Water Supply Department',
      deptHi: 'जल आपूर्ति विभाग',
      sla: '3 Days',
      icon: <Droplets className="w-6 h-6 text-blue-600" />,
      color: 'border-blue-200 bg-blue-50/50 hover:border-blue-300',
    },
    {
      key: 'streetlight',
      titleEn: 'Streetlights & Power',
      titleHi: 'स्ट्रीटलाइट व बिजली',
      deptEn: 'Electrical Department',
      deptHi: 'विद्युत विभाग',
      sla: '5 Days',
      icon: <Lightbulb className="w-6 h-6 text-yellow-600" />,
      color: 'border-yellow-200 bg-yellow-50/50 hover:border-yellow-300',
    },
    {
      key: 'garbage',
      titleEn: 'Garbage & Sanitation',
      titleHi: 'कचरा व स्वच्छता',
      deptEn: 'Sanitation Department',
      deptHi: 'स्वच्छता विभाग',
      sla: '2 Days',
      icon: <Trash2 className="w-6 h-6 text-emerald-600" />,
      color: 'border-emerald-200 bg-emerald-50/50 hover:border-emerald-300',
    },
    {
      key: 'other',
      titleEn: 'General Grievances',
      titleHi: 'सामान्य शिकायतें',
      deptEn: 'General Administration',
      deptHi: 'सामान्य प्रशासन',
      sla: '7 Days',
      icon: <HelpCircle className="w-6 h-6 text-purple-600" />,
      color: 'border-purple-200 bg-purple-50/50 hover:border-purple-300',
    },
  ]

  const workflowSteps = [
    {
      number: '01',
      titleEn: 'Citizen Files Grievance',
      titleHi: 'नागरिक शिकायत दर्ज करते हैं',
      descEn: 'Submit photo evidence and locality in under 60 seconds. No compulsory account creation.',
      descHi: '60 सेकंड में फोटो साक्ष्य और स्थान दर्ज करें। अनिवार्य खाते की आवश्यकता नहीं।',
      icon: <Send className="w-5 h-5 text-civic" />,
    },
    {
      number: '02',
      titleEn: 'Automated SLA Clock Starts',
      titleHi: 'स्वचालित एसएलए समय शुरू',
      descEn: 'Dispatched to responsible junior officer. Strict legal turnaround timer countdown begins.',
      descHi: 'संबंधित कनिष्ठ अधिकारी को सौंपा गया। सख्त कानूनी समय-सीमा उल्टी गिनती शुरू।',
      icon: <Clock className="w-5 h-5 text-civic" />,
    },
    {
      number: '03',
      titleEn: 'Auto-Escalation If Delayed',
      titleHi: 'विलंब पर स्वचालित उच्च-अधिकारी वृद्धि',
      descEn: 'If SLA expires without resolution, complaint automatically escalates to Executive Engineer or Commissioner.',
      descHi: 'यदि समय सीमा में समाधान नहीं हुआ, तो शिकायत स्वतः वरिष्ठ अभियंता या आयुक्त को स्थानांतरित होती है।',
      icon: <AlertTriangle className="w-5 h-5 text-amber-500" />,
    },
    {
      number: '04',
      titleEn: 'Verified Public Audit',
      titleHi: 'सत्यापित सार्वजनिक ऑडिट',
      descEn: 'Resolution status and timestamp logged publicly. Total transparency, zero personal data leak.',
      descHi: 'समाधान स्थिति और समय सार्वजनिक रूप से दर्ज। पूर्ण पारदर्शिता, शून्य व्यक्तिगत डेटा लीक।',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-600" />,
    },
  ]

  return (
    <div className="space-y-16 py-6 sm:py-10">
      {/* ── HERO SECTION ── */}
      <section className="relative overflow-hidden rounded-3xl bg-gradient-to-b from-blue-50/60 via-white to-gray-50 border border-civic/15 p-6 sm:p-12 lg:p-16 shadow-xs">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-civic/10 text-civic text-xs sm:text-sm font-semibold tracking-wide">
            <span className="w-2 h-2 rounded-full bg-civic animate-pulse" />
            {t('landing_hero_badge')}
          </div>

          {/* Headline */}
          <h1 className="text-3xl sm:text-5xl lg:text-6xl font-extrabold text-ink tracking-tight leading-tight">
            {t('landing_hero_title')}
          </h1>

          {/* Subtitle */}
          <p className="text-base sm:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {t('landing_hero_sub')}
          </p>

          {/* Primary Action Buttons */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4">
            <Link
              to="/file"
              className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-xl bg-civic hover:bg-civic-hover text-white font-semibold text-base shadow-md hover:shadow-lg transition-all gap-2 group"
            >
              <span>{t('landing_cta_file')}</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              to="/track"
              className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-xl bg-white hover:bg-gray-50 text-ink border border-line font-semibold text-base shadow-xs hover:shadow transition-all gap-2"
            >
              <Search className="w-4 h-4 text-gray-500" />
              <span>{t('landing_cta_track')}</span>
            </Link>

            <Link
              to="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3.5 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold text-base transition-colors gap-2"
            >
              <BarChart3 className="w-4 h-4 text-gray-600" />
              <span>{t('landing_cta_dash')}</span>
            </Link>
          </div>

          {/* Quick Track Search Input */}
          <div className="pt-6 max-w-md mx-auto">
            <form onSubmit={handleQuickTrack} className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={quickTrackId}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setQuickTrackId(e.target.value)}
                  placeholder={t('landing_quick_track_placeholder')}
                  className="w-full pl-10 pr-3 py-2.5 bg-white border border-line rounded-xl text-sm focus:outline-hidden focus:ring-2 focus:ring-civic focus:border-transparent uppercase shadow-2xs font-mono"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2.5 bg-ink hover:bg-black text-white text-sm font-medium rounded-xl transition-colors shrink-0"
              >
                {t('check')}
              </button>
            </form>
          </div>
        </div>
      </section>

      {/* ── KEY METRICS / TRUST BANNER ── */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-2xl border border-line shadow-2xs text-center space-y-1">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-civic flex items-center justify-center mx-auto mb-2">
            <Building className="w-5 h-5" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-ink">5</p>
          <p className="text-xs sm:text-sm font-medium text-gray-500">
            {language === 'en' ? 'Municipal Depts' : 'नगर निगम विभाग'}
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-line shadow-2xs text-center space-y-1">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-2">
            <Clock className="w-5 h-5" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-ink">2 - 7</p>
          <p className="text-xs sm:text-sm font-medium text-gray-500">
            {language === 'en' ? 'Days Guaranteed SLA' : 'दिनों की गारंटीकृत SLA'}
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-line shadow-2xs text-center space-y-1">
          <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center mx-auto mb-2">
            <TrendingUp className="w-5 h-5" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-ink">Auto</p>
          <p className="text-xs sm:text-sm font-medium text-gray-500">
            {language === 'en' ? 'Hierarchy Escalation' : 'पदानुक्रमित वृद्धि'}
          </p>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-line shadow-2xs text-center space-y-1">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-2">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <p className="text-2xl sm:text-3xl font-extrabold text-ink">100%</p>
          <p className="text-xs sm:text-sm font-medium text-gray-500">
            {language === 'en' ? 'Zero-PII Public Privacy' : 'गोपनीयता संरक्षित'}
          </p>
        </div>
      </section>

      {/* ── CIVIC CATEGORIES ── */}
      <section className="space-y-6">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-ink">
            {language === 'en' ? 'What Problem Would You Like Resolved?' : 'आप किस समस्या का समाधान चाहते हैं?'}
          </h2>
          <p className="text-sm sm:text-base text-gray-500">
            {language === 'en'
              ? 'Select an issue category to launch an expedited complaint with designated department routing.'
              : 'संबंधित विभाग को त्वरित शिकायत भेजने के लिए एक समस्या श्रेणी चुनें।'}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {categoryCards.map((cat: CategoryCard) => (
            <Link
              key={cat.key}
              to={`/file?category=${cat.key}`}
              className={`p-5 rounded-2xl border transition-all hover:shadow-md flex flex-col justify-between group ${cat.color}`}
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="p-2.5 rounded-xl bg-white shadow-2xs">{cat.icon}</div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white text-gray-700 border border-gray-200">
                    SLA: {cat.sla}
                  </span>
                </div>
                <div>
                  <h3 className="font-bold text-ink text-lg group-hover:text-civic transition-colors">
                    {language === 'en' ? cat.titleEn : cat.titleHi}
                  </h3>
                  <p className="text-xs text-gray-600 mt-1">
                    {language === 'en' ? cat.deptEn : cat.deptHi}
                  </p>
                </div>
              </div>
              <div className="pt-4 mt-2 border-t border-gray-200/50 flex items-center justify-between text-xs font-semibold text-civic group-hover:translate-x-0.5 transition-transform">
                <span>{language === 'en' ? 'Report this issue' : 'यह समस्या दर्ज करें'}</span>
                <ChevronRight className="w-4 h-4" />
              </div>
            </Link>
          ))}

          {/* Track Existing Card */}
          <Link
            to="/track"
            className="p-5 rounded-2xl border border-civic/30 bg-civic/5 hover:bg-civic/10 transition-all hover:shadow-md flex flex-col justify-between group"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="p-2.5 rounded-xl bg-white shadow-2xs">
                  <Search className="w-6 h-6 text-civic" />
                </div>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white text-civic border border-civic/20">
                  {language === 'en' ? 'Instant' : 'तत्काल'}
                </span>
              </div>
              <div>
                <h3 className="font-bold text-ink text-lg group-hover:text-civic transition-colors">
                  {language === 'en' ? 'Already Filed a Complaint?' : 'पहले से शिकायत दर्ज है?'}
                </h3>
                <p className="text-xs text-gray-600 mt-1">
                  {language === 'en'
                    ? 'Check real-time status and escalation logs with your Tracking ID.'
                    : 'अपने ट्रैकिंग आईडी के साथ वास्तविक समय स्थिति और वृद्धि विवरण देखें।'}
                </p>
              </div>
            </div>
            <div className="pt-4 mt-2 border-t border-civic/10 flex items-center justify-between text-xs font-semibold text-civic group-hover:translate-x-0.5 transition-transform">
              <span>{language === 'en' ? 'Track status now' : 'अभी स्थिति ट्रैक करें'}</span>
              <ChevronRight className="w-4 h-4" />
            </div>
          </Link>
        </div>
      </section>

      {/* ── HOW SLA ESCALATION WORKS (STEP WORKFLOW) ── */}
      <section className="bg-white rounded-3xl border border-line p-6 sm:p-10 lg:p-12 shadow-xs space-y-10">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <span className="text-xs font-bold uppercase tracking-wider text-civic">
            {language === 'en' ? 'Guaranteed Administrative Protocol' : 'गारंटीकृत प्रशासनिक प्रोटोकॉल'}
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-ink">
            {t('landing_how_title')}
          </h2>
          <p className="text-sm sm:text-base text-gray-500">
            {t('landing_how_sub')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {workflowSteps.map((step) => (
            <div key={step.number} className="relative space-y-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl font-black text-gray-300 font-mono">
                  {step.number}
                </span>
                <div className="p-2 rounded-lg bg-gray-100">{step.icon}</div>
              </div>
              <h3 className="font-bold text-ink text-base">
                {language === 'en' ? step.titleEn : step.titleHi}
              </h3>
              <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">
                {language === 'en' ? step.descEn : step.descHi}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── BOTTOM CTA BANNER ── */}
      <section className="bg-slate-100 border border-slate-200 rounded-3xl p-8 sm:p-12 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="space-y-2 text-center md:text-left">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">
            {language === 'en' ? 'Ready to Fix Your Locality?' : 'अपने क्षेत्र को बेहतर बनाने के लिए तैयार हैं?'}
          </h2>
          <p className="text-slate-600 text-sm sm:text-base max-w-xl">
            {language === 'en'
              ? 'Join thousands of citizens making local governance transparent and accountable.'
              : 'हजारों नागरिकों के साथ जुड़ें और स्थानीय प्रशासन को पारदर्शी और जवाबदेह बनाएं।'}
          </p>
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/file"
            className="px-6 py-3.5 bg-civic hover:bg-civic-hover text-white font-bold rounded-xl text-sm sm:text-base transition-colors shadow-sm"
          >
            {t('landing_cta_file')}
          </Link>
          <Link
            to="/admin"
            className="px-5 py-3.5 bg-white hover:bg-slate-50 text-slate-800 font-semibold rounded-xl text-sm sm:text-base transition-colors border border-slate-300 shadow-2xs"
          >
            {language === 'en' ? 'Officer Portal' : 'अधिकारी पोर्टल'}
          </Link>
        </div>
      </section>
    </div>
  )
}
export default LandingPage
