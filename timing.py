import sys

class Speed:
    VeryQuick = 10
    Quick = 15
    Normal = 20
    Slow = 30
    VerySlow = 60

class EventWrapper:
    def __init__(self, event, t):
        self.t = t
        self.event = event
        self.cancelled = False
    def cancel(self):
        print >>sys.stderr, "at", self, "cancelled =True"
        self.cancelled = True
    def trigger(self):
        print >>sys.stderr, "at", self, "triggers"
        if not self.cancelled:
            print >>sys.stderr, "at", self, "HIT"
            self.event.trigger( self.t )
    def __cmp__(self, that):
        return self.t - that.t

# I don't envision any terribly fancy uses of this, mostly just scheduling
# monsters to make sure stuff can move at different speeds.

# I know from experience that there should be a way to effectively
# delete a node, cancelling a future event.

from heapq import heappush, heappop

class Simulator:
    def __init__(self, t0 = 0):
        self.q = []
        self.t = t0
    def schedule(self, event, t):
        evw = EventWrapper( event, t )
        heappush( self.q, evw )
        return evw
    def advance(self, dt):
        # We use a player-centric model where we "advance" when the player
        # makes a move, then catch up to all the events that happened
        # "during" the move. A slower player will advance less time per
        # move.
        self.t += dt
    def next(self):
        if not self.q:
            return None
        if self.q[0].t > self.t:
            return None
        return heappop( self.q )
