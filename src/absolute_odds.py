import itertools
import operator

esl = ["Mineski", "Fnatic", "Optic", "VP", "OG", "Pain"]
sma = ["Mineski", "Newbee", "VGJ", "EG", "TNC", "Vici", "Secret", "Liquid", "VP", "TFT", "EG"]
ignore = ["VP", "Liquid", "OG", "Secret", "Spirit", "Pain", "NaVi", "EG", "LGD", "Storm", "Infamous", 'LFY']

ep = [2250, 1350, 675, 225]
sp =  [3375, 2025, 1011, 336]

scores = {
	'Mineski': 3150,
	'Vici': 2835,
	'Newbee': 2445,
	'VGJ': 1935,
	'EG': 1335,
	'Fnatic': 1040,
	'TNC': 495,
	'Optic': 450,
	'TFT': 0
}

for t in ignore: scores[t] = 0

dmi = {}

make_it, dont_make = 0, 0
fnatic_opt = 0
for _esl in itertools.permutations(esl, 4):
	for _sma in itertools.permutations(sma, 4):
		ss = dict(scores)
		for i, _ in enumerate(_esl):
			ss[_] = ss[_] + ep[i]
		for i, _ in enumerate(_sma):
			ss[_] = ss[_] + sp[i]
		sort_score = sorted(ss.items(), key=operator.itemgetter(1), reverse=True)
		t4 = [_[0] for _ in sort_score if _[0] not in ignore][:4]
		if "Mineski" in t4:
			make_it += 1
		else:
			dont_make += 1

			k = "{} - {}".format(str(sorted(_esl)), str(sorted(_sma)))
			dmi[k] = 1 + dmi.get(k, 0)
			print("{} / {}".format(_esl, _sma))

print("Make it: {}\nDon't Make It: {}".format(make_it, dont_make))
print("")
for i, j in sorted(dmi.items(), key=operator.itemgetter(1), reverse=True):
	print("{}: {}".format(i, j))