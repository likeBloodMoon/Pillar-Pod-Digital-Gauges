# Event History: design contract

The viewer is the car's own data logger. It should look like a factory performance display (the
GT-R's multi-function screen is the reference): flat charcoal panels, thin grey outlines, white
numerals, one red accent. It is not a web dashboard.

## Who and what for
A player, after a drive or a crash, wants to know **what happened and how bad it was**. They pick an
event, read the answer in a couple of seconds, then scrub the readings around it. On a PC they also
compare drives and export data.

## Hierarchy (per event)
1. **The answer**: one hero reading, big and light (`1.21 bar`, `Peak boost`).
2. **The situation**: a single row of context at the peak: RPM, speed, the gear in its box,
   temperatures, throttle. Grey label above white numerals with a small grey unit.
3. **The readings**: stacked lanes on one shared time axis, the event's main channel first and
   tallest. One cursor runs through every lane and shows the values. With no cursor, each lane shows
   its value at the peak.
4. **Where in the drive**: the timeline strip on top, with every event on the drive's speed trace.

## Tokens (`K` in `viewer.js`)
- Every colour is solid. No gradients, glows, tints or see-through fills.
- Page `#0d0d0d`. Panels `#181818` with a 1 px `#4a4a4a` outline and 6 px corners; hover and selected
  rows, and an event's time window in the lanes, are `#232323`. Dividers `#2e2e2e`.
- Text: white `#f2f2f2`, grey `#a6a6a6`, dim `#666666`.
- Traces are white; a second trace in the same lane (brake under throttle) is grey and dashed, so
  lanes never need colour to tell lines apart.
- One accent, red `#e3241b`, and only for: the line where an event starts, the selected event (its
  numbered circle and its timeline marker), the recording dot and errors. Event kinds are not
  colour-coded; the list numbers them in circles, like the display's preset row.
- Font: the system UI font (Segoe UI in the game and on Windows). Sentence case, no letter-spacing;
  numbers use tabular figures.

## Honesty
- Only readings the recorder stored. No made-up metrics, scores or ratings.
- A channel the car doesn't report (no turbo, no exhaust temperature) is shown as not reported. It is
  never drawn as a flat zero.
- Thresholds quoted in the UI are the recorder's real ones (`dbgRecorder.lua`, table `T`).

## States
| Where | State | Shows |
|---|---|---|
| in game | connecting | "Connecting to the car…" until the first answer |
| in game | no recorder | which parts to fit to start recording |
| both | recording, no events | that it's recording, and what makes an event (real thresholds) |
| both | event still recording | a red "Recording" on the event; its window grows |
| in game | save | Saving… / Saved, with the path / Save failed |
| in game | clear | asks again before clearing |
| PC | no file | a drop zone, where the files are, how they get there |
| PC | wrong or newer file | an error in the drop zone; the open file stays |
| both | narrow app | compact list, the context row wraps |

## Interaction
- Click an event, or use ↑ / ↓ to step through them.
- Click a timeline marker to jump to its event.
- Hover or drag over the lanes to scrub. Lane chips add or remove channels; channels the car
  doesn't report are greyed out.
