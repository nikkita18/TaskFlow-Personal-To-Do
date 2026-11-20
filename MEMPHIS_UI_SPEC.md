# Loopa / TaskFlow: Memphis Postmodern Landing Page & UI Specification

A design and architecture specification for integrating a Memphis / Postmodern animated landing page and design system into the recruitment project.

---

## 1. Visual Language & Memphis Design System

### A. Color Palette (Solid Fills Only — No Gradients, No Soft Shadows)
* **Canvas Ground:** Warm Cream `#f5efe2`
* **Ink / Outlines / Text:** Near-black `#17140d`
* **Card Surface:** Pure White `#ffffff`
* **Primary Coral:** `#ff5b57` (CTAs, highlight bars, chart bars, icon chips)
* **Teal:** `#12b3a4` (Nav CTA, marker highlights, status chips, checks)
* **Mustard:** `#ffc531` (Logo tile, marker highlights, confetti, dots)
* **Violet:** `#6b5be6` (Eyebrow pills, icon chips, plus-sign confetti)
* **Sky Blue:** `#3aa0ff` (Zigzag confetti, chart bars)
* **Logo Band Ground:** Deep Charcoal/Black `#17140d` with Cream `#f5efe2` typography

### B. Outlines & Tactile Hard Shadows
* **Outlines:** `3px solid #17140d` on all buttons, cards, modal dialogs, and major shapes.
* **Hard Offset Shadows:** Flat, crisp shadows with **zero blur**:
  - Hero Elements & Main Cards: `box-shadow: 8px 8px 0 #17140d;`
  - Smaller Elements (Pills, Chips, Buttons): `box-shadow: 5px 5px 0 #17140d;`
  - Active / Hover State: `transform: translate(2px, 2px); box-shadow: 3px 3px 0 #17140d;` (tactile mechanical press-in feel).

### C. Typography System
* **Display / Headings / Wordmark:** `Bricolage Grotesque` (700 / 800) with tight tracking (`-0.03em`).
* **Body / Labels / UI:** `DM Sans` (400 / 500 / 700).
* **Aggressive Scale Ratio:** 76px hero display down to 14–16px UI labels.

---

## 2. Animated Geometric Confetti (Pure CSS Keyframes — NO JS)

9 decorative geometric confetti shapes scattered across the hero canvas as self-contained inline SVGs with `3px-7px` black strokes. All animations run on pure CSS keyframes with `pointer-events: none` and `overflow-x: hidden` on the container so they never trigger scrollbars or block interactions:

1. **Coral Triangle (`#ff5b57`):** Gentle drift (`translateY` + rotate, 18s ease-in-out infinite alternate).
2. **Teal Quarter-Arc (`#12b3a4`):** Bobbing & rocking (12s ease-in-out infinite).
3. **Mustard Dotted Circle (`#ffc531`):** Slow 360-degree rotation (26s linear infinite).
4. **Violet Plus-Sign (`#6b5be6`):** Continuous spinning (16s linear infinite).
5. **Black Squiggle 'Bacteria' Line (`#17140d`):** Gentle pendulum sway around top-center (8s ease-in-out infinite).
6. **Mustard Half-Circle (`#ffc531`):** Floating bob (`translateY(-14px)`, 10s ease-in-out infinite).
7. **Small Solid Teal Dot (`#12b3a4`):** Soft pulse / scale (`scale(1.15)`, 6s ease-in-out infinite).
8. **Sky-Blue Zigzag (`#3aa0ff`):** Horizontal wave & bob (14s ease-in-out infinite).
9. **Coral Striped / Terrazzo Circle (`#ff5b57`):** Counter-clockwise spin (22s linear infinite).

---

## 3. Page Structure & Components Breakdown

### 1. Minimal Top Navigation
* **Left:** 
  - 42px Mustard `#ffc531` rounded-square logo tile with 3px black outline and 5px hard shadow, holding a black squiggle glyph.
  - "Loopa" wordmark in `Bricolage Grotesque 800` (26px).
* **Center:**
  - 4 DM Sans 500 links: *Product*, *Features*, *Pricing*, *Docs* (turning coral on hover with smooth transition).
* **Right:**
  - "Sign In" link / button for existing users.
  - Teal `#12b3a4` pill CTA: **"Start free"**, white bold text, 3px black outline, 5px hard offset shadow, pressing in on hover.
  - Theme toggle button (Dark / Light Memphis variation).

### 2. Asymmetric Hero Section (~1.05fr Copy / 0.95fr Product Card)
* **Left Column:**
  - **Eyebrow Pill:** Violet `#6b5be6` pill (uppercase 14px bold white text, mustard dot indicator, 3px outline, 5px hard shadow): `NEW • Team plans just dropped`.
  - **Main Display Headline (76px, line-height 0.98, Bricolage Grotesque 800):**
    > Ship work that <span class="marker-mustard">actually</span> gets <span class="marker-teal">done.</span>
  - **Marker-Highlight Underlines:** Flat mustard `#ffc531` and teal `#12b3a4` rectangular highlighter bars slightly rotated (`-1.5deg`), placed behind the words via pseudo-elements (`z-index: -1`).
  - **Lead Paragraph (~19px DM Sans):** Charcoal copy explaining effortless personal & team task management without endless meetings.
  - **Dual Tactile CTAs:**
    - Primary: Coral `#ff5b57` pill **"Start free →"** (white text, 3px outline, 8px hard shadow).
    - Secondary: White ghost pill **"Watch demo"** / **"Sign In"** (3px outline, 8px hard shadow).
  - **Social Proof / Trust Row:**
    - Four overlapping circular avatars (Coral, Teal, Violet, Mustard) with thick black outlines and initials.
    - Two-line proof copy: *"12,000+ teams plan their week in Loopa. No credit card, no meetings about meetings."*

* **Right Column: Tilted (-2deg) Product Dashboard Mockup:**
  - White container with `22px` rounded corners, `3px` black outline, and `8px` hard offset shadow.
  - **Browser Chrome Top Bar:** 3 outlined traffic-light dots (coral, mustard, teal) + a cream sub-bar with `"This week • Design squad"`.
  - **Body Content:**
    - Row with Bricolage title *"Sprint velocity"* + Teal `"+38%"` pill badge.
    - Outlined Chart Panel holding **6 vertical bars** (Mustard 44%, Coral 62%, Violet 52%, Teal 82%, Sky 70%, Coral 96%) with rounded tops and 2px black outlines.
    - Checklist with 3 outlined rows: 2 completed with teal checkmarks (*"Ship the new onboarding flow"*, *"Review Q3 roadmap draft"*) and 1 open item (*"Sync with the growth pod"*).

### 3. Full-Bleed Black Logo Strip
* Viewport-wide solid black `#17140d` banner with 3px black border top and bottom.
* Left: Mustard `#ffc531` tracked uppercase badge: `TRUSTED BY TEAMS AT`.
* Right: 5 Cream `#f5efe2` wordmarks in Bricolage 700 at 85% opacity (`Northwind`, `Fig&Co`, `Superbloom`, `Kettle`, `Halcyon`).

### 4. Features Section: "Why Teams Switch"
* Centered header with violet eyebrow pill: `WHY TEAMS SWITCH`.
* 2-line display heading (46px Bricolage Grotesque 800):
  > Boring tools kill momentum.  
  > Loopa keeps it loud.
* **Three-Column Card Row:**
  - **Card 1 (Coral):** 62px Coral icon-chip (glyph: Lightning / Flow), Bricolage title *"Plans that flow"*, copy *"Drop ideas into quick lists, organize by priority, and keep moving."*, soft coral circle accent bleeding off the bottom-right corner.
  - **Card 2 (Teal):** 62px Teal icon-chip (glyph: Bar Chart), Bricolage title *"Progress you can see"*, copy *"Visual overdue alerts, velocity tracking, and crystal-clear task states."*, soft teal circle accent.
  - **Card 3 (Violet):** 62px Violet icon-chip (glyph: Shield / Key), Bricolage title *"Built for the crew"*, copy *"Salted PBKDF2 crypto, independent tokens, and private task isolation."*, soft violet circle accent.

---

## 4. Seamless Integration with Problem C2 Task Tracker

1. **Dual-Mode / Interactive Application Flow:**
   - When **logged out**: The page displays this Memphis landing page with the hero, confetti, tilted dashboard mockup, logo strip, and feature cards.
   - Clicking **"Start free"** opens the Memphis-styled **"Create Account"** modal or flips to the auth panel.
   - Clicking **"Sign In"** or **"Watch demo"** opens the **"Sign In"** modal (with pre-filled demo account button for fast live evaluation).
2. **When Logged In:**
   - Nav bar shows user badge, **"Go to Tasks"** button, and Logout.
   - The task management dashboard (filters, search, overdue tags, add task modal) adopts the exact same Memphis aesthetic: warm cream background, 3px solid black outlines, 5px/8px hard offset shadows, and bright Memphis color chips!
3. **100% Track C Compliance:**
   - Pure HTML5, CSS3, and vanilla JS.
   - Zero React/Vue, zero Bootstrap/Tailwind.
   - Responsive down to 360px mobile viewports (stacks gracefully to 1 column, touch targets >= 44px).
   - Preserves all 12 backend unit tests without modifying any API contract.

---

## 5. Next Steps for Implementation
1. Load Google Fonts: `Bricolage Grotesque:wght@700;800` and `DM Sans:wght@400;500;700`.
2. Expand `style.css` with the Memphis design tokens, confetti keyframe animations, hard offset shadows, and marker highlights.
3. Update `templates/index.html` to integrate the Memphis landing hero, confetti SVGs, logo band, feature grid, and unified task tracker views.
4. Enhance `static/js/app.js` to handle smooth modal transitions between the landing page and the authenticated task dashboard.
