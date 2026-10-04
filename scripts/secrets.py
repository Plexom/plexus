#!/usr/bin/env python3
"""Looks for secrets where the readiness checklist and a release must not let one through.

"No key, certificate or credential in the iteration's commits" is not left to the
model reading the diff: a forty-character token in a diff of two thousand lines is
exactly what reading skims past. A pattern does not skim. What it finds
is shown masked, so the check itself does not copy the secret into the
conversation.

Two modes, from the project root:
    python3 secrets.py diff <base>     lines and files added between <base> and HEAD
    python3 secrets.py path <path>     a file, a directory, or a .zip / .tar(.gz) artefact

A match is a lead, not a verdict: a test fixture may hold a fake key on purpose.
The stage shows each to the user; nothing is dismissed silently.
Exit code: 0 — nothing found; 2 — findings, listed; 1 — could not look (reason on stderr).
"""

import io
import os
import re
import subprocess
import sys
import tarfile
import zipfile

PATTERNS = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{20,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("password or token in the code",
     re.compile(r"(?i)\b(?:password|passwd|secret|token|api[_-]?key|access[_-]?key)\w*\s*[:=]\s*"
                r"['\"]([^'\"\s]{8,})['\"]")),
]
# a file of this kind is a secret by what it is, whatever it holds
FILES = [re.compile(p) for p in (r"(^|/)\.env(\.[^/]*)?$", r"\.pem$", r"\.key$", r"\.p12$",
                                 r"\.pfx$", r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",
                                 r"(^|/)credentials(\.json)?$", r"\.keystore$", r"\.jks$")]
HARMLESS_FILES = re.compile(r"(^|/)\.env\.(example|sample|template)$")
# a value that only names where the secret comes from is not one
PLACEHOLDER = re.compile(r"(?i)^(\$\{?\w+\}?|<[^>]*>|x{6,}|\*{6,}|changeme|your[_-].*|example.*|dummy.*|"
                         r"test.*|fake.*|placeholder.*|process\.env.*|os\.environ.*)$")
MAX_BYTES = 2 * 1024 * 1024  # a larger member is a binary or data, not where a key is typed


def mask(text):
    text = text.strip()
    return text[:4] + "…" + "*" * 6 if len(text) > 6 else "*" * 6


def scan_line(line):
    found = []
    for name, rx in PATTERNS:
        for m in rx.finditer(line):
            value = m.group(1) if m.groups() else m.group(0)
            if m.groups() and PLACEHOLDER.match(value):
                continue
            found.append((name, mask(value)))
    return found


def secret_file(name):
    return any(p.search(name) for p in FILES) and not HARMLESS_FILES.search(name)


def scan_text(where, text, out):
    for n, line in enumerate(text.splitlines(), 1):
        for kind, shown in scan_line(line):
            out.append("%s:%d  %s  %s" % (where, n, kind, shown))


def git(*args):
    p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True, errors="replace", timeout=60)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "git %s failed" % " ".join(args))
    return p.stdout


def scan_diff(base, out):
    git("rev-parse", "--verify", "--quiet", base + "^{commit}")
    for name in git("diff", "--name-only", "--diff-filter=A", base + "...HEAD").splitlines():
        if secret_file(name):
            out.append("%s  a file of a kind that holds secrets, added" % name)
    current, line_no = None, 0
    for line in git("diff", "--unified=0", "--no-color", base + "...HEAD").splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else None
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            line_no = int(m.group(1)) if m else 0
        elif line.startswith("+") and current:
            for kind, shown in scan_line(line[1:]):
                out.append("%s:%d  %s  %s" % (current, line_no, kind, shown))
            line_no += 1


def scan_path(path, out):
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            for f in filenames:
                full = os.path.join(dirpath, f)
                scan_member(os.path.relpath(full, path), lambda full=full: io.open(full, "rb").read(),
                            os.path.getsize(full), out)
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            for info in z.infolist():
                if not info.is_dir():
                    scan_member(info.filename, lambda info=info: z.read(info), info.file_size, out)
    elif tarfile.is_tarfile(path):
        with tarfile.open(path) as t:
            for m in t.getmembers():
                if m.isfile():
                    scan_member(m.name, lambda m=m: t.extractfile(m).read(), m.size, out)
    elif os.path.isfile(path):
        scan_member(os.path.basename(path), lambda: io.open(path, "rb").read(),
                    os.path.getsize(path), out)
    else:
        raise RuntimeError("no such file or directory: %s" % path)


def scan_member(name, load, size, out):
    if secret_file(name):
        out.append("%s  a file of a kind that holds secrets" % name)
    if size > MAX_BYTES:
        return
    data = load()
    if b"\0" in data[:8192]:
        return  # binary
    scan_text(name, data.decode("utf-8", "replace"), out)


def main(argv):
    if len(argv) != 3 or argv[1] not in ("diff", "path"):
        sys.stderr.write("usage: secrets.py diff <base> | secrets.py path <file or directory>\n")
        return 1
    out = []
    try:
        (scan_diff if argv[1] == "diff" else scan_path)(argv[2], out)
    except (RuntimeError, OSError, subprocess.SubprocessError, tarfile.TarError,
            zipfile.BadZipFile) as e:
        sys.stderr.write("Could not look for secrets: %s\n" % e)
        return 1
    if not out:
        print("Secrets: none found in %s %s" % (argv[1], argv[2]))
        return 0
    print("Secrets: %d possible, values masked — each is shown to the user:" % len(out))
    for line in out:
        print("  " + line)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
