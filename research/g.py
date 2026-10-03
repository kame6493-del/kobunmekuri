import json,sys,re
S=[json.loads(l) for l in open('sentences.jsonl',encoding='utf-8')]
pri={"枕草子":0,"徒然草":0,"竹取物語":1,"更級日記":1,"方丈記":1,"源氏物語":2}
for pat in sys.argv[1:]:
    rx=re.compile(pat); hs=[s for s in S if rx.search(s['text'])]
    hs.sort(key=lambda s:(pri.get(s['work'],3),len(s['text'])))
    print(f"## {pat} ({len(hs)})")
    for s in hs[:7]: print(f"  {s['id']} {s['work']}{s['loc']} {s['text'][:90]}")
