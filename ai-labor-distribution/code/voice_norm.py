import re
_DROP={'inc','llc','corp','co','ltd','group','holdings','the'}
def company_norm(name):
    """lowercase; remove '.' and apostrophes; other non-alphanumerics -> space; drop tokens {inc,llc,corp,co,ltd,group,holdings,the}; join with no separators."""
    if name is None: return ''
    s=str(name).lower()
    s=re.sub(r"[.'’`]",'',s)
    s=re.sub(r'[^a-z0-9]+',' ',s)
    toks=[t for t in s.split() if t not in _DROP]
    return ''.join(toks)
