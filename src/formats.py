from numpy.random import normal
import numpy as np
from random import shuffle
from math import log
from utils import * 

class TFormatError(Exception):
    pass

class RetObj:
    def __init__(self, n, N):
        self.n = n 
        self.N = N
        self.placings = dict()  # map team -> place -> frequency
        self.matrix = [[0 for x in range(n)] for y in range(n)] 
        self.this_run = dict()  # interim storage

    def clear_temp(self):
        self.this_run = dict()

    def add_res(self, t, p):
        self.this_run[t] = p 
        d = self.placings.get(t, dict())
        d[p] = 1 + d.get(p, 0)
        self.placings[t] = d

    def matrix_score(self):
        ss = 0.0
        for x in range(self.n): 
            for y in range(self.n):
                val = (0. + self.matrix[x][y]) / (0. + self.N)
                expected = (1. / self.n) if x < y else 0.0
                ss += pow(val - expected, 2.0)
        return 100 * (ss / (0.0 + pow(self.n, 2.0)))

    def summary(self):
        out = ""
        # for t in sorted(self.placings.keys()):
        #     out += "Rank " + str(t) + "\n"
        #     for place in sorted(self.placings[t].keys()):
        #         out += "\t" + str(place) + ": " + str(self.placings[t][place]) + "\n"
        # out += "\n\n"
        out += "Matrix summary score: " + "{0:.2f}".format(self.matrix_score())
        return out


N = 10**4
class TFormat:
    """
        A base tournament format.  
        * Teams are a list of Team objects
        * Perception error is a scalar multiple by which we multiply a random Gaussian error value to each teams true skill.
    """
    def __init__(self, name, teams, perception_error):
        self.name = name
        self.teams = teams
        self.perception_error = perception_error

    def __repr__(self):
        return "{} format with {} teams ({} perception_error)".format(self.name, len(self.teams), self.perception_error)

    def run(self):
        raise TFormatError("Run method not implemented for {}".format(self.name))


class SingleElim(TFormat):
    def __init__(self, teams, perception_error=0, seeding='standard', to_win=2):
        rounds = log(len(teams), 2)
        if abs(round(rounds) - rounds) > 0.01:
            raise TFormatError("Unacceptable number of teams in a single elimination bracket - must be a power of 2 (currently {})".format(len(teams)))
        self.seeding = seeding
        self.to_win = to_win
        super().__init__("{}-team first-to-{} Single Elim {} seeding".format(len(teams), to_win, seeding), teams, perception_error)


    def run(self):
        n = len(self.teams)
        matches = sePairings(n)
        ret = RetObj(n, N)

        for i in range(N):
            ts = self.teams[::1]
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            if self.seeding == 'standard':
                ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            elif self.seeding == 'random':
                shuffle(ts)
            
            pairings = [ts[i] for i in matches]            
            while len(pairings) != 1:
                lp = len(pairings)
                losers_place = '2' if len(pairings) == 2 else "{}-{}".format(round(1 + (lp / 2)), round(lp))
                winners = []
                losers = []

                for i in range(0, len(pairings), 2):
                    m = boX(pairings[i], pairings[1 + i], self.to_win)
                    winners.append(m[0])
                    losers.append(m[1])

                for l in losers:
                    ret.add_res(l.rank, losers_place)
                pairings = winners
            ret.add_res(pairings[0].rank, '1')

            # process placings        
            for i in range(1, n + 1 ):
                for j in range(i+1, n + 1):
                    pa = stripPlace(ret.this_run[i])
                    pb = stripPlace(ret.this_run[j])
                    if pa > pb: 
                         pass # defeated by worse team, no points
                    elif pa == pb:
                        ret.matrix[i-1][j-1] += 0.5 # higher skill team tied with lower skilled team, not broken
                    else:
                        ret.matrix[i-1][j-1] += 1.0  # higher skill team won
                    
            #print(np.matrix(ret.matrix))    
            ret.clear_temp()

        return ret