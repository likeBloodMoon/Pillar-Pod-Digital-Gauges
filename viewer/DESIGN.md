# Event History: design contract

The viewer is the car's own data logger, so it looks like the rest of the mod: the multi-function
display and the digital cluster. It is not a generic dashboard.

## Who and what for
A player, after a drive or a crash, wants to know **what happened and how bad it was**. They pick an
event, read the answer in a couple of seconds, then scrub the readings around it. On a PC they also
compare drives and export data.

## Hierarchy (per event)
1. **The answer**: one hero reading, big, like the cluster's speed (`1.21 bar`, `PEAK BOOST`).
2. **The situation**: a single row of context at the peak: RPM, speed, the gear in its box,
   temperatures, throttle. Grey uppercase label above white numerals with a small unit, as on the display.
3. **The readings**: stacked lanes on one shared time axis, the event's main channel first and
   tallest. One cursor runs through every lane and shows the values. With no cursor, each lane shows
   its value at the peak.
4. **Where in the drive**: the timeline strip on top, with every event on the drive's speed trace.

## Tokens (from `mfd.html` / `cluster.html`)
- Background: navy-black `#05080d` to `#0a111b`. Panels `#0c1420`, hairlines `#16202e`.
- Text: white `#f4f6f8`, grey `#8d99a8`, dim `#3b4757`.
- Traces: blue `#2e7cf6`, sky `#7cc4ff`. Throttle green `#7ed321`, brake red.
- Red `#e8262d` is reserved for rules and the moment an event starts. Amber `#f5b31a` marks engine
  events, sky marks driving events (braking, cornering), red marks impacts.
- Font: Barlow Semi Condensed 500/600/700 (the mod's own, OFL). Labels are uppercase and
  letter-spaced; numbers use tabular figures.

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
| both | event still recording | a REC mark on the event; its window grows |
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
