from typing import Optional
import datetime


def pools_query(last_id: int, data_provider: str) -> str:
    """
    Generate query string to fetch pool data from DIVA Protocol subgraph.
    
    Args:
        last_id: fetch pool with IDs later than this.
        data_provider: Who reports the data for the reference asset.
    """
    return """
            { 
                pools (first: 1000, where: {id_gt: %s, expiryTime_gte: "%s", expiryTime_lte: "%s", statusFinalReferenceValue: "Open", dataProvider: "%s"}) {
                    id
                    dataProvider
                    referenceAsset
                    collateralToken
                    collateralBalance
                    statusFinalReferenceValue
                    expiryTime
                  }
                }
            """ % (
                last_id,
                (int(datetime.now().timestamp()) - 86400),
                int(datetime.now().timestamp()),
                data_provider)


def fetch_from_subgraph(query: str) -> list[dict]:
    """Query the DIVA Protocol subgraph."""
    pass