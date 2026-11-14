"""Feature builders shared by training (03) and application (04)."""
import re

import numpy as np
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer

from annot_tools import snippet
from common import DATA

EMB_MODELS = {"minilm": "sentence-transformers/all-MiniLM-L6-v2",
              "mpnet": "sentence-transformers/all-mpnet-base-v2"}

RX = [re.compile(p, re.I) for p in (
    r"\b(i|we|my|our|i've|we've|i'm|we're)\b",                       # first person
    r"\b(moved|left|relocated|got out)\b",                            # past tense move
    r"\b(moving|leaving|planning|considering|thinking|will|going to|soon|next (year|month))\b",
    r"(moved|moving|relocat\w+|left|leaving)[^.]{0,30}\b(to|out of|for)\b",
    r"\b(moved|moving|move) (back|here|to (the bay|sf|san francisco|oakland|san jose|berkeley))",
)]


def model_input(df):
    """Same ~650-char window the annotator saw, prefixed with a coarse context tag
    (the Bay is the implicit origin in Bay-local subreddits)."""
    tag = np.where(df.group == "bay_local", "[bay subreddit] ", "[other subreddit] ")
    return [t + snippet(x) for t, x in zip(tag, df.text)]


def rx_feats(texts):
    return np.array([[bool(r.search(t)) for r in RX] + [len(t) > 400] for t in texts], float)


def embed(texts, key, cache_name=None):
    if cache_name:
        cache = DATA / f"emb_{key}_{cache_name}.npy"
        if cache.exists():
            e = np.load(cache)
            if len(e) == len(texts):
                return e
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(EMB_MODELS[key], device="cpu")
    e = m.encode(list(texts), batch_size=32, show_progress_bar=False, normalize_embeddings=True)
    if cache_name:
        np.save(cache, e)
    return e


class Featurizer:
    """kind in {tfidf, emb_minilm, emb_mpnet, hybrid}; hybrid = word TF-IDF + MiniLM + regex flags."""

    def __init__(self, kind):
        self.kind = kind

    def fit(self, texts):
        if self.kind in ("tfidf", "hybrid"):
            self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit(texts)
        return self

    def transform(self, texts, emb=None):
        k = self.kind
        if k == "tfidf":
            return self.vec.transform(texts)
        if k.startswith("emb_"):
            return emb if emb is not None else embed(texts, k[4:])
        e = emb if emb is not None else embed(texts, "minilm")
        return hstack([self.vec.transform(texts), csr_matrix(e), csr_matrix(rx_feats(texts))]).tocsr()
