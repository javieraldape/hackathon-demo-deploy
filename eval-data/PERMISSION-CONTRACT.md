# Scoped Brain permission contract — preparation v1

This is a planning artifact, not enforcement code. It operationalizes the supplied implementation plan v5.2 without changing its founder decisions. Evaluation labels must be authored independently of classifier output. The owner’s local CLI is outside the member-access threat model.

## Reader sets

| Fact or condition | Expected member readers | Required negative check |
| --- | --- | --- |
| Ordinary fact, no labels, not Personal or uncertain | All members through shared | Ordinary content remains answerable after nearby sensitive content is removed |
| HR/Payroll only | Head of People and CEO | Intern and unrelated employees receive no restricted fact |
| Leadership only | CEO, Head of People and CFO | Manager without Leadership membership is denied |
| Juniper only | CEO, CFO and engineering lead | HR without Juniper membership is denied |
| Customer terms after activation | CEO, CFO and account executives | Other members cannot recover prior shared copies |
| Multiple named scope labels | Union of those scopes’ members, as D16 explicitly specifies | A person in neither scope is denied; a person in either scope is allowed |
| Own health, family, bank/ID details or medical leave | The uniquely identified member subject only | HR, CEO and manager have no automatic override |
| Personal fact whose subject is not a member, or cannot be uniquely resolved | No member; vault pending resolution | No fallback to shared or named scopes |
| Uncertain fact, including uncertainty alongside other labels | No member; vault | No copies in any member-readable area |
| Pay or performance-plan fact about exactly one member, labelled only HR/Payroll, not a complaint | HR/Payroll readers plus the subject and their current direct manager, if mapped to a member | Former manager and unrelated managers denied |
| Complaint, even about a single member | Readers of applicable named scopes; no subject/manager-copy exception | Complaint classification must suppress pay/performance-copy routing |
| Fact with another named label in addition to HR/Payroll | Union of named-scope readers; no subject/manager-copy exception | Being subject or manager alone grants nothing |
| Sensitive original, including its source title, slug and history | No member; vault | Direct lookup, deleted-version reads, citations and metadata cannot expose it |

Precedence: uncertainty or unresolved Personal ownership goes to vault; otherwise Personal overrides named scopes; otherwise apply named-scope union and the narrow copy exception; only an unlabeled non-Personal certain fact may be shared. Several subjects never qualify for the single-person copy exception. A mixed sensitive sentence should be split into atomic facts; if Personal ownership remains ambiguous, quarantine it.

Union is deliberate, not “must belong to every scope.” A fact tagged HR and Juniper is visible to HR-only and Juniper-only members. Tests must encode this policy honestly rather than call intended union access a leak. This tradeoff should be explained in the demo if shown.

## Changes and failed updates

- Re-ingestion or adding a restrictive scope must not accidentally enlarge the effective reader set. Record actual readers as well as storage areas; absence from shared alone is insufficient.
- Explicit grants, such as adding an approved scope member, are authorized reader-set expansions and must be distinguished from automatic reclassification. Test the grant on the next request.
- A manager change revokes the former manager’s copied facts unless another grant independently authorizes them. Existing notebook copies must not survive merely because a new copy was added.
- Activation removes obsolete shared pages and their histories before serving the updated state. Test exact page lookup as well as search.
- Keep the PGLite server stopped during mutation. If a change fails partway, do not restart into a partially applied authorization state; finish or restore a known-safe state first.
- Revocation controls subsequent service responses. It cannot erase information a previously authorized reader already received.

## QM stretch boundary

Identity and room scope must come from authenticated QM execution context, not model-selected arguments. Missing, unmapped or inconsistent fields restrict retrieval to shared. Personal access requires verified principal identity and matching personal conversation scope. The broad QM credential may invoke only the narrow recall operation; direct member read operations must be refused. QM tests remain separate until the bridge is actually integrated.
