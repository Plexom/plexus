#!/usr/bin/env python3
"""Looks for secrets where the readiness checklist and a release must not let one through.

"No key, certificate or credential in the iteration's commits" is not left to the
model reading the diff: a forty-character token in a diff of two thousand lines is
exactly what reading skims past. A pattern does not skim. What it finds
is shown masked, so the check itself does not copy the secret into the
conversation.

Two modes, from the project root:
    python3 secrets.py diff <base>     lines added, files added or changed, between <base> and HEAD
    python3 secrets.py path <path>     a file, a directory or an artefact — archives and
                                       compressed files opened, nested ones too

A match is a lead, not a verdict: a test fixture may hold a fake key on purpose.
The stage shows each to the user; nothing is dismissed silently.
Exit code: 0 — nothing found, and everything looked into; 2 — findings, listed, with anything
not looked into; 1 — could not look, at all or into some files (named). What was not read is
never reported as clean.
"""

import bz2
import codecs
import gzip
import io
import os
import re
import subprocess
import sys
import tarfile
import zipfile
import zlib

try:
    import lzma
except ImportError:  # a Python built without it
    lzma = None

# a name a secret is kept under: `password`, `DB_PASSWORD`, `api_key`, `"apiKey"` — after
# `_` too, where `\b` would not stand
KEY = (r"(?i)(?<![A-Za-z0-9])(?:password|passwd|secret|token|api[_-]?key|access[_-]?key)\w*"
       r"['\"]?\s*[:=]\s*")
PATTERNS = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY(?: BLOCK)?-----")),
    ("AWS access key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitHub token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{60,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,}")),
    ("npm token", re.compile(r"\bnpm_[A-Za-z0-9]{36}\b")),
    ("Hugging Face token", re.compile(r"\bhf_[A-Za-z0-9]{30,}\b")),
    ("Slack token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b")),
    ("Slack webhook", re.compile(r"\bhooks\.slack\.com/services/[A-Za-z0-9/]{20,}")),
    ("Telegram bot token", re.compile(r"\b\d{8,10}:AA[A-Za-z0-9_-]{33}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("Stripe live key", re.compile(r"\b[sr]k_live_[0-9A-Za-z]{20,}\b")),
    ("Anthropic API key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}")),
    ("OpenAI API key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}")),
    ("JSON web token", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("bearer token", re.compile(r"\bBearer\s+([A-Za-z0-9._~+/=-]{20,})")),
    ("password in an address", re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]*://[^/\s:@'\"]+:([^/\s@'\"]{3,})@")),
    ("password or token", re.compile(KEY + r"['\"]([^'\"\s]{8,})['\"]")),
]
# In code a value without quotes is a name or a call — `password = getPassword()` — never the
# secret itself. Unquoted secrets are written where values are bare: settings, environment
# files, shell scripts. There, and only there, a bare value counts too.
BARE = ("password or token, unquoted", re.compile(KEY + r"([^'\"\s#,;]{8,})"))
SETTINGS = re.compile(r"(?i)(^|/)(\.env[^/]*|[^/]*\.(ya?ml|properties|ini|cfg|conf|toml|env|sh|bash|zsh)"
                      r"|Dockerfile[^/]*|Makefile)$")
# a file of this kind is a secret by what it is, whatever it holds
FILES = [re.compile(p) for p in (r"(^|/)\.env(\.[^/]*)?$", r"\.pem$", r"\.key$", r"\.p12$",
                                 r"\.pfx$", r"(^|/)id_(rsa|dsa|ecdsa|ed25519)$",
                                 r"(^|/)credentials(\.json)?$", r"\.keystore$", r"\.jks$")]
HARMLESS_FILES = re.compile(r"(^|/)\.env\.(example|sample|template)$")
# a value that only names where the secret comes from is not one
PLACEHOLDER = re.compile(r"(?i)^(\$.*|\{\{.*|<[^>]*>|x{6,}|\*{6,}|changeme|password|secret|your[_-].*|"
                         r"example.*|dummy.*|test.*|fake.*|placeholder.*|process\.env.*|os\.environ.*)$")
CAP = 256 * 1024 * 1024  # read whole; a larger file is named as not looked into, never passed
DEPTH = 5  # archives inside archives, as deep as an artefact goes
STRINGS = re.compile(rb"[\x20-\x7e]{8,}")  # the text inside a binary, as `strings` finds it
# compressions opened here; one without an opener (no lzma in this Python) is named, not passed
COMPRESSED = [(b"\x1f\x8b", lambda f: gzip.GzipFile(fileobj=f), ".gz"),
              (b"BZh", bz2.BZ2File, ".bz2"),
              (b"\xfd7zXZ\x00", lzma.LZMAFile if lzma else None, ".xz")]
# what this script cannot open: named, so a key inside one is not passed as clean
SEALED = [(b"7z\xbc\xaf\x27\x1c", "a 7z archive"), (b"Rar!", "a rar archive"),
          (b"\x28\xb5\x2f\xfd", "zstd-compressed"), (b"xar!", "an installer package"),
          (b"!<arch>\n", "a Debian package"), (b"\xed\xab\xee\xdb", "an RPM package"),
          (b"\xd0\xcf\x11\xe0", "an MSI installer or an old Office file")]
SEALED_NAMES = re.compile(r"(?i)\.(dmg|br|appimage|snap)$")  # no telling bytes at the start


def mask(text):
    text = text.strip()
    return text[:4] + "…" + "*" * 6 if len(text) > 6 else "*" * 6


def scan_line(line, where=""):
    found = []
    for name, rx in PATTERNS + ([BARE] if SETTINGS.search(where) else []):
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
        for kind, shown in scan_line(line, where):
            out.append("%s:%d  %s  %s" % (where, n, kind, shown))


def git(*args):
    # paths as they are: quoted, `docs/ключи.txt` turns into `"docs/\320\272…"` and is skipped
    p = subprocess.run(["git", "-c", "core.quotePath=false"] + list(args), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True, encoding="utf-8",
                       errors="replace", timeout=60)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or "git %s failed" % " ".join(args))
    return p.stdout


def new_path(line):
    """The file a `+++` line of a diff names, or None for a deleted one. A name git still
    quotes — one holding `"`, `\\` or a control character — is unquoted here."""
    name = line[4:]
    if name.startswith('"') and name.endswith('"'):
        name = codecs.escape_decode(name[1:-1].encode("utf-8"))[0].decode("utf-8", "replace")
    return name[2:] if name.startswith("b/") else None


def scan_diff(base, out):
    git("rev-parse", "--verify", "--quiet", base + "^{commit}")
    # changed as well as added: a tracked .env that gets a new password is the same leak
    for row in git("diff", "--name-status", "--diff-filter=ACMR", base + "...HEAD").splitlines():
        status, name = row.split("\t")[0], row.split("\t")[-1]
        if secret_file(name):
            out.append("%s  a file of a kind that holds secrets, %s"
                       % (name, "added" if status[0] in "AC" else "changed"))
    current, line_no = None, 0
    for line in git("diff", "--unified=0", "--no-color", base + "...HEAD").splitlines():
        if line.startswith("+++ "):
            current = new_path(line)
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            line_no = int(m.group(1)) if m else 0
        elif line.startswith("+") and current:
            for kind, shown in scan_line(line[1:], current):
                out.append("%s:%d  %s  %s" % (current, line_no, kind, shown))
            line_no += 1


def scan_path(path, out, unread):
    if os.path.isdir(path):
        for dirpath, dirnames, filenames in os.walk(path):
            dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
            for f in filenames:
                scan_file(os.path.relpath(os.path.join(dirpath, f), path), os.path.join(dirpath, f),
                          out, unread)
    elif os.path.isfile(path):
        scan_file(os.path.basename(path), path, out, unread)
    else:
        raise RuntimeError("no such file or directory: %s" % path)


def scan_file(name, full, out, unread):
    if os.path.getsize(full) > CAP:
        if secret_file(name):
            out.append("%s  a file of a kind that holds secrets" % name)
        unread.append("%s — larger than %d MB" % (name, CAP >> 20))
        return
    with io.open(full, "rb") as f:
        scan_member(name, f.read(), out, unread)


UNPACK_ERRORS = (ValueError, OSError, EOFError, RuntimeError, NotImplementedError, zlib.error,
                 zipfile.BadZipFile, tarfile.TarError) + ((lzma.LZMAError,) if lzma else ())


def bounded(stream):
    data = stream.read(CAP + 1)
    if len(data) > CAP:
        raise ValueError("larger than %d MB unpacked" % (CAP >> 20))
    return data


def members(name, data):
    """(name, opener) of each file inside an archive or a compressed file, or None when the
    data is neither. An opener returns the member's bytes."""
    if data[:4] in (b"PK\x03\x04", b"PK\x05\x06"):
        z = zipfile.ZipFile(io.BytesIO(data))
        return [("%s!/%s" % (name, i.filename),
                 (lambda i=i: None) if i.flag_bits & 0x1 else (lambda i=i: bounded(z.open(i))))
                for i in z.infolist() if not i.is_dir()]
    if data[257:262] == b"ustar":
        t = tarfile.open(fileobj=io.BytesIO(data))
        return [("%s!/%s" % (name, m.name), lambda m=m: bounded(t.extractfile(m)))
                for m in t.getmembers() if m.isfile()]
    for magic, opener, ext in COMPRESSED:
        if data.startswith(magic) and opener:
            inner = name[:-len(ext)] if name.endswith(ext) else name + "!"
            return [(inner, lambda: bounded(opener(io.BytesIO(data))))]
    return None


def scan_member(name, data, out, unread, depth=0):
    """One file's bytes: opened when it is an archive or compressed, nested ones too; read
    as text; or, in a binary, the text strings it holds — a key compiled into an app is
    still a key. What cannot be opened is named in `unread`, never passed as clean."""
    if secret_file(name):
        out.append("%s  a file of a kind that holds secrets" % name)
    sealed = [what for magic, what in SEALED if data.startswith(magic)]
    if SEALED_NAMES.search(name):
        sealed.append("a disk image or compressed")
    if any(data.startswith(m) for m, opener, _ in COMPRESSED if not opener):
        sealed.append("xz-compressed")
    if sealed:
        unread.append("%s — %s, this check cannot open it" % (name, sealed[0]))
        return
    try:
        inside = members(name, data)
        if inside is not None and depth >= DEPTH:
            raise ValueError("archives nested deeper than %d" % DEPTH)
        for member, load in inside or []:
            body = load()
            if body is None:
                unread.append("%s — encrypted" % member)
            else:
                scan_member(member, body, out, unread, depth + 1)
    except UNPACK_ERRORS as e:
        unread.append("%s — could not be opened: %s" % (name, e))
        return
    if inside is not None:
        return
    if b"\0" in data[:8192]:
        for run in STRINGS.findall(data):
            for kind, shown in scan_line(run.decode("ascii"), name):
                out.append("%s  %s  %s, inside the binary" % (name, kind, shown))
        return
    scan_text(name, data.decode("utf-8", "replace"), out)


def main(argv):
    if len(argv) != 3 or argv[1] not in ("diff", "path"):
        sys.stderr.write("usage: secrets.py diff <base> | secrets.py path <file or directory>\n")
        return 1
    out, unread = [], []
    try:
        if argv[1] == "diff":
            scan_diff(argv[2], out)
        else:
            scan_path(argv[2], out, unread)
    except (RuntimeError, OSError, subprocess.SubprocessError, tarfile.TarError,
            zipfile.BadZipFile) as e:
        sys.stderr.write("Could not look for secrets: %s\n" % e)
        return 1
    if out:
        print("Secrets: %d possible, values masked — each is shown to the user:" % len(out))
        for line in out:
            print("  " + line)
    if unread:
        print("Not looked into: %d — each is shown to the user, who checks it or says why it "
              "holds no secret:" % len(unread))
        for line in unread:
            print("  " + line)
    if out:
        return 2
    if unread:
        return 1
    print("Secrets: none found in %s %s" % (argv[1], argv[2]))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
