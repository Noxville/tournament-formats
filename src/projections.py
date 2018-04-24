from utils import * 
import copy

N = 10**3

class CurTeam:
    def __init__(self, name, points, rating, disqualified=False):
        self.name = name
        self.points = points
        self.rating = rating
        self.disqualified = disqualified
        self.qualifies = 0
        self.placement = dict()
        self.tot_points = 0

    def add_run(self, is_qual, place, points):
        if is_qual:
            self.qualifies += 1
        self.placement[place] = 1 + self.placement.get(place, 0)
        self.tot_points += points

class MDL:
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
        first_run = rr_fixed_games(_ts, num_matches_per_series=2, func='glicko')
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
                        tiebreakers = rr_fixed_games(tied, num_series=1, func='glicko')
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return [_.team for _ in sorted(first_run.values(), key=lambda x: x.score(), reverse=True)]

    def run(self, teams):
        a = [1, 3, 5, 7, 9, 11]
        gr_a = self.resolve_group([_ for _ in teams if _.rank in a])
        gr_b = self.resolve_group([_ for _ in teams if _.rank not in a])

        # winners bracket
        wb_r1_1 = boXg(gr_b[1], gr_a[2])
        wb_r1_2 = boXg(gr_b[2], gr_a[1])

        wb_sf_1 = boXg(wb_r1_1[0], gr_a[0])
        wb_sf_2 = boXg(wb_r1_2[0], gr_b[0])

        wb_final = boXg(wb_sf_1[0], wb_sf_2[0])

        # losers bracket
        lb_r1_1 = boXg(gr_a[3], gr_b[4], 1)
        lb_r1_2 = boXg(gr_b[3], gr_a[4], 1)

        lb_r2_1 = boXg(lb_r1_1[0], wb_r1_1[1])
        lb_r2_2 = boXg(lb_r1_2[0], wb_r1_2[1])

        lb_r3_1 = boXg(lb_r2_1[0], wb_sf_2[1])
        lb_r3_2 = boXg(lb_r2_2[0], wb_sf_1[1])

        lb_sf = boXg(lb_r3_1[0], lb_r3_2[0])

        lb_finals = boXg(lb_sf[0], wb_final[1])

        finals = boXg(lb_finals[0], wb_final[0])

        return [lb_sf[1], lb_finals[1], finals[1], finals[0]] # 4 / 3 / 2 / 1

class Epicenter:
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
        first_run = rr_box_matches(_ts, func='glicko')
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
                        tiebreakers = rr_fixed_games(tied, num_series=1, func='glicko')
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return [_.team for _ in sorted(first_run.values(), key=lambda x: x.score(), reverse=True)]

    def run(self, teams):
        a = [1, 3, 5, 7, 9, 11]
        gr_a = self.resolve_group([_ for _ in teams if _.rank in a])
        gr_b = self.resolve_group([_ for _ in teams if _.rank not in a])

        # winners bracket
        wb_r1_1 = boXg(gr_a[0], gr_b[1])
        wb_r1_2 = boXg(gr_a[1], gr_b[0])

        wb_final = boXg(wb_r1_1[0], wb_r1_2[0])

        # losers bracket
        lb_r2_1 = boXg(gr_a[3], gr_b[2], 1)
        lb_r2_2 = boXg(gr_a[2], gr_b[3], 1)

        lb_r3_1 = boXg(lb_r2_1[0], wb_r1_2[1], 1)
        lb_r3_2 = boXg(lb_r2_2[0], wb_r1_1[1], 1)

        lb_sf = boXg(lb_r3_1[0], lb_r3_2[0])
        lb_finals = boXg(lb_sf[0], wb_final[1])

        finals = boXg(lb_finals[0], wb_final[0])

        return [lb_sf[1], lb_finals[1], finals[1], finals[0]]

eighth = []
teams = {}

for t in [
    # name, points, rating, disqualified
    CurTeam('VP', 7872, 1948.52),
    CurTeam('Liquid', 4734, 1928.64),
    CurTeam('Secret', 4710, 1922.61),
    CurTeam('Mineski', 3150, 1816.20),
    CurTeam('Newbee', 2220, 1880.08),
    CurTeam('Vici', 2160, 1891.08),
    CurTeam('VGJ. Thunder', 1935, 1831.79),
    CurTeam('LGD', 1821, 1913.38),
    CurTeam('EG', 1335, 1898.07),
    CurTeam('NaVi', 1199, 1718.25),
    CurTeam('Fnatic', 950, 1830.65),
    CurTeam('OG', 630, 1835.04, True),
    CurTeam('TNC', 495, 1835.97),
    CurTeam('Optic', 450, 1843.46),
    CurTeam('LFY', 199, 1768.59, True),
    CurTeam('coL', 135, 1795.93, True),
    CurTeam('Immortals', 90, 1660.64),
    CurTeam('Kinguin', 90, 1647.74),
    CurTeam('Vega', 90, 1716.47),
    CurTeam('Echo', 30, 1500),
    CurTeam('IGV', 0, 1664.18),
    CurTeam('IG', 0, 1749.94),
    CurTeam('VGJ. Storm', 0, 1831.67),
    CurTeam('Infamous', 0, 1537.20, True),
    CurTeam('Empire', 0, 1700.81, True),
    CurTeam('paiN', 0, 1632.91, True),
    CurTeam('FTM', 0, 1734.51),
    CurTeam('Spirit', 0, 1678.48),
    CurTeam('Alpha Red', 0, 1450), # this is a complete guess
    CurTeam('Keen Gaming', 0, 1687.90), 
    CurTeam('SG', 0, 1605.67, True), 
    CurTeam('TFT', 0, 1651.26), 

    # Supermajor teams yet to join
    CurTeam('SEA', 0, 1500),
    CurTeam('NA', 0, 1500),
    CurTeam('EU', 0, 1500),
]:
    teams[t.name] = t

mdl, epi = MDL(), Epicenter()
mdl_teams = pluck_t(teams, ['Mineski', 'Newbee', 'Secret', 'Vici', 'IGV', 'IG', 'LGD', 'TNC', 'VGJ. Storm', 'Infamous', 'OG', 'Vega'])
epi_teams = pluck_t(teams, ['VP', 'Liquid', 'Secret', 'Newbee', 'NaVi', 'OG', 'Empire', 'coL', 'paiN', 'LGD', 'Mineski', 'FTM'])
smaj_teams = pluck_t(teams, ['VP', 'Liquid', 'Secret', 'Newbee', 'NaVi', 'EG', 'VGJ. Thunder', 'Vici', 'Mineski', 'OG', 'LGD', 'SEA', 'NA', 'Infamous', 'TFT', 'Spirit'])
gesc_teams = pluck_t(teams, ['Secret', 'EG', 'Alpha Red', 'Fnatic', 'Keen Gaming', 'VGJ. Storm','SG', 'TFT', 'Vega'])
esl_teams = pluck_t(teams, ['VP', 'Newbee', 'EG', 'Liquid', 'Vici', 'Mineski', 'OG', 'NaVi', 'LFY', 'Fnatic', 'Optic', 'paiN'])

for n in range(N):
    points = {}
    for t in teams.values():
        points[t.name] = t.points

    re = mdl.run(mdl_teams)
    #print("MDL: {}".format([_.name for _ in re]))
    points[re[0].name] = points[re[0].name] + (75 * 3)
    points[re[1].name] = points[re[1].name] + (225 * 3)
    points[re[2].name] = points[re[2].name] + (450 * 3)
    points[re[3].name] = points[re[3].name] + (750 * 3)    

    re = epi.run(epi_teams)
    #print("Epi: {}".format([_.name for _ in re]))
    points[re[0].name] = points[re[0].name] + (75 * 3)
    points[re[1].name] = points[re[1].name] + (225 * 3)
    points[re[2].name] = points[re[2].name] + (450 * 3)
    points[re[3].name] = points[re[3].name] + (750 * 3)


    # allocate prizes!

    ordered_teams = sorted(points.items(), key=lambda x: x[1], reverse=True)
    place = 1    

    for p in ordered_teams: 
        top8 = place < 9
        teams[p[0]].add_run(False if teams[p[0]].disqualified else top8, place, p[1])
        if not teams[p[0]].disqualified:
            place += 1

for i, t in enumerate(sorted(teams.values(), key=lambda x: ( 10**7 if not x.disqualified else 0) + ((10**7 * float(x.qualifies)) / N) + (float(x.tot_points) / (100 * N)), reverse=True)):
    exp_pt = float(t.tot_points) / N
    out = "{},{},{},{},{},{}".format(str(1 + i) + ("*" if t.disqualified else ""), t.name, float(t.qualifies) / N, t.points, exp_pt - t.points, exp_pt)
    for place in range(1, 11):
        perc = float(t.placement.get(place, 0)) / N
        out += "," + '{0:.5f}'.format(perc)
    print(out)

