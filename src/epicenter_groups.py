import itertools

class Team:
	def __init__(self, name, rating, rank, region):
		self.name = name
		self.rating = rating
		self.rank = rank
		self.region = region

ts = [
	Team("Liquid", 1931.82, 2, "EU"),
	Team("Mineski", 1867.2, 6, "SEA"),
	Team("Newbee", 1896.16, 5, "China"),
	Team("Col", 1777.44, 8, "NA"),
	Team("FLYTOMOON", 1736.68, 9, "CIS"),
	Team("NaVi", 1703.9, 11, "CIS"),
	Team("Empire", 1719.09, 10, "CIS"),
	Team("Pain", 1630.16, 12, "SA"),
	Team("OG", 1827.96, 7, "EU"),
	Team("LGD", 1908.09, 4, "China"),
	Team("Secret", 1925.56, 3, "EU"),
	Team("VP", 1951.61, 1, "CIS")
]

def g_key(ts):
	return ", ".join(sorted([_.name for _ in ts]))


threshold = 300
seen = {}
for p in itertools.permutations(ts, r=6):
	rest = [t for t in ts if t not in p]

	if len([_ for _ in p if _.region == 'China']) != 1: # 2 China, gotta be split 1/1
		continue

	if len([_ for _ in p if _.region == 'CIS']) != 2: # 2 CIS, gotta be split 1/1
		continue

	if len([_ for _ in p if _.region == 'EU']) not in [1,2]: # 3 EU, so it's gotta be a 1/2 split
		continue

	if len([_ for _ in p if _.name in ["VP", "Liquid"]]) != 1:
		continue

	p_s = sum([t.rating for t in p])
	r_s = sum([t.rating for t in rest])
	rating_diff = abs(p_s - r_s)

	p_ra = sum([t.rank for t in p])
	r_ra = sum([t.rank for t in rest])
	rank_diff = abs(p_ra - r_ra)

	score = (10 * rating_diff) + rank_diff

	if score < threshold:
		if g_key(rest) + " vs " + g_key(p) not in seen:
			seen[g_key(p) + " vs " + g_key(rest)] = score
		
print("Score, groups")
for pair, score in seen.items():
	print("{}: {}".format(score, pair))