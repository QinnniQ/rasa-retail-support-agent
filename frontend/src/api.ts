export type Issue = 'order' | 'missing' | 'damaged' | 'return' | 'refund' | 'partner' | 'human'
export type Order = {
  order_id: string
  status: string
  delivery_status: string
  delivery_date: string | null
  partner_order: boolean
  return_eligible: boolean | string | null
  refund_status: string
  items: { name: string; quantity_ordered: number; quantity_delivered: number; condition: string }[]
}
export type Trace = { step: string; detail: string }
export type Reply = {
  messages: string[]
  mode: 'demo' | 'rasa'
  order: Order | null
  case_id: number | null
  quick_replies: string[]
  trace: Trace[]
}
export type Case = {
  id: number
  session_id: string
  issue: Issue
  reason: string
  order_id: string | null
  summary: string
  status: 'open' | 'investigating' | 'resolved'
  assignee: string | null
  created_at: string
}
export type Status = {
  mode: 'demo' | 'rasa'
  deployment?: 'cloudflare'
  retail_api: string
  rasa: string
  case_store: string
}

async function json<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, init)
  if (!response.ok)
    throw new Error(
      response.status === 401
        ? 'Ongeldige toegangscode.'
        : response.status === 503
          ? 'De dienst is niet beschikbaar.'
          : `Verzoek mislukt (${response.status}).`,
    )
  return response.json() as Promise<T>
}
export const api = {
  chat: (session_id: string, message: string, category?: Issue) =>
    json<Reply>('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id, message, category }),
    }),
  status: () => json<Status>('/api/status'),
  cases: (credential: string, publicDemo = false) =>
    json<Case[]>('/api/cases', {
      headers: { [publicDemo ? 'X-Demo-Session' : 'X-Support-Token']: credential },
    }),
  updateCase: (
    id: number,
    credential: string,
    body: { status?: Case['status']; assignee?: string },
    publicDemo = false,
  ) =>
    json<Case>(`/api/cases/${id}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        [publicDemo ? 'X-Demo-Session' : 'X-Support-Token']: credential,
      },
      body: JSON.stringify(body),
    }),
}
