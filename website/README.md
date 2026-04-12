# SuperOPC Website

Static landing page for SuperOPC — deployable to GitHub Pages, Vercel, or Cloudflare Pages.

## Deploy to GitHub Pages

1. Go to repo Settings → Pages
2. Set Source: `Deploy from a branch`
3. Branch: `main`, Folder: `/website`
4. Save — live in ~60 seconds at `https://gjts.github.io/SuperOPC/`

## Deploy to Vercel (custom domain)

```bash
npx vercel website/
```

## Local preview

```bash
# Python
python -m http.server 3000 --directory website

# Node
npx serve website
```

## Files

- `index.html` — Full landing page (single file, zero dependencies)
