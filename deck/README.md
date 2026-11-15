# deck/

Source of the presentation deck *Priced Out of Reach* (18 slides, speaker notes in each slide’s `<aside>`), exported from the Slides artifact at https://claude.ai/artifact/XrbvJxFiptkMhRtcJe8raM (private until shared from its Share menu).

```
project/deck.json         slide order, sections, typefaces
project/deck.css          shared styles
project/slides/<id>.html  one slide each, 1920×1080
```

Every figure on a slide comes from a workstream’s `FINDINGS.md` (see `../SYNTHESIS.md` for the mapping). Slide 16 (`atlas.html`) embeds a 14 KB animated map built from `units-leaving-reach/results/viz/units.json`: units are pooled into 0.025° cells and each cell’s share out of reach is stored per year, for the “rents keep 2026 pace” scenario with 20% annual turnover. The full interactive version is `units-leaving-reach/site/out-of-reach-atlas.html`.

Placeholders to fill before presenting: `[Team name]` on the cover and closing slides.
