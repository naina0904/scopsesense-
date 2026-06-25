import os


# =====================================================
# TRAVERSAL EXCLUSIONS
# =====================================================
# Directories that are safe to skip entirely.
# These contain generated/vendored/compiled artifacts
# that have zero semantic value for engineering intelligence
# and can be very large, slowing down indexing significantly.

_EXCLUDED_DIRS = {
    "node_modules",
    "dist",
    "build",
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".next",
    ".nuxt",
    "target",          # Java/Rust build output
    "bin",
    "obj",
    "out",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".eggs",
    "*.egg-info",
    ".idea",
    ".vscode",
    "vendor",          # Go / PHP vendor directories
    "Pods",            # iOS CocoaPods
    ".gradle",
    "cmake-build-debug",
    "cmake-build-release",
}

# =====================================================
# EXTENSION ALLOWLIST
# =====================================================
# Source code extensions: always semantically valuable.
# Config/manifest/doc extensions: highly valuable for
# SRS-to-code matching, dependency analysis, and narrative
# generation. Binary formats are intentionally absent.

_ALLOWED_EXTENSIONS = {
    # Core source
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".swift",
    ".kt",
    ".scala",
    # Config / infra / manifests
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".env",
    ".ini",
    ".cfg",
    ".conf",
    # Docs / requirements
    ".md",
    ".txt",
    ".rst",
    # Data / schema
    ".sql",
    ".graphql",
    ".proto",
    # Shell / scripting
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".makefile",
}

# Exact basenames that are semantically valuable even without extension
_ALLOWED_BASENAMES = {
    "Dockerfile",
    "Makefile",
    "Procfile",
    "Vagrantfile",
    ".env.example",
    ".env.sample",
    "docker-compose.yml",
    "docker-compose.yaml",
}

# =====================================================
# LOCKFILE EXCLUSION
# =====================================================
# Auto-generated dependency lock files are excluded from
# semantic indexing. They contain only version-pinning
# data, have no implementation signal, are often several
# MB in size, and pollute the vector store with noise
# that degrades SRS-to-code match quality.
#
# NOT excluded (semantically valuable):
#   package.json, pyproject.toml, requirements.txt,
#   Dockerfile, Cargo.toml, go.mod
# =====================================================

_LOCKFILE_BASENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pnpm-lock.yml",
    "poetry.lock",
    "Gemfile.lock",
    "Cargo.lock",
    "composer.lock",
    "bun.lockb",
    "packages.lock.json",   # .NET NuGet lock
    "pubspec.lock",         # Dart / Flutter
    "mix.lock",             # Elixir
    "go.sum",               # Go checksum database (not go.mod)
}


class CodeParser:

    def __init__(self):

        # Exposed for external inspection / testing
        self.supported_extensions = sorted(_ALLOWED_EXTENSIONS)
        self.excluded_dirs = _EXCLUDED_DIRS

    def parse_repository(
        self,
        repo_path
    ):

        documents = []
        skipped_binary = 0
        skipped_error = 0

        for root, dirs, files in os.walk(repo_path):

            # ─────────────────────────────────────────
            # TRAVERSAL EXCLUSION
            # Prune excluded directories in-place so
            # os.walk never descends into them.
            # ─────────────────────────────────────────
            dirs[:] = [
                d for d in dirs
                if d not in _EXCLUDED_DIRS
                and not d.endswith(".egg-info")
            ]

            for file in files:

                ext = os.path.splitext(file)[1].lower()
                basename = os.path.basename(file)

                # ─────────────────────────────────────
                # LOCKFILE EXCLUSION
                # Auto-generated lock files are excluded
                # before any I/O — they add no semantic
                # signal and bloat the vector store.
                # ─────────────────────────────────────
                if basename in _LOCKFILE_BASENAMES:
                    continue

                # ─────────────────────────────────────
                # EXTENSION / BASENAME FILTER
                # ─────────────────────────────────────
                if ext not in _ALLOWED_EXTENSIONS and basename not in _ALLOWED_BASENAMES:
                    continue

                full_path = os.path.join(root, file)

                try:

                    with open(
                        full_path,
                        "r",
                        encoding="utf-8",
                        errors="strict"   # reject files with invalid UTF-8
                    ) as f:
                        content = f.read()

                    # ─────────────────────────────────
                    # BINARY SAFETY NET
                    # If a file with a valid extension
                    # somehow contains null bytes (e.g.
                    # a compiled .py or corrupted file),
                    # skip it rather than sending binary
                    # garbage to the embedding model.
                    # ─────────────────────────────────
                    if "\x00" in content:
                        skipped_binary += 1
                        continue

                    # Skip trivially empty files
                    stripped = content.strip()
                    if not stripped:
                        continue

                    documents.append({
                        "path": full_path,
                        "content": content
                    })

                except (UnicodeDecodeError, UnicodeError):
                    # Binary file with a text extension — safe to skip
                    skipped_binary += 1

                except OSError as e:
                    # Permission error, broken symlink, etc.
                    skipped_error += 1
                    print(
                        f"[CodeParser] Skipped {full_path}: {e}"
                    )

        if skipped_binary or skipped_error:
            print(
                f"[CodeParser] Skipped {skipped_binary} binary "
                f"and {skipped_error} unreadable files in {repo_path}"
            )

        print(
            f"[CodeParser] Traversal complete. Parsed {len(documents)} "
            f"valid code files from {repo_path}."
        )

        return documents