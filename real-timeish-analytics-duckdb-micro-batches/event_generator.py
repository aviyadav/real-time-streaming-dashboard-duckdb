import os
import json
import time
import random
import uuid
from datetime import datetime, timezone

INBOX = "inbox_events"
os.makedirs(INBOX, exist_ok=True)

EVENTS = ["page_view", "add_to_cart", "checkout"]
SKUS = [f"SKU-{i:03d}" for i in range(1, 21)]

def generate_events(num_events):
    events = []
    for _ in range(num_events):
        event_type = random.choices(EVENTS, weights=[70, 20, 10])[0]
        event = {
            "user_id": str(uuid.uuid4()),
            "event": event_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "sku": random.choice(SKUS),
            "price": round(random.uniform(10.0, 500.0), 2) if event_type == "checkout" else 0.0
        }
        events.append(event)
    return events

def main():
    print("Starting event generator...")
    print(f"Events will be written to {INBOX}/ every minute.")
    
    while True:
        # Generate a random number of events for this minute (e.g., between 50 and 500)
        num_events = random.randint(50, 500)
        events = generate_events(num_events)
        
        # Create a unique filename based on the current timestamp
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"events_{timestamp_str}.jsonl"
        filepath = os.path.join(INBOX, filename)
        
        # Write events as JSON lines
        with open(filepath, "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")
                
        print(f"[{datetime.now().isoformat()}] Generated {num_events} events and saved to {filepath}")
        
        # Sleep for 60 seconds
        time.sleep(10)

if __name__ == "__main__":
    main()
