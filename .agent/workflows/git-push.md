---
description: Branch management and deployment workflow
---

# Git Workflow: Main and Production

This workflow defines how changes are pushed to the repository.

## Default Pushes (Development and Updates)
By default, all updates, fixes, and features should be pushed to the `main` branch.

// turbo
1. Switch to main branch: `git checkout main`
2. Add changes: `git add .`
3. Commit: `git commit -m "Update message"`
4. Push: `git push origin main`

## Production Pushes (Explicit Request Only)
Pushing to the `produccion_sistema_v7` branch is ONLY allowed when:
- The user explicitly asks for it.
- The AI explicitly proposes it and the user approves.

// turbo
1. Switch to production branch: `git checkout produccion_sistema_v7`
2. Merge main: `git merge main`
3. Push: `git push origin produccion_sistema_v7`
4. Return to main: `git checkout main`
