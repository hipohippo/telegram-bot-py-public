from bots.mta_bot.query.feed_query import query_stop_and_route, RouteGroup


def test_query():
    query_stop_and_route("A12", "N", RouteGroup.ACE, api_key)