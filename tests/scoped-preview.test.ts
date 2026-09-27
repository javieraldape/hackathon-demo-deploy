import { afterEach, expect, test } from 'bun:test';
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer, type Server } from 'node:http';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { readConfig, verifyUpstream } from '../scripts/run-scoped-preview.ts';

const config = {
  origin: 'https://preview.example.com', port: 8188, upstreamPort: 8129,
  org: 'fixture', sessionSecret: 'fixture-only-session-secret-32-characters',
  users: {
    admin: { principal: 'admin@example.com', salt: 'a'.repeat(32), hash: 'a'.repeat(64) },
    intern: { principal: 'intern@example.com', salt: 'b'.repeat(32), hash: 'b'.repeat(64) },
  },
};
const directories: string[] = [];
const servers: Server[] = [];
afterEach(() => {
  for (const server of servers.splice(0)) server.close();
  for (const path of directories.splice(0)) rmSync(path, { recursive: true, force: true });
});

function privateConfig(value = config) {
  const directory = mkdtempSync(join(tmpdir(), 'scoped-preview-'));
  directories.push(directory);
  const path = join(directory, 'gate.json');
  writeFileSync(path, JSON.stringify(value), { mode: 0o600 });
  return path;
}

test('requires an external private configuration', () => {
  expect(readConfig(privateConfig())).toEqual(config);
  expect(() => readConfig(undefined)).toThrow();
  expect(() => readConfig('relative.json')).toThrow();
  const path = privateConfig();
  chmodSync(path, 0o644);
  expect(() => readConfig(path)).toThrow('mode 0600');
  expect(() => readConfig(import.meta.filename)).toThrow('outside the repository');
});

test('rejects matching upstream and gateway ports', () => {
  expect(() => readConfig(privateConfig({ ...config, port: config.upstreamPort }))).toThrow('ports must differ');
});

async function upstream(anonymous: number, authenticated: number) {
  const server = createServer((req, res) => res.writeHead(req.headers.cookie ? authenticated : anonymous).end());
  servers.push(server);
  await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Missing fixture port');
  return { ...config, upstreamPort: address.port };
}

test('accepts an authenticated upstream with a valid session', async () => {
  await verifyUpstream(await upstream(401, 200));
});

test('refuses a bypass portal or unexpected upstream', async () => {
  for (const status of [200, 302, 404, 500]) {
    await expect(verifyUpstream(await upstream(status, 200))).rejects.toThrow('bypass disabled');
  }
});

test('refuses an upstream rejecting the configured session', async () => {
  await expect(verifyUpstream(await upstream(401, 401))).rejects.toThrow('configured portal session');
});
