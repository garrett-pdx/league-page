#!/usr/bin/env node
/*
Renders the raster favicons and PWA icons from static/brand/seal-simple.svg, and the iOS launch
screens from static/brand/seal.svg and wordmark.svg.

Run after changing the mark:

    node scripts/render-icons.js

Everything it writes is committed, so this is an authoring-time tool -- Vercel never runs it, and
sharp is a devDependency for that reason. It is deliberately NOT wired into `npm run build`: a
build that shells out to a native image library is a build that breaks on someone else's machine,
and the icons change about once a year.

WHY seal-simple.svg AND NOT seal.svg
The full seal's ring text closes up below roughly 96px, and the largest icon here is masked (see
below) so its outer edge is not even guaranteed to survive. The small mark is the app-icon form.

MASKABLE ICONS ARE THE TRAP
The web manifest (src/routes/manifest.json/+server.js) declares the two android-chrome icons as `"purpose": "maskable any"`. Android
crops a maskable icon to a circle, and only the central 80% -- the "safe zone" -- is guaranteed to
survive. Our mark is itself a circle that fills its viewBox, so rendering it edge to edge would put
the gold outer ring exactly where the crop lands and shave it off. Those two sizes are therefore
inset to 72% on an opaque ground. Everything else is not masked and can sit closer to the edge.

LAUNCH SCREENS
iOS shows an apple-touch-startup-image while a home-screen copy of the site starts. Each one must
match a device's exact pixel size, so the sizes are read from the <link> tags in src/app.html: add
a tag there and the next run renders it. The seal and wordmark sit centred on white, the
manifest's background_color, so the launch screen fades into the page. The SVGs' text renders in
whatever fallback font this machine has (no webfonts outside a browser); textLength keeps it to
width.

TRANSPARENCY
Browser tab favicons keep their alpha; the mark is a dark disc and reads on light or dark chrome.
The touch and maskable icons get an opaque white ground instead, because iOS composites a
transparent home-screen icon onto black, which would swallow the seal's black disc entirely.
*/

import sharp from 'sharp';
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(resolve(root, 'static/brand/seal-simple.svg'));
const seal = readFileSync(resolve(root, 'static/brand/seal.svg'));
const wordmark = readFileSync(resolve(root, 'static/brand/wordmark.svg'));

// The SVG carries only a viewBox, so sharp rasterizes it at its 200 unit intrinsic size unless
// told otherwise. Rendering big and downsampling gives clean edges at 16px, where rendering
// directly at target size does not.
const RENDER_DENSITY = 600;

const WHITE = { r: 255, g: 255, b: 255, alpha: 1 };
const CLEAR = { r: 0, g: 0, b: 0, alpha: 0 };

/** Render the mark at `inset` of the frame, on `background`. */
async function icon(size, { inset = 1, background = CLEAR } = {}) {
    const inner = Math.round(size * inset);
    const mark = await sharp(src, { density: RENDER_DENSITY })
        .resize(inner, inner, { fit: 'contain', background: CLEAR })
        .png()
        .toBuffer();

    return sharp({
        create: { width: size, height: size, channels: 4, background },
    })
        .composite([{ input: mark, gravity: 'center' }])
        .png()
        .toBuffer();
}

/** A launch screen: the seal over the wordmark, centred as a group on white. */
async function splash(width, height) {
    const short = Math.min(width, height);
    const sealSize = Math.round(short * 0.5);
    const markWidth = Math.round(sealSize * 1.4);
    const gap = Math.round(short * 0.08);

    const sealPng = await sharp(seal, { density: RENDER_DENSITY })
        .resize(sealSize, sealSize, { fit: 'contain', background: CLEAR })
        .png()
        .toBuffer();
    const markPng = await sharp(wordmark, { density: RENDER_DENSITY })
        .resize({ width: markWidth })
        .png()
        .toBuffer();
    const markHeight = (await sharp(markPng).metadata()).height;

    // Optical centre: the group sits slightly above the middle.
    const top = Math.round((height - (sealSize + gap + markHeight)) * 0.45);
    return sharp({ create: { width, height, channels: 3, background: '#ffffff' } })
        .composite([
            { input: sealPng, top, left: Math.round((width - sealSize) / 2) },
            { input: markPng, top: top + sealSize + gap, left: Math.round((width - markWidth) / 2) },
        ])
        .jpeg({ quality: 82, mozjpeg: true })
        .toBuffer();
}

/** Every launch-screen size src/app.html asks for, as [width, height]. */
function splashSizes() {
    const html = readFileSync(resolve(root, 'src/app.html'), 'utf8');
    const sizes = [...html.matchAll(/pwa\/apple-splash-(\d+)-(\d+)\.jpg/g)].map((m) => [+m[1], +m[2]]);
    return [...new Map(sizes.map((s) => [s.join('x'), s])).values()];
}

/*
Minimal ICO container, written by hand rather than pulling in a second dependency.

An .ico is a 6 byte header, then one 16 byte directory entry per image, then the payloads. Since
Vista the payload may be a PNG rather than a BMP, which is what makes this short. A dimension byte
of 0 means 256.
*/
function buildIco(pngs) {
    const header = Buffer.alloc(6);
    header.writeUInt16LE(0, 0); // reserved
    header.writeUInt16LE(1, 2); // 1 = icon
    header.writeUInt16LE(pngs.length, 4);

    let offset = 6 + pngs.length * 16;
    const entries = [];
    for (const { size, data } of pngs) {
        const e = Buffer.alloc(16);
        e.writeUInt8(size >= 256 ? 0 : size, 0); // width
        e.writeUInt8(size >= 256 ? 0 : size, 1); // height
        e.writeUInt8(0, 2); // palette count
        e.writeUInt8(0, 3); // reserved
        e.writeUInt16LE(1, 4); // colour planes
        e.writeUInt16LE(32, 6); // bits per pixel
        e.writeUInt32LE(data.length, 8);
        e.writeUInt32LE(offset, 12);
        entries.push(e);
        offset += data.length;
    }

    return Buffer.concat([header, ...entries, ...pngs.map((p) => p.data)]);
}

const write = (rel, buf) => {
    const out = resolve(root, rel);
    mkdirSync(dirname(out), { recursive: true });
    writeFileSync(out, buf);
    console.log(`  ${rel}  (${buf.length.toLocaleString()} bytes)`);
};

const run = async () => {
    console.log('Rendering icons from static/brand/seal-simple.svg');

    // Browser tab icons: transparent, near full bleed.
    write('static/favicons/favicon-16x16.png', await icon(16, { inset: 1 }));
    write('static/favicons/favicon-32x32.png', await icon(32, { inset: 1 }));

    // Windows tile: transparent, the tile supplies its own colour via browserconfig.xml.
    write('static/favicons/mstile-150x150.png', await icon(150, { inset: 0.8 }));

    // iOS home screen: opaque, and not circle-masked, so it can sit closer to the edge.
    write('static/favicons/apple-touch-icon.png', await icon(180, { inset: 0.88, background: WHITE }));
    write('static/pwa/apple-icon-180.png', await icon(180, { inset: 0.88, background: WHITE }));

    // Declared maskable in manifest.json: inset to the 80% safe zone, with headroom.
    for (const size of [192, 512]) {
        const buf = await icon(size, { inset: 0.72, background: WHITE });
        write(`static/favicons/android-chrome-${size}x${size}.png`, buf);
        write(`static/pwa/manifest-icon-${size}.png`, buf);
    }

    // favicon.ico carries the classic three sizes for anything too old to read the SVG link.
    const icoSizes = [16, 32, 48];
    const members = [];
    for (const size of icoSizes) {
        members.push({ size, data: await icon(size, { inset: 1 }) });
    }
    write('static/favicons/favicon.ico', buildIco(members));

    // iOS launch screens, one per size src/app.html declares.
    for (const [w, h] of splashSizes()) {
        write(`static/pwa/apple-splash-${w}-${h}.jpg`, await splash(w, h));
    }

    console.log('Done.');
};

run().catch((err) => {
    console.error(err);
    process.exit(1);
});
