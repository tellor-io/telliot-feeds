---
name: Support for new query type
about: All changes needed for supporting new query types (data specifications)
title: Support New Query Type -- [QUERY TYPE NAME HERE]
labels: enhancement
assignees: ''

---

- [ ] Links to [dataSpecs](https://github.com/tellor-io/dataSpecs) issue & new query type file
- [ ] Add query type (subclass `AbiQuery`)
- [ ] Add sources (subclass `DataSource`)
- [ ] Add feed (instance of `DataFeed`)
- [ ] Add example instance of the query type to catalog
- [ ] Add support for building custom instances of the new query type (using the `--build-feed` flag)
- [ ] Tests for new query type, sources, feeds, & additions to the CLI
- [ ] Update docs for each addition
- [ ] Include example transactions from a block explorer of new query type submitted to Tellor using `telliot-feeds`
