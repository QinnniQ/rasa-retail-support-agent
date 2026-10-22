import { advice, classify, exampleOrders, extractOrderId, issues } from './demo-policy.js'

const SESSION_ID = /^[a-f0-9]{32}$/i
const CASE_STATUSES = ['open', 'investigating', 'resolved']
const WEEK = 7 * 24 * 60 * 60
const HOUR = 60 * 60

function json(body, status = 200) {
  return Response.json(body, { status, headers: { 'Cache-Control': 'no-store' } })
}

function sessionId(request) {
  const id = request.headers.get('x-demo-session')
  return id && SESSION_ID.test(id) ? id.toLowerCase() : null
}

async function limit(request, env, session, now) {
  if (!env.DEMO_RATE_SECRET) return json({ detail: 'Rate limit is not configured' }, 503)
  const ip = request.headers.get('cf-connecting-ip') || `session:${session}`
  const key = await crypto.subtle.importKey(
    'raw',
    new TextEncoder().encode(env.DEMO_RATE_SECRET),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const bytes = await crypto.subtle.sign(
    'HMAC',
    key,
    new TextEncoder().encode(`${Math.floor(now / HOUR)}:${ip}`),
  )
  const digest = Array.from(new Uint8Array(bytes), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('')
  const row = await env.DEMO_DB.prepare('SELECT count FROM demo_limits WHERE key=?')
    .bind(digest)
    .first()
  if (row?.count >= 40) return json({ detail: 'Demo limit reached; try again later' }, 429)
  await env.DEMO_DB.prepare(
    'INSERT INTO demo_limits(key,count,expires_at) VALUES(?,1,?) ON CONFLICT(key) DO UPDATE SET count=count+1',
  )
    .bind(digest, now + HOUR)
    .run()
  return null
}

async function cleanup(db, now) {
  await db
    .prepare('DELETE FROM demo_cases WHERE created_unix < ?')
    .bind(now - WEEK)
    .run()
  await db
    .prepare('DELETE FROM demo_sessions WHERE updated_at < ?')
    .bind(now - WEEK)
    .run()
  await db.prepare('DELETE FROM demo_limits WHERE expires_at < ?').bind(now).run()
}

async function chat(request, env, now) {
  let body
  try {
    const raw = await request.text()
    if (raw.length > 2500) return json({ detail: 'Message too long' }, 413)
    body = JSON.parse(raw)
  } catch {
    return json({ detail: 'Invalid JSON' }, 400)
  }
  if (
    !body ||
    typeof body !== 'object' ||
    !SESSION_ID.test(body.session_id || '') ||
    typeof body.message !== 'string' ||
    !body.message.trim() ||
    body.message.length > 1000 ||
    (body.category != null && !issues.includes(body.category))
  )
    return json({ detail: 'Invalid chat request' }, 422)
  const id = body.session_id.toLowerCase()
  const limited = await limit(request, env, id, now)
  if (limited) return limited
  const previous = await env.DEMO_DB.prepare('SELECT issue,order_id FROM demo_sessions WHERE id=?')
    .bind(id)
    .first()
  let issue = body.category || classify(body.message) || previous?.issue || null
  let orderId = extractOrderId(body.message) || previous?.order_id || null
  const trace = [
    { step: 'message', detail: 'Bericht ontvangen en gevalideerd' },
    { step: 'routing', detail: `Deterministische demo-classificatie: ${issue || 'onbekend'}` },
  ]
  let answer,
    replies,
    order = null,
    caseId = null
  if (!issue && !orderId) {
    answer =
      'Ik kan helpen met bestellingen, ontbrekende of beschadigde artikelen, retouren en terugbetalingen. Kies een onderwerp of geef een voorbeeldordernummer.'
    replies = ['Bestelling volgen', 'Artikel ontbreekt', 'Retourneren']
  } else if (!orderId && issue !== 'human') {
    answer = 'Wat is je voorbeeldordernummer? Gebruik bijvoorbeeld KV-10482, KV-20991 of KV-77830.'
    replies = ['KV-10482', 'KV-20991', 'KV-77830']
    trace.push({ step: 'slot', detail: 'Wacht op voorbeeldordernummer' })
  } else if (orderId && !exampleOrders[orderId]) {
    answer = `Ik kan ${orderId} niet vinden in de fictieve voorbeeldorders. Controleer het nummer of probeer KV-10482.`
    replies = ['KV-10482', 'Contact met medewerker']
    orderId = null
    trace.push({ step: 'lookup', detail: 'Order niet gevonden' })
  } else {
    replies = ['Contact met medewerker', 'Andere vraag']
    order = orderId ? exampleOrders[orderId] : null
    trace.push({
      step: 'lookup',
      detail: order ? `Fictieve order ${orderId} opgehaald` : 'Geen order gekoppeld',
    })
    let handoff, reason
    if (order) [answer, handoff, reason] = advice(order, issue || 'order')
    else
      [answer, handoff, reason] = [
        'Ik kan een demonstratiecase voor een medewerker aanmaken. Beschrijf zo nodig je probleem en geef een voorbeeldordernummer.',
        true,
        'Klant vraagt om ondersteuning',
      ]
    if (order)
      trace.push({
        step: 'policy',
        detail: `Demo-regel voor ${issue || 'order'} geëvalueerd; handoff=${handoff}`,
      })
    if (handoff) {
      const caseIssue = issue || 'human'
      const existing = await env.DEMO_DB.prepare(
        "SELECT id FROM demo_cases WHERE session_id=? AND issue=? AND order_id IS ? AND status!='resolved' ORDER BY id DESC LIMIT 1",
      )
        .bind(id, caseIssue, orderId)
        .first()
      if (existing) caseId = existing.id
      else {
        const count = await env.DEMO_DB.prepare(
          'SELECT COUNT(*) AS n FROM demo_cases WHERE session_id=?',
        )
          .bind(id)
          .first()
        if (count.n >= 20) return json({ detail: 'Session case limit reached' }, 429)
        const summary = `Demonstratievraag over ${caseIssue}${orderId ? ` bij voorbeeldorder ${orderId}` : ''}. Advies: ${answer}`
        const inserted = await env.DEMO_DB.prepare(
          'INSERT INTO demo_cases(session_id,issue,reason,order_id,summary,created_unix) VALUES(?,?,?,?,?,?)',
        )
          .bind(id, caseIssue, reason, orderId, summary, now)
          .run()
        caseId = inserted.meta.last_row_id
      }
      answer += ` Demonstratiecase #${caseId} is aangemaakt voor opvolging.`
      trace.push({ step: 'handoff', detail: `Case #${caseId} opgeslagen` })
    }
  }
  await env.DEMO_DB.prepare(
    'INSERT INTO demo_sessions(id,issue,order_id,updated_at) VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET issue=excluded.issue,order_id=excluded.order_id,updated_at=excluded.updated_at',
  )
    .bind(id, issue, orderId, now)
    .run()
  return json({
    messages: [answer],
    mode: 'demo',
    order,
    case_id: caseId,
    quick_replies: replies,
    trace,
  })
}

export async function handleCloudDemo({ request, env }) {
  const path = new URL(request.url).pathname
  const method = request.method.toUpperCase()
  const now = Math.floor(Date.now() / 1000)
  if (!env.DEMO_DB) return json({ detail: 'Demo database is not configured' }, 503)
  if (path === '/api/status' && method === 'GET') {
    let caseStore = 'ok'
    try {
      await env.DEMO_DB.prepare('SELECT 1 FROM demo_cases LIMIT 1').first()
    } catch {
      caseStore = 'unavailable'
    }
    return json({
      mode: 'demo',
      deployment: 'cloudflare',
      retail_api: 'ok',
      rasa: 'not_configured',
      case_store: caseStore,
    })
  }
  if (path === '/api/examples' && method === 'GET')
    return json(
      Object.values(exampleOrders).map((order) => ({
        order_id: order.order_id,
        status: order.status,
        issue_type: order.issue_type || 'voorbeeldscenario',
      })),
    )
  if (path === '/api/chat' && method === 'POST') {
    await cleanup(env.DEMO_DB, now)
    return chat(request, env, now)
  }
  if (path === '/api/cases' && method === 'GET') {
    const id = sessionId(request)
    if (!id) return json({ detail: 'Demo session required' }, 401)
    await cleanup(env.DEMO_DB, now)
    const rows = await env.DEMO_DB.prepare(
      'SELECT id,session_id,issue,reason,order_id,summary,status,assignee,created_at FROM demo_cases WHERE session_id=? ORDER BY id DESC LIMIT 20',
    )
      .bind(id)
      .all()
    return json(rows.results)
  }
  const match = path.match(/^\/api\/cases\/(\d+)$/)
  if (match && method === 'PATCH') {
    const id = sessionId(request)
    if (!id) return json({ detail: 'Demo session required' }, 401)
    const limited = await limit(request, env, id, now)
    if (limited) return limited
    let body
    try {
      const raw = await request.text()
      if (raw.length > 1000) return json({ detail: 'Case update too long' }, 413)
      body = JSON.parse(raw)
    } catch {
      return json({ detail: 'Invalid JSON' }, 400)
    }
    if (
      !body ||
      typeof body !== 'object' ||
      (body.status != null && !CASE_STATUSES.includes(body.status)) ||
      (body.assignee != null && typeof body.assignee !== 'string')
    )
      return json({ detail: 'Invalid case update' }, 422)
    const current = await env.DEMO_DB.prepare(
      'SELECT id FROM demo_cases WHERE id=? AND session_id=? AND created_unix>=?',
    )
      .bind(Number(match[1]), id, now - WEEK)
      .first()
    if (!current) return json({ detail: 'Case not found' }, 404)
    const assignee = body.assignee == null ? null : body.assignee.trim() ? 'Demo medewerker' : ''
    await env.DEMO_DB.prepare(
      'UPDATE demo_cases SET status=COALESCE(?,status), assignee=COALESCE(?,assignee) WHERE id=? AND session_id=?',
    )
      .bind(body.status ?? null, assignee, current.id, id)
      .run()
    const updated = await env.DEMO_DB.prepare(
      'SELECT id,session_id,issue,reason,order_id,summary,status,assignee,created_at FROM demo_cases WHERE id=? AND session_id=?',
    )
      .bind(current.id, id)
      .first()
    return json(updated)
  }
  return json({ detail: 'Not found' }, 404)
}
