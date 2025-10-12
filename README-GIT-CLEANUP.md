# === XÓA SUBMODULE CONFIG ĐÚNG CÁCH ===

# 1. Deinitialize
git submodule deinit -f backend 2>$null

# 2. Untrack (KHÔNG xóa files!)
git rm --cached -r backend 2>$null

# 3. Clean up git internals
Remove-Item .git/modules/backend -Recurse -Force -ErrorAction SilentlyContinue
git config -f .gitmodules --remove-section submodule.backend 2>$null
git config --remove-section submodule.backend 2>$null

# 4. Add to .gitignore
Add-Content .gitignore "`nbackend/" -ErrorAction SilentlyContinue

# 5. Commit
git add .gitignore
git commit -m "Remove backend submodule config, keep as local directory"

# 6. Push
git push origin main