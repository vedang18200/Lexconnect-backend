#!/bin/bash

echo "🔄 Running database migrations..."

# Run migrations with error output
if alembic upgrade head; then
    echo "✅ Migrations complete."
else
    echo "❌ Migration failed! Trying again in 5 seconds..."
    sleep 5
    if alembic upgrade head; then
        echo "✅ Migrations complete (retry successful)."
    else
        echo "❌ Migration failed after retry. Exiting."
        exit 1
    fi
fi

echo "✅ Starting application..."
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}
