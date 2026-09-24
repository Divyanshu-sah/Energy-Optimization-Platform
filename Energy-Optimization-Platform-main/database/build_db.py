"""
Complete Database Builder for EnergiX Copilot
Run this single file to create the entire database schema
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
import pandas as pd
import os
from pathlib import Path

 
# CONFIGURATION
 

DB_CONFIG = {
    'host': 'localhost',      
    'port': 5432,             
    'user': 'postgres',       
    'password': 'energix123',   
    'database': 'energix_db'  
}

 
# DATABASE SETUP FUNCTIONS
 


def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    print("📀 Checking database...")

    # Connect to default postgres database
    conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Check if database exists
    cursor.execute(
        f"SELECT 1 FROM pg_database WHERE datname = '{DB_CONFIG['database']}'"
    )
    if not cursor.fetchone():
        cursor.execute(f"CREATE DATABASE {DB_CONFIG['database']}")
        print(f"✅ Database '{DB_CONFIG['database']}' created")
    else:
        print(f"📁 Database '{DB_CONFIG['database']}' already exists")

    cursor.close()
    conn.close()


def get_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)


 
# TABLE CREATION (Single Source of Truth)
 


def create_schema_and_tables():
    """Create all tables in correct order"""
    print("\n📝 Creating tables...")

    conn = get_connection()
    cursor = conn.cursor()

    # Create schema
    cursor.execute("CREATE SCHEMA IF NOT EXISTS energix")
    cursor.execute("SET search_path TO energix")

    #   == 1. MACHINES TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id BIGSERIAL PRIMARY KEY,
            machine_id VARCHAR(50) UNIQUE NOT NULL,
            machine_type VARCHAR(50) NOT NULL,
            plant_id VARCHAR(20) NOT NULL,
            zone_id VARCHAR(20) NOT NULL,
            rated_power_kw NUMERIC(10,2) NOT NULL,
            normal_load_min INTEGER NOT NULL,
            normal_load_max INTEGER NOT NULL,
            efficiency_baseline NUMERIC(5,4) NOT NULL,
            temp_sensitivity NUMERIC(5,4) NOT NULL,
            vibration_normal_min NUMERIC(5,2) NOT NULL,
            vibration_normal_max NUMERIC(5,2) NOT NULL,
            output_per_load NUMERIC(5,2) NOT NULL,
            shift_preference VARCHAR(20) NOT NULL,
            is_active BOOLEAN DEFAULT true,
            last_maintenance_date TIMESTAMP,
            next_maintenance_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ machines table created")

    #   == 2. TELEMETRY TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id BIGSERIAL PRIMARY KEY,
            machine_id VARCHAR(50) NOT NULL REFERENCES machines(machine_id) ON DELETE CASCADE,
            plant_id VARCHAR(20) NOT NULL,
            zone_id VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            shift_id VARCHAR(20),
            voltage_v NUMERIC(8,2),
            current_a NUMERIC(10,2),
            power_kw NUMERIC(10,2) NOT NULL,
            energy_kwh_interval NUMERIC(10,4),
            power_factor NUMERIC(5,4),
            runtime_state VARCHAR(20) NOT NULL,
            load_percent NUMERIC(5,2),
            output_units NUMERIC(10,2),
            cycle_time_sec NUMERIC(10,2),
            utilization_percent NUMERIC(5,2),
            temperature_c NUMERIC(5,2),
            vibration_mm_s NUMERIC(6,3),
            ambient_temperature_c NUMERIC(5,2),
            humidity_percent NUMERIC(5,2),
            energy_per_unit NUMERIC(10,4),
            idle_energy_ratio NUMERIC(5,4),
            baseline_power_kw NUMERIC(10,2),
            power_deviation_percent NUMERIC(6,2),
            hour_of_day INTEGER,
            day_of_week INTEGER,
            weekend_flag BOOLEAN,
            peak_tariff_flag BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_power_positive CHECK (power_kw >= 0),
            CONSTRAINT check_load_range CHECK (load_percent BETWEEN 0 AND 120)
        )
    """)
    print("  ✅ telemetry table created")

    #   == 3. PREDICTIONS TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id BIGSERIAL PRIMARY KEY,
            telemetry_id BIGINT NOT NULL REFERENCES telemetry(id) ON DELETE CASCADE,
            machine_id VARCHAR(50) NOT NULL REFERENCES machines(machine_id),
            timestamp TIMESTAMP NOT NULL,
            anomaly_score NUMERIC(10,6),
            is_anomaly BOOLEAN NOT NULL,
            anomaly_type VARCHAR(50),
            anomaly_confidence NUMERIC(5,4),
            efficiency_score NUMERIC(5,2),
            efficiency_class VARCHAR(20),
            efficiency_confidence NUMERIC(5,4),
            model_version VARCHAR(50),
            inference_time_ms NUMERIC(8,3),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  ✅ predictions table created")

    #   == 4. ALERTS TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id BIGSERIAL PRIMARY KEY,
            machine_id VARCHAR(50) NOT NULL REFERENCES machines(machine_id),
            prediction_id BIGINT NOT NULL REFERENCES predictions(id),
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            recommended_action VARCHAR(100),
            status VARCHAR(20) DEFAULT 'active',
            acknowledged_by VARCHAR(100),
            acknowledged_at TIMESTAMP,
            resolved_at TIMESTAMP,
            resolution_notes TEXT,
            anomaly_score NUMERIC(10,6),
            actual_value NUMERIC(10,2),
            expected_value NUMERIC(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_severity CHECK (severity IN ('critical', 'warning', 'info')),
            CONSTRAINT check_status CHECK (status IN ('active', 'acknowledged', 'resolved'))
        )
    """)
    print("  ✅ alerts table created")

    #   == 5. RECOMMENDATIONS TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id BIGSERIAL PRIMARY KEY,
            machine_id VARCHAR(50) REFERENCES machines(machine_id),
            plant_id VARCHAR(20),
            category VARCHAR(50) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            estimated_savings_kwh NUMERIC(10,2),
            estimated_savings_percent NUMERIC(5,2),
            estimated_roi_days INTEGER,
            implementation_steps JSONB,
            difficulty VARCHAR(20),
            status VARCHAR(20) DEFAULT 'pending',
            applied_at TIMESTAMP,
            actual_savings_kwh NUMERIC(10,2),
            generated_by VARCHAR(50) DEFAULT 'sarvam_ai',
            confidence_score NUMERIC(5,4),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            CONSTRAINT check_priority CHECK (priority IN ('high', 'medium', 'low')),
            CONSTRAINT check_rec_status CHECK (status IN ('pending', 'applied', 'dismissed'))
        )
    """)
    print("  ✅ recommendations table created")

    #   == 6. FORECASTS TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS forecasts (
            id BIGSERIAL PRIMARY KEY,
            plant_id VARCHAR(20) NOT NULL,
            forecast_timestamp TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            predicted_power_kw NUMERIC(10,2) NOT NULL,
            predicted_lower_bound_kw NUMERIC(10,2),
            predicted_upper_bound_kw NUMERIC(10,2),
            actual_power_kw NUMERIC(10,2),
            model_version VARCHAR(50),
            horizon_minutes INTEGER,
            confidence_level NUMERIC(5,4),
            prediction_error_kw NUMERIC(10,2),
            absolute_percentage_error NUMERIC(5,2),
            is_used_for_optimization BOOLEAN DEFAULT false
        )
    """)
    print("  ✅ forecasts table created")

    #   == 7. SUMMARIES TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS summaries (
            id BIGSERIAL PRIMARY KEY,
            plant_id VARCHAR(20),
            summary_type VARCHAR(20) NOT NULL,
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            title VARCHAR(200),
            content TEXT NOT NULL,
            key_metrics JSONB,
            generated_by VARCHAR(50) DEFAULT 'sarvam_ai',
            generation_time_ms INTEGER,
            is_shared BOOLEAN DEFAULT false,
            share_token UUID DEFAULT gen_random_uuid(),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_summary_type CHECK (summary_type IN ('hourly', 'daily', 'weekly', 'alert_digest'))
        )
    """)
    print("  ✅ summaries table created")

    #   == 8. SIMULATOR_STATE TABLE   ==
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS simulator_state (
            id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
            is_running BOOLEAN DEFAULT false,
            simulation_speed INTEGER DEFAULT 1,
            selected_scenario VARCHAR(50),
            start_date TIMESTAMP,
            current_timestamp TIMESTAMP,
            total_telemetry_generated BIGINT DEFAULT 0,
            anomalies_generated INTEGER DEFAULT 0,
            start_time TIMESTAMP,
            last_update TIMESTAMP,
            CONSTRAINT check_speed CHECK (simulation_speed BETWEEN 1 AND 3600)
        )
    """)
    print("  ✅ simulator_state table created")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ All tables created successfully!")


 
# INDEX CREATION
 


def create_indexes():
    """Create performance indexes"""
    print("\n📊 Creating indexes...")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO energix")

    indexes = [
        # Telemetry indexes (most critical)
        "CREATE INDEX IF NOT EXISTS idx_telemetry_machine_time ON telemetry(machine_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_telemetry_plant_time ON telemetry(plant_id, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_telemetry_timestamp ON telemetry(timestamp)",
        # Alert indexes
        "CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts(status, severity, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_machine ON alerts(machine_id, created_at DESC)",
        # Prediction indexes
        "CREATE INDEX IF NOT EXISTS idx_predictions_anomaly ON predictions(is_anomaly, timestamp DESC)",
        "CREATE INDEX IF NOT EXISTS idx_predictions_machine ON predictions(machine_id, timestamp DESC)",
        # Forecast indexes
        "CREATE INDEX IF NOT EXISTS idx_forecasts_plant_time ON forecasts(plant_id, forecast_timestamp DESC)",
        # Recommendation indexes
        "CREATE INDEX IF NOT EXISTS idx_recommendations_pending ON recommendations(priority, status) WHERE status = 'pending'",
        # Machines indexes
        "CREATE INDEX IF NOT EXISTS idx_machines_plant ON machines(plant_id)",
        "CREATE INDEX IF NOT EXISTS idx_machines_type ON machines(machine_type)",
    ]

    for idx_sql in indexes:
        try:
            cursor.execute(idx_sql)
        except Exception as e:
            print(f"  ⚠️ Index warning: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Indexes created successfully!")


 
# SEED DATA
 


def seed_machines_from_csv():
    """Seed machines from CSV file"""
    print("\n🌱 Seeding machines from CSV...")

    csv_path = Path("data/synthetic/raw/machine_metadata.csv")

    if not csv_path.exists():
        print(f"⚠️ CSV file not found at {csv_path}")
        print("   Skipping machine seeding...")
        return

    # Read CSV
    df = pd.read_csv(csv_path)

    # Create SQLAlchemy engine
    engine = create_engine(
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

    # Insert data
    df.to_sql("machines", engine, schema="energix", if_exists="append", index=False)
    print(f"✅ Seeded {len(df)} machines")

    # Show sample
    print("\n📋 Sample machines added:")
    print(
        df[["machine_id", "machine_type", "plant_id"]].head(10).to_string(index=False)
    )


def seed_sample_telemetry():
    """Seed sample telemetry data (optional - for testing)"""
    print("\n🌱 Seeding sample telemetry (optional)...")

    # Ask user if they want to seed sample telemetry
    response = input("   Seed sample telemetry data? (y/N): ").lower()

    if response != "y":
        print("   Skipping sample telemetry...")
        return

    # Generate 1000 sample records
    import numpy as np
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO energix")

    # Get machine IDs
    cursor.execute("SELECT machine_id FROM machines LIMIT 10")
    machine_ids = [row[0] for row in cursor.fetchall()]

    if not machine_ids:
        print("   No machines found, skipping...")
        cursor.close()
        conn.close()
        return

    # Generate sample telemetry
    start_time = datetime.now() - timedelta(days=7)
    records = []

    for i in range(1000):
        timestamp = start_time + timedelta(minutes=i * 5)
        machine_id = np.random.choice(machine_ids)

        records.append(
            {
                "machine_id": machine_id,
                "plant_id": "P01",
                "zone_id": "Z01",
                "timestamp": timestamp,
                "power_kw": np.random.uniform(50, 200),
                "load_percent": np.random.uniform(30, 90),
                "runtime_state": "active",
                "temperature_c": np.random.uniform(25, 45),
                "vibration_mm_s": np.random.uniform(0.5, 3.0),
            }
        )

    # Insert using SQLAlchemy
    engine = create_engine(
        f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )

    df_telemetry = pd.DataFrame(records)
    df_telemetry.to_sql(
        "telemetry", engine, schema="energix", if_exists="append", index=False
    )

    cursor.close()
    conn.close()

    print(f"✅ Seeded {len(records)} sample telemetry records")


 
# VERIFICATION
 


def verify_database():
    """Verify database setup"""
    print("\n🔍 Verifying database setup...")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SET search_path TO energix")

    # Get table counts
    cursor.execute("""
        SELECT table_name, 
               (SELECT COUNT(*) FROM information_schema.tables WHERE table_name = t.table_name) as exists_flag
        FROM information_schema.tables t 
        WHERE table_schema = 'energix'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()
    print("\n📊 Tables created:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM energix.{table[0]}")
        count = cursor.fetchone()[0]
        print(f"  ✅ {table[0]}: {count} records")

    # Show foreign key relationships
    cursor.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'energix'
    """)

    relationships = cursor.fetchall()
    if relationships:
        print("\n🔗 Foreign Key Relationships:")
        for rel in relationships:
            print(f"  {rel[0]}.{rel[1]} → {rel[2]}.{rel[3]}")

    cursor.close()
    conn.close()


 
# MAIN EXECUTION
 


def main():
    """Main execution flow"""
    print("=" * 60)
    print("🚀 EnergiX Copilot - Database Builder")
    print("=" * 60)

    try:
        # Step 1: Create database
        create_database_if_not_exists()

        # Step 2: Create all tables
        create_schema_and_tables()

        # Step 3: Create indexes
        create_indexes()

        # Step 4: Seed machines from CSV
        seed_machines_from_csv()

        # Step 5: Optional sample telemetry
        seed_sample_telemetry()

        # Step 6: Verify everything
        verify_database()

        print("\n" + "=" * 60)
        print("✅ DATABASE BUILD COMPLETE!")
        print("=" * 60)
        print("\n📝 Connection Details:")
        print(f"   Host: {DB_CONFIG['host']}:{DB_CONFIG['port']}")
        print(f"   Database: {DB_CONFIG['database']}")
        print(f"   User: {DB_CONFIG['user']}")
        print("\n🔧 Connect using:")
        print(
            f"   psql -h {DB_CONFIG['host']} -p {DB_CONFIG['port']} -U {DB_CONFIG['user']} -d {DB_CONFIG['database']}"
        )
        print("\n📊 Visualize using:")
        print("   python database/visualize_schema.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Is PostgreSQL running?")
        print("2. Are credentials correct?")
        print("3. Run: docker-compose up -d (if using Docker)")


if __name__ == "__main__":
    main()
