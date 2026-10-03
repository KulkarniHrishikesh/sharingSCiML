# Case 6 of 9 (Turbomachinery Breadth Program): PPTC Cavitating Propeller

**Status: NOT STARTED — this session did Phase A (literature/data verification) and
Phase A.5 (dictionary templates) only. No meshing tool or solver was run.**
Per explicit instruction, this session did **not** run `blockMesh`, `snappyHexMesh`,
`checkMesh`, `topoSet`, `decomposePar`, or any OpenFOAM solver. Everything below is either
(a) verified by downloading/reading the primary source directly, (b) confirmed by inspecting
this machine's actual OpenFOAM v2412 installation (source tree, compiled binaries, shipped
tutorials), or (c) explicitly flagged as an assumption/approximation not yet checked.

This is the first case in this program to introduce **two-phase cavitation modeling
(Schnerr–Sauer)** — none of the 8 cases built so far (ERCOFTAC pump, axialTurbine, FDA blood
pump, Timisoara, Francis-99, NREL Phase VI, VKI LS89, NASA Rotor 37) use a phase-change model;
all are single-phase incompressible or compressible RANS. See §4 for what that actually
requires in this OpenFOAM v2412 install.

---

## 1. Rig Description

**Potsdam Propeller Test Case (PPTC)**, SVA Potsdam GmbH (Schiffbau-Versuchsanstalt Potsdam),
model propeller **VP1304** — a 5-bladed, right-handed, **controllable-pitch** propeller
purpose-designed by SVA in 1998 to generate a strong tip vortex, extensively tested for the
SMP'11 (2011) and SMP'15 (2015) international propeller-workshop series.

**Main geometric particulars** (SVA report 3752 Table 1 / 3753 Table 1, cross-checked against
the PFF parametric blade file — see §3.1 for one real inconsistency found between SVA's own
documents):

| Quantity | Symbol | Value |
|---|---|---|
| Diameter | D | 0.250 m |
| Hub diameter ratio | dh/D | 0.300 |
| Pitch ratio at r/R=0.7 | P0.7/D | 1.635 |
| Mean pitch ratio | Pmean/D | 1.5675 |
| Expanded area ratio | AE/A0 | 0.77896 |
| Chord length at r/R=0.7 | c0.7 | 0.10417 m |
| Skew | θeff | 18.8° |
| Number of blades | Z | 5 |
| Sense of rotation | — | right-handed |
| Blade-hub interface | — | 0.3 mm gap (it's a CPP — controllable pitch), sharp trailing edge on upper radii |
| Material (real model) | — | cold-rolled brass, CNC/HSC-milled |

Two **different physical rig configurations** were used, each with its own geometry file
(different hub-cap shape, since the caps differ between pull/push dynamometer arrangements —
see §3.1):
1. **Open-water tests** (SVA report 3752): dynamometer H39 (Kempf & Remmers) behind the
   propeller, towing tank, ship coordinate system (SCS, x upstream, right-handed).
2. **Velocity-field (LDV) + cavitation tests** (SVA reports 3753/3754): cavitation tunnel K15A
   (Kempf & Remmers small test section, 600×600 mm), dynamometer J25 *in front of* the
   propeller, shaft inclination 0°, propeller coordinate system (PCS, x downstream).

## 2. Operating Conditions / Cavitation Numbers Actually Tested

All values below are extracted directly from the primary SVA reports (pdftotext'd and
grepped this session — not taken from any secondary/survey summary).

### 2.1 Open water (towing tank, SVA report 3752)
- Two shaft speeds: **n = 10 s⁻¹ and n = 15 s⁻¹**, atmospheric pressure (no cavitation),
  swept across advance coefficient J. Purpose: assess Reynolds-number sensitivity of KT/10KQ.

### 2.2 Open water in the cavitation tunnel (SVA report 3753 §7.1)
- Three shaft speeds, **n = 15, 20, 25 s⁻¹**, run at over-pressure specifically to *suppress*
  cavitation (so this gives a clean non-cavitating KT/KQ/η0 baseline at the same n used for
  the cavitating tests below).

### 2.3 Cavitation bucket (SVA report 3753 §7.2, n = 25 s⁻¹, two blades tested)
Cavitation buckets (inception/desinence boundaries vs. σn) measured for tip-vortex,
suction-side, and pressure-side cavitation independently, for blades 1 and 3.

### 2.4 Three official cavitation working points (SVA report 3753 Table 2) — **primary
validation targets**

| Test case | J | KT (non-cav.) | σn | n [s⁻¹] |
|---|---|---|---|---|
| 2.3.1 | 1.019 | 0.387 | **2.024** | 24.987 |
| 2.3.2 | 1.269 | 0.245 | **1.424** | 24.986 |
| 2.3.3 | 1.408 | 0.167 | **2.000** | 25.014 |

Each has photo/video documentation of the actual cavitation pattern (tip vortex,
suction-side sheet, pressure-side).

### 2.5 Cavitation-number sweeps at fixed advance ratio (SVA report 3753 §4, photos+videos)
At three fixed Jc, σnc was varied and cavitation photographed/filmed at each point:
- **Jc = 0.9945**: σnc = 5.076, 4.578, 4.077, 3.075, 2.074
- **Jc = 1.2535**: σnc = 3.062, 2.560, 2.259, 2.059, 1.456
- **Jc = 1.4000**: σnc = 4.032, 3.032, 2.022 (and further points, see report3753.txt)

### 2.6 Measured environmental data (used directly in `case/constant/transportProperties`)
From the actual test-block headers in report 3753 (not generic defaults): water temperature
tW ≈ 21.9–23.6 °C, density ρ ≈ 997.3–997.7 kg/m³, kinematic viscosity ν ≈ 9.25–9.58×10⁻⁷ m²/s,
measured vapour pressure pV ≈ 2.687–2.944 kPa, ambient pressure pA ≈ 98.2–98.4 kPa, dissolved
air content 46.7–48.7%. **Recommended primary build target: test case 2.3.1** (J=1.019,
σn=2.024, n=24.987 s⁻¹) — the design-point condition with the mildest cavitation extent, a
sensible first rung before 2.3.2/2.3.3's heavier loading.

### 2.7 LDV velocity-field measurement planes (SVA report 3754)
7 axial planes downstream of the propeller disk: **x/D = −0.2, 0.094, 0.10, 0.11, 0.13, 0.16,
0.20** — each with axial-only, then full 3-component, then a "detailed" 3D velocity field.
Useful as a non-cavitating CFD validation target independent of the cavitation-pattern
comparison.

### 2.8 Not covered by this build (flagged for later)
The **oblique/inclined-shaft** PPTC variant (SMP'15, "PPTC 2015" — the exact configuration in
Gaggero & Villa 2018, §4.3 below) is a distinct, later SVA test campaign with a non-zero shaft
inclination; this README's baseline plan targets the simpler zero-inclination SMP'11 case
first, with oblique flow as a natural Phase-2 extension once the baseline runs.

## 3. Data Openness — Verified Live, Not Assumed

The portfolio's "open — SVA Potsdam explicitly publishes geometry, reports, and videos for
university/research use" claim was **checked live this session and confirmed true, with no
registration wall found** — a genuinely better outcome than several other backlog candidates
in the wider survey (Krain's incomplete geometry, NASA SDT's proprietary blade CAD, MEXICO's
consortium-gated data). SVA's site states: *"The data are free to download and free to use.
However, we only kindly request that the SVA is mentioned as source of the data."* No login,
no data-request form, no e-mail-gated download was encountered anywhere in this session's
retrieval path (page: `sva-potsdam.de/en/pptc-smp11-workshop/`).

### 3.1 What was actually downloaded this session (all in `references/`, ~137 MB total)

| File(s) | Content | Format |
|---|---|---|
| `case2_PPTC_geometry.pdf`, `case2_PPTC_datasheet.png` | Geometry datasheet | PDF/PNG |
| `case2_PPTC.PFF` | **Full parametric blade description**: 5 blades, D=250mm, hub=75mm, 12 radial stations × up to 43 chordwise offset points/station, pitch/camber/thickness/rake per station | SVA proprietary "PFF 2.0" text format (human-readable, parsed by this session) |
| `geometry_openwater/` (from `case2-1_open_water_test_geometry.zip`) | Open-water-rig CAD, "detailed model" + "closed hub fillets" (gap-free, easier to mesh) variants | `.3dm` (Rhino), `.igs` (IGES), `.stp` (STEP) |
| `geometry_cavitation/` (from `case2-2-3_vel-cavitation_test_geometry.zip`) | Cavitation/LDV-rig CAD, same detailed/closed-fillet variants (different hub cap than open-water rig) | `.3dm`/`.igs`/`.stp` |
| `case2-1_PPTC_hubcap2D.dat`, `case2-2+3_PPTC_hubcap2D.dat` | 2D hub-cap revolution profiles (open-water rig: 22 points; cavitation rig: 8 points — genuinely different geometry) | plain text x/y |
| `SVA_report_3752.pdf` | Open Water Tests report | PDF, full text extracted to `report3752.txt` |
| `SVA-report-3753.pdf` | Cavitation Tests report (**source of §2.3–2.6 above**) | PDF, full text extracted to `report3753.txt` |
| `SVA-report-3754.pdf` | LDV velocity-field measurement report | PDF, full text extracted to `report3754.txt` |
| `ldv_velocity_data/Velocities-_{0.094D,0.100D,0.110D,0.130D,0.160D,0.200D}.zip` | Raw measured LDV velocity-field data, one `.xls` per axial plane (~8.5–8.8 MB each) | zipped `.xls` |

Every file was fetched with a plain `curl` (HTTP 200, direct WordPress-hosted static file at
`sva-potsdam.de/wp-content/uploads/...`) — no scraping workaround, no auth, no cookies needed.

**Real inconsistency found between SVA's own documents** (documented, not silently resolved):
`case2_PPTC_geometry.pdf` states hub diameter ratio dh/D = **0.1500**, while SVA report 3753
Table 1 states dh/D = **0.300**, and the PFF file's raw numbers (HubDiameter=75.0mm,
PropDiameter=250.0mm) give 75/250 = **0.300** — independently confirming 0.300 is correct and
the geometry PDF's 0.1500 figure is very likely a typo in that one document. Flagged here so
whoever builds this case next doesn't silently trust the PDF over the report+raw-data.

### 3.2 What was *not* found / could not be verified this session
- No IGES/STEP-to-STL conversion was attempted (see §5, explicitly out of scope for this
  session — CAD import/conversion is meshing-adjacent preprocessing).
- The smp'11/smp'15 workshop *participant submissions* (i.e. other groups' computed
  results, for a broader CFD-vs-CFD comparison beyond the SVA experimental data itself) were
  not retrieved — `marinepropulsors.com/smp/files/downloads/smp11_workshop/` exists and is
  linked from search results, but this session only pulled the Barkmann geometry-description
  PDF from it, not the full proceedings archive.
- Gaggero & Villa (2018), the primary "someone has already done this in OpenFOAM" reference,
  is paywalled at Springer; a ResearchGate/academia.edu mirror exists but both returned
  HTTP 403 to automated fetch this session — its methodology (Schnerr–Sauer + VOF, RANS
  homogeneous-mixture) was confirmed via the paper's own abstract/search-indexed summary, not
  by reading the full paper. The 2015 SMP workshop's official comparison plots (how well that
  paper's OpenFOAM run actually matched σn/KT breakdown) were **not** independently verified.

## 4. OpenFOAM v2412 Solver/Library Research — The Key New-Capability Question

This is the substantive research deliverable for this case. Findings below come from directly
inspecting **this machine's actual OpenFOAM v2412 installation** at
`/usr/lib/openfoam/openfoam2412/` (source tree, `Make/options` link lists, and the actually
*compiled* binaries in `platforms/linux64GccDPInt32Opt/bin/`) — not from documentation
recollection.

### 4.1 The solver: `interPhaseChangeDyMFoam`

- **Confirmed present and already compiled** in this install:
  `/usr/lib/openfoam/openfoam2412/platforms/linux64GccDPInt32Opt/bin/interPhaseChangeDyMFoam`
- Source: `applications/solvers/multiphase/interPhaseChangeFoam/interPhaseChangeDyMFoam/`
- Description (from the solver's own `.C` header): *"Solver for two incompressible,
  isothermal immiscible fluids with phase-change (e.g. cavitation). Uses VOF ... with optional
  mesh motion and mesh topology changes."*
- **Why not plain `interPhaseChangeFoam`** (also present, also compiled): that variant is
  **static-mesh only** — no `dynamicFvMesh`/`createDynamicFvMesh.H` include, so it cannot
  rotate the propeller at all. The DyM (dynamic-mesh) variant is required for any genuine
  rotation, cavitating or not.
- **Why not MRF** (this program's default rotating-machinery approach on all 8 prior single-
  phase cases): confirmed via literature search this session — *"in case of transient
  simulations, moving meshes with the sliding plane approach are utilized ... AMI technique is
  expected to give better results than MRF in simulating complicated transient cases like
  cavitation."* MRF freezes the rotor at one instantaneous position; a cavitation sheet/tip
  vortex is inherently a moving, blade-position-dependent phenomenon, so a frozen-rotor
  approximation is the wrong tool here specifically (unlike the 8 existing single-phase cases,
  where steady MRF is defensible).
- **A second candidate solver, `overInterPhaseChangeDyMFoam`**, is also present and compiled
  (`applications/solvers/multiphase/interPhaseChangeFoam/overInterPhaseChangeDyMFoam/`) — same
  physics, but using **overset (chimera) mesh** instead of a `cyclicAMI` sliding interface.
  OpenFOAM v2412 ships an official tutorial for it too
  (`tutorials/multiphase/overInterPhaseChangeDyMFoam/twoSimpleRotors/`). Overset avoids AMI
  face-matching/interpolation-quality issues on complex blade geometry and is reportedly
  preferred by some marine-propeller CFD groups for exactly this reason — **flagged as a live
  alternative** to the AMI approach below, not dismissed; §7 lists deciding between them as an
  open question.

### 4.2 The critical discovery: OpenFOAM v2412 ships its own official propeller-cavitation tutorial

`$FOAM_TUTORIALS/multiphase/interPhaseChangeDyMFoam/propeller/` is a **working, complete,
directly runnable** OpenFOAM v2412 tutorial that is *exactly* this case's physics/solver
combination (a generic, non-PPTC 5-blade-ish rotating propeller with Schnerr–Sauer cavitation
and AMI sliding rotation) — this is the authoritative reference this case's `case/` dictionary
templates are built against, not a guess:

- **Mesh topology**: a stationary background domain (built with `blockMesh`) plus a rotating
  cylindrical `cellZone` (built via `snappyHexMesh` from separate `.obj.gz` surfaces —
  `innerCylinder`, `innerCylinderSmall`, `outerCylinder`, `propellerStem{1,2,3}`,
  `propellerTip`, at `tutorials/resources/geometry/propeller/`), connected by a `cyclicAMI`
  pair (`AMI1`/`AMI2`) created via `createPatch` from patches produced by `topoSet`.
- **Mesh motion**: `constant/dynamicMeshDict` → `dynamicFvMesh dynamicMotionSolverFvMesh;
  motionSolver solidBody; cellZone innerCylinderSmall; solidBodyMotionFunction rotatingMotion;`
  — true rigid rotation of the inner zone, not a frame trick.
- **Cavitation model**: `constant/transportProperties` → `phaseChangeTwoPhaseMixture
  SchnerrSauer;` with `phases (water vapour);`, `pSat`, `sigma`, plus Kunz/Merkle coefficient
  blocks also present (all three models compiled into the same
  `libphaseChangeTwoPhaseMixtures.so`).
- **Required libraries** (from that tutorial solver's own `Make/options`): `-lfiniteVolume
  -lfvOptions -lmeshTools -lsampling -lphaseChangeTwoPhaseMixtures -ltwoPhaseMixture
  -ltwoPhaseProperties -linterfaceProperties -lincompressibleTransportModels
  -lturbulenceModels -lincompressibleTurbulenceModels -ldynamicMesh -ldynamicFvMesh
  -ltopoChangerFvMesh` — confirmed by reading the actual `Make/options` file for
  `interPhaseChangeDyMFoam`, not inferred.
- **Solver control**: `system/controlDict` sets `maxCo 2; maxAlphaCo 1;` — the alpha-Courant
  cap specifically bounds how far the VOF interface can move per timestep, on top of the usual
  Courant number.

This program's own `pimpleFoam/RAS/propeller` tutorial (single-phase, non-cavitating, same
generic geometry) additionally ships a `propellerInfo` function object
(`system/propellerInfo`) that directly computes thrust/torque/KT/KQ/η0-style propeller
performance and wake sampling on a disk — a ready-made template for this case's validation
post-processing once a mesh exists (see the commented block in `case/system/controlDict`).

### 4.3 Confirmed OpenFOAM precedent in the literature (secondary confirmation)

- Gaggero, S., Villa, D. (2018). *"Cavitating Propeller Performance in Inclined Shaft
  Conditions with OpenFOAM: PPTC 2015 Test Case."* J. Marine Science and Application, 17 —
  confirmed via search-indexed abstract: uses OpenFOAM's homogeneous-mixture RANS + VOF with
  Schnerr–Sauer mass transfer, validated against the actual SMP'15 measurements. Full text not
  independently read this session (§3.2).
- Gaggero, S., Villa, D. (2017). *"Steady cavitating propeller performance by using OpenFOAM,
  StarCCM+ and a boundary element method."* — an earlier, steady-state comparison, also
  PPTC-specific.
- Multiple further independent OpenFOAM-PPTC studies turned up in this session's search
  (Chalmers/Bensow open-water OpenFOAM propeller work; "Numerical simulations of propeller
  cavitation flows based on OpenFOAM"; "Numerical modelling of freestream cavitating flow
  through ship propeller using OpenFOAM") — consistent, convergent precedent, not a single
  isolated paper.
- A literature-reported known limitation, carried over from the portfolio survey and worth
  taking seriously in this case's own Phase D: *standard RANS under-predicts lift breakdown at
  low cavitation numbers unless interface turbulence damping is added* — i.e. plan for a
  possible turbulence-damping modification at the alpha interface (a known VOF/RANS
  interaction issue, not unique to this propeller) if the baseline kOmegaSST run shows the same
  gap.

## 5. Proposed Case-Build Plan (Phase B onward — not started)

1. **Phase B — geometry realization** (not done this session, deliberately): import
   `references/geometry_cavitation/detailed model/case2-2+3_PPTC_geo.igs` (or the
   `closed hub fillets` no-gap variant, likely easier to mesh first) into a CAD tool capable of
   IGES import (FreeCAD/OpenCASCADE, or a licensed CAD package) and export clean, closed,
   manifold STL surfaces for: the 5 blades, the hub+hub-cap, and a rotating-cylinder enclosure
   surface. The PFF parametric file is a second, independent path to the same blade geometry
   (loft from the 12-radii × 43-point section table) if CAD import proves difficult — the same
   "build from tabulated sections" pattern already used for NREL Phase VI's S809 blade.
2. **Phase C — mesh**: `blockMesh` for the farfield background (template written this session,
   `case/system/blockMeshDict`, domain sized per ITTC open-water guidelines — untested), then
   `snappyHexMesh` with a real `snappyHexMeshDict` (not written this session — see
   `case/system/snappyHexMeshDict.NOTES` for exactly why and what it needs), then
   `topoSet`/`createPatch` to build the `AMI1`/`AMI2` cyclicAMI pair (templates written this
   session, patch names to be reconciled with whatever `snappyHexMeshDict` actually produces).
   `checkMesh` gate before any run, per this program's standard convention.
3. **Phase D — first run**: start with the non-cavitating open-water baseline (§2.2, n=15/20/25
   s⁻¹, cavitation suppressed) to validate KT/KQ/η0 against SVA report 3753's own measured
   non-cavitating numbers *before* turning cavitation on — isolates mesh/rotation-setup bugs
   from cavitation-model bugs, same "isolate the variable" discipline as the NREL Phase VI
   bug hunt (root/outboard patch split) documented in that case's `PROBLEM.md`.
4. **Phase E — cavitation validation**: switch on Schnerr–Sauer, run test case 2.3.1
   (J=1.019, σn=2.024) first (mildest cavitation extent), then 2.3.2/2.3.3, comparing predicted
   cavity extent/pattern against SVA's own cavitation photographs/videos (report 3753 §7.2) and
   the LDV wake data (§2.7) for the non-cavitating flow-field cross-check.
5. **Phase F (optional/backlog)**: the oblique-shaft SMP'15 variant (§2.8) as a follow-on once
   the zero-inclination baseline is validated — this is the exact configuration Gaggero & Villa
   (2018) studied, so it's the natural point to attempt a closer quantitative comparison against
   a specific published OpenFOAM result rather than only the raw SVA experimental data.

### What was actually written this session (`case/`, all explicitly Phase-A/B templates, none run)

| File | Status |
|---|---|
| `system/controlDict` | `interPhaseChangeDyMFoam`, transient PIMPLE, alpha-Courant capped, endTime sized to ~12 shaft revolutions at the n=24.987 s⁻¹ target — placeholder `propellerInfo` function object commented out pending real patch names |
| `system/fvSchemes`, `system/fvSolution` | Copied near-verbatim from OpenFOAM's own official `interPhaseChangeDyMFoam/propeller` tutorial (the authoritative in-version reference), generalised from k-epsilon to k-omega SST for consistency with this program's other cases |
| `constant/transportProperties` | Schnerr–Sauer selected; water ρ/ν and pSat taken from *measured* SVA report 3753 environmental data (not generic tutorial defaults); vapour ρ/ν flagged as an approximation from steam tables (SVA doesn't report vapour properties directly) |
| `constant/dynamicMeshDict` | `dynamicMotionSolverFvMesh` + `solidBody rotatingMotion` on a placeholder `rotatingZone`, ω = 2π×24.987 = 157.02 rad/s at the primary target point; axis/origin/sign flagged as needing reconciliation against SVA's own SCS-vs-PCS coordinate-system split (§3.1) once real geometry is imported |
| `constant/turbulenceProperties` | kOmegaSST RAS, with the interface-turbulence-damping caveat (§4.3) flagged for Phase D follow-up |
| `constant/g` | Present (required by the solver's hydrostatic term), orientation flagged as pending axis finalisation |
| `system/blockMeshDict` | Background farfield box, D=0.25m-scaled per ITTC-style guidelines — **not meshed, sizing unverified** |
| `system/createPatchDict` | AMI1/AMI2 cyclicAMI pair, modelled on the official tutorial, placeholder source-patch names |
| `system/snappyHexMeshDict.NOTES` | Explains explicitly why no `snappyHexMeshDict` was written (needs STL that doesn't exist yet — see Phase B) rather than fabricating one |
| `system/decomposeParDict` | Placeholder subdomain count (16, scotch) — real value pending actual cell count |
| `0.orig/{U,p_rgh,alpha.water,k,omega,nut}` | BC templates for inlet/outlet/farfield/AMI1/AMI2/propellerBlades/propellerHub (latter two are placeholder patch names), U/p_rgh numerically derived from the J=1.019, σn=2.024 target point; k/omega from an assumed (unverified) 1% turbulence intensity, same class of assumption this program already made and flagged for NREL Phase VI |

## 6. Open Questions Needing a Human Decision

1. **AMI/sliding-mesh vs. overset** (`interPhaseChangeDyMFoam` vs. `overInterPhaseChangeDyMFoam`,
   §4.1) — both are compiled and tutorial-backed in this install; a real decision, not yet made.
2. **Which CAD variant to mesh first** — "detailed model" (includes the real 0.3mm CPP
   hub-blade gap) vs. "closed hub fillets" (gap-free, almost certainly easier to mesh cleanly
   with `snappyHexMesh`, at the cost of a geometric simplification of the real hub-gap flow
   physics). The FDA-blood-pump and Rotor-37 cases in this program both did some amount of
   CAD-to-mesh simplification already — precedent exists for starting with the simplified
   variant and documenting the gap.
3. **Coordinate-system reconciliation** — SVA's SCS (open-water rig) vs. PCS (cavitation rig)
   differ in x-direction sign; the two geometry CAD sets are *not* delivered in the same frame
   as each other. Needs to be resolved deliberately in Phase B/C, not left to convention-
   guessing (flagged explicitly in `case/constant/dynamicMeshDict`'s comments).
4. **Turbulence intensity at inflow** — not stated in any SVA report read this session; the
   1% assumption in `0.orig/k`/`omega` is unverified, same caveat class as NREL Phase VI's own
   unverified TI assumption.
5. **Domain size / mesh resolution** — `case/system/blockMeshDict`'s farfield extents follow
   generic ITTC guidance, not a PPTC-specific blockage study; genuinely needs a convergence
   check once meshing starts, not a rubber-stamp.
6. **Compute budget** — this will be markedly more expensive than any of the 8 existing cases:
   a transient (not steady), dynamic-mesh (not frozen-MRF), two-phase (not single-phase) solver,
   with deltaT likely in the 1e-6–1e-4 s range over many shaft revolutions to reach a periodic
   cavitation pattern. Worth sizing/estimating before committing wall-clock time, given this
   program's existing compute pressure (the portfolio's own compute-weight table already rates
   this case "Medium," the middle of the 9).
7. **Whether to also read the Gaggero & Villa (2018) full text** — currently blocked by a
   paywall/403 on every mirror tried this session; a human with journal access could resolve
   this and potentially hand this case a much more specific, already-published quantitative
   comparison target (mesh size, exact BCs, reported error bars) rather than this session's
   from-scratch Phase B/C plan.

---

*Compiled by direct primary-source retrieval (SVA Potsdam's own site, this machine's actual
OpenFOAM v2412 installation) this session — no claim above is carried over unverified from the
portfolio survey's summary text. Companion documents: `../TURBOMACHINERY_BREADTH_PORTFOLIO.md`
§2.6 (the approved case definition this README fulfils), `../nrelPhaseVI_v2412/PROBLEM.md`
(the tone/structure this README follows), `../MASTER_REPORT.md` (the 5 already-built cases).*
