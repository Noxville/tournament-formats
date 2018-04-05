from numpy.random import normal
import numpy as np
from random import shuffle
from math import log
from utils import * 
import copy

class TFormatError(Exception): pass

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
        #print("rank {} finished {}".format(t, p))

    def matrix_score(self):
        nmat, n = copy.deepcopy(self.matrix), self.n

        for x in range(n): 
            for y in range(n):
                if (x < y): 
                    nmat[x][y] =  pow(1 - (nmat[x][y] / self.N), 2.0) # square from perfect score of 1
                else: 
                    nmat[x][y] = 0

        #print(np.matrix(nmat))
        #print("\n\n")
        cell_error_rate = 100 * (sum(map(sum, nmat)) / (0.5 * n * (n+1)))
        return  cell_error_rate 

    def accumulate(self):
        for i in range(1, self.n + 1 ):
            for j in range(i + 1, self.n + 1):
                pa = stripPlace(self.this_run[i])
                pb = stripPlace(self.this_run[j])

                if pa > pb: 
                     pass # defeated by worse team, no points
                elif pa == pb:
                    self.matrix[i-1][j-1] += 0.5 # higher skill team tied with lower skilled team, not broken
                else:
                    self.matrix[i-1][j-1] += 1.0  # higher skill team won

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
        self.n = len(teams)

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
        matches = sePairings(self.n)
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
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
     
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class GSLInto4TeamSingleElim(TFormat):
    def __init__(self, teams, name, perception_error=0, gsl_games=[2,2,2,2], finals=3):
        """ 
            *gsl_games* is the number of games to win the various stages of a GSL bracket (default is that they're all bo3s):
            -[0] opening rounds
            -[1] winners match
            -[2] losers match
            -[3] decider

            *finals* is the grand finals # games to win 
        """
        self.gsl_games = gsl_games
        self.finals = finals
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = gsl([ts[0], ts[2], ts[4], ts[6]], gsl_games=self.gsl_games)
            gr_b = gsl([ts[1], ts[3], ts[5], ts[7]], gsl_games=self.gsl_games)

            ret.add_res(gr_a[2].rank, '5-6')
            ret.add_res(gr_b[2].rank, '5-6')
            ret.add_res(gr_a[3].rank, '7-8')
            ret.add_res(gr_b[3].rank, '7-8')

            semifinal_1 = boX(gr_a[0], gr_b[1], 2)
            semifinal_2 = boX(gr_b[0], gr_a[1], 2)

            ret.add_res(semifinal_1[1].rank, '3-4')
            ret.add_res(semifinal_2[1].rank, '3-4')

            finals = boX(semifinal_1[0], semifinal_2[0], self.finals)

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class GSLInto8TeamSingleElim(TFormat):
    def __init__(self, teams, name, perception_error=0, gsl_games=[2,2,2,2], finals=3):
        self.gsl_games = gsl_games
        self.finals = finals
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = gsl([ts[0], ts[2], ts[4], ts[6]], gsl_games=self.gsl_games)
            gr_b = gsl([ts[1], ts[3], ts[5], ts[7]], gsl_games=self.gsl_games)

            qf_1 = boX(gr_a[0], gr_b[3])
            qf_2 = boX(gr_a[2], gr_b[1])
            qf_3 = boX(gr_a[1], gr_b[2])
            qf_4 = boX(gr_a[3], gr_b[0])

            for _ in [qf_1, qf_2, qf_3, qf_4]:
                ret.add_res(_[1].rank, '5-8')

            semifinal_1 = boX(qf_1[0], qf_2[0])
            semifinal_2 = boX(qf_3[0], qf_4[0])

            ret.add_res(semifinal_1[1].rank, '3-4')
            ret.add_res(semifinal_2[1].rank, '3-4')

            finals = boX(semifinal_1[0], semifinal_2[0], self.finals)

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class EightTeamDoubleElim(TFormat):
    def __init__(self, teams, name, perception_error=0, wb=2, lb=1, losers_finals=2, grand_finals=3):
        self.wb = wb
        self.lb = lb
        self.losers_finals = losers_finals
        self.grand_finals = grand_finals
        super().__init__(name, teams, perception_error)


    def run(self):
        n = len(self.teams)
        matches = sePairings(n)
        ret = RetObj(n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            qf_1 = boX(ts[0], ts[7], self.wb)
            qf_2 = boX(ts[3], ts[4], self.wb)
            qf_3 = boX(ts[1], ts[6], self.wb)
            qf_4 = boX(ts[2], ts[5], self.wb)

            sf_1 = boX(qf_1[0], qf_2[0], self.wb)
            sf_2 = boX(qf_3[0], qf_4[0], self.wb)

            wb_finals = boX(sf_1[0], sf_2[0], self.wb)

            lb_r1_1 = boX(qf_1[1], qf_2[1], self.lb)
            lb_r1_2 = boX(qf_3[1], qf_4[1], self.lb)

            ret.add_res(lb_r1_1[1].rank, '7-8')
            ret.add_res(lb_r1_2[1].rank, '7-8')
            
            lb_r2_1 = boX(lb_r1_1[0], sf_2[1], self.lb)
            lb_r2_2 = boX(lb_r1_2[0], sf_1[1], self.lb)

            ret.add_res(lb_r2_1[1].rank, '5-6')
            ret.add_res(lb_r2_2[1].rank, '5-6')

            lb_r3 = boX(lb_r2_1[0], lb_r2_2[0], self.lb)
            ret.add_res(lb_r3[1].rank, '4')

            lb_finals = boX(lb_r3[0], wb_finals[1], self.losers_finals)
            ret.add_res(lb_finals[1].rank, '3')

            gf = boX(lb_finals[0], wb_finals[0], self.grand_finals)
            ret.add_res(gf[1].rank, '2')
            ret.add_res(gf[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class GSLIntoBubble(TFormat):
    def __init__(self, teams, name, perception_error=0, gsl_games=[2,2,2,2], playoffs=[1, 2, 2, 2]):
        self.gsl_games = gsl_games
        self.playoffs = playoffs
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = gsl([ts[0], ts[2], ts[4], ts[6]], gsl_games=self.gsl_games)
            gr_b = gsl([ts[1], ts[3], ts[5], ts[7]], gsl_games=self.gsl_games)

            r1_1 = boX(gr_a[2], gr_b[3], self.playoffs[0])
            r1_2 = boX(gr_a[3], gr_b[2], self.playoffs[0])
            
            for _ in [r1_1, r1_2]:
                ret.add_res(_[1].rank, '7-8')

            r2_1 = boX(r1_1[0], gr_b[1], self.playoffs[1])
            r2_2 = boX(r1_2[0], gr_a[1], self.playoffs[1])
            
            for _ in [r2_1, r2_2]:
                ret.add_res(_[1].rank, '5-6')

            r3_1 = boX(r2_1[0], gr_a[0], self.playoffs[2])
            r3_2 = boX(r2_2[0], gr_b[0], self.playoffs[2])
            
            for _ in [r3_1, r3_2]:
                ret.add_res(_[1].rank, '3-4')

            finals = boX(r3_1[0], r3_2[0], self.playoffs[3])

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)