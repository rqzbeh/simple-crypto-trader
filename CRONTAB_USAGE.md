# Crontab Usage Guide - Smart Trade Tracking

## Overview

This trading bot is designed to work perfectly with crontab/scheduled execution. It uses a **smart queuing system** that tracks trades across multiple runs and only trains on completed trades.

## How It Works

### Trade Lifecycle

```
Run 1 (0h):  Generate signal → Log trade → Status: 'open'
Run 2 (2h):  Check trade → Entry reached? → Status: 'queued' or train if completed
Run 3 (4h):  Final check → Status: 'completed'/'stopped'/'checked' → Train
```

### Smart Queuing System

The system has **THREE distinct phases**:

#### Phase 1: Entry Not Reached Yet (Status: 'queued')
```
Time: 0-4h
Check: Has entry price been reached?
- NO → Keep in queue for next run
- YES → Move to Phase 2
Action: Wait, do NOT train yet
```

#### Phase 2: Entry Reached, Trade In Progress (Status: 'queued')
```
Time: 0-4h (after entry)
Check: Has TP or SL been hit?
- NO → Keep in queue for next run
- YES → Move to Phase 3
Action: Wait, do NOT train yet
```

#### Phase 3: Trade Completed (Status: 'completed'/'stopped'/'checked')
```
Conditions for completion:
1. TP hit → Status: 'completed', train with success
2. SL hit → Status: 'stopped', train with SL failure
3. 4h elapsed → Status: 'checked', train with partial result
Action: TRAIN on completed trade
```

## Crontab Configuration

### Recommended: Every 2 Hours

```bash
# Edit crontab
crontab -e

# Add this line (runs every 2 hours)
0 */2 * * * cd /path/to/simple-crypto-trader && /usr/bin/python3 main.py >> logs/trader.log 2>&1
```

**Why 2 hours?**
- Gives trades time to develop
- Checks progress mid-window
- Still respects 4h maximum window
- Efficient balance between responsiveness and server load

### Alternative: Every Hour

```bash
# More frequent checks (more responsive but more API calls)
0 * * * * cd /path/to/simple-crypto-trader && /usr/bin/python3 main.py >> logs/trader.log 2>&1
```

### Alternative: Every 4 Hours

```bash
# Minimal checks (less API usage but less granular)
0 */4 * * * cd /path/to/simple-crypto-trader && /usr/bin/python3 main.py >> logs/trader.log 2>&1
```

## Data Persistence

### Files That Persist Across Runs

1. **`trade_log.json`** - All trade records
   - Stores open, queued, and completed trades
   - Updated every run
   - Never deleted (historical record)

2. **`learning_state.json`** - ML learning data
   - Performance history (last 50 trades)
   - Indicator performance metrics
   - Precision metrics (TP/SL/Entry accuracy)
   - Strategy adjustments
   - **NEW**: Automatically saved after each trade verification

3. **`daily_risk.json`** - Daily risk tracking
   - Resets daily
   - Prevents overtrading

## Example Timeline

### Scenario: 2-Hour Crontab

```
00:00 - Script Run #1
  ├─ Generate BTC LONG signal
  ├─ Entry: $50,000
  ├─ SL: $49,500 (1%)
  ├─ TP: $51,500 (3%)
  └─ Log trade with status: 'open'

02:00 - Script Run #2
  ├─ Check trade outcomes
  ├─ BTC current: $49,800 (entry not reached yet)
  ├─ Status: 'queued' (waiting for entry)
  └─ NO TRAINING (incomplete)

04:00 - Script Run #3
  ├─ Check trade outcomes
  ├─ BTC low: $49,900 (entry reached!)
  ├─ BTC current: $50,300 (in profit, but no TP/SL hit)
  ├─ Time elapsed: 4h (MAX reached)
  ├─ Status: 'checked' (partial result)
  └─ ✅ TRAIN: "tp_not_reached" (direction correct, TP too far)
```

### Scenario: Trade Completes Early

```
00:00 - Script Run #1
  ├─ Generate ETH SHORT signal
  ├─ Entry: $3,000
  ├─ SL: $3,024 (0.8%)
  ├─ TP: $2,928 (2.4%)
  └─ Log trade with status: 'open'

02:00 - Script Run #2
  ├─ Check trade outcomes
  ├─ ETH high: $3,010 (entry reached)
  ├─ ETH low: $2,920 (TP HIT! 🎯)
  ├─ Status: 'completed'
  └─ ✅ TRAIN: SUCCESS (perfect trade)

04:00 - Script Run #3
  ├─ Trade already verified
  └─ Skip (already trained)
```

## Verification Logic

### What Gets Checked Each Run

```python
for each trade in trade_log.json:
    if status in ['open', 'queued']:
        time_elapsed = now - entry_time
        
        if time_elapsed < 2h:
            # Too early, skip
            continue
        
        # Fetch intraday price data
        high_price, low_price, current_price = get_prices()
        
        # Phase 1: Check if entry reached
        if entry_not_reached:
            if time_elapsed >= 4h:
                # Max time reached
                status = 'entry_not_reached'
                train(failure='entry_not_reached')
            else:
                # Keep waiting
                status = 'queued'
        
        # Phase 2: Check if TP/SL hit
        elif entry_reached:
            if tp_hit:
                status = 'completed'
                train(success=True)
            elif sl_hit:
                status = 'stopped'
                train(failure='sl_hit')
            elif time_elapsed >= 4h:
                # Max time reached, partial result
                status = 'checked'
                train(failure='tp_not_reached' or 'wrong_direction')
            else:
                # Keep waiting
                status = 'queued'
```

## Benefits of This System

### ✅ Accurate Training
- Only trains on completed trades
- Knows exact TP/SL hits from intraday data
- No assumptions about partial results (unless max time reached)

### ✅ Efficient Resource Usage
- Works with any crontab schedule (1h, 2h, 4h)
- Doesn't waste API calls on early checks
- Queues trades automatically

### ✅ Persistent Learning
- `learning_state.json` persists across runs
- Accumulates knowledge over days/weeks
- Never loses training progress

### ✅ Flexible Timing
- Doesn't require exact 4h intervals
- Handles irregular schedules
- Respects maximum 4h window

## Monitoring

### Check Learning Progress

```bash
# View recent trade results
cat trade_log.json | jq '.[-10:] | .[] | {symbol, direction, status, actual_profit, failure_reason}'

# View learning state
cat learning_state.json | jq '{
  total_trades: .precision_metrics.total_trades,
  adjustments: .strategy_adjustments,
  failures: {
    entry_not_reached: .precision_metrics.entry_not_reached_count,
    sl_hit_early: .precision_metrics.sl_hit_early_count,
    tp_too_far: .precision_metrics.tp_too_far_count,
    wrong_direction: .precision_metrics.wrong_direction_count
  }
}'
```

### Log Output

```bash
# When script runs
📚 Loaded learning state: 45 trades, 45 total verified
[OK] Verified 3 trade outcomes and updated learning system
[⏳] 2 trades still in queue (waiting for entry or completion)

📊 Strategy Auto-Adjusted:
   Entry Adjustment: 0.85x (Entry timing acceptable)
   SL Adjustment: 1.15x (SL hit too often, widening stops)
   TP Adjustment: 0.75x (TPs slightly high, adjusting)
```

## Troubleshooting

### Issue: Trades stuck in queue

**Symptom**: Many trades showing status 'queued' for > 4 hours

**Solution**: This shouldn't happen. The system auto-closes trades at 4h. Check:
```bash
# Find old queued trades
cat trade_log.json | jq '.[] | select(.status == "queued") | {symbol, timestamp, status}'
```

### Issue: Learning state not persisting

**Symptom**: Adjustments reset each run

**Solution**: Check file permissions
```bash
# Ensure bot can write to learning_state.json
ls -la learning_state.json
chmod 644 learning_state.json
```

### Issue: Too many API calls

**Symptom**: Rate limit errors from Yahoo Finance

**Solution**: Increase crontab interval
```bash
# Change from 1h to 2h intervals
0 */2 * * * ...
```

## Best Practices

1. **Use 2h intervals** - Optimal balance
2. **Monitor logs** - Check for errors regularly
3. **Backup data** - Copy .json files weekly
4. **Don't edit manually** - Let the system learn
5. **Review adjustments** - Check learning_state.json monthly

## Summary

The bot is **fully compatible with crontab** execution:

✅ Tracks trades across multiple runs
✅ Only trains on completed trades
✅ Respects 4h maximum window
✅ Persists learning data
✅ Works with any schedule (1h/2h/4h)
✅ Handles entry/TP/SL verification correctly

No manual intervention needed - just set up crontab and let it run! 🚀
