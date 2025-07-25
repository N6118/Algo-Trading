import psycopg2
from urllib.parse import quote_plus

# Remote database configuration
password = quote_plus("password")
DB_URI = f"postgresql://postgres:{password}@100.121.186.86:5432/theodb"

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
        cur.execute("DROP TABLE IF EXISTS futures_contract_rolls CASCADE;")

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

        print("✅ Creating futures contract roll table...")
        cur.execute("""
            CREATE TABLE futures_contract_rolls (
                id SERIAL PRIMARY KEY,
                base_symbol TEXT NOT NULL,
                front_month_conid INT NOT NULL,
                back_month_conid INT NOT NULL,
                roll_date DATE NOT NULL,
                roll_type TEXT NOT NULL,  -- 'EXPIRY', 'VOLUME', 'MANUAL'
                roll_offset INTEGER NOT NULL,  -- Days before expiry to roll
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (front_month_conid) REFERENCES ibkr_contracts(conid),
                FOREIGN KEY (back_month_conid) REFERENCES ibkr_contracts(conid),
                UNIQUE (base_symbol, front_month_conid, back_month_conid, roll_date)
            );
        """)
        
        cur.execute("CREATE INDEX idx_futures_rolls_symbol ON futures_contract_rolls (base_symbol);")
        cur.execute("CREATE INDEX idx_futures_rolls_date ON futures_contract_rolls (roll_date);")
        cur.execute("CREATE INDEX idx_futures_rolls_active ON futures_contract_rolls (is_active) WHERE is_active = true;")

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

        print("✅ Creating trades table...")
        cur.execute("""
            CREATE TABLE trades (
                id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                strategy_id INT NOT NULL,
                signal_id INT,
                symbol TEXT NOT NULL,
                exchange TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity INT NOT NULL CHECK (quantity > 0),
                entry_price DOUBLE PRECISION NOT NULL CHECK (entry_price > 0),
                exit_price DOUBLE PRECISION CHECK (exit_price > 0),
                stop_loss DOUBLE PRECISION CHECK (stop_loss > 0),
                take_profit DOUBLE PRECISION CHECK (take_profit > 0),
                status TEXT NOT NULL,
                pnl DOUBLE PRECISION,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                closed_at TIMESTAMPTZ,
                is_active BOOLEAN DEFAULT true,
                UNIQUE (user_id, strategy_id, symbol, created_at),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (strategy_id) REFERENCES strategies(id),
                FOREIGN KEY (signal_id) REFERENCES signal_generation(id)
            );
        """)

        print("✅ Creating risk_settings table...")
        cur.execute("""
            CREATE TABLE risk_settings (
                id SERIAL PRIMARY KEY,
                user_id INT,
                strategy_id INT,
                max_active_trades INT NOT NULL DEFAULT 10,
                max_trades_per_day INT NOT NULL DEFAULT 20,
                max_risk_per_trade_pct DOUBLE PRECISION NOT NULL DEFAULT 0.02,
                max_total_risk_pct DOUBLE PRECISION NOT NULL DEFAULT 0.05,
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, strategy_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (strategy_id) REFERENCES strategies(id)
            );
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
