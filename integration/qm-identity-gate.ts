import { createServer, request as httpRequest, type IncomingMessage } from 'node:http';
import { createHmac, scryptSync, timingSafeEqual } from 'node:crypto';
import { readFileSync, statSync } from 'node:fs';

export type GateConfig = {
  origin: string;
  port: number;
  upstreamPort: number;
  org: string;
  sessionSecret: string;
  users: Record<'admin' | 'intern', { principal: string; salt: string; hash: string }>;
};

export function validateConfig(config: GateConfig): GateConfig {
  const origin = new URL(config.origin);
  if (origin.protocol !== 'https:' || origin.origin !== config.origin || origin.username || origin.password
    || !Number.isInteger(config.port) || config.port < 1024 || config.port > 65535
    || !Number.isInteger(config.upstreamPort) || config.upstreamPort < 1024 || config.upstreamPort > 65535
    || !config.org || config.sessionSecret.length < 32) throw new Error('Invalid identity gateway configuration');
  for (const name of ['admin', 'intern'] as const) {
    const user = config.users[name];
    if (!user?.principal || !/^[a-f0-9]{32}$/.test(user.salt) || !/^[a-f0-9]{64}$/.test(user.hash)) {
      throw new Error('Invalid account configuration');
    }
  }
  if (config.users.admin.principal === config.users.intern.principal) throw new Error('Accounts must have distinct principals');
  return config;
}

export function authenticate(header: string | undefined, config: GateConfig): string | null {
  if (!header?.startsWith('Basic ') || header.length > 1024) return null;
  const decoded = Buffer.from(header.slice(6), 'base64').toString('utf8');
  const colon = decoded.indexOf(':');
  if (colon < 0) return null;
  const name = decoded.slice(0, colon);
  if (name !== 'admin' && name !== 'intern') return null;
  const user = config.users[name];
  const actual = scryptSync(decoded.slice(colon + 1), user.salt, 32);
  return timingSafeEqual(actual, Buffer.from(user.hash, 'hex')) ? user.principal : null;
}

export function portalCookie(config: GateConfig, principal: string, now = Date.now()): string {
  const seconds = Math.floor(now / 1000);
  const claims = { k: 'session', sub: principal, org: config.org, iat: seconds, auth: seconds, exp: seconds + 60 };
  const key = createHmac('sha256', config.sessionSecret).update('portal.session.v1').digest();
  const body = Buffer.from(JSON.stringify(claims)).toString('base64url');
  const signature = createHmac('sha256', key).update(body).digest('base64url');
  return `portal_session=${body}.${signature}`;
}

export function allowedRequest(req: Pick<IncomingMessage, 'url' | 'headers' | 'method'>, config: GateConfig): boolean {
  if (!['GET', 'HEAD', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'].includes(req.method ?? '')) return false;
  const raw = req.url ?? '/';
  if (!raw.startsWith('/') || raw.startsWith('//') || /[\\\x00-\x20]/.test(raw)) return false;
  let path: string;
  try { path = decodeURIComponent(raw.split('?')[0]); } catch { return false; }
  if (path.split('/').some(segment => segment === '.' || segment === '..')
    || path.includes('//') || path.includes('\\') || path.includes('%')) return false;
  if (!/^\/(?:$|me$|api(?:\/|$)|assets\/|brand-mark\.svg$|favicon\.ico$|favicon\.svg$|manifest\.webmanifest$|robots\.txt$)/.test(path)) return false;
  if (/^\/(?:auth|admin|v1|signin|playground|apps|deployments)(?:\/|$)/i.test(path)
    || /(?:^|\/)(?:admin|auth|share[^/]*|impersonate|fork|adopt|deployments|apps)(?:\/|$)/i.test(path)) return false;
  if (req.headers.origin && req.headers.origin !== config.origin) return false;
  const site = req.headers['sec-fetch-site'];
  if ((site === 'cross-site' || site === 'same-site') && req.headers['sec-fetch-mode'] !== 'navigate') return false;
  if (!['GET', 'HEAD', 'OPTIONS'].includes(req.method ?? '') && req.headers.origin !== config.origin) return false;
  return true;
}

export function createGate(config: GateConfig) {
  validateConfig(config);
  let failedWindow = 0;
  let failedCount = 0;
  const server = createServer((req, res) => {
    res.setHeader('cache-control', 'no-store');
    res.setHeader('referrer-policy', 'no-referrer');
    if (!allowedRequest(req, config)) { res.writeHead(403).end('Forbidden'); return; }
    if (!req.headers.authorization) {
      res.writeHead(401, { 'www-authenticate': 'Basic realm="Scoped QM", charset="UTF-8"' }).end('Sign in');
      return;
    }
    const now = Date.now();
    if (now - failedWindow > 60_000) { failedWindow = now; failedCount = 0; }
    const principal = authenticate(req.headers.authorization, config);
    if (!principal) {
      if (failedCount >= 20) { res.writeHead(429, { 'retry-after': '60' }).end('Try later'); return; }
      failedCount++;
      res.writeHead(401, { 'www-authenticate': 'Basic realm="Scoped QM", charset="UTF-8"' }).end('Sign in');
      return;
    }
    const headers: Record<string, string> = {
      host: `localhost:${config.upstreamPort}`,
      cookie: portalCookie(config, principal),
    };
    for (const name of ['accept', 'accept-language', 'content-type', 'content-length', 'last-event-id', 'range', 'if-range']) {
      const value = req.headers[name];
      if (typeof value === 'string') headers[name] = value;
    }
    if (req.headers.origin) headers.origin = `http://localhost:${config.upstreamPort}`;
    const upstream = httpRequest({ hostname: '127.0.0.1', port: config.upstreamPort, path: req.url, method: req.method, headers }, response => {
      const outgoing: Record<string, string | string[]> = {};
      for (const name of ['content-type', 'content-length', 'content-encoding', 'content-range', 'accept-ranges', 'content-security-policy', 'x-content-type-options']) {
        const value = response.headers[name];
        if (value !== undefined) outgoing[name] = value;
      }
      const location = response.headers.location;
      if (location && location.startsWith('/') && !location.startsWith('//')) outgoing.location = location;
      res.writeHead(response.statusCode ?? 502, outgoing);
      response.pipe(res);
    });
    upstream.on('error', () => {
      if (!res.headersSent) res.writeHead(502).end('QM unavailable');
      else res.destroy();
    });
    upstream.setTimeout(120_000, () => upstream.destroy(new Error('Upstream timeout')));
    req.on('aborted', () => upstream.destroy());
    res.on('close', () => upstream.destroy());
    req.pipe(upstream);
  });
  server.requestTimeout = 120_000;
  server.headersTimeout = 15_000;
  return server;
}

if (import.meta.main) {
  const path = process.env.SCOPED_GATE_CONFIG;
  if (!path || (statSync(path).mode & 0o077) !== 0) throw new Error('Private gateway configuration required');
  const config = validateConfig(JSON.parse(readFileSync(path, 'utf8')));
  createGate(config).listen(config.port, '127.0.0.1', () => console.log('Scoped QM identity gateway listening on loopback'));
}
