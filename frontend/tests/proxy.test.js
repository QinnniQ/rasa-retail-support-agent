import test from 'node:test'
import assert from 'node:assert/strict'
import { onRequest } from '../functions/api/[[path]].js'

test('proxy rejects unconfigured or disallowed destinations', async () => {
  const request = new Request('https://demo.example/api/chat')
  assert.equal((await onRequest({ request, env: {} })).status, 503)
  assert.equal(
    (await onRequest({ request, env: { API_ORIGIN: 'http://api.example' } })).status,
    503,
  )
  assert.equal(
    (
      await onRequest({
        request: new Request('https://demo.example/internal/cases'),
        env: { API_ORIGIN: 'https://api.example' },
      })
    ).status,
    404,
  )
})

test('proxy forwards allowlisted API route without browser cookies', async () => {
  const originalFetch = globalThis.fetch
  let captured
  globalThis.fetch = async (target, init) => {
    captured = { target: String(target), init }
    return new Response('{"ok":true}', { headers: { 'content-type': 'application/json' } })
  }
  try {
    const request = new Request('https://demo.example/api/cases/7?view=full', {
      headers: { cookie: 'private=1', 'x-support-token': 'test' },
    })
    const response = await onRequest({ request, env: { API_ORIGIN: 'https://api.example' } })
    assert.equal(response.status, 200)
    assert.equal(captured.target, 'https://api.example/api/cases/7?view=full')
    assert.equal(captured.init.headers.get('x-support-token'), 'test')
    assert.equal(captured.init.headers.get('cookie'), null)
    assert.equal(captured.init.redirect, 'manual')
  } finally {
    globalThis.fetch = originalFetch
  }
})
