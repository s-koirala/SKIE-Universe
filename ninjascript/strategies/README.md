# ninjascript/strategies

NinjaTrader 8 strategies for SKIE-Universe. One C# file per strategy, namespace `NinjaTrader.NinjaScript.Strategies`.

## TrivialSmokeTest.cs

Phase-0 end-to-end execution smoke test per [plan/implementation-plan_2026-04-15.md §P0-9](../../plan/implementation-plan_2026-04-15.md).

### Build

1. Open NinjaTrader 8 Desktop.
2. From the Control Center: `New -> NinjaScript Editor`.
3. In the left tree, right-click `Strategies -> Import NinjaScript...` is not required for local files; instead copy `TrivialSmokeTest.cs` into:
   `%USERPROFILE%\Documents\NinjaTrader 8\bin\Custom\Strategies\TrivialSmokeTest.cs`.
4. In the NinjaScript Editor, press `F5` to compile. The output window must report `0 errors`.
5. NT8 ships with .NET Framework 4.8 and its bundled C# compiler. No external toolchain is used.

### Deploy (paper trading)

1. Connect to the `Playback` or `Sim101` (paper) account.
2. Load an `MES` front-month chart on a 1-minute interval, RTH session template.
3. Control Center -> `Strategies` tab -> `Add` -> select `TrivialSmokeTest`.
4. Parameters: leave defaults (`EntryHourCT=9, EntryMinuteCT=30, FlattenHourCT=15, FlattenMinuteCT=0, ContractRoot=MES, Qty=1`).
5. Account: `Sim101`. Enabled: `True`.

### Acceptance-test procedure

Run 3 consecutive weekday paper sessions. For each session:

1. Verify one `BUY` fill is written to `%USERPROFILE%\Documents\NinjaTrader 8\logs\skie_ninja_smoke_fills.csv` at or just after 09:30 CT.
2. Verify one `SELL` (flatten) fill is written at or just after 15:00 CT.
3. Confirm the CSV header is exactly:
   `order_id,submit_ts,fill_ts,symbol,side,qty,limit_px,fill_px,order_type,session,mid_at_submit,book_depth_at_submit`
4. Confirm each row has 12 comma-separated fields; `book_depth_at_submit` is empty; timestamps are ISO-8601 with offset.
5. Pass the CSV to the Phase-1 ingest validator (P1-3) once available; it must parse with zero schema errors.

### Timezone handling (F-2-1)

NT8 `Time[0]` is the bar timestamp in the session-template / workstation time zone, not guaranteed exchange-local CT. The strategy converts every bar/clock timestamp to `America/Chicago` via `TimeZoneInfo.ConvertTime`, using `Bars.TradingHours.TimeZoneInfo` as the source when the NT8 build exposes it, else `TimeZoneInfo.Local`. All CT entry/flatten comparisons and CSV `submit_ts`/`fill_ts` values are CT-anchored; timestamps are ISO-8601 with the CT offset (`-05:00` CDT or `-06:00` CST). See [NT8 TradingHours help](https://ninjatrader.com/support/helpGuides/nt8/NT%20HelpGuide%20English.html?tradinghours.htm).

### L2 / book_depth_at_submit policy (F-2-15)

Phase-0 smoke test intentionally leaves `book_depth_at_submit` empty: L2 market depth is not subscribed in this strategy (out of scope for P0-9). The P1-3 ingest validator MUST accept `book_depth_at_submit` as nullable for Phase-0 fixture data and MUST require non-null values only for Phase-1 production ingests where an L2 subscription is active.

### Troubleshooting

- If `Bars.TradingHours.IsMarketOpenAt` is not present in the NT8 build in use, the helper falls back to `true` and relies on `IsExitOnSessionCloseStrategy = true` plus the chart's session template.
- If CT timestamps still look wrong after the F-2-1 fix, verify (a) the Windows TZ database has `Central Standard Time` installed (standard on Win10/11), and (b) for older NT8 builds that do not expose `Bars.TradingHours.TimeZoneInfo`, the workstation's `TimeZoneInfo.Local` correctly describes the session-template TZ.
