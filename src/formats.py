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
        self.right_top_4 = 0

    def clear_temp(self):
        self.this_run = dict()

    def add_res(self, t, p):
        self.this_run[t] = p 
        d = self.placings.get(t, dict())
        d[p] = 1 + d.get(p, 0)
        self.placings[t] = d
        # print("rank {} finished {}".format(t, p))

    def matrix_score(self):
        nmat, n = copy.deepcopy(self.matrix), self.n

        for x in range(n): 
            for y in range(n):
                if (x < y): 
                    nmat[x][y] =  pow(1 - (nmat[x][y] / self.N), 2.0) # square from perfect score of 1
                else: 
                    nmat[x][y] = 0

        print(np.matrix(nmat))
        #print("\n\n")
        cell_error_rate = 100 * (sum(map(sum, nmat)) / (0.5 * n * (n+1)))
        return  cell_error_rate 

    def accumulate(self):
        top4right = True
        for i in range(1, self.n + 1 ):            
            if (i <= 4) and stripPlace(self.this_run[i]) > 4:
                top4right = False
            for j in range(i + 1, self.n + 1):
                pa = stripPlace(self.this_run[i])
                pb = stripPlace(self.this_run[j])

                if pa > pb: 
                     pass # defeated by worse team, no points
                elif pa == pb:
                    self.matrix[i-1][j-1] += 0.5 # higher skill team tied with lower skilled team, not broken
                else:
                    self.matrix[i-1][j-1] += 1.0  # higher skill team won
        if top4right:
            self.right_top_4 += 1

    def top4(self):
        return (100.0 * self.right_top_4) / self.N

N = 10**5
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

class Perfect(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            for i in range(1, 1+ self.n):
                ret.add_res(i, str(i))
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class Worst(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            for i in range(1, 1 + self.n):
                ret.add_res(i, str(self.n - i))
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)


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

class RoundRobinIntoBubble(TFormat):
    def __init__(self, teams, name, perception_error=0):
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts, num_series=1, num_matches_per_series=1)
        ordered = sorted(first_run.values(), key=lambda x: x.three_score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.three_score()

        return sorted(first_run.values(), key=lambda x: x.three_score(), reverse=True)

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            groups = [_.team for _ in self.resolve_group(ts)]
            ret.add_res(groups[8].rank, '9')
            ret.add_res(groups[7].rank, '8')
            ret.add_res(groups[6].rank, '7')

            r1_1 = boX(groups[5], groups[2])
            r1_2 = boX(groups[4], groups[3])
            
            for _ in [r1_1, r1_2]:
                ret.add_res(_[1].rank, '5-6')

            r2_1 = boX(r1_1[0], groups[1])
            r2_2 = boX(r1_2[0], groups[0])
            
            for _ in [r2_1, r2_2]:
                ret.add_res(_[1].rank, '3-4')

            finals = boX(r2_1[0], r2_2[0])

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class SummitIdioticFormat(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)

    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts, num_series=3)
        tidx = list(first_run.keys())

        a = first_run[tidx[0]]
        b = first_run[tidx[1]]
        c = first_run[tidx[2]]

        tiebreakers = None
        if sum([1 if t.wins == 3 else 0 for t in first_run.values()]) == 3:
            # play bo1s until a winner
            flag = True
            while flag:
                tiebreakers = rr_fixed_games(_ts, num_series=1)
                if sum([1 if t.wins == 1 else 0 for t in tiebreakers.values()]) != 3:
                    flag = False # tie broken, last set of tiebreakers are good
            for _t, r in tiebreakers.items():
                first_run[_t].tiebreakers = r.wins
        
        elif a.wins == b.wins:
            _m  = boX(a.team, b.team, 1)
            first_run[_m[0]].tiebreakers = 1
        elif a.wins == c.wins:
            _m  = boX(a.team, c.team, 1)
            first_run[_m[0]].tiebreakers = 1
        elif b.wins == c.wins:
            _m  = boX(b.team, c.team, 1)
            first_run[_m[0]].tiebreakers = 1

        return sorted(first_run.values(), key=lambda x: x.score(), reverse=True)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = self.resolve_group([ts[0]] + [ts[8]] + [ts[3]])
            gr_b = self.resolve_group([ts[1]] + [ts[7]] + [ts[4]])
            gr_c = self.resolve_group([ts[2]] + [ts[6]] + [ts[5]])
            
            top = [_.team for _ in sorted([gr_a[0]] + [gr_b[0]] + [gr_c[0]], key=lambda x: x.score(), reverse=True)]
            middle = [_.team for _ in sorted([gr_a[1]] + [gr_b[1]] + [gr_c[1]], key=lambda x: x.score(), reverse=True)]
            bottom = [_.team for _ in sorted([gr_a[2]] + [gr_b[2]] + [gr_c[2]], key=lambda x: x.score(), reverse=True)]

            ret.add_res(bottom[1].rank, '8-9')
            ret.add_res(bottom[2].rank, '8-9')

            # wildcards
            wc_sf_1 = boX(middle[0], bottom[0], 2)
            wc_sf_2 = boX(middle[1], middle[2], 2)

            ret.add_res(wc_sf_1[1].rank, '6-7')
            ret.add_res(wc_sf_2[1].rank, '6-7')

            wc_final = boX(wc_sf_1[0], wc_sf_2[0], 2)
            ret.add_res(wc_final[1].rank, '5')

            # playoffs
            po_sf_1 = boX(top[0], wc_final[0], 2)
            po_sf_2 = boX(top[1], top[2], 2)

            ret.add_res(po_sf_1[1].rank, '3-4')
            ret.add_res(po_sf_2[1].rank, '3-4')

            finals = boX(po_sf_1[0], po_sf_2[0], 3)
            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)


class PerfectWorldMasters(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts, num_series=1, num_matches_per_series=2)
        ordered = sorted(first_run.values(), key=lambda x: x.three_score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.three_score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.three_score()

        return sorted(first_run.values(), key=lambda x: x.three_score(), reverse=True)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [1, 4, 5, 8, 9]
            gr_a = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank in a])]
            gr_b = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank not in a])]

            ret.add_res(gr_a[4].rank, '9-10')
            ret.add_res(gr_b[4].rank, '9-10')

            # winners bracket
            qf_1_1 = boX(gr_a[0], gr_b[3])
            qf_1_2 = boX(gr_b[1], gr_a[2])
            qf_1_3 = boX(gr_b[0], gr_a[3])
            qf_1_4 = boX(gr_a[1], gr_b[2])

            sf_2_1 = boX(qf_1_1[0], qf_1_2[0])
            sf_2_2 = boX(qf_1_3[0], qf_1_4[0])

            wb_finals = boX(sf_2_1[0], sf_2_2[0])

            # losers bracket
            lb_r1_1 = boX(qf_1_1[1], qf_1_2[1], 1)
            lb_r1_2 = boX(qf_1_3[1], qf_1_4[1], 1)
            ret.add_res(lb_r1_1[1].rank, '7-8')
            ret.add_res(lb_r1_2[1].rank, '7-8')

            lb_r2_1 = boX(lb_r1_1[0], sf_2_2[1])
            lb_r2_2 = boX(lb_r1_2[0], sf_2_1[1])
            ret.add_res(lb_r2_1[1].rank, '5-6')
            ret.add_res(lb_r2_2[1].rank, '5-6')

            lb_r3 = boX(lb_r2_1[0], lb_r2_2[0])
            ret.add_res(lb_r3[1].rank, '4')

            lb_final = boX(lb_r3[0], wb_finals[1])
            ret.add_res(lb_final[1].rank, '3')

            finals = boX(wb_finals[0], lb_final[0], 3)
            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class ESLDoubleElimIntoSingleElim(TFormat):
    def __init__(self, teams, name, perception_error, playoff_game):
        self.playoff_game = playoff_game
        super().__init__(name, teams, perception_error)

    def resolve_group(self, _ts):
        # winners
        qf_1 = boX(_ts[0], _ts[7], 1)
        qf_2 = boX(_ts[3], _ts[4], 1)
        qf_3 = boX(_ts[1], _ts[6], 1)
        qf_4 = boX(_ts[2], _ts[5], 1)

        sf_1 = boX(qf_1[0], qf_2[0])
        sf_2 = boX(qf_3[0], qf_4[0])

        finals = boX(sf_1[0], sf_2[0])

        # losers
        lb_r1_1 = boX(qf_1[1], qf_2[1])
        lb_r1_2 = boX(qf_3[1], qf_4[1])

        lb_sf_1 = boX(lb_r1_1[0], sf_2[1])
        lb_sf_2 = boX(lb_r1_2[0], sf_1[1])

        losers_finals = boX(lb_sf_1[0], lb_sf_2[0])

        return [ 
            finals[0], 
            finals[1],
            losers_finals[0],
            losers_finals[1],
            lb_sf_1[1], lb_sf_2[1],
            lb_r1_1[1], lb_r1_2[1],
        ]

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [0, 2, 4, 6, 8, 10, 12, 14]
            gr_a = self.resolve_group([_ for i, _ in enumerate(ts) if i in a])
            gr_b = self.resolve_group([_ for i, _ in enumerate(ts) if i not in a])

            for g in [gr_a, gr_b]:
                ret.add_res(g[7].rank, '13-16')
                ret.add_res(g[6].rank, '13-16')
                ret.add_res(g[5].rank, '9-12')
                ret.add_res(g[4].rank, '9-12')
                ret.add_res(g[3].rank, '7-8')

            # playoffs
            qf_1 = boX(gr_a[1], gr_b[2])
            qf_2 = boX(gr_b[1], gr_a[2])
            ret.add_res(qf_1[1].rank, '5-6')
            ret.add_res(qf_2[1].rank, '5-6')

            sf_1 = boX(qf_1[0], gr_a[0])
            sf_2 = boX(qf_2[0], gr_b[0])            

            decider = boX(sf_1[1], sf_2[1])
            ret.add_res(decider[0].rank, '3' if self.playoff_game else '3-4')
            ret.add_res(decider[1].rank, '4' if self.playoff_game else '3-4')

            finals = boX(sf_1[0], sf_2[0], 3)
            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class DotaAsiaChampionships(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts)
        ordered = sorted(first_run.values(), key=lambda x: x.score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.three_score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return sorted(first_run.values(), key=lambda x: x.score(), reverse=True)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [1, 4, 5, 8, 9, 11, 13, 15]
            gr_a = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank in a])]
            gr_b = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank not in a])]

            ret.add_res(gr_a[7].rank, '15-16')
            ret.add_res(gr_b[7].rank, '15-16')

            ret.add_res(gr_a[6].rank, '13-14')
            ret.add_res(gr_b[6].rank, '13-14')

            # breakout
            bo_1 = boX(gr_a[2], gr_b[5])
            bo_2 = boX(gr_a[4], gr_b[3])
            bo_3 = boX(gr_a[5], gr_b[2])
            bo_4 = boX(gr_a[3], gr_b[4])

            for _ in [bo_1, bo_2, bo_3, bo_4]:
                ret.add_res(_[1].rank, '9-12')

            # winners
            wb_qf_1 = boX(bo_1[0], gr_a[1])
            wb_qf_2 = boX(bo_2[0], gr_b[0])
            wb_qf_3 = boX(bo_3[0], gr_b[1])
            wb_qf_4 = boX(bo_4[0], gr_a[0])

            wb_sf_1 = boX(wb_qf_1[0], wb_qf_2[0])
            wb_sf_2 = boX(wb_qf_3[0], wb_qf_4[0])

            wb_finals = boX(wb_sf_1[0], wb_sf_2[0])

            # losers
            lb_r1_1 = boX(wb_qf_1[1], wb_qf_2[1], 1)
            lb_r1_2 = boX(wb_qf_3[1], wb_qf_4[1], 1)
            ret.add_res(lb_r1_1[1].rank, '7-8')
            ret.add_res(lb_r1_2[1].rank, '7-8')
           
            lb_r2_1 = boX(lb_r1_1[0], wb_sf_2[1])
            lb_r2_2 = boX(lb_r1_2[0], wb_sf_1[1])
            ret.add_res(lb_r2_1[1].rank, '5-6')
            ret.add_res(lb_r2_2[1].rank, '5-6')

            lb_r3 = boX(lb_r2_1[0], lb_r2_2[0])
            ret.add_res(lb_r3[1].rank, '4')

            lb_finals = boX(lb_r3[0], wb_finals[1])
            ret.add_res(lb_finals[1].rank, '3')

            grand_finals = boX(wb_finals[0], lb_finals[0], 3)
            ret.add_res(grand_finals[1].rank, '2')
            ret.add_res(grand_finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class PGLBucharest(TFormat):
    def __init__(self, teams, name, perception_error):
        super().__init__(name, teams, perception_error)

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            wins = {}
            losses = {}

            for t in ts:
                wins[t] = 0
                losses[t] = 0

            # swiss r1
            for seed in range(8):
                m = boX(ts[seed], ts[self.n - 1 - seed], 1)
                wins[m[0]] = 1 + wins[m[0]] 
                losses[m[1]] = 1 + losses[m[1]] 
                       
            # swiss r2
            oneOh = sorted([t for t in ts if (wins[t] == 1 and losses[t] == 0)], key=lambda x: random())            
            ohOne = sorted([t for t in ts if (wins[t] == 0 and losses[t] == 1)], key=lambda x: random())
            for score in [oneOh, ohOne]:
                for pair in chunk(score, 2):
                    m = boX(pair[0], pair[1], 1)
                    wins[m[0]] = 1 + wins[m[0]] 
                    losses[m[1]] = 1 + losses[m[1]] 

            # swiss r3
            twoOh = sorted([t for t in ts if (wins[t] == 2 and losses[t] == 0)], key=lambda x: random())            
            oneOne = sorted([t for t in ts if (wins[t] == 1 and losses[t] == 1)], key=lambda x: random())
            ohTwo = sorted([t for t in ts if (wins[t] == 0 and losses[t] == 2)], key=lambda x: random())
            for score in [twoOh, oneOne, ohTwo]:
                for pair in chunk(score, 2):
                    m = boX(pair[0], pair[1], 1)
                    wins[m[0]] = 1 + wins[m[0]] 
                    losses[m[1]] = 1 + losses[m[1]] 

            # swiss r4
            twoOne = sorted([t for t in ts if (wins[t] == 2 and losses[t] == 1)], key=lambda x: random())            
            oneTwo = sorted([t for t in ts if (wins[t] == 1 and losses[t] == 2)], key=lambda x: random())
            for score in [twoOne, oneTwo]:
                for pair in chunk(score, 2):
                    m = boX(pair[0], pair[1], 1)
                    wins[m[0]] = 1 + wins[m[0]] 
                    losses[m[1]] = 1 + losses[m[1]] 

            # swiss r5
            twoTwo = sorted([t for t in ts if (wins[t] == 2 and losses[t] == 2)], key=lambda x: random())
            for pair in chunk(twoTwo, 2):
                m = boX(pair[0], pair[1], 1)
                wins[m[0]] = 1 + wins[m[0]] 
                losses[m[1]] = 1 + losses[m[1]] 

            threeOh = sorted([t for t in ts if (wins[t] == 3 and losses[t] == 0)], key=lambda x: random())
            threeOne = sorted([t for t in ts if (wins[t] == 3 and losses[t] == 1)], key=lambda x: random())
            threeTwo = sorted([t for t in ts if (wins[t] == 3 and losses[t] == 2)], key=lambda x: random())
            twoThree = sorted([t for t in ts if (wins[t] == 2 and losses[t] == 3)], key=lambda x: random())
            oneThree = sorted([t for t in ts if (wins[t] == 1 and losses[t] == 3)], key=lambda x: random())
            zeroThree = sorted([t for t in ts if (wins[t] == 0 and losses[t] == 3)], key=lambda x: random())

            for _ in zeroThree:
                ret.add_res(_.rank, '15-16')

            for _ in oneThree:
                ret.add_res(_.rank, '12-14')

            for _ in twoThree:
                ret.add_res(_.rank, '9-11')

            qf_1 = boX(threeOh[0], threeTwo[2]) # 1v8
            qf_2 = boX(threeOne[1], threeOne[2]) # 4v5
            qf_3 = boX(threeOh[1], threeTwo[1]) # 2v7
            qf_4 = boX(threeOne[0], threeTwo[0]) # 3v6

            for _ in [qf_1, qf_2, qf_3, qf_4]:
                ret.add_res(_[1].rank, '5-8')

            sf_1 = boX(qf_1[0], qf_2[0])
            sf_2 = boX(qf_3[0], qf_4[0])

            for _ in [sf_1, sf_2]:
                ret.add_res(_[1].rank, '3-4')

            finals = boX(sf_1[0], sf_2[0], 3)
            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')

            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)


class MDLChangsha(TFormat):
    def __init__(self, teams, name, perception_error=0):        
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts, num_matches_per_series=2)
        ordered = sorted(first_run.values(), key=lambda x: x.score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return sorted(first_run.values(), key=lambda x: x.score(), reverse=True)

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [1, 3, 5, 7, 9, 11]
            gr_a = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank in a])]
            gr_b = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank not in a])]

            ret.add_res(gr_a[5].rank, '11-12')
            ret.add_res(gr_b[5].rank, '11-12')

            # winners bracket
            wb_r1_1 = boX(gr_b[1], gr_a[2])
            wb_r1_2 = boX(gr_b[2], gr_a[1])

            wb_sf_1 = boX(wb_r1_1[0], gr_a[0])
            wb_sf_2 = boX(wb_r1_2[0], gr_b[0])

            wb_final = boX(wb_sf_1[0], wb_sf_2[0])

            # losers bracket
            lb_r1_1 = boX(gr_a[3], gr_b[4], 1)
            lb_r1_2 = boX(gr_b[3], gr_a[4], 1)
            ret.add_res(lb_r1_1[1].rank, '9-10')
            ret.add_res(lb_r1_2[1].rank, '9-10')

            lb_r2_1 = boX(lb_r1_1[0], wb_r1_1[1])
            lb_r2_2 = boX(lb_r1_2[0], wb_r1_2[1])
            ret.add_res(lb_r2_1[1].rank, '7-8')
            ret.add_res(lb_r2_2[1].rank, '7-8')

            lb_r3_1 = boX(lb_r2_1[0], wb_sf_2[1])
            lb_r3_2 = boX(lb_r2_2[0], wb_sf_1[1])
            ret.add_res(lb_r3_1[1].rank, '5-6')
            ret.add_res(lb_r3_2[1].rank, '5-6')

            lb_sf = boX(lb_r3_1[0], lb_r3_2[0])
            ret.add_res(lb_sf[1].rank, '4')

            lb_finals = boX(lb_sf[0], wb_final[1])
            ret.add_res(lb_finals[1].rank, '3')

            finals = boX(lb_finals[0], wb_final[0])

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class TheInternational2017(TFormat):
    def __init__(self, teams, name, perception_error=0):        
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_group(self, _ts):
        first_run = rr_fixed_games(_ts, num_matches_per_series=2)
        ordered = sorted(first_run.values(), key=lambda x: x.score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.three_score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return sorted(first_run.values(), key=lambda x: x.score(), reverse=True)

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [1, 3, 5, 7, 9, 11, 13, 15, 17]
            gr_a = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank in a])]
            gr_b = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank not in a])]

            ret.add_res(gr_a[8].rank, '17-18')
            ret.add_res(gr_b[8].rank, '17-18')

            # winnners bracket
            wb_r1_1 = boX(gr_a[0], gr_b[3])
            wb_r1_2 = boX(gr_a[2], gr_b[1])            
            wb_r1_3 = boX(gr_b[2], gr_a[1])
            wb_r1_4 = boX(gr_b[0], gr_a[3])

            wb_r2_1 = boX(wb_r1_1[0], wb_r1_2[0])
            wb_r2_2 = boX(wb_r1_3[0], wb_r1_4[0])

            wb_finals = boX(wb_r2_1[0], wb_r2_2[0])

            # losers bracket
            lb_r1_1 = boX(gr_a[4], gr_b[7], 1)
            lb_r1_2 = boX(gr_a[6], gr_b[5], 1)            
            lb_r1_3 = boX(gr_b[6], gr_a[5], 1)
            lb_r1_4 = boX(gr_b[4], gr_a[7], 1)
            ret.add_res(lb_r1_1[1].rank, '13-16')
            ret.add_res(lb_r1_2[1].rank, '13-16')
            ret.add_res(lb_r1_3[1].rank, '13-16')
            ret.add_res(lb_r1_4[1].rank, '13-16')

            lb_r2_1 = boX(lb_r1_1[0], wb_r1_1[1])
            lb_r2_2 = boX(lb_r1_2[0], wb_r1_2[1])
            lb_r2_3 = boX(lb_r1_3[0], wb_r1_3[1])
            lb_r2_4 = boX(lb_r1_4[0], wb_r1_4[1])
            ret.add_res(lb_r2_1[1].rank, '9-12')
            ret.add_res(lb_r2_2[1].rank, '9-12')
            ret.add_res(lb_r2_3[1].rank, '9-12')
            ret.add_res(lb_r2_4[1].rank, '9-12')

            lb_r3_1 = boX(lb_r2_1[0], lb_r2_2[0])
            lb_r3_2 = boX(lb_r2_3[0], lb_r2_4[0])
            ret.add_res(lb_r3_1[1].rank, '7-8')
            ret.add_res(lb_r3_2[1].rank, '7-8')

            lb_r4_1 = boX(lb_r3_1[0], wb_r2_2[1])
            lb_r4_2 = boX(lb_r3_2[0], wb_r2_1[1])            
            ret.add_res(lb_r4_1[1].rank, '5-6')
            ret.add_res(lb_r4_2[1].rank, '5-6')

            lb_sf = boX(lb_r4_1[0], lb_r4_2[0])
            ret.add_res(lb_sf[1].rank, '4')

            lb_finals = boX(lb_sf[0], wb_finals[1])
            ret.add_res(lb_finals[1].rank, '3')

            finals = boX(lb_finals[0], wb_finals[0], 3)
            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')

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

class SuperMajor(TFormat):
    def __init__(self, teams, name, perception_error=0, gsl_games=[2,2,2,2]):
        self.gsl_games = gsl_games
        super().__init__(name, teams, perception_error)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = gsl([ts[0], ts[5], ts[8], ts[13]], gsl_games=self.gsl_games)
            gr_b = gsl([ts[1], ts[4], ts[9], ts[12]], gsl_games=self.gsl_games)
            gr_c = gsl([ts[2], ts[7], ts[10], ts[15]], gsl_games=self.gsl_games)
            gr_d = gsl([ts[3], ts[6], ts[11], ts[14]], gsl_games=self.gsl_games)

            wb_r1_1 = boX(gr_a[0], gr_c[1])
            wb_r1_2 = boX(gr_d[0], gr_b[1])
            wb_r1_3 = boX(gr_b[0], gr_d[1])
            wb_r1_4 = boX(gr_c[0], gr_a[1])

            wb_r2_1 = boX(wb_r1_1[0], wb_r1_2[0])
            wb_r2_2 = boX(wb_r1_3[0], wb_r1_4[0])

            wb_finals = boX(wb_r2_1[0], wb_r2_2[0])

            # lb

            lb_r1_1 = boX(gr_a[2], gr_c[3])
            lb_r1_2 = boX(gr_d[2], gr_b[3])
            lb_r1_3 = boX(gr_b[2], gr_d[3])
            lb_r1_4 = boX(gr_c[2], gr_a[3])

            for _ in [lb_r1_1, lb_r1_2, lb_r1_3, lb_r1_4]:
                ret.add_res(_[1].rank, '13-16')

            lb_r2_1 = boX(lb_r1_1[0], wb_r1_4[1])
            lb_r2_2 = boX(lb_r1_2[0], wb_r1_3[1])
            lb_r2_3 = boX(lb_r1_3[0], wb_r1_2[1])
            lb_r2_4 = boX(lb_r1_4[0], wb_r1_1[1])

            for _ in [lb_r2_1, lb_r2_2, lb_r2_3, lb_r2_4]:
                ret.add_res(_[1].rank, '9-12')

            lb_r3_1 = boX(lb_r2_1[0], lb_r2_2[0])
            lb_r3_2 = boX(lb_r2_3[0], lb_r2_4[0])

            for _ in [lb_r3_1, lb_r3_2]:
                ret.add_res(_[1].rank, '7-8')

            lb_r4_1 = boX(lb_r3_1[0], wb_r2_1[1])
            lb_r4_2 = boX(lb_r3_2[0], wb_r2_2[1])

            for _ in [lb_r4_1, lb_r4_2]:
                ret.add_res(_[1].rank, '5-6')

            lb_sf = boX(lb_r4_1[0], lb_r4_2[0])
            ret.add_res(lb_sf[1].rank, '4')
            
            lb_finals = boX(lb_sf[0], wb_finals[1])
            ret.add_res(lb_finals[1].rank, '3')

            finals = boX(wb_finals[0], lb_finals[0], 3)

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class ESLTwelveTeamFormat(TFormat):
    def __init__(self, teams, name, perception_error=0, gsl_games=[1,2,2,2]):
        self.gsl_games = gsl_games
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret


    def resolve_placings(self, _ts):
        first_run = rr_fixed_games(_ts)
        ordered = sorted(first_run.values(), key=lambda x: x.score(), reverse=False)
        
        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.three_score()
            elif res == cur:
                tied.append(res)
            else:                
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return sorted(first_run.values(), key=lambda x: x.score(), reverse=True)


    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            gr_a = gsl([ts[0], ts[5], ts[6], ts[11]], gsl_games=self.gsl_games)
            gr_b = gsl([ts[1], ts[4], ts[7], ts[10]], gsl_games=self.gsl_games)
            gr_c = gsl([ts[2], ts[3], ts[8], ts[9]], gsl_games=self.gsl_games)

            for _ in [gr_a, gr_b, gr_c]:
                ret.add_res(_[2].rank, '7-9')
                ret.add_res(_[3].rank, '10-12')

            winners = [_.team for _ in self.resolve_placings([gr_a[0], gr_b[0], gr_c[0]])]
            rups = sorted([gr_a[1], gr_b[1], gr_c[1]], key=lambda x: random()) # [_.team for _ in self.resolve_placings([gr_a[1], gr_b[1], gr_c[1]])]

            qf_1 = boX(rups[0], rups[1])
            qf_2 = boX(winners[2], rups[2])

            ret.add_res(qf_1[1].rank, '5-6')
            ret.add_res(qf_2[1].rank, '5-6')

            semifinal_1 = boX(qf_1[0], winners[0])
            semifinal_2 = boX(qf_2[0], winners[1])            

            decider = boX(semifinal_1[1], semifinal_2[1])
            ret.add_res(decider[1].rank, '4')
            ret.add_res(decider[0].rank, '3')

            finals = boX(semifinal_1[0], semifinal_2[0], 3)

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

class Epicenter(TFormat):
    def __init__(self, teams, name, perception_error=0):
        super().__init__(name, teams, perception_error)

    def broken(self, tbs):
        seen_score = {}
        ret = True
        for t in tbs:
            if t.wins in seen_score:
                ret = False
                break
            else:
                seen_score[t.wins] = True
        return ret

    def resolve_group(self, _ts):
        first_run = rr_box_matches(_ts)
        ordered = sorted(first_run.values(), key=lambda x: x.score(), reverse=False)

        tied = []
        cur = None
        for res in ordered:
            if cur == None:
                cur = res.series_score()
            elif res == cur:
                tied.append(res)
            else:
                if len(tied) > 1:
                    pass
                else:
                    flag = True
                    while flag:
                        tiebreakers = rr_fixed_games(tied, num_series=1)
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return sorted(first_run.values(), key=lambda x: x.series_score(), reverse=True)

    def run(self):
        ret = RetObj(self.n, N)

        for i in range(N):
            ts = copy.deepcopy(self.teams)
            for t in ts: 
                t.perceived_skill = t.true_skill + (self.perception_error * normal())
            ts = sorted(ts, key=lambda x: x.perceived_skill, reverse=True)
            
            a = [1, 3, 5, 7, 9, 11]
            gr_a = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank in a])]
            gr_b = [_.team for _ in self.resolve_group([_ for _ in ts if _.rank not in a])]

            ret.add_res(gr_a[5].rank, '11-12')
            ret.add_res(gr_b[5].rank, '11-12')

            ret.add_res(gr_a[4].rank, '9-10')
            ret.add_res(gr_b[4].rank, '9-10')

            # winners bracket
            wb_r1_1 = boX(gr_a[0], gr_b[1])
            wb_r1_2 = boX(gr_a[1], gr_b[0])

            wb_final = boX(wb_r1_1[0], wb_r1_2[0])

            # losers bracket
            lb_r2_1 = boX(gr_a[3], gr_b[2], 1)
            lb_r2_2 = boX(gr_a[2], gr_b[3], 1)
            ret.add_res(lb_r2_1[1].rank, '7-8')
            ret.add_res(lb_r2_2[1].rank, '7-8')

            lb_r3_1 = boX(lb_r2_1[0], wb_r1_2[1], 1)
            lb_r3_2 = boX(lb_r2_2[0], wb_r1_1[1], 1)
            ret.add_res(lb_r3_1[1].rank, '5-6')
            ret.add_res(lb_r3_2[1].rank, '5-6')

            lb_sf = boX(lb_r3_1[0], lb_r3_2[0])
            ret.add_res(lb_sf[1].rank, '4')

            lb_finals = boX(lb_sf[0], wb_final[1])
            ret.add_res(lb_finals[1].rank, '3')

            finals = boX(lb_finals[0], wb_final[0])

            ret.add_res(finals[1].rank, '2')
            ret.add_res(finals[0].rank, '1')
                       
            ret.accumulate()                              
            ret.clear_temp()

        return (self, ret)

