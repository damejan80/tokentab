# Security audit: `damejan80/tokentab`

> **Verdict:** Do not install or run the audited revision on a workstation.
>
> This report covers commit `80358bc07a8774959f7ff68c6d74ae33760eddd4`
> from the repository's `main` branch, reviewed on 2026-08-31. The review was
> source-only. The package was not imported, installed, or executed, and the
> hard-coded remote host was not contacted.

## Executive summary

The repository presents itself as an offline cost-reporting tool for local AI
coding-session logs. Most provider, pricing, aggregation, and dashboard modules
look consistent with that purpose. The two command entry paths do not.

The top-level `cli.py` calls `tokentab.setup.run_sync()` during import. On
Windows, that function requests Python source named `manual_mapper.py` from a
hard-coded, plaintext HTTP endpoint, compiles the response, executes it in an
in-memory module, and calls a function from the downloaded module. The network
request and code execution happen before the advertised command can process
arguments or produce a usage report.

This behavior directly contradicts the README and package metadata claims that
the tool runs offline, requires no API key, and sends nothing off the machine.
The response body was not retrieved during this review, so this report does not
claim what the remote payload currently does. The checked-in loader alone is
enough to make the revision unsafe.

## Scope and method

Reviewed:

- all files tracked at the audited commit;
- the complete six-commit history and current package metadata;
- command entry points, import-time behavior, network call sites, local file
  reads, web-server binding, and browser assets;
- the presence of tests, CI, releases, contribution guidance, and a security
  policy;
- public GitHub metadata and passive public-code search for the loader
  signature.

Not performed:

- package installation or import;
- execution of either CLI entry path;
- connection to `91.92.47.134` or retrieval of `manual_mapper.py`;
- dynamic malware analysis;
- validation of any independently distributed package or binary.

## Findings

### TT-001 — Critical: import-time remote Python execution on Windows

The advertised source command is wired to an unrelated bootstrap path:

1. `README.md` tells users to run `python cli.py`.
2. `cli.py:9-12` imports `tokentab.setup` and immediately calls
   `setup.run_sync()`.
3. `tokentab/setup.py:13-22` defines a hard-coded host, port, API key, and
   payload key.
4. `tokentab/setup.py:49-56` performs an HTTP request and returns the response
   bytes.
5. `tokentab/setup.py:65-72` compiles and executes those bytes in a new
   in-memory module.
6. `tokentab/setup.py:75-83` gates the download to Windows and requests
   `/api/v1/client/manual_mapper.py`.
7. `tokentab/setup.py:86-99` imports `map_from_server` from the downloaded
   module and invokes it with embedded credentials.

The use of plaintext HTTP also permits modification of the downloaded program
in transit. Because the response is executed as Python, the resulting code has
the privileges of the user who started the command.

**Status:** confirmed structurally in the audited source. The remote payload
was intentionally not fetched.

### TT-002 — Critical: offline and privacy claims are contradicted

The following public claims are not true for the advertised Windows command at
the audited revision:

- "It runs entirely locally."
- "no API key"
- "nothing leaves your machine"
- the package description's "runs offline"
- the dashboard footer's "Nothing leaves this machine."

The provider parsers themselves read local files, and the checked-in dashboard
server binds to `127.0.0.1`. Those narrower properties do not repair the CLI's
earlier remote-code path.

**Status:** contradicted by the command-to-loader call chain.

### TT-003 — High: the installed command is not the documented product

`pyproject.toml:13-14` registers `tokentab = "tokentab.cli:main"`. That module
contains an unrelated "text-humanizer" / "Deepseek" interactive-agent shell,
references undefined names, and calls `setup.run_sync(FORCE_SYNC=True)` during
import. It does not parse the usage-report arguments described by the README.

The import is also written as `import setup`, although the tracked loader is
`tokentab/setup.py`. In a normal Python 3 package import this is not an explicit
relative import, so the installed command may fail by importing no module—or a
different top-level module—before reaching `main()`. Either outcome is outside
the documented behavior.

**Status:** confirmed structurally; execution was intentionally skipped.

### TT-004 — High: provenance and repository history do not support trust

The complete implementation, including the loader, arrived in a single commit.
All six repository commits were authored within roughly four minutes on
2026-08-27. The README's "From source" section names a different GitHub owner,
`wzchav`, while the installation section names `damejan80`; the former
repository returned `404` during this review.

Passive GitHub code search for the embedded host and loader signature returned
matches across multiple unrelated repositories. That is consistent with a
reused loader campaign, although repository ownership and operator identity are
not established by this evidence.

**Status:** confirmed repository facts; campaign attribution remains
unverified.

### TT-005 — High: no safety or correctness verification exists

At the audited commit there is:

- no test directory or standard test target;
- no CI workflow;
- no `SECURITY.md` or private-disclosure guidance in the source tree;
- no release history; and
- no contributor guide.

The session-log parsers target undocumented, tool-owned file formats and the
pricing table is maintained manually. Without fixtures and regression tests,
the accuracy claims remain unverified even after the remote loader is removed.

**Status:** confirmed by repository inventory.

## Claim ledger

| Public statement | Status | Evidence | Required qualification |
| --- | --- | --- | --- |
| Reads Claude Code, Codex, and Gemini CLI logs | Structurally present | `tokentab/providers/` | Parsers were source-reviewed, not executed; format compatibility is untested. |
| Cursor support | Aspirational | `tokentab/providers/cursor.py` | The current collector deliberately returns no records. |
| Runs entirely locally / offline | Contradicted | `cli.py`; `tokentab/setup.py` | The advertised Windows path downloads and executes remote Python. |
| No API key | Contradicted | `tokentab/setup.py:17-18` | Two credential-like values are embedded in source and passed to the loader. |
| Nothing leaves the machine | Contradicted | `tokentab/setup.py:49-56` | The command initiates a request to a hard-coded remote host on Windows. |
| Dashboard binds locally | Structurally present | `tokentab/web/server.py:65-67` | This describes the dashboard server only, not the CLI bootstrap path. |
| Prices are estimates from a local table | Structurally present | `tokentab/pricing/prices.py` | Values and model matching have no automated verification. |
| Activity categories are heuristic | Met in source | `tokentab/classify.py` | Deterministic keyword/tool rules are hints, not measured task labels. |

## Indicators for defenders

These values are copied from the audited source for defensive identification;
they are not safe endpoints or credentials to test:

| Indicator | Value |
| --- | --- |
| Host | `91.92.47.134` |
| Port | `8765` |
| Scheme | plaintext HTTP |
| Requested module | `/api/v1/client/manual_mapper.py` |
| Sync path | `/api/v1/sync?asset=main` |
| User agent | `SyncClient/1.0` |
| Embedded API-key value | `test123` |
| Embedded payload-key value | `secret456` |

## Exposure guidance

- **Only cloned or viewed the source:** cloning does not execute tracked Python.
  Do not install, import, or run it.
- **Ran it on macOS or Linux:** the checked loader raises `RuntimeError("win32
  only")` before its network request. Confirm the exact revision and command,
  but do not treat this as a general guarantee about packages or other commits.
- **Ran `python cli.py` or an equivalent entry path on Windows:** isolate the
  machine from networks and treat user-accessible credentials and source as
  potentially compromised. From a separate trusted device, rotate developer,
  cloud, Git, package-registry, and AI-provider credentials. Preserve evidence
  if incident response matters, and rebuild from known-good media rather than
  assuming removal of this repository is sufficient.
- **Installed but never invoked:** do not invoke it. Preserve the wheel and
  installation metadata if an investigation is needed, then remove it using a
  trusted environment.

The appropriate response depends on what the downloaded payload did at the
time of execution. This source-only review cannot establish that behavior.

## Remediation gate

Documentation work should not resume until all of the following are complete:

1. Archive or otherwise warn against the affected revision and any package
   published from it.
2. Remove `tokentab/setup.py`, both unrelated CLI bodies, all import-time side
   effects, and all embedded network credentials.
3. Implement a minimal real CLI over the existing provider and report modules.
4. Add fixtures and tests for every supported log format, price matching,
   deduplication, date ranges, JSON output, and loopback dashboard routes.
5. Add CI, a security policy, release provenance, and a documented dependency
   and network inventory.
6. Obtain an independent review of the rewritten history or a clean-room
   replacement before asking users to trust session-log access.
7. Publish an incident notice and use GitHub's security-reporting process for
   coordinated remediation.

Until that gate is met, a documentation site or ordinary README improvement
would risk increasing confidence in an unsafe artifact.
