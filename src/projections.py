from utils import * 
import copy

N = 10**4

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
    def run(self, teams):
        lgd = [t for t in teams if t.name == 'LGD'][0]
        vici = [t for t in teams if t.name == 'Vici'][0]
        vgjs = [t for t in teams if t.name == 'VGJ. Storm'][0]

        lb_finals = boX(vici, lgd, func='glicko')

        finals = boX(lb_finals[0], vgjs, func='glicko')

        return [lb_finals[1], finals[1], finals[0]]

class ESL:
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
        first_run = rr_fixed_games(_ts, func='glicko')
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
                        tiebreakers = rr_fixed_games(tied, func='glicko')
                        if self.broken(tiebreakers.values()):
                            flag = False # tie broken, last set of tiebreakers are good
                    for _t, r in tiebreakers.items():
                        first_run[_t].tiebreakers = r.wins
                tied = []
            cur = res.score()

        return [_.team for _ in sorted(first_run.values(), key=lambda x: x.score(), reverse=True)]


    def run(self, teams):
        dec_a = boX([t for t in teams if t.name == 'Fnatic'][0], [t for t in teams if t.name == 'Spirit'][0], func='glicko')
        dec_b = boX([t for t in teams if t.name == 'paiN'][0], [t for t in teams if t.name == 'Liquid'][0], func='glicko')
        dec_c = boX([t for t in teams if t.name == 'Mineski'][0], [t for t in teams if t.name == 'LFY'][0], func='glicko')

        winners = self.resolve_placings([[t for t in teams if t.name == 'VP'][0], [t for t in teams if t.name == 'OG'][0], [t for t in teams if t.name == 'Optic'][0]])
        rups = sorted([dec_a[0], dec_a[0], dec_a[0]], key=lambda x: random()) # [_.team for _ in self.resolve_placings([gr_a[1], gr_b[1], gr_c[1]])]

        qf_1 = boX(rups[0], rups[1], func='glicko')
        qf_2 = boX(winners[2], rups[2], func='glicko')

        semifinal_1 = boX(qf_1[0], winners[0], func='glicko')
        semifinal_2 = boX(qf_2[0], winners[1], func='glicko')            

        decider = boX(semifinal_1[1], semifinal_2[1], func='glicko')

        finals = boX(semifinal_1[0], semifinal_2[0], 3, func='glicko')

        return [decider[1], decider[0], finals[1], finals[0]]

class SMaj:
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
        a = [1, 3, 5, 7, 9, 11, 13, 15]
        gr_a = self.resolve_group([_ for _ in teams if _.rank in a])
        gr_b = self.resolve_group([_ for _ in teams if _.rank not in a])

        # winners bracket
        wb_r1_1 = boX(gr_a[0], gr_b[3], func='glicko')
        wb_r1_2 = boX(gr_a[2], gr_b[1], func='glicko')
        wb_r1_3 = boX(gr_a[3], gr_b[0], func='glicko')
        wb_r1_4 = boX(gr_a[1], gr_b[2], func='glicko')

        wb_r1_1 = boX(wb_r1_1[0], wb_r1_2[0], func='glicko')
        wb_r1_2 = boX(wb_r1_3[0], wb_r1_4[0], func='glicko')

        wb_final = boX(wb_r1_1[0], wb_r1_2[0], func='glicko')

        # losers bracket
        lb_r1_1 = boX(wb_r1_1[0], wb_r1_2[1], func='glicko')
        lb_r1_2 = boX(wb_r1_3[0], wb_r1_3[1], func='glicko')

        lb_r2_1 = boX(lb_r1_1[0], wb_r1_2[1], func='glicko')
        lb_r2_2 = boX(lb_r1_2[0], wb_r1_1[1], func='glicko')

        lb_sf = boX(lb_r2_1[0], lb_r2_2[0], func='glicko')
        lb_finals = boX(lb_sf[0], wb_final[1], func='glicko')

        finals = boX(lb_finals[0], wb_final[0], func='glicko')

        return [lb_sf[1], lb_finals[1], finals[1], finals[0]]

eighth = []
teams = {}

for t in [
    # name, points, rating, disqualified
    CurTeam('VP', 8097, 1933),
    CurTeam('Liquid', 6084, 1940),
    CurTeam('Secret', 4800, 1910),
    CurTeam('Mineski', 3150, 1875),
    CurTeam('Newbee', 2445, 1882),
    CurTeam('Vici', 2835, 1917),
    CurTeam('VGJ. Thunder', 1935, 1814),
    CurTeam('LGD', 6321, 1942),
    CurTeam('EG', 1335, 1885),
    CurTeam('NaVi', 1199, 1724, True),
    CurTeam('Fnatic', 1040, 1851),
    CurTeam('OG', 630, 1827, True),
    CurTeam('TNC', 495, 1851),
    CurTeam('Optic', 450, 1834),
    CurTeam('LFY', 199, 1741, True),
    CurTeam('coL', 135, 1764, True),
    CurTeam('Immortals', 90, 1673),
    CurTeam('Kinguin', 90, 1630),
    CurTeam('Vega', 90, 1684),
    CurTeam('Echo', 30, 1500, True),
    CurTeam('IGV', 0, 1655, True),
    CurTeam('IG', 0, 1761, True),
    CurTeam('VGJ. Storm', 1347, 1930, True),
    CurTeam('Infamous', 0, 1511, True),
    CurTeam('Empire', 0, 1683, True),
    CurTeam('paiN', 0, 1657, True),
    CurTeam('FTM', 675, 1734.51),
    CurTeam('Spirit', 0, 1678.48, True),
    CurTeam('Alpha Red', 0, 1450, True), # this is a complete guess
    CurTeam('Keen Gaming', 0, 1728, True), 
    CurTeam('SG', 0, 1605.67, True), 
    CurTeam('TFT', 0, 1675)
]:
    teams[t.name] = t

esl, smaj = ESL(), SMaj()
mdl_teams = pluck_t(teams, ['Mineski', 'Newbee', 'Secret', 'Vici', 'IGV', 'IG', 'LGD', 'TNC', 'VGJ. Storm', 'Infamous', 'OG', 'Vega'])
epi_teams = pluck_t(teams, ['VP', 'Liquid', 'Secret', 'Newbee', 'NaVi', 'OG', 'Empire', 'coL', 'paiN', 'LGD', 'Mineski', 'FTM'])
smaj_teams = pluck_t(teams, ['VP', 'Liquid', 'Secret', 'Newbee', 'NaVi', 'EG', 'VGJ. Thunder', 'Vici', 'Mineski', 'OG', 'LGD', 'TNC', 'VGJ. Storm', 'Infamous', 'TFT', 'Spirit'])
gesc_teams = pluck_t(teams, ['Secret', 'EG', 'Alpha Red', 'Fnatic', 'Keen Gaming', 'VGJ. Storm','SG', 'TFT'])
esl_teams = pluck_t(teams, ['VP', 'Newbee', 'EG', 'Liquid', 'Vici', 'Mineski', 'OG', 'Spirit', 'LFY', 'Fnatic', 'Optic', 'paiN'])

for n in range(N):
    points = {}
    for t in teams.values():
        points[t.name] = t.points       

    re = esl.run(esl_teams)
    #print("ESL: {}".format([_.name for _ in re]))
    points[re[0].name] = points[re[0].name] + (75 * 3)
    points[re[1].name] = points[re[1].name] + (225 * 3)
    points[re[2].name] = points[re[2].name] + (450 * 3)
    points[re[3].name] = points[re[3].name] + (750 * 3)    

    re = smaj.run(smaj_teams)
    #print("Super Major: {}".format([_.name for _ in re]))
    points[re[0].name] = points[re[0].name] + (75 * 3)
    points[re[1].name] = points[re[1].name] + (225 * 3)
    points[re[2].name] = points[re[2].name] + (450 * 3)
    points[re[3].name] = points[re[3].name] + (750 * 3)    

    # allocate prizes (placements)!
    ordered_teams = sorted(points.items(), key=lambda x: x[1], reverse=True)
    place = 1    

    for p in ordered_teams: 
        if not teams[p[0]].disqualified:
            top8 = place < 9
            teams[p[0]].add_run(top8, place, p[1])
            place += 1
            if place == 8:
                eighth.append(p[1])
        else:
            teams[p[0]].add_run(False, 'dq', p[1])

for i, t in enumerate(sorted(teams.values(), key=lambda x: ( 10**7 if not x.disqualified else 0) + ((10**7 * float(x.qualifies)) / N) + (float(x.tot_points) / (100 * N)), reverse=True)):
    exp_pt = float(t.tot_points) / N
    out = "{},{},{},{},{},{}".format(str(1 + i) + ("x" if t.disqualified else ""), t.name, float(t.qualifies) / N, t.points, exp_pt - t.points, exp_pt)
    for place in range(1, 11):
        perc = float(t.placement.get(place, 0)) / N
        out += "," + '{0:.5f}'.format(perc)
    print(out)
print("\n")
print(float(sum(eighth))/N)

