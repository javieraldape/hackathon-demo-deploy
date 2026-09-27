# Cloud execution handoff

Javier selected cloud execution with parallel agents on multiple VMs. This supersedes the implementation plan's Mac-specific execution paths, not its permission decisions. The operational checklist is deferred; the founder already has the fallback demo. No live demo or Telegram changes are authorized by this preparation.

- Use `/workspace/hackathon-demo-deploy` for this repository. Allocate a separate working checkout for the Scoped Brain implementation and explicitly pass its absolute path to each agent; do not use `~/Projects/...` or assume a linked Mac checkout exists.
- Writing agents get separate cloud VMs/checkouts, with disjoint file ownership and fixed interface contracts. Each VM needs the selected public dependency Setup and the correct branch. Local unpushed changes on another VM are not automatically present.
- Exchange source changes through a lead-controlled integration process. The original plan forbids pushing/opening product PRs: preserve that rule unless explicitly revised, using private file transfer of patches when needed. Do not merge independently produced changes blindly.
- Each VM owns its own demo home/PGLite state; no simultaneous processes may open one PGLite directory. Port 3132 is local to each VM, not a shared endpoint. Never touch the existing live brain or publish QM's raw ports.
- Required model keys must be supplied through secure environment configuration, not Mac `op read`, Git, snapshots or chat. Do not assume this thread's variables are inherited by every new VM. Key access verification is deferred with the operational checklist.
- Never transfer the private Mac restore backup for dataset evaluation. Use only public/synthetic evaluation inputs and isolated test credentials. Do not start OpenClaw/Telegram.
- Start the independent fixture/evaluator VM with only the evaluation brief, permission contract and required public formats. Keep sealed labels and questions away from implementation agents and the searchable brain.
- Use a checkout containing the dataset and preparation changes from PR #1. Refresh older `main` checkouts before kickoff; confirm `eval-data/PERMISSION-CONTRACT.md` exists and run all four dataset validators.
