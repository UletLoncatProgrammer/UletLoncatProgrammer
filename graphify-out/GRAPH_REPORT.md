# Graph Report - .  (2026-07-24)

## Corpus Check
- Corpus is ~2,064 words - fits in a single context window. You may not need a graph.

## Summary
- 55 nodes · 96 edges · 9 communities (6 shown, 3 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 45,000 input · 8,500 output

## Community Hubs (Navigation)
- Stock Alert Engine
- README Documentation
- Telegram Bot Core
- CI Workflows & Secrets
- Python Dependencies
- RSI & Quote Tool
- Telegram Notification Module
- Claude Integration
- Dedupe State Tracking

## God Nodes (most connected - your core abstractions)
1. `README.md (project overview / setup guide)` - 18 edges
2. `main()` - 9 edges
3. `main()` - 8 edges
4. `Stock Alert Automation (workflow)` - 8 edges
5. `Telegram Assistant Bot (workflow)` - 8 edges
6. `requirements.txt (Python dependency manifest)` - 8 edges
7. `analyze()` - 6 edges
8. `fetch_history()` - 5 edges
9. `compute_rsi()` - 5 edges
10. `load_config()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `send_message()`  [EXTRACTED]
  stock_alert.py → telegram_notif.py
- `get_stock_quote()` --calls--> `fetch_history()`  [EXTRACTED]
  telegram_bot.py → stock_alert.py
- `Stock Alert Automation (workflow)` --shares_data_with--> `alert_state.json (alert dedupe state)`  [EXTRACTED]
  .github/workflows/alert.yml → README.md
- `Stock Alert Automation (workflow)` --references--> `config.json (stocks, targets, thresholds)`  [EXTRACTED]
  .github/workflows/alert.yml → README.md
- `Stock Alert Automation (workflow)` --references--> `requirements.txt (Python dependency manifest)`  [EXTRACTED]
  .github/workflows/alert.yml → requirements.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Telegram credentials shared by both scheduled workflows** — secret_telegram_bot_token, secret_telegram_chat_id, github_workflows_alert_workflow, github_workflows_bot_workflow [EXTRACTED 1.00]
- **Run-then-commit-state automation pattern** — github_workflows_alert_workflow, github_workflows_bot_workflow, alert_state_json, telegram_offset_json [INFERRED 0.85]
- **Claude-backed Telegram Q&A flow with live stock data tool** — telegram_bot, secret_anthropic_api_key, readme_qa_bot, readme_get_stock_quote_tool [EXTRACTED 1.00]

## Communities (9 total, 3 thin omitted)

### Community 0 - "Stock Alert Engine"
Cohesion: 0.29
Nodes (12): DataFrame, analyze(), dedupe_alerts(), fetch_history(), load_config(), load_state(), main(), Analyzes a stock watchlist and sends Telegram alerts on price/technical triggers (+4 more)

### Community 1 - "README Documentation"
Cohesion: 0.22
Nodes (9): get_stock_quote tool (live price/RSI lookup for Claude), Jakarta (WIB) trading-hours schedule, Moving-average crossover (golden/death cross), Price target (buy_below / sell_above), Telegram Q&A bot (Claude-backed), README.md (project overview / setup guide), RSI overbought/oversold alert condition, Volatility spike alert condition (+1 more)

### Community 2 - "Telegram Bot Core"
Cohesion: 0.39
Nodes (8): fetch_updates(), is_addressed_to_bot(), load_offset(), main(), Polls Telegram for new messages and answers them with Claude, including live sto, save_offset(), send_message(), strip_mention()

### Community 3 - "CI Workflows & Secrets"
Cohesion: 0.38
Nodes (7): alert_state.json (alert dedupe state), config.json (stocks, targets, thresholds), Stock Alert Automation (workflow), Telegram Assistant Bot (workflow), ANTHROPIC_API_KEY (secret), TELEGRAM_BOT_TOKEN (secret), TELEGRAM_CHAT_ID (secret)

### Community 4 - "Python Dependencies"
Cohesion: 0.33
Nodes (6): anthropic (>=0.40.0), numpy (>=1.24.0), pandas (>=2.0.0), requests (>=2.31.0), requirements.txt (Python dependency manifest), yfinance (>=0.2.40)

### Community 5 - "RSI & Quote Tool"
Cohesion: 0.50
Nodes (4): Series, compute_rsi(), get_stock_quote(), run_tool()

## Knowledge Gaps
- **10 isolated node(s):** `ANTHROPIC_API_KEY (secret)`, `yfinance (>=0.2.40)`, `pandas (>=2.0.0)`, `numpy (>=1.24.0)`, `requests (>=2.31.0)` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `README.md (project overview / setup guide)` connect `README Documentation` to `Stock Alert Engine`, `Telegram Bot Core`, `CI Workflows & Secrets`, `Python Dependencies`, `Telegram Notification Module`, `Dedupe State Tracking`?**
  _High betweenness centrality (0.446) - this node is a cross-community bridge._
- **Why does `requirements.txt (Python dependency manifest)` connect `Python Dependencies` to `README Documentation`, `CI Workflows & Secrets`?**
  _High betweenness centrality (0.178) - this node is a cross-community bridge._
- **Why does `Telegram Assistant Bot (workflow)` connect `CI Workflows & Secrets` to `Dedupe State Tracking`, `README Documentation`, `Telegram Bot Core`, `Python Dependencies`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **What connects `ANTHROPIC_API_KEY (secret)`, `yfinance (>=0.2.40)`, `pandas (>=2.0.0)` to the rest of the system?**
  _10 weakly-connected nodes found - possible documentation gaps or missing edges._