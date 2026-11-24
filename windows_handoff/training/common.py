import re
V = {'अ':'a','आ':'aa','इ':'i','ई':'ee','उ':'u','ऊ':'oo','ऋ':'ri','ए':'e','ऐ':'ai','ओ':'o','औ':'au','ऑ':'o','ऍ':'e'}
M = {'ा':'aa','ि':'i','ी':'ee','ु':'u','ू':'oo','ृ':'ri','े':'e','ै':'ai','ो':'o','ौ':'au','ॉ':'o','ॅ':'e'}
C = {'क':'k','ख':'kh','ग':'g','घ':'gh','ङ':'n','च':'ch','छ':'chh','ज':'j','झ':'jh','ञ':'n','ट':'t','ठ':'th','ड':'d','ढ':'dh','ण':'n',
     'त':'t','थ':'th','द':'d','ध':'dh','न':'n','प':'p','फ':'ph','ब':'b','भ':'bh','म':'m','य':'y','र':'r','ल':'l','व':'v','श':'sh','ष':'sh',
     'स':'s','ह':'h','क़':'q','ख़':'kh','ग़':'g','ज़':'z','ड़':'d','ढ़':'rh','फ़':'f','ळ':'l'}
NUK = {'क':'q','ख':'kh','ग':'g','ज':'z','ड':'d','ढ':'rh','फ':'f'}
def _word(w, drop_schwa=True):
    out = []; i = 0; n = len(w)
    while i < n:
        ch = w[i]
        if ch in C:
            base = C[ch]
            if i+1 < n and w[i+1] == '़': base = NUK.get(ch, base); i += 1
            nxt = w[i+1] if i+1 < n else ''
            if nxt == '्': out.append(base); i += 2; continue
            if nxt in M: out.append(base + M[nxt]); i += 2; continue
            out.append(base + 'a'); i += 1; continue
        if ch in V: out.append(V[ch])
        elif ch in 'ंँ': out.append('n')
        elif ch == 'ः': out.append('h')
        elif '०' <= ch <= '९': out.append(str(ord(ch) - ord('०')))
        elif ch in '़्।': pass
        else: out.append(ch)
        i += 1
    s = ''.join(out)
    if drop_schwa and len(s) > 3 and s.endswith('a') and not s.endswith('aa') and w[-1] in C:
        s = s[:-1]
    return s
def romanize(text, drop_schwa=True):
    return ' '.join(_word(w, drop_schwa) for w in text.split()).lower()

import pandas as pd
def light(s):  # casual short-vowel spelling: 'kripayaa' -> 'kripaya', 'eemel' -> 'imel'
    return s.replace('aa', 'a').replace('ee', 'i').replace('oo', 'u')
def is_dev(s):
    return bool(re.search('[ऀ-ॿ]', s))
def norm(s):
    s = str(s).strip()
    return s if is_dev(s) else s.lower()
import random as _random
_SPELL = [(r'\bkya\b', ['kia', 'kya', 'kyaa']), (r'\bhai\b', ['h', 'hai', 'he']), (r'\bhain\b', ['h', 'hain', 'hai']),
          (r'\bmujhe\b', ['mjhe', 'mujhe', 'muje']), (r'\bnahin?\b', ['nhi', 'nahi', 'nai']), (r'\bkaro\b', ['kro', 'karo', 'kar do']),
          (r'\bkaren\b', ['kare', 'karo', 'kren']), (r'\bkarein\b', ['kare', 'karo']), (r'\baap\b', ['ap', 'aap', 'tum']),
          (r'\bmein\b', ['me', 'mai', 'mein']), (r'\bmen\b', ['me', 'mein']), (r'\bkripaya\b', ['please', 'plz', 'kripya']),
          (r'\bkripayaa\b', ['please', 'plz']), (r'\bke liye\b', ['ke liye', 'ke lie', 'k liye']), (r'\bbhi\b', ['bhi', 'b']),
          (r'\bthik\b', ['theek', 'thik']), (r'\baur\b', ['or', 'aur'])]
_EN = [(r'\bbatti(?:yaan|yan|yon|yaa)?\b', 'lights'), (r'\broshanee\b|\broshni\b', 'light'), (r'\bchaal?oo?\b', 'on'),
       (r'\bband\b', 'off'), (r'\bsangeet\b', 'music'), (r'\bgaanaa?\b', 'song'), (r'\bgaane\b', 'songs'),
       (r'\bmausam\b', 'weather'), (r'\bsamay\b', 'time'), (r'\bsandesh\b', 'message'), (r'\bbhejo\b', 'send karo'),
       (r'\bhataa?o\b', 'delete karo'), (r'\bhataa?en\b', 'delete karo'), (r'\byaad dilaa?o\b', 'remind karo'),
       (r'\bsamaachaar\b|\bkhabar\b', 'news'), (r'\bkal\b', 'tomorrow'), (r'\baaj\b', 'today'), (r'\bghar\b', 'home'),
       (r'\btaareekh\b|\btarikh\b', 'date'), (r'\bsoochee\b|\bsuchi\b', 'list'), (r'\bphon\b', 'phone'),
       (r'\bvolyoom\b|\bvolyum\b', 'volume'), (r'\bkailendar\b', 'calendar'), (r'\beemel\b|\bimel\b', 'email')]
_FILL_PRE = ['', '', '', 'please ', 'plz ', 'google ', 'alexa ', 'bhai ', 'yaar ', 'hey ']
_FILL_SUF = ['', '', '', ' please', ' bhai', ' na', ' yaar', ' plz', ' jaldi', ' abhi']
def chatify(s, rng):
    """Casual Hinglish rewrite of a romanized query: texting spellings, English swaps, fillers."""
    for pat, opts in _SPELL:
        if rng.random() < 0.6: s = re.sub(pat, lambda m: rng.choice(opts), s)
    for pat, rep in _EN:
        if rng.random() < 0.5: s = re.sub(pat, rep, s)
    if rng.random() < 0.3: s = light(s)
    s = rng.choice(_FILL_PRE) + s + rng.choice(_FILL_SUF)
    return re.sub(r'\s+', ' ', s).strip()
def augment(df, seed=42, chat=True, pseudo=None):
    """Training set = originals + romanized (full/light) copies of Devanagari rows
    + one casual 'chat' copy of every romanized row + optional pseudo-labelled test rows."""
    rows = [df[['query_text', 'y']]]
    d = df[~df.roman]
    r1 = d.query_text.map(romanize); r2 = r1.map(light)
    rows += [pd.DataFrame({'query_text': r1, 'y': d.y}), pd.DataFrame({'query_text': r2, 'y': d.y})]
    if pseudo is not None and len(pseudo):
        rows.append(pseudo[['query_text', 'y']])
    out = pd.concat(rows)
    if chat:
        rng = _random.Random(seed)
        ro = out[~out.query_text.map(is_dev)]
        rows.append(pd.DataFrame({'query_text': [chatify(t, rng) for t in ro.query_text], 'y': ro.y.values}))
        out = pd.concat([out, rows[-1]])
    out = out.drop_duplicates(['query_text', 'y']).sample(frac=1, random_state=seed)
    return out.reset_index(drop=True)

import collections
def _key(s):
    s = light(s.lower()); s = re.sub(r'[^a-z0-9 ]', '', s); s = re.sub(r'(.)\1+', r'\1', s)
    return s.replace('w', 'v').replace('sh', 's').replace('ph', 'f').replace('z', 'j')
def _grams(s):
    s = ' ' + s + ' '; return {s[i:i+3] for i in range(len(s) - 2)}
def twin_groups(texts, thresh=0.5):
    """Group id per row: a romanized row shares its group with its most similar Devanagari row
    (its transliteration twin), so CV folds never split a sentence from its twin."""
    texts = list(texts); groups = list(range(len(texts)))
    dv = [i for i, t in enumerate(texts) if is_dev(t)]
    G = {i: _grams(_key(romanize(texts[i]))) for i in dv}
    idx = collections.defaultdict(list)
    for i in dv:
        for t in G[i]: idx[t].append(i)
    for j, t in enumerate(texts):
        if is_dev(t): continue
        g = _grams(_key(t)); cnt = collections.Counter()
        for x in g:
            for i in idx.get(x, ()): cnt[i] += 1
        if not cnt: continue
        s, i = max((c / (len(g) + len(G[i]) - c), i) for i, c in cnt.items())
        if s >= thresh: groups[j] = groups[i]
    return groups
