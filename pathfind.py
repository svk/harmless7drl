from heapq import heappush, heappop
import sys

infinity = "infinity"

class PathfindingNode:
    def __init__(self, prev, current, cost, heuristic):
        self.prev = prev
        if self.prev:
            self.cost = prev.cost + cost
        else:
            self.cost = 0
        self.current = current
        self.estimate = heuristic( current )
        self.beaten = False
    def __cmp__(self, that):
        return self.cost + self.estimate - that.cost - that.estimate
    def retrace(self, accumulator = []):
        accumulator.append( self.current )
        if self.prev:
            return self.prev.retrace( accumulator )
        return list( reversed( accumulator ) )

class Pathfinder:
    def __init__(self, cost, goal, heuristic, limit = None):
        # goal and heuristic are functions tile -> Bool, tile -> comparable
        # cost is a function tile -> comparable or infinity
        self.goal = goal
        self.heuristic = heuristic
        self.cost = cost
        self.limit = limit
        self.q = []
    def addOrigin(self, origin):
        heappush( self.q, PathfindingNode( None, origin, 0, self.heuristic ) )
        return self
    def seek(self):
        closed = set()
        bestPathTo = {}
        while self.q:
            node = heappop( self.q )
            if node.beaten:
                continue
            if self.goal( node.current ):
                return node.retrace()
            if self.limit and node.cost + node.estimate > self.limit:
                return None
            closed.add( node.current )
            for neighbour in node.current.neighbours():
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
                next = PathfindingNode( node, neighbour, cost, self.heuristic )
                bestPathTo[ neighbour ] = next
                heappush( self.q, next )
        return None
