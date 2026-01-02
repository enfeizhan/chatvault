# Versioning Best Practices for ChatVault

This guide outlines how to manage versions for the ChatVault library and how to automate the process to avoid common pitfalls.

## 1. Semantic Versioning (SemVer)

We follow [SemVer 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

- **PATCH**: Bug fixes, documentation updates, and small internal refactors. No changes to the public API.
- **MINOR**: New features, new backends, or enhancements. Must be backwards compatible.
- **MAJOR**: Breaking changes to the API (e.g., renaming core classes, changing method signatures that users call).

## 2. Shared Development (AIlease & ChatVault)

Since you are often updating ChatVault while working on AIlease, follow these tips to avoid package management friction:

### Editable Installs (Local Dev)
Instead of frequently updating the version and reinstalling, use an **editable install** in your application environment:

```bash
cd /path/to/AIlease
pip install -e /path/to/chatvault
```

With an editable install, any changes you make to the ChatVault source code are immediately reflected in AIlease without needing to bump the version or reinstall.

### Version Pinning in AIlease
In AIlease's `pyproject.toml` or `requirements.txt`, use semantic ranges:

```toml
# Recommended: Allow minor updates but prevent breaking changes
chatvault = ">=0.1.0,<1.0.0"
```

## 3. Automation with `hatch-vcs`

To avoid forgetting to update `version = "0.x.y"` in `pyproject.toml`, we use `hatch-vcs`. This plugin pulls the version number directly from your **Git Tags**.

### How it works:
1. We configure Hatch to use `vcs` for dynamic versioning.
2. When you want to release a new version, you simply tag your commit:
   ```bash
   git tag v0.1.1
   git push origin v0.1.1
   ```
3. Hatch automatically uses `0.1.1` as the package version during build/publish.

## 4. Avoiding "Small Update" Fatigue

If you have a small fix that doesn't warrant a PyPI release:
1. Commit it to the `main` branch.
2. If AIlease needs it but you aren't ready for a full PyPI push, AIlease can point to the Git commit directly:
   ```bash
   pip install git+https://github.com/enfeizhan/chatvault.git@main
   ```
3. Only tag and push to PyPI when you have a "milestone" or a set of stable fixes.
