# reconnaissancetechnologies.com — redesign

A static rebuild of [reconnaissancetechnologies.com](https://reconnaissancetechnologies.com) in a new visual language: a deep-blue gradient hero with an oversized, motion-blurred wordmark, white rounded panels floating on a near-black canvas, light numerals, numbered card rails and expandable list rows. All copy, page structure and URLs are carried over from the live site.

## Build

No dependencies beyond Python 3:

```sh
python3 build.py           # writes the site to dist/
python3 build.py --serve   # builds, then serves dist/ at http://localhost:8000
```

`dist/` is committed so the site can be deployed as-is to any static host (Netlify, Vercel, GitHub Pages, cPanel, S3…). Internal links are relative, so it also works from a sub-path or straight from disk.

## Structure

| Path | What it is |
| --- | --- |
| `content/site.json` | Site-wide data: navigation, services, industries, clients, testimonials, awards, tech stack, contact details, home-page copy |
| `content/pages/*.json` | One file per page (`our-services--cybersecurity.json` → `/our-services/cybersecurity/`). A hero (`word`, `title`, `body`, `cta`) plus a list of `sections` |
| `build.py` | The generator: page chrome, section renderers and the custom pages (home, services index, our work, solutions, CSR, 404) |
| `assets/css/style.css` | The design system (tokens at the top) |
| `assets/js/main.js` | Menus, mobile drawer, sticky bar, card rail, tabs, accordions, scroll reveal, enquiry form |
| `assets/video/` | Hero background loop (`hero.webm`, `hero.mp4` fallback, `hero-poster.jpg`). Re-encoded from the brand video: the 0.4–15.8s light-streak section, 1280px wide, no audio |
| `assets/img/` | Logo (vector, plus a white variant for dark backgrounds), favicon, client logos, award badges |

### Section types

`stats`, `cards`, `cta`, `intro`, `tabs`, `team`, `prose`, `contact`, `badges`, `openings`. The generator sets the page rhythm automatically. The first section is a white panel rising over the hero. After that, card groups alternate between white accordion lists and dark numbered card rails, and `cta` sections become dark bands. Cards that carry bullet `points` always render as accordion rows.

## Pages

Home, Our Services (index plus 11 service pages), 8 industry pages, Global Delivery Model, Engagement Model, About Us, Development Methodology, Partnerships, Career Overview, Contact Us, Awards, Media Coverage, CSR, Privacy Policy, Our Work, Products & Solutions, and a 404, along with `sitemap.xml` and `robots.txt`. URLs match the live site, including the existing `software-devlopment` and `web-appliaction-development` slugs, so current links and search rankings carry over.

## Content notes

- **Placeholder copy dropped.** The live services index is lorem ipsum, so its rows use each service page's own intro instead. The about page's fourth team card ("Lana Byrd … flowbite platform") is a template placeholder and was removed. So was the "Come discover Hidden Brains" line on the careers page.
- **Empty pages on the live site.** Blog, Webinars, Events, Case Studies and Certifications currently return empty pages and are left out of the navigation. Our Work, Solutions and CSR are built from the matching teaser copy on the live home page.
- **Products and client pages** (Mágico, BuzzForge, Stoqit, Blue Sea Travels, H.O.W Tech, CAC Foundation, Bliss Explorers) redirect off-site on the live site, and the new site links out to the same destinations.
- **Enquiry forms** have no backend on static hosting. Submitting one opens the visitor's email app with a pre-filled message to `enquiries@reconnaissancetechnologies.com`. To use a form service (Formspree, Netlify Forms, your own API), change the `<form>` in `contact_form()` in `build.py`.
- Typos in the source copy were kept as published so content stays one-to-one with the live site. Edit `content/pages/*.json` to correct them.
