# Inspectable Subagent Transcript Harness

This document defines the development-validation harness for child transcript
body audit when `multi_agent_v1` child ids are not readable after completion.

Use this harness for validation runs where the verdict depends on full
child-trajectory evidence, such as Task 10 true nested isolation checks.

## Problem

`multi_agent_v1.spawn_agent` returns stable agent ids that are good for
dispatch-ledger identity, but current local probes show those ids are not
accepted by `codex_app.read_thread` and are not discoverable with
`codex_app.list_threads`. A parent `multi_agent_v1` subagent also does not have
a read/export transcript tool. Therefore, receipt-level audit is possible, but
post-run transcript-body audit is not.

Local probe evidence:

- `docs/verification/2026-06-06/transcript-toolchain-probe/parent_probe_result.json`
- `docs/verification/2026-06-06/transcript-toolchain-probe/main_thread_probe_result.json`
- `docs/verification/2026-06-06/transcript-toolchain-probe/codex_thread_readability_probe_result.json`

The same probes show a viable path: `codex_app.create_thread` threads can be
read with `codex_app.read_thread` while they are still active. They are not
reliably readable after they finalize, so export must happen before final
handoff.

## Harness Contract

For transcript-audited development validation, dispatch each child executor or
reviewer as an inspectable Codex thread instead of an ordinary `multi_agent_v1`
child.

The parent coordinator records:

```json
{
  "dispatch_mode": "codex_thread_inspectable",
  "thread_id": "<codex_app_thread_id>",
  "stage": "<stage_id>",
  "role": "<executor | spec_compliance_reviewer | quality_reviewer>",
  "brief_path": "stage_briefs/<stage>_<role>.md",
  "receipt_path": "stage_results/<stage>_result.json",
  "trace_bundle_path": "transcripts/<stage>_<role>_<thread_id>_trace_bundle.json",
  "transcript_export_path": "transcripts/<stage>_<role>_<thread_id>_read_thread.json",
  "final_status": "READY_FOR_TRANSCRIPT_EXPORT"
}
```

## Child Prompt Requirements

Every inspectable child prompt must include these requirements:

1. Read only the assigned brief and allowed files.
2. Write the normal stage result or review receipt.
3. Write a trace bundle under `transcripts/` containing:
   - `stage`, `role`, `thread_id_if_known`, and `brief_path`;
   - every file read and why;
   - every file written;
   - every command/tool run with command text, exit code, and important output
     summary;
   - issue classification and final verdict/status;
   - a `forbidden_context_read` boolean and evidence.
4. Do not send a final completion answer yet. Instead, stop with a short
   progress message containing:

```text
READY_FOR_TRANSCRIPT_EXPORT
```

The thread must remain active so the parent can call `codex_app.read_thread`.

## Export Procedure

1. Parent dispatches the child with `codex_app.create_thread`.
2. Parent waits until the receipt and trace bundle exist, or until
   `read_thread` shows the child has reached `READY_FOR_TRANSCRIPT_EXPORT`.
3. Parent calls `codex_app.read_thread(threadId=<thread_id>, includeOutputs=true)`.
4. Parent writes the returned JSON to:

```text
transcripts/<stage>_<role>_<thread_id>_read_thread.json
```

5. Parent verifies the exported transcript includes the assignment marker,
   brief path, receipt path, and `READY_FOR_TRANSCRIPT_EXPORT`.
6. Parent sends a finalize message to the child thread:

```text
Transcript export has been saved. Finalize now without further file changes.
```

7. Parent updates the dispatch ledger with `transcript_export_path` and
   `trace_bundle_path`.

Do not rely on `read_thread` after finalization. Local probes show completed
probe threads may become unreadable or undiscoverable.

## Audit Semantics

The transcript-body auditor receives:

- the exported `read_thread` JSON;
- the child trace bundle;
- the original brief;
- the child receipt;
- the coordinator ledger row.

The auditor verifies:

- the child stayed within the brief;
- the receipt is supported by the actual conversation and trace bundle;
- no archived/prior-run context was read unless explicitly allowed;
- no inline fallback or role mixing occurred;
- tool failures and repair decisions are represented in the receipt.

If either `read_thread` export or the trace bundle is missing, the child is not
eligible for a clean transcript-body PASS.

## Limitations

This is a development-validation harness, not the normal AutoStudy runtime
surface. A real user-facing runtime can still use ordinary subagents and
receipt-level review, but Task 10-style clean PASS requires inspectable threads
until the platform exposes a stable transcript export API for `multi_agent_v1`.
