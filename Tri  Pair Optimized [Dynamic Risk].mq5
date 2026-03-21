//+------------------------------------------------------------------+
//| Tri Pair Optimized [Dynamic Risk] v3.0                          |
//| Full Strategy + CSV Trade Logging (36 Fields)                   |
//+------------------------------------------------------------------+
#include <Trade\Trade.mqh>

//--- Inputs
input double MaximumRisk         = 0.01;
input double StopLossPips        = 60;
input double BreakEvenRR         = 0.7;
input int    MovingPeriod        = 12;
input int    MovingShift         = 6;
input int    ATRPeriod           = 14;
input double ATRMinimumPips      = 10.0;
input double TrailingStopATRMult = 1.2;
input int    SessionStartHour    = 6;
input int    SessionEndHour      = 17;
input ulong  MagicNumber         = 123456;

//--- Indicator handles
int ExtHandle  = INVALID_HANDLE; // MA
int atrHandle  = INVALID_HANDLE; // ATR14
int atr5Handle = INVALID_HANDLE; // ATR5
int adxHandle  = INVALID_HANDLE; // ADX14

//--- Trade object & state
CTrade ExtTrade;
bool   BreakEvenApplied        = false;
bool   TrailingStopActivated   = false;
bool   PartialExitApplied      = false;
double max_price               = 0;

//--- Alert flags
bool AlertedLossStreak           = false;
bool AlertedDrawdown             = false;
bool AlertedBreakevenStall       = false;
bool AlertedStallAtHalfR         = false;
bool AlertedStallAt1_5R          = false;
bool AlertedUnderperformingTrade = false;

//--- Per-trade log fields (captured at entry)
double   g_entry_price           = 0;
double   g_sl_price              = 0;
double   g_tp_price              = 0;
double   g_lot_size              = 0;
double   g_risk_amount           = 0;
double   g_atr14                 = 0;
double   g_atr5                  = 0;
double   g_atr_ratio             = 0;
double   g_adx14                 = 0;
double   g_di_plus               = 0;
double   g_di_minus              = 0;
double   g_ma_value              = 0;
double   g_candle_body_pct       = 0;
double   g_price_ma_dist_pips    = 0;
double   g_prev_candle_range_pct = 0;
datetime g_entry_time            = 0;
int      g_session_hour          = 0;
int      g_day_of_week           = 0;
string   g_direction             = "";

//--- Tick-by-tick MFE / MAE
double g_mfe_pips = 0;
double g_mae_pips = 0;

//--- Misc
int    loss_counter        = 0;
double equity_start        = 0;
bool   hit_break_even      = false;
bool   g_position_was_open = false;

enum TradeStatus { HOLDING, PARTIALLY_EXITED };
TradeStatus trade_status = HOLDING;

//+------------------------------------------------------------------+
//| Helpers                                                          |
//+------------------------------------------------------------------+
double PipSize()
{
   return (StringFind(_Symbol, "JPY") != -1) ? 0.01 : 0.0001;
}

string TimeframeToString(ENUM_TIMEFRAMES tf)
{
   switch(tf)
     {
      case PERIOD_M1:  return "M1";
      case PERIOD_M5:  return "M5";
      case PERIOD_M15: return "M15";
      case PERIOD_M30: return "M30";
      case PERIOD_H1:  return "H1";
      case PERIOD_H4:  return "H4";
      case PERIOD_D1:  return "D1";
      default:         return EnumToString(tf);
     }
}

//+------------------------------------------------------------------+
//| Reset all per-trade state after a close                          |
//+------------------------------------------------------------------+
void ResetTradeState()
{
   g_entry_price           = 0;
   g_sl_price              = 0;
   g_tp_price              = 0;
   g_lot_size              = 0;
   g_risk_amount           = 0;
   g_atr14                 = 0;
   g_atr5                  = 0;
   g_atr_ratio             = 0;
   g_adx14                 = 0;
   g_di_plus               = 0;
   g_di_minus              = 0;
   g_ma_value              = 0;
   g_candle_body_pct       = 0;
   g_price_ma_dist_pips    = 0;
   g_prev_candle_range_pct = 0;
   g_entry_time            = 0;
   g_session_hour          = 0;
   g_day_of_week           = 0;
   g_direction             = "";
   g_mfe_pips              = 0;
   g_mae_pips              = 0;
   BreakEvenApplied        = false;
   TrailingStopActivated   = false;
   PartialExitApplied      = false;
   hit_break_even          = false;
   trade_status            = HOLDING;
   max_price               = 0;
}

//+------------------------------------------------------------------+
//| Capture all entry-time context immediately after PositionOpen    |
//+------------------------------------------------------------------+
void CaptureEntryContext(ENUM_ORDER_TYPE signal, double price, double sl, double tp, double lot)
{
   double pip = PipSize();

   //--- MA value at entry
   double ma_buf[1];
   g_ma_value = (CopyBuffer(ExtHandle, 0, 0, 1, ma_buf) == 1) ? ma_buf[0] : 0;

   //--- ATR14 and ATR5
   double atr14_buf[1], atr5_buf[1];
   g_atr14 = (CopyBuffer(atrHandle,  0, 0, 1, atr14_buf) == 1) ? atr14_buf[0] : 0;
   g_atr5  = (CopyBuffer(atr5Handle, 0, 0, 1, atr5_buf)  == 1) ? atr5_buf[0]  : 0;
   g_atr_ratio = (g_atr14 > 0) ? g_atr5 / g_atr14 : 0;

   //--- ADX14, DI+, DI-  (buffers: 0=ADX, 1=+DI, 2=-DI)
   double adx_buf[1], dip_buf[1], dim_buf[1];
   g_adx14   = (CopyBuffer(adxHandle, 0, 0, 1, adx_buf) == 1) ? adx_buf[0] : 0;
   g_di_plus  = (CopyBuffer(adxHandle, 1, 0, 1, dip_buf) == 1) ? dip_buf[0] : 0;
   g_di_minus = (CopyBuffer(adxHandle, 2, 0, 1, dim_buf) == 1) ? dim_buf[0] : 0;

   //--- Candle metrics: rates[0]=signal candle, rates[1]=previous candle
   MqlRates rates[2];
   if(CopyRates(_Symbol, _Period, 0, 2, rates) == 2)
     {
      double body  = MathAbs(rates[0].close - rates[0].open);
      double range = rates[0].high - rates[0].low;
      g_candle_body_pct = (range > 0) ? (body / range) * 100.0 : 0;

      double prev_range_pips = (rates[1].high - rates[1].low) / pip;
      double atr14_pips      = (g_atr14 > 0) ? g_atr14 / pip : 1;
      g_prev_candle_range_pct = (atr14_pips > 0) ? (prev_range_pips / atr14_pips) * 100.0 : 0;
     }

   //--- Entry price to MA distance in pips
   g_price_ma_dist_pips = (g_ma_value > 0) ? MathAbs(price - g_ma_value) / pip : 0;

   //--- Session context at entry
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   g_session_hour = dt.hour;
   g_day_of_week  = dt.day_of_week;

   //--- Risk amount in account currency
   double tick_val  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pip_value = tick_val * (pip / tick_size);
   g_risk_amount    = MathAbs(price - sl) / pip * pip_value * lot;

   //--- Core entry fields
   g_entry_price = price;
   g_sl_price    = sl;
   g_tp_price    = tp;
   g_lot_size    = lot;
   g_entry_time  = TimeCurrent();
   g_direction   = (signal == ORDER_TYPE_BUY) ? "BUY" : "SELL";
   g_mfe_pips    = 0;
   g_mae_pips    = 0;
}

//+------------------------------------------------------------------+
//| Update MFE and MAE every tick while position is open             |
//+------------------------------------------------------------------+
void UpdateMFEMAE()
{
   if(!PositionSelect(_Symbol)) return;
   if((ulong)PositionGetInteger(POSITION_MAGIC) != MagicNumber) return;
   if(g_entry_price == 0) return;

   double pip   = PipSize();
   ENUM_POSITION_TYPE ptype = (ENUM_POSITION_TYPE)PositionGetInteger(POSITION_TYPE);

   double current = (ptype == POSITION_TYPE_BUY)
                    ? SymbolInfoDouble(_Symbol, SYMBOL_BID)
                    : SymbolInfoDouble(_Symbol, SYMBOL_ASK);

   double favorable = (ptype == POSITION_TYPE_BUY)
                      ? (current - g_entry_price) / pip
                      : (g_entry_price - current) / pip;
   double adverse   = (ptype == POSITION_TYPE_BUY)
                      ? (g_entry_price - current) / pip
                      : (current - g_entry_price) / pip;

   if(favorable > g_mfe_pips) g_mfe_pips = favorable;
   if(adverse   > g_mae_pips) g_mae_pips = adverse;
}

//+------------------------------------------------------------------+
//| Write one row to the CSV log in the MT5 common files folder      |
//+------------------------------------------------------------------+
void LogTradeToCSV(ulong deal_ticket)
{
   double   exit_price = HistoryDealGetDouble(deal_ticket, DEAL_PRICE);
   datetime exit_time  = (datetime)HistoryDealGetInteger(deal_ticket, DEAL_TIME);
   ENUM_DEAL_REASON reason = (ENUM_DEAL_REASON)HistoryDealGetInteger(deal_ticket, DEAL_REASON);

   double pip          = PipSize();
   double sl_dist_pips = (g_sl_price > 0) ? MathAbs(g_entry_price - g_sl_price) / pip : StopLossPips;
   double tp_dist_pips = (g_tp_price > 0) ? MathAbs(g_tp_price - g_entry_price) / pip : sl_dist_pips * 1.9;

   double price_move_pips = (g_direction == "BUY")
                            ? (exit_price - g_entry_price) / pip
                            : (g_entry_price - exit_price) / pip;

   double r_multiple = (sl_dist_pips > 0) ? price_move_pips / sl_dist_pips : 0;
   double rr_target  = (sl_dist_pips > 0) ? tp_dist_pips / sl_dist_pips    : 1.9;
   double mfe_pct_tp = (tp_dist_pips > 0) ? (g_mfe_pips / tp_dist_pips) * 100.0 : 0;
   double mae_pct_sl = (sl_dist_pips > 0) ? (g_mae_pips / sl_dist_pips) * 100.0 : 0;
   double duration_h = (double)(exit_time - g_entry_time) / 3600.0;

   string result_str;
   if     (r_multiple >  0.05) result_str = "WIN";
   else if(r_multiple < -0.05) result_str = "LOSS";
   else                         result_str = "BE";

   string close_reason;
   switch(reason)
     {
      case DEAL_REASON_TP:     close_reason = "TP";                                              break;
      case DEAL_REASON_SL:     close_reason = "SL";                                              break;
      case DEAL_REASON_EXPERT: close_reason = TrailingStopActivated ? "TRAILING" : "EA_CLOSE";   break;
      case DEAL_REASON_CLIENT: close_reason = "MANUAL";                                           break;
      default:                 close_reason = "OTHER";                                            break;
     }

   //--- Open CSV in common files folder (FILE_READ|FILE_WRITE does not truncate)
   string csv_file = "trade_log_" + _Symbol + ".csv";
   int fh = FileOpen(csv_file, FILE_READ | FILE_WRITE | FILE_ANSI | FILE_COMMON);
   if(fh == INVALID_HANDLE)
     {
      // File doesn't exist yet — create it
      fh = FileOpen(csv_file, FILE_WRITE | FILE_ANSI | FILE_COMMON);
      if(fh == INVALID_HANDLE)
        {
         Print("LogTradeToCSV: FileOpen failed, error=", GetLastError());
         return;
        }
     }

   FileSeek(fh, 0, SEEK_END);
   long file_size = FileTell(fh);

   //--- Write header if file is empty
   if(file_size == 0)
     {
      FileWriteString(fh,
                      "trade_id,symbol,timeframe,direction,"
                      "entry_time,exit_time,duration_hours,"
                      "entry_price,sl_price,tp_price,exit_price,"
                      "lot_size,risk_amount,rr_target,r_multiple,"
                      "result,close_reason,"
                      "mfe_pips,mae_pips,mfe_pct_tp,mae_pct_sl,"
                      "ma_value,atr14,atr5,atr_ratio,"
                      "adx14,di_plus,di_minus,"
                      "session_hour,day_of_week,"
                      "candle_body_pct,price_ma_distance_pips,prev_candle_range_pct,"
                      "source\n");
     }

   //--- Build and write data row
   string row = StringFormat(
                   "%I64u,%s,%s,%s,"
                   "%s,%s,%.4f,"
                   "%s,%s,%s,%s,"
                   "%.2f,%.2f,%.4f,%.4f,"
                   "%s,%s,"
                   "%.2f,%.2f,%.2f,%.2f,"
                   "%s,%.5f,%.5f,%.4f,"
                   "%.2f,%.2f,%.2f,"
                   "%d,%d,"
                   "%.2f,%.2f,%.2f,"
                   "%s\n",
                   deal_ticket,
                   _Symbol,
                   TimeframeToString(_Period),
                   g_direction,
                   TimeToString(g_entry_time, TIME_DATE | TIME_MINUTES | TIME_SECONDS),
                   TimeToString(exit_time,    TIME_DATE | TIME_MINUTES | TIME_SECONDS),
                   duration_h,
                   DoubleToString(g_entry_price, _Digits),
                   DoubleToString(g_sl_price,    _Digits),
                   DoubleToString(g_tp_price,    _Digits),
                   DoubleToString(exit_price,    _Digits),
                   g_lot_size,
                   g_risk_amount,
                   rr_target,
                   r_multiple,
                   result_str,
                   close_reason,
                   g_mfe_pips, g_mae_pips, mfe_pct_tp, mae_pct_sl,
                   DoubleToString(g_ma_value, _Digits),
                   g_atr14, g_atr5, g_atr_ratio,
                   g_adx14, g_di_plus, g_di_minus,
                   g_session_hour, g_day_of_week,
                   g_candle_body_pct, g_price_ma_dist_pips, g_prev_candle_range_pct,
                   "BACKTEST"
                );

   FileWriteString(fh, row);
   FileClose(fh);

   Print("Trade logged | ticket:", deal_ticket,
         " | ", g_direction,
         " | result:", result_str,
         " | R:", DoubleToString(r_multiple, 2),
         " | exit:", DoubleToString(exit_price, _Digits));
}

//+------------------------------------------------------------------+
//| Expert initialisation                                            |
//+------------------------------------------------------------------+
int OnInit()
{
   ExtHandle  = iMA(_Symbol, _Period, MovingPeriod, MovingShift, MODE_SMA, PRICE_CLOSE);
   atrHandle  = iATR(_Symbol, _Period, 14);
   atr5Handle = iATR(_Symbol, _Period, 5);
   adxHandle  = iADX(_Symbol, _Period, 14);

   if(ExtHandle  == INVALID_HANDLE ||
      atrHandle  == INVALID_HANDLE ||
      atr5Handle == INVALID_HANDLE ||
      adxHandle  == INVALID_HANDLE)
     {
      Print("Indicator initialization failed");
      return INIT_FAILED;
     }

   ChartIndicatorAdd(0, 0, ExtHandle);
   ExtTrade.SetExpertMagicNumber(MagicNumber);
   equity_start = AccountInfoDouble(ACCOUNT_EQUITY);
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   IndicatorRelease(ExtHandle);
   IndicatorRelease(atrHandle);
   IndicatorRelease(atr5Handle);
   IndicatorRelease(adxHandle);
}

//+------------------------------------------------------------------+
bool IsWithinSession()
{
   MqlDateTime dt;
   TimeToStruct(TimeCurrent(), dt);
   if(dt.day_of_week < 2 || dt.day_of_week > 4) return false;
   return (dt.hour >= SessionStartHour && dt.hour < SessionEndHour);
}

bool IsATRValid()
{
   double atr[1];
   if(CopyBuffer(atrHandle, 0, 0, 1, atr) != 1) return false;
   return (atr[0] / PipSize() >= ATRMinimumPips);
}

//+------------------------------------------------------------------+
double CalculatePortfolioAdjustedLot(double stoploss_pips, ENUM_ORDER_TYPE order_type)
{
   double equity         = AccountInfoDouble(ACCOUNT_EQUITY);
   double max_risk_money = equity * MaximumRisk;
   double active_risk    = 0.0;

   for(int i = 0; i < PositionsTotal(); i++)
     {
      if(!PositionGetTicket(i)) continue;
      if((ulong)PositionGetInteger(POSITION_MAGIC) != MagicNumber) continue;
      string symb      = PositionGetString(POSITION_SYMBOL);
      double op        = PositionGetDouble(POSITION_PRICE_OPEN);
      double sl        = PositionGetDouble(POSITION_SL);
      double vol       = PositionGetDouble(POSITION_VOLUME);
      if(sl == 0) continue;

      double spip      = (StringFind(symb, "JPY") != -1) ? 0.01 : 0.0001;
      double tick_val  = SymbolInfoDouble(symb, SYMBOL_TRADE_TICK_VALUE);
      double tick_size = SymbolInfoDouble(symb, SYMBOL_TRADE_TICK_SIZE);
      double pv        = tick_val * (spip / tick_size);
      active_risk     += MathAbs(op - sl) / spip * pv * vol;
     }

   double remaining = MathMax(0.0, max_risk_money - active_risk);
   if(remaining <= 0.0) return 0.0;

   double pip       = PipSize();
   double tick_val  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_size = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   double pv        = tick_val * (pip / tick_size);
   double raw_lot   = remaining / (stoploss_pips * pv);

   double step   = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double minvol = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double maxvol = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   raw_lot = step * MathFloor(raw_lot / step);
   return NormalizeDouble(MathMax(minvol, MathMin(raw_lot, maxvol)), 2);
}

//+------------------------------------------------------------------+
void CheckForOpen()
{
   if(!IsWithinSession() || !IsATRValid()) return;

   MqlRates rt[2];
   if(CopyRates(_Symbol, _Period, 0, 2, rt) != 2 || rt[1].tick_volume > 1) return;

   double ma[1];
   if(CopyBuffer(ExtHandle, 0, 0, 1, ma) != 1) return;

   bool isBuy  = rt[0].open < ma[0] && rt[0].close > ma[0];
   bool isSell = rt[0].open > ma[0] && rt[0].close < ma[0];

   ENUM_ORDER_TYPE signal = isBuy ? ORDER_TYPE_BUY : isSell ? ORDER_TYPE_SELL : (ENUM_ORDER_TYPE)-1;
   if(signal == (ENUM_ORDER_TYPE)-1) return;

   double pip   = PipSize();
   double price = SymbolInfoDouble(_Symbol, signal == ORDER_TYPE_BUY ? SYMBOL_ASK : SYMBOL_BID);
   double sl    = (signal == ORDER_TYPE_BUY) ? price - StopLossPips * pip       : price + StopLossPips * pip;
   double tp    = (signal == ORDER_TYPE_BUY) ? price + StopLossPips * 1.9 * pip : price - StopLossPips * 1.9 * pip;
   double lot   = CalculatePortfolioAdjustedLot(StopLossPips, signal);

   if(lot <= 0) return;

   if(ExtTrade.PositionOpen(_Symbol, signal, lot, price, sl, tp, ""))
      CaptureEntryContext(signal, price, sl, tp, lot);
}

//+------------------------------------------------------------------+
void ApplyTrailingStop()
{
   // Placeholder
}

void CheckTradeAlerts()
{
   // Placeholder
}

//+------------------------------------------------------------------+
//| Scan history for the most recent OUT deal on this symbol/magic   |
//+------------------------------------------------------------------+
ulong FindLastCloseDeal()
{
   HistorySelect(0, TimeCurrent());
   int total = HistoryDealsTotal();
   for(int i = total - 1; i >= 0; i--)
     {
      ulong ticket = HistoryDealGetTicket(i);
      if(ticket == 0) continue;
      if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
      if((ulong)HistoryDealGetInteger(ticket, DEAL_MAGIC) != MagicNumber) continue;
      ENUM_DEAL_ENTRY de = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(ticket, DEAL_ENTRY);
      if(de != DEAL_ENTRY_OUT && de != DEAL_ENTRY_INOUT) continue;
      return ticket;
     }
   return 0;
}

//+------------------------------------------------------------------+
void OnTick()
{
   bool position_open = PositionSelect(_Symbol) &&
                        (ulong)PositionGetInteger(POSITION_MAGIC) == MagicNumber;

   //--- Backtest fallback: OnTradeTransaction may not fire in Strategy Tester.
   //--- Detect open→closed transition and log the trade from history.
   //--- g_entry_price guard prevents double-logging: if OnTradeTransaction already
   //--- handled this close it will have called ResetTradeState() which zeros g_entry_price.
   if(g_position_was_open && !position_open && g_entry_price != 0)
     {
      ulong deal_ticket = FindLastCloseDeal();
      if(deal_ticket > 0)
        {
         LogTradeToCSV(deal_ticket);
         ResetTradeState();
        }
     }

   g_position_was_open = position_open;

   if(position_open)
     {
      UpdateMFEMAE();
      ApplyTrailingStop();
      CheckTradeAlerts();
     }
   else
     {
      CheckForOpen();
     }
}

//+------------------------------------------------------------------+
//| Fires on every deal — detects position closes and triggers log   |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction &trans,
                        const MqlTradeRequest     &request,
                        const MqlTradeResult      &result)
{
   if(trans.type   != TRADE_TRANSACTION_DEAL_ADD) return;
   if(trans.symbol != _Symbol)                    return;

   HistorySelect(0, TimeCurrent());
   if(!HistoryDealSelect(trans.deal)) return;
   if((ulong)HistoryDealGetInteger(trans.deal, DEAL_MAGIC) != MagicNumber) return;

   ENUM_DEAL_ENTRY de = (ENUM_DEAL_ENTRY)HistoryDealGetInteger(trans.deal, DEAL_ENTRY);
   if(de != DEAL_ENTRY_OUT && de != DEAL_ENTRY_INOUT) return;

   //--- Guard: if entry state is already zeroed, OnTick fallback already logged this close.
   if(g_entry_price == 0) return;

   LogTradeToCSV(trans.deal);
   ResetTradeState();
}
