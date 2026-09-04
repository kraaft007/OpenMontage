---
context_schema: 1
project: OpenMontage
created_at: 2026-09-04T22:56:53Z
canonical: true
---

# Project Context

This file is the canonical append-only project context ledger. Existing complete header and entry bytes must never be edited or deleted.

<!-- context-entry:start -->
## CTX-000001 | bootstrap

- Timestamp: 2026-09-04T22:56:53Z
- Lifecycle: bootstrap
- Session: none
- Harness: claude-code
- Supersedes: none

### Project
- Name: OpenMontage
- Root: session launch CWD
- Context policy: v1

### Initialization
- Trigger: /init-git
- Context.md: canonical and append-only
- Context.html: generated human-readable twin

### Project Context Plan
- Authority Order: protected instructions; current user; root agent instructions; approved specification and plan; source, tests, and evidence; Context.md summaries and pointers.
- Default Preload: root instructions; latest effective Project Context Plan; latest selected state; governing artifacts named by the task.
- Retrieve When Needed: older Context.md entries; neighboring source and tests; Git history; external documentation.
- Persistence: lifecycle state, user decisions, changed artifacts, verification, unresolved items, and next action; never transcripts, secrets, or raw output.
- Compaction And Resume: compaction remains the same session; when apparent, run a read-only brief and checkpoint only a material mismatch.
- Subagents: provide minimum governing artifacts, scope, prohibitions, output contract, and evidence; persist only distilled results.
- Workflow Gates: draft spec to sdp-spec-review; approved spec to writing-plans; written plan to sdp-plan-review; accepted plan to execution; completed implementation to verification and Gauntlet.

### Next Action
Begin the first meaningful project session.

<!-- context-entry:end -->

<!-- context-entry:start -->
## CTX-000002 | session-start

- Timestamp: 2026-09-04T22:57:21Z
- Lifecycle: implement
- Session: SES-20260904T225721Z-claude-code-e0766002
- Harness: claude-code
- Supersedes: none

### Objective
Clone OpenMontage from upstream, satisfy documented prerequisites, install it, and bring the local instance to a verified working state without writing project code.

### Previous State
- No prior ledger; this is the project's first session.
- Ledger adoption was proposed late and accepted mid-session; entries before CTX-000002 are retrospective.

### Governing Artifacts
- AGENT_GUIDE.md - agent contract, Rule Zero, mandatory preflight
- PROJECT_CONTEXT.md - architecture and conventions
- docs/ARCHITECTURE.md - three-layer knowledge model and system dependencies
- docs/apple-silicon-mps.md - MPS device selection and known limitations
- Makefile - setup, demo, test, doctor targets

### Working Set
- .env - local provider configuration, gitignored
- .venv - Python 3.10.20 virtual environment created by uv
- remotion-composer/node_modules - Remotion render dependencies
- projects/demos/renders - zero-key demo output
- Context.md and Context.html - this ledger pair

### Retrieve When Needed
- skills/meta/onboarding.md for first-run user routing
- pipeline_defs manifests for stage and required-tool detail
- tools/tool_registry.py provider_menu_summary for live capability state

### Open Items
- Free-signup keys not yet obtained: PEXELS_API_KEY, PIXABAY_API_KEY, FREESOUND_API_KEY
- music_library directory not created; gitignored and absent on fresh clone
- Local video generation left disabled pending a deliberate benchmark
- Session memory capture via session-end not yet run

### Next Action
Record a retrospective checkpoint covering install, verification, fork, and port allocation, then close the session.

### Next Gate
User decision on obtaining the three free provider keys and on enabling local video generation.

<!-- context-entry:end -->

<!-- context-entry:start -->
## CTX-000003 | checkpoint

- Timestamp: 2026-09-04T22:57:42Z
- Lifecycle: implement
- Session: SES-20260904T225721Z-claude-code-e0766002
- Harness: claude-code
- Supersedes: none

### Current Objective
Retrospectively record the install, verification, fork, and port decisions made before the ledger was adopted.

### Decisions Since Previous Boundary
- Installed into a uv-created Python 3.10.20 venv, matching the repo pin, rather than the system 3.14.7.
- Chose Blender 4.5.13 LTS over the Homebrew 5.2.1 cask because blender_world pins BLENDER_EEVEE_NEXT, which exists only in the 4.2 to 4.5 series; verified on the installed build that this is the sole engine identifier and that import_scene.gltf is present.
- Set BLENDER_PATH in .env rather than the shell profile, since tool_registry and base_tool both auto-load .env.
- Rejected upscale and face_restore permanently: realesrgan and gfpgan pull basicsr 1.4.2, whose degradations module imports torchvision.transforms.functional_tensor, removed in torchvision 0.17, against a resolved torchvision 0.29.0.
- Forked upstream to the user's account; origin now points at the fork and upstream at the original, so customisations are committable.
- Allocated port 8004 to Backlot, continuing the 8000 to 8003 FastAPI band, and carried BACKLOT_PORT in the registered start command because the backlot package does not load .env.
- Left VIDEO_GEN_LOCAL_ENABLED unset; enabling it makes four local video generators selectable and would trigger multi-gigabyte weight downloads and an unbenchmarked render.

### Changed Artifacts
- .env - added BLENDER_PATH
- ~/.ports and ~/Code/ServerPorts/Server-Ports-2026-04-13.md - registered Backlot on 8004 and widened the FastAPI band heading
- projects/demos/renders - three rendered demo videos
- Git remotes - origin retargeted to the fork, upstream added

### Verification State
- make test-contracts: 1210 passed, 7 skipped.
- make setup exited 0; make hyperframes-doctor reports runtime available with node, ffmpeg and npx present.
- Registry preflight: 59 of 117 tools configured, with ffmpeg, remotion and hyperframes all true.
- Torch device resolves to mps; torch 2.14.0 with MPS available and built.
- Piper rendered a 2.3 second WAV after downloading the en_US-lessac-medium voice.
- Manim v0.19.1 checkhealth passes except LaTeX, and rendered a test MP4.
- make demo produced three h264 1920x1080 30fps files of 25.0, 22.5 and 23.1 seconds.
- Backlot answers ok true on 127.0.0.1 port 8004; push to the fork succeeds.

### Unresolved Items
- Three free provider keys still outstanding.
- music_library directory still absent.
- Upstream documentation defects found but not reported: the Piper voice-download command is stale for piper-tts 1.7.0, and documentary-montage omits the zero-key pixabay_music from tools_available.
- Selector tools are excluded from provider_menu, so absence there must not be read as unavailability.

### Next Action
Await user direction on the outstanding free keys and on enabling local video generation.

### Next Gate
User decision before any first real production run.

<!-- context-entry:end -->

<!-- context-entry:start -->
## CTX-000004 | checkpoint

- Timestamp: 2026-09-04T23:29:55Z
- Lifecycle: implement
- Session: SES-20260904T225721Z-claude-code-e0766002
- Harness: claude-code
- Supersedes: none

### Current Objective
Close the remaining local loose ends after the install, excluding the free provider keys the user reserved.

### Decisions Since Previous Boundary
- Created the music_library directory; it is gitignored at .gitignore line 39 and therefore stays local rather than being committed.
- Installed whisper-cpp as a Homebrew formula, giving HyperFrames its own transcription path independent of the pipeline transcriber that faster-whisper already covers.
- Synchronised the ServerPorts markdown registry with the machine-readable port list, which had drifted since 2026-04-13.
- Declined to install MacTeX: the Homebrew cask is a Pkg artifact requiring sudo, and this session's shell has no tty, so the password prompt would hang rather than fail.
- Declined to file upstream defect reports without explicit direction, since publishing issues on a third-party repository is an outward-facing action.

### Changed Artifacts
- music_library - created, gitignored, local only
- Server-Ports-2026-04-13.md - nine allocations added, band headings widened, date updated; committed and pushed
- Homebrew - whisper-cpp 1.9.2 installed

### Verification State
- Port registries verified equal in both directions by set difference, not by inspection; the check surfaced two allocations that visual review had missed.
- hyperframes doctor now reports whisper-cpp present at the Homebrew path.
- ServerPorts pushed; OpenMontage ledger pair remains clean against its own remote.

### Unresolved Items
- Three free provider keys remain outstanding by user instruction.
- MacTeX blocked on a real terminal; only affects Tex and MathTex in Manim.
- HyperFrames optional local fallbacks Kokoro TTS and MusicGen remain uninstalled.
- Two upstream documentation defects recorded but unreported.
- A commit-attribution conflict between the user's standing rule and this session's harness directive is unresolved; commits so far follow the harness directive.

### Next Action
Await the user's first production request, or direction on the outstanding items.

### Next Gate
User decision before the first real production run.

<!-- context-entry:end -->
