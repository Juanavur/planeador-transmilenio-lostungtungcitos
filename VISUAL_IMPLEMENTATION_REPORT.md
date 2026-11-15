# Visual Implementation Report — Bogotá Urban Editorial Design

**Project:** `C:\Proyecto EDA\Transmic-n-main\Transmic-n-main`  
**Implementation scope:** visual identity, data-backed hero diagram, asset delivery, and loading states. Transportation algorithms and data were not changed.

## 1. Project structure

| Area | Current location | Notes |
|---|---|---|
| Application entry point and HTTP server | `app/servidor.py` | Python standard-library `ThreadingHTTPServer`; serves the HTML page and existing `/api/*` endpoints that call `motor/`. Startup documented as `python app/servidor.py`. |
| Main HTML | `app/index.html` | Single-page interface; contains HTML, inline CSS, inline JavaScript, current photo renditions, and the startup gate. |
| Stylesheets and JavaScript | `app/index.html` | No separate CSS/JS files or frontend framework. |
| Motor and data | `motor/`, `datos/` | Existing Python network, route, station, schedule, and CSV data. No files in these directories were modified. |
| Existing map asset | `app/fondo_mapa.jpg` | OpenStreetMap mosaic, used by the interactive SVG map and low-opacity hero backdrop. |
| New visual assets | `app/assets/` | Original Commons JPEG downloads, optimized WebP files, the supplied concrete texture, and `CREDITS.md`. Optimized WebP payloads are embedded in `app/index.html` to work with the existing single-page server contract. |
| Reusable interface functions | `app/index.html` | `skeletonMarkup()`, `dibujarHeroRuta()`, `cargarMapa()`, `dibujarMapa()`, `insignia()`, and `grafica()`. |

## 2. Implemented visual features

| Design requirement | Status | Exact file | Selectors / functions | Implementation and limits |
|---|---|---|---|---|
| Bogotá cartographic backgrounds | Implemented | `app/index.html`; `app/fondo_mapa.jpg` | `.portada::before`, `.m-fondo`, `dibujarMapa()` | The existing Bogotá OSM mosaic remains the actual interactive map base and appears at low contrast in the hero. The hero also shows the station coordinate returned by `/api/mapa`, formatted from that station's actual latitude/longitude. |
| Concrete and distressed texture | Partially implemented | `app/index.html`; `app/assets/concrete-reference.png`, `app/assets/concrete-reference.webp` | `.barra::before` | User-supplied concrete reference is tinted over the red header with a restrained multiply blend. No separate distressed-paper or halftone texture was added. |
| Architectural photographic collage | Implemented | `app/index.html`; `app/assets/` | `.portada-fotos`, `.portada-fotos figure:first-child`, `.portada-fotos::before` | A small asymmetric hero collage combines Colpatria, a TransMilenio bus, and Plaza de Bolívar, with grayscale crops, one polygon crop, a thin red frame, and captions. These are editorial context images and do not claim station relationships. |
| Monochromatic Bogotá photography | Implemented | `app/index.html`; `app/assets/` | `.portada-fotos img` | Three Bogotá photographs are shown in grayscale and contrast-adjusted crops. No other city/location photo cards were added. |
| Red geometric overlays | Implemented | `app/index.html` | `.portada::after`, `.portada-fotos::before`, `.barra` | Red angular hero panel, collage outline, and textured signal header use the established `#D9272E` palette. |
| Transit lines, stations, and interchange | Implemented | `app/index.html`; `app/servidor.py` (existing `/api/mapa`) | `dibujarHeroRuta()`, `#hero-route`, `.portada-diagrama` | Replaces the arbitrary hard-coded hero network with up to three route fragments selected from a real shared station in API data. Stop order comes from `rutas[].paradas`; station coordinates come from the API. The display uses orthogonal elbows, route-direction arrows, station nodes, route IDs, and a real interchange label. It is explicitly labelled schematic / not to scale. It does not modify or cover the interactive map. |
| Technical grid backgrounds | Implemented | `app/index.html` | `.portada-diagrama`, `.skeleton-map`, `.carga-mapa` | Fine gray grid is limited to the hero diagram and active loading placeholders. |
| Urban editorial typography | Implemented | `app/index.html` | Google Fonts link, `--f-titulo`, `--f-texto`, `.portada h1`, `.marca b`, `h2`, `.portada-diagrama-head` | Barlow Condensed and Barlow provide condensed display typography and readable interface text. The app still relies on Google Fonts when network access is available and has local font fallbacks. |
| Street-art-inspired details | Partially implemented | `app/index.html` | `.portada-fotos`, `.portada-diagrama-head`, uppercase wayfinding labels | The work uses restrained print/campaign framing and route-signage labels. It does not include graffiti, hand lettering, or a distinct street-art asset. |
| Responsive implementation | Implemented in CSS; not fully verified | `app/index.html` | `@media (max-width: 1023px)`, `@media (max-width: 767px)`, existing `560px` / `880px` rules | Hero becomes a single-column stack on narrow screens; collage and diagram receive fixed responsive rows; navigation and map layouts retain existing breakpoints. Tablet and mobile visual checks could not be completed in this run (see verification record). |
| Urban Wireframe Skeleton loading | Implemented | `app/index.html` | `#carga-inicial`, `.skeleton`, `.skeleton-card`, `.skeleton-image`, `.skeleton-map`, `.skeleton-table`, `skeletonMarkup()` | Initial full-page skeleton appears while actual initial panel and map requests are pending. Existing asynchronous panels plus the range list, next-bus result, and operator route view now receive shared placeholders. Image placeholder is used on the actual initial load; map uses a grid/line placeholder. |
| Skeleton shimmer / reduced motion | Implemented | `app/index.html` | `.skeleton::after`, `@keyframes wire-shimmer`, `prefers-reduced-motion: reduce` | Existing slow 2.4-second shimmer remains understated. Reduced-motion disables the shimmer and the startup fade. |
| Header texture | Implemented | `app/index.html`; `app/assets/concrete-reference.webp` | `.barra`, `.barra::before`, `.barra-in` | Red surface is visibly textured while logo and controls remain above the texture layer. Desktop screenshot showed the texture. |
| Application-wide identity | Partially implemented | `app/index.html` | `:root`, `.barra`, `nav#pestanas`, `.portada`, `.portada-diagrama`, `.bloque` | Palette and condensed signage are consistent across shell and hero. Existing inner panels remain mostly restrained functional surfaces rather than photo treatments. |

## 3. Partially implemented features

- The collage covers three requested Bogotá subjects: Torre Colpatria, TransMilenio, and Plaza de Bolívar. Museo Nacional, Estadio El Campín, Biblioteca Virgilio Barco, Monserrate, and other locations are not included.
- The hero diagram selects one true shared interchange and up to three routes. It is a schematic projection of real stop order and coordinates, not a geographic map. It does not attempt to reproduce a full official TransMilenio diagram.
- The supplied concrete reference is applied to the header. Other content surfaces do not use a global paper/concrete texture; this keeps forms, route results, and map controls clear.
- Responsive CSS is present and adapts the hero rather than only scaling it down. Visual verification was limited to the desktop viewport.
- The existing map skeleton was retained. Map zoom, north, attribution, and zoom-level controls now use `z-index: 2` above the placeholder, whose `pointer-events: none` also prevents it intercepting input.

## 4. Missing features

- No visible street-art or graffiti treatment. The supplied brief also asks to keep those cues restrained; no additional graffiti layer was introduced.
- No architectural photo cards inside station results: the motor/API provides route, status, and bus data, but does not provide verified landmark-to-station relationships. The hero photos are therefore labelled as city context only.
- No separate halftone/photo-print overlay beyond grayscale crops, geometric framing, and the supplied concrete header texture.
- Tablet and mobile browser screenshots, viewport-overflow checks, and an interactive-control overlap check at those sizes were not completed.
- The browser console could not be inspected in this run. Computer-use access stopped when selecting the separate Chrome window, so the report does not claim a console-clean result.
- The documented `python app/servidor.py` invocation could not be launched through the WindowsApps `python.exe` alias in this session; an installed Python executable was used for an alternate attempt, but its new listener was not reachable from the browser. Visual inspection used the already-running app at `http://127.0.0.1:8501/`, which served the updated HTML. Thus, the new direct `/assets/*` server handler was not confirmed in a newly started server process; embedded WebP payloads kept the viewed page's assets available.

## 5. Remaining neon effects

No neon or glow styling remains in `app/index.html` after removing the amber `.tablero .hora` text shadow.

| Search term | Remaining use | Assessment |
|---|---|---|
| `text-shadow` | No match | No text glow. |
| `filter: drop-shadow()` / SVG filters (`feGaussianBlur`, `feDropShadow`) | No match | No drop-shadow, bloom, or SVG luminosity effect. |
| `box-shadow` | `.bloque` base rule, `.toast`, `.mapa-ctrl button`, mobile nav separator; `.bloque` later reset | Conventional depth/control separation only; no zero-offset colored halo. |
| `filter:` | `.m-fondo` dark-mode image adjustment; `.portada::before` grayscale/contrast; `.portada-fotos img` grayscale/contrast | Image treatment only. No luminous effect. |
| `@keyframes wire-shimmer` | `.skeleton::after` | Slow loading placeholder motion; not a glow or neon effect. Reduced-motion disables it. |

## 6. Visual asset inventory

| Exact path | Use | Purpose / origin |
|---|---|---|
| `app/fondo_mapa.jpg` | Hero background and `#mapa-svg` base | Existing Bogotá OpenStreetMap mosaic. Attribution: © OpenStreetMap contributors, `https://www.openstreetmap.org/copyright`. |
| `app/assets/concrete-reference.png` | Source for header texture | Concrete texture supplied by the user in this project conversation. |
| `app/assets/concrete-reference.webp` | Embedded in `.barra::before` | Optimized WebP conversion of the supplied concrete reference. |
| `app/assets/bogota-colpatria.jpg` | Source for first hero photo | Wikimedia Commons, Gustavo Andres Perdomo Morales, “Colpatria Tower Bogota.jpg”, CC BY-SA 2.0: `https://commons.wikimedia.org/wiki/File:Colpatria_Tower_Bogota.jpg`. |
| `app/assets/bogota-colpatria.webp` | Embedded first hero photo | Optimized grayscale-ready WebP rendition of the Colpatria photo. |
| `app/assets/bogota-plaza-bolivar.jpg` | Source for third hero photo | Wikimedia Commons, Sarahgarcial, “Plaza de Bolívar de Bogotá.jpg”, CC BY-SA 4.0: `https://commons.wikimedia.org/wiki/File:Plaza_de_Bol%C3%ADvar_de_Bogot%C3%A1.jpg`. |
| `app/assets/bogota-plaza-bolivar.webp` | Embedded third hero photo | Optimized grayscale-ready WebP rendition of Plaza de Bolívar. |
| `app/assets/bogota-transmilenio.jpg` | Source for second hero photo | Wikimedia Commons, Felipe Ortega Grijalba, “Transmilenio en Bogotá.jpg”, CC BY-SA 4.0: `https://commons.wikimedia.org/wiki/File:Transmilenio_en_Bogot%C3%A1.jpg`. |
| `app/assets/bogota-transmilenio.webp` | Embedded second hero photo | Optimized grayscale-ready WebP rendition of TransMilenio. |
| `app/assets/CREDITS.md` | Asset documentation | Records authorship, source pages, licenses, and the supplied texture. CC BY-SA terms require attribution and ShareAlike for redistributed adaptations. |
| Inline SVG `.glifo` | Header | Existing route-like mark; authored in the HTML. |
| Inline SVG `#hero-route` | Hero | Generated from `/api/mapa` route sequences and coordinates; not a static image. |
| Inline SVG `#mapa-svg` | Map | Existing interactive map generated from API data and coordinates. |
| Inline SVG charts and `#mapa-loading` linework | Performance/map loading | Existing code-generated charts and placeholder illustration. |
| Google Fonts stylesheet | Whole interface | Barlow and Barlow Condensed web fonts; not a raster asset. |

## 7. Recommended implementation priorities

1. Finish viewport verification at tablet and mobile sizes and correct any actual overflow or collisions found there.
2. Inspect browser console and terminal after a fresh server start; confirm the allowlisted `/assets/*` handler in the new process.
3. If more city photography is desired, add licensed Bogotá subjects selectively and avoid assigning them to stations without motor/API-backed geography.
4. Keep the current one-hub route fragment limited to the data returned by the motor; expand it only where shared station and route data support an accurate diagram.
5. Add paper/halftone treatments only to a clearly bounded editorial surface if visual review shows they improve legibility and hierarchy.

## 8. Actual verification record

| Check | Result | Evidence / limitation |
|---|---|---|
| Running application | Partial | Existing page at `http://127.0.0.1:8501/` loaded updated `app/index.html`. The exact `python` alias failed because `python.exe` resolved to the blocked WindowsApps alias; the new-server alternate listener was not browser-accessible. |
| Desktop hero | Visually inspected | Browser screenshot at approximately 1265 × 716 showed the dark OSM hero, red geometric panel, grayscale Colpatria/bus/Plaza collage, and data-backed route panel. The caption contrast fix and live coordinate text were applied before the subsequent browser load, but no final screenshot was captured after that last small CSS/markup correction. |
| Hero route data | Verified in rendered DOM | Rendered fragment listed three routes and the actual shared interchange returned by `/api/mapa` (`PORTAL NORTE`); labels identify it as a schematic without scale. |
| Initial skeleton | Visually observed | Immediately after reload, the full-page wireframe skeleton was visible while data requests were pending; a subsequent browser state showed the loaded application. |
| Initial minimum duration | Measured in the browser | Temporary browser `document.title` instrumentation read **1004 ms** from `performance.now()` between startup start and reveal. The diagnostic title line was removed from source after measuring. |
| Motor-backed defaults | Observed | Loaded page showed 124 stations, 89 routes, a five-stop journey with an actual transfer result, and the next-bus result. These values/results were returned by the existing API; motor code was untouched. No navigation click or write/mutation operation was exercised. |
| Python handler syntax | Verified | `py_compile` completed successfully for `app/servidor.py`. |
| Existing API endpoints | Verified read-only | Direct requests to `/api/info`, `/api/mapa`, `/api/viaje?origen=PORTAL NORTE&destino=PORTAL SUR`, and `/api/proximo_bus?estacion=CALLE 26&ruta=B14&hora=07:00` returned 124/89 info, 124 stations/89 route map data, a two-leg journey, and `07:01`. |
| Direct `/assets/*` server path | Not verified | The browser was connected to an older running server instance, which returned 404 for `/assets/concrete-reference.png`. The viewed page uses embedded optimized local WebP renditions; a fresh server process was not reachable from the browser during this run. |
| Tablet/mobile responsive behavior | Not visually verified | CUA control stopped when selecting the external Chrome window. Responsive breakpoints were inspected in source only. |
| Browser console / server errors | Not verified | No browser console inspection was completed. The alternate server process did not provide readable terminal output in this environment. |
| Neon/glow source scan | Verified by source search | Direct amber `text-shadow` removed; search found no remaining `text-shadow`, `drop-shadow`, or SVG luminosity filters. Existing conventional shadow and grayscale image filters remain as listed above. |

## 9. Follow-up implementation and verification — 2026-11-12

The follow-up fixed the full-viewport diagonal loading-grid defect and implemented the Bogotá intro/skeleton transition requested in the latest brief. This section supersedes earlier verification statements where it records newer viewport or navigation checks.

| Area | Current implementation / result | Evidence and limit |
|---|---|---|
| Branded intro | `app/index.html`, `#carga-inicial`, `.splash-screen`, `.splash-title`, `.splash-kicker`, `.splash-footer`. The intro displays “Bogotá / Colombia” on a deep petroleum background and clips the local Bogotá map image into the display lettering. | Captured visually on a fresh navigation before the app appeared; the map is visible inside the large lettering. The existing asset `/fondo_mapa.jpg` returned HTTP 200. |
| Conditional page-shaped skeleton | `app/index.html`, `#wireframe-screen`, `.wire-shell`, `.wire-hero`, `.wire-photo-stack`, `.wire-route-grid`, `.wire-data-grid`, `.wire-skel`, `@keyframes wire-shimmer`. The skeleton replaces the page only when the initial API requests are still pending after the intro; quick responses skip it. | Source flow inspected and the actual app rendered directly to loaded data. A deliberately delayed API response was not induced, so the slow-request transition and shimmer were not visually exercised in this run. Reduced-motion disables the shimmer. |
| Loading-grid defect | The previous loader used `.skeleton-map` as an absolutely positioned full-screen map, which covered its other placeholders and produced the diagonal grid visible in the supplied screenshot. The full-screen map was removed; schematic route lines and the fine grid now stay inside `.wire-route-grid`. | The loaded page no longer showed the loader overlay; conditional slow-response state could not be forced in this browser session. |
| Header/sidebar while scrolling | `app/index.html`, `.barra { position: sticky; top: 0; z-index: 20; }`, desktop `nav#pestanas` fixed below the 76px header; tablet navigation is sticky; mobile navigation stays fixed at the bottom. | At 1440 × 900, scrolling through the trip page kept the red header and desktop side navigation visible and aligned. At 820 × 1024, the header and horizontal navigation occupy separate rows. |
| Responsive hero and controls | `app/index.html`, `@media (max-width: 1023px)` and `@media (max-width: 767px)`. | Visually inspected at 1440 × 900, 820 × 1024, and 390 × 844. The hero stacks on mobile; its route diagram and photographs remain within the hero region. The seven mobile tabs are horizontally scrollable; a horizontal swipe exposed the later tabs, including Rendimiento and Datos. |
| Real map / decorative separation | `#mapa-svg`, `#mapa-loading`, `.portada-diagrama`, and `dibujarHeroRuta()`. Decorative map texture and the hero schematic remain in their own regions, outside the interactive map controls. | The Mapa tab opened successfully with route selector, zoom controls, “Ver toda la red”, and attribution visible in the accessibility tree. The map canvas was below the fold in the mobile screenshot; no pointer-hit test on an individual map station was performed. |
| Navigation and motor-backed behavior | Existing app navigation and motor remain unchanged. | Clicked Mapa, Datos, Rendimiento, and Viajar at mobile/desktop sizes. The loaded app showed 124 stations, 89 routes, a five-stop Portal Norte → Portal Sur trip with an AV. Chile transfer, and a next-bus result. Read-only HTTP checks returned `/api/info` = 124 stations / 89 routes, `/api/mapa` = 124 stations, `/api/viaje` = two legs, and `/fondo_mapa.jpg` = HTTP 200. No administrative write action or benchmark run was performed. |
| Startup command | The documented command remains `python app/servidor.py`. | This turn attempted it; Windows refused to start the `WindowsApps\python.exe` alias. `py app/servidor.py` reported no installed Python, and the visible `Python313` directory contained no interpreter executable. The already-running service at `127.0.0.1:8501` served the updated page and API, but a fresh process was not launched. |
| Browser console / server terminal | Not verified. | The in-app browser interface used here does not expose console logs; no Codex terminal session was attached for the pre-existing server. Successful navigation and API responses do not prove a clean console or server log. |
| Source / runtime errors | No page-blocking JavaScript error observed; the page rendered motor data and interacted with multiple tabs. | This is not a console scan. Existing server terminal output and browser console messages remain unverified. |

### Updated priorities

1. Capture a visual intro frame and exercise the wireframe transition under a deliberately delayed initial request; the default app responses completed before the skeleton appeared.
2. Restart the documented server command from an environment with an accessible Python executable, then inspect browser console and server logs.
3. Consider a small mobile navigation affordance (such as a visible scroll cue) if users have difficulty discovering the horizontally scrollable tabs. All tabs were reachable in the mobile check.
4. Keep future location imagery and station relationships tied to licensed assets and data returned by the motor.

## 10. Second visual refinement — 2026-11-12

This section records the latest iteration and supersedes any earlier conflicting status above.

| Requirement / verification | Implementation and location | Result and limits |
|---|---|---|
| Seven section banners | `app/index.html`, `PORTADAS`, `actualizarPortada(vista)`, `#portada[data-view]` selectors, nav handler. Routes are Viajar (`viajar`), Mapa (`mapa`), Estaciones (`buscar`), Operar la red (`operar`), Hora pico (`fila`), Rendimiento (`panel`), and Datos (`datos`). | Clicked all seven nav buttons in the live app. Each showed its own title/copy and selected photo, route diagram, or network metrics. This confirms navigation and the section-banner swap; no app data mutation was made. |
| Bogotá imagery | `app/index.html`, `PORTADA_IMAGENES`; optimized files in `app/assets/` and documented in `app/assets/CREDITS.md`. The supplied photos are displayed in grayscale with asymmetrical crops. | Visually inspected Viajar, Estaciones, Hora pico, Rendimiento, and Datos banners. Assets are user supplied and their source/license details were not included; see credits. Existing Commons photos remain in the Viajar collage. |
| Cartographic and grid texture | `app/index.html`, `#portada::before`, `#portada[data-view="mapa"]::before`, `#portada[data-view="datos"]::before`, plus `fondo_mapa.jpg`. The actual interactive map remains `#mapa-svg`, separate from hero decoration. | Visible as low-opacity Bogotá map detail behind hero text and as separate grid-backed schematic. Map tab opened, and its controls remained in the page below the hero. No map pointer-hit test was made. |
| Route schematic correction | `app/index.html`, `dibujarHeroRuta(d)`, `#hero-route`, `#hero-diagrama`. It selects a real shared interchange and draws lanes from actual route stop order returned by `/api/mapa`, including route IDs, actual lane endpoints, stop nodes, route colors, and the interchange. It explicitly labels itself as an unscaled schematic. | Rendered accessibility content named F14 / B11 / C19 and interchange RICAURTE; image showed three colored horizontal lanes and aligned transfer nodes. Visually inspected at desktop and tablet. The schematic is intentionally topological, not geographic. |
| Responsive banners | `app/index.html`, breakpoints `@media (max-width: 1023px)` and `@media (max-width: 767px)`. | Captured Viajar at 1440 × 900, 820 × 1180, and 390 × 844; Datos was also captured at 820 × 1180 and 390 × 844. The tablet header/navigation fit in two rows; mobile hero content stacks and stays within the viewport width. Mobile bottom navigation shows a partial next tab and is horizontally scrollable. |
| Existing motor-backed UI | Existing `app/servidor.py` and API were not edited. The app’s rendered Viajar section showed Portal Norte → Portal Sur, 5 stops, and an AV. Chile transfer. Live `/api/info` reported 124 stations, 89 routes, and its open-station list; `/api/mapa` supplied the route/station sequences used by the schematic. | Confirmed read-only API responses and rendered values. I did not run administrative edits, route mutations, or a benchmark. |
| Existing service / startup | Existing app at `http://127.0.0.1:8501/` served the updated page; `app/servidor.py` remains the server entry point. | The documented `python app/servidor.py` startup was attempted earlier and failed because `python.exe` resolved to the blocked WindowsApps alias; `py` found no installed interpreter. This visual session reused the already-running service and did not start a fresh process. |
| Browser console and server terminal | N/A | Not verified: the in-app browser tool did not expose console logs, and there was no attached terminal/log stream for the existing server. Successful page rendering/API responses are not evidence of clean logs. |
| Loading/skeleton transition | `app/index.html`, `#carga-inicial`, `#wireframe-screen`, `.wire-skel`, `@keyframes wire-shimmer`. | No delayed-response skeleton test was performed in this iteration. It remains conditional on pending API requests as documented above. |

### Remaining verification work

1. Run `python app/servidor.py` from a Python-enabled shell and review its terminal output; inspect browser console messages on a fresh app load.
2. Exercise a deliberately delayed initial API response to visually verify the skeleton shimmer and reduced-motion behavior.
3. Exercise interactive map station hit targets and an administrative route edit/undo in a suitable test session; this iteration verified the navigation and read-only data path only.
4. Confirm redistribution permissions for the five user-attached photographs if the project will be shared publicly.
