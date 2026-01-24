#!/usr/bin/env python3
"""
generate_docs.py - Automatische Repo-Dokumentation für Disce/Kleiner Bär

Erzeugt:
  - docs/generated/repo_map.md      (Baumstruktur)
  - docs/generated/modules.md       (Python-Module mit Klassen/Funktionen)
  - docs/generated/integrations.md  (Erkannte externe Services)

Usage:
  python generate_docs.py [--root /path/to/repo]

Ohne --root wird das aktuelle Verzeichnis verwendet.
"""

import os
import ast
import argparse
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# =============================================================================
# KONFIGURATION
# =============================================================================

# Ordner, die ignoriert werden
IGNORE_DIRS = {
    '.git', '__pycache__', '.venv', 'venv', 'env', 
    'node_modules', '.idea', '.vscode', 'dist', 'build',
    '.pytest_cache', '.mypy_cache', 'eggs', '*.egg-info'
}

# Dateien, die ignoriert werden
IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db', '.gitignore', '.env',
    '*.pyc', '*.pyo', '*.so', '*.dylib'
}

# Dateiendungen für die Repo-Map
TRACKED_EXTENSIONS = {
    '.py', '.md', '.yaml', '.yml', '.json', '.toml', 
    '.txt', '.sh', '.sql', '.html', '.css', '.js'
}

# Patterns für Integration-Erkennung
INTEGRATION_PATTERNS = {
    'OpenAI': [
        r'openai\.', r'from openai', r'import openai',
        r'OPENAI_API_KEY', r'gpt-4', r'gpt-3\.5', r'ChatCompletion'
    ],
    'Azure': [
        r'azure\.', r'from azure', r'AZURE_', 
        r'speech_config', r'SpeechRecognizer', r'pronunciation'
    ],
    'Airtable': [
        r'airtable', r'AIRTABLE_', r'pyairtable', r'Airtable\('
    ],
    'Make/Integromat': [
        r'make\.com', r'integromat', r'webhook', r'MAKE_WEBHOOK'
    ],
    'Streamlit': [
        r'import streamlit', r'from streamlit', r'st\.'
    ],
    'Whisper': [
        r'whisper', r'transcribe', r'WHISPER_'
    ],
    'LanguageTool': [
        r'language_tool', r'languagetool', r'LanguageTool'
    ],
    'spaCy': [
        r'import spacy', r'from spacy', r'nlp\('
    ],
    'NLTK': [
        r'import nltk', r'from nltk'
    ],
    'HuggingFace': [
        r'transformers', r'from transformers', r'huggingface'
    ]
}

# =============================================================================
# HILFSFUNKTIONEN
# =============================================================================

def should_ignore(path: Path) -> bool:
    """Prüft, ob ein Pfad ignoriert werden soll."""
    name = path.name
    
    # Ignorierte Ordner
    for pattern in IGNORE_DIRS:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    
    # Ignorierte Dateien
    for pattern in IGNORE_FILES:
        if pattern.startswith('*'):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    
    return False


def get_tree_structure(root: Path, prefix: str = "", max_depth: int = 5, current_depth: int = 0) -> list[str]:
    """Erzeugt eine Baumstruktur als Liste von Strings."""
    if current_depth > max_depth:
        return [f"{prefix}... (max depth reached)"]
    
    lines = []
    items = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    
    # Filtern
    items = [item for item in items if not should_ignore(item)]
    
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        connector = "└── " if is_last else "├── "
        
        if item.is_dir():
            lines.append(f"{prefix}{connector}📁 {item.name}/")
            extension = "    " if is_last else "│   "
            lines.extend(get_tree_structure(item, prefix + extension, max_depth, current_depth + 1))
        else:
            # Nur getrackte Extensions
            if item.suffix in TRACKED_EXTENSIONS or item.name in {'Dockerfile', 'Makefile', 'requirements.txt'}:
                icon = "🐍" if item.suffix == ".py" else "📄"
                lines.append(f"{prefix}{connector}{icon} {item.name}")
    
    return lines


def analyze_python_file(filepath: Path) -> dict:
    """Analysiert eine Python-Datei und extrahiert Struktur."""
    result = {
        'classes': [],
        'functions': [],
        'imports': [],
        'docstring': None,
        'lines': 0,
        'error': None
    }
    
    try:
        content = filepath.read_text(encoding='utf-8')
        result['lines'] = len(content.splitlines())
        
        tree = ast.parse(content)
        
        # Modul-Docstring
        if (tree.body and isinstance(tree.body[0], ast.Expr) 
            and isinstance(tree.body[0].value, ast.Constant)):
            result['docstring'] = tree.body[0].value.value.strip().split('\n')[0][:100]
        
        for node in ast.walk(tree):
            # Klassen
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                result['classes'].append({
                    'name': node.name,
                    'methods': methods[:5],  # Max 5 Methoden anzeigen
                    'method_count': len(methods)
                })
            
            # Top-Level Funktionen
            elif isinstance(node, ast.FunctionDef) and hasattr(node, 'col_offset') and node.col_offset == 0:
                result['functions'].append(node.name)
            
            # Imports
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    result['imports'].append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result['imports'].append(node.module.split('.')[0])
        
        # Deduplizieren
        result['imports'] = sorted(set(result['imports']))
        
    except Exception as e:
        result['error'] = str(e)[:50]
    
    return result


def detect_integrations(root: Path) -> dict:
    """Durchsucht Python-Dateien nach Integration-Patterns."""
    integrations = defaultdict(list)
    
    for py_file in root.rglob('*.py'):
        if should_ignore(py_file) or any(should_ignore(p) for p in py_file.parents):
            continue
        
        try:
            content = py_file.read_text(encoding='utf-8')
            rel_path = py_file.relative_to(root)
            
            for integration, patterns in INTEGRATION_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        if str(rel_path) not in integrations[integration]:
                            integrations[integration].append(str(rel_path))
                        break
        except:
            pass
    
    return dict(integrations)


# =============================================================================
# GENERATOREN
# =============================================================================

def generate_repo_map(root: Path) -> str:
    """Erzeugt repo_map.md"""
    lines = [
        "# Repo Map",
        "",
        f"> Automatisch generiert am {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> Root: `{root.name}/`",
        "",
        "## Struktur",
        "",
        "```",
    ]
    
    lines.extend(get_tree_structure(root))
    lines.append("```")
    
    # Stats
    py_files = list(root.rglob('*.py'))
    py_files = [f for f in py_files if not any(should_ignore(p) for p in f.parents) and not should_ignore(f)]
    
    total_lines = 0
    for f in py_files:
        try:
            total_lines += len(f.read_text().splitlines())
        except:
            pass
    
    lines.extend([
        "",
        "## Stats",
        "",
        f"- **Python-Dateien:** {len(py_files)}",
        f"- **Gesamte Zeilen (Python):** {total_lines:,}",
        f"- **Durchschnitt pro Datei:** {total_lines // max(len(py_files), 1)} Zeilen",
    ])
    
    return "\n".join(lines)


def generate_modules_doc(root: Path) -> str:
    """Erzeugt modules.md"""
    lines = [
        "# Module Reference",
        "",
        f"> Automatisch generiert am {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    
    # Gruppiere nach Top-Level-Ordner
    modules_by_folder = defaultdict(list)
    
    for py_file in sorted(root.rglob('*.py')):
        if should_ignore(py_file) or any(should_ignore(p) for p in py_file.parents):
            continue
        
        rel_path = py_file.relative_to(root)
        
        # Top-Level-Ordner bestimmen
        parts = rel_path.parts
        folder = parts[0] if len(parts) > 1 else "(root)"
        
        analysis = analyze_python_file(py_file)
        modules_by_folder[folder].append((rel_path, analysis))
    
    for folder in sorted(modules_by_folder.keys()):
        lines.append(f"## 📁 {folder}")
        lines.append("")
        
        for rel_path, analysis in modules_by_folder[folder]:
            lines.append(f"### `{rel_path}`")
            
            if analysis['error']:
                lines.append(f"⚠️ Parse-Fehler: {analysis['error']}")
                lines.append("")
                continue
            
            lines.append(f"*{analysis['lines']} Zeilen*")
            
            if analysis['docstring']:
                lines.append(f"> {analysis['docstring']}")
            
            lines.append("")
            
            # Klassen
            if analysis['classes']:
                lines.append("**Klassen:**")
                for cls in analysis['classes']:
                    methods_str = ", ".join(cls['methods'][:3])
                    if cls['method_count'] > 3:
                        methods_str += f", ... (+{cls['method_count'] - 3})"
                    lines.append(f"- `{cls['name']}` → {methods_str or '(keine Methoden)'}")
                lines.append("")
            
            # Funktionen
            if analysis['functions']:
                funcs = analysis['functions'][:8]
                more = len(analysis['functions']) - 8
                funcs_str = ", ".join(f"`{f}()`" for f in funcs)
                if more > 0:
                    funcs_str += f" ... (+{more})"
                lines.append(f"**Funktionen:** {funcs_str}")
                lines.append("")
            
            # Key Imports
            external_imports = [i for i in analysis['imports'] 
                              if i not in {'os', 'sys', 'typing', 'pathlib', 're', 'json', 'datetime'}
                              and not i.startswith('_')][:6]
            if external_imports:
                lines.append(f"**Key Imports:** {', '.join(external_imports)}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    return "\n".join(lines)


def generate_integrations_doc(root: Path) -> str:
    """Erzeugt integrations.md"""
    integrations = detect_integrations(root)
    
    lines = [
        "# Integrations",
        "",
        f"> Automatisch generiert am {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Diese Datei listet externe Services/Libraries, die im Code referenziert werden.",
        "",
    ]
    
    if not integrations:
        lines.append("*Keine Integrationen erkannt.*")
        return "\n".join(lines)
    
    for integration in sorted(integrations.keys()):
        files = integrations[integration]
        lines.append(f"## {integration}")
        lines.append("")
        lines.append(f"Gefunden in {len(files)} Datei(en):")
        lines.append("")
        for f in sorted(files)[:10]:
            lines.append(f"- `{f}`")
        if len(files) > 10:
            lines.append(f"- ... und {len(files) - 10} weitere")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generiert Repo-Dokumentation")
    parser.add_argument('--root', type=str, default='.', help='Pfad zum Repo-Root')
    args = parser.parse_args()
    
    root = Path(args.root).resolve()
    
    if not root.exists():
        print(f"❌ Pfad existiert nicht: {root}")
        return
    
    # Output-Ordner erstellen
    output_dir = root / 'docs' / 'generated'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📂 Analysiere: {root}")
    print(f"📁 Output: {output_dir}")
    print()
    
    # Generieren
    print("🗺️  Generiere repo_map.md ...")
    (output_dir / 'repo_map.md').write_text(generate_repo_map(root), encoding='utf-8')
    
    print("📦 Generiere modules.md ...")
    (output_dir / 'modules.md').write_text(generate_modules_doc(root), encoding='utf-8')
    
    print("🔌 Generiere integrations.md ...")
    (output_dir / 'integrations.md').write_text(generate_integrations_doc(root), encoding='utf-8')
    
    print()
    print("✅ Fertig! Generierte Dateien:")
    for f in output_dir.glob('*.md'):
        print(f"   - {f.relative_to(root)}")


if __name__ == '__main__':
    main()
