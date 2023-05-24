import json
from dataclasses import dataclass
from dataclasses import field
from typing import Dict
from typing import List
from typing import Optional

import clamfig
import yaml
from telliot_core.model.base import Base

from telliot_feeds.queries.abi_query import AbiQuery
from telliot_feeds.queries.query import OracleQuery


@dataclass
class CatalogEntry(Base):
    """Query Catalog Entry

    An entry in the query Catalog containing relevant information about the query
    """

    #: Catalog ID
    tag: str
    title: str
    query_type: str
    descriptor: str
    query_id: str
    active: bool
    abi: str

    @property
    def query(self) -> OracleQuery:
        """Return query object corresponding to catalog entry"""
        state = json.loads(self.descriptor)
        return clamfig.deserialize(state)  # type: ignore


@dataclass
class Catalog(Base):
    """Query Catalog

    The query catalog contains one `CatalogEntry` object for each valid query in the Tellor network.
    It is stored as a mapping of query names (i.e. tags) to `CatalogEntry` objects.
    """

    _entries: Dict[str, CatalogEntry] = field(default_factory=dict)

    def add_entry(self, tag: str, title: str, q: OracleQuery, active: bool = True) -> None:
        """Add a new entry to the catalog."""

        if tag in self._entries:
            raise Exception(f"Error adding query entry: {tag} already exists")

        if isinstance(q, AbiQuery):
            abi = json.dumps(q.abi)
        else:
            abi = ""

        entry = CatalogEntry(
            tag=tag,
            title=title,
            query_type=q.__class__.__name__,
            descriptor=q.descriptor,
            query_id=f"0x{q.query_id.hex()}",
            active=active,
            abi=abi,
        )

        self._entries[tag] = entry

    def find(
        self,
        *,
        tag: Optional[str] = None,
        query_id: Optional[str] = None,
        query_type: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> List[OracleQuery]:
        """Search the query catalog for matching entries."""

        entries = []
        for entry in self._entries.values():
            if tag is not None:
                if tag not in entry.tag:  # includes search for substring
                    continue
            if query_id is not None:
                # Add 0x if necessary for match
                if query_id[:2] not in ["0x", "0X"]:
                    query_id = "0x" + query_id
                if query_id.lower() != entry.query_id.lower():
                    continue
            if query_type is not None:
                if query_type.lower() != entry.query_type.lower():
                    continue
            if active is not None:
                if active != entry.active:
                    continue

            entries.append(entry)

        return entries

    def to_yaml(self) -> str:
        all_entries = self.find()
        return yaml.dump(clamfig.serialize(all_entries), sort_keys=False)

    def to_markdown(self) -> str:
        lines = ["# TellorX Query Catalog", ""]
        for entry in self.find():
            lines.append(f"## {entry.title}")
            lines.append("")
            lines.append("| Parameter | Value |")
            lines.append("| --- | --- |")
            lines.append(f"| Tag | `{entry.tag}` |")
            lines.append(f"| Active | `{entry.active}` |")
            lines.append(f"| Type | `{entry.query_type}` |")
            lines.append(f"| Descriptor | `{entry.descriptor}` |")
            lines.append(f"| Encoding ABI | `{entry.abi}` |")
            lines.append(f"| Query ID | `{entry.query_id}` |")  # type: ignore
            lines.append(f"| Query data | `0x{entry.query.query_data.hex()}` |")
            lines.append("")

        return "\n".join(lines)
