import psycopg2

DB_URI = "postgres://tsdbadmin:lzpxf5ekb2md3osf@o7fwchs8z2.eqklalx668.tsdb.cloud.timescale.com:34210/tsdb?sslmode=require"

def setup_database():
    """Creates tables and continuous aggregates in TimescaleDB (Run only once)."""
    try:
        conn = psycopg2.connect(DB_URI)
        conn.autocommit = True
        cur = conn.cursor()

        print("📌 Dropping existing tables if they exist...")
        cur.execute("DROP TABLE IF EXISTS stock_ticks CASCADE;")
        cur.execute("DROP TABLE IF EXISTS tbl_ohlc_fifteen_input CASCADE;")
        cur.execute("DROP TABLE IF EXISTS tbl_ohlc_fifteen_output CASCADE;")

        print("✅ Creating tick data table...")
        cur.execute("""
            CREATE TABLE stock_ticks (
                symbol TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                price DOUBLE PRECISION,
                PRIMARY KEY (symbol, timestamp)
            );
        """)

        print("✅ Converting tick data table into a hypertable...")
        cur.execute("SELECT create_hypertable('stock_ticks', 'timestamp');")

        print("✅ Creating index on (symbol, timestamp DESC) for faster queries...")
        cur.execute("CREATE INDEX stock_ticks_symbol_idx ON stock_ticks (symbol, timestamp DESC);")

        print("✅ Creating OHLC input table (for Flask app)...")
        cur.execute("""
            CREATE TABLE tbl_ohlc_fifteen_input (
                token INT NOT NULL,
                symbol TEXT NOT NULL,
                open DOUBLE PRECISION,
                close DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                created TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (created, token) -- 🔹 Fix: Prevent SERIAL conflicts
            );
        """)
        cur.execute("SELECT create_hypertable('tbl_ohlc_fifteen_input', 'created');")

        print("✅ Creating OHLC output table (for Flask app)...")
        cur.execute("""
            CREATE TABLE tbl_ohlc_fifteen_output (
                token INT NOT NULL,
                symbol TEXT,
                open DOUBLE PRECISION,
                close DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                created TIMESTAMPTZ,
                atr DOUBLE PRECISION,
                atr_trail_stop_loss DOUBLE PRECISION,
                dc_upper DOUBLE PRECISION,
                dc_lower DOUBLE PRECISION,
                dc_mid DOUBLE PRECISION,
                fh_price DOUBLE PRECISION,
                fl_price DOUBLE PRECISION,
                fh_status BOOL,
                fl_status BOOL,
                sh_price DOUBLE PRECISION,
                sl_price DOUBLE PRECISION,
                sh_status BOOL,
                sl_status BOOL
            );
        """)
        
        print("✅ Converting OHLC output table into a hypertable...")
        cur.execute("SELECT create_hypertable('tbl_ohlc_fifteen_output', 'created');")  # 🔹 Fix: Convert to hypertable

        print("✅ Creating continuous aggregates for OHLC data...")
        cur.execute("""
            CREATE MATERIALIZED VIEW stock_ohlc_15min
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('15 minutes', timestamp) AS bucket,
                symbol,
                first(price, timestamp) AS open,
                max(price) AS high,
                min(price) AS low,
                last(price, timestamp) AS close
            FROM stock_ticks
            GROUP BY bucket, symbol;
        """)

        print("✅ Setting auto-refresh policies...")
        cur.execute("""
            SELECT add_continuous_aggregate_policy('stock_ohlc_15min',
                start_offset => INTERVAL '31 minutes',  -- 🔹 Fix: Must cover at least two buckets
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '15 minutes');
        """)

        print("🎉 TimescaleDB setup completed successfully!")

    except Exception as e:
        print("❌ Error setting up database:", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    setup_database()
