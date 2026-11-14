# Experiment J: Labor-demand recomposition (Indeed postings, Bay Area)

Source: base/indeed_base_v3.parquet (n=134,595 CA postings; 45,850 Bay Area). All numbers below were computed by scripts `code/jobs_*.py`; tables are saved as `base/jobs_*.csv`. AI_POSITIONED = AI_PRODUCER + SOFTWARE_ENG + DATA_ENG_ANALYTICS; EXPOSED = CLERICAL_ADMIN + CUSTOMER_SUPPORT + PROF_EXPOSED.

## Read this first: three data cautions that shape every result

1. **No time trend is claimed.** 55.8% of rows are censored at "30+ days ago" (post_date = crawl - 30d). Uncensored Bay rows dated May-Aug 2026 are the only usable time slice, and that slice is a biased subsample (fast-filling or freshly posted roles). See "Time" section: the apparent rise in AI_POSITIONED share across months is a crawl-seeding artifact. Treat as **uninterpretable**.
2. **Crawl seeding (v3).** 20.2% of Bay rows came from keyword-seeded searches skewed to tech/AI titles. All SHARE/MIX claims use the unseeded subsample (Bay n=36,587) as primary, full sample alongside. Pay-within-class, regression, requirement and transparency results are much less sensitive; `seeded` is a control in the regressions.
3. **Hourly annualization is not innocent.** Salary is annualized at 2080 hours. Bay salaried postings split 23,347 annual-posted / 14,995 hourly-posted; part-time share of hourly-posted is 48% in FRONTLINE_SERVICE, 28% in EXPOSED, 93% in AI_DATA_WORK. Annualizing overstates realized annual pay for the hourly, part-time-heavy classes, which *shrinks* the apparent gap between AI_POSITIONED and the rest. Class pay is therefore reported both ways below. Sample for pay: postings with usable salary (10k-1.5M annualized after trimming; 530 CA rows dropped).

## The headline numbers

1. **Posted pay gap.** Bay median posted pay (annualized) for AI_POSITIONED is **$210,000** vs **$72,800** for EXPOSED: ratio **2.88x** (bootstrap 95% CI 2.81-2.99), gap **$137,200**; vs FRONTLINE_SERVICE ($44,720) 4.70x, gap $165,280. On the unseeded sample the EXPOSED ratio is 3.04x. Holding pay *type* fixed the gap is smaller: annual-posted only, POS $213,000 vs EXPOSED $109,874 = **1.94x**; hourly-posted only, $109,897 vs $52,000 = **2.11x**. So the honest range is roughly 1.9x-2.9x; the pooled 2.9x is partly a pay-type composition effect.
2. **Class explains about half of posted-wage variance.** Between-occupation-class share of var(log sal_mid) in the Bay = **48.6%** (17 classes; 50.0% unseeded; 47.8% for the 13-group collapse); 51.4% is within class. Dropping AI_POSITIONED postings lowers the Bay median posted pay from $125,000 to **$95,000** (unseeded: $119,000 to $90,000); AI_POSITIONED is 21.1% of salaried Bay postings.
3. **Labor demand mix.** AI_POSITIONED = **18.8%** of unseeded Bay postings vs EXPOSED 8.3% (ratio **2.26**; full sample 21.3% vs 7.8%, 2.72). By county, AI_POSITIONED share runs from 27.3% (Santa Clara) and 24.9% (San Francisco) to 0.4% (Napa), 0.9% (Sonoma).
4. **The AI premium is real in cross-section but it is not an AI_POSITIONED-only story and it mostly disappears within firm for "AI use".** With occupation and city FE (cluster by company, n=38,691): ai_build +0.144 (se 0.014), ai_use +0.074 (0.025), ai_brand +0.128 (0.018) log points. Inside EXPOSED occupations the ai_use premium is **+0.126 (0.036)**, larger than inside AI_POSITIONED (+0.014, se 0.022). But adding company FE, EXPOSED ai_use falls to **+0.029 (0.037), not distinguishable from zero**: AI-using exposed roles are at higher-paying employers, not paid more than that employer's other exposed roles.

**Also notable (contradicts parts of the working hypothesis):** the entry rung in EXPOSED is *not* thinner (23.9% of unseeded Bay exposed postings are entry-level vs 4.2% in AI_POSITIONED); exposed postings are not notably more opaque on pay; and AI-use does not carry a negative premium in exposed roles.

## TEST 1: The prize (Bay Area, posted pay by class)

Annualized (hourly x 2080), all Bay postings; share_with_salary = usable salary.

| class | n | share_postings_all | share_postings_unseeded | share_with_salary | median_annualized | p25 | p75 | p90 | median_sal_lo | median_sal_hi |
|---|---|---|---|---|---|---|---|---|---|---|
| AI_PRODUCER | 4158 | 0.091 | 0.085 | 0.837 | 214,500 | 180,000 | 254,000 | 300,000 | 165,000 | 260,000 |
| SOFTWARE_ENG | 5038 | 0.110 | 0.093 | 0.834 | 208,000 | 173,250 | 243,600 | 281,300 | 163,465 | 250,000 |
| PRODUCT_DESIGN | 1633 | 0.036 | 0.035 | 0.852 | 187,500 | 145,800 | 219,950 | 254,475 | 150,000 | 220,000 |
| LEGAL_PROF | 302 | 0.007 | 0.008 | 0.864 | 187,500 | 150,092 | 239,215 | 277,000 | 150,000 | 220,000 |
| DATA_ENG_ANALYTICS | 558 | 0.012 | 0.010 | 0.828 | 175,500 | 140,000 | 218,688 | 264,907 | 140,000 | 210,000 |
| MANAGEMENT | 6578 | 0.143 | 0.143 | 0.860 | 164,250 | 105,079 | 219,750 | 271,500 | 135,000 | 190,000 |
| OTHER_ENGINEERING | 1378 | 0.030 | 0.029 | 0.814 | 160,500 | 121,173 | 200,000 | 234,998 | 129,300 | 192,000 |
| AI_DATA_WORK | 145 | 0.003 | 0.003 | 0.986 | 156,000 | 156,000 | 156,000 | 198,182 | 104,000 | 208,000 |
| SALES_BIZ | 1951 | 0.043 | 0.042 | 0.781 | 116,000 | 80,000 | 175,000 | 232,500 | 92,000 | 140,000 |
| OTHER | 8818 | 0.192 | 0.199 | 0.820 | 102,500 | 58,240 | 163,000 | 214,000 | 85,000 | 116,480 |
| PROF_EXPOSED | 1309 | 0.029 | 0.029 | 0.820 | 98,800 | 75,000 | 135,000 | 172,580 | 84,000 | 110,000 |
| HEALTH_CLINICAL | 3301 | 0.072 | 0.068 | 0.889 | 97,500 | 57,200 | 145,000 | 204,214 | 85,530 | 106,371 |
| SKILLED_TRADE | 2188 | 0.048 | 0.047 | 0.876 | 68,640 | 54,621 | 91,624 | 127,668 | 60,000 | 76,960 |
| EDUCATION | 781 | 0.017 | 0.020 | 0.894 | 65,900 | 53,040 | 100,590 | 156,936 | 58,240 | 72,800 |
| CUSTOMER_SUPPORT | 979 | 0.021 | 0.023 | 0.862 | 62,000 | 46,176 | 105,000 | 171,570 | 52,000 | 68,900 |
| CLERICAL_ADMIN | 1304 | 0.028 | 0.032 | 0.769 | 57,200 | 46,800 | 78,312 | 106,953 | 52,000 | 62,400 |
| FRONTLINE_SERVICE | 5429 | 0.118 | 0.135 | 0.875 | 44,720 | 40,560 | 53,643 | 71,760 | 41,600 | 47,819 |

Same classes in posted-hourly terms (hourly-posted subset only) and annual-posted-only medians:

| class | n_sal | share_of_salaried_posted_hourly | n_hourly | median_hourly_rate | p25_rate | p75_rate | parttime_share_of_hourly_posted | n_annual_posted | median_annual_posted_only |
|---|---|---|---|---|---|---|---|---|---|
| AI_PRODUCER | 3480 | 0.036 | 127 | 60.0 | 45.0 | 75.8 | 0.102 | 3339 | 215,950 |
| SOFTWARE_ENG | 4204 | 0.044 | 185 | 52.5 | 38.5 | 70.0 | 0.162 | 4008 | 211,655 |
| PRODUCT_DESIGN | 1391 | 0.085 | 118 | 46.2 | 30.2 | 73.8 | 0.110 | 1265 | 193,200 |
| LEGAL_PROF | 261 | 0.027 | 7 | 71.0 | 57.2 | 90.0 | 0.143 | 252 | 187,500 |
| DATA_ENG_ANALYTICS | 462 | 0.084 | 39 | 52.8 | 44.5 | 67.1 | 0.051 | 422 | 182,025 |
| MANAGEMENT | 5655 | 0.153 | 867 | 28.5 | 22.8 | 37.5 | 0.221 | 4755 | 176,850 |
| OTHER_ENGINEERING | 1122 | 0.079 | 89 | 50.5 | 35.7 | 67.7 | 0.101 | 1027 | 165,200 |
| AI_DATA_WORK | 143 | 0.937 | 134 | 75.0 | 75.0 | 75.0 | 0.933 | 9 | 182,000 |
| SALES_BIZ | 1523 | 0.093 | 141 | 26.0 | 22.0 | 32.4 | 0.177 | 1365 | 125,000 |
| OTHER | 7230 | 0.448 | 3241 | 27.5 | 22.5 | 37.5 | 0.313 | 3867 | 152,000 |
| PROF_EXPOSED | 1073 | 0.277 | 297 | 32.5 | 26.0 | 40.0 | 0.209 | 768 | 114,125 |
| HEALTH_CLINICAL | 2935 | 0.727 | 2134 | 35.5 | 24.5 | 62.5 | 0.393 | 695 | 127,500 |
| SKILLED_TRADE | 1917 | 0.770 | 1476 | 30.0 | 25.0 | 38.4 | 0.084 | 405 | 104,250 |
| EDUCATION | 698 | 0.782 | 546 | 29.0 | 24.5 | 42.5 | 0.604 | 128 | 89,608 |
| CUSTOMER_SUPPORT | 844 | 0.581 | 490 | 23.5 | 20.5 | 27.3 | 0.304 | 339 | 115,032 |
| CLERICAL_ADMIN | 1003 | 0.760 | 762 | 25.0 | 21.5 | 30.0 | 0.295 | 235 | 95,000 |
| FRONTLINE_SERVICE | 4753 | 0.908 | 4314 | 21.0 | 19.2 | 24.0 | 0.485 | 383 | 105,000 |

Collapsed groups, unseeded Bay sample (for mix-sensitive comparison):

| cls | n | share_unseeded | n_sal | med | p25 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| AI_POSITIONED | 6896 | 0.188 | 5683 | 213,500 | 177,300 | 251,750 | 299,980 |
| PRODUCT_DESIGN | 1285 | 0.035 | 1079 | 189,850 | 150,000 | 221,750 | 254,750 |
| LEGAL_PROF | 279 | 0.008 | 239 | 187,500 | 150,092 | 243,300 | 277,370 |
| OTHER_ENGINEERING | 1070 | 0.029 | 854 | 167,550 | 128,167 | 204,425 | 240,700 |
| MANAGEMENT | 5220 | 0.143 | 4432 | 167,050 | 107,500 | 222,500 | 272,750 |
| AI_DATA_WORK | 113 | 0.003 | 111 | 156,000 | 156,000 | 156,000 | 198,182 |
| SALES_BIZ | 1520 | 0.042 | 1137 | 115,000 | 80,900 | 175,000 | 236,262 |
| HEALTH_CLINICAL | 2471 | 0.068 | 2159 | 100,000 | 58,240 | 147,550 | 211,640 |
| OTHER | 7285 | 0.199 | 5890 | 97,500 | 56,160 | 160,500 | 214,000 |
| EXPOSED | 3055 | 0.083 | 2421 | 70,200 | 49,920 | 106,766 | 147,600 |
| SKILLED_TRADE | 1726 | 0.047 | 1474 | 68,640 | 54,080 | 92,560 | 126,246 |
| EDUCATION | 714 | 0.020 | 632 | 66,560 | 53,040 | 104,000 | 158,808 |
| FRONTLINE_SERVICE | 4953 | 0.135 | 4303 | 44,439 | 40,477 | 52,000 | 69,482 |

Notes. AI_DATA_WORK's $156,000 "median" is an artifact (see Test 4): do not use the P/AI_DATA_WORK ratio (1.35x, gap $54,000) as a finding. California contrast: POS $194,400 vs EXPOSED $57,902 (3.36x), FRONTLINE $42,640; CA overall median $78,000 and $70,000 without AI_POSITIONED. The variance decomposition uses log(sal_mid) of salaried postings; "occupation x city" cells explain 57.7% but that is an upper bound inflated by small cells.

## TEST 2: The AI premium, properly identified

OLS on log(sal_mid), controls: seeded, senior, junior, fulltime, contract, remote, deg_ba, yrs_min (0 if missing + missing dummy), log desc_len; occupation-class (17) and city FE (cities with <30 salaried postings pooled); SEs clustered by company_norm; * = p<0.05. Coefficients are log points (0.10 = about 10.5%). **This is a cross-sectional association with selection on unobservables, not a causal estimate.**

All Bay postings (and CA):

| spec | ai_build | ai_use | ai_brand | n |
|---|---|---|---|---|
| Bay|all|no FE no controls | +0.455 (0.026)* | +0.319 (0.050)* | +0.426 (0.036)* | 38691 |
| Bay|all|occ FE only | +0.163 (0.014)* | +0.094 (0.031)* | +0.153 (0.019)* | 38691 |
| Bay|all|occ+city FE|ai_build/use/brand | +0.144 (0.014)* | +0.074 (0.025)* | +0.128 (0.018)* | 38691 |
| Bay|all|occ+city+COMPANY FE (within-firm) | +0.068 (0.010)* | -0.014 (0.007) | +0.035 (0.008)* | 38691 |
| Bay|all, unseeded only|occ+city FE | +0.161 (0.017)* | +0.080 (0.026)* | +0.126 (0.020)* | 30412 |
| Bay|all, annual-posted only|occ+city FE | +0.107 (0.013)* | +0.038 (0.023) | +0.070 (0.015)* | 23260 |
| CA|all|occ+city FE|ai_build/use/brand | +0.156 (0.013)* | +0.065 (0.020)* | +0.157 (0.016)* | 114517 |

Where does it sit (Bay unless labelled):

| spec | ai_build | ai_use | ai_brand | n |
|---|---|---|---|---|
| Bay|within AI_POSITIONED|occ+city FE | +0.078 (0.010)* | +0.014 (0.022) | +0.008 (0.014) | 8146 |
| Bay|within AI_POSITIONED|occ+city+COMPANY FE | +0.042 (0.010)* | -0.016 (0.009) | +0.015 (0.009) | 8146 |
| Bay|within EXPOSED|occ+city FE | +0.199 (0.045)* | +0.126 (0.036)* | +0.214 (0.041)* | 2920 |
| Bay|within EXPOSED|occ+city+COMPANY FE | +0.140 (0.068)* | +0.029 (0.037) | +0.088 (0.043)* | 2920 |
| Bay|within EXPOSED, unseeded only|occ+city FE | +0.218 (0.048)* | +0.149 (0.041)* | +0.211 (0.051)* | 2421 |
| Bay|within EXPOSED, annual-posted only|occ+city FE | +0.156 (0.047)* | +0.080 (0.033)* | +0.123 (0.041)* | 1342 |
| Bay|within EXPOSED, firms <30% AI_POSITIONED postings|occ+city FE | +0.231 (0.077)* | +0.117 (0.049)* | +0.146 (0.070)* | 2430 |
| Bay|within EXPOSED, firms >=30% AI_POSITIONED postings|occ+city FE | +0.083 (0.057) | +0.046 (0.038) | +0.120 (0.031)* | 490 |
| Bay|within FRONTLINE_SERVICE|occ+city FE | +0.367 (0.210) | +0.222 (0.085)* | +0.335 (0.110)* | 4753 |
| Bay|within occ=CLERICAL_ADMIN|city FE | +0.322 (0.057)* | +0.293 (0.055)* | +0.177 (0.056)* | 1003 |
| Bay|within occ=CUSTOMER_SUPPORT|city FE | +0.208 (0.113) | +0.049 (0.062) | +0.267 (0.062)* | 844 |
| Bay|within occ=PROF_EXPOSED|city FE | +0.141 (0.053)* | +0.088 (0.044)* | +0.153 (0.048)* | 1073 |
| Bay|within occ=SOFTWARE_ENG|city FE | +0.076 (0.014)* | +0.057 (0.027)* | +0.024 (0.017) | 4204 |
| Bay|within occ=AI_PRODUCER|city FE | +0.062 (0.012)* | -0.028 (0.020) | -0.012 (0.016) | 3480 |
| CA|within EXPOSED|occ+city FE | +0.234 (0.042)* | +0.059 (0.032) | +0.211 (0.031)* | 10981 |
| CA|within EXPOSED|occ+city+COMPANY FE | +0.137 (0.053)* | -0.006 (0.027) | +0.138 (0.038)* | 10981 |

Reading:
- **AI premium is not an AI_POSITIONED phenomenon.** Within AI_POSITIONED only ai_build pays (+0.078); ai_use (+0.014) and ai_brand (+0.008) are ~0, and with company FE ai_use is slightly negative (-0.016, se 0.009). Within EXPOSED all three are positive and larger (build +0.199, use +0.127, brand +0.214), also within clerical (ai_use +0.293, se 0.055) and PROF_EXPOSED (+0.088, se 0.044), but ~0 in CUSTOMER_SUPPORT (+0.049, se 0.062).
- **Is AI fluency a wage-sorting device for clerical/support?** Between firms, yes: exposed postings that ask for AI use sit at higher-paying employers (and tech-intensive firms; only 220 of 2,920 salaried exposed postings, 158 firms, mention AI use; 113 of those are at firms >=30% AI_POSITIONED). Within firm, no: ai_use +0.029 (se 0.037) and, for CA, -0.006 (0.027). The **negative-premium hypothesis (absorbing AI tools unpaid) is not supported**: the sign is positive between firms and zero within firm; the within-firm zero is compatible with "asked to use AI, not paid more for it" but cannot distinguish it from no effect. ai_build and ai_brand keep a within-firm exposed premium (+0.140 se 0.068; +0.088 se 0.043), and the exposed premium is larger at low-tech firms (<30% AI_POSITIONED): ai_use +0.117 (0.049).
- Robust to unseeded-only and annual-posted-only samples; the all-Bay ai_use coefficient falls to +0.039 (p=0.10) on annual-posted-only.
- Fragile: exposed ai_use rests on 220 postings; within-firm estimates identified only from multi-posting firms.

## TEST 3: The entry rung (Bay, unseeded sample for shares)

"Entry-level" = junior flag. years known = share of postings with a parsed years-of-experience figure (low for frontline, so yrs stats there are selected). Caveat: yrs_min picks up any "N years" mention, so junior-flagged roles with yrs_min>=2 may reflect other sentences.

| cls | n | entry_share | ba_share | nodeg_share | yrs_known | yrs_med | yrs_mean | yrs_ge3 | share_of_all_postings | share_of_all_entry |
|---|---|---|---|---|---|---|---|---|---|---|
| AI_DATA_WORK | 113 | 0.062 | 0.805 | 0.345 | 0.442 | 3.000 | 2.680 | 0.660 | 0.003 | 0.002 |
| AI_POSITIONED | 6896 | 0.042 | 0.488 | 0.328 | 0.572 | 5.000 | 5.012 | 0.782 | 0.188 | 0.065 |
| EDUCATION | 714 | 0.104 | 0.361 | 0.254 | 0.189 | 2.000 | 3.148 | 0.274 | 0.020 | 0.017 |
| EXPOSED | 3055 | 0.239 | 0.304 | 0.326 | 0.382 | 3.000 | 3.724 | 0.598 | 0.083 | 0.163 |
| FRONTLINE_SERVICE | 4953 | 0.184 | 0.067 | 0.209 | 0.147 | 2.000 | 2.890 | 0.291 | 0.135 | 0.204 |
| HEALTH_CLINICAL | 2471 | 0.193 | 0.135 | 0.210 | 0.216 | 2.000 | 2.529 | 0.235 | 0.068 | 0.107 |
| LEGAL_PROF | 279 | 0.308 | 0.082 | 0.100 | 0.616 | 5.000 | 5.140 | 0.733 | 0.008 | 0.019 |
| MANAGEMENT | 5220 | 0.086 | 0.487 | 0.278 | 0.605 | 5.000 | 6.315 | 0.815 | 0.143 | 0.100 |
| OTHER | 7285 | 0.156 | 0.369 | 0.313 | 0.412 | 3.000 | 4.186 | 0.639 | 0.199 | 0.255 |
| OTHER_ENGINEERING | 1070 | 0.051 | 0.652 | 0.285 | 0.623 | 5.000 | 5.409 | 0.822 | 0.029 | 0.012 |
| PRODUCT_DESIGN | 1285 | 0.033 | 0.507 | 0.288 | 0.660 | 5.000 | 5.774 | 0.889 | 0.035 | 0.010 |
| SALES_BIZ | 1520 | 0.047 | 0.406 | 0.239 | 0.527 | 5.000 | 4.792 | 0.714 | 0.042 | 0.016 |
| SKILLED_TRADE | 1726 | 0.081 | 0.101 | 0.374 | 0.396 | 3.000 | 3.877 | 0.575 | 0.047 | 0.031 |

Within entry-level postings, and AI vs no-AI entry roles:

| cls | n_junior | jr_yrs_known | jr_yrs_mean | jr_yrs_med | jr_yrs_ge2 | jr_ba | jr_ai_strict_share | n_jr_ai | jr_ai_yrs_mean | jr_noai_yrs_mean | jr_ai_ba | jr_noai_ba |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AI_DATA_WORK | 7 | 0.286 | 2.000 | 2.000 | 1.000 | 0.714 | 0.000 | 0 |  | 2.000 |  | 0.714 |
| AI_POSITIONED | 291 | 0.227 | 4.364 | 4.000 | 0.818 | 0.395 | 0.581 | 169 | 4.902 | 3.480 | 0.373 | 0.426 |
| EDUCATION | 74 | 0.149 | 2.091 | 1.000 | 0.455 | 0.216 | 0.054 | 4 | 2.000 | 2.100 | 0.750 | 0.186 |
| EXPOSED | 730 | 0.370 | 3.341 | 3.000 | 0.733 | 0.305 | 0.062 | 45 | 4.040 | 3.269 | 0.422 | 0.298 |
| FRONTLINE_SERVICE | 911 | 0.121 | 2.173 | 1.000 | 0.336 | 0.058 | 0.052 | 47 | 4.333 | 2.112 | 0.021 | 0.060 |
| HEALTH_CLINICAL | 477 | 0.187 | 2.820 | 1.000 | 0.483 | 0.057 | 0.008 | 4 | 0.000 | 2.852 | 0.250 | 0.055 |
| LEGAL_PROF | 86 | 0.593 | 4.314 | 3.000 | 0.863 | 0.047 | 0.035 | 3 | 8.000 | 4.083 | 0.000 | 0.048 |
| MANAGEMENT | 448 | 0.509 | 4.373 | 4.000 | 0.794 | 0.446 | 0.060 | 27 | 5.833 | 4.248 | 0.741 | 0.428 |
| OTHER | 1138 | 0.311 | 2.927 | 2.000 | 0.672 | 0.335 | 0.100 | 114 | 2.761 | 2.951 | 0.553 | 0.311 |
| OTHER_ENGINEERING | 55 | 0.291 | 2.562 | 2.000 | 0.688 | 0.436 | 0.073 | 4 | 2.500 | 2.571 | 0.750 | 0.412 |
| PRODUCT_DESIGN | 43 | 0.465 | 3.850 | 2.500 | 0.650 | 0.674 | 0.209 | 9 | 3.000 | 4.062 | 0.889 | 0.618 |
| SALES_BIZ | 71 | 0.310 | 2.682 | 3.000 | 0.955 | 0.352 | 0.070 | 5 | 2.500 | 2.700 | 0.600 | 0.333 |
| SKILLED_TRADE | 140 | 0.207 | 2.931 | 2.000 | 0.517 | 0.114 | 0.029 | 4 | 6.000 | 2.821 | 0.000 | 0.118 |

By detailed class:

| cls | n | entry_share | ba_share | nodeg_share | yrs_med | n_junior | jr_yrs_mean | jr_ba |
|---|---|---|---|---|---|---|---|---|
| AI_DATA_WORK | 113 | 0.062 | 0.805 | 0.345 | 3.000 | 7 | 2.000 | 0.714 |
| AI_PRODUCER | 3105 | 0.051 | 0.423 | 0.327 | 5.000 | 158 | 4.833 | 0.348 |
| CLERICAL_ADMIN | 1179 | 0.363 | 0.182 | 0.358 | 3.000 | 428 | 3.834 | 0.259 |
| CUSTOMER_SUPPORT | 830 | 0.193 | 0.189 | 0.410 | 2.000 | 160 | 1.839 | 0.125 |
| DATA_ENG_ANALYTICS | 376 | 0.053 | 0.559 | 0.354 | 5.000 | 20 | 3.000 | 0.700 |
| EDUCATION | 714 | 0.104 | 0.361 | 0.254 | 2.000 | 74 | 2.091 | 0.216 |
| FRONTLINE_SERVICE | 4953 | 0.184 | 0.067 | 0.209 | 2.000 | 911 | 2.173 | 0.058 |
| HEALTH_CLINICAL | 2471 | 0.193 | 0.135 | 0.210 | 2.000 | 477 | 2.820 | 0.057 |
| LEGAL_PROF | 279 | 0.308 | 0.082 | 0.100 | 5.000 | 86 | 4.314 | 0.047 |
| MANAGEMENT | 5220 | 0.086 | 0.487 | 0.278 | 5.000 | 448 | 4.373 | 0.446 |
| OTHER | 7285 | 0.156 | 0.369 | 0.313 | 3.000 | 1138 | 2.927 | 0.335 |
| OTHER_ENGINEERING | 1070 | 0.051 | 0.652 | 0.285 | 5.000 | 55 | 2.562 | 0.436 |
| PRODUCT_DESIGN | 1285 | 0.033 | 0.507 | 0.288 | 5.000 | 43 | 3.850 | 0.674 |
| PROF_EXPOSED | 1046 | 0.136 | 0.534 | 0.223 | 4.000 | 142 | 2.719 | 0.648 |
| SALES_BIZ | 1520 | 0.047 | 0.406 | 0.239 | 5.000 | 71 | 2.682 | 0.352 |
| SKILLED_TRADE | 1726 | 0.081 | 0.101 | 0.374 | 3.000 | 140 | 2.931 | 0.114 |
| SOFTWARE_ENG | 3415 | 0.033 | 0.540 | 0.325 | 5.000 | 113 | 3.765 | 0.407 |

Findings.
- **Bottom rung of exposed occupations is not thinner: it is thicker.** Entry-level share: EXPOSED 23.9% (CLERICAL 36.3%, CUSTOMER_SUPPORT 19.3%, PROF_EXPOSED 13.6%) vs FRONTLINE 18.4%, HEALTH 19.3%, SKILLED_TRADE 8.1%, AI_POSITIONED 4.2%. EXPOSED holds 16.3% of all entry postings but 8.3% of all postings. This is a stock of posted roles, not a change over time; it cannot show hollowing-out.
- **Experience floor** among entry-flagged roles: EXPOSED mean 3.3 yrs (73% >=2 yrs; BA required in 30.5%) vs FRONTLINE 2.2 (34%; 5.8%) vs AI_POSITIONED 4.4 (82%; 39.5%). The exposed entry floor is above frontline and below AI_POSITIONED; PROF_EXPOSED entry roles require BA in 65%.
- **AI-mentioning entry roles have a higher floor**: Bay (unseeded) junior roles: mean yrs_min 4.09 (AI, n=435) vs 3.23 (no AI); BA 42.3% vs 23.1%. In EXPOSED junior roles: AI 4.04 vs 3.27 (n_ai=45; all-Bay regression among exposed junior roles with years known, ai_use +1.11 yrs, se 0.48, n=305; all classes +0.40, se 0.28, n.s.). Small n in exposed; suggestive only. Only 6.2% of exposed entry roles mention AI vs 58.1% in AI_POSITIONED entry roles.

## TEST 4: AI_DATA_WORK (the "new contract underclass")

**This class is one platform.** Bay n=145 postings, 125 (86%) from DataAnnotation; statewide 447 postings, 419 (94%) DataAnnotation. It is not a market segment, and no market-wide median should be quoted.

| group | n | n_companies | top_company_share | n_hourly | share_hourly_posted | med_hourly_rate | med_annualized_2080 | n_annual_posted | med_annual_posted | contract | parttime | fulltime | remote | deg_ba | deg_grad | no_deg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AI_DATA_WORK_Bay | 145 | 19 | 0.862 | 134 | 0.937 | 75.0 | 156,000 | 9 | 182,000 | 0.876 | 0.862 | 0.959 | 0.745 | 0.807 | 0.455 | 0.324 |
| AI_DATA_WORK_CA | 447 | 27 | 0.937 | 434 | 0.975 | 75.0 | 156,000 | 11 | 175,000 | 0.942 | 0.937 | 0.971 | 0.796 | 0.841 | 0.441 | 0.273 |
| AI_DATA_WORK_Bay_DataAnnotation | 125 | 1 | 1.000 | 125 | 1.000 | 75.0 | 156,000 | 0 |  | 1.000 | 1.000 | 1.000 | 0.848 | 0.904 | 0.512 | 0.360 |
| AI_DATA_WORK_Bay_nonDA | 20 | 18 | 0.100 | 9 | 0.500 | 30.0 | 117,300 | 9 | 182,000 | 0.100 | 0.000 | 0.700 | 0.100 | 0.200 | 0.100 | 0.100 |
| AI_PRODUCER_Bay | 4158 | 1054 | 0.050 | 127 | 0.036 | 60.0 | 214,500 | 3339 | 215,950 | 0.013 | 0.006 | 0.692 | 0.045 | 0.432 | 0.494 | 0.338 |
| AI_PRODUCER_CA | 5263 | 1441 | 0.043 | 196 | 0.044 | 52.5 | 205,000 | 4239 | 209,750 | 0.015 | 0.007 | 0.691 | 0.053 | 0.467 | 0.485 | 0.337 |
| FRONTLINE_Bay | 5429 | 2146 | 0.038 | 4314 | 0.908 | 21.0 | 44,720 | 383 | 105,000 | 0.012 | 0.428 | 0.492 | 0.002 | 0.069 | 0.039 | 0.218 |
| FRONTLINE_CA | 23390 | 6917 | 0.044 | 18464 | 0.919 | 20.1 | 42,640 | 1226 | 86,500 | 0.011 | 0.428 | 0.443 | 0.001 | 0.070 | 0.029 | 0.225 |

- **Pay in hourly terms only.** DataAnnotation posts $50-$100 an hour (91 of 125 Bay postings carry the identical range, so the "median $75/hr" is the midpoint of a posted range, not an observed rate). 100% of DataAnnotation Bay postings are contract and part-time, 85% remote. The annualized figure ($156,000 = $75 x 2080) is **invalid**: hours are not guaranteed. Annual earnings are indeterminate. (Pure arithmetic, not an estimate: at 1,040 hours it would be $78,000.) The Bay non-DataAnnotation hourly postings (n=9) have median $30/hr.
- **Contrast.** The CA postings that quoted an annual figure for this class include a contract "AI Training Specialist (Data Annotation)" at $20,800-$41,600 (Remote Talent Cloud, non-Bay), alongside salaried human-data jobs at OpenAI/Anthropic/Apple ($145k-$385k): the class label mixes gig and elite roles.
- **vs AI_PRODUCER and FRONTLINE**: AI_PRODUCER posts annual salary (96% annual-posted, median $215,950; its 127 hourly-posted median $60/hr). FRONTLINE median $21/hr, 48% part-time. Posted rate is in tech-contractor territory; the contract/part-time/no-guaranteed-hours structure is gig work. It is paid like neither on terms we can verify.
- **Geography.** Bay AI_DATA_WORK by county: Santa Clara 43, San Francisco 29, Alameda 28, Contra Costa 25, San Mateo 13, Napa 4, Sonoma 2, Solano 1; cities are spread across many small places ("Remote in Richmond/Pleasanton/San Ramon"). 74.5% of Bay postings are remote; the posting location is nominal for a remote platform, so the Bay may be capturing little of this employment.
- **Titling pattern: whose occupations are being recruited to train AI?** DataAnnotation titles take the form "<former occupation> - AI Trainer". Of 417 CA such titles (125 Bay), prefix mapped through the occupation taxonomy (+ hand-assigned buckets for 124 unmatched prefixes):

| sample | key | n | level |
|---|---|---|---|
| CA | SOFTWARE_ENG | 84 | bucket |
| CA | AI_PRODUCER | 67 | bucket |
| CA | TECH_like | 32 | bucket |
| CA | PROF_EXPOSED | 31 | bucket |
| CA | OTHER_ENGINEERING | 31 | bucket |
| CA | CLERICAL_ADMIN | 28 | bucket |
| CA | QUANT_stat | 23 | bucket |
| CA | UNMAPPED | 23 | bucket |
| CA | EXPOSED_like_analyst | 21 | bucket |
| CA | SCIENCE_research | 18 | bucket |
| CA | EDUCATION | 14 | bucket |
| CA | PRODUCT_DESIGN | 11 | bucket |
| CA | DATA_ENG_ANALYTICS | 8 | bucket |
| CA | MANAGEMENT | 7 | bucket |
| CA | FINANCE_SALES | 7 | bucket |
| CA | CUSTOMER_SUPPORT | 5 | bucket |
| CA | HEALTH_CLINICAL | 5 | bucket |
| CA | AI_DATA_WORK | 1 | bucket |
| CA | SALES_BIZ | 1 | bucket |
| CA | AI_POSITIONED(+tech-like) | 191 | top |
| CA | OTHER (engineering, science, education, finance/sales, mgmt, design) | 118 | top |
| CA | EXPOSED(clerical/support/prof/legal + analyst-like) | 85 | top |
| CA | QUANT_stat (technical-quant, ambiguous) | 23 | top |
| Bay | SOFTWARE_ENG | 25 | bucket |
| Bay | AI_PRODUCER | 22 | bucket |
| Bay | EXPOSED_like_analyst | 11 | bucket |
| Bay | TECH_like | 11 | bucket |
| Bay | CLERICAL_ADMIN | 9 | bucket |
| Bay | OTHER_ENGINEERING | 9 | bucket |
| Bay | QUANT_stat | 8 | bucket |
| Bay | PROF_EXPOSED | 6 | bucket |
| Bay | EDUCATION | 5 | bucket |
| Bay | SCIENCE_research | 5 | bucket |
| Bay | UNMAPPED | 4 | bucket |
| Bay | PRODUCT_DESIGN | 3 | bucket |
| Bay | MANAGEMENT | 2 | bucket |
| Bay | HEALTH_CLINICAL | 2 | bucket |
| Bay | DATA_ENG_ANALYTICS | 2 | bucket |
| Bay | SALES_BIZ | 1 | bucket |
| Bay | AI_POSITIONED(+tech-like) | 60 | top |
| Bay | OTHER (engineering, science, education, finance/sales, mgmt, design) | 31 | top |
| Bay | EXPOSED(clerical/support/prof/legal + analyst-like) | 26 | top |
| Bay | QUANT_stat (technical-quant, ambiguous) | 8 | top |

  In California: EXPOSED-type former occupations (clerical, support, PROF_EXPOSED incl. accountants/bookkeepers/proofreaders/copywriters, + analyst-like roles) = **85 of 417 (20%)**; taxonomy-only EXPOSED = 64 (15%). AI_POSITIONED-type (software, ML, data) = **191 (46%)**, taxonomy-only 159 (38%). Quantitative/statistical (23, 6%), other engineering, science, teaching etc. the rest. Bay: 26 of 125 exposed-type (21%), 60 AI_POSITIONED-type (48%). **The solicited occupations skew technical, not exposed.** The claim "exposed professionals are being recruited to train their own replacements" is supported for a fifth of titles (accountants, bookkeepers, AR/AP, proofreaders, copywriters, bank clerks) but not as the dominant pattern.

## TEST 5: Pay transparency

Omission = no usable posted salary in the structured field (so includes parse failures; a different definition from "violates SB 1162"). Range width = sal_hi/sal_lo among salaried. Size proxy = Indeed `company_reviews` count (crude; "no reviews listed" is 25% of postings and mixes small firms with missing profiles). Employer minimum: 30 postings (30 salaried for width).

By class group (Bay):

| key | n | omit_rate | n_sal | width_med | width_p90 | share_width_ge2 | share_width_eq1 |
|---|---|---|---|---|---|---|---|
| AI_DATA_WORK | 145 | 0.014 | 143 | 2.000 | 2.000 | 0.720 | 0.189 |
| AI_POSITIONED | 9754 | 0.165 | 8146 | 1.454 | 2.024 | 0.127 | 0.022 |
| EDUCATION | 781 | 0.106 | 698 | 1.214 | 1.763 | 0.042 | 0.175 |
| EXPOSED | 3592 | 0.187 | 2920 | 1.214 | 1.618 | 0.044 | 0.133 |
| FRONTLINE_SERVICE | 5429 | 0.125 | 4753 | 1.080 | 1.400 | 0.020 | 0.328 |
| HEALTH_CLINICAL | 3301 | 0.111 | 2935 | 1.167 | 1.449 | 0.025 | 0.147 |
| LEGAL_PROF | 302 | 0.136 | 261 | 1.368 | 1.849 | 0.038 | 0.054 |
| MANAGEMENT | 6578 | 0.140 | 5655 | 1.294 | 1.857 | 0.058 | 0.058 |
| OTHER | 8818 | 0.180 | 7230 | 1.252 | 1.857 | 0.064 | 0.154 |
| OTHER_ENGINEERING | 1378 | 0.186 | 1122 | 1.429 | 1.991 | 0.099 | 0.024 |
| PRODUCT_DESIGN | 1633 | 0.148 | 1391 | 1.434 | 1.870 | 0.044 | 0.037 |
| SALES_BIZ | 1951 | 0.219 | 1523 | 1.333 | 2.000 | 0.104 | 0.113 |
| SKILLED_TRADE | 2188 | 0.124 | 1917 | 1.222 | 1.715 | 0.050 | 0.140 |

By detailed class:

| key | n | omit_rate | width_med | width_p90 |
|---|---|---|---|---|
| AI_DATA_WORK | 145 | 0.014 | 2.000 | 2.000 |
| AI_PRODUCER | 4158 | 0.163 | 1.488 | 2.131 |
| CLERICAL_ADMIN | 1304 | 0.231 | 1.167 | 1.511 |
| CUSTOMER_SUPPORT | 979 | 0.138 | 1.222 | 1.634 |
| DATA_ENG_ANALYTICS | 558 | 0.172 | 1.417 | 1.989 |
| EDUCATION | 781 | 0.106 | 1.214 | 1.763 |
| FRONTLINE_SERVICE | 5429 | 0.125 | 1.080 | 1.400 |
| HEALTH_CLINICAL | 3301 | 0.111 | 1.167 | 1.449 |
| LEGAL_PROF | 302 | 0.136 | 1.368 | 1.849 |
| MANAGEMENT | 6578 | 0.140 | 1.294 | 1.857 |
| OTHER | 8818 | 0.180 | 1.252 | 1.857 |
| OTHER_ENGINEERING | 1378 | 0.186 | 1.429 | 1.991 |
| PRODUCT_DESIGN | 1633 | 0.148 | 1.434 | 1.870 |
| PROF_EXPOSED | 1309 | 0.180 | 1.250 | 1.696 |
| SALES_BIZ | 1951 | 0.219 | 1.333 | 2.000 |
| SKILLED_TRADE | 2188 | 0.124 | 1.222 | 1.715 |
| SOFTWARE_ENG | 5038 | 0.166 | 1.449 | 2.000 |

By company-size proxy:

| key | n | omit_rate | width_med | share_width_ge2 |
|---|---|---|---|---|
| no_reviews_listed | 11549 | 0.285 | 1.250 | 0.059 |
| 1-19 | 7165 | 0.163 | 1.219 | 0.034 |
| 20-199 | 8350 | 0.109 | 1.217 | 0.031 |
| 200-1999 | 8971 | 0.110 | 1.378 | 0.085 |
| 2000+ | 9815 | 0.082 | 1.400 | 0.122 |

By county:

| key | n | omit_rate | width_med |
|---|---|---|---|
| Alameda | 6255 | 0.153 | 1.200 |
| Contra Costa | 2979 | 0.136 | 1.167 |
| Marin | 760 | 0.129 | 1.158 |
| Napa | 607 | 0.143 | 1.117 |
| San Francisco | 12458 | 0.191 | 1.325 |
| San Mateo | 4435 | 0.127 | 1.250 |
| Santa Clara | 15669 | 0.150 | 1.389 |
| Solano | 1063 | 0.135 | 1.140 |
| Sonoma | 1624 | 0.111 | 1.140 |

Highest omission, employers with >=30 Bay postings:

| name | n | omit_rate | n_sal | top_occ |
|---|---|---|---|---|
| Career Launch | 33 | 1.000 | 0 | AI_PRODUCER |
| Advanced Micro Devices, Inc | 199 | 0.995 | 1 | OTHER |
| Oracle | 35 | 0.971 | 1 | SOFTWARE_ENG |
| Costco Wholesale Corporation | 202 | 0.970 | 6 | FRONTLINE_SERVICE |
| Prohealth Home Care Inc | 33 | 0.939 | 2 | HEALTH_CLINICAL |
| deCircle | 32 | 0.938 | 2 | OTHER |
| Rivian | 32 | 0.906 | 3 | SOFTWARE_ENG |
| University of California San Francisco | 189 | 0.894 | 20 | OTHER |
| Horizontal Talent | 30 | 0.833 | 5 | OTHER |
| Etched | 35 | 0.429 | 20 | OTHER |
| Essel | 31 | 0.387 | 19 | SKILLED_TRADE |
| Everforth | 34 | 0.382 | 21 | MANAGEMENT |

Widest posted ranges, employers with >=30 salaried Bay postings:

| name | n | n_sal | omit_rate | width_med | width_p90 | share_width_ge2 | top_occ |
|---|---|---|---|---|---|---|---|
| Accenture | 283 | 267 | 0.057 | 3.204 | 3.482 | 0.891 | MANAGEMENT |
| UC San Francisco Academic | 52 | 50 | 0.038 | 2.624 | 3.351 | 0.560 | OTHER |
| Wipro Limited | 33 | 33 | 0.000 | 2.475 | 2.689 | 0.758 | OTHER |
| PRICE WATERHOUSE COOPERS | 73 | 73 | 0.000 | 2.343 | 3.320 | 1.000 | MANAGEMENT |
| Tesla | 449 | 449 | 0.000 | 2.143 | 2.926 | 0.621 | SOFTWARE_ENG |
| Microsoft | 43 | 42 | 0.023 | 2.136 | 2.319 | 0.833 | SOFTWARE_ENG |
| ByteDance | 137 | 137 | 0.000 | 2.115 | 2.485 | 0.657 | AI_PRODUCER |
| TikTok USDS JV | 44 | 43 | 0.023 | 2.115 | 2.630 | 0.605 | AI_PRODUCER |
| Hewlett Packard Enterprise | 60 | 59 | 0.017 | 2.026 | 2.029 | 0.966 | SOFTWARE_ENG |
| Walmart | 160 | 153 | 0.044 | 2.000 | 2.167 | 0.523 | FRONTLINE_SERVICE |
| Abbott Laboratories | 82 | 81 | 0.012 | 2.000 | 2.001 | 0.679 | MANAGEMENT |
| GEICO | 66 | 66 | 0.000 | 2.000 | 2.432 | 0.712 | SOFTWARE_ENG |

Findings.
- **Overall Bay omission is 15.6%** (unseeded 16.9%). **Negative result:** EXPOSED omit at 18.7% vs AI_POSITIONED 16.5%, FRONTLINE 12.5%, SALES_BIZ 21.9%; in a cluster-robust linear probability model (class, county, size, seeded, remote, contract, part-time) the EXPOSED coefficient vs OTHER is -0.008 (se 0.018), i.e. no excess opacity for exposed work. (CLERICAL_ADMIN alone is 23.1%, the highest of the exposed classes.) Saved in `jobs_transparency_lpm.csv`.
- **Opacity falls on small/unprofiled employers, not on a class:** 28.5% omission with no reviews listed vs 8.2% at firms with 2,000+ reviews. A few large employers omit almost everything: AMD 99.5% of 199 postings, Costco 97% of 202, UCSF 89% of 189, Oracle 97% of 35.
- **Wide ranges are a tech/consulting/gig pattern.** Median width 1.45 for AI_POSITIONED sub-classes vs 1.08 for FRONTLINE; 12.7% of AI_POSITIONED postings have hi/lo >= 2 vs 2.0% FRONTLINE. Accenture (median 3.2x, 89% of 267 postings >= 2x), PwC (2.3x, 100% >=2x), Wipro, Tesla (2.1x, 449 postings), ByteDance/TikTok, HPE. DataAnnotation posts 2.0x on everything. Formal compliance with limited information: a 2-3x range cannot be a pay decision.

## TEST 6: AI as gatekeeper (ai_hiring)

**The flag as built is noisy; corrected rates are lower.** I extracted the regex match context for all 1,977 ai_hiring postings in the file (1,570 Bay) from the source text. A random hand-read of 40 Bay matches found 32 genuine employer disclosures (80%); the 8 false positives were candidate-side rules ("the use of AI or recording tools during live interviews is not permitted", Adobe 391 postings; Sofar). A full template audit of all 120 employers' boilerplate (grouping matches by company, then hand-classifying each template; script `jobs_t6b.py`, `jobs_t6c.py`) gives **posting-weighted precision 65% overall (1,291 of 1,977) and 64% in the Bay (1,008 of 1,570)**. The 40-posting hand sample (80%, wide CI around +/-13 pts) is higher because NVIDIA's genuine boilerplate is 35% of all matches. False positives: DICK'S, Marvell, Air Apps, CBRE, Foot Locker, Savers, Micron, Everlaw, Pfizer, Carter's ("does not use AI"), etc. All of these are interview/application conduct rules. Residual error remains in the "corrected" flag (regex-based plus hand-resolved edge cases), and **recall is unknown** (the regex is narrow; many disclosures phrased differently are missed, so rates are floors).

Corrected disclosure (Bay): rate = share of postings with a genuine employer AI-in-hiring disclosure.

| key | n | orig_rate | corrected_rate | n_corrected | n_employers | top_emp_share | corrected_rate_ex_nvidia | med_pay_hiringAI | med_pay_other | senior_hiringAI | senior_other | junior_hiringAI | junior_other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AI_POSITIONED | 9754 | 0.064 | 0.047 | 454 | 21 | 0.753 | 0.012 | 248,125 | 208,000 | 0.747 | 0.564 | 0.013 | 0.045 |
| EXPOSED | 3592 | 0.016 | 0.006 | 22 | 10 | 0.545 | 0.003 | 161,250 | 72,500 | 0.773 | 0.225 | 0.045 | 0.230 |
| FRONTLINE_SERVICE | 5429 | 0.009 | 0.007 | 39 | 11 | 0.385 | 0.006 | 48,880 | 44,720 | 0.128 | 0.074 | 0.026 | 0.178 |
| HEALTH_CLINICAL | 3301 | 0.000 | 0.000 | 1 | 1 | 1.000 | 0.000 | 158,818 | 97,500 | 0.000 | 0.131 | 0.000 | 0.199 |
| MANAGEMENT | 6578 | 0.049 | 0.026 | 169 | 19 | 0.669 | 0.009 | 227,900 | 162,450 | 0.953 | 0.895 | 0.030 | 0.084 |
| OTHER | 8818 | 0.032 | 0.020 | 175 | 22 | 0.714 | 0.006 | 198,812 | 100,000 | 0.474 | 0.199 | 0.034 | 0.147 |
| CLERICAL_ADMIN | 1304 | 0.007 | 0.001 | 1 | 1 | 1.000 | 0.001 | 104,600 | 57,200 | 0.000 | 0.114 | 1.000 | 0.368 |
| CUSTOMER_SUPPORT | 979 | 0.011 | 0.007 | 7 | 4 | 0.571 | 0.003 | 139,000 | 61,277 | 1.000 | 0.242 | 0.000 | 0.175 |
| FRONTLINE_SERVICE | 5429 | 0.009 | 0.007 | 39 | 11 | 0.385 | 0.006 | 48,880 | 44,720 | 0.128 | 0.074 | 0.026 | 0.178 |
| HEALTH_CLINICAL | 3301 | 0.000 | 0.000 | 1 | 1 | 1.000 | 0.000 | 158,818 | 97,500 | 0.000 | 0.131 | 0.000 | 0.199 |
| MANAGEMENT | 6578 | 0.049 | 0.026 | 169 | 19 | 0.669 | 0.009 | 227,900 | 162,450 | 0.953 | 0.895 | 0.030 | 0.084 |
| OTHER | 8818 | 0.032 | 0.020 | 175 | 22 | 0.714 | 0.006 | 198,812 | 100,000 | 0.474 | 0.199 | 0.034 | 0.147 |
| PROF_EXPOSED | 1309 | 0.028 | 0.011 | 14 | 7 | 0.571 | 0.005 | 193,588 | 97,500 | 0.714 | 0.324 | 0.000 | 0.131 |
| ALL | 45850 | 0.034 | 0.022 | 1008 | 51 | 0.676 | 0.007 | 219,750 | 122,500 | 0.707 | 0.387 | 0.024 | 0.117 |

Top Bay employers (corrected flag):

| company | n | med_pay | top_occ | exposed_share | junior |
|---|---|---|---|---|---|
| NVIDIA | 681 | 239,250 | AI_POSITIONED | 0.018 | 0.019 |
| eBay Inc. | 53 | 209,746 | AI_POSITIONED | 0.038 | 0.019 |
| Block, Inc. | 38 | 237,600 | AI_POSITIONED | 0.026 | 0.000 |
| Everforth | 34 | 165,000 | AI_POSITIONED | 0.000 | 0.029 |
| Braze | 22 | 152,875 | SALES_BIZ | 0.000 | 0.000 |
| Pinterest | 16 | 218,332 | AI_POSITIONED | 0.000 | 0.000 |
| Epicurean Group | 15 | 47,840 | FRONTLINE_SERVICE | 0.000 | 0.000 |
| Sigma Computing | 12 | 156,250 | AI_POSITIONED | 0.083 | 0.000 |
| Kelly Services | 12 | 94,120 | OTHER | 0.000 | 0.083 |
| Everforth, Cybercoders | 11 | 140,000 | MANAGEMENT | 0.000 | 0.000 |
| Beacon Software | 9 |  | MANAGEMENT | 0.000 | 0.000 |
| Abby Care | 8 | 190,000 | AI_POSITIONED | 0.000 | 0.125 |
| Windfall | 7 | 165,000 | AI_POSITIONED | 0.143 | 0.000 |
| Levy Sector | 7 | 50,877 | FRONTLINE_SERVICE | 0.000 | 0.143 |
| Bozzuto | 7 | 56,055 | SKILLED_TRADE | 0.000 | 0.286 |

Findings.
- Corrected Bay rate **2.2%** (orig. 3.4%). **Hypothesis not supported by these data:** disclosure is concentrated in AI_POSITIONED (4.7%) and management (2.6%); EXPOSED 0.6%, FRONTLINE 0.7%, CLERICAL 0.1%. Only 51 employers (Bay) account for all disclosures, and **NVIDIA alone is 68% of Bay corrected matches** (rate excluding NVIDIA 0.7% overall). These are rates of *disclosure*, which depends on state disclosure norms and big-company legal boilerplate, not on how many applicants are actually screened by algorithm. High-volume applicant pools may be screened without disclosure.
- Disclosing postings are senior and high-paid: median posted pay $219,750 vs $122,500 for other postings; senior 71% vs 39%; entry-level 2.4% vs 11.7%. That mostly reflects who discloses (NVIDIA, eBay, Block, Pinterest), not who is screened. Compass Group affiliates (Epicurean Group 15, Levy 7, FISD 6 Bay postings) disclose an AI recruiting assistant, which is most of the frontline disclosures.

## TEST 7: Firm-level recomposition (postings x WARN)

Join: exact match on company_norm; WARN file = warn_ca.csv (5,392 notices 2023-04 to 2026-11; 2,741 firms; 1,760 notices in the 9 Bay counties by notice county, 922 firms).

| match definition | % Bay postings matched | Bay posting firms matched | WARN firms with any Bay posting | WARN employees covered |
|---|---|---|---|---|
| any CA WARN | **14.1%** (6,484 / 45,850) | 226 of 11,869 | 226 / 2,741 = 8.2% | 19.8% |
| Bay-county WARN | **12.5%** (5,745) | 170 | 170 / 922 = 18.4% | 37.7% |
| Bay-county WARN since 2025-01 | 5.3% (2,450) | 97 | 97 / 600 = 16.2% | 29.5% |

**Limits (honest).** (a) company_norm is a fuzzy exact key: a parent's WARN may not correspond to the posting entity (Walmart: 16 WARN notices, 37.5% closures, while its 160 Bay postings are 43% AI_POSITIONED, so the notices and the postings plausibly concern different parts of the company; Optum: 3 Bay layoff employees vs 11 Bay postings); subsidiaries match only if the name coincides (LinkedIn has 15 notices but 1 posting under that name). (b) Matching is mostly large employers: only 226 of 11,869 firms and only 18% of Bay-county WARN filers have a posting at all; 108 matched firms have >=5 postings. (c) Postings are 2026; WARN spans 2023-2026, so the layoff and the posting are not simultaneous. (d) Postings are not hires, and WARN employees are counts at a site, not occupations cut. (e) The crawl was seeded toward tech, which inflates AI_POSITIONED in both groups. The matched subset supports a descriptive mix comparison, not a "cutting X while hiring Y" claim for any individual firm.

Mix of postings at matched vs non-matched firms (Bay, unseeded sample; difference in share of postings, WARN minus non-WARN; 95% CI from a firm-cluster bootstrap):

| flag | sample | class_ | diff | lo | hi | n_firms | n_warn_firms |
|---|---|---|---|---|---|---|---|
| warn_baycounty | all | POS | 0.185 | 0.091 | 0.267 | 11869 | 170 |
| warn_baycounty | all | EXP | -0.037 | -0.051 | -0.017 | 11869 | 170 |
| warn_baycounty | all | FL | -0.072 | -0.103 | -0.018 | 11869 | 170 |
| warn_baycounty | unseeded | POS | 0.140 | 0.043 | 0.207 | 10102 | 165 |
| warn_baycounty | unseeded | EXP | -0.035 | -0.052 | -0.011 | 10102 | 165 |
| warn_baycounty | unseeded | FL | -0.079 | -0.120 | -0.011 | 10102 | 165 |
| warn_bay | all | POS | 0.189 | 0.090 | 0.262 | 11869 | 226 |
| warn_bay | all | EXP | -0.039 | -0.052 | -0.022 | 11869 | 226 |
| warn_bay | all | FL | -0.059 | -0.094 | 0.002 | 11869 | 226 |
| warn_bay | unseeded | POS | 0.152 | 0.043 | 0.221 | 10102 | 215 |
| warn_bay | unseeded | EXP | -0.038 | -0.054 | -0.016 | 10102 | 215 |
| warn_bay | unseeded | FL | -0.063 | -0.110 | 0.005 | 10102 | 215 |

- **WARN-filing firms post more AI_POSITIONED roles**: Bay-county WARN firms 31.1% vs 17.1% of unseeded postings (+14.0 pts, CI +4.3 to +20.7); full sample +18.5 pts (CI +9.1 to +26.7). They post fewer EXPOSED (-3.5 pts, CI -5.2 to -1.1) and fewer FRONTLINE (-7.9, CI -12.0 to -1.1) roles. Using any-CA-WARN: +15.2 pts (CI +4.3 to +22.1).
- **But WARN filers are large firms, and large firms are tech-heavy.** Restricting to firms with >=30 Bay postings, WARN firms are 41.5% AI_POSITIONED vs 30.4% (posting-weighted; 13 vs 26 firms with >=100 postings: 44.6% vs 33.0%). Gap shrinks to ~11 pts and rests on 35 matched firms. Dropping the five biggest matched posters (Apple, Google, Tesla, TikTok, Accenture): 27.2% vs 18.6%.
- Median posted pay (salaried): POS roles at WARN firms $214,000 vs $205,000 elsewhere; EXPOSED roles $114,250 vs $70,304 (small n; mostly big-tech support roles).
- **Verdict:** descriptively consistent with recomposition (firms cutting staff are tilted to AI_POSITIONED hiring), but not evidence of within-firm substitution; the pattern may simply be that big tech both files notices and hires engineers. This supports "layoffs and AI-technical hiring coexist" at firms such as Tesla (449 postings, 48% AI_POSITIONED; 2,589 Bay layoff employees), Cisco (166; 45%; 2,668), Intuit (115; 44%; 927), eBay (61; 49%; 951), Salesforce (136; 46%; 677), Apple (866; 43%).

Top matched firms by WARN employees (any CA notice; Bay-county employees beside):

| company | warn_employees | warn_emp_bay | n_notices | n_postings | pos_share | exp_share | fl_share | top_occ | med_pay |
|---|---|---|---|---|---|---|---|---|---|
| Tesla | 3933 | 2589 | 34 | 449 | 0.479 | 0.022 | 0.004 | SOFTWARE_ENG | 175,000 |
| Cisco Systems | 2668 | 2668 | 14 | 166 | 0.446 | 0.030 | 0.006 | SOFTWARE_ENG | 214,600 |
| Intel | 2439 | 1179 | 34 | 56 | 0.107 | 0.036 | 0.000 | OTHER | 235,649 |
| Walmart | 1652 | 877 | 16 | 160 | 0.431 | 0.025 | 0.350 | FRONTLINE_SERVICE | 171,000 |
| Northrop Grumman | 1647 | 78 | 8 | 39 | 0.179 | 0.051 | 0.000 | OTHER_ENGINEERING | 131,400 |
| Qualcomm | 1534 | 194 | 9 | 110 | 0.409 | 0.009 | 0.091 | OTHER | 208,900 |
| Broadcom | 1514 | 1514 | 2 | 14 | 0.286 | 0.000 | 0.000 | OTHER | 158,450 |
| Intuit | 1509 | 927 | 6 | 115 | 0.443 | 0.043 | 0.009 | AI_PRODUCER | 238,250 |
| LinkedIn | 1446 | 1409 | 15 | 1 | 1.000 | 0.000 | 0.000 | AI_PRODUCER | 223,500 |
| Genentech | 1121 | 1121 | 7 | 168 | 0.137 | 0.012 | 0.018 | MANAGEMENT | 219,000 |
| eBay | 951 | 951 | 5 | 61 | 0.492 | 0.049 | 0.000 | SOFTWARE_ENG | 214,350 |
| KOHLS | 929 | 60 | 5 | 3 | 0.000 | 0.000 | 0.333 | OTHER | 47,008 |
| Workday | 913 | 913 | 3 | 20 | 0.400 | 0.000 | 0.000 | AI_PRODUCER | 205,700 |
| Cepheid | 896 | 843 | 28 | 3 | 0.000 | 0.000 | 0.000 | MANAGEMENT | 200,000 |
| Apple | 792 | 614 | 10 | 866 | 0.428 | 0.033 | 0.010 | OTHER | 214,000 |
| Nordstrom Inc | 784 | 0 | 1 | 8 | 0.000 | 0.250 | 0.500 | FRONTLINE_SERVICE | 49,270 |
| Safeway | 760 | 760 | 11 | 21 | 0.143 | 0.048 | 0.667 | FRONTLINE_SERVICE | 40,352 |
| Tower Semiconductor Ltd. | 699 | 0 | 1 | 1 | 0.000 | 0.000 | 0.000 | SALES_BIZ | 250,000 |
| Salesforce | 677 | 677 | 6 | 136 | 0.463 | 0.044 | 0.000 | SOFTWARE_ENG | 221,392 |
| Macy’s | 626 | 147 | 8 | 14 | 0.000 | 0.143 | 0.643 | FRONTLINE_SERVICE | 44,512 |
| Visa | 613 | 613 | 5 | 10 | 0.700 | 0.100 | 0.000 | SOFTWARE_ENG | 156,950 |
| Gilead Sciences | 604 | 512 | 11 | 207 | 0.053 | 0.082 | 0.005 | MANAGEMENT | 208,845 |
| PayPal | 562 | 562 | 2 | 64 | 0.594 | 0.000 | 0.000 | SOFTWARE_ENG | 208,283 |
| Netflix | 553 | 227 | 3 | 36 | 0.722 | 0.083 | 0.000 | SOFTWARE_ENG | 503,500 |
| Thermo Fisher Scientific | 540 | 176 | 11 | 25 | 0.040 | 0.120 | 0.080 | OTHER | 81,006 |

Glassdoor linkage: `base/glassdoor_company.csv` did **not exist** at the time of writing (checked repeatedly), so the WARN-vs-employee-subrating test was **not run**.

## TEST 8: Geography (Bay Area counties; sorted by AI_POSITIONED share of unseeded postings)

| rank_pos_share_unseeded | county | n | n_unseeded | pos_share_unseeded | pos_share_all | exp_share_unseeded | fl_share_unseeded | pos_to_exp_plus_fl_unseeded | med_pay_unseeded | med_pay | med_AI_POSITIONED | med_EXPOSED | med_FRONTLINE_SERVICE | n_sal_EXPOSED | n_sal_AI_POSITIONED | ai_strict_share | remote_share |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Santa Clara | 15669 | 12643 | 0.273 | 0.300 | 0.061 | 0.093 | 1.769 | 157,500 | 160,000 | 213,500 | 79,140 | 45,074 | 730 | 4089 | 0.270 | 0.029 |
| 2 | San Francisco | 12458 | 9325 | 0.249 | 0.281 | 0.081 | 0.063 | 1.725 | 160,000 | 165,000 | 210,800 | 93,600 | 52,000 | 723 | 2799 | 0.294 | 0.072 |
| 3 | San Mateo | 4435 | 3564 | 0.175 | 0.200 | 0.101 | 0.158 | 0.676 | 120,390 | 126,074 | 212,750 | 72,800 | 44,564 | 343 | 754 | 0.224 | 0.034 |
| 4 | Alameda | 6255 | 5114 | 0.078 | 0.085 | 0.103 | 0.178 | 0.277 | 78,000 | 82,500 | 170,000 | 68,557 | 44,720 | 513 | 405 | 0.070 | 0.031 |
| 5 | Contra Costa | 2979 | 2587 | 0.026 | 0.030 | 0.112 | 0.283 | 0.065 | 55,120 | 57,314 | 148,750 | 55,560 | 42,588 | 266 | 70 | 0.040 | 0.029 |
| 6 | Marin | 760 | 607 | 0.016 | 0.014 | 0.142 | 0.222 | 0.045 | 60,180 | 62,400 | 156,658 | 57,200 | 43,680 | 88 | 6 | 0.018 | 0.018 |
| 7 | Solano | 1063 | 885 | 0.015 | 0.013 | 0.077 | 0.285 | 0.041 | 57,428 | 58,240 | 143,127 | 54,080 | 42,744 | 65 | 10 | 0.009 | 0.005 |
| 8 | Sonoma | 1624 | 1346 | 0.009 | 0.010 | 0.108 | 0.296 | 0.022 | 52,000 | 55,120 | 135,200 | 52,000 | 42,858 | 148 | 11 | 0.018 | 0.006 |
| 9 | Napa | 607 | 516 | 0.004 | 0.007 | 0.095 | 0.386 | 0.008 | 49,920 | 52,000 | 155,619 | 49,400 | 43,680 | 44 | 2 | 0.036 | 0.010 |

Ranking (unseeded AI_POSITIONED share): 1 Santa Clara 27.3%, 2 San Francisco 24.9%, 3 San Mateo 17.5%, 4 Alameda 7.8%, 5 Contra Costa 2.6%, 6 Marin 1.6%, 7 Solano 1.5%, 8 Sonoma 0.9%, 9 Napa 0.4%. Santa Clara, SF and San Mateo are AI-positioned (ratio of AI_POSITIONED to EXPOSED+FRONTLINE 1.77, 1.73, 0.68); every other county is dominated by frontline and exposed demand (Napa: FRONTLINE 38.6%, AI_POSITIONED 0.4%; Sonoma 29.6% frontline; Solano 28.5%; Contra Costa 28.3%). Median posted pay follows: $157,500 (Santa Clara) and $160,000 (SF) vs $49,920 (Napa). EXPOSED median posted pay is $93,600 in San Francisco, $79,140 Santa Clara, $72,800 San Mateo, $68,557 Alameda vs $49,400-57,200 in Napa, Sonoma, Solano, Contra Costa and Marin: even the pay of exposed work is geographic. Small cells: AI_POSITIONED salaried postings are 2-11 in Napa, Sonoma, Solano and Marin, so those pay figures are not reliable; shares are. Full per-class medians in `base/jobs_county_class_pay.csv` and class-mix columns in `jobs_county_table.csv`.

## Time (uncensored rows only; labelled ~May-Aug 2026; DO NOT READ AS A TREND)

Bay rows with censored==False and post_date in Feb-Sep 2026 (n=17,382; 98% fall in May-Aug; Feb/Apr/Sep cells have 11-234 postings). Uncensored postings are a biased subsample of fast-filling/fresh roles, and the "month" of a posting is nearly collinear with the crawl batch.

| index | m | n | ai_any | ai_strict | ai_use | ai_build | pos_share | exp_share | fl_share | med_sal |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-02 | 11 | 0.182 | 0.091 | 0.091 | 0.091 | 0.091 | 0.455 | 0.091 | 59,725 |
| 1 | 2026-04 | 14 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 175,000 |
| 2 | 2026-05 | 861 | 0.386 | 0.218 | 0.150 | 0.116 | 0.206 | 0.046 | 0.099 | 126,880 |
| 3 | 2026-06 | 4091 | 0.422 | 0.244 | 0.163 | 0.128 | 0.249 | 0.068 | 0.083 | 141,500 |
| 4 | 2026-07 | 8045 | 0.381 | 0.235 | 0.149 | 0.121 | 0.254 | 0.074 | 0.082 | 127,500 |
| 5 | 2026-08 | 4126 | 0.424 | 0.260 | 0.164 | 0.132 | 0.311 | 0.065 | 0.064 | 141,000 |
| 6 | 2026-09 | 234 | 0.709 | 0.359 | 0.316 | 0.124 | 0.329 | 0.051 | 0.013 | 200,550 |

Composition check: AI_POSITIONED share rises from 20.6% (May) to 31.1% (Aug) on the full uncensored sample, but the **seeded share of those rows climbs from 5% (May) to 82% (Aug)**; on unseeded rows only, AI_POSITIONED falls (25.2% June, 20.1% July, 11.0% Aug, n=762) and EXPOSED rises (4.7% to 10.6%). The two readings point in opposite directions; the trend is a crawl artifact. Uncensored ai_strict share is 22% vs 19.7% for censored (uncensored also has 88.6% salary posted vs 81.5%). **Null/uninterpretable trend; cross-section is the finding.**

## What is solid, what is fragile

Solid: pay gap by class and its approximate size (1.9x-2.9x depending on how pay type is handled); class explains about half of variance; county gradient in AI_POSITIONED share (unseeded and full agree); entry-level thickness of exposed occupations; no excess omission in exposed classes; DataAnnotation dominance of AI_DATA_WORK.
Fragile: ai_use premium inside exposed (220 postings; zero within firm); AI vs non-AI entry floor in exposed (n=45); WARN comparison (mostly big firms, 3-14% of postings); ai_hiring (precision 64-65%, recall unknown, 68% NVIDIA).
Not run: Glassdoor sub-rating test (file absent).

---

## ADDENDUM (TEST 7 sub-test): Do WARN-filing firms have worse Glassdoor sub-ratings?

Added after the main memo; nothing above was changed. Script `code/jobs_t7g.py`; results `base/jobs_warn_glassdoor.csv` (firm-level comparisons, raw and size-adjusted) and `base/jobs_warn_glassdoor_bands.csv` (size-band cells; rows for the 30+ review variant are appended after the first 20 and repeat the same labels).

**Data handling.** Sub-rating zeros: in `glassdoor_ca.parquet` the "not rated" codes are already NaN (zero share = 0 in every rating column; 31-33% missing in sub-ratings), and the shipped `glassdoor_company.csv` means equal my recomputation from the parquet to 1e-15, so they already treat 0 as missing. I used recomputed firm means anyway, with 0 forced to missing. Firms need >=10 reviews (also checked >=30). WARN set = firms with a WARN notice in a Bay county (primary) or any CA notice, joined on company_norm (exact).

**Match.** Of 922 Bay-county WARN firms, 223 (24.2%) are in the Glassdoor table and 134 (14.5%) have >=10 reviews. For any-CA WARN: 418 of 2,741 (15.2%) present, 197 (7.2%) with >=10 reviews. Comparison cells: 134 WARN vs 1,229 non-WARN firms (primary). The sample is the large, well-known employers that Glassdoor covers; it is not a sample of all filers.

**Size control.** WARN firms have more reviews (median 50 vs 20), so raw gaps are partly a size effect. I report raw differences, differences controlling for log(review count), and differences with review-count band dummies (10-24, 25-99, 100-499, 500+). Review count is a crude size proxy. Heteroskedasticity-robust SEs; firm is the unit (each firm's mean counts once). Cells: 40/709, 47/438, 37/77, 10/5 (WARN/non-WARN) by band, so the 500+ band is not usable.

Difference = WARN minus non-WARN, in rating points (1-5 scale), Bay-county WARN, all CA reviews, firms with >=10 reviews:

| rating | mean WARN | mean non-WARN | raw diff (se) | + log(reviews) control (se) | + size-band control (se) |
|---|---|---|---|---|---|
| overall | 3.540 | 3.508 | +0.031 (0.038) | -0.028 (0.039) | -0.012 (0.040) |
| compensation & benefits | 3.640 | 3.376 | +0.264 (0.044) | +0.209 (0.047) | +0.216 (0.047) |
| career opportunities | 3.285 | 3.278 | +0.007 (0.046) | -0.071 (0.048) | -0.062 (0.049) |
| senior leadership | 2.985 | 3.085 | -0.100 (0.045) | -0.133 (0.047) | -0.121 (0.047) |
| work-life balance | 3.626 | 3.465 | +0.161 (0.042) | +0.167 (0.044) | +0.184 (0.044) |

**Result.**
- **Null on overall rating:** WARN filers are not rated worse overall (raw +0.03, adjusted -0.01 to -0.03, all within about 1 se of zero).
- **Only senior leadership is lower**, by about 0.12-0.13 points (adjusted, about 2.6 se). The sign holds in every size band with adequate cells (10-24: -0.155; 25-99: -0.106; 100-499: -0.143) and in the Bay-reviews-only sample (-0.175, se 0.057), the any-CA WARN set (-0.167, se 0.043) and the 30+ review threshold (-0.129, se 0.050). It is a modest effect: about 0.12 points on a scale where firms differ by a standard deviation of far more.
- **Compensation/benefits and work-life are higher** at WARN firms (+0.22 and +0.18 adjusted), mostly in the smaller size bands; comp is near zero in the 100-499 band (+0.03). This is the opposite of "worse sub-ratings", and plausibly reflects that WARN filers are disproportionately tech and large-company employers. Career opportunities: no difference after size control (-0.06, se 0.05).
- Cannot say: ratings are cumulative over 2025-2026 reviews, not timed against the layoff notice, and the WARN firms in this table are 14% of Bay-county filers. Review count is a weak size proxy and the 500+ band has only 15 firms. This is association among well-known firms, not an effect of layoffs on morale.
