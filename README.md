# trikkia

Reconstruction of early-2000s Italian cultural websites, scraped from the Wayback Machine and rebuilt with modern static site technology (Astro + Cloudflare Pages).

## Sites

### blue-room (blue-room.it, 2004–2006)
An experimental arts venue in Italy programming electronic music, video art, and contemporary art.
- Live music: Auditorium + Sala Studio
- Resident DJs, guest artists, A/V performances
- Flash-heavy original design (recreated with Ruffle + CSS)

### cinedetour (cinedetour.it / detour.it, ~2001)
— to be documented

## Structure

```
trikkia/
├── scraper.py          ← Wayback Machine CDX scraper
├── blue-room/
│   ├── scraped/        ← raw downloaded pages + assets
│   └── site/           ← Astro project (WIP)
└── cinedetour/
    ├── scraped/        ← raw downloaded pages + assets
    └── site/           ← Astro project (WIP)
```

## Scraping

```bash
python scraper.py blue-room blue-room.it
python scraper.py cinedetour cinedetour.it
```
