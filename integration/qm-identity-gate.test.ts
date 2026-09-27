import { afterAll, beforeAll, expect, test } from 'bun:test';
import { createServer, request } from 'node:http';
import { scryptSync } from 'node:crypto';
import { authenticate, createGate, portalCookie, validateConfig, type GateConfig } from './qm-identity-gate.ts';
const qmSource = process.env.QM_SOURCE;
if (!qmSource) throw new Error('Set QM_SOURCE to the pinned, patched QM checkout for session compatibility tests');
const { deriveKey, openSession } = await import(`${qmSource}/plugins/portal/src/session.ts`);

const salt = '0123456789abcdef0123456789abcdef';
const account = (principal: string, password: string) => ({ principal, salt, hash: scryptSync(password, salt, 32).toString('hex') });
const config: GateConfig = {
  origin: 'https://demo.example.test', port: 8189, upstreamPort: 8129, org: 'demo-org',
  sessionSecret: 'synthetic-session-secret-with-more-than-32-characters',
  users: { admin: account('admin-principal', 'synthetic-admin-password'), intern: account('intern-principal', 'synthetic-intern-password') },
};
const basic = (name: string, password: string) => `Basic ${Buffer.from(`${name}:${password}`).toString('base64')}`;
const upstream = createServer((req, res) => {
  res.setHeader('content-type', 'application/json');
  res.setHeader('set-cookie', 'portal_session=must-not-reach-browser');
  res.end(JSON.stringify(req.headers));
});
let gate: ReturnType<typeof createGate>;
let url: string;

beforeAll(async () => {
  await new Promise<void>(resolve => upstream.listen(0, '127.0.0.1', resolve));
  config.upstreamPort = (upstream.address() as { port: number }).port;
  gate = createGate(config);
  await new Promise<void>(resolve => gate.listen(0, '127.0.0.1', resolve));
  url = `http://127.0.0.1:${(gate.address() as { port: number }).port}`;
});
afterAll(() => { gate.close(); upstream.close(); });

test('authenticates two exact usernames with different credentials', () => {
  expect(authenticate(basic('admin', 'synthetic-admin-password'), config)).toBe('admin-principal');
  expect(authenticate(basic('intern', 'synthetic-intern-password'), config)).toBe('intern-principal');
  expect(authenticate(basic('admin', 'synthetic-intern-password'), config)).toBeNull();
  expect(authenticate(basic('ADMIN', 'synthetic-admin-password'), config)).toBeNull();
  expect(authenticate(undefined, config)).toBeNull();
});

test('creates a portal-compatible short-lived session with second-based expiry', () => {
  const now = Date.now();
  const token = portalCookie(config, 'intern-principal', now).split('=')[1];
  const key = deriveKey(config.sessionSecret, 'portal.session.v1');
  expect(openSession(token, key, now, config.org)?.sub).toBe('intern-principal');
  expect(openSession(token, key, now + 61_000, config.org)).toBeNull();
  expect(openSession(token + 'x', key, now, config.org)).toBeNull();
});

test('rejects absent credentials, privileged paths, and cross-site writes', async () => {
  expect((await fetch(url + '/me')).status).toBe(401);
  const headers = { authorization: basic('intern', 'synthetic-intern-password') };
  for (const path of ['/admin', '/auth/impersonate?target=admin', '/v1/sessions', '/signin', '/api/sessions/example/share']) {
    expect((await fetch(url + path, { headers })).status).toBe(403);
  }
  expect((await fetch(url + '/api/turn', { method: 'POST', headers })).status).toBe(403);
  expect((await fetch(url + '/api/turn', { method: 'POST', headers: { ...headers, origin: 'https://evil.example' } })).status).toBe(403);
});

test('replaces all supplied identity material and never sends a session to the browser', async () => {
  const response = await fetch(url + '/api/turn', { method: 'POST', headers: {
    authorization: basic('intern', 'synthetic-intern-password'), origin: config.origin,
    cookie: 'portal_session=forged; webuiuser=admin', 'x-portal-identity': 'forged',
    'x-as-principal': 'admin', 'x-forwarded-for': 'trusted', 'x-agent-capability': 'forged',
    'content-type': 'application/json',
  }, body: '{"principalId":"admin"}' });
  expect(response.status).toBe(200);
  expect(response.headers.get('set-cookie')).toBeNull();
  expect(response.headers.get('cache-control')).toBe('no-store');
  const headers = await response.json();
  for (const name of ['authorization', 'x-portal-identity', 'x-as-principal', 'x-forwarded-for', 'x-agent-capability']) expect(headers[name]).toBeUndefined();
  expect(headers.origin).toBe(`http://localhost:${config.upstreamPort}`);
  const claims = openSession(headers.cookie.split('=')[1], deriveKey(config.sessionSecret, 'portal.session.v1'), Date.now(), config.org);
  expect(claims?.sub).toBe('intern-principal');
});

test('refuses an unsafe configuration or shared principal identity', () => {
  expect(() => validateConfig({ ...config, origin: 'http://demo.example.test' })).toThrow();
  expect(() => validateConfig({ ...config, users: { admin: config.users.admin, intern: config.users.admin } })).toThrow();
});

test('rejects noncanonical paths before the portal can normalize them', async () => {
  for (const path of ['/./admin', '/%2e/admin', '/./auth/admin-login', '/./v1/background-work', '/api/../admin', '/api/%252e/admin', '/api/sessions/x/share-link']) {
    const status = await new Promise<number | undefined>((resolve, reject) => {
      const call = request(url, { path, headers: { authorization: basic('intern', 'synthetic-intern-password') } }, response => {
        response.resume();
        response.on('end', () => resolve(response.statusCode));
      });
      call.on('error', reject);
      call.end();
    });
    expect(status).toBe(403);
  }
});

test('anonymous attempts cannot lock out a valid account', async () => {
  for (let i = 0; i < 21; i++) await fetch(url + '/me');
  expect((await fetch(url + '/me')).status).toBe(401);
  for (let i = 0; i < 21; i++) await fetch(url + '/me', { headers: { authorization: basic('intern', 'wrong-password') } });
  expect((await fetch(url + '/me', { headers: { authorization: basic('intern', 'wrong-password') } })).status).toBe(429);
  const fresh = await fetch(url + '/');
  expect(fresh.status).toBe(401);
  expect(fresh.headers.get('www-authenticate')).toContain('Basic');
  expect((await fetch(url + '/me', { headers: { authorization: basic('intern', 'synthetic-intern-password') } })).status).toBe(200);
  expect((await fetch(url + '/me', { headers: { authorization: basic('admin', 'synthetic-admin-password') } })).status).toBe(200);
});
