from bots.mta_bot.query.feed_query import query_stop_and_route, RouteGroup


class TestMtaBot():
    def test_query(self):
        query_stop_and_route("A12", "N", RouteGroup.ACE, api_key)