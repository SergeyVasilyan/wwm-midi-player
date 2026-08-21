# Security Policy

## Supported versions

Only the latest release is supported. If you're on an older version,
please update before reporting an issue.

## Reporting a vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, use GitHub's private reporting: go to the
[Security tab](https://github.com/KrapFey/wwm-midi-player/security)
of this repository and click **"Report a vulnerability"**. This opens a
private advisory visible only to the maintainer until a fix is ready.

Please include:

- A description of the vulnerability and its potential impact.
- Steps to reproduce it (a sample `.mid` file, if the issue is triggered by
  loading one, is especially helpful).
- Any relevant environment details (Windows version, whether you're running
  from source or the installer build).

We'll acknowledge reports within a few days and aim to ship a fix as soon
as practical, coordinating disclosure timing with you.

## Scope

Realistic areas of concern for this project:

- **MIDI file parsing** — the app parses arbitrary `.mid`/`.midi` files
  (via `mido`) that a user opens; a malformed file causing a crash or
  resource exhaustion is in scope.
- **WWM mode input injection** — the app posts synthetic key events (via
  `pywin32`) only to the specific *Where Winds Meet* window it locates by
  title; anything that lets it target or affect other windows/processes
  would be a real bug.

This is a small, actively-developed hobby project — please be patient, and
thank you for helping keep it safe to use.
