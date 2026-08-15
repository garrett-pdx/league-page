# Brand assets

Hand-authored SVG for The Mudd League. Original marks in the tradition of a college seal — **not**
reproductions of the Harvey Mudd or Claremont-Mudd-Scripps seal. Own ring text, own centre, own year.

## Which file at which size

| File | Use | Notes |
| --- | --- | --- |
| `seal.svg` | 96px and up | Full mark: ring text, globe, sunburst, football, founding year |
| `seal-simple.svg` | 48px and below, and anything in between | Ring text and fine detail dropped. Nav logo and the SVG favicon |
| `wordmark.svg` | horizontal lockup | README, and anywhere the seal is too tall |
| `laurel.svg` | champion avatar | Home page and Trophy Room. Aspect ratio matches the 210×170 PNG it replaced |
| `banner.svg` | Trophy Room heading | **Carries no text** — see below |

`../favicons/safari-pinned-tab.svg` is a separate single-colour mask, not part of this folder's
palette. Safari discards its fills and paints the silhouette with the colour in the `mask-icon`
link in `src/app.html`.

## Palette

| Role | Colour | Contrast |
| --- | --- | --- |
| Ground / linework | `#000000` | — |
| Gold | `#EAAA00` | 10.25 under black; 6.20 under navy |
| Cardinal accent | `#862633` | 8.98 on white. 4.38 on gold, so it is a shape fill, never lettering |
| Navy ink | `#00316b` | 6.20 on gold |

These are the same values as `--goldFill`, `--cardinal` and `--navy700` in
`src/theme/_tokens.scss`. **They are duplicated here as literal hex on purpose** — see below — so
if a token changes, change it here by hand too.

## Three constraints these files are built around

**An SVG loaded through `<img src>` gets no page CSS and no webfonts.** `var(--goldFill)` resolves
to nothing there, which is why every colour is literal hex. Oswald does not load either, so any
text uses a fallback stack mirroring `--fontDisplay` and pins its width with `textLength` +
`lengthAdjust="spacingAndGlyphs"`. Without that, lettering overruns or gaps on machines without
Oswald — and the seal's ring text would no longer fit its arc.

**No text lives in `banner.svg`.** The file it replaced had "Champion's Cup" baked into the bitmap
in a grey system font — unselectable, untranslatable, invisible to a screen reader except through
`alt`, and unable to follow the display font. The ribbon is now decoration and `Awards.svelte`
lays the heading over it as real markup. Don't add a `<text>` element back.

**An XML comment may not contain two consecutive hyphens.** That includes writing CSS custom
property names in full. It is a parse error, not a warning, and it blanks the entire file — the
browser renders an error page instead of the image.

## Regenerating the raster icons

The PNG/ICO favicons and PWA icons are rendered from `seal-simple.svg`:

```
node scripts/render-icons.js
```

Its output is committed, and it is deliberately **not** part of `npm run build` — a build that
shells out to a native image library breaks on someone else's machine, and the mark changes about
once a year. `sharp` is a devDependency for the same reason; Vercel never runs it.

Two things that script gets right and a naive resize would not:

- **The android-chrome icons are declared `"purpose": "maskable any"`** in `static/manifest.json`.
  Android crops a maskable icon to a circle and guarantees only the central 80%. This mark *is* a
  circle filling its frame, so rendering it edge to edge puts the gold ring exactly where the crop
  lands. Those two sizes are inset to 72% on an opaque ground.
- **iOS composites a transparent home-screen icon onto black**, which would swallow the seal's
  black disc. The touch and maskable icons therefore get an opaque white ground; only the browser
  tab favicons keep their alpha.

`favicon.ico` is assembled by hand in that script rather than via a second dependency — an ICO is
a short header plus one directory entry per image, and since Vista the payloads may be PNGs.

The one thing still hand-maintained: the `mask-icon` colour at `src/app.html:18` and the tile
colour at `:22`, which are HTML attributes and cannot take `var()`.

## Dropping in a stag

The centre of `seal.svg` is geometric because organic silhouette work cannot be drawn by eye with
no rasterizer to check against. To add one later, replace the contents of the `#centre` group.
Supply it as **SVG, single-colour silhouette** — the path data inlines directly, stays sharp at
every size, and the pinned-tab mask accepts nothing else. It must still read at ~40px in the nav.
Licence matters because the site is public: prefer CC0 or public domain, and avoid anything
derived from a college athletics mark.
