import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { DatabaseSync } from 'node:sqlite'
import { onRequest } from '../functions/api/[[path]].js'

function database() {
  const sqlite = new DatabaseSync(':memory:')
  sqlite.exec(readFileSync(new URL('../migrations/0001_public_demo.sql', import.meta.url), 'utf8'))
  return {
    sqlite,
    prepare(sql) {
      let args = []
      return {
        bind(...values) {
          args = values
          return this
        },
        first() {
          return sqlite.prepare(sql).get(...args) ?? null
        },
        all() {
          return { results: sqlite.prepare(sql).all(...args) }
        },
        run() {
          const result = sqlite.prepare(sql).run(...args)
          return { meta: { last_row_id: Number(result.lastInsertRowid) } }
        },
      }
    },
  }
}

const A = 'a'.repeat(32)
const B = 'b'.repeat(32)
function call(env, path, method = 'GET', body, session = A) {
  const request = new Request(`https://support.nickcloud.dev${path}`, {
    method,
    headers: {
      'content-type': 'application/json',
      'x-demo-session': session,
      'cf-connecting-ip': '198.51.100.5',
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  return onRequest({ request, env })
}

test('D1 portfolio demo follows a multi-step issue and limits case access to the visitor', async () => {
  const db = database()
  const env = { DEMO_DB: db, DEMO_RATE_SECRET: 'test-secret' }
  try {
    const status = await (await call(env, '/api/status')).json()
    assert.equal(status.deployment, 'cloudflare')
    const first = await (
      await call(env, '/api/chat', 'POST', { session_id: A, message: 'Er ontbreekt een artikel' })
    ).json()
    assert.match(first.messages[0], /voorbeeldordernummer/)
    const second = await (
      await call(env, '/api/chat', 'POST', { session_id: A, message: 'KV-10482' })
    ).json()
    assert.equal(second.order.order_id, 'KV-10482')
    assert.equal(second.mode, 'demo')
    assert.ok(second.case_id > 0)
    assert.match(second.messages[0], /Demonstratiecase/)
    const ownCases = await (await call(env, '/api/cases')).json()
    assert.equal(ownCases.length, 1)
    assert.match(ownCases[0].summary, /voorbeeldorder KV-10482/)
    const otherCases = await (await call(env, '/api/cases', 'GET', undefined, B)).json()
    assert.equal(otherCases.length, 0)
    assert.equal(
      (await call(env, `/api/cases/${second.case_id}`, 'PATCH', { status: 'resolved' }, B)).status,
      404,
    )
    const updated = await (
      await call(env, `/api/cases/${second.case_id}`, 'PATCH', {
        status: 'investigating',
        assignee: 'actual-person-name',
      })
    ).json()
    assert.equal(updated.status, 'investigating')
    assert.equal(updated.assignee, 'Demo medewerker')
  } finally {
    db.sqlite.close()
  }
})

test('public demo rejects malformed messages and avoids storing raw visitor text', async () => {
  const db = database()
  const env = { DEMO_DB: db, DEMO_RATE_SECRET: 'test-secret' }
  try {
    assert.equal(
      (await call(env, '/api/chat', 'POST', { session_id: 'guessable', message: 'hi' })).status,
      422,
    )
    assert.equal(
      (await call(env, '/api/chat', 'POST', { session_id: A, message: 'x'.repeat(1001) })).status,
      422,
    )
    await call(env, '/api/chat', 'POST', {
      session_id: A,
      message: 'Mijn e-mail is me@example.com; artikel beschadigd KV-20991',
    })
    const rows = db.sqlite.prepare('SELECT summary FROM demo_cases').all()
    assert.equal(rows.length, 1)
    assert.doesNotMatch(rows[0].summary, /me@example.com/)
    assert.equal(db.sqlite.prepare('SELECT COUNT(*) AS n FROM demo_sessions').get().n, 1)
  } finally {
    db.sqlite.close()
  }
})

test('public demo fails closed when its rate limit secret is missing', async () => {
  const db = database()
  try {
    assert.equal(
      (await call({ DEMO_DB: db }, '/api/chat', 'POST', { session_id: A, message: 'Hi' })).status,
      503,
    )
  } finally {
    db.sqlite.close()
  }
})
