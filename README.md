# Claude Gallery

A horizontally scrolling project board for your HTML pages. Each project is a column, and the pages in it are cards ordered by priority (top is highest).

## Add pages
Drop a file in `content/<project>/`. A new folder becomes a new project automatically.

Optional tags inside each HTML file's `<head>`:

```html
<title>My Page</title>
<meta name="description" content="One-line summary shown on the card">
<meta name="tags" content="chart, q3">
<meta name="date" content="2026-11-06">
```

## Plan projects before they have pages
Add them to `site.json`. Each project can have a title, emoji, color, order, description and a status of `idea`, `planned`, `active` or `done`. A project with no pages shows as an empty column you can drag pages into.

## Reorder
- Drag the handle on a card to change its priority, or move it to another project.
- Drag the handle on a project header to reorder projects.
- With the keyboard, focus a handle and use the arrow keys.

Your arrangement is saved in your browser. To make it the default for everyone:
1. Click **Save layout** on the site and copy the text.
2. Save it as `layout.json` next to `build.py`.
3. Rebuild and push. **Reset order** goes back to the saved `layout.json`.

## Preview locally
```
python3 build.py
cd site && python3 -m http.server 8000
```
Open http://localhost:8000

## Publish (GitHub Pages, automatic)
1. Create a GitHub repo and push this folder to `main`.
2. Repo **Settings → Pages → Source: GitHub Actions**.
3. Every push rebuilds and redeploys. Site: `https://<user>.github.io/<repo>/`

## Publish (no git)
Run `python3 build.py`, then drag the `site/` folder into Netlify Drop or Cloudflare Pages.
