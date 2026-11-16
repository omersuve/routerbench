"""Small explicit release surface. Historical/private material is never exported."""
import hashlib
import ast
import sys
import tomllib
import re
from pathlib import Path
import zipfile

FILES = ('README.md', 'LICENSE', 'NOTICE.md', 'pyproject.toml', 'AGENTS.md', '.gitignore',
         '.github/workflows/ci.yml')
DIRECTORIES = ('routerbench', 'tests', 'datasets', 'examples', 'results', 'docs')
SUFFIXES = {'.py', '.json', '.jsonl', '.md', '.toml', '.txt'}

def release_files(root):
    root = Path(root).resolve()
    paths = [root / name for name in FILES]
    for directory in DIRECTORIES:
        for path in sorted((root / directory).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in SUFFIXES:
                paths.append(path)
    if any(not p.is_file() or p.is_symlink() or root not in p.resolve().parents for p in paths):
        raise ValueError('release path missing, symlinked or outside root')
    return sorted(set(paths))

def audit_release(root):
    root = Path(root).resolve()
    paths = release_files(root)
    issues = []
    personal = re.compile('/' + r'(Users|home)/[A-Za-z0-9_.-]+|~/' + r'(Projects|\.agents|\.codex)')
    secret = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-' + r'[A-Za-z0-9_-]{20,}|Bearer\s+[A-Za-z0-9_-]{20,}')
    included = {p.relative_to(root).as_posix() for p in paths}
    metadata = tomllib.loads((root / 'pyproject.toml').read_text())
    if metadata.get('project', {}).get('dependencies', []):
        issues.append({'kind': 'unexpected_runtime_dependency'})
    for path in paths:
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding='utf-8')
        if personal.search(text):
            issues.append({'path': relative, 'kind': 'personal_path'})
        if secret.search(text):
            issues.append({'path': relative, 'kind': 'credential_pattern'})
        if path.name.startswith('.env'):
            issues.append({'path': relative, 'kind': 'env_file'})
        if path.suffix == '.py':
            for node in ast.walk(ast.parse(text)):
                names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and not node.level and node.module else []
                for name in names:
                    if name not in sys.stdlib_module_names and name != 'routerbench':
                        issues.append({'path':relative,'kind':'nonstdlib_import'})
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target or target.startswith('#'):
                    continue
                candidate = (path.parent / target.split('#')[0]).resolve()
                if root not in candidate.parents or candidate.relative_to(root).as_posix() not in included:
                    issues.append({'path':relative,'kind':'unshipped_markdown_link'})
    if not {'LICENSE', 'NOTICE.md', 'pyproject.toml'} <= included:
        issues.append({'kind':'missing_license_or_metadata'})
    return {'passed': not issues, 'file_count': len(paths), 'issues': issues,
            'scope': 'Explicit release surface only. Not an exhaustive secret detector or a legal opinion.',
            'excluded': ['archive', 'evidence', 'src', 'data', 'runs', 'dist', 'provider raw outputs', 'model weights'],
            'runtime_dependencies': [], 'license': 'MIT (original code, docs and authored synthetic datasets)'}

def export_release(root, output):
    root, output = Path(root).resolve(), Path(output)
    result = audit_release(root)
    if not result['passed']:
        raise ValueError('release audit failed')
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in release_files(root):
            info = zipfile.ZipInfo('routerbench-0.1.0/' + path.relative_to(root).as_posix(), date_time=(2026,1,1,0,0,0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return {**result, 'archive_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'published': False}
