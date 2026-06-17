# 🌿 Git Workflow

> The rules for how code moves from idea → production.

---

## Branch Structure

```
main          ← production-ready code only. Always deployable.
dev           ← integration branch. All features merge here first.
feature/*     ← individual features or refactors
fix/*         ← bug fixes
chore/*       ← non-code changes (docs, config, CI)
```

---

## Branch Naming

| Type      | Pattern                          | Example                          |
|-----------|----------------------------------|----------------------------------|
| Feature   | `feature/<short-description>`    | `feature/scraper-modularization` |
| Bug Fix   | `fix/<short-description>`        | `fix/playwright-timeout`         |
| Refactor  | `feature/refactor-<description>` | `feature/refactor-test-scripts`  |
| Chore     | `chore/<short-description>`      | `chore/update-readme`            |

**Rules:**
- Lowercase, hyphens only, no spaces.
- Keep it under 40 characters.
- Always branch off `dev`, never off `main`.

---

## Workflow — Step by Step

```bash
# 1. Start from dev, always
git checkout dev
git pull origin dev

# 2. Create your branch
git checkout -b feature/scraper-modularization

# 3. Make small, focused commits
git add backend/scrapers/
git commit -m "feat: add scraper base class and watchmmafull module"

# 4. Push and open a PR to dev
git push origin feature/scraper-modularization
# → Open PR: feature/scraper-modularization → dev

# 5. After testing on dev, merge dev → main for release
git checkout main
git merge dev
git push origin main
```

---

## Commit Message Format

```
<type>: <short summary in present tense>

[optional body — what and why, not how]
```

| Type       | When to use                                  |
|------------|----------------------------------------------|
| `feat`     | New feature or capability                    |
| `fix`      | Bug fix                                      |
| `refactor` | Code change that doesn't fix a bug or add a feature |
| `chore`    | Config, deps, docs, CI — no production code  |
| `test`     | Adding or fixing tests                       |
| `perf`     | Performance improvement                      |

**Examples:**
```
feat: add Playwright session pooling to reduce stream latency
fix: handle missing MIME type for .txt HLS streams
refactor: move test_mma.py into backend/tests/
chore: add .gitignore entry for sports_tv.db
test: add pytest suite for watchmmafull scraper
perf: cache resolved m3u8 URLs with 30-min TTL
```

---

## What Goes in Each Branch

| Branch      | What lives here                                  |
|-------------|--------------------------------------------------|
| `main`      | Only merge-ready, tested code. Never commit directly. |
| `dev`       | Latest integrated work. Should always run.        |
| `feature/*` | One feature, one concern. Small and focused.      |
| `fix/*`     | Isolated bug fix only. No feature creep.          |

---

## PR Checklist (before merging to dev)

- [ ] Code runs locally without errors
- [ ] Relevant test script passes (or new test added)
- [ ] No debug `print()` statements left in
- [ ] Commit messages follow the format above
- [ ] `REFACTOR.md` or `ROADMAP.md` updated if applicable

---

## Release to Production (main)

1. All planned phase items are checked off in `ROADMAP.md`
2. `dev` branch is stable and tested on device/emulator
3. Merge `dev → main` with a release commit:
   ```
   chore: release v1.x — Phase X complete
   ```
4. Tag the release:
   ```bash
   git tag v1.x
   git push origin v1.x
   ```

---

_Last updated: 2026-06-15_
