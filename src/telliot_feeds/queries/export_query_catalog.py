from telliot_feeds.queries.query_catalog import query_catalog

for q in query_catalog.find(active=True):
    print(f"{q.tag:15} 0x{q.query_id.hex()} {q.descriptor}")

with open("query_catalog.md", "w") as f:
    f.write(query_catalog.to_markdown())

with open("query_catalog.yaml", "w") as f:
    f.write(query_catalog.to_yaml())
