from heapq import heappush, heappop
import sys

infinity = "infinity"

class PathfindingNode:
    def __init__(self, prev, current, cost, heuristic, tiebreaker):
        self.prev = prev
        if self.prev:
            self.cost = prev.cost + cost
        else:
            self.cost = 0
        self.current = current
        self.estimate = heuristic( current )
        self.tiebreaker = tiebreaker( current )
        self.beaten = False
    def __cmp__(self, that):
        rv = self.cost + self.estimate - that.cost - that.estimate
        if rv == 0:
            return self.tiebreaker - that.tiebreaker
        return rv
    def retrace(self):
        rv = []
        n = self
        while n:
            rv.insert( 0, n.current )
            n = n.prev
        return rv
### vvv Hardest bug yet! Still haven't quite understood why it breaks.
#    def retrace(self, accumulator = []):
#       accumulator.append( self.current )
#       print>>sys.stderr, "retracing through", self.current
#       if self.prev:
#           return self.prev.retrace( accumulator )
#       return list( reversed( accumulator ) )

class Pathfinder:
    def __init__(self, cost, goal, heuristic, neighbours = lambda x : x.neighbours(), limit = None, tiebreaker = lambda tile: 0, delay = None):
        # goal and heuristic are functions tile -> Bool, tile -> comparable
        # cost is a function tile -> comparable or infinity
        self.goal = goal
        self.heuristic = heuristic
        self.cost = cost
        self.limit = limit
        self.tiebreaker = tiebreaker
        self.neighbours = neighbours
        self.delay = delay
        self.q = []
    def addOrigin(self, origin):
        heappush( self.q, PathfindingNode( None, origin, 0, self.heuristic, self.tiebreaker ) )
        return self
    def seek(self):
        closed = set()
        bestPathTo = {}
        while self.q:
            if self.delay:
                self.delay()
            node = heappop( self.q )
            if node.beaten:
                continue
            if self.goal( node.current ):
                return node.retrace()
            if self.limit and node.cost + node.estimate > self.limit:
                return None
            closed.add( node.current )
            for neighbour in self.neighbours( node.current ):
                cost = self.cost( neighbour )
                if cost == infinity:
                    continue
                try:
                    oldCost = bestPathTo[ neighbour ].cost
                    if oldCost < cost + node.cost:
                        continue
                    bestPathTo[ neighbour ].beaten = True
                except KeyError:
                    pass
                if neighbour in closed:
                    continue
                next = PathfindingNode( node, neighbour, cost, self.heuristic, self.tiebreaker )
                bestPathTo[ neighbour ] = next
                heappush( self.q, next )
        return None
