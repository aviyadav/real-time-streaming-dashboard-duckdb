import duckdb
import json
import time
import datetime
import os
import random
import socket

# Configuration
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "production-tracking-events-tracking-event-id-idx")
DUCKDB_FILE = "events.db"
RETENTION_DAYS = 90

class DynamoDBProducer:
    def __init__(self):
        self.table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    def publish_random_event(self):
        # Simulate a random event
        event_id = f"evt-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        timestamp = int(time.time() * 1000)
        event = {
            "event_id": event_id,
            "timestamp": timestamp,
            "event_type": random.choice(["page_view", "click", "purchase", "login"]),
            "user_id": f"user-{random.randint(100, 999)}",
            "metadata": {
                "source": random.choice(["web", "mobile"]),
                "app_version": random.choice(["1.0", "1.1", "2.0"]),
                "ip_address": f"{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            }
        }
        
        # Publish to DynamoDB
        try:
            self.table.put_item(Item=event)
            print(f"[Producer] Published event: {event_id}")
            return event
        except ClientError as e:
            print(f"[Producer] Error publishing event: {e}")
            return None

class MicroBatchWriter:
    def __init__(self, db_file=DUCKDB_FILE, retention_days=RETENTION_DAYS):
        self.db_file = db_file
        self.retention_days = retention_days
        self.conn = None
        
    def connect(self):
        """Connect to DuckDB and create necessary tables"""
        try:
            self.conn = duckdb.connect(self.db_file, read_only=False)
            print(f"[Writer] Connected to DuckDB: {self.db_file}")
            
            # Create events table if not exists
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id VARCHAR PRIMARY KEY,
                    timestamp TIMESTAMP,
                    event_type VARCHAR,
                    user_id VARCHAR,
                    source VARCHAR,
                    app_version VARCHAR,
                    ip_address VARCHAR,
                    processing_time TIMESTAMP
                )
            """)
            
            # Create aggregated hourly table
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS events_hourly (
                    date_hour DATE,
                    event_type VARCHAR,
                    count BIGINT,
                    processing_time TIMESTAMP
                )
            """)
            
            print("[Writer] Tables created successfully")
            return True
        except Exception as e:
            print(f"[Writer] Error connecting to DuckDB: {e}")
            return False
    
    def write_micro_batch(self, events):
        """Write a micro-batch of events to DuckDB"""
        if not self.conn:
            print("[Writer] No database connection")
            return False
        
        if not events:
            print("[Writer] No events to write")
            return True  # No-op, not an error
        
        try:
            # Start transaction
            self.conn.begin()
            
            # Convert events to DataFrame-like structure
            batch_data = [
                (e['event_id'],
                 datetime.datetime.fromtimestamp(e['timestamp'] / 1000),
                 e['event_type'],
                 e['user_id'],
                 e['metadata']['source'],
                 e['metadata']['app_version'],
                 e['metadata']['ip_address'],
                 datetime.datetime.utcnow())
                for e in events
            ]
            
            # Insert into events table
            self.conn.executemany("""
                INSERT OR IGNORE INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            
            # Commit transaction
            self.conn.commit()
            
            print(f"[Writer] Successfully wrote {len(events)} events")
            return True
        except Exception as e:
            # Rollback on error
            self.conn.rollback()
            print(f"[Writer] Error writing batch: {e}")
            return False
    
    def aggregate_hourly(self):
        """Aggregate events by hour and insert into hourly table"""
        if not self.conn:
            return
        
        try:
            # Aggregate events from the last hour
            self.conn.execute("""
                INSERT INTO events_hourly
                SELECT
                    date_trunc('hour', timestamp) as date_hour,
                    event_type,
                    COUNT(*) as count,
                    CURRENT_TIMESTAMP as processing_time
                FROM events
                WHERE timestamp >= NOW() - INTERVAL '1 hour'
                  AND event_type IS NOT NULL
                GROUP BY date_hour, event_type
            """)
            
            print("[Writer] Hourly aggregation completed")
        except Exception as e:
            print(f"[Writer] Error aggregating hourly: {e}")
    
    def cleanup_old_data(self):
        """Delete data older than retention period"""
        if not self.conn:
            return
        
        try:
            # Delete old events
            self.conn.execute(f"""
                DELETE FROM events
                WHERE timestamp < NOW() - INTERVAL '{self.retention_days} days'
            """)
            
            # Delete old hourly aggregations
            self.conn.execute(f"""
                DELETE FROM events_hourly
                WHERE date_hour < NOW() - INTERVAL '{self.retention_days} days'
            """)
            
            print(f"[Writer] Cleaned up data older than {self.retention_days} days")
        except Exception as e:
            print(f"[Writer] Error cleaning up: {e}")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("[Writer] Database connection closed")

def main():
    print("\n=== Micro-Batch Writer Simulation ===")
    print(f"Target DynamoDB Table: {DYNAMODB_TABLE_NAME}")
    print(f"DuckDB File: {DUCKDB_FILE}")
    print(f"Retention: {RETENTION_DAYS} days")
    print("=" * 60)
    
    # Initialize
    producer = DynamoDBProducer()
    writer = MicroBatchWriter()
    
    if not writer.connect():
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Simulation loop
        while True:
            # 1. Read from DynamoDB (simulated)
            # In production, you'd use DynamoDB Streams or Kinesis
            micro_batch = []
            for _ in range(random.randint(5, 20)):  # Simulate 5-20 events per batch
                event = producer.publish_random_event()
                if event:
                    micro_batch.append(event)
                time.sleep(0.05)  # Simulate realistic event arrival rate
            
            # 2. Write micro-batch to DuckDB
            writer.write_micro_batch(micro_batch)
            
            # 3. Periodic tasks
            if random.random() < 0.3:  # 30% chance to do extra work
                writer.aggregate_hourly()
                
            if random.random() < 0
