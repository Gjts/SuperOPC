#!/usr/bin/env python3
"""
skill_extractor.py — Extract architectural patterns and skills from GitHub projects.

Inspired by skill-from-masters / skill-from-github.  Analyzes high-star
repositories to extract reusable knowledge:
  - Project structure patterns
  - Technology stack choices
  - Architecture decisions (from README, docs, etc.)
  - Testing and CI patterns
  - Dependency choices

Output is stored as structured JSON in .opc/intelligence/extracted-skills/
and can be used by the context_assembler to inform planning and execution.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REQUEST_TIMEOUT = 15
USER_AGENT = "SuperOPC-SkillExtractor/1.0"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = REPO_ROOT / ".opc" / "intelligence" / "extracted-skills"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


@dataclass
class ExtractedSkill:
    repo: str
    stars: int = 0
    language: str = ""
    description: str = ""
    url: str = ""
    structure_pattern: dict[str, Any] = field(default_factory=dict)
    tech_stack: list[str] = field(default_factory=list)
    architecture_hints: list[str] = field(default_factory=list)
    testing_patterns: list[str] = field(default_factory=list)
    ci_patterns: list[str] = field(default_factory=list)
    key_dependencies: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    extracted_at: str = field(default_factory=_now)


COMMON_CONFIG_FILES = {
    "package.json": "node",
    "requirements.txt": "python",
    "Pipfile": "python",
    "pyproject.toml": "python",
    "Cargo.toml": "rust",
    "go.mod": "go",
    "build.gradle": "java/kotlin",
    "pom.xml": "java",
    "Gemfile": "ruby",
    "composer.json": "php",
    "*.csproj": "dotnet",
}

CI_FILES = [
    ".github/workflows",
    ".gitlab-ci.yml",
    ".circleci/config.yml",
    "Jenkinsfile",
    ".travis.yml",
    "azure-pipelines.yml",
]

TEST_INDICATORS = [
    "tests/", "test/", "__tests__/", "spec/", "specs/",
    "jest.config", "pytest.ini", "conftest.py", ".rspec",
    "vitest.config", "karma.conf", "cypress.config",
]

ARCHITECTURE_KEYWORDS = [
    "monorepo", "microservice", "serverless", "event-driven",
    "hexagonal", "clean architecture", "domain-driven",
    "cqrs", "event sourcing", "actor model",
    "plugin", "middleware", "pipeline",
]


class SkillExtractor:
    """Extracts architectural patterns and skills from GitHub repositories."""

    def __init__(self, output_dir: Path | None = None):
        self._output_dir = output_dir or OUTPUT_DIR

    def extract_from_repo(self, owner_repo: str) -> ExtractedSkill:
        print(f"\n🔍 Analyzing {owner_repo}...")

        repo_data = self._fetch_repo_metadata(owner_repo)
        tree = self._fetch_repo_tree(owner_repo)
        readme_text = self._fetch_readme(owner_repo)

        skill = ExtractedSkill(
            repo=owner_repo,
            stars=repo_data.get("stargazers_count", 0),
            language=repo_data.get("language", "") or "",
            description=repo_data.get("description", "") or "",
            url=repo_data.get("html_url", ""),
        )

        skill.structure_pattern = self._analyze_structure(tree)
        skill.tech_stack = self._detect_tech_stack(tree, repo_data)
        skill.architecture_hints = self._detect_architecture(tree, readme_text)
        skill.testing_patterns = self._detect_testing(tree)
        skill.ci_patterns = self._detect_ci(tree)
        skill.key_dependencies = self._extract_dependencies(owner_repo, tree)
        skill.lessons = self._synthesize_lessons(skill)

        self._persist(skill)
        return skill

    def search_and_extract(self, query: str, *, limit: int = 5, min_stars: int = 1000) -> list[ExtractedSkill]:
        print(f"🔎 Searching GitHub for '{query}' (min {min_stars} stars)...")
        safe_q = urllib.parse.quote(f"{query} stars:>{min_stars}")
        url = f"https://api.github.com/search/repositories?q={safe_q}&sort=stars&order=desc&per_page={limit}"

        try:
            data = _fetch_json(url)
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"  ⚠️ Search failed: {e}")
            return []

        results: list[ExtractedSkill] = []
        for item in data.get("items", [])[:limit]:
            full_name = item["full_name"]
            try:
                skill = self.extract_from_repo(full_name)
                results.append(skill)
            except Exception as e:
                print(f"  ⚠️ Failed to analyze {full_name}: {e}")

        return results

    def _fetch_repo_metadata(self, owner_repo: str) -> dict[str, Any]:
        try:
            return _fetch_json(f"https://api.github.com/repos/{owner_repo}")
        except (urllib.error.URLError, json.JSONDecodeError):
            return {}

    def _fetch_repo_tree(self, owner_repo: str) -> list[str]:
        try:
            data = _fetch_json(
                f"https://api.github.com/repos/{owner_repo}/git/trees/HEAD?recursive=1"
            )
            return [item["path"] for item in data.get("tree", []) if item.get("type") == "blob"]
        except (urllib.error.URLError, json.JSONDecodeError):
            return []

    def _fetch_readme(self, owner_repo: str) -> str:
        for name in ["README.md", "readme.md", "Readme.md"]:
            try:
                url = f"https://raw.githubusercontent.com/{owner_repo}/HEAD/{name}"
                return _fetch_text(url)[:8000]
            except urllib.error.URLError:
                continue
        return ""

    def _analyze_structure(self, tree: list[str]) -> dict[str, Any]:
        top_dirs: set[str] = set()
        depth_counts = {1: 0, 2: 0, 3: 0}
        total_files = len(tree)

        for path in tree:
            parts = path.split("/")
            if len(parts) > 1:
                top_dirs.add(parts[0])
            depth = min(len(parts), 3)
            depth_counts[depth] = depth_counts.get(depth, 0) + 1

        has_src = any(d in top_dirs for d in ["src", "lib", "app", "pkg", "internal"])
        has_tests = any(d in top_dirs for d in ["tests", "test", "__tests__", "spec"])
        has_docs = any(d in top_dirs for d in ["docs", "doc", "documentation"])
        has_ci = any(d in top_dirs for d in [".github", ".circleci", ".gitlab"])

        pattern = "standard"
        if any(d in top_dirs for d in ["packages", "apps", "libs"]):
            pattern = "monorepo"
        elif has_src and total_files < 50:
            pattern = "minimal"
        elif total_files > 500:
            pattern = "large-scale"

        return {
            "pattern": pattern,
            "top_level_dirs": sorted(top_dirs)[:20],
            "total_files": total_files,
            "has_src": has_src,
            "has_tests": has_tests,
            "has_docs": has_docs,
            "has_ci": has_ci,
        }

    def _detect_tech_stack(self, tree: list[str], repo_data: dict) -> list[str]:
        stack: list[str] = []
        primary_lang = repo_data.get("language", "")
        if primary_lang:
            stack.append(primary_lang)

        tree_set = set(tree)
        for config_file, tech in COMMON_CONFIG_FILES.items():
            if config_file in tree_set and tech not in stack:
                stack.append(tech)

        if "docker-compose.yml" in tree_set or "Dockerfile" in tree_set:
            stack.append("docker")
        if any("terraform" in p.lower() for p in tree):
            stack.append("terraform")

        return stack[:10]

    def _detect_architecture(self, tree: list[str], readme: str) -> list[str]:
        hints: list[str] = []
        readme_lower = readme.lower()

        for keyword in ARCHITECTURE_KEYWORDS:
            if keyword in readme_lower:
                hints.append(keyword)

        tree_str = " ".join(tree).lower()
        if any(d in tree_str for d in ["packages/", "apps/", "libs/"]):
            hints.append("monorepo")
        if any(d in tree_str for d in ["domain/", "domains/"]):
            hints.append("domain-driven")
        if any(d in tree_str for d in ["handlers/", "events/"]):
            hints.append("event-driven")
        if any(d in tree_str for d in ["middleware/", "middlewares/"]):
            hints.append("middleware-pipeline")

        return list(dict.fromkeys(hints))[:10]

    def _detect_testing(self, tree: list[str]) -> list[str]:
        patterns: list[str] = []
        tree_str = " ".join(tree).lower()

        for indicator in TEST_INDICATORS:
            if indicator.rstrip("/") in tree_str:
                patterns.append(indicator.rstrip("/"))

        test_files = [p for p in tree if "test" in p.lower() or "spec" in p.lower()]
        total_files = len(tree) or 1
        test_ratio = len(test_files) / total_files

        if test_ratio > 0.3:
            patterns.append("high-test-coverage (>30% test files)")
        elif test_ratio > 0.1:
            patterns.append("moderate-test-coverage (10-30%)")

        return list(dict.fromkeys(patterns))[:8]

    def _detect_ci(self, tree: list[str]) -> list[str]:
        patterns: list[str] = []
        for ci_file in CI_FILES:
            if any(p.startswith(ci_file.rstrip("/")) for p in tree):
                patterns.append(ci_file)
        return patterns

    def _extract_dependencies(self, owner_repo: str, tree: list[str]) -> list[str]:
        deps: list[str] = []

        if "package.json" in tree:
            try:
                url = f"https://raw.githubusercontent.com/{owner_repo}/HEAD/package.json"
                pkg = json.loads(_fetch_text(url))
                all_deps = list(pkg.get("dependencies", {}).keys())[:10]
                deps.extend(all_deps)
            except (urllib.error.URLError, json.JSONDecodeError):
                pass

        if "requirements.txt" in tree:
            try:
                url = f"https://raw.githubusercontent.com/{owner_repo}/HEAD/requirements.txt"
                text = _fetch_text(url)
                for line in text.splitlines()[:15]:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        pkg_name = line.split("=")[0].split(">")[0].split("<")[0].split("[")[0].strip()
                        if pkg_name:
                            deps.append(pkg_name)
            except urllib.error.URLError:
                pass

        return deps[:15]

    def _synthesize_lessons(self, skill: ExtractedSkill) -> list[str]:
        lessons: list[str] = []

        struct = skill.structure_pattern
        if struct.get("pattern") == "monorepo":
            lessons.append("Uses monorepo structure — consider for multi-package projects")
        if struct.get("has_tests") and struct.get("has_ci"):
            lessons.append("Good engineering practice: test suite + CI pipeline present")
        if not struct.get("has_tests"):
            lessons.append("No test directory detected — avoid this anti-pattern")

        if "event-driven" in skill.architecture_hints:
            lessons.append("Event-driven architecture — good for decoupled, scalable systems")
        if "clean architecture" in skill.architecture_hints:
            lessons.append("Clean architecture layers — good separation of concerns")

        if skill.stars > 10000:
            lessons.append(f"High-star project ({skill.stars}) — likely has battle-tested patterns")
        if len(skill.key_dependencies) > 10:
            lessons.append("Heavy dependency tree — watch for supply chain complexity")

        return lessons

    def _persist(self, skill: ExtractedSkill) -> None:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        safe_name = skill.repo.replace("/", "--")
        filepath = self._output_dir / f"{safe_name}.json"
        filepath.write_text(
            json.dumps(asdict(skill), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  ✅ Saved to {filepath}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperOPC Skill Extractor — Learn from GitHub")
    sub = parser.add_subparsers(dest="command")

    analyze = sub.add_parser("analyze", help="Analyze a specific repository")
    analyze.add_argument("repo", help="owner/repo (e.g. vercel/next.js)")

    search = sub.add_parser("search", help="Search and analyze top repos for a topic")
    search.add_argument("query", help="Search query")
    search.add_argument("--limit", type=int, default=3, help="Number of repos to analyze")
    search.add_argument("--min-stars", type=int, default=1000, help="Minimum star count")

    args = parser.parse_args()
    extractor = SkillExtractor()

    if args.command == "analyze":
        skill = extractor.extract_from_repo(args.repo)
        print(f"\n📊 {skill.repo} ({skill.stars} ⭐)")
        print(f"   Stack: {', '.join(skill.tech_stack)}")
        print(f"   Architecture: {', '.join(skill.architecture_hints) or 'not detected'}")
        print(f"   Testing: {', '.join(skill.testing_patterns) or 'not detected'}")
        print(f"   Lessons:")
        for lesson in skill.lessons:
            print(f"     - {lesson}")

    elif args.command == "search":
        skills = extractor.search_and_extract(args.query, limit=args.limit, min_stars=args.min_stars)
        print(f"\n📊 Analyzed {len(skills)} repositories:")
        for skill in skills:
            print(f"  {skill.repo} ({skill.stars} ⭐) — {', '.join(skill.tech_stack)}")
            for lesson in skill.lessons[:2]:
                print(f"    - {lesson}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
