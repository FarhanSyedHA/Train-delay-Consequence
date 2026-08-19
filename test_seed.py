from seed import get_driver

# Multi-hop cascade query: Delay TR_101 and trace down to TR_401 (Trip -> Trip -> Trip)
query = """
  MATCH path = (source:Trip {id: $trip_id})-[:NEXT_SERVICE|CREW_HANDOVER*1..3]->(affected:Trip)
  RETURN 
      source.name AS RootTrain,
      [n IN nodes(path) | n.name] AS ImpactChain,
      [r IN relationships(path) | type(r)] AS DependencyTypes,
      length(path) AS CascadeHops
  """

def test_seed():
  driver = get_driver()
  try:
    with driver.session() as session:
      results = session.run(query, trip_id="TR_101").data()
      for row in results:
          print(f"Cascade: {' -> '.join(row['ImpactChain'])} (Hops: {row['CascadeHops']})")
  finally:
    driver.close()

if __name__ == "__main__":
    test_seed()