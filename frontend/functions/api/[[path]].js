// Cloudflare Pages proxy for a separately hosted HTTPS FastAPI service.
export async function onRequest({ request, env }) {
  const path = new URL(request.url).pathname
  if (!/^\/api\/(chat|status|examples|cases(?:\/\d+)?)$/.test(path)) {
    return new Response('Not found', { status: 404 })
  }
  if (!env.API_ORIGIN) return new Response('API origin is not configured', { status: 503 })
  let origin
  try {
    origin = new URL(env.API_ORIGIN)
  } catch {
    return new Response('Invalid API origin', { status: 503 })
  }
  if (origin.protocol !== 'https:' || origin.username || origin.password) {
    return new Response('API origin must use HTTPS', { status: 503 })
  }
  const target = new URL(path, origin)
  target.search = new URL(request.url).search
  const headers = new Headers()
  for (const name of ['accept', 'content-type', 'x-support-token']) {
    const value = request.headers.get(name)
    if (value) headers.set(name, value)
  }
  const response = await fetch(target, {
    method: request.method,
    headers,
    body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
    redirect: 'manual',
  })
  return new Response(response.body, {
    status: response.status,
    headers: {
      'content-type': response.headers.get('content-type') || 'application/json',
      'cache-control': 'no-store',
    },
  })
}
