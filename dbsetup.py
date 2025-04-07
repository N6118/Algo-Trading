import psycopg2

DB_URI = "postgresql://postgres:password@localhost:5432/theostock"

def setup_database():
    """Creates tables and continuous aggregates in TimescaleDB (Run only once)."""
    try:
        conn = psycopg2.connect(DB_URI)
        conn.autocommit = True
        cur = conn.cursor()

        print("Dropping existing tables if they exist...")
        cur.execute("DROP TABLE IF EXISTS stock_ticks CASCADE;")
        cur.execute("DROP TABLE IF EXISTS tbl_ohlc_fifteen_input CASCADE;")
        cur.execute("DROP TABLE IF EXISTS tbl_ohlc_fifteen_output CASCADE;")
        cur.execute("DROP TABLE IF EXISTS tbl_market_logtime CASCADE;")
        cur.execute("DROP TABLE IF EXISTS ibkr_contracts CASCADE;")

        print("✅ Creating tick data table...")
        cur.execute("""
            CREATE TABLE stock_ticks (
                token INT NOT NULL,  -- ✅ IBKR conId (token)
                symbol TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                price DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                PRIMARY KEY (token, timestamp)  -- ✅ Optimized indexing
            );
        """)

        print("✅ Converting tick data table into a hypertable...")
        cur.execute("""
            SELECT create_hypertable('stock_ticks', 'timestamp', 
                chunk_time_interval => INTERVAL '1 day');
        """)

        print("✅ Creating indexes on stock_ticks for faster queries...")
        cur.execute("CREATE INDEX stock_ticks_token_idx ON stock_ticks (token, timestamp DESC);")
        cur.execute("CREATE INDEX stock_ticks_symbol_idx ON stock_ticks (symbol, timestamp DESC);")
        
        print("✅ Setting up compression policy for stock_ticks...")
        cur.execute("""
            ALTER TABLE stock_ticks SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'token,symbol'
            );
        """)
        
        cur.execute("""
            SELECT add_compression_policy('stock_ticks', 
                compress_after => INTERVAL '7 days');
        """)
        
        print("✅ Setting up retention policy for stock_ticks...")
        cur.execute("""
            SELECT add_retention_policy('stock_ticks', 
                drop_after => INTERVAL '90 days');
        """)

        print("✅ Creating OHLC input table...")
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
                PRIMARY KEY (created, token)
            );
        """)
        
        cur.execute("""
            SELECT create_hypertable('tbl_ohlc_fifteen_input', 'created',
                chunk_time_interval => INTERVAL '1 day');
        """)
        
        cur.execute("CREATE INDEX idx_ohlc_input_symbol ON tbl_ohlc_fifteen_input (symbol, created DESC);")

        print("✅ Creating OHLC output table (for Flask app)...")
        cur.execute("""
            CREATE TABLE tbl_ohlc_fifteen_output (
                id SERIAL,
                token INT NOT NULL,
                symbol TEXT,
                open DOUBLE PRECISION,
                close DOUBLE PRECISION,
                high DOUBLE PRECISION,
                low DOUBLE PRECISION,
                volume DOUBLE PRECISION,
                created TIMESTAMPTZ NOT NULL,
                atr DOUBLE PRECISION,
                atr_trail_stop_loss DOUBLE PRECISION,
                dc_upper DOUBLE PRECISION,
                dc_lower DOUBLE PRECISION,
                dc_mid DOUBLE PRECISION,
                fh_price DOUBLE PRECISION,
                fl_price DOUBLE PRECISION,
                fh_status BOOLEAN,
                fl_status BOOLEAN,
                sh_price DOUBLE PRECISION,
                sl_price DOUBLE PRECISION,
                sh_status BOOLEAN,
                sl_status BOOLEAN,
                lowestfrom1stlow INTEGER,
                highestfrom1sthigh INTEGER,
                fl_dbg INTEGER,
                fh_dbg INTEGER,
                dpivot DOUBLE PRECISION,
                ds1 DOUBLE PRECISION,
                ds2 DOUBLE PRECISION,
                ds3 DOUBLE PRECISION,
                ds4 DOUBLE PRECISION,
                ds5 DOUBLE PRECISION,
                dr1 DOUBLE PRECISION,
                dr2 DOUBLE PRECISION,
                dr3 DOUBLE PRECISION,
                dr4 DOUBLE PRECISION,
                dr5 DOUBLE PRECISION,
                wpivot DOUBLE PRECISION,
                ws1 DOUBLE PRECISION,
                ws2 DOUBLE PRECISION,
                ws3 DOUBLE PRECISION,
                ws4 DOUBLE PRECISION,
                ws5 DOUBLE PRECISION,
                wr1 DOUBLE PRECISION,
                wr2 DOUBLE PRECISION,
                wr3 DOUBLE PRECISION,
                wr4 DOUBLE PRECISION,
                wr5 DOUBLE PRECISION,
                mpivot DOUBLE PRECISION,
                ms1 DOUBLE PRECISION,
                ms2 DOUBLE PRECISION,
                ms3 DOUBLE PRECISION,
                ms4 DOUBLE PRECISION,
                ms5 DOUBLE PRECISION,
                mr1 DOUBLE PRECISION,
                mr2 DOUBLE PRECISION,
                mr3 DOUBLE PRECISION,
                mr4 DOUBLE PRECISION,
                mr5 DOUBLE PRECISION,
                n INTEGER,
                n_lookback INTEGER,
                FhArray TEXT,
                FlArray TEXT,
                ShArray TEXT,
                SlArray TEXT,
                need_break_fractal_up BOOLEAN,
                anchorArray TEXT,
                anchor1stArray TEXT,
                anchorCntrArray TEXT,
                high1stArray TEXT,
                low1stArray TEXT,
                lowDailyCur DOUBLE PRECISION,
                highDailyCur DOUBLE PRECISION,
                lowWeeklyCur DOUBLE PRECISION,
                highWeeklyCur DOUBLE PRECISION,
                lowMonthlyCur DOUBLE PRECISION,
                highMonthlyCur DOUBLE PRECISION,
                lowDaily DOUBLE PRECISION,
                highDaily DOUBLE PRECISION,
                lowWeekly DOUBLE PRECISION,
                highWeekly DOUBLE PRECISION,
                lowMonthly DOUBLE PRECISION,
                highMonthly DOUBLE PRECISION,
                dpivotCur DOUBLE PRECISION,
                wpivotCur DOUBLE PRECISION,
                mpivotCur DOUBLE PRECISION,
                direction BOOLEAN,
                PRIMARY KEY (created, id),
                UNIQUE (created, token, n)
            );
        """)
        
        print("✅ Converting OHLC output table into a hypertable...")
        cur.execute("""
            SELECT create_hypertable('tbl_ohlc_fifteen_output', 'created', 
                chunk_time_interval => INTERVAL '1 day');
        """)

        print("✅ Creating indexes on OHLC output table...")
        cur.execute("CREATE INDEX idx_token_created ON tbl_ohlc_fifteen_output(token, created DESC);")
        cur.execute("CREATE INDEX idx_symbol_created ON tbl_ohlc_fifteen_output(symbol, created DESC) WHERE symbol IS NOT NULL;")

        print("✅ Creating market logtime table...")
        cur.execute("""
            CREATE TABLE tbl_market_logtime (
                id SERIAL PRIMARY KEY,
                start TIMESTAMPTZ,
                end_time TIMESTAMPTZ,
                type TEXT
            );
        """)

        print("✅ Creating IBKR contract details table...")
        cur.execute("""
            CREATE TABLE ibkr_contracts (
                conid INT PRIMARY KEY,
                symbol TEXT NOT NULL,
                sec_type TEXT NOT NULL,
                exchange TEXT NOT NULL,
                currency TEXT NOT NULL,
                is_active BOOLEAN DEFAULT true,
                last_updated TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (symbol, exchange)
            );
        """)
        
        cur.execute("CREATE INDEX idx_contracts_symbol ON ibkr_contracts (symbol);")
        cur.execute("CREATE INDEX idx_contracts_active ON ibkr_contracts (is_active) WHERE is_active = true;")

        print("✅ Creating continuous aggregates for OHLC data...")

        # 5-minute OHLC
        cur.execute("""
            CREATE MATERIALIZED VIEW stock_ohlc_5min
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('5 minutes', timestamp) AS created,
                token,
                symbol,
                first(price, timestamp) AS open,
                max(price) AS high,
                min(price) AS low,
                last(price, timestamp) AS close,
                SUM(volume) AS volume
            FROM stock_ticks
            GROUP BY created, token, symbol;
        """)

        # 15-minute OHLC
        cur.execute("""
            CREATE MATERIALIZED VIEW stock_ohlc_15min
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('15 minutes', timestamp) AS created,
                token,
                symbol,
                first(price, timestamp) AS open,
                max(price) AS high,
                min(price) AS low,
                last(price, timestamp) AS close,
                SUM(volume) AS volume
            FROM stock_ticks
            GROUP BY created, token, symbol;
        """)

        # 60-minute OHLC
        cur.execute("""
            CREATE MATERIALIZED VIEW stock_ohlc_60min
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('60 minutes', timestamp) AS created,
                token,
                symbol,
                first(price, timestamp) AS open,
                max(price) AS high,
                min(price) AS low,
                last(price, timestamp) AS close,
                SUM(volume) AS volume
            FROM stock_ticks
            GROUP BY created, token, symbol;
        """)

        print("✅ Setting up refresh policies for continuous aggregates...")
        
        # Refresh policies for OHLC views
        cur.execute("""
            SELECT add_continuous_aggregate_policy('stock_ohlc_5min',
                start_offset => INTERVAL '15 minutes',
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '5 minutes');
        """)

        cur.execute("""
            SELECT add_continuous_aggregate_policy('stock_ohlc_15min',
                start_offset => INTERVAL '31 minutes',
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '15 minutes');
        """)

        cur.execute("""
            SELECT add_continuous_aggregate_policy('stock_ohlc_60min',
                start_offset => INTERVAL '3 hours',
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '60 minutes');
        """)

        print("✅ Setting up compression policies for OHLC views...")
        for table in ['stock_ohlc_5min', 'stock_ohlc_15min', 'stock_ohlc_60min']:
            cur.execute(f"""
                ALTER MATERIALIZED VIEW {table} SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'token,symbol'
                );
            """)
            
            cur.execute(f"""
                SELECT add_compression_policy('{table}', 
                    compress_after => INTERVAL '7 days');
            """)

        print("✅ TimescaleDB setup completed successfully!")

    except Exception as e:
        print("❌ Error setting up database:", e)
        raise e
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    setup_database()
