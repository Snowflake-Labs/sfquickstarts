# This script emulates the phenomenon of people buying seat tickets for a fictional Band's Concert

import json       # Enables Python -> Json
import random      # Randomizing logic used below
import time        # Lets us manipulate time pacing in the script below 
import uuid        # For generating unique ID codes per each ticket 
from datetime import datetime, timezone   # Records the exact time each purchase happened 
import boto3 # AWS toolkit 

# ── Venue and Event config ──────────────────────────────────────────────────
# Basic identifying info for the event
EVENT_ID   = "EVT001"
EVENT_NAME = "The Rolling Queries - Frisco Arena"

# ── AWS Config and Kinesis Client ───────────────────────────────────────────
# Establishes Kinesis Data stream as the receiver of the generated events 
STREAM_NAME = "ticketing-stream"   
REGION      = "us-east-1"          
kinesis = boto3.client("kinesis", region_name=REGION)   

# ── Seat map generation ──────────────────────────────────────────────────────
# Establishes Venue Layout of 16 sections, 2 rows per section, and 10 seats per row 
# Total of 320 seats for this use case 
SECTIONS = list("ABCDEFGHIJKLMNOP")  
ROWS      = [1, 2]                    
SEATS     = list(range(1, 11))       

# ── Grouping Sections under names and mapping to price tiers ──────────────────
PRICE_TIERS = {
    "FLOOR":  {"sections": list("ABCD"),         "price": 150.00},
    "LOWER":  {"sections": list("EFGHIJKL"),     "price": 85.00},
    "UPPER":  {"sections": list("MNOP"),         "price": 45.00},
}

# ── Enriched payload fields ──────────────────────────────────────────────────
# Additional randomized details attached to each event
CHANNELS = ["web", "mobile", "box_office", "resale"]   # where ticket was bought, factors into channel distribution pie chart 
PROMO_CODES = [None, None, None, "EARLY20", "VIP10", "GROUP15"]   # details if promo was used, factors into calculated price chart

# ── Burst pacing ──────────────────────────────────────────────────────────────
# Emulates waves of ticket purchasing momentum 
#   1. Fast pacing 
#   2. Pacing slows 
#   3. Final Fast Rush 
#
# The decimal numbers to the left define the tickets sold percentage threshold, that kickstarts each phase 
# The middle parentheses denoted the burst range of tickets sold 
# The last parentheses denote the pause range per burst 
PHASES = [
    (0.25, "INITIAL RUSH",    (18, 24), (4.0, 6.0)),
    (0.75, "SLOWDOWN PHASE", (6, 12),  (10.0, 14.0)),
    (1.00, "FINAL RUSH",     (18, 24), (3.0, 5.0)),
]
INTRA_BURST_DELAY_RANGE = (0.05, 0.15)  # very tiny pause between each individual sale, to manage chaos


# Displays the pacing phase 
def current_phase(progress: float):
    for cutoff, label, burst_size_range, burst_pause_range in PHASES:
        if progress < cutoff:
            return label, burst_size_range, burst_pause_range
    # Safety fallback, stay in last phase if we are at or past 100%
    return PHASES[-1][1], PHASES[-1][2], PHASES[-1][3]


# Master List of every seat in the venue
# Each is tagged with its price tier and price 
def build_seat_pool():
    pool = []
    for tier, config in PRICE_TIERS.items():           # go through FLOOR, LOWER, UPPER tiers one at a time
        for section in config["sections"]:              # go through each section within that tier
            for row in ROWS:                             # go through each row in that section
                for seat in SEATS:                       # go through each seat in that row
                    pool.append({
                        "seat_id": f"{section}-{row}{seat:02d}",   # e.g. "E-105" = section E, row 1, seat 05
                        "price_tier": tier,
                        "price":      config["price"],
                    })
    return pool


# ── Event generator ───────────────────────────────────────────────────────────
# Ticket per seat purchase 
# This is the record that gets sent to AWS and goes to Snowflake eventually 
def generate_purchase(seat: dict) -> dict:
    return {
        "purchase_id":  str(uuid.uuid4()),                       # a random unique ID for this specific purchase
        "event_id":     EVENT_ID,                                 # the same event for every one, just filler
        "seat_id":      seat["seat_id"],                          # which physical seat was bought
        "customer_id":  f"CUST-{random.randint(1000, 9999)}",    # a made up customer id, just filler 
        "price_paid":   seat["price"],                            # how much this seat costs
        "channel":      random.choice(CHANNELS),                  # random channel
        "promo_code":   random.choice(PROMO_CODES),               # random promo code or none
        "party_size":   random.randint(1, 6),                     # how many people the buyer says are attending
        "purchased_at": datetime.now(timezone.utc).isoformat(),  # exact timestamp of the purchase, in standard time format
    }


# Action of sending the purchase event to Kinesis 
def send_event(event: dict):
    kinesis.put_record(
        StreamName=STREAM_NAME,                
        Data=json.dumps(event),                
        PartitionKey=event["seat_id"], # A shard is a unit that handles a fixed amount of data independently
    )


# ── Main loop ──────────────────────────────────────────────────────────────────
# The logic of the script runtime, every seat sold randomly
def main():
    seat_pool = build_seat_pool()
    random.shuffle(seat_pool) # Like a card deck, scrambles the order of all 320 seats before loop begins. Each burst takes off the top of this deck.

    sold = []              # keeps track of every purchase we've made so far, for the running counter
    burst_num = 0           # counts which wave/burst we're currently on
    total = len(seat_pool)  # total number of seats to sell (320)
    active_phase = None     # tracks which pacing phase we're currently announcing

    print(f"Starting producer — {total} seats available")
    print("Phased pacing: " + " → ".join(label for _, label, _, _ in PHASES))
    print("Press Ctrl+C to stop.\n")

    i = 0                       # While loop continuation based on seats sold
    while i < total:            
        burst_num += 1

        # Evaluates the phase the script is in
        phase_label, burst_size_range, burst_pause_range = current_phase(i / total)
        if phase_label != active_phase:               # if new phase has been entered 
            active_phase = phase_label
            print(f"=== phase: {active_phase} ===\n")  # announce in console

        # Decides how many seats sell in the wave, and labeling them sold
        burst_size = min(random.randint(*burst_size_range), total - i)
        burst_seats = seat_pool[i:i + burst_size]   # grab that many seats 
        i += burst_size                              

        print(f"--- burst {burst_num} ({burst_size} seat(s)) ---")
        for seat in burst_seats:                      # sell each seat in this wave one at a time
            event = generate_purchase(seat)            # build the fake purchase record
            sold.append(event)                          # remember it for the running total
            send_event(event)                            # actually send it to AWS
            print(f"[{len(sold):>4}/{total}] SENT  {event['seat_id']:<10}  ${event['price_paid']:.2f}")
            time.sleep(random.uniform(*INTRA_BURST_DELAY_RANGE))   # tiny pause so sales within the wave don't all fire at the exact same millisecond

        if i < total:                                  # if there are still seats left after this wave
            pause = random.uniform(*burst_pause_range)   # wait a bit before starting the next wave 
            print(f"    (pausing {pause:.1f}s before next burst)\n")
            time.sleep(pause)

    print(f"\nDone — {len(sold)}/{total} seats sold across {burst_num} bursts.")


if __name__ == "__main__":   # this just means: only run main() if this file is executed directly (not imported by another script)
    main()
