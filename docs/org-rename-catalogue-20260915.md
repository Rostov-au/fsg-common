# `Rostov-au/` occurrence catalogue -- 15 Sep 2026

tr#669 / crm#655 gate line 7 prep. **A snapshot, not a live report** -- it
reflects each of the five repos' `origin/main` at the commit named below, via
`git grep -n "Rostov-au/" <ref>` (tracked files only, never a filesystem
walk). The commands here regenerate it; nothing here was hand-typed.

The actual rename is `scripts/rename_github_org.py` (this repo) -- see
`docs/README.md`'s "Where things live" / `scripts/commands_index.json`'s
`org-rename-prep` group. **This is prep only.** The org does not exist yet
(crm#655's own transfer checklist still has "create the company git and n8n
accounts" ahead of it), so nothing here has been run with `--apply` against
any of the five real checkouts -- only against a throwaway clone, discarded
after.

## Totals

| Repo | Commit (`origin/main`) | Occurrences |
| --- | --- | --- |
| fsg-common | `278ca4b106b9bc7f113ec11dc98373b3a17ec56a` | 6 |
| fsg-estimating-crm | `a6da39a4adc247547fa9f9217ab37e49e0b47670` | 56 |
| fsg-tender-review | `2e482afabc708670db3cbe606582ab26eeb87b18` | 40 |
| fsg-estimating-tools | `7ad12f73b5fd3eca588c10973828fe6d08fafc3c` | 15 |
| fsg-bluebeam-steel-standards | `83f4520f75e1a9ef70de80184e23138d77489869` | 15 |
| **Total** | | **132** |

## Regenerate

Run from a checkout of each repo (or against `origin/main` directly, as
here, to avoid depending on which branch happens to be checked out):

```
git -C <repo> grep -n "Rostov-au/" origin/main
```

## fsg-common (6)

```
README.md:62:Rostov-au/fsg-tender-review#184, and the standing instruction on #180 is that
docs/consumers.md:16:fsg-common @ git+https://github.com/Rostov-au/fsg-common@v0.1.0
docs/consumers.md:32:answer Rostov-au/fsg-tender-review#184 item 1 -- see fsg_common's
src/fsg_common/sections/_resolver.py:32:(Rostov-au/fsg-tender-review#184 item 1, "questions-for-estimators.md" Q25),
src/fsg_common/sections/_resolver.py:738:# (Rostov-au/fsg-tender-review#184 Q25): both resolvers converge on this
tools/known_issues.py:44:    disagreed about -- item 1 of Rostov-au/fsg-tender-review#184, "Questions
```

## fsg-estimating-crm (56)

```
.claude/skills/session-start/SKILL.md:200:  gh issue list -R "Rostov-au/$repo" --state open --label now,sprint-1
.claude/skills/synthetic-run/SKILL.md:357:GitHub issue** -- one `gh issue create -R Rostov-au/fsg-estimating-crm` per
.gitattributes:14:# scripts/fsg_common/ is a byte-for-byte copy of Rostov-au/fsg-common at the
.github/ISSUE_TEMPLATE/finding.md:38:(`Rostov-au/repo#123`). If nothing blocks or is blocked, say so rather
.github/pull_request_template.md:16:  Closes Rostov-au/fsg-tender-review#45        another repo, LINKS ONLY --
.github/workflows/validate.yml:314:          pip install --force-reinstall --no-cache-dir "git+https://github.com/Rostov-au/fsg-common.git@${PIN}"
CLAUDE.md:115:Rostov-au/<repo>`.
docs/COMMANDS.md:55:| is the scheduled check-in routine actually running | `python scripts/check_routine_heartbeat.py -R Rostov-au/fsg-estimating-crm` |
docs/GIT_WORKFLOW.md:10:- **`fsg-estimating-tools` (a separate git repo, `Rostov-au/fsg-estimating-tools` on GitHub):** the workbook side's own plain-text extraction -- VBA source (`src/vba/`, mechanically extracted from the live `.xlam` via `scripts/extract_vba.py`), ribbon Custom UI XML (`src/customUI/`), docs, and reference/template files. This isn't just documentation *about* the workbook the way this repo's blueprint is -- it's real tracked source pulled directly from the live add-in.
docs/GIT_WORKFLOW.md:134:This repo is already on GitHub (`Rostov-au/fsg-estimating-crm`, private) and has been cloned onto more than one machine -- the one-time remote setup below is just for reference, or for cloning onto a *new* machine, not something still pending. `git push` (already part of the daily loop above) is what keeps the backup current -- a commit alone only saves the checkpoint locally.
docs/GIT_WORKFLOW.md:136:**`fsg-estimating-tools` has its own separate GitHub remote** (`Rostov-au/fsg-estimating-tools`, private) -- the same daily loop and backing-up discipline applies there independently. Pushing one repo does not push the other; check `git status`/`git push` in whichever repo you're actually working in.
docs/GIT_WORKFLOW.md:140:git clone https://github.com/Rostov-au/fsg-estimating-crm.git
docs/GIT_WORKFLOW.md:143:git remote add origin https://github.com/Rostov-au/fsg-estimating-crm.git
docs/SERVER_MIGRATION.md:41:git clone https://github.com/Rostov-au/fsg-estimating-crm.git
docs/SERVER_MIGRATION.md:184:git clone https://github.com/Rostov-au/fsg-estimating-crm.git
docs/archive-tools-repo-planning.md:406:GitHub natively resolves `Rostov-au/other-repo#123` references across repos in the same org -- no monorepo, no submodule, no third repo needed. Two cheap additions make this actually useful instead of theoretical:
docs/archive/estimating-and-crm-board.md:2444:        gh -R Rostov-au/<repo> pr view <n> --json state,mergedAt
docs/archive/estimating-and-crm-board.md:2445:        gh api repos/Rostov-au/<repo>/actions/runners
docs/archive/estimating-and-crm-board.md:2487:              REPO_URL: https://github.com/Rostov-au/fsg-tender-review
docs/archive/estimating-and-crm-board.md:2763:    **CURRENT STATE, measured:** `gh api repos/Rostov-au/<repo>/actions/runners` returns
docs/check-in-routine.md:28:Pass `-R Rostov-au/<repo>` on every `gh` command. PR numbers collide across the
docs/check-in-routine.md:42:   Rostov-au/fsg-estimating-crm` reads this record and reports RUNNING,
docs/david-runbook-20260915.md:194:each repo carries have to be checked after every transfer, and every `Rostov-au/` reference in
docs/issue-tracking-replaces-kanban.md:42:`https://github.com/orgs/Rostov-au/projects` and each repo's own Projects
docs/issue-tracking-replaces-kanban.md:97:  gh issue list -R "Rostov-au/$repo" --state open --json number,title,labels
docs/issue-tracking-replaces-kanban.md:266:`gh issue list -R Rostov-au/<repo> --state all --limit 1000 --json createdAt,closedAt,labels,state`.
docs/issue-tracking-replaces-kanban.md:341:  gh issue list -R "Rostov-au/$repo" --state open --milestone "Work server" --json number,title,labels
docs/morning-actions-20260906.md:3:> **Superseded 7 Sep 2026.** Every open action and question here was carried onto the pinned David lists, one per repo: [#398](https://github.com/Rostov-au/fsg-estimating-crm/issues/398) for this repo, fsg-estimating-tools#245, fsg-bluebeam-steel-standards#51 and fsg-tender-review#389 (audit 6 Sep 2026, Part 4, sessions item 5). Read those, not this; a line ticked there is done, a line here says nothing about today.
pyproject.toml:14:# scripts/fsg_common/ is a vendored, byte-for-byte copy of Rostov-au/
scripts/apply_cnda_instrument_scope_20260909.py:4:David's decision, 9 Sep 2026, Rostov-au/fsg-tender-review#284 (and crm#516):
scripts/check_routine_heartbeat.py:18:    python scripts/check_routine_heartbeat.py -R Rostov-au/fsg-estimating-crm
scripts/check_routine_heartbeat.py:146:        "-R", "--repo", required=True, help="owner/repo, e.g. Rostov-au/fsg-estimating-crm"
scripts/commands_index.json:207:    "is the scheduled check-in routine actually running": "python scripts/check_routine_heartbeat.py -R Rostov-au/fsg-estimating-crm",
scripts/fsg_common/sections/_resolver.py:32:(Rostov-au/fsg-tender-review#184 item 1, "questions-for-estimators.md" Q25),
scripts/fsg_common/sections/_resolver.py:738:# (Rostov-au/fsg-tender-review#184 Q25): both resolvers converge on this
scripts/waiting_on_david.py:93:    "Rostov-au/fsg-tender-review",
scripts/waiting_on_david.py:94:    "Rostov-au/fsg-estimating-crm",
scripts/waiting_on_david.py:95:    "Rostov-au/fsg-estimating-tools",
scripts/waiting_on_david.py:96:    "Rostov-au/fsg-bluebeam-steel-standards",
scripts/waiting_on_david.py:97:    "Rostov-au/fsg-common",
scripts/waiting_on_david.py:336:         "-R", "Rostov-au/fsg-estimating-crm"],
tests/test_check_pr_body.py:25:                     "Fixed: #6", "fix #7", "Resolves Rostov-au/fsg-estimating-crm#12",
tests/test_check_pr_body.py:26:                     "Closes https://github.com/Rostov-au/fsg-estimating-crm/issues/12"):
tests/test_check_routine_heartbeat.py:10:(`gh issue view 415 -R Rostov-au/fsg-estimating-crm --json comments`): 10
tests/test_pull_request_template.py:43:        """`Closes #45` and `Closes Rostov-au/repo#45` behave differently and
tests/test_pull_request_template.py:45:        self.assertRegex(self.text, r"Closes\s+Rostov-au/[\w.-]+#")
tests/test_sync_bugs_to_issues.py:72:        return {"html_url": f"https://github.com/Rostov-au/{repo}/issues/{n}",
tests/test_sync_bugs_to_issues.py:245:            "https://github.com/Rostov-au/fsg-estimating-crm/issues/"))
tests/test_sync_bugs_to_issues.py:279:        url = "https://github.com/Rostov-au/fsg-estimating-crm/issues/7"
tests/test_sync_bugs_to_issues.py:305:        url = "https://github.com/Rostov-au/fsg-estimating-crm/issues/7"
tests/test_sync_bugs_to_issues.py:311:            pr_url="https://github.com/Rostov-au/fsg-estimating-crm/pull/8")
tests/test_sync_bugs_to_issues.py:325:        url = "https://github.com/Rostov-au/fsg-estimating-crm/issues/7"
tests/test_sync_bugs_to_issues.py:340:        url = "https://github.com/Rostov-au/fsg-estimating-crm/issues/7"
tests/test_waiting_on_david.py:43:        url=f"https://github.com/Rostov-au/fsg-estimating-tools/issues/{number}",
tests/test_waiting_on_david.py:224:            unreadable=[("Rostov-au/fsg-estimating-tools", "HTTP 401")],
tests/test_waiting_on_david.py:295:                code = wod.main(["--repo", "Rostov-au/fsg-estimating-tools",
```

Note: `docs/david-runbook-20260915.md:194` already names this exact mechanical
step by hand -- this catalogue and `rename_github_org.py` are what make that
line runnable rather than a description.

## fsg-tender-review (40)

```
.claude/skills/session-start/SKILL.md:322:gh run view "$RUN" -R Rostov-au/fsg-tender-review   # then open the run summary for the Advisory verdict table
.claude/skills/session-start/SKILL.md:369:  gh issue list -R "Rostov-au/$repo" --state open --label now,sprint-1
.claude/skills/session-start/SKILL.md:383:Rostov-au/fsg-tender-review`. Useful labels: `tender-review`, `needs-david`,
.claude/skills/tier-a-replay/SKILL.md:144:  (`gh issue create -R Rostov-au/fsg-tender-review`, label `tender-review`; add
.github/ISSUE_TEMPLATE/finding.md:38:(`Rostov-au/repo#123`). If nothing blocks or is blocked, say so rather
.github/workflows/ci.yml:385:          pip install --force-reinstall --no-cache-dir "git+https://github.com/Rostov-au/fsg-common.git@${PIN}"
.github/workflows/health.yml:203:          pip install --force-reinstall --no-cache-dir "git+https://github.com/Rostov-au/fsg-common.git@${PIN}"
CLAUDE.md:765:moved to `Rostov-au/fsg-common` (`fsg_common.sections`), a shared package both repos import
CLAUDE.md:817:Rostov-au/fsg-tender-review`. Useful labels: `tender-review`, `needs-david`,
README.md:43:| know what's built vs. planned | `gh issue list -R Rostov-au/fsg-tender-review` (the kanban board that used to answer this was retired 4 Sep 2026, all cards migrated to issues). Decisions are in [docs/adr-log.md](docs/adr-log.md); `next-steps.md` was archived on 3 Sep 2026 because a second planner that can disagree with the board is what made it contradict itself |
README.md:197:via n8n. See `gh issue list -R Rostov-au/fsg-tender-review` for what's built vs. planned in
docs/README.md:239:  issues (`gh issue list -R Rostov-au/fsg-tender-review`), not the kanban board this line used
docs/README.md:272:(`gh issue list -R Rostov-au/fsg-tender-review`); the kanban board this line used to name was
docs/adr-log.md:2101:<https://github.com/Rostov-au/fsg-tender-review/issues/284#issuecomment-5582279668>
docs/adr-log.md:2176:<https://github.com/Rostov-au/fsg-tender-review/issues/480#issuecomment-recorded-2026-09-09>
docs/adr-log.md:2286:<https://github.com/Rostov-au/fsg-estimating-crm/issues/211#issuecomment-5628209861>
docs/archive/DECISIONS-NEEDED.md:3:> **Archived 3 Sep 2026, bannered 7 Sep 2026.** A record of one session or week, not current status; do not reason from it. Work is tracked in GitHub issues (`gh issue list -R Rostov-au/fsg-tender-review`, process in `fsg-estimating-crm/docs/issue-tracking-replaces-kanban.md`) and decisions in `docs/adr-log.md`. The kanban board this file names was retired 4 Sep 2026.
docs/archive/HANDOFF-2026-08-22.md:3: (same banner)
docs/archive/HANDOFF-2026-08-23-unattended-run.md:3: (same banner)
docs/archive/HANDOFF-2026-08-23.md:3: (same banner)
docs/archive/HANDOFF-2026-09-02-gates-and-tier-c.md:3: (same banner)
docs/archive/HANDOFF-lane-r-20260902.md:3: (same banner)
docs/archive/HANDOFF-wt-parallel-20260901.md:3: (same banner)
docs/archive/HANDOFF-wt-parallel-ab-20260902.md:3: (same banner)
docs/archive/MONDAY-2026-08-24-s-drive-plan.md:3: (same banner)
docs/archive/MONDAY-2026-08-31-tier-abc-synthetic-kanban-handover.md:3: (same banner)
docs/archive/UNATTENDED-QUEUE.md:3: (same banner)
docs/archive/next-steps.md:5:> now GitHub issues (`gh issue list -R Rostov-au/fsg-tender-review`, process in
docs/calibration-runbook.md:5:`gh issue list -R Rostov-au/fsg-tender-review` is the status -- the kanban board
docs/handover-20260912-tuesday-sprint.md:340:**3. CRM data-lifecycle survey** (if not landed): "Search `Rostov-au/fsg-estimating-crm` GitHub
docs/review-20260906-reports/process.md:20,70,94,116,126: five `GET /repos/Rostov-au/...` regenerate-commands
requirements.txt:31:# private repo (Rostov-au/fsg-common), so a bare `pip install fsg-common`
scripts/setup_worktree.py:9:(`Rostov-au/fsg-common`), so a bare `pip install fsg-common` would hit PyPI
src/fsg_tender_review/resolve.py:155:        "private sibling repo (Rostov-au/fsg-common), typically checked out "
tests/test_check_pr_body.py:25:                     "Fixed: #6", "fix #7", "Resolves Rostov-au/fsg-estimating-crm#12",
tests/test_check_pr_body.py:26:                     "Closes https://github.com/Rostov-au/fsg-estimating-crm/issues/12"):
```

(the nine identical `docs/archive/*` banners and the five identical
`docs/review-20260906-reports/process.md` `GET /repos/Rostov-au/...` lines
are collapsed above for readability -- the full uncollapsed 40-line output is
reproducible verbatim with the command under "Regenerate".)

## fsg-estimating-tools (15)

```
.gitattributes:34:# scripts/fsg_common/ is a byte-for-byte copy of Rostov-au/fsg-common at the
.github/ISSUE_TEMPLATE/finding.md:38:(`Rostov-au/repo#123`). If nothing blocks or is blocked, say so rather
.github/workflows/validate.yml:311:          pip install --force-reinstall --no-cache-dir "git+https://github.com/Rostov-au/fsg-common.git@${PIN}"
CLAUDE.md:101:  Rostov-au/fsg-estimating-tools`. Useful labels: `tools`, `needs-david`,
docs/backlog.md:14:> is picked up from `gh issue list -R Rostov-au/fsg-estimating-tools`, never from this
docs/bluebeam-import-interface-spec.md:7:[`fsg-bluebeam-steel-standards`](https://github.com/Rostov-au/fsg-bluebeam-steel-standards)
docs/bluebeam-import-interface-spec.md:8:-- its [`docs/mto-takeoff-toolset.md`](https://github.com/Rostov-au/fsg-bluebeam-steel-standards/blob/main/docs/mto-takeoff-toolset.md)
docs/route-a-population-measurement-20260905.md:7:([interim](https://github.com/Rostov-au/fsg-estimating-tools/issues/101#issuecomment-5544866118),
docs/route-a-population-measurement-20260905.md:8:[correction](https://github.com/Rostov-au/fsg-estimating-tools/issues/101#issuecomment-5544886692));
ruff.toml:8:# scripts/fsg_common/ is a vendored, byte-for-byte copy of Rostov-au/
scripts/fsg_common/sections/_resolver.py:32:(Rostov-au/fsg-tender-review#184 item 1, "questions-for-estimators.md" Q25),
scripts/fsg_common/sections/_resolver.py:738:# (Rostov-au/fsg-tender-review#184 Q25): both resolvers converge on this
scripts/vendor_fsg_common.py:20:is a byte-for-byte copy of `src/fsg_common` from `Rostov-au/fsg-common`
tests/test_check_pr_body.py:27:                     "Fixed: #6", "fix #7", "Resolves Rostov-au/fsg-estimating-crm#12",
tests/test_check_pr_body.py:28:                     "Closes https://github.com/Rostov-au/fsg-estimating-crm/issues/12"):
```

## fsg-bluebeam-steel-standards (15)

```
.gitattributes:10:# tools/fsg_common/ is a byte-for-byte copy of Rostov-au/fsg-common at the
.github/workflows/validate.yml:99:          pip install --force-reinstall --no-cache-dir "git+https://github.com/Rostov-au/fsg-common.git@${PIN}"
CLAUDE.md:62:  (`Rostov-au/fsg-common`), **public since 12 Sep 2026** (`crm#552`, David's decision -- it was
CLAUDE.md:67:  `src/fsg_common/` from `Rostov-au/fsg-common` at the commit in `fsg-common.pin`;
README.md:14:   [`fsg-estimating-tools`'s interface spec](https://github.com/Rostov-au/fsg-estimating-tools/blob/main/docs/bluebeam-import-interface-spec.md)
README.md:122:([#69](https://github.com/Rostov-au/fsg-bluebeam-steel-standards/issues/69)).
docs/mto-takeoff-toolset.md:26:[`fsg-estimating-tools`'s `docs/bluebeam-import-interface-spec.md`](https://github.com/Rostov-au/fsg-estimating-tools/blob/main/docs/bluebeam-import-interface-spec.md)
docs/plan.md:68:[#69](https://github.com/Rostov-au/fsg-bluebeam-steel-standards/issues/69) so
docs/plan.md:183:spec](https://github.com/Rostov-au/fsg-estimating-tools/blob/main/docs/bluebeam-import-interface-spec.md)
ruff.toml:9:# Vendored, byte-for-byte, from Rostov-au/fsg-common at fsg-common.pin
scripts/vendor_fsg_common.py:19:`src/fsg_common/` from `Rostov-au/fsg-common` at the commit in
tools/fsg_common/sections/_resolver.py:32:(Rostov-au/fsg-tender-review#184 item 1, "questions-for-estimators.md" Q25),
tools/fsg_common/sections/_resolver.py:738:# (Rostov-au/fsg-tender-review#184 Q25): both resolvers converge on this
tools/fsg_mto/btx.py:819:# https://github.com/Rostov-au/fsg-bluebeam-steel-standards/issues/69, opened
tools/fsg_mto/sections.py:182:        "Rostov-au/fsg-common would also work, but then the resolver is not "
```

**Verified against a throwaway clone, 15 Sep 2026:** `fsg-bluebeam-steel-standards`
was cloned to a scratch directory, `rename_github_org.py FSG-Steel --apply`
(a placeholder org name) run against that clone only, and the result checked
three ways: `git grep -n "Rostov-au"` on the clone returned nothing; `git
diff --stat` showed exactly 11 files / 15 insertions / 15 deletions, matching
the 15-occurrence count above one-for-one; and a byte-level diff of a CRLF
file in the set confirmed only the `Rostov-au/` substring changed, line
endings and non-ASCII bytes (em-dashes) untouched. The clone was then
deleted. The real checkout was never touched.
