#run  to populate data in the database.
import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase, exceptions

load_dotenv()

URI = os.getenv("COGNODB_URI")
USER = os.getenv("COGNODB_USER", "cognodb")
PASSWORD = os.getenv("COGNODB_PASSWORD")

if not URI or not PASSWORD:
    print("Error: COGNODB_URI and COGNODB_PASSWORD must be set in your .env file.")
    sys.exit(1)

# Major Indian Railway Hubs & Junctions
STATIONS = [
    {"id": "STN_NDLS", "name": "New Delhi", "code": "NDLS", "city": "Delhi NCR", "platforms": 16},
    {"id": "STN_GZB", "name": "Ghaziabad Junction", "code": "GZB", "city": "Ghaziabad", "platforms": 6},
    {"id": "STN_AGC", "name": "Agra Cantt", "code": "AGC", "city": "Agra", "platforms": 6},
    {"id": "STN_CNB", "name": "Kanpur Central", "code": "CNB", "city": "Kanpur", "platforms": 10},
    {"id": "STN_LKO", "name": "Lucknow Charbagh", "code": "LKO", "city": "Lucknow", "platforms": 9},
]

# the complete scheduled journey of a train from start to finish.
TRIPS = [
    # Corridor 1: Vande Bharat Express & Return (Shared Rake Turnaround at Lucknow)
    {"id": "TR_22436", "name": "Vande Bharat Express (NDLS-LKO)", "train_no": "22436", "type": "Vande Bharat", "delay_min": 0, "status": "ON_TIME"},
    {"id": "TR_22435", "name": "Vande Bharat Express (LKO-NDLS)", "train_no": "22435", "type": "Vande Bharat", "delay_min": 0, "status": "ON_TIME"},
    
    # Corridor 2: Lucknow Shatabdi Express via Ghaziabad
    {"id": "TR_12004", "name": "Lucknow Shatabdi Express", "train_no": "12004", "type": "Shatabdi", "delay_min": 0, "status": "ON_TIME"},
    
    # Corridor 3: Regional Feeder Line connecting at Kanpur Central Junction
    {"id": "TR_04206", "name": "Kanpur - Lucknow MEMU Express", "train_no": "04206", "type": "MEMU Express", "delay_min": 0, "status": "ON_TIME"},
    
    # Corridor 4: Evening Superfast (Driver / Loco Pilot Handover at New Delhi)
    {"id": "TR_12418", "name": "Prayagraj Superfast Express", "train_no": "12418", "type": "Superfast", "delay_min": 0, "status": "ON_TIME"},
    
    # Corridor 5: Agra Intercity Express
    {"id": "TR_14212", "name": "Intercity Express (NDLS-AGC)", "train_no": "14212", "type": "Intercity", "delay_min": 0, "status": "ON_TIME"},
]

TRIP_STOPS = [
    # TR_22436: NDLS (06:00) -> CNB (10:15) -> LKO (11:30)
    {"id": "TS_22436_1", "trip_id": "TR_22436", "station_id": "STN_NDLS", "seq": 1, "arr": "05:45", "dep": "06:00", "platform": "Platform 1"},
    {"id": "TS_22436_2", "trip_id": "TR_22436", "station_id": "STN_CNB", "seq": 2, "arr": "10:10", "dep": "10:15", "platform": "Platform 3"},
    {"id": "TS_22436_3", "trip_id": "TR_22436", "station_id": "STN_LKO", "seq": 3, "arr": "11:30", "dep": "11:40", "platform": "Platform 2"},

    # TR_22435: LKO (12:15) -> CNB (13:15) -> NDLS (17:30) [Uses TR_22436's Vande Bharat rake]
    {"id": "TS_22435_1", "trip_id": "TR_22435", "station_id": "STN_LKO", "seq": 1, "arr": "12:00", "dep": "12:15", "platform": "Platform 2"},
    {"id": "TS_22435_2", "trip_id": "TR_22435", "station_id": "STN_CNB", "seq": 2, "arr": "13:10", "dep": "13:15", "platform": "Platform 1"},
    {"id": "TS_22435_3", "trip_id": "TR_22435", "station_id": "STN_NDLS", "seq": 3, "arr": "17:30", "dep": "17:45", "platform": "Platform 1"},

    # TR_12004: NDLS (06:10) -> GZB (06:42) -> CNB (10:05)
    {"id": "TS_12004_1", "trip_id": "TR_12004", "station_id": "STN_NDLS", "seq": 1, "arr": "05:55", "dep": "06:10", "platform": "Platform 4"},
    {"id": "TS_12004_2", "trip_id": "TR_12004", "station_id": "STN_GZB", "seq": 2, "arr": "06:40", "dep": "06:42", "platform": "Platform 2"},
    {"id": "TS_12004_3", "trip_id": "TR_12004", "station_id": "STN_CNB", "seq": 3, "arr": "10:05", "dep": "10:10", "platform": "Platform 5"},

    # TR_04206: CNB (10:25) -> LKO (11:45) [Feeder connection for passengers from NDLS]
    {"id": "TS_04206_1", "trip_id": "TR_04206", "station_id": "STN_CNB", "seq": 1, "arr": "10:15", "dep": "10:25", "platform": "Platform 6"},
    {"id": "TS_04206_2", "trip_id": "TR_04206", "station_id": "STN_LKO", "seq": 2, "arr": "11:45", "dep": "11:55", "platform": "Platform 4"},

    # TR_12418: NDLS (18:10) -> CNB (23:55) [Piloted by crew arriving on TR_22435]
    {"id": "TS_12418_1", "trip_id": "TR_12418", "station_id": "STN_NDLS", "seq": 1, "arr": "17:55", "dep": "18:10", "platform": "Platform 14"},
    {"id": "TS_12418_2", "trip_id": "TR_12418", "station_id": "STN_CNB", "seq": 2, "arr": "23:50", "dep": "23:55", "platform": "Platform 4"},

    # TR_14212: NDLS (17:40) -> AGC (21:30)
    {"id": "TS_14212_1", "trip_id": "TR_14212", "station_id": "STN_NDLS", "seq": 1, "arr": "17:25", "dep": "17:40", "platform": "Platform 6"},
    {"id": "TS_14212_2", "trip_id": "TR_14212", "station_id": "STN_AGC", "seq": 2, "arr": "21:30", "dep": "21:40", "platform": "Platform 3"},
]

# Physical and Operational Dependencies
OPERATIONAL_DEPENDENCIES = {
    # 1. Rolling Stock Re-use (Turnaround at Lucknow Charbagh)
    # TR_22436 arrives at LKO at 11:30 and turns around into TR_22435 departing at 12:15 (45 min buffer, 30 min required for cleaning)
    "rolling_stock": [
        {"from_trip": "TR_22436", "to_trip": "TR_22435", "turnaround_min": 45, "min_required_min": 30}
    ],
    
    # 2. Crew Handover (Loco Pilot / Guard Shift Chaining at New Delhi)
    # Crew from TR_22435 arrives at NDLS at 17:30 and is rostered to operate TR_12418 departing at 18:10 (40 min buffer)
    "crew_handover": [
        {"from_trip": "TR_22435", "to_trip": "TR_12418", "buffer_min": 40, "min_required_min": 25}
    ],
    
    # 3. Passenger Connections (Transfers between platforms at Kanpur Central)
    # Shatabdi TR_12004 arrives at CNB at 10:05 -> Transfers to MEMU TR_04206 departing at 10:25 (20 min window)
    # Vande Bharat TR_22436 arrives at CNB at 10:10 -> Transfers to MEMU TR_04206 departing at 10:25 (15 min window)
    "passenger_transfers": [
        {"from_stop": "TS_12004_3", "to_stop": "TS_04206_1", "min_walk_min": 8, "scheduled_window_min": 20, "pax_volume": 125},
        {"from_stop": "TS_22436_2", "to_stop": "TS_04206_1", "min_walk_min": 7, "scheduled_window_min": 15, "pax_volume": 65}
    ]
}

# connecction to the database
def get_driver():
    URI = os.getenv("COGNODB_URI")
    USER = os.getenv("COGNODB_USER", "cognodb")
    PASSWORD = os.getenv("COGNODB_PASSWORD")
    if not URI or not PASSWORD:
        raise RuntimeError("COGNODB_URI and COGNODB_PASSWORD must be set in .env")
    print(f"Connecting to CognoDB instance: {URI} ...")
    return GraphDatabase.driver(URI, auth=(USER, PASSWORD))

def seed_database():
    driver = get_driver()

    try:
        with driver.session() as session:
            # clean out existing data
            print("Clearing existing database graph...")
            session.run("MATCH (n) DETACH DELETE n")

            print("Creating indexes and constraints...")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:Station) REQUIRE s.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trip) REQUIRE t.id IS UNIQUE")
            session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (ts:TripStop) REQUIRE ts.id IS UNIQUE")

            # inserting stations
            print(f"Inserting {len(STATIONS)} Indian Railway Stations...")
            session.run(
                """
                UNWIND $stations AS s
                CREATE (:Station {
                    id: s.id,
                    name: s.name,
                    code: s.code,
                    city: s.city,
                    platforms: s.platforms
                })
                """,
                stations=STATIONS
            )

            # inserting trips
            print(f"Inserting {len(TRIPS)} Train Services...")
            session.run(
                """
                UNWIND $trips AS t
                CREATE (:Trip {
                    id: t.id,
                    name: t.name,
                    train_no: t.train_no,
                    type: t.type,
                    delay_min: t.delay_min,
                    status: t.status
                })
                """,
                trips=TRIPS
            )

            # Inserting TripStops and connect to Stations & Trips
            print(f"Inserting {len(TRIP_STOPS)} Trip Stops and linking topologies...")
            session.run(
                """
                UNWIND $stops AS ts
                CREATE (stop:TripStop {
                    id: ts.id,
                    trip_id: ts.trip_id,
                    station_id: ts.station_id,
                    sequence: ts.seq,
                    scheduled_arr: ts.arr,
                    scheduled_dep: ts.dep,
                    platform: ts.platform
                })
                """,
                stops=TRIP_STOPS
            )

            session.run(
                """
                MATCH (t:Trip), (ts:TripStop)
                WHERE t.id = ts.trip_id
                CREATE (t)-[:HAS_STOP {sequence: ts.sequence}]->(ts)
                """
            )

            session.run(
                """
                MATCH (s:Station), (ts:TripStop)
                WHERE s.id = ts.station_id
                CREATE (ts)-[:CALLS_AT]->(s)
                """
            )

            # Building sequential stop relationships (:NEXT_STOP)
            session.run(
                """
                MATCH (ts1:TripStop), (ts2:TripStop)
                WHERE ts1.trip_id = ts2.trip_id AND ts2.sequence = ts1.sequence + 1
                CREATE (ts1)-[:NEXT_STOP]->(ts2)
                """
            )

            print("Creating operational dependency chains...")
            
            session.run(
                """
                UNWIND $rs_deps AS dep
                MATCH (t1:Trip {id: dep.from_trip}), (t2:Trip {id: dep.to_trip})
                CREATE (t1)-[:NEXT_SERVICE {
                    turnaround_min: dep.turnaround_min,
                    min_required_min: dep.min_required_min,
                    dependency_type: 'ROLLING_STOCK'
                }]->(t2)
                """,
                rs_deps=OPERATIONAL_DEPENDENCIES["rolling_stock"]
            )

            session.run(
                """
                UNWIND $crew_deps AS dep
                MATCH (t1:Trip {id: dep.from_trip}), (t2:Trip {id: dep.to_trip})
                CREATE (t1)-[:CREW_HANDOVER {
                    buffer_min: dep.buffer_min,
                    min_required_min: dep.min_required_min,
                    dependency_type: 'CREW_CHAIN'
                }]->(t2)
                """,
                crew_deps=OPERATIONAL_DEPENDENCIES["crew_handover"]
            )

            # Passenger transfers
            session.run(
                """
                UNWIND $transfers AS tr
                MATCH (ts1:TripStop {id: tr.from_stop}), (ts2:TripStop {id: tr.to_stop})
                CREATE (ts1)-[:PASSENGER_TRANSFER {
                    min_walk_min: tr.min_walk_min,
                    scheduled_window_min: tr.scheduled_window_min,
                    pax_volume: tr.pax_volume
                }]->(ts2)
                """,
                transfers=OPERATIONAL_DEPENDENCIES["passenger_transfers"]
            )

            # Summary Count Query
            node_counts = session.run("MATCH (n) RETURN labels(n)[0] AS label, count(n) AS count").data()
            rel_counts = session.run("MATCH ()-[r]->() RETURN type(r) AS rel_type, count(r) AS count").data()

            print("\n" + "="*45)
            print("Database successfully seeded with Indian Railway Network!")
            print("="*45)
            print("Node Counts:")
            for item in node_counts:
                print(f"  • {item['label']}: {item['count']}")
            print("\nRelationship Counts:")
            for item in rel_counts:
                print(f"  • {item['rel_type']}: {item['count']}")
            print("="*45)

    except exceptions.ServiceUnavailable as e:
        print(f"\nCould not connect to CognoDB Cloud: {e}")
        print("Please verify your COGNODB_URI and COGNODB_PASSWORD in .env.")
    except Exception as e:
        print(f"\nSeed execution failed: {e}")
    finally:
        driver.close()


if __name__ == "__main__":
    seed_database()