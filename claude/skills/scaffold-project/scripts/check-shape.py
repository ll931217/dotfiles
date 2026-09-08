#!/usr/bin/env python3
"""Report which repos have drifted from the scaffold-project shape.

Usage:
  check-shape.py <repo> [<repo> ...]      check specific repos
  check-shape.py --all ~/Projects         check every git repo one level down
  check-shape.py <repo> --json            machine-readable output
  check-shape.py --self-check             run the built-in tests

Exit codes: 0 = every repo conforms, 1 = at least one gap, 2 = bad usage.
"""
import json
import subprocess
import sys
from pathlib import Path

BLOCKS = {
    "track block": ("<!-- BEGIN scaffold-project -->", "add it with the scaffold-project skill (conform mode)"),
    "quality block": ("<!-- BEGIN scaffold-project-quality -->", "append assets/claude-md-section-quality.md"),
    "platform block": ("<!-- BEGIN scaffold-project-platform -->", "append assets/claude-md-section-platform.md"),
}
FILES = {
    "README.md": "write one: what it is, how to run, test, configure",
    ".env.example": "list every config key with a placeholder",
    ".editorconfig": "copy from another conforming repo",
    ".gitignore": "add one for this language",
    ".claude/jira_issues": "create it empty, and gitignore it (wt worktree dispatch needs it)",
}
# a cap from the quality block -> a lint setting that must appear somewhere in the repo's config
CAPS = {
    "max-lines": ("max-lines", "funlen", "PLR0915", "max_lines", "MethodLength"),
    "complexity": ("complexity", "gocyclo", "max-complexity", "mccabe", "CyclomaticComplexity"),
    "max-params": ("max-params", "max-args", "too_many_arguments", "ParameterNumber"),
}
LINT_FILES = (
    "eslint.config.js", "eslint.config.mjs", ".eslintrc", ".eslintrc.js", ".eslintrc.json",
    "biome.json", "pyproject.toml", "ruff.toml", ".golangci.yml", ".golangci.yaml",
    "detekt.yml", "checkstyle.xml", "phpstan.neon", "clippy.toml", ".editorconfig",
)


def tracked(repo: Path, path: str) -> bool:
    r = subprocess.run(["git", "-C", str(repo), "ls-files", "--error-unmatch", path],
                       capture_output=True, text=True)
    return r.returncode == 0


def check(repo: Path) -> list[str]:
    gaps = []
    claude = repo / "CLAUDE.md"
    text = claude.read_text(errors="replace") if claude.is_file() else ""
    if not text:
        gaps.append("CLAUDE.md: missing -> run the scaffold-project skill in conform mode")
    for name, (marker, fix) in BLOCKS.items():
        if marker not in text:
            gaps.append(f"CLAUDE.md: no {name} -> {fix}")
    for name, fix in FILES.items():
        if not (repo / name).exists():
            gaps.append(f"{name}: missing -> {fix}")
    if (repo / ".env").exists() and tracked(repo, ".env"):
        gaps.append(".env: committed -> git rm --cached .env and add it to .gitignore")
    if (repo / ".claude/jira_issues").exists() and tracked(repo, ".claude/jira_issues"):
        gaps.append(".claude/jira_issues: committed -> git rm --cached it; the file must exist but stay ignored")
    configs = "\n".join((repo / f).read_text(errors="replace")
                        for f in LINT_FILES if (repo / f).is_file())
    if not configs.strip():
        gaps.append("lint config: none found -> configure the ecosystem linter with the quality-block caps")
    else:
        for cap, needles in CAPS.items():
            if not any(n in configs for n in needles):
                gaps.append(f"lint config: {cap} cap not configured -> add it so the quality block is enforced, not just documented")
    return gaps


def repos_under(root: Path) -> list[Path]:
    return sorted(p.parent for p in root.glob("*/.git"))


def self_check() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d) / "empty"
        repo.mkdir()
        gaps = check(repo)
        assert any("CLAUDE.md: missing" in g for g in gaps), gaps
        assert all(" -> " in g for g in gaps), "every gap must name a fix"
        (repo / "CLAUDE.md").write_text("\n".join(m for m, _ in BLOCKS.values()))
        for f in FILES:
            (repo / f).parent.mkdir(parents=True, exist_ok=True)
            (repo / f).write_text("x")
        (repo / "pyproject.toml").write_text("max-lines\ncomplexity\nmax-args\n")
        assert check(repo) == [], check(repo)
    print("self-check ok")
    return 0


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if "--self-check" in flags:
        return self_check()
    if "-h" in flags or "--help" in flags or not args:
        print(__doc__)
        return 0 if flags & {"-h", "--help"} else 2
    targets = repos_under(Path(args[0]).expanduser()) if "--all" in flags \
        else [Path(a).expanduser() for a in args]
    if not targets:
        print(f"no git repos found under {args[0]}", file=sys.stderr)
        return 2
    result = {str(t): check(t) for t in targets}
    if "--json" in flags:
        print(json.dumps(result, indent=2))
    else:
        for repo, gaps in result.items():
            if gaps:
                print(f"\n{repo}  {len(gaps)} gap(s)")
                for g in gaps:
                    print(f"  - {g}")
            else:
                print(f"\n{repo}  conforms")
        total = sum(len(g) for g in result.values())
        print(f"\n{len(result)} repo(s) checked, {total} gap(s). "
              f"{'Run the scaffold-project skill in conform mode to close them.' if total else 'All conform.'}")
    return 1 if any(result.values()) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
