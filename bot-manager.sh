#!/bin/bash
# Nutrition Bot Manager Script
# Usage: ./bot-manager.sh [start|stop|restart|status|logs]

BOT_DIR="/data/.openclaw/workspace/nutrition_bot_v2"
PID_FILE="$BOT_DIR/bot.pid"
LOG_FILE="$BOT_DIR/bot.log"

check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            echo "✅ Nutrition Bot is RUNNING (PID: $PID)"
            return 0
        else
            echo "❌ Nutrition Bot is STOPPED (stale PID file)"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        # Check if running without PID file
        PID=$(pgrep -f "python3 $BOT_DIR/main.py" | head -1)
        if [ -n "$PID" ]; then
            echo "$PID" > "$PID_FILE"
            echo "✅ Nutrition Bot is RUNNING (PID: $PID) - PID file recreated"
            return 0
        fi
        echo "❌ Nutrition Bot is STOPPED"
        return 1
    fi
}

start_bot() {
    if check_status > /dev/null 2>&1; then
        echo "Bot is already running!"
        return 0
    fi
    
    echo "🚀 Starting Nutrition Bot..."
    cd "$BOT_DIR"
    
    # Start bot in background with logging
    nohup python3 main.py >> "$LOG_FILE" 2>&1 &
    PID=$!
    
    # Save PID
    echo $PID > "$PID_FILE"
    
    # Wait a moment and check if it's still running
    sleep 2
    if kill -0 $PID 2>/dev/null; then
        echo "✅ Bot started successfully (PID: $PID)"
        echo "📊 Logs: tail -f $LOG_FILE"
    else
        echo "❌ Failed to start bot"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_bot() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "🛑 Stopping Nutrition Bot (PID: $PID)..."
        kill "$PID" 2>/dev/null
        sleep 2
        
        # Force kill if still running
        if kill -0 "$PID" 2>/dev/null; then
            kill -9 "$PID" 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Bot stopped"
    else
        # Try to find and kill anyway
        PID=$(pgrep -f "python3 $BOT_DIR/main.py" | head -1)
        if [ -n "$PID" ]; then
            echo "🛑 Stopping Nutrition Bot (PID: $PID)..."
            kill "$PID" 2>/dev/null
            sleep 1
            kill -9 "$PID" 2>/dev/null
            echo "✅ Bot stopped"
        else
            echo "Bot is not running"
        fi
    fi
}

restart_bot() {
    stop_bot
    sleep 2
    start_bot
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📊 Showing last 50 lines of logs:"
        tail -n 50 "$LOG_FILE"
    else
        echo "No log file found"
    fi
}

# Main
case "${1:-status}" in
    start)
        start_bot
        ;;
    stop)
        stop_bot
        ;;
    restart)
        restart_bot
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status|logs]"
        check_status
        ;;
esac
