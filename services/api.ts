const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  if (!response.ok) {
    throw new Error(`API request failed with status ${response.status}`)
  }
  return response.json() as Promise<T>
}

export function analyzeCsv(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return request('/api/analyze-csv', { method: 'POST', body: formData })
}

export function getSampleAnalysis() {
  return request('/api/sample/analyze')
}

export function sendCopilotMessage(message: string, analysis: unknown) {
  return request('/api/copilot/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, analysis }),
  })
}
