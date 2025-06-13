
import pystac_client


def test_pystac_client_compatibility(api_base_href: str):
    client = pystac_client.Client.open(api_base_href)

    next(client.search().items())
    next(client.collection_search().collections())
