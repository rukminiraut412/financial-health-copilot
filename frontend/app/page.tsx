'use client'

import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Area, AreaChart, Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import {
  ArrowUpRight, BarChart3, Bell, Bot, Check, ChevronRight, CircleDollarSign,
  FileUp, Home, Lightbulb, Loader2, Menu, MessageCircle, MoreHorizontal,
  PiggyBank, ReceiptIndianRupee, ShieldCheck, Sparkles, Target, TrendingDown,
  TrendingUp, Upload, Wallet, X, Zap, AlertCircle, Info,
} from 'lucide-react'
import {
  analyzeCsv,
  getSampleAnalysis,
  sendCopilotMessage,
  type AnalysisResponse,
  type ActionItem,
  type AnomalyItem,
  type SubscriptionItem,
  type CategoryBudgetStatus,
  type MonthlyTrend,
} from '@/services/api'

type Page = 'dashboard' | 'upload' | 'copilot'

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'upload', label: 'Upload data', icon: FileUp },
  { id: 'copilot', label: 'AI Copilot', icon: Bot },
]

const pieColors = ['#2f6b57', '#d6924a', '#7e9f91', '#aabfb4', '#bf735d', '#557b9a', '#8c7355', '#4e7f86']

// India-focused INR currency formatting
const inrFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const money = (value: number | null | undefined): string => inrFormatter.format(Number(value || 0))

function getGreeting(hour: number): string {
  if (hour >= 5 && hour < 12) return 'Good Morning'
  if (hour >= 12 && hour < 17) return 'Good Afternoon'
  if (hour >= 17 && hour < 21) return 'Good Evening'
  return 'Good Night'
}

function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-[#e5e9e4] bg-white shadow-[0_8px_30px_rgba(36,62,49,0.04)] ${className}`}>
      {children}
    </section>
  )
}

function SectionHeading({
  eyebrow,
  title,
  action,
  onAction,
}: {
  eyebrow?: string
  title: string
  action?: string
  onAction?: () => void
}) {
  return (
    <div className="mb-5 flex items-end justify-between">
      <div>
        {eyebrow && <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.16em] text-[#2f6b57]">{eyebrow}</p>}
        <h2 className="font-serif text-xl font-semibold tracking-tight text-[#18352b]">{title}</h2>
      </div>
      {action && (
        <button
          type="button"
          onClick={onAction}
          className="flex items-center gap-1 text-sm font-semibold text-[#2f6b57] hover:underline"
        >
          {action}
          <ChevronRight className="size-4" />
        </button>
      )}
    </div>
  )
}

function Stat({
  label,
  value,
  icon: Icon,
  trend,
  tone = 'green',
}: {
  label: string
  value: string
  icon: React.ElementType
  trend?: string
  tone?: 'green' | 'amber' | 'blue'
}) {
  return (
    <Card className="p-5">
      <div className="mb-5 flex items-center justify-between">
        <div
          className={`flex size-10 items-center justify-center rounded-xl ${
            tone === 'amber'
              ? 'bg-[#fff5e7] text-[#b87527]'
              : tone === 'blue'
              ? 'bg-[#edf4f5] text-[#4e7f86]'
              : 'bg-[#eaf3ed] text-[#2f6b57]'
          }`}
        >
          <Icon className="size-5" />
        </div>
        {trend && (
          <span className="flex items-center gap-1 rounded-full bg-[#edf7ef] px-2 py-1 text-xs font-semibold text-[#3b825b]">
            <TrendingUp className="size-3" />
            {trend}
          </span>
        )}
      </div>
      <p className="text-sm text-[#718078]">{label}</p>
      <p className="mt-1 text-2xl font-bold tracking-tight text-[#18352b]">{value}</p>
    </Card>
  )
}

/**
 * Empty dashboard state displayed when no transaction data has been uploaded yet.
 */
function DashboardEmptyState({
  greeting,
  userName,
  formattedDate,
  setPage,
  onExploreDemo,
  demoLoading,
  demoError,
}: {
  greeting: string
  userName: string
  formattedDate: string
  setPage: (p: Page) => void
  onExploreDemo: () => void
  demoLoading: boolean
  demoError: string
}) {
  return (
    <div className="mx-auto max-w-[1440px] px-5 py-8 lg:px-10">
      <div className="mb-10 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-medium text-[#718078]">{formattedDate}</p>
          <h1 className="font-serif text-4xl font-semibold tracking-tight text-[#18352b] sm:text-5xl">
            {greeting}
            {userName ? `, ${userName}` : ''}
            <span className="text-[#d6924a]">.</span>
          </h1>
          <p className="mt-3 max-w-xl text-[#718078]">
            Your personal financial health command center. Connect your transaction data to unlock instant analytics.
          </p>
        </div>
        <button
          onClick={() => setPage('upload')}
          className="flex items-center justify-center gap-2 rounded-xl bg-[#2f6b57] px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#245644]"
        >
          <Upload className="size-4" />
          Upload transactions
        </button>
      </div>

      <Card className="flex flex-col items-center justify-center p-10 text-center sm:p-16">
        <div className="mb-6 flex size-20 items-center justify-center rounded-3xl bg-[#eaf3ed] text-[#2f6b57] shadow-inner">
          <FileUp className="size-10" />
        </div>
        <h2 className="font-serif text-3xl font-semibold text-[#18352b]">No transaction data yet</h2>
        <p className="mt-3 max-w-md text-base text-[#718078]">
          Upload a CSV to generate your financial health score, spending breakdown, anomaly alerts, and actionable recommendations.
        </p>

        {demoError && (
          <p className="mt-4 flex items-center gap-2 text-sm font-medium text-[#b75c49]">
            <AlertCircle className="size-4" />
            {demoError}
          </p>
        )}

        <div className="mt-8 flex flex-col gap-3 sm:flex-row">
          <button
            onClick={() => setPage('upload')}
            className="flex items-center justify-center gap-2 rounded-xl bg-[#2f6b57] px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#245644]"
          >
            <Upload className="size-4" />
            Upload transactions
          </button>
          <button
            onClick={onExploreDemo}
            disabled={demoLoading}
            className="flex items-center justify-center gap-2 rounded-xl border border-[#d7e2d8] bg-white px-6 py-3.5 text-sm font-semibold text-[#2f6b57] transition hover:bg-[#f1f8f2] disabled:opacity-60"
          >
            {demoLoading ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Loading sample data...
              </>
            ) : (
              <>
                <Sparkles className="size-4 text-[#d6924a]" />
                Explore demo data
              </>
            )}
          </button>
        </div>
      </Card>

      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-[#e5e9e4] bg-white p-5">
          <ShieldCheck className="mb-3 size-6 text-[#2f6b57]" />
          <p className="font-serif text-base font-semibold text-[#18352b]">Private & Secure</p>
          <p className="mt-1 text-xs text-[#718078]">No bank credentials required. Data processed deterministically.</p>
        </div>
        <div className="rounded-2xl border border-[#e5e9e4] bg-white p-5">
          <BarChart3 className="mb-3 size-6 text-[#2f6b57]" />
          <p className="font-serif text-base font-semibold text-[#18352b]">Objective Health Score</p>
          <p className="mt-1 text-xs text-[#718078]">Evaluates savings rates, living within means, and essential spending.</p>
        </div>
        <div className="rounded-2xl border border-[#e5e9e4] bg-white p-5">
          <CircleDollarSign className="mb-3 size-6 text-[#2f6b57]" />
          <p className="font-serif text-base font-semibold text-[#18352b]">Action Engine Guidance</p>
          <p className="mt-1 text-xs text-[#718078]">Converts raw numbers into high-impact, achievable next steps.</p>
        </div>
      </div>
    </div>
  )
}

/**
 * Active dashboard rendering REAL data from the backend AnalysisResponse.
 */
function Dashboard({
  analysis,
  setPage,
  greeting,
  userName,
  formattedDate,
}: {
  analysis: AnalysisResponse
  setPage: (p: Page) => void
  greeting: string
  userName: string
  formattedDate: string
}) {
  const summary = analysis.summary || { total_income: 0, total_expenses: 0, net_savings: 0, savings_rate: 0 }

  const categories = useMemo(() => {
    if (analysis.category_breakdown && analysis.category_breakdown.length > 0) {
      return analysis.category_breakdown.map((cb) => ({
        name: cb.category,
        value: cb.total_amount,
        percentage: cb.percentage,
      }))
    }
    return Object.entries(analysis.category_spending || {}).map(([name, value]) => ({
      name,
      value: Number(value),
      percentage: analysis.category_percentages?.[name] || 0,
    }))
  }, [analysis])

  const budget = analysis.budget_summary || {
    total_budget: 0,
    total_actual: 0,
    total_remaining: 0,
    overall_utilization_percentage: 0,
    categories: [],
    overspent_categories: [],
  }

  const ess = analysis.essential_vs_non_essential || {
    essential_spending: 0,
    non_essential_spending: 0,
    essential_percentage: 0,
    non_essential_percentage: 0,
  }

  const hs = analysis.health_score || {
    score: 0,
    grade: 'N/A',
    status: 'Unknown',
    insights: [],
  }

  const score = Math.max(0, Math.min(100, Math.round(hs.score || 0)))

  // Determine trend action label dynamically
  const trendAction = `${analysis.monthly_trends.length} month${analysis.monthly_trends.length === 1 ? '' : 's'}`

  return (
    <div className="mx-auto max-w-[1440px] px-5 py-8 lg:px-10">
      <div className="mb-8 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="mb-2 text-sm font-medium text-[#718078]">{formattedDate}</p>
          <h1 className="font-serif text-4xl font-semibold tracking-tight text-[#18352b] sm:text-5xl">
            {greeting}
            {userName ? `, ${userName}` : ''}
            <span className="text-[#d6924a]">.</span>
          </h1>
          <p className="mt-3 max-w-xl text-[#718078]">
            Here is your financial pulse based on {analysis.total_transactions} analyzed transactions.
          </p>
        </div>
        <button
          onClick={() => setPage('upload')}
          className="flex items-center justify-center gap-2 rounded-xl bg-[#2f6b57] px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-[#245644]"
        >
          <Upload className="size-4" />
          Upload new CSV
        </button>
      </div>

      {/* 4 Primary Cash Flow Stats */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label="Total income" value={money(summary.total_income)} icon={ArrowUpRight} />
        <Stat label="Total expenses" value={money(summary.total_expenses)} icon={ReceiptIndianRupee} tone="amber" />
        <Stat
          label="Net savings"
          value={money(summary.net_savings)}
          icon={PiggyBank}
          trend={`${summary.savings_rate.toFixed(1)}%`}
        />
        <Stat label="Savings rate" value={`${summary.savings_rate.toFixed(1)}%`} icon={Target} tone="blue" />
      </div>

      {/* Health Score + Essential vs Non-essential */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="overflow-hidden bg-[#18352b] p-6 text-white sm:p-8">
          <div className="flex items-start justify-between">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-[#b9d1c2]">Financial Health Score</p>
                <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs font-bold text-[#d6924a]">
                  Grade {hs.grade}
                </span>
              </div>
              <p className="mt-3 text-6xl font-bold tracking-tight">
                {score}
                <span className="text-2xl text-[#8eaea0]">/100</span>
              </p>
              <p className="mt-2 text-sm text-[#b9d1c2]">
                Status: <span className="font-semibold text-white">{hs.status}</span>
              </p>
            </div>
            <div className="flex size-12 items-center justify-center rounded-2xl bg-white/10">
              <ShieldCheck className="size-6 text-[#d9e9dc]" />
            </div>
          </div>

          <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full bg-[#d6924a] transition-all duration-500" style={{ width: `${score}%` }} />
          </div>

          <div className="mt-3 flex justify-between text-xs text-[#8eaea0]">
            <span>Needs attention (&lt;50)</span>
            <span>Fair (50–69)</span>
            <span>Good (70–84)</span>
            <span>Excellent (85+)</span>
          </div>

          {hs.insights && hs.insights.length > 0 && (
            <div className="mt-5 border-t border-white/10 pt-4 text-xs text-[#b9d1c2]">
              <p className="font-semibold text-white">Key observation:</p>
              <p className="mt-1 leading-relaxed">{hs.insights[0]}</p>
            </div>
          )}
        </Card>

        <Card className="p-6 sm:p-8">
          <SectionHeading eyebrow="Your balance" title="Essential vs non-essential" />
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:gap-8">
            <div className="relative size-36 shrink-0 self-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Essential', value: Number(ess.essential_spending || 0) },
                      { name: 'Non-essential', value: Number(ess.non_essential_spending || 0) },
                    ]}
                    innerRadius={49}
                    outerRadius={66}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    <Cell fill="#2f6b57" />
                    <Cell fill="#d6924a" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-xl font-bold text-[#18352b]">
                  {Math.round(Number(ess.essential_percentage || 0))}%
                </span>
                <span className="text-[10px] text-[#718078]">essential</span>
              </div>
            </div>

            <div className="flex flex-col gap-4 text-sm">
              <div>
                <p className="flex items-center gap-2 text-[#718078]">
                  <span className="size-2 rounded-full bg-[#2f6b57]" />
                  Essential needs
                </p>
                <p className="mt-1 font-bold text-[#18352b]">{money(ess.essential_spending)}</p>
                <p className="text-xs text-[#718078]">{ess.essential_percentage.toFixed(1)}% of total living expenses</p>
              </div>
              <div>
                <p className="flex items-center gap-2 text-[#718078]">
                  <span className="size-2 rounded-full bg-[#d6924a]" />
                  Non-essential wants
                </p>
                <p className="mt-1 font-bold text-[#18352b]">{money(ess.non_essential_spending)}</p>
                <p className="text-xs text-[#718078]">{ess.non_essential_percentage.toFixed(1)}% of total living expenses</p>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Spending Breakdown + Monthly Trends */}
      <div className="mt-6 grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="p-6">
          <SectionHeading eyebrow="Where it goes" title="Category breakdown" />
          {categories.length > 0 ? (
            <div className="grid items-center gap-5 md:grid-cols-[0.95fr_1.05fr]">
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={categories}
                      innerRadius={55}
                      outerRadius={84}
                      dataKey="value"
                      strokeWidth={2}
                      stroke="#fff"
                    >
                      {categories.map((_, i) => (
                        <Cell key={i} fill={pieColors[i % pieColors.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v: any) => money(Number(v))} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-col gap-3">
                {categories.slice(0, 6).map((item, i) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 text-[#718078]">
                      <span className="size-2.5 rounded-full" style={{ background: pieColors[i % pieColors.length] }} />
                      {item.name}
                    </span>
                    <span className="font-semibold text-[#18352b]">{money(item.value)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-[#718078]">No category expense data recorded.</p>
          )}
        </Card>

        <Card className="p-6">
          <SectionHeading eyebrow="Over time" title="Monthly trends" action={trendAction} />
          {analysis.monthly_trends && analysis.monthly_trends.length > 0 ? (
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={analysis.monthly_trends}>
                  <defs>
                    <linearGradient id="savingsGrad" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="#78a88c" stopOpacity={0.4} />
                      <stop offset="100%" stopColor="#78a88c" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#8a978f', fontSize: 12 }} />
                  <YAxis hide />
                  <Tooltip formatter={(v: any) => money(Number(v))} />
                  <Area type="monotone" dataKey="savings" stroke="#2f6b57" fill="url(#savingsGrad)" strokeWidth={2.5} />
                  <Area type="monotone" dataKey="expenses" stroke="#d6924a" fill="none" strokeWidth={2} strokeDasharray="4 4" />
                </AreaChart>
              </ResponsiveContainer>
              <div className="mt-2 flex gap-4 text-xs text-[#718078]">
                <span className="flex items-center gap-2">
                  <i className="size-2 rounded-full bg-[#2f6b57]" />
                  Net Savings
                </span>
                <span className="flex items-center gap-2">
                  <i className="size-2 rounded-full bg-[#d6924a]" />
                  Total Expenses
                </span>
              </div>
            </div>
          ) : (
            <p className="py-8 text-center text-sm text-[#718078]">Single-period statement; monthly trend will appear with multiple dates.</p>
          )}
        </Card>
      </div>

      {/* Anomalies + Budget Summary */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <Card className="p-6">
          <SectionHeading eyebrow="Pay attention" title="Unusual spending alerts" />
          {analysis.anomalies && analysis.anomalies.length > 0 ? (
            <div className="flex flex-col gap-3">
              {analysis.anomalies.map((a: AnomalyItem, i: number) => (
                <div key={i} className="flex gap-3 rounded-xl border border-[#f0e5d8] bg-[#fffaf4] p-4">
                  <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-[#fff0d9] text-[#b87527]">
                    <Bell className="size-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                      <p className="font-semibold text-[#18352b]">{a.description}</p>
                      <span className="shrink-0 text-sm font-bold text-[#18352b]">{money(a.amount)}</span>
                    </div>
                    <p className="mt-1 text-sm text-[#718078]">{a.reason}</p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="inline-flex rounded-full bg-[#f6e4ca] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#9c6321]">
                        {a.severity} severity
                      </span>
                      {a.category && (
                        <span className="text-[11px] text-[#718078]">({a.category})</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-sm text-[#718078]">No unusual spending detected.</p>
          )}
        </Card>

        <Card className="p-6">
          <SectionHeading eyebrow="Budget control" title="Budget overview" />
          {budget.total_budget > 0 ? (
            <>
              <div className="mb-5 flex items-end justify-between">
                <div>
                  <p className="text-sm text-[#718078]">Total spent</p>
                  <p className="mt-1 text-3xl font-bold text-[#18352b]">{money(budget.total_actual)}</p>
                </div>
                <p className="text-right text-sm text-[#718078]">
                  of {money(budget.total_budget)}
                  <br />
                  <span className="font-semibold text-[#2f6b57]">
                    {budget.overall_utilization_percentage.toFixed(1)}% used
                  </span>
                </p>
              </div>

              <div className="mb-5 h-3 overflow-hidden rounded-full bg-[#edf1ed]">
                <div
                  className="h-full rounded-full bg-[#d6924a] transition-all duration-500"
                  style={{ width: `${Math.min(budget.overall_utilization_percentage, 100)}%` }}
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                {budget.categories.map((b: CategoryBudgetStatus) => (
                  <div key={b.category} className="rounded-xl bg-[#f8faf7] p-3">
                    <div className="flex justify-between text-xs">
                      <span className="font-medium text-[#718078]">{b.category}</span>
                      <span
                        className={
                          b.status === 'over_budget'
                            ? 'font-bold text-[#bd6b55]'
                            : b.status === 'near_limit'
                            ? 'font-bold text-[#b87527]'
                            : 'font-bold text-[#3b825b]'
                        }
                      >
                        {b.status === 'over_budget' ? 'Over' : b.status === 'near_limit' ? 'Near limit' : 'On track'}
                      </span>
                    </div>
                    <p className="mt-2 text-sm font-bold text-[#18352b]">
                      {money(b.actual)} <span className="font-normal text-[#9ba69e]">/ {money(b.budget)}</span>
                    </p>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="py-6 text-center text-sm text-[#718078]">
              <p>No category budgets configured yet.</p>
              <p className="mt-1 text-xs text-[#9ba69e]">Budgets help monitor spending limits across Food, Shopping, and Utilities.</p>
            </div>
          )}
        </Card>
      </div>

      {/* Subscriptions + Action Plan */}
      <div className="mt-6 grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
        <Card className="p-6">
          <SectionHeading eyebrow="Keep an eye on" title="Recurring subscriptions" />
          {analysis.subscriptions && analysis.subscriptions.length > 0 ? (
            <div className="flex flex-col gap-4">
              {analysis.subscriptions.map((s: SubscriptionItem) => (
                <div key={s.description} className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-[#edf4f5] text-[#4e7f86]">
                      <ReceiptIndianRupee className="size-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[#18352b]">{s.description}</p>
                      <p className="text-xs text-[#718078]">{s.frequency} ({s.occurrences} recorded)</p>
                    </div>
                  </div>
                  <p className="text-sm font-bold text-[#18352b]">{money(s.estimated_monthly_cost)}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-sm text-[#718078]">No recurring subscriptions detected.</p>
          )}
        </Card>

        <Card className="p-6">
          <SectionHeading eyebrow="Action Engine" title="Your action plan" />
          {analysis.actions && analysis.actions.length > 0 ? (
            <div className="grid gap-3 md:grid-cols-3">
              {analysis.actions.map((a: ActionItem, i: number) => (
                <div key={i} className="flex flex-col justify-between rounded-xl border border-[#e5e9e4] p-4">
                  <div>
                    <div className="mb-3 flex items-center justify-between">
                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          a.priority === 'high'
                            ? 'bg-[#fbe9e4] text-[#b75c49]'
                            : a.priority === 'medium'
                            ? 'bg-[#fff2dd] text-[#a66a25]'
                            : 'bg-[#eaf3ed] text-[#3b825b]'
                        }`}
                      >
                        {a.priority} priority
                      </span>
                      <Zap className="size-4 text-[#d6924a]" />
                    </div>
                    <p className="font-semibold text-[#18352b]">{a.title}</p>
                    <p className="mt-2 text-xs leading-relaxed text-[#718078]">{a.description}</p>
                  </div>
                  {a.estimated_monthly_impact && a.estimated_monthly_impact > 0 && (
                    <p className="mt-3 border-t border-[#f0f3ef] pt-2 text-xs font-semibold text-[#2f6b57]">
                      Potential impact: {money(a.estimated_monthly_impact)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="py-6 text-sm text-[#718078]">No recommended action items generated.</p>
          )}
        </Card>
      </div>
    </div>
  )
}

/**
 * CSV Upload component with validation and loading states.
 */
function UploadPage({
  onAnalysis,
  setPage,
  onExploreDemo,
  demoLoading,
}: {
  onAnalysis: (a: AnalysisResponse) => void
  setPage: (p: Page) => void
  onExploreDemo: () => void
  demoLoading: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'' | 'loading'>('')
  const [error, setError] = useState('')

  const handleUpload = async () => {
    if (!file) {
      setError('Please choose a CSV file first.')
      return
    }
    setError('')
    setStatus('loading')
    try {
      const result = await analyzeCsv(file)
      onAnalysis(result)
      setPage('dashboard')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setError(msg || 'Unable to reach the analysis service. Please check that the backend is running.')
      setStatus('')
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-5 py-12 lg:px-10">
      <button
        onClick={() => setPage('dashboard')}
        className="mb-10 flex items-center gap-2 text-sm font-semibold text-[#2f6b57] hover:underline"
      >
        <ChevronRight className="size-4 rotate-180" />
        Back to dashboard
      </button>

      <div className="mb-10">
        <div className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-[#eaf3ed] text-[#2f6b57]">
          <FileUp className="size-6" />
        </div>
        <h1 className="font-serif text-4xl font-semibold text-[#18352b]">
          Bring your money story to life<span className="text-[#d6924a]">.</span>
        </h1>
        <p className="mt-3 max-w-lg text-[#718078]">
          Upload a CSV of your transactions to get a clear, personal view of your financial health. No bank passwords required.
        </p>
      </div>

      <Card className="p-6 sm:p-10">
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="flex w-full flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[#c8d8cc] bg-[#f8fbf8] px-6 py-16 transition hover:border-[#2f6b57] hover:bg-[#f1f8f2]"
        >
          <div className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-white text-[#2f6b57] shadow-sm">
            <Upload className="size-6" />
          </div>
          <p className="font-semibold text-[#18352b]">
            {file ? file.name : 'Drop your CSV here or browse'}
          </p>
          <p className="mt-2 text-sm text-[#718078]">
            CSV with columns: <span className="font-mono text-xs font-semibold">date, description, amount, type</span>
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            className="hidden"
            onChange={(e) => {
              const selected = e.target.files?.[0]
              if (selected && !selected.name.toLowerCase().endsWith('.csv')) {
                setError('Please choose a valid CSV file with .csv extension.')
              } else {
                setFile(selected || null)
                setError('')
              }
            }}
          />
        </button>

        {error && (
          <div className="mt-4 flex items-start gap-2 rounded-xl bg-[#fdf2ef] p-3 text-sm font-medium text-[#b75c49]">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <button
            onClick={handleUpload}
            disabled={status === 'loading'}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-[#2f6b57] px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-[#245644] disabled:opacity-60"
          >
            {status === 'loading' ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Analyzing your transactions...
              </>
            ) : (
              <>
                <Sparkles className="size-4" />
                Analyze my finances
              </>
            )}
          </button>
          <button
            type="button"
            onClick={onExploreDemo}
            disabled={demoLoading || status === 'loading'}
            className="rounded-xl border border-[#d7e2d8] px-4 py-3 font-semibold text-[#2f6b57] transition hover:bg-[#f1f8f2] disabled:opacity-60"
          >
            {demoLoading ? 'Loading demo...' : 'Explore demo data'}
          </button>
        </div>
      </Card>

      <div className="mt-8 grid gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-[#f8faf7] p-4">
          <ShieldCheck className="mb-3 size-5 text-[#2f6b57]" />
          <p className="text-sm font-semibold text-[#18352b]">Private by design</p>
          <p className="mt-1 text-xs text-[#718078]">Your financial data stays protected.</p>
        </div>
        <div className="rounded-xl bg-[#f8faf7] p-4">
          <BarChart3 className="mb-3 size-5 text-[#2f6b57]" />
          <p className="text-sm font-semibold text-[#18352b]">Clear insights</p>
          <p className="mt-1 text-xs text-[#718078]">No complicated financial jargon.</p>
        </div>
        <div className="rounded-xl bg-[#f8faf7] p-4">
          <CircleDollarSign className="mb-3 size-5 text-[#2f6b57]" />
          <p className="text-sm font-semibold text-[#18352b]">Actionable next steps</p>
          <p className="mt-1 text-xs text-[#718078]">Small adjustments with real savings impact.</p>
        </div>
      </div>
    </div>
  )
}

/**
 * AI Financial Copilot component grounded strictly in the current analysis.
 */
function Copilot({
  analysis,
  setPage,
}: {
  analysis: AnalysisResponse | null
  setPage: (p: Page) => void
}) {
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string; actions?: ActionItem[] }>>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [copilotError, setCopilotError] = useState('')

  const suggestions = [
    'Where am I spending the most?',
    'How can I save more money?',
    'What unusual spending do I have?',
    'What is my financial health score?',
  ]

  const ask = async (question: string) => {
    const cleanQuestion = question.trim()
    if (!cleanQuestion || loading) return

    setCopilotError('')

    if (!analysis) {
      setMessages((m) => [
        ...m,
        { role: 'user', content: cleanQuestion },
        {
          role: 'assistant',
          content: 'Upload your transaction data first so I can answer questions about your finances.',
        },
      ])
      setInput('')
      return
    }

    setMessages((m) => [...m, { role: 'user', content: cleanQuestion }])
    setInput('')
    setLoading(true)

    try {
      const response = await sendCopilotMessage(cleanQuestion, analysis)
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: response.response || 'I could not find an answer grounded in your analysis.',
          actions: response.actions,
        },
      ])
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setCopilotError(msg)
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: `Unable to generate a response: ${msg}`,
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-5 py-10 lg:px-10">
      <div className="mb-8 flex items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <div className="flex size-12 items-center justify-center rounded-2xl bg-[#eaf3ed] text-[#2f6b57]">
            <Bot className="size-6" />
          </div>
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.16em] text-[#2f6b57]">Your money companion</p>
            <h1 className="font-serif text-4xl font-semibold text-[#18352b]">AI Financial Copilot</h1>
          </div>
        </div>

        {analysis && (
          <span className="rounded-full bg-[#edf7ef] px-3 py-1 text-xs font-semibold text-[#2f6b57]">
            Using live statement data
          </span>
        )}
      </div>

      <Card className="overflow-hidden">
        <div className="flex min-h-[500px] flex-col">
          <div className="flex-1 p-5 sm:p-8">
            {!analysis ? (
              <div className="flex h-full min-h-[380px] flex-col items-center justify-center text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-3xl bg-[#f8faf7] text-[#718078] border border-[#e5e9e4]">
                  <AlertCircle className="size-8 text-[#d6924a]" />
                </div>
                <h2 className="font-serif text-2xl font-semibold text-[#18352b]">No transaction data connected</h2>
                <p className="mt-2 max-w-md text-sm text-[#718078]">
                  Upload your transaction data first so I can answer questions about your finances.
                </p>
                <div className="mt-6 flex gap-3">
                  <button
                    onClick={() => setPage('upload')}
                    className="flex items-center gap-2 rounded-xl bg-[#2f6b57] px-4 py-2.5 text-sm font-semibold text-white hover:bg-[#245644]"
                  >
                    <Upload className="size-4" />
                    Upload transactions
                  </button>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full min-h-[380px] flex-col items-center justify-center text-center">
                <div className="mb-5 flex size-16 items-center justify-center rounded-3xl bg-[#18352b] text-white">
                  <MessageCircle className="size-7" />
                </div>
                <h2 className="font-serif text-2xl font-semibold text-[#18352b]">What would you like to understand?</h2>
                <p className="mt-2 max-w-md text-sm text-[#718078]">
                  Ask me anything about your spending, savings, subscriptions, budgets, or financial health. I will use your current statement data to give you explainable answers.
                </p>
                <div className="mt-7 flex flex-wrap justify-center gap-2">
                  {suggestions.map((s) => (
                    <button
                      key={s}
                      type="button"
                      disabled={loading}
                      onClick={() => ask(s)}
                      className="rounded-full border border-[#d7e2d8] px-3.5 py-2 text-xs font-medium text-[#426258] transition hover:border-[#2f6b57] hover:bg-[#f1f8f2] disabled:opacity-50"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-5">
                {messages.map((m, i) => (
                  <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                        m.role === 'user'
                          ? 'rounded-br-sm bg-[#2f6b57] text-white'
                          : 'rounded-bl-sm bg-[#f1f6f1] text-[#304d41]'
                      }`}
                    >
                      <p className="whitespace-pre-line">{m.content}</p>

                      {m.actions && m.actions.length > 0 && (
                        <div className="mt-3 border-t border-[#d8e6db] pt-3">
                          <p className="mb-1 text-xs font-bold uppercase tracking-wider text-[#2f6b57]">
                            Recommended Next Steps:
                          </p>
                          <div className="flex flex-col gap-2">
                            {m.actions.map((act, idx) => (
                              <div key={idx} className="rounded-lg bg-white/70 p-2 text-xs text-[#18352b]">
                                <span className="font-bold">{act.title}:</span> {act.description}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex gap-3">
                    <div className="flex items-center gap-2 rounded-2xl rounded-bl-sm bg-[#f1f6f1] px-4 py-3 text-sm text-[#2f6b57]">
                      <Loader2 className="size-4 animate-spin" />
                      <span>Thinking and analyzing data...</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="border-t border-[#edf0ec] bg-[#fbfcfa] p-4">
            {copilotError && (
              <div className="mb-3 flex items-center gap-2 text-xs font-medium text-[#b75c49]">
                <AlertCircle className="size-3.5" />
                <span>{copilotError}</span>
              </div>
            )}

            {/* Form submission bug fix: correctly handles e.preventDefault() and triggers ask(input) */}
            <form
              onSubmit={(e) => {
                e.preventDefault()
                ask(input)
              }}
              className="flex gap-2"
            >
              <input
                value={input}
                disabled={loading}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  analysis
                    ? 'Ask about spending, savings, subscriptions, or budgets...'
                    : 'Upload transactions first to start chatting...'
                }
                className="min-w-0 flex-1 rounded-xl border border-[#d7e2d8] bg-white px-4 py-3 text-sm outline-none placeholder:text-[#9ba69e] focus:border-[#2f6b57] disabled:bg-[#f6f8f5]"
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                aria-label="Send message"
                className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-[#2f6b57] text-white transition hover:bg-[#245644] disabled:opacity-40"
              >
                {loading ? <Loader2 className="size-5 animate-spin" /> : <ArrowUpRight className="size-5" />}
              </button>
            </form>
            <p className="mt-2 text-center text-[11px] text-[#9ba69e]">
              Deterministic financial guidance grounded in your uploaded statements.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default function PageRoot() {
  const [page, setPage] = useState<Page>('dashboard')
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [greeting, setGreeting] = useState('Good Morning')
  const [formattedDate, setFormattedDate] = useState('')
  const [userName, setUserName] = useState('')
  const [signedIn, setSignedIn] = useState(false)
  const [authInput, setAuthInput] = useState('')
  const [demoLoading, setDemoLoading] = useState(false)
  const [demoError, setDemoError] = useState('')

  // Load greeting and browser locale date dynamically
  useEffect(() => {
    const updateTimeAndGreeting = () => {
      const now = new Date()
      setGreeting(getGreeting(now.getHours()))
      setFormattedDate(
        now.toLocaleDateString(undefined, {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        })
      )
    }

    updateTimeAndGreeting()
    const timer = window.setInterval(updateTimeAndGreeting, 60000)

    // MVP localStorage demo authentication
    try {
      const stored = window.localStorage.getItem('moneymind-auth')
      if (stored) {
        setUserName(stored)
        setSignedIn(true)
      }
    } catch {
      // localStorage may fail in some restricted environments
    }

    return () => window.clearInterval(timer)
  }, [])

  const signIn = () => {
    const name = authInput.trim()
    if (!name) return
    try {
      window.localStorage.setItem('moneymind-auth', name)
    } catch {}
    setUserName(name)
    setSignedIn(true)
    setAuthInput('')
  }

  const signOut = () => {
    try {
      window.localStorage.removeItem('moneymind-auth')
    } catch {}
    setUserName('')
    setSignedIn(false)
  }

  const handleExploreDemo = async () => {
    setDemoLoading(true)
    setDemoError('')
    try {
      const sample = await getSampleAnalysis()
      setAnalysis(sample)
      setPage('dashboard')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setDemoError(msg || 'Unable to load sample analysis.')
    } finally {
      setDemoLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7faf6] text-[#18352b]">
      {/* Top Header */}
      <header className="sticky top-0 z-10 border-b border-[#e5e9e4] bg-[#f7faf6]/95 backdrop-blur">
        <div className="mx-auto flex h-20 max-w-[1440px] items-center justify-between px-5 lg:px-10">
          <button
            onClick={() => setPage('dashboard')}
            className="flex items-center gap-3 text-left transition hover:opacity-90"
          >
            <div className="flex size-10 items-center justify-center rounded-xl bg-[#18352b] text-white">
              <Sparkles className="size-5" />
            </div>
            <div>
              <p className="font-serif text-lg font-semibold leading-none">moneymind</p>
              <p className="mt-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#718078]">
                Financial health copilot
              </p>
            </div>
          </button>

          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setPage(id as any)}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                  page === id
                    ? 'bg-[#e5efe7] text-[#2f6b57]'
                    : 'text-[#718078] hover:bg-white hover:text-[#18352b]'
                }`}
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <button
              aria-label="Notifications"
              className="hidden size-10 items-center justify-center rounded-xl border border-[#e5e9e4] bg-white text-[#718078] sm:flex"
            >
              <Bell className="size-4" />
            </button>
            <div className="hidden size-10 items-center justify-center rounded-xl bg-[#d6924a] font-serif font-bold text-white sm:flex">
              {userName ? userName.charAt(0).toUpperCase() : 'M'}
            </div>
            <button
              aria-label="Toggle navigation menu"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="flex size-10 items-center justify-center rounded-xl border border-[#e5e9e4] bg-white md:hidden"
            >
              <Menu className="size-5" />
            </button>
          </div>
        </div>

        {mobileOpen && (
          <nav className="flex flex-col gap-1 border-t border-[#e5e9e4] px-5 py-3 md:hidden">
            {navItems.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => {
                  setPage(id as any)
                  setMobileOpen(false)
                }}
                className={`flex items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-semibold ${
                  page === id ? 'bg-[#e5efe7] text-[#2f6b57]' : 'text-[#718078]'
                }`}
              >
                <Icon className="size-4" />
                {label}
              </button>
            ))}
          </nav>
        )}

        {/* Demo Identity / MVP Sign-in badge */}
        <div className="fixed right-5 top-24 z-20 flex items-center gap-2 rounded-xl border border-[#e5e9e4] bg-white p-2 shadow-sm">
          <span className="sr-only">Frontend MVP authentication</span>
          {signedIn ? (
            <>
              <span className="max-w-32 truncate px-2 text-sm font-semibold text-[#18352b]">
                {userName}
              </span>
              <button
                onClick={signOut}
                className="rounded-lg bg-[#f7faf6] px-3 py-2 text-xs font-semibold text-[#2f6b57] hover:bg-[#e5efe7]"
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <input
                value={authInput}
                onChange={(event) => setAuthInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter') signIn()
                }}
                placeholder="Name or nickname"
                aria-label="Name or nickname"
                className="w-28 rounded-lg border border-[#e5e9e4] px-2 py-2 text-xs outline-none focus:border-[#2f6b57]"
              />
              <button
                onClick={signIn}
                className="rounded-lg bg-[#2f6b57] px-3 py-2 text-xs font-semibold text-white hover:bg-[#245644]"
              >
                Sign In
              </button>
            </>
          )}
        </div>
      </header>

      {/* Main View Router */}
      <main>
        {page === 'upload' ? (
          <UploadPage
            onAnalysis={setAnalysis}
            setPage={setPage}
            onExploreDemo={handleExploreDemo}
            demoLoading={demoLoading}
          />
        ) : page === 'copilot' ? (
          <Copilot analysis={analysis} setPage={setPage} />
        ) : analysis ? (
          <Dashboard
            analysis={analysis}
            setPage={setPage}
            greeting={greeting}
            userName={userName}
            formattedDate={formattedDate}
          />
        ) : (
          <DashboardEmptyState
            greeting={greeting}
            userName={userName}
            formattedDate={formattedDate}
            setPage={setPage}
            onExploreDemo={handleExploreDemo}
            demoLoading={demoLoading}
            demoError={demoError}
          />
        )}
      </main>
    </div>
  )
}
