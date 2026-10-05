/*
The league's look, generated from league/league.json: the colour tokens, the brand art and the
icons.

    npm run brand          (node scripts/brand.mjs [--no-icons] [--out <dir>])

--out writes the tokens and art to <dir> instead (no icons), to try a palette without touching
the site. LEAGUE_CONFIG points it at another league's league.json.

From `theme` in league.json -- usually just `primary` (a dark brand colour) and `trophy` (the
championship fill colour) -- this writes:

    src/theme/_league.scss   the colour tokens: a contrast-checked ramp of the primary
                             (--brand900 .. --brand050), the trophy colours, the emblem colour,
                             and Sass values for the Material theme
    static/brand/*.svg       seal, simple seal, wordmark, ribbon and laurel, from
                             scripts/brand-templates/ with the league's name, tagline, founding
                             year and colours. A file in league/brand/ with the same name
                             replaces the generated one, so a league can use hand-made art.
    static/favicons, static/pwa icons   rendered from the simple seal (scripts/render-icons.js)
    static/pwa launch screens           the seal and wordmark on white, one per size in src/app.html

All outputs are committed; nothing here runs during a build. Re-run after changing the theme,
the name or the founding year, then `npm run smui-theme-light` (dev does not recompile Sass).

Contrast is measured against #ebebeb, the darker end of the page background, which is the
figure that governs. Targets: brand700 at least 7:1 (headings, ink), brand500 6.1:1 (AA small
text), brand400 3.54:1 (borders, icons and large text only), trophyInk 5.25:1. Any token can be
pinned in theme.tokens, which is how a league keeps an existing palette exactly.
*/
import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const configPath = process.env.LEAGUE_CONFIG || resolve(root, 'league/league.json');
const leagueDir = dirname(configPath);
const league = JSON.parse(readFileSync(configPath, 'utf8'));
const theme = league.theme || {};
const outArg = process.argv.indexOf('--out');
const scratch = outArg > -1 ? resolve(process.argv[outArg + 1]) : null;

/* ---- colour arithmetic ------------------------------------------------------------------ */

const hexToRgb = (hex) => {
    const h = hex.replace('#', '');
    const full = h.length === 3 ? h.split('').map((c) => c + c).join('') : h;
    return [0, 2, 4].map((i) => parseInt(full.slice(i, i + 2), 16));
};
const rgbToHex = (rgb) => '#' + rgb.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, '0')).join('');
const rgbToHsl = ([r, g, b]) => {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b);
    const l = (max + min) / 2;
    if(max === min) return [0, 0, l];
    const d = max - min;
    const s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    const h = max === r ? (g - b) / d + (g < b ? 6 : 0) : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
    return [h / 6, s, l];
};
const hslToRgb = ([h, s, l]) => {
    if(s === 0) return [l * 255, l * 255, l * 255];
    const q = l < 0.5 ? l * (1 + s) : l + s - l * s, p = 2 * l - q;
    const f = (t) => {
        t = (t + 1) % 1;
        if(t < 1 / 6) return p + (q - p) * 6 * t;
        if(t < 1 / 2) return q;
        if(t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
        return p;
    };
    return [f(h + 1 / 3) * 255, f(h) * 255, f(h - 1 / 3) * 255];
};
const luminance = (hex) => {
    const [r, g, b] = hexToRgb(hex).map((v) => {
        v /= 255;
        return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
    });
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a, b) => {
    const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
    return (x + 0.05) / (y + 0.05);
};
const mix = (a, b, t) => {
    const [x, y] = [hexToRgb(a), hexToRgb(b)];
    return rgbToHex(x.map((v, i) => v + (y[i] - v) * t));
};

const BG = '#ebebeb';

// The shade of `hex` (same hue and saturation) that measures `target` against the page.
const shadeAt = (hex, target) => {
    const [h, s] = rgbToHsl(hexToRgb(hex));
    let lo = 0, hi = rgbToHsl(hexToRgb(BG))[2];
    for(let i = 0; i < 40; i++) {
        const mid = (lo + hi) / 2;
        if(contrast(rgbToHex(hslToRgb([h, s, mid])), BG) > target) lo = mid; else hi = mid;
    }
    return rgbToHex(hslToRgb([h, s, (lo + hi) / 2]));
};

/* ---- palette ------------------------------------------------------------------------------ */

const warnings = [];
const primary = theme.primary || '#00316b';
const trophy = theme.trophy || '#EAAA00';

const brand = {};
const c700 = contrast(primary, BG);
if(c700 >= 7) brand[700] = primary;
else {
    brand[700] = shadeAt(primary, 7.5);
    warnings.push(`theme.primary ${primary} is ${c700.toFixed(2)}:1 on the page, below the 7:1 headings need; using ${brand[700]}`);
}
const c = contrast(brand[700], BG);
brand[900] = shadeAt(brand[700], Math.min(16, Math.max(13.74, c + 3)));
brand[800] = shadeAt(brand[700], (contrast(brand[900], BG) + c) / 2);
brand[600] = shadeAt(brand[700], (c + 6.1) / 2);
brand[500] = shadeAt(brand[700], 6.1);
brand[400] = shadeAt(brand[700], 3.54);
brand[100] = mix(brand[400], '#ffffff', 0.86);
brand['050'] = mix(brand[400], '#ffffff', 0.94);

const tokens = {
    ...Object.fromEntries(Object.entries(brand).map(([k, v]) => [`brand${k}`, v])),
    accentBorder: mix(brand[700], '#ffffff', 0.79),
    trophyFill: trophy,
    trophyInk: shadeAt(trophy, 5.25),
    trophyOnFill: null, // decided below, after pins
    emblem: theme.emblem || brand[600],
    sealGround: theme.sealGround || brand[900],
    ...(theme.tokens || {}),
};
// Ink on a trophy fill: the brand colour when it reads (4.5:1), else black or white.
if(!theme.tokens?.trophyOnFill) {
    tokens.trophyOnFill = contrast(tokens.brand700, tokens.trophyFill) >= 4.5 ? 'var(--brand700)'
        : contrast('#000000', tokens.trophyFill) >= contrast('#ffffff', tokens.trophyFill) ? '#000000' : '#ffffff';
}
const trophyShade = theme.tokens?.trophyShade || (() => {
    const [h, s, l] = rgbToHsl(hexToRgb(tokens.trophyFill));
    return rgbToHex(hslToRgb([h, s, l * 0.86]));
})();
if(contrast(tokens.brand500, BG) < 4.5) warnings.push(`brand500 ${tokens.brand500} is below 4.5:1 for small text`);
if(contrast(tokens.trophyInk, BG) < 4.5) warnings.push(`trophyInk ${tokens.trophyInk} is below 4.5:1`);

/* ---- tokens file ---------------------------------------------------------------------------- */

const [r, g, b] = hexToRgb(tokens.brand700);
const css = `// GENERATED by scripts/brand.mjs from league/league.json -- do not edit. Change theme in
// league.json (or pin a value in theme.tokens) and run \`npm run brand\`.

// Sass values for the Material theme and upstream's :root block, which cannot take var().
$brand700: ${tokens.brand700};
$brand400: ${tokens.brand400};
$brand100: ${tokens.brand100};

:root {
  // Primary ramp. On #ebebeb: brand700 ${contrast(tokens.brand700, BG).toFixed(2)}, brand500 ${contrast(tokens.brand500, BG).toFixed(2)},
  // brand400 ${contrast(tokens.brand400, BG).toFixed(2)} (borders, icons and large text only).
${['900', '800', '700', '600', '500', '400', '100', '050'].map((k) => `  --brand${k}: ${tokens[`brand${k}`]};`).join('\n')}
  --accentBorder: ${tokens.accentBorder};
  --shadowCardHover: 0 6px 14px -4px rgba(${r}, ${g}, ${b}, 0.22), 0 2px 6px -2px rgba(${r}, ${g}, ${b}, 0.14);

  // Championship colour: a fill with ink on it, never ink on the page (trophyInk is for that).
  --trophyInk: ${tokens.trophyInk};
  --trophyFill: ${tokens.trophyFill};
  --trophyOnFill: ${tokens.trophyOnFill};

  // Emblem colour: art only, never a second interactive colour.
  --emblem: ${tokens.emblem};
}
`;
if(scratch) mkdirSync(scratch, { recursive: true });
writeFileSync(scratch ? resolve(scratch, '_league.scss') : resolve(root, 'src/theme/_league.scss'), css);

/* ---- brand art ------------------------------------------------------------------------------- */

const escapeXml = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const name = league.name;
const sealName = (league.shortName && name.length > 22 ? league.shortName : name).toUpperCase();
const tagline = (theme.tagline || (league.dynasty ? 'Dynasty Football' : league.keepers ? 'Keeper Football' : 'Fantasy Football')).toUpperCase();
const year = league.founded ? String(league.founded) : '';

// Ring text: ~12.5 units per character at 16px, the top arc holds about 270.
const ringLength = (text) => Math.min(270, Math.round(text.length * 12.5));
const ringFont = (text) => Math.max(11, Math.min(16, Math.round(16 * 270 / Math.max(270, text.length * 12.5) * 10) / 10));
const wordLength = Math.min(400, Math.round(name.length * 25.4));

const values = {
    name: escapeXml(name),
    nameUpper: escapeXml(name.toUpperCase()),
    sealTop: escapeXml(sealName),
    sealBottom: escapeXml(tagline),
    tagline: escapeXml(tagline),
    taglineLower: escapeXml(tagline.toLowerCase()),
    year: escapeXml(year),
    topLength: ringLength(sealName),
    bottomLength: Math.min(250, ringLength(tagline) + 24),
    ringFontSize: ringFont(sealName),
    wordLength,
    wordFontSize: name.length > 18 ? Math.round(46 * 18 / name.length) : 46,
    taglineLength: Math.min(260, Math.round(tagline.length * 13.3)),
    trophy: tokens.trophyFill,
    trophyShade,
    brand700: tokens.brand700,
    brand500: tokens.brand500,
    emblem: tokens.emblem,
    ground: tokens.sealGround,
};

const outDir = scratch ? resolve(scratch, 'brand') : resolve(root, 'static/brand');
mkdirSync(outDir, { recursive: true });
const art = [];
for(const file of ['seal.svg', 'seal-simple.svg', 'wordmark.svg', 'banner.svg', 'laurel.svg']) {
    const override = resolve(leagueDir, 'brand', file);
    if(existsSync(override)) {
        copyFileSync(override, resolve(outDir, file));
        art.push(`${file} (league/brand)`);
        continue;
    }
    let svg = readFileSync(resolve(root, 'scripts/brand-templates', file), 'utf8');
    svg = svg.replace(/\{\{(\w+)\}\}/g, (m, k) => {
        if(!(k in values)) throw new Error(`${file}: no value for {{${k}}}`);
        return values[k];
    });
    // A founding year is optional; without one the seal simply has no year line.
    if(!year) svg = svg.replace(/\n\s*<text[^>]*>\s*<\/text>/, '');
    writeFileSync(resolve(outDir, file), svg);
    art.push(file);
}

console.log(`tokens   ${scratch ? scratch + '/_league.scss' : 'src/theme/_league.scss'}  (brand700 ${tokens.brand700}, trophy ${tokens.trophyFill})`);
console.log(`art      ${scratch ? scratch + '/brand/' : 'static/brand/'}: ${art.join(', ')}`);
for(const w of warnings) console.warn(`warning  ${w}`);

if(!process.argv.includes('--no-icons') && !scratch) {
    const res = spawnSync(process.execPath, [resolve(root, 'scripts/render-icons.js')], { stdio: 'inherit' });
    if(res.status !== 0) process.exit(res.status || 1);
}
console.log('Now run `npm run smui-theme-light` to rebuild the stylesheet.');
