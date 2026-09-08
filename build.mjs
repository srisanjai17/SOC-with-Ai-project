/**
 * SOC with AI — Production Build Script
 *
 * Concatenates vanilla IIFE JS modules in dependency order,
 * minifies JS + CSS with esbuild, copies static assets.
 *
 * Usage:
 *   npm run build          # one-time build
 *   npm run build:watch    # rebuild on file change
 */
import { readFileSync, writeFileSync, mkdirSync, cpSync, readdirSync, unlinkSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── Configuration ──────────────────────────────────────────────────
const JS_ENTRY_ORDER = [
  'static/modules/core.js',
  'static/modules/watchdog.js',
  'static/modules/ui.js',
  'static/dashboard.js',
  'static/lazy-load.js',
];

const CSS_INPUT = 'static/dashboard.css';

const EXTRA_FILES = [
  { src: 'static/sw.js', dest: 'dist/sw.js' },
  { src: 'static/manifest.json', dest: 'dist/manifest.json' },
  { src: 'static/og-image.png', dest: 'dist/static/og-image.png' },
];

const HTML_FILES = [
  'templates/dashboard.html',
];
const HTML_FRAGMENTS_DIR = 'templates/fragments';
// ───────────────────────────────────────────────────────────────────

function build() {
  const start = Date.now();
  console.log('🔨 Building SOC with AI for production...\n');

  // 1. Ensure output directories exist
  mkdirSync('dist/assets', { recursive: true });
  mkdirSync('dist/static', { recursive: true });
  mkdirSync('dist/templates/fragments', { recursive: true });

  // 2. Concatenate JS modules in dependency order
  let combinedJS = '';
  for (const file of JS_ENTRY_ORDER) {
    const content = readFileSync(resolve(__dirname, file), 'utf-8');
    combinedJS += `\n/* === ${file} === */\n${content}\n`;
  }

  // Write temp source for esbuild
  const tmpSrc = resolve(__dirname, 'dist/_tmp_src.js');
  writeFileSync(tmpSrc, combinedJS);

  // 3. Bundle + minify JS with esbuild
  const jsOut = resolve(__dirname, 'dist/assets/bundle.min.js');
  try {
    execSync(
      `npx esbuild "${tmpSrc}" --bundle --minify --target=es2020 --format=iife --outfile="${jsOut}"`,
      { stdio: 'inherit', cwd: __dirname }
    );
  } catch (e) {
    // esbuild might not be installed yet — install and retry
    console.log('📦 Installing esbuild...');
    execSync('npm install --no-save esbuild', { stdio: 'inherit', cwd: __dirname });
    execSync(
      `npx esbuild "${tmpSrc}" --bundle --minify --target=es2020 --format=iife --outfile="${jsOut}"`,
      { stdio: 'inherit', cwd: __dirname }
    );
  }

  // Clean temp file
  try { unlinkSync(tmpSrc); } catch {}

  // 4. Minify CSS
  const cssOut = resolve(__dirname, 'dist/assets/dashboard.min.css');
  execSync(
    `npx esbuild "${resolve(__dirname, CSS_INPUT)}" --minify --outfile="${cssOut}"`,
    { stdio: 'inherit', cwd: __dirname }
  );

  // 5. Copy extra static files
  for (const { src, dest } of EXTRA_FILES) {
    const srcPath = resolve(__dirname, src);
    const destPath = resolve(__dirname, dest);
    if (existsSync(srcPath)) {
      cpSync(srcPath, destPath);
    }
  }

  // 6. Copy HTML templates (unchanged — server serves them)
  for (const htmlFile of HTML_FILES) {
    cpSync(resolve(__dirname, htmlFile), resolve(__dirname, `dist/${htmlFile}`));
  }

  // Copy fragment templates
  const fragDir = resolve(__dirname, HTML_FRAGMENTS_DIR);
  if (existsSync(fragDir)) {
    for (const f of readdirSync(fragDir)) {
      cpSync(resolve(fragDir, f), resolve(__dirname, `dist/templates/fragments/${f}`));
    }
  }

  // 7. Report sizes
  const origSize = JS_ENTRY_ORDER.reduce((sum, f) => {
    return sum + readFileSync(resolve(__dirname, f), 'utf-8').length;
  }, 0);
  const cssOrig = readFileSync(resolve(__dirname, CSS_INPUT), 'utf-8').length;
  const minJS = readFileSync(jsOut, 'utf-8').length;
  const minCSS = readFileSync(cssOut, 'utf-8').length;
  const jsRatio = ((1 - minJS / origSize) * 100).toFixed(1);
  const cssRatio = ((1 - minCSS / cssOrig) * 100).toFixed(1);

  const elapsed = ((Date.now() - start) / 1000).toFixed(1);

  console.log('\n✅ Build complete in ' + elapsed + 's\n');
  console.log('   JS Bundle:');
  console.log(`     ${JS_ENTRY_ORDER.length} modules → dist/assets/bundle.min.js`);
  console.log(`     ${(origSize / 1024).toFixed(1)}KB → ${(minJS / 1024).toFixed(1)}KB (-${jsRatio}%)\n`);
  console.log('   CSS Bundle:');
  console.log(`     ${CSS_INPUT} → dist/assets/dashboard.min.css`);
  console.log(`     ${(cssOrig / 1024).toFixed(1)}KB → ${(minCSS / 1024).toFixed(1)}KB (-${cssRatio}%)\n`);
  console.log('   Other files copied to dist/');
}

build();
