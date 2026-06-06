import re, math
from collections import Counter, defaultdict

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").translate(TR_MAP).lower()).strip()

def tokens(text: str):
    return re.findall(r"[a-zA-Z0-9]+", normalize(text))

def cosine_rank(query: str, docs: list[str]):
    if not docs:
        return []
    all_docs = [tokens(query)] + [tokens(d) for d in docs]
    n = len(all_docs)
    df = defaultdict(int)
    for doc in all_docs:
        for t in set(doc): df[t]+=1
    def vec(doc):
        c=Counter(doc); v={}
        for t,tf in c.items():
            idf=math.log((n+1)/(df[t]+1))+1
            v[t]=(1+math.log(tf))*idf
        return v
    qv=vec(all_docs[0])
    qnorm=math.sqrt(sum(x*x for x in qv.values())) or 1.0
    ranked=[]
    for i,doc in enumerate(all_docs[1:]):
        dv=vec(doc); dnorm=math.sqrt(sum(x*x for x in dv.values())) or 1.0
        dot=sum(qv.get(t,0)*dv.get(t,0) for t in qv)
        ranked.append((i, dot/(qnorm*dnorm)))
    return sorted(ranked, key=lambda x:x[1], reverse=True)
