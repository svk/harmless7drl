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
    def __cmp__(self, that):
        return self.cost + self.estimate - that.cost - that.estimate
    def retrace(self, accumulator = []):
        accumulator.append( self.current )
        if self.prev:
            return self.prev.retrace( accumulator )
        return list( reversed( accumulator ) )

class Pathfinder:
    def __init__(self, cost, goal, heuristic):
        # goal and heuristic are functions tile -> Bool, tile -> comparable
        # cost is a function tile -> comparable or infinity
        self.goal = goal
        self.heuristic = heuristic
        self.cost = cost
        self.q = []
    def addOrigin(self, origin):
        heappush( self.q, PathfindingNode( None, origin, 0, self.heuristic ) )
        return self
    def seek(self):
        closed = set()
        while self.q:
            node = heappop( self.q )
            node.current.fgColour = "magenta"
            if self.goal( node.current ):
                return node.retrace()
            closed.add( node.current )
            for neighbour in node.current.neighbours():
                if neighbour in closed:
                    continue
                cost = self.cost( neighbour )
                if cost == infinity:
                    continue
                next = PathfindingNode( node, neighbour, cost, self.heuristic )
                heappush( self.q, next )
        return None
