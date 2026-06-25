import os
import re


class DependencyEngine:

    def analyze_repository(
        self,
        repo_path
    ):

        dependencies = []

        # Directories to skip
        excluded_dirs = {
            "node_modules", "dist", "build", ".git", "venv", ".venv",
            "__pycache__", ".next", ".nuxt", "target", "bin", "obj",
            "out", "coverage", ".pytest_cache", "vendor"
        }

        # -----------------------------------
        # WALK FILES
        # -----------------------------------

        for root, dirs, files in os.walk(repo_path):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:

                ext = os.path.splitext(file)[1].lower()
                if ext not in {".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"}:
                    continue

                file_path = os.path.join(
                    root,
                    file
                )

                try:

                    with open(

                        file_path,

                        "r",

                        encoding="utf-8",

                        errors="ignore"

                    ) as f:

                        content = f.read()

                    imports = []
                    if ext == ".py":
                        imports = self.extract_python_imports(content)
                    elif ext in {".js", ".jsx", ".ts", ".tsx"}:
                        imports = self.extract_js_imports(content)
                    elif ext == ".go":
                        imports = self.extract_go_imports(content)
                    elif ext == ".rs":
                        imports = self.extract_rust_imports(content)

                    dependencies.append({

                        "file":
                            file,

                        "imports":
                            imports
                    })

                except Exception:

                    continue

        return dependencies

    # -----------------------------------
    # IMPORT EXTRACTIONS
    # -----------------------------------

    def extract_python_imports(self, content):
        imports = []
        # import x
        pattern1 = r"import\s+([a-zA-Z0-9_\.]+)"
        # from x import y
        pattern2 = r"from\s+([a-zA-Z0-9_\.]+)\s+import"

        matches1 = re.findall(pattern1, content)
        matches2 = re.findall(pattern2, content)

        imports.extend(matches1)
        imports.extend(matches2)
        return list(set(imports))

    def extract_js_imports(self, content):
        imports = []
        # import ... from 'module'
        pattern1 = r"import\s+(?:(?:\s*[a-zA-Z0-9_\{\}\s\*\,]+\s*from\s+)|(?:\s*))['\"]([^'\"]+)['\"]"
        # require('module')
        pattern2 = r"require\(\s*['\"]([^'\"]+)['\"]\s*\)"
        # import('module')
        pattern3 = r"import\(\s*['\"]([^'\"]+)['\"]\s*\)"

        matches1 = re.findall(pattern1, content)
        matches2 = re.findall(pattern2, content)
        matches3 = re.findall(pattern3, content)

        imports.extend(matches1)
        imports.extend(matches2)
        imports.extend(matches3)
        return list(set(imports))

    def extract_go_imports(self, content):
        imports = []
        # Find single-line imports
        single_pattern = r"import\s+(?:[a-zA-Z0-9_\.]+\s+)?['\"]([^'\"]+)['\"]"
        matches_single = re.findall(single_pattern, content)
        imports.extend(matches_single)

        # Find multi-line import blocks: import ( ... )
        multi_blocks = re.findall(r"import\s*\(((?:[^)]|\n)*)\)", content)
        for block in multi_blocks:
            block_matches = re.findall(r"['\"]([^'\"]+)['\"]", block)
            imports.extend(block_matches)

        return list(set(imports))

    def extract_rust_imports(self, content):
        imports = []
        # use path::to::module;
        pattern1 = r"use\s+([a-zA-Z0-9_]+)(?:::\s*[a-zA-Z0-9_\{\}\*\,]+)*\s*;"
        # extern crate module;
        pattern2 = r"extern\s+crate\s+([a-zA-Z0-9_]+)\s*;"

        matches1 = re.findall(pattern1, content)
        matches2 = re.findall(pattern2, content)

        imports.extend(matches1)
        imports.extend(matches2)
        return list(set(imports))