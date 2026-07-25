# Lightweight Games

Use one HTML file with Canvas, SVG, or DOM by default. Keep the main loop, controls, local persistence, and result state self-contained.

## Infer The Game Shape

- Arcade or score chase: current score, best score, end state, and fast restart.
- Puzzle: moves, solved state, reset, and optional best completion.
- Story or dialogue: scene progress, clear ending, and replay.
- Simulation or management: visible resource changes, round goals, and saved progress.
- Action: readable health or risk, pause/restart, and touch controls.

## Completion Baseline

- Show a readable start state and concise controls.
- Expose the core interaction without requiring initial scrolling on phones.
- Provide current-state feedback during play.
- Include a visible end or completion state.
- Provide replay or restart.
- Store only useful, non-sensitive progress locally.
- Keep score and best score clearly distinct.
- Pause when the page becomes hidden if real time affects fairness.

## Input

Support keyboard and pointer input when both make sense. Use Pointer Events to unify mouse, pen, and touch. Avoid hover-only actions. Prevent page scrolling only inside the active play surface.

## Layout

Budget status, playfield, and controls as one vertical system. Preserve the game mechanic between desktop and mobile instead of building unrelated layouts. Prefer portrait usability unless the concept genuinely requires landscape.

## Testing

Test start, pause if present, failure, success, replay, stored progress, keyboard, touch, resizing, background/foreground changes, and repeated rapid input. Check that elapsed time is capped after long inactive frames.
