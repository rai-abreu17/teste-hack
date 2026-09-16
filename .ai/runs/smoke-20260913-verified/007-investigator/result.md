## Cross-Critique of the Anonymous Peer Finding

**Scope note:** this is a closed-form geometry exercise; nothing here validates any sensor, servo, or real architecture, and no application state exists to inspect.

### Agreements (verified independently)
- **Volume:** V = L²H = 30²·12 = 10 800 cm³ = **10.8 L**. Correct, unit conversion correct.
- **Footprint:** w = 2h·tan(θ/2) = 40·tan 30° = 40/√3 ≈ **23.094 cm**. Correct.
- **Containment:** half-width 11.55 cm < 15 cm, so the centred square lies wholly inside the 30 cm span. Correct, and the peer's arithmetic cross-check is a legitimate sanity test.
- **Fraction:** f = w²/L² = (40/√3)²/900 = 1600/2700 = **16/27 ≈ 59.26 %**. Correct — and it is exactly rational; the peer reported the decimal without noting the closed form, which is a missed strengthening, not an error.
- **Occlusion argument (item 4):** correct in substance. Rotation about the *exact* optical centre is a change of basis on the ray bundle, not a change of baseline; for any scene point P, the segment centre→P is invariant, so an interposed obstacle stays interposed. Only translation of the centre (parallax) or motion of the occluder can reveal P.

### Contradictions / unsupported or under-specified points
1. **Plane ambiguity (most material).** Item 3 says "fração da **base**", while item 2 says "projeção na **superfície**". The peer silently equates them. Defensible (the material fills the base, so the top surface's top-view extent is the same 30×30), but at the *base plane* h = 32 cm gives w ≈ 36.95 cm > 30 cm, i.e. nominal full coverage. The answer swings 59 % vs 100 % on an unstated choice; it should be stated, not assumed.
2. **"Rotation only changes which regions are framed"** is stated more loosely than justified. A pure *roll* about the optical axis keeps the footprint square but rotates it: its half-diagonal is w/√2 ≈ 16.33 cm > 15 cm, so corners spill outside the base and coverage *drops below* 16/27. A *tilt* breaks the premise of item 2 entirely — the footprint becomes a keystone (trapezoid), and w = 2h·tan(θ/2) no longer applies. Neither case is flagged.
3. **"Superfície plana e uniforme"** is asserted as a hypothesis but is also doing hidden work: with a flat, unoccluded ideal surface there is *no* occluder, so item 4 is a counterfactual about a scene the model has excluded.

### Decisive tests
- Recompute f symbolically as (2h tan(θ/2)/L)²; if it does not reduce to 16/27, an arithmetic slip exists.
- Set h = 32 cm (base plane) and re-evaluate; divergence to >100 % confirms the ambiguity is decisive, not cosmetic.
- Roll the square footprint 45° and compute the square–square intersection area; any claim that coverage is rotation-invariant fails immediately.
- Formalise occlusion as: P occluded ⟺ ∃ obstacle on segment [C,P]. Apply rotation R about C: the segment is unchanged ⇒ predicate unchanged. This is the clean proof the peer gestures at.

### Residual uncertainty
The intended reference plane and whether "girar" means roll or tilt are not resolvable from the given text. Conditional on the peer's (reasonable) reading, all four answers stand.
