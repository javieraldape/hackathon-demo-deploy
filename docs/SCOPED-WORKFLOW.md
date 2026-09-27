# Scoped workflow operations

## Identity and recall

`integration/qm-identity-gate.ts` is the account gateway, not the former shared admin preview. It listens on loopback, normally port **8188**, and authenticates the `admin` and `intern` HTTP Basic accounts. Run it only behind the exact configured HTTPS origin. Its private JSON configuration is selected by `SCOPED_GATE_CONFIG` and contains `origin`, `port`, `upstreamPort`, `org`, `sessionSecret`, and distinct `users.admin`/`users.intern` entries with `principal`, `salt`, and `hash`. These are operator-managed values, not committed sample credentials. The file must deny group/world access. Account password hashes use the gateway's scrypt format.

The gateway drops caller cookies and identity headers and signs a short-lived `portal_session` for the verified principal. QM must use the matching signing secret and organization, admit those actual principals, and run with `PORTAL_LOCAL_AUTH_BYPASS=0`. Public requests must not reach its raw portal/API ports. Gateway path and origin restrictions block admin/auth/sharing and other unsupported routes; this is a bounded demo gateway, not a general identity provider.

Configure QM's external memory provider as **read-only**, with capture off and strict failure handling (`failOpen: false`). Its read operation is `qm_recall`, forwarding `query`, trusted `acting_user`, searched `qm_scope`, and the turn's `conversation_scope`. Configure the optional read mappings `scopeArg: "qm_scope"` and `conversationScopeArg: "conversation_scope"`. Identity and conversation context come from QM's authenticated turn, never user-supplied tool arguments. QM's local notebook is not GBrain and must not become a silent fallback for brain questions.

In the existing GBrain, the operator configures `scoped.qm_bridge` using the registered bridge client ID, exact authenticated principals, and the attested personal-scope format:

```json
{
  "clientId": "<registered bridge client ID>",
  "verifiedPersonalScopeFormat": "personal:<principal>",
  "principals": {
    "admin": "<verified admin principal>",
    "intern": "<verified intern principal>"
  }
}
```

Verify the actual signed identities and personal-scope binding before setting this mapping. A shared OAuth credential cannot itself prove that a forwarded per-user claim is genuine; QM supplies that trust boundary.

The bridge client's grant must restrict operations to exactly `qm_recall`, with the expected source reads and full MCP surface. Only a rostered admin whose **both** scopes equal `personal:<that principal>` gets all scoped sources plus existing `default` memory. The intern, rooms, unknown/missing identities, mismatches, and incomplete grants fall back to `mvp-shared` only. Admin personal recall supplements normal retrieval with authorized private pages/facts without relaxing GBrain's global private-visibility filters. This is a retrieval operation, not a promise to return every document on every query.

Source names are fixed by code: `mvp-shared`, `mvp-hr-payroll`, `mvp-juniper`, and `mvp-vault`, alongside existing `default` memory. Named sources remain distinct; existing member credentials do not inherit the new QM admin role. Register/reconcile sources and dedicated clients deliberately through the trusted operator path. The installer does not provision this runtime policy. Do not re-provision existing sources or reuse old broad credentials.

## Telegram capture

Use the existing allowlisted Telegram bot and the existing GBrain HTTP MCP server. Configure the capture plugin from the patched GBrain source at `integration/openclaw-telegram-capture`, enable its plugin entry, and restrict `commands.ownerAllowFrom` to the same verified numeric owner already permitted by the channel. A DM allowlist alone does not mark a command sender as owner. No wildcard or username substitutes for the verified owner identity.

The gateway process needs these private environment variables:

- `GBRAIN_TELEGRAM_CAPTURE_MCP_URL` and `GBRAIN_TELEGRAM_CAPTURE_TOKEN_URL`: same-origin endpoints; HTTPS, or the supported loopback HTTP form.
- `GBRAIN_TELEGRAM_CAPTURE_CLIENT_ID` and `GBRAIN_TELEGRAM_CAPTURE_CLIENT_SECRET`: a dedicated client, never the QM client.
- `GBRAIN_TELEGRAM_MEDIA_DIR`: the canonical local inbound-media directory.

The capture client requires write scope, host-brain binding, `mvp-vault` write source, full MCP surface, client-credentials authentication, and exactly the `capture_telegram_transcript` operation allow-list. The resident server also needs its verified persistence writer and `ANTHROPIC_API_KEY`/`TYPESAFE_API_KEY`. The operation uses that existing engine and supported persistence APIs; do not start a CLI ingest process against the live PGLite database.

Remove the Telegram model's ability to call generic writes (`remember`, `put_page`, extraction/upload writers), admin operations, or shell/HTTP/filesystem paths that can bypass these grants or read credentials. A separate read-only credential is appropriate for ordinary recall. Hiding a tool or adding a prompt prohibition is insufficient: denied calls must fail at dispatch, including when binding fails and ordinary chat resumes.

The owner flow is:

1. Send `/capture_meeting arm` in the allowlisted DM, approve any native binding request, and confirm the bound receipt. For a non-sensitive title that shared readers should be able to search, use `/capture_meeting arm --public-title <exact meeting title>` instead. That owner command explicitly authorizes only the title for shared lookup; transcript text cannot grant this approval. Close an existing binding before changing its title approval.
2. Send one pasted transcript message or one UTF-8 `.txt` document of at most 20,000 bytes.
3. Wait for a committed receipt or explicit failure; an ordinary agent reply is not evidence of capture.
4. Send `/capture_meeting done`, then verify ordinary chat resumes.

Inline `/capture_meeting <transcript>` is refused because that native command context lacks a transport message ID. Staged documents must be a single regular, non-symlink `text/plain` file within the configured inbox, with valid UTF-8. PDF, voice, image, multiple attachments, and oversized inputs are unsupported. Duplicate/reserved source identities are refused rather than silently overwritten; never change identities merely to bypass duplicate protection.

An explicitly approved public title must be a bounded single line matching the transcript's marked first-line title. It is attached only to facts independently classified as shared, and its owner attestation is recorded with capture provenance. If a named transcript has shared facts but its title lacks either confident classifier approval or explicit owner approval, capture refuses before writing. Follow the actionable response rather than repeatedly submitting the same file to obtain a different classifier verdict.

Both native OpenClaw **2026.9.6** compatibility patches are required, in numeric order, followed by a gateway restart. They fix Telegram runtime ownership during arm/detach and persist binding changes before changing in-memory state. Test arm, done, and ordinary chat; native binding state is under `telegram.thread-bindings`, not the generic conversation-binding table.

## Classification, publication, and recovery

Haiku extracts atomic facts with evidence; hosted Jev classifies them, and deterministic code chooses destinations. Named-scope unions are preserved. Unsupported sensitive facts and low-confidence decisions stay in vault, and every original stays in vault. Malformed/incomplete classification or provider failure aborts publication. The vault guarantee is **GBrain placement**, not erasure from Telegram/OpenClaw session or media retention or from configured provider processing. Keep those additional copies and external data flows in the operator's privacy review.

Classification precedes writes, and publication verifies committed pages through readback. An incomplete write/readback retains private audit state and `$GBRAIN_HOME/.scoped/publication-blocked`. The shared MCP dispatcher checks that marker around remote reads, including generic read tools; inaccessible marker state fails closed. Leave reads closed and reconcile the recorded publication or restore a consistent backup. Never remove a marker merely to make the demo work, retry as a generic shared write, or launch a second datastore process.

An optional operator-only `amend_scoped_context` operation can add a public context index for an **existing committed** ingestion. It accepts only that manifest's `source_id` and SHA-256 `source_hash`, verifies the vault original, and sends only its explicitly marked first-line title/evidence for a separate Jev public verdict. The index contains that approved title and the manifest's already-public shared bodies/references, never private pages. A matching committed replay is idempotent; a mismatch refuses. Failed publication retains the same read block.

If an amendment is needed, use a separate temporary confidential client registered through the already-running server's authenticated admin API with its cookie/CSRF checks. Require admin scope, shared write binding, shared+vault read grants, full surface, and exactly `amend_scoped_context` as its operation allow-list. Neither QM nor capture credentials qualify. Revoke the temporary client after verification. The patched GBrain `docs/SCOPED-CONTEXT-AMENDMENT.md` gives the wire contract; this repository does not claim an amendment has been run on a new target.
