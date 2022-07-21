---
name: Support for new query type
about: All changes needed for supporting new query types (data specifications)
title: Support New Query Type -- [QUERY TYPE NAME HERE]
labels: enhancement
assignees: ''

---

- [ ] Add sources (subclass `DataSource`)
- [ ] Add feed (instance of `DataFeed`)
- [ ] Add example instance of the query type to catalog
- [ ] Add support for building custom instances of the new query type (using the `--build-feed` flag)
- [ ] Update docs for each addition
- [ ] Tests for new sources, feeds, & additions to the CLI
- [ ] Include example transactions from a block explorer of new query type submitted to Tellor using `telliot-feeds`
