/**
 * Frontend API Service for Financial Health Copilot.
 * Connects to the FastAPI backend with strict typing, robust error handling,
 * and support for local development and production deployments.
 */

export interface CashFlowSummary {
  total_income: number
  total_expenses: number
  net_savings: number
  savings_rate: number
}

export interface CategoryBreakdown {
  category: string
  total_amount: number
  percentage: number
  transaction_count: number
}

export interface MonthlyTrend {
  month: string
  income: number
  expenses: number
  savings: number
  expense?: number
  net?: number
}

export interface EssentialVsNonEssential {
  essential_spending: number
  non_essential_spending: number
  essential_percentage: number
  non_essential_percentage: number
  essential_categories?: Record<string, number>
  non_essential_categories?: Record<string, number>
}

export interface HealthScoreBreakdown {
  savings_score: number
  essential_spending_score: number
  living_within_means_score: number
}

export interface HealthScoreMetrics {
  savings_rate: number
  essential_ratio: number
  non_essential_ratio: number
  expense_to_income_ratio: number
}

export interface HealthScore {
  score: number
  grade: string
  status: string
  breakdown?: HealthScoreBreakdown
  metrics?: HealthScoreMetrics
  insights: string[]
}

export interface AnomalyItem {
  date: string
  description: string
  amount: number
  category: string
  reason: string
  severity: string
}

export interface SubscriptionItem {
  description: string
  category: string
  amount: number
  frequency: string
  occurrences: number
  estimated_monthly_cost: number
}

export interface CategoryBudgetStatus {
  category: string
  budget: number
  actual: number
  remaining: number
  utilization_percentage: number
  status: string
}

export interface BudgetSummary {
  categories: CategoryBudgetStatus[]
  total_budget: number
  total_actual: number
  total_remaining: number
  overall_utilization_percentage: number
  overspent_categories: string[]
}

export interface ActionItem {
  title: string
  description: string
  action_type: string
  category?: string | null
  priority: string
  estimated_monthly_impact?: number | null
  reason: string
}

export interface DateRange {
  start_date?: string | null
  end_date?: string | null
}

export interface AnalysisResponse {
  summary: CashFlowSummary
  category_spending: Record<string, number>
  category_percentages: Record<string, number>
  category_breakdown: CategoryBreakdown[]
  top_spending_categories: CategoryBreakdown[]
  monthly_trends: MonthlyTrend[]
  essential_vs_non_essential: EssentialVsNonEssential
  health_score: HealthScore
  anomalies: AnomalyItem[]
  subscriptions: SubscriptionItem[]
  budget_summary: BudgetSummary
  actions: ActionItem[]
  total_transactions: number
  date_range: DateRange
}

export interface CopilotResponse {
  response: string
  actions: ActionItem[]
  sources: string[]
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}

/**
 * Returns the configured backend API base URL.
 * In development, defaults safely to http://localhost:8000 if unset.
 * In production, fails explicitly with a configuration error instead of silently defaulting to localhost.
 */
export function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL?.trim()
  if (envUrl) {
    return envUrl.replace(/\/+$/, '')
  }

  if (process.env.NODE_ENV === 'development' || typeof window === 'undefined') {
    return 'http://localhost:8000'
  }

  throw new Error(
    'Production configuration error: NEXT_PUBLIC_API_URL environment variable is not defined. Please configure your deployed backend API URL.'
  )
}

/**
 * Robust JSON fetch wrapper with full error parsing and network safety.
 */
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const baseUrl = getApiBaseUrl()
  const cleanPath = path.startsWith('/') ? path : `/${path}`
  const url = `${baseUrl}${cleanPath}`

  let response: Response
  try {
    response = await fetch(url, options)
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err)
    throw new Error(
      `Unable to reach the analysis service. Please check that the backend is running. (${errorMsg})`
    )
  }

  if (!response.ok) {
    let errorDetail = ''
    try {
      const errorJson = await response.json()
      errorDetail = errorJson.detail || errorJson.message || JSON.stringify(errorJson)
    } catch {
      try {
        errorDetail = await response.text()
      } catch {
        errorDetail = `HTTP ${response.status} ${response.statusText}`
      }
    }
    throw new Error(errorDetail || `API request failed with status ${response.status}`)
  }

  try {
    return (await response.json()) as T
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : String(err)
    throw new Error(`Failed to parse response as JSON: ${errorMsg}`)
  }
}

/**
 * Normalizes backend analysis data to guarantee safe field access in all UI components.
 */
export function normalizeAnalysis(raw: any): AnalysisResponse {
  if (!raw) {
    throw new Error('Analysis data cannot be null or undefined')
  }

  const rawSummary = raw.summary || {}
  const rawEss = raw.essential_vs_non_essential || {}
  const rawHs = raw.health_score || {}
  const rawBudget = raw.budget_summary || {}

  // Parse health score safely whether it arrives as an object (standard) or number (fallback)
  const healthScore: HealthScore =
    typeof rawHs === 'number'
      ? {
          score: rawHs,
          grade: rawHs >= 85 ? 'A' : rawHs >= 70 ? 'B' : rawHs >= 50 ? 'C' : 'D',
          status: rawHs >= 85 ? 'Excellent' : rawHs >= 70 ? 'Good' : rawHs >= 50 ? 'Fair' : 'Needs Attention',
          insights: [],
        }
      : {
          score: Number(rawHs.score ?? 0),
          grade: String(rawHs.grade ?? 'N/A'),
          status: String(rawHs.status ?? 'Normal'),
          breakdown: rawHs.breakdown,
          metrics: rawHs.metrics,
          insights: Array.isArray(rawHs.insights) ? rawHs.insights : [],
        }

  const normalized: AnalysisResponse = {
    summary: {
      total_income: Number(rawSummary.total_income ?? rawSummary.income ?? 0),
      total_expenses: Number(rawSummary.total_expenses ?? rawSummary.expenses ?? 0),
      net_savings: Number(rawSummary.net_savings ?? rawSummary.savings ?? 0),
      savings_rate: Number(rawSummary.savings_rate ?? 0),
    },
    category_spending: raw.category_spending || {},
    category_percentages: raw.category_percentages || {},
    category_breakdown: Array.isArray(raw.category_breakdown)
      ? raw.category_breakdown.map((cb: any) => ({
          category: String(cb.category || 'Other'),
          total_amount: Number(cb.total_amount ?? cb.value ?? 0),
          percentage: Number(cb.percentage ?? 0),
          transaction_count: Number(cb.transaction_count ?? 1),
        }))
      : [],
    top_spending_categories: Array.isArray(raw.top_spending_categories)
      ? raw.top_spending_categories
      : [],
    monthly_trends: Array.isArray(raw.monthly_trends)
      ? raw.monthly_trends.map((mt: any) => ({
          month: String(mt.month || ''),
          income: Number(mt.income ?? 0),
          expenses: Number(mt.expenses ?? mt.expense ?? 0),
          savings: Number(mt.savings ?? mt.net ?? 0),
        }))
      : [],
    essential_vs_non_essential: {
      essential_spending: Number(rawEss.essential_spending ?? rawEss.essential ?? 0),
      non_essential_spending: Number(rawEss.non_essential_spending ?? rawEss.non_essential ?? 0),
      essential_percentage: Number(rawEss.essential_percentage ?? 0),
      non_essential_percentage: Number(rawEss.non_essential_percentage ?? 0),
      essential_categories: rawEss.essential_categories || {},
      non_essential_categories: rawEss.non_essential_categories || {},
    },
    health_score: healthScore,
    anomalies: Array.isArray(raw.anomalies)
      ? raw.anomalies.map((a: any) => ({
          date: String(a.date || ''),
          description: String(a.description || 'Unusual Transaction'),
          amount: Number(a.amount ?? 0),
          category: String(a.category || 'General'),
          reason: String(a.reason ?? a.explanation ?? 'Flagged as unusual activity'),
          severity: String(a.severity || 'medium'),
        }))
      : [],
    subscriptions: Array.isArray(raw.subscriptions)
      ? raw.subscriptions.map((s: any) => ({
          description: String(s.description || 'Subscription'),
          category: String(s.category || 'Bills & Utilities'),
          amount: Number(s.amount ?? 0),
          frequency: String(s.frequency || 'Monthly'),
          occurrences: Number(s.occurrences ?? 1),
          estimated_monthly_cost: Number(s.estimated_monthly_cost ?? s.amount ?? 0),
        }))
      : [],
    budget_summary: {
      categories: Array.isArray(rawBudget.categories)
        ? rawBudget.categories.map((c: any) => ({
            category: String(c.category || ''),
            budget: Number(c.budget ?? 0),
            actual: Number(c.actual ?? 0),
            remaining: Number(c.remaining ?? (c.budget - c.actual)),
            utilization_percentage: Number(c.utilization_percentage ?? (c.budget > 0 ? (c.actual / c.budget) * 100 : 0)),
            status: String(c.status || 'under_budget'),
          }))
        : [],
      total_budget: Number(rawBudget.total_budget ?? 0),
      total_actual: Number(rawBudget.total_actual ?? rawBudget.actual_spending ?? 0),
      total_remaining: Number(rawBudget.total_remaining ?? rawBudget.remaining_amount ?? 0),
      overall_utilization_percentage: Number(rawBudget.overall_utilization_percentage ?? rawBudget.utilization ?? 0),
      overspent_categories: Array.isArray(rawBudget.overspent_categories) ? rawBudget.overspent_categories : [],
    },
    actions: Array.isArray(raw.actions)
      ? raw.actions.map((act: any) => ({
          title: String(act.title || ''),
          description: String(act.description || ''),
          action_type: String(act.action_type || 'recommendation'),
          category: act.category ? String(act.category) : null,
          priority: String(act.priority || 'medium'),
          estimated_monthly_impact: act.estimated_monthly_impact != null ? Number(act.estimated_monthly_impact) : null,
          reason: String(act.reason || ''),
        }))
      : [],
    total_transactions: Number(raw.total_transactions ?? 0),
    date_range: raw.date_range || {},
  }

  return normalized
}

/**
 * Checks API server health.
 */
export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/api/health')
}

/**
 * Ingests a CSV statement, processes transactions, and returns full AnalysisResponse.
 */
export async function analyzeCsv(file: File): Promise<AnalysisResponse> {
  if (!file) {
    throw new Error('Please select a CSV file to analyze.')
  }
  if (!file.name.toLowerCase().endsWith('.csv')) {
    throw new Error('Invalid file format. Please select a file with .csv extension.')
  }

  const formData = new FormData()
  formData.append('file', file)

  const raw = await request<AnalysisResponse>('/api/analyze-csv', {
    method: 'POST',
    body: formData,
  })

  return normalizeAnalysis(raw)
}

/**
 * Loads sample financial statement analysis directly from the backend.
 */
export async function getSampleAnalysis(): Promise<AnalysisResponse> {
  const raw = await request<AnalysisResponse>('/api/sample/analyze')
  return normalizeAnalysis(raw)
}

/**
 * Sends a financial question to the AI Copilot grounded in the current analysis.
 */
export async function sendCopilotMessage(
  message: string,
  analysis: AnalysisResponse | null
): Promise<CopilotResponse> {
  const cleanMessage = message.trim()
  if (!cleanMessage) {
    throw new Error('Please enter a question for the Copilot.')
  }

  return request<CopilotResponse>('/api/copilot/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: cleanMessage,
      analysis: analysis,
    }),
  })
}
