import { readFileSync, realpathSync, statSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createGate, portalCookie, validateConfig } from '../integration/qm-identity-gate.ts';

export function readConfig(path: string | undefined) {
  if (!path || !isAbsolute(path)) throw new Error('SCOPED_GATE_CONFIG must be an absolute private file path');
  const canonical = realpathSync(path);
  const repository = realpathSync(resolve(dirname(fileURLToPath(import.meta.url)), '..'));
  const location = relative(repository, canonical);
  const info = statSync(canonical);
  if (!(location === '..' || location.startsWith(`..${sep}`)) || !info.isFile()
    || (info.mode & 0o777) !== 0o600 || info.uid !== process.getuid?.()) {
    throw new Error('Gateway configuration must be outside the repository, owned by this user, and mode 0600');
  }
  const config = validateConfig(JSON.parse(readFileSync(canonical, 'utf8')));
  if (config.port === config.upstreamPort) throw new Error('Gateway and upstream ports must differ');
  return config;
}

export async function verifyUpstream(config: ReturnType<typeof readConfig>) {
  const url = `http://127.0.0.1:${config.upstreamPort}/`;
  const anonymous = await fetch(url, {
    headers: { host: `localhost:${config.upstreamPort}`, accept: 'application/json' },
    redirect: 'manual', signal: AbortSignal.timeout(5_000),
  });
  if (anonymous.status !== 401) throw new Error('QM must be running with local auth bypass disabled; refusing preview');
  await anonymous.body?.cancel();
  const authenticated = await fetch(url, {
    headers: { host: `localhost:${config.upstreamPort}`, cookie: portalCookie(config, config.users.admin.principal) },
    redirect: 'manual', signal: AbortSignal.timeout(5_000),
  });
  if (authenticated.status !== 200) throw new Error('QM did not accept the configured portal session; refusing preview');
  await authenticated.body?.cancel();
}

if (import.meta.main) {
  try {
    const config = readConfig(process.env.SCOPED_GATE_CONFIG);
    await verifyUpstream(config);
    createGate(config).listen(config.port, '127.0.0.1', () => console.log('Scoped QM identity gateway listening on loopback'));
  } catch {
    console.error('Scoped preview refused: check the external 0600 config, running authenticated QM, and matching portal session secret');
    process.exitCode = 1;
  }
}
