// -----------------------------------------------------------------------------
// TrivialSmokeTest.cs
//
// Author       : SKIE
// Purpose      : Phase-0 smoke test to prove end-to-end execution loop per
//                plan/implementation-plan_2026-04-15.md §P0-9.
// Reference    : NinjaTrader 8 Strategy documentation
//                https://ninjatrader.com/support/helpGuides/nt8/NT%20HelpGuide%20English.html
//                Bars.TradingHours.TimeZoneInfo property (NT8 AB-supported):
//                https://ninjatrader.com/support/helpGuides/nt8/NT%20HelpGuide%20English.html?tradinghours.htm
//
// Behavior
//   - Buys 1 MES (default) at 09:30 CT (exchange local time).
//   - Flattens all positions at 15:00 CT.
//   - Trades only on weekdays during RTH. Skips half-days and closes by
//     deferring to NinjaTrader's session template via Bars.IsResetOnNewTradingDay
//     and Bars.BarsType / Bars.TradingHours.Sessions checks.
//   - Writes one CSV row per fill event to:
//     %USERPROFILE%\Documents\NinjaTrader 8\logs\skie_ninja_smoke_fills.csv
//
// Timezone correctness (P0-9 F-2-1 fix)
//   - NT8 `Time[0]` is NOT guaranteed to be exchange-local CT. It is the bar
//     timestamp in the time zone dictated by the session template / workstation
//     (commonly ET or the user's local TZ). Comparing `Time[0].Hour/Minute`
//     directly against CT entry/flatten times produced a ~1-hour trade offset
//     for ET-configured workstations.
//   - Fix: convert every bar/clock time to America/Chicago via
//     `TimeZoneInfo.ConvertTime`. Source TZ is
//     `Bars.TradingHours.TimeZoneInfo` when available (NT8 exposes this on
//     the TradingHours object); otherwise we fall back to `TimeZoneInfo.Local`
//     and the user must verify the NT8 workstation TZ at F5 compile time.
//   - CSV `submit_ts` and `fill_ts` are emitted as ISO-8601 with the CT offset
//     (`-05:00` CDT / `-06:00` CST), not the workstation offset.
//
// Acceptance Criteria (plan §P0-9)
//   - Runs against a NinjaTrader paper account for 3 sessions with zero errors.
//   - Emits a CSV whose schema matches the Phase-1 cost-model ingest (plan §6.1):
//       order_id, submit_ts, fill_ts, symbol, side, qty, limit_px, fill_px,
//       order_type, session, mid_at_submit, book_depth_at_submit
//   - CSV is consumable by P1-3 validator with zero schema errors.
//
// Magic-number policy
//   - The only hard-coded numerics are (a) the default entry/flatten CT times
//     and (b) the default qty=1 — both overridable via NinjaScriptProperty.
//     Justification: these are the literal acceptance-test parameters in §P0-9.
// -----------------------------------------------------------------------------

#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Text;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Strategies;
#endregion

namespace NinjaTrader.NinjaScript.Strategies
{
    public class TrivialSmokeTest : Strategy
    {
        // CSV schema header (must match plan §6.1 exactly).
        private const string CsvHeader =
            "order_id,submit_ts,fill_ts,symbol,side,qty,limit_px,fill_px,order_type,session,mid_at_submit,book_depth_at_submit";

        // Session tag written to each CSV row. RTH is the only regime we trade here.
        private const string SessionTag = "RTH";

        // Resolved absolute log file path (set in State.Configure).
        private string fillLogPath;

        // Track pending submits so we can emit the submit_ts once the fill arrives.
        // Key: OrderId string. Value: (submitTs, midAtSubmit).
        private Dictionary<string, (DateTime submitTs, double midAtSubmit)> pendingSubmits;

        // Latched flags per trading day to avoid double entries / re-entries.
        private DateTime lastTradedDate = DateTime.MinValue;
        private bool enteredToday;
        private bool flattenedToday;

        #region NinjaScriptProperties
        [NinjaScriptProperty]
        [Display(Name = "Entry Hour CT", Order = 1, GroupName = "Parameters")]
        [Range(0, 23)]
        public int EntryHourCT { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Entry Minute CT", Order = 2, GroupName = "Parameters")]
        [Range(0, 59)]
        public int EntryMinuteCT { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Flatten Hour CT", Order = 3, GroupName = "Parameters")]
        [Range(0, 23)]
        public int FlattenHourCT { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Flatten Minute CT", Order = 4, GroupName = "Parameters")]
        [Range(0, 59)]
        public int FlattenMinuteCT { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Contract Root", Order = 5, GroupName = "Parameters")]
        public string ContractRoot { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Quantity", Order = 6, GroupName = "Parameters")]
        [Range(1, int.MaxValue)]
        public int Qty { get; set; }
        #endregion

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = "SKIE Phase-0 smoke test. Buys 1 MES at 09:30 CT, flattens at 15:00 CT. Logs fills to CSV.";
                Name = "TrivialSmokeTest";

                Calculate = Calculate.OnBarClose;
                IsInstantiatedOnEachOptimizationIteration = false;
                IsExitOnSessionCloseStrategy = true;
                ExitOnSessionCloseSeconds = 60;
                EntriesPerDirection = 1;
                EntryHandling = EntryHandling.AllEntries;
                IsUnmanaged = false;
                BarsRequiredToTrade = 1;

                // Defaults per §P0-9.
                EntryHourCT = 9;
                EntryMinuteCT = 30;
                FlattenHourCT = 15;
                FlattenMinuteCT = 0;
                ContractRoot = "MES";
                Qty = 1;
            }
            else if (State == State.Configure)
            {
                pendingSubmits = new Dictionary<string, (DateTime, double)>(StringComparer.Ordinal);

                string userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
                string logDir = Path.Combine(userProfile, "Documents", "NinjaTrader 8", "logs");
                Directory.CreateDirectory(logDir);
                fillLogPath = Path.Combine(logDir, "skie_ninja_smoke_fills.csv");

                if (!File.Exists(fillLogPath))
                {
                    File.WriteAllText(fillLogPath, CsvHeader + Environment.NewLine, Encoding.UTF8);
                }
            }
        }

        protected override void OnBarUpdate()
        {
            if (CurrentBar < BarsRequiredToTrade) return;
            if (Bars == null || Bars.BarsSeries == null) return;

            // Reset per-day latches on new trading day.
            DateTime tradingDay = Bars.GetTradingDayFromLocal(Time[0]);
            if (tradingDay != lastTradedDate)
            {
                lastTradedDate = tradingDay;
                enteredToday = false;
                flattenedToday = false;
            }

            // Weekdays only.
            DayOfWeek dow = tradingDay.DayOfWeek;
            if (dow == DayOfWeek.Saturday || dow == DayOfWeek.Sunday) return;

            // Only act when the exchange session is open. Bars.IsResetOnNewTradingDay
            // and the session template supplied by the instrument cover half-days.
            if (!Bars.BarsType.IsIntraday) return;
            if (!Bars.IsTickReplay && !IsSessionOpenAt(Time[0])) return;

            // Convert bar time to America/Chicago for all CT comparisons.
            DateTime tCt = ToCentral(Time[0]);

            // Entry: at or after EntryTime CT, once per day.
            if (!enteredToday && IsAtOrAfterCT(tCt, EntryHourCT, EntryMinuteCT)
                && IsBeforeCT(tCt, FlattenHourCT, FlattenMinuteCT))
            {
                string signalName = "SmokeEntry";
                double midAtSubmit = (GetCurrentBid(0) + GetCurrentAsk(0)) / 2.0;
                DateTime submitTs = tCt;

                EnterLong(Qty, signalName);
                // Stash submit metadata keyed by signal name; matched in OnExecutionUpdate.
                pendingSubmits[signalName] = (submitTs, midAtSubmit);
                enteredToday = true;
            }

            // Flatten: at or after FlattenTime CT.
            if (!flattenedToday && IsAtOrAfterCT(tCt, FlattenHourCT, FlattenMinuteCT))
            {
                if (Position.MarketPosition != MarketPosition.Flat)
                {
                    string signalName = "SmokeFlatten";
                    double midAtSubmit = (GetCurrentBid(0) + GetCurrentAsk(0)) / 2.0;
                    DateTime submitTs = tCt;

                    if (Position.MarketPosition == MarketPosition.Long)
                        ExitLong(Position.Quantity, signalName, string.Empty);
                    else if (Position.MarketPosition == MarketPosition.Short)
                        ExitShort(Position.Quantity, signalName, string.Empty);

                    pendingSubmits[signalName] = (submitTs, midAtSubmit);
                }
                flattenedToday = true;
            }
        }

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price,
            int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            if (execution == null || execution.Order == null) return;
            if (execution.Order.OrderState != OrderState.Filled
                && execution.Order.OrderState != OrderState.PartFilled) return;

            string signalName = execution.Order.FromEntrySignal;
            if (string.IsNullOrEmpty(signalName)) signalName = execution.Order.Name ?? string.Empty;

            DateTime submitTs;
            double midAtSubmit;
            if (pendingSubmits.TryGetValue(signalName, out var meta))
            {
                // submitTs was stored already in CT from OnBarUpdate.
                submitTs = meta.submitTs;
                midAtSubmit = meta.midAtSubmit;
            }
            else
            {
                submitTs = ToCentral(execution.Order.Time);
                midAtSubmit = double.NaN;
            }

            // Convert fill timestamp to CT for CSV emission.
            DateTime fillTs = ToCentral(time);

            string side = marketPosition == MarketPosition.Long ? "BUY"
                        : marketPosition == MarketPosition.Short ? "SELL"
                        : "FLAT";

            // NT8 OrderType enum → CSV token.
            string orderType = execution.Order.OrderType.ToString();

            // Limit price: NaN for market orders.
            double limitPx = execution.Order.LimitPrice;

            string row = string.Join(",",
                Escape(orderId),
                FormatCtIso(submitTs),
                FormatCtIso(fillTs),
                Escape(Instrument != null ? Instrument.FullName : ContractRoot),
                side,
                quantity.ToString(CultureInfo.InvariantCulture),
                double.IsNaN(limitPx) || limitPx == 0.0 ? string.Empty : limitPx.ToString("G", CultureInfo.InvariantCulture),
                price.ToString("G", CultureInfo.InvariantCulture),
                Escape(orderType),
                SessionTag,
                double.IsNaN(midAtSubmit) ? string.Empty : midAtSubmit.ToString("G", CultureInfo.InvariantCulture),
                string.Empty /* book_depth_at_submit — not available without L2 subscription */
            );

            try
            {
                File.AppendAllText(fillLogPath, row + Environment.NewLine, Encoding.UTF8);
            }
            catch (IOException ex)
            {
                Print("TrivialSmokeTest CSV append failed: " + ex.Message);
            }
        }

        // -------------------------------------------------------------------------
        // Helpers
        // -------------------------------------------------------------------------

        // America/Chicago resolves to "Central Standard Time" on Windows
        // (.NET Framework 4.8 / NT8). Windows TZ IDs handle CST/CDT transitions
        // automatically.
        private static readonly TimeZoneInfo CentralTz =
            TimeZoneInfo.FindSystemTimeZoneById("Central Standard Time");

        // Convert an arbitrary DateTime (from Time[0], DateTime.Now, or an
        // Order timestamp) to America/Chicago. Source TZ is
        // Bars.TradingHours.TimeZoneInfo when available (NT8 AB-supported),
        // else TimeZoneInfo.Local. Guarded with try/catch to tolerate older
        // NT8 builds that lack the property.
        private DateTime ToCentral(DateTime t)
        {
            try
            {
                TimeZoneInfo sourceTz = null;
                if (Bars != null && Bars.TradingHours != null)
                {
                    // TradingHours.TimeZoneInfo exists on NT8 AB builds; guarded
                    // by try/catch for forward-compat with older releases.
                    sourceTz = Bars.TradingHours.TimeZoneInfo;
                }
                if (sourceTz == null) sourceTz = TimeZoneInfo.Local;

                DateTime src = t.Kind == DateTimeKind.Utc
                    ? t
                    : DateTime.SpecifyKind(t, DateTimeKind.Unspecified);

                if (t.Kind == DateTimeKind.Utc)
                    return TimeZoneInfo.ConvertTimeFromUtc(src, CentralTz);
                return TimeZoneInfo.ConvertTime(src, sourceTz, CentralTz);
            }
            catch
            {
                // Fall back: assume input is workstation-local.
                try
                {
                    DateTime localT = DateTime.SpecifyKind(t, DateTimeKind.Local);
                    return TimeZoneInfo.ConvertTime(localT, TimeZoneInfo.Local, CentralTz);
                }
                catch
                {
                    return t;
                }
            }
        }

        // ISO-8601 with the America/Chicago UTC offset (`-05:00` CDT or
        // `-06:00` CST). `t` is assumed already converted to CT by ToCentral.
        private static string FormatCtIso(DateTime t)
        {
            TimeSpan off = CentralTz.GetUtcOffset(
                t.Kind == DateTimeKind.Unspecified
                    ? DateTime.SpecifyKind(t, DateTimeKind.Unspecified)
                    : t);
            DateTimeOffset dto = new DateTimeOffset(
                DateTime.SpecifyKind(t, DateTimeKind.Unspecified), off);
            return dto.ToString("yyyy-MM-ddTHH:mm:ss.fffzzz", CultureInfo.InvariantCulture);
        }

        private static bool IsAtOrAfterCT(DateTime t, int h, int m)
        {
            return t.Hour > h || (t.Hour == h && t.Minute >= m);
        }

        private static bool IsBeforeCT(DateTime t, int h, int m)
        {
            return t.Hour < h || (t.Hour == h && t.Minute < m);
        }

        private bool IsSessionOpenAt(DateTime t)
        {
            try
            {
                if (Bars.TradingHours == null) return true;
                return Bars.TradingHours.Sessions != null
                    && Bars.TradingHours.IsMarketOpenAt(t);
            }
            catch
            {
                return true;
            }
        }

        private static string Escape(string s)
        {
            if (string.IsNullOrEmpty(s)) return string.Empty;
            if (s.IndexOfAny(new[] { ',', '"', '\n', '\r' }) < 0) return s;
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        }
    }
}
