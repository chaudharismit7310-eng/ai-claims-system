import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger("uvicorn")

def create_resilient_engine():
    db_url = settings.DATABASE_URL
    if db_url and db_url.startswith("postgresql"):
        try:
            # Test PostgreSQL connectivity with a short timeout
            test_engine = create_engine(db_url, connect_args={"connect_timeout": 3})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to primary PostgreSQL database.")
            return test_engine
        except Exception as err:
            logger.warning(
                f"PostgreSQL connection to {db_url.split('@')[-1]} failed ({err}). "
                "Falling back to local SQLite database (sqlite:///./claims.db)."
            )
            return create_engine("sqlite:///./claims.db", connect_args={"check_same_thread": False})
    elif db_url and "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    else:
        return create_engine(db_url)

def migrate_columns(active_engine):
    """
    Safely adds any missing hardware capture / proof columns to existing claims table
    without dropping existing data on PostgreSQL or SQLite.
    """
    from sqlalchemy import inspect
    try:
        inspector = inspect(active_engine)
        if "claims" in inspector.get_table_names():
            columns = [c["name"] for c in inspector.get_columns("claims")]
            with active_engine.connect() as conn:
                if "device_latitude" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN device_latitude FLOAT;"))
                if "device_longitude" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN device_longitude FLOAT;"))
                if "capture_timestamp" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN capture_timestamp VARCHAR;"))
                if "is_live_capture" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN is_live_capture BOOLEAN DEFAULT FALSE;"))
                if "walkaround_video_url" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN walkaround_video_url VARCHAR;"))
                if "video_analysis_json" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN video_analysis_json VARCHAR;"))
                if "garage_audit_json" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN garage_audit_json VARCHAR;"))
                if "final_approved_amount" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN final_approved_amount FLOAT;"))
                if "settlement_notes" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN settlement_notes TEXT;"))
                if "settlement_status" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN settlement_status VARCHAR DEFAULT 'pending';"))
                if "is_post_transit" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN is_post_transit BOOLEAN DEFAULT FALSE;"))
                if "incident_location" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN incident_location VARCHAR;"))
                if "inspection_location" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN inspection_location VARCHAR;"))
                if "transit_reason" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN transit_reason VARCHAR;"))
                if "photo_capture_lat" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN photo_capture_lat FLOAT;"))
                if "photo_capture_lon" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN photo_capture_lon FLOAT;"))
                if "submission_device_lat" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN submission_device_lat FLOAT;"))
                if "submission_device_lon" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN submission_device_lon FLOAT;"))
                if "exif_gps_status" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN exif_gps_status VARCHAR DEFAULT 'METADATA_STRIPPED';"))
                if "geographic_incongruity" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN geographic_incongruity BOOLEAN DEFAULT FALSE;"))
                if "geographic_incongruity_reason" not in columns:
                    conn.execute(text("ALTER TABLE claims ADD COLUMN geographic_incongruity_reason VARCHAR;"))
                conn.commit()
    except Exception as e:
        logger.warning(f"Database column migration notice: {e}")

engine = create_resilient_engine()
migrate_columns(engine)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()