# Set up the global event integration

## Dependencies

- A separately installed [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view) checkout with its supported embed/message API.
- Python 3.10+ with standard-library modules. Node.js is needed only for the included JavaScript checks.
- Public HTTPS access to GDACS and the BBC World/Business RSS feeds; optional existing public-headline caches.
- A hardware-accelerated browser/OBS browser source for rendering the globe.

Follow the upstream project's current installation/security instructions. The historical lab used upstream revision `7be5937fc3e3b10cdfa8d3f833536167268768ad`; the integration is not a guarantee of compatibility with every later revision. Optional upstream provider keys remain outside this repository.

## Install the panel and collector

Choose an application root. `GEV_ROOT` defaults to `/opt/gods-eye-view`. Place these files into the checkout's served `public/` directory:

```text
thm-global-panel.html
thm-global-panel.js
```

Run `update-global-events.py` with a user allowed to write `GEV_ROOT/public/thm-events.json`. It uses the upstream data-center reference dataset if present; a missing dataset means no proximity analysis, not proof of no nearby infrastructure.

```bash
GEV_ROOT=/opt/gods-eye-view python3 update-global-events.py
```

Start with an alert-only view. Open `/thm-global-panel.html?standalone=1&embed=1` on the globe app's own origin. Verify actual WebGL rendering and attribution before adding it to OBS. In the recorded dashboard, parent controls prepared the next event when its rotation was activated; a standalone view selects the initial available event.

If embedding the panel under another origin, add `parentOrigin` with that exact, URL-encoded origin. For example, `http://192.0.2.10:3101` is a **documentation address**, not a reachable lab service. The default trusts only the panel's own origin. Also configure the upstream application's frame policy to allow only the intended origin. Do not replace origin checks with `*`.

## Optional headline context

The context builder reads public-headline caches if available and independently fetches BBC World/Business RSS. The supplied `freshness.py` helper is included so it does not depend on an unpublished local module.

1. Create an application-owned output directory and set `THM_DASHBOARD_ROOT` to it. Put `context/places.json` there as `global-places.json`.
2. Optionally set `THM_NEWS_CACHE` to a directory holding the existing `news.json` / `intel.json` public-headline caches. Missing caches are skipped.
3. Run `python3 context/build_context.py`. It writes `global-context.json` atomically.
4. Serve that JSON through an existing, source-restricted web server. Set `THM_CONTEXT_URL` on the globe collector to the JSON's actual HTTP(S) URL. The collector treats an absent/unavailable context endpoint as optional; it does not need an administrator token.
5. Schedule the context builder and globe collector every five minutes with your existing service/timer mechanism. Each invocation should finish before another starts. Enable the timer at boot and verify both last/next runs. Restrict write access to application-owned directories.

The recorded deployment used an existing read-only dashboard service and a source-specific firewall rule. That private routing/deployment helper is intentionally not shipped as a public one-command installer. Publish only the event JSON, never dashboard credentials or management proxy routes.

## Freshness and geographic limits

Context rejects unsupported/ambiguous geography, irrelevant stories, future dates, failed-source records and reports older than seven days. It uses a separate source fetch-age check; rewriting JSON does not renew an old source fetch. Event output retains source times and collection status. The panel polls once a minute and marks unavailable/cached views. Inspect the original report before acting.

GDACS alert descriptions can represent forecast or peak conditions. Reference data-center counts are point distances within 200 km, not hazard-footprint intersection or verified outages. Rule-based business relevance is a watchlist, not article analysis or a prediction.

## Local checks

From this directory:

```bash
python3 context/test_context.py
node context/test_panel.cjs
node context/test_startup.cjs
python3 -m py_compile update-global-events.py context/build_context.py context/freshness.py
```

The first check covers relevance, explicit geography and stale/unrelated exclusion. The JavaScript checks cover region scrolling and text-before-globe-readiness. These tests use synthetic events and make no live API calls.

## Recovery practice

Keep a known-good copy of panel assets/configuration and any application/VM backups. In a disposable preview, block an upstream feed, verify that stale/unavailable state is explicit, then restore access. Separately test a globe that never sends its ready/view-applied message: report text must remain visible and the timeout must not hang scene control. Do not inject failures into a live broadcast.

## Required reading

- [God's Eye View](https://github.com/bilawalsidhu/gods-eye-view): embed protocol and upstream deployment requirements.
- [GDACS](https://www.gdacs.org/): alert reporting and original event details.
- [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/): reference geometry and its public-domain terms.
- [OBS browser source](https://github.com/obsproject/obs-browser): browser rendering and lifecycle.
