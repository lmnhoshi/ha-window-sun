# Changelog

## 0.2.1 – 2026-11-16

- Logo, shown in Home Assistant and the Marketplace.
- README: screenshot, calculation diagram, floor-plan label example.

## 0.2.0 – 2026-11-16

- Each window has a minimum and a maximum sun angle from the wall (default 1°–179°,
  the previous fixed rule). Set them in Configure. Existing windows keep 1°–179°.
- New attributes `min_angle` and `max_angle` on the sun-hours sensor.

## 0.1.0 – 2026-11-16

- First release: one entry per window (orientation, floor, ground-floor convention).
- Sun hours, first/last sun, shown day (today → tomorrow once today's sun is over),
  and a "sun on window" binary sensor. No obstacles.
