/**
 * nexus/file_watcher.js
 * Watches nexus/knowledge_base/ for .md file changes and triggers
 * re-embedding via the NEXUS HTTP server (POST /api/nodes/reembed).
 *
 * Requirements:
 *   npm install chokidar node-fetch   (or: npm install in this directory)
 *
 * Usage:
 *   node nexus/file_watcher.js
 *   # or with a custom KB path:
 *   NEXUS_KB_PATH=./nexus/knowledge_base node nexus/file_watcher.js
 *
 * The watcher debounces rapid saves (e.g. editor auto-save storms) with a
 * 500 ms delay so a single edit triggers only one re-embed call.
 */

"use strict";

const path = require("path");
const chokidar = require("chokidar");

// node-fetch v3 is ESM-only; use dynamic import or install v2 for CommonJS.
// We detect which version is available at runtime.
let fetchFn;
async function getFetch() {
  if (fetchFn) return fetchFn;
  // Node 18+ ships global fetch
  if (typeof globalThis.fetch === "function") {
    fetchFn = globalThis.fetch;
    return fetchFn;
  }
  try {
    const nf = await import("node-fetch");
    fetchFn = nf.default;
  } catch {
    // node-fetch not installed; try global fetch one more time
    if (typeof fetch === "function") {
      fetchFn = fetch;
    } else {
      throw new Error(
        "No fetch available. Run: npm install node-fetch  (or use Node 18+)"
      );
    }
  }
  return fetchFn;
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const KB_PATH = path.resolve(
  process.env.NEXUS_KB_PATH || path.join(__dirname, "knowledge_base")
);
const NEXUS_URL = process.env.NEXUS_URL || "http://127.0.0.1:7200";
const REEMBED_ENDPOINT = `${NEXUS_URL}/api/nodes/reembed`;
const DEBOUNCE_MS = parseInt(process.env.WATCHER_DEBOUNCE_MS || "500", 10);

console.log(`[nexus/watcher] watching: ${KB_PATH}`);
console.log(`[nexus/watcher] nexus server: ${NEXUS_URL}`);

// ---------------------------------------------------------------------------
// Debounce map  {filePath → timeoutHandle}
// ---------------------------------------------------------------------------

const debounceMap = new Map();

function scheduleReembed(filePath) {
  if (debounceMap.has(filePath)) {
    clearTimeout(debounceMap.get(filePath));
  }
  const handle = setTimeout(() => {
    debounceMap.delete(filePath);
    triggerReembed(filePath);
  }, DEBOUNCE_MS);
  debounceMap.set(filePath, handle);
}

async function triggerReembed(filePath) {
  const fetch = await getFetch();
  try {
    const resp = await fetch(REEMBED_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: filePath }),
    });

    if (resp.ok) {
      const data = await resp.json();
      console.log(
        `[nexus/watcher] re-embedded: ${data.title || filePath}`
      );
    } else {
      const text = await resp.text();
      console.warn(
        `[nexus/watcher] reembed failed (${resp.status}): ${text} — ${filePath}`
      );
    }
  } catch (err) {
    // Server may be starting up; log and continue — next change will retry.
    console.warn(`[nexus/watcher] reembed error: ${err.message} — ${filePath}`);
  }
}

// ---------------------------------------------------------------------------
// Chokidar watcher
// ---------------------------------------------------------------------------

const watcher = chokidar.watch(KB_PATH, {
  persistent: true,
  ignoreInitial: true,   // don't flood on startup
  awaitWriteFinish: {    // wait until the file stops growing before firing
    stabilityThreshold: 200,
    pollInterval: 100,
  },
  ignored: /(^|[/\\])\../, // ignore dotfiles
});

watcher
  .on("add", (filePath) => {
    if (filePath.endsWith(".md")) {
      console.log(`[nexus/watcher] new node: ${filePath}`);
      scheduleReembed(filePath);
    }
  })
  .on("change", (filePath) => {
    if (filePath.endsWith(".md")) {
      console.log(`[nexus/watcher] changed: ${filePath}`);
      scheduleReembed(filePath);
    }
  })
  .on("unlink", (filePath) => {
    // Deleted files don't need re-embedding; the server DELETE route
    // handles vector cleanup when invoked explicitly.
    if (filePath.endsWith(".md")) {
      console.log(`[nexus/watcher] deleted (no action): ${filePath}`);
    }
  })
  .on("error", (err) => {
    console.error(`[nexus/watcher] watcher error: ${err}`);
  })
  .on("ready", () => {
    console.log("[nexus/watcher] ready — watching for .md changes");
  });

// Graceful shutdown
process.on("SIGINT", async () => {
  console.log("[nexus/watcher] shutting down");
  await watcher.close();
  process.exit(0);
});
