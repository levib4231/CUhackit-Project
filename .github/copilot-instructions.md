<!-- Copilot/AI agent instructions for CUhackit-Project -->
# Copilot instructions — CUhackit-Project

Purpose: Quickly orient an AI coding assistant to be immediately useful in this repository.

- Repo shape: small static web project. Key files:
  - `README.md` — high-level project notes.
  - `CUTRACKIT/index.html` — single-page HTML entrypoint (DOM structure and content).
  - `CUTRACKIT/index.css` — the project's styling; modifications here change visual layout.

Big picture
- This is a tiny static site (no build system detected). Changes are made directly to HTML/CSS.
- There are no server components, JS frameworks, package manifests, or tests in the repository root.

Developer workflows (what actually works here)
- Run/preview: open `CUTRACKIT/index.html` in a browser or use a local static server (e.g. `python -m http.server` from the `CUTRACKIT` folder).
- No automated build or test commands discovered. Avoid adding assumptions about node/npm unless new files add them.

Project conventions and patterns
- Keep styles in `CUTRACKIT/index.css`. The project uses a single global stylesheet — prefer editing that file for visual changes.
- The HTML file is the canonical source of structure and content; modify `index.html` for markup changes (head/meta, nav, sections).
- Keep changes minimal and self-contained: this repo appears intended for small hackathon demos — prefer simple, explicit edits over introducing new tooling.

Integration points and external dependencies
- None discovered in the repository. If you introduce dependencies (node tooling, bundlers), add a clear README section and `package.json` so maintainers can opt-in.

Examples (concrete edits an agent might perform)
- Update page title and description (SEO/meta): edit the `<title>` and `<meta name="description">` in `CUTRACKIT/index.html`.
- Adjust layout spacing: modify CSS variables or selectors in `CUTRACKIT/index.css` that target `.container`, `header`, `main`, or `footer`.
- Add a new section: include a semantic `<section id="features">` in `CUTRACKIT/index.html` and style it in `index.css` using the existing naming patterns.

When to ask the user for direction
- Before adding tooling (npm, build steps, CI): confirm the preferred workflow.
- When proposed changes affect hosting or deployment (e.g., introduce a `gh-pages` branch or static site generator).

Commit & PR hints for the agent
- Use focused commits with one logical change per commit (e.g., "style: tweak header spacing" or "feat: add features section").
- If adding tooling, include an updated `README.md` with explicit run/preview commands.

If anything here looks incomplete or you want more detail (hosting, deployment, or ramping to a multi-file app), tell me which area to expand.
