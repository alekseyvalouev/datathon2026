# Bay Area planning-commission / council meeting minutes, transcripts and public-comment records (as of 14 Nov 2026)

Researcher's note on verification: this sandbox could not reach `webapi.legistar.com`, `*.legistar.com` (mostly), `dataverse.harvard.edu`, `huggingface.co` or `youtube.com` directly (proxy 403 / allowlist). Facts below marked "verified" come from pages actually fetched or from search-result listings; anything I could not open is listed under Gaps and must be smoke-tested by the team (each test is a 1-line curl).

## Q1. Which Bay Area cities publish through Legistar (and is the Legistar Web API usable), which use other platforms, and how does the SF Planning Commission publish minutes and comment letters?

### Takeaway
The single most useful primary source is the San Francisco Planning Commission: its minutes list each public speaker by name with a +/-/= (support/oppose/neutral) mark and a short topic label, back to 1998, as public PDFs/HTML. Legistar is widespread in the Bay Area (San Jose, Hayward, Alameda, San Leandro confirmed; others unverified from here) and has a no-auth JSON API for many clients, but Legistar minutes generally do not carry coded speaker positions; Berkeley's and Oakland's minutes are plain PDFs and Berkeley's record only a count of commenters.

### Cited Findings

**San Francisco Planning Commission (best primary source)**
- Minutes format, verified on the 24 Aug 2017 minutes (Pier 70 item): each item has a `SPEAKERS:` line with entries of the form marker + name + short topic, e.g. "+ Scott Feeny – Support, maximize housing", "- Speaker – View shed loss, taking compensation", "= Allison Heath – DEIR"; "+" = support, "-" = opposition, "=" = neutral/no position; unnamed people appear as "Speaker"; some entries lack marker or topic; an `ACTION:` line gives the outcome and vote — [SF Planning minutes 2017-08-24 PDF](https://commissions.sfplanning.org/cpcpackets/20170824_cal.min.pdf)
- So the record is: speaker name = yes; position = yes (clerk-coded); text = a short topic label, NOT verbatim speech — [same PDF](https://commissions.sfplanning.org/cpcpackets/20170824_cal.min.pdf)
- URL patterns seen live in search results: minutes `https://commissions.sfplanning.org/cpcpackets/YYYYMMDD_cal.min.pdf` (2017 example); older minutes mirrored at `https://sfplanning.s3.amazonaws.com/default/files/meetingarchive/planning_dept/commissions.sfplanning.org/cpcpackets/YYYYMMDD_cal.min.pdf` (2013-2014 examples); legacy HTML minutes back to 1998 at `default.sfplanning.org/meetingarchive/...` ([Oct 1998 minutes page](https://default.sfplanning.org/meetingarchive/planning_dept/sf-planning.org/modules/min1098-documentid=4779.htm)); 2015-era agenda pages on [sfgov.org/sfplanningarchive](https://www.sfgov.org/sfplanningarchive/meeting/planning-commission-october-8-2015-agenda); current agendas as PDFs under `sfplanning.org/sites/default/files/agendas/YYYY-MM/` (a 15 Oct 2026 agenda is indexed, so the site is live as of autumn 2026) — [2013 minutes on S3](https://sfplanning.s3.amazonaws.com/default/files/meetingarchive/planning_dept/commissions.sfplanning.org/cpcpackets/20130912_cal.min.pdf); [Oct 2026 agenda](https://sfplanning.org/sites/default/files/agendas/2026-10/20261015_cpc%20%28ID%201591031%29.pdf)
- Written correspondence: project case packets are posted as PDFs at `commissions.sfplanning.org/cpcpackets/<case-number>_<MMDDYY>.pdf` (examples indexed) and per-hearing "hearing packet" resource pages exist on sfplanning.org (e.g. 16 Apr 2026). The Sahn repo (Q2) states written public comment is taken from the "Commission Packet" issued before each hearing, available since 2017 — [example case packet](https://commissions.sfplanning.org/cpcpackets/2020-008417CWP_011421.pdf); [hearing packet page, Apr 16 2026](https://sfplanning.org/resource/planning-commission-hearing-packet-april-16-2026); [Sahn repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Sahn's repo documents where the spoken-comment record lives by era: 2019 onward in PDFs, 2015-2018 on sfgov.org archive pages, 1998-2014 on a mirrored legacy site — [Sahn repo](https://github.com/alexandersahn/sf-planning-public-comment-data)

**San Francisco Board of Supervisors**
- Land Use and Transportation Committee agendas are published on sfbos.org (HTML pages 2019-2023, PDFs 2024-2025) and, in 2026, as PDFs at `media.api.sf.gov/documents/lutMMDDYY_agenda.pdf` (26 Oct and 9 Nov 2026 agendas indexed) — [sfbos.org 2023 agenda](https://sfbos.org/event/2023/lut032023_agenda); [Nov 9 2026 agenda](https://media.api.sf.gov/documents/lut110926_agenda.pdf)

**Legistar Web API (general)**
- URL pattern `https://webapi.legistar.com/v1/{Client}/matters`, `/events`, `eventitems/{id}/votes`, `matters/{id}/histories`; OData `$filter`, `$top`, `$skip`; responses capped at 1000 records per call; some clients require a `token` URL parameter; GETs only return items public on the client's InSite web portal; no rate limit or terms of use are documented on the page; footer shows © 2026 Granicus (page live in 2026) — [Legistar Web API examples](https://webapi.legistar.com/Home/Examples)
- An R package ships a tested table of 286 Legistar client names with a TRUE/FALSE flag for whether each answered an API call (last updated 12 May 2024) — fastest way to enumerate which Bay Area clients respond — [legistarapi `legistar_clients`](https://elipousson.github.io/legistarapi/reference/legistar_clients.html)

**Confirmed Bay Area Legistar sites (from fetched page or search listing)**
- Hayward: `hayward.legistar.com`; 16 bodies including Planning Commission, City Council, and a Housing Policy & Resource Committee; older documents in a separate Laserfiche "Meeting Documents Archive" — [hayward.legistar.com/Departments.aspx](https://hayward.legistar.com/Departments.aspx)
- San Jose: `sanjose.legistar.com` (calendar and departments pages indexed); Planning Commission agendas/minutes are also linked from the city planning site — [sanjose.legistar.com](https://sanjose.legistar.com/Calendar.aspx); [San Jose Planning Commission page](https://www.sanjoseca.gov/your-government/departments-offices/planning-building-code-enforcement/planning-division/commissions-hearings-and-developers-roundtable/planning-commission)
- City of Alameda: `alameda.legistar.com` — [alameda.legistar.com](https://alameda.legistar.com/Departments.aspx)
- San Leandro: `sanleandro.int.legistar.com` (note the non-standard `.int.` host) — [sanleandro.int.legistar.com](https://sanleandro.int.legistar.com/Departments.aspx)
- San Jose council agenda PDFs are hosted on the city's Legistar site (as linked by a third-party summariser) — [tldrgov San Jose page](https://tldrgov.pages.dev/ca/san-jose/city-council/2025-08-26)

**Non-Legistar cities**
- Oakland Planning Commission: agendas, staff reports and minutes are PDFs on oaklandca.gov (pattern `oaklandca.gov/files/assets/city/v/1/boards-amp-commissions/documents/pc/pre-2016-archive/MM-DD-YYYY-<type>.pdf` for the pre-mid-2016 archive); video is on Granicus (`oakland.granicus.com/player/clip/<id>`), with unpredictable clip IDs; the archive page does not mention posted public comments; mid-2016 onward is on a separate "Planning Commission & Committee Meetings" page — [Oakland PC archive](https://www.oaklandca.gov/Government/Boards-Commissions/Planning-Commission/Archive-of-Planning-Commission-Meetings-and-Documents)
- Berkeley: Planning Commission and Zoning Adjustments Board documents are PDFs on berkeleyca.gov (`/sites/default/files/legislative-body-meeting-minutes/…`, `/legislative-body-meeting-agendas/…`); the 17 Sep 2025 Planning Commission minutes record public comment as a count only ("Public Comments: 42"), no names, positions or content — [Berkeley PC minutes 2025-09-17](https://berkeleyca.gov/sites/default/files/legislative-body-meeting-minutes/2025-09-17_FINAL%20Minutes_0.pdf); [Berkeley ZAB page](https://berkeleyca.gov/your-government/boards-commissions/zoning-adjustments-board?page=6)
- Berkeley posts long "administrative record" PDFs for ZAB appeals to council (example: 2600 Tenth Street, July 2024), a likely location of written comment letters — [Berkeley admin record PDF](https://berkeleyca.gov/sites/default/files/documents/2024-07-30%20ADMIN%20RECORD%20ZAB%20APPEAL%20%202600%20TENTH%20STREET%20%28WEB%29.pdf)
- Fremont: Planning Commission agendas are in a city-website "Agenda Center" (fremont.gov/government/agenda-center/planning-commission), i.e. not obviously a `fremont.legistar.com` site — [Fremont agenda center](https://www.fremont.gov/government/agenda-center/planning-commission)

### Inferences
- For a 2-day event, scraping SF Planning minutes from scratch is unnecessary: Sahn's GitHub repo (Q2) already delivers the parsed result. Raw minutes matter only for spot-validation or for meetings after March 2026.
- Legistar API is good for agenda-item metadata (title, file number, date, body, attachments, votes) and for locating housing items and attachment PDFs (minutes, correspondence); it is not a source of structured per-speaker comments. Expect to download and parse attached PDFs.
- Berkeley's own minutes are useless for stance coding (counts only); for the home city the practical routes are meeting-video captions (Q3) or written letters inside agenda-packet / administrative-record PDFs.
- No documented rate limit does not mean none; keep to a polite pace (e.g. ~1 request/sec) and page with `$top=1000&$skip=`.

### Gaps
- NOT verified from here (network blocked): whether `webapi.legistar.com/v1/{client}/bodies` answers without a token for `sfgov`, `oakland`, `sanjose`, `sunnyvaleca`, `mountainview`, `hayward`, `santaclara`, `alameda`, `sanleandro`. From background knowledge (not confirmed in this session) SF Board of Supervisors, Oakland City Council, Sunnyvale, Mountain View, Santa Clara, Cupertino, Richmond, MTC and BART run Legistar sites; treat as a hypothesis and test with `curl "https://webapi.legistar.com/v1/<client>/bodies"`.
- Could not establish which specific Bay Area cities use PrimeGov, eScribe, CivicClerk/CivicPlus or NovusAgenda; searches returned only vendor marketing. Fremont appears to use a CivicPlus-style Agenda Center (inference from URL only). Palo Alto, Redwood City, Walnut Creek, Concord, Santa Rosa, Napa, Vallejo, San Rafael not checked.
- Did not confirm whether the SF Board of Supervisors' Legistar matter attachments reliably include public-correspondence PDFs, nor whether the Oakland City Council (as opposed to Planning Commission) minutes name speakers.
- Legistar "eComment" (Granicus) written comments: not verified for any Bay Area city.
- No explicit terms-of-use page for the Legistar API or for sfplanning.org scraping was found.

## Q2. Ready-made research datasets covering Bay Area cities or usable as labelled training data

### Takeaway
A ready-made, openly licensed, stance-labelled Bay Area dataset exists: Alexander Sahn's `sf-planning-public-comment-data` (73,002 SF Planning Commission comments, 1998 to March 2026, support/oppose/neutral, CC BY 4.0, CSV on GitHub) — this alone makes the scaled-down replication feasible within hours. The original Einstein-Glick-Palmer replication data (Dataverse doi:10.7910/DVN/RRF7EU) and Sahn's AJPS replication archive (doi:10.7910/DVN/WZOC7H) are secondary labelled sources; LocalView and MeetingBank give unlabelled transcripts.

### Cited Findings

**Sahn — SF Planning Commission public comment (top recommendation)**
- Repo: `github.com/alexandersahn/sf-planning-public-comment-data`; described as public comments and outcomes at the SF Planning Commission, 1998-present, parsed from minutes, extending Sahn (2025, AJPS) — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Coverage stated in README: 1,252 meetings, 25,560 agenda items, 73,002 comments, 28,421 commenters, January 1998 to March 2026; spoken comment 1998-present, written comment since 2017 — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Files: `comments.csv` (commenter, comment text, position, linked project/hearing, role/affiliation, `channel` = spoken vs written), `items.csv.gz` (case number, item text, staff recommendation, Commission action and vote, coded outcome, DataSF project attributes, coordinates), `meetings.csv`, `staff_tenure.csv`, `person_roster.csv`, `name_crosswalk.csv`, `codebook.md`, plus `data/reference/emails_coded.csv.gz` (coded written comments); `./update.sh` rebuilds from source — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Licence: code MIT, data CC BY 4.0; underlying records are public documents of the City and County of San Francisco — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Label provenance caveat (critical for classifier training): `position` comes from three sources flagged in `position_source` — the commission secretary's marks (systematic from about 2005), a classifier trained on those marks, and LLM coding for written comment — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Other caveats: addresses/phone numbers redacted from text; written-comment senders are salted hashes; names are not identities (namesakes); written comments are attached to the first hearing on/after the packet date and only 37% of items were heard on the packet date — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Underlying paper: 957 meetings 1998-2021, 8,392 agenda items (Regular Calendar and Discretionary Review only), 42,451 comments; polarity recorded by the stenographer for 31,182 (74%); a sentiment-based prediction agreed with recorded polarity only 69% of the time on 27,903 comments; 47.7% of commenters matched to a commercial voter file — [Sahn paper PDF](https://alexandersahn.com/papers/public_meetings_paper.pdf)
- Official replication archive for the article: AJPS Dataverse, https://doi.org/10.7910/DVN/WZOC7H; the GitHub repo is a successor build, not the replication archive — [Sahn paper PDF](https://alexandersahn.com/papers/public_meetings_paper.pdf); [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Published as Sahn (2025), AJPS 69(2): 685-700, doi:10.1111/ajps.12900; a follow-up on written comments (Sahn and Simko, "Issue Accountability Among Public Meeting Commenters") is described as conditionally accepted at AJPS — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data); [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/ajps.12900)

**Einstein, Glick & Palmer — Massachusetts (out-of-area labelled data)**
- Planning/zoning board hearings in 97 metro-Boston cities and towns (Boston excluded), 2015-2017, multi-unit housing proposals; 3,123 unique participants, 2,580 matched to voter file; 3,629 comment observations in the regression sample — [Einstein, Glick & Palmer paper](https://maxwellpalmer.com/docs/articles/Einstein_Glick_Palmer_Participation.pdf)
- Coding: position (support / oppose / neutral) and reasons (traffic, parking, density, affordability etc., ~19-20 categories, multiple allowed); intercoder agreement reported as full on position and 85% on topics — [same paper](https://maxwellpalmer.com/docs/articles/Einstein_Glick_Palmer_Participation.pdf)
- Minutes vary: summaries in most towns, full transcripts in some (Cambridge exact transcription) — [same paper](https://maxwellpalmer.com/docs/articles/Einstein_Glick_Palmer_Participation.pdf)
- Replication data stated to be at Harvard Dataverse https://doi.org/10.7910/DVN/RRF7EU — [same paper](https://maxwellpalmer.com/docs/articles/Einstein_Glick_Palmer_Participation.pdf)

**LocalView (Barari & Simko)**
- 139,616 videos with transcripts, 1,012 places, 2,861 governments, 49 states, 2006-2022; text is YouTube caption text (channel-uploaded or auto-generated), ~90% of videos have transcripts; Harvard Dataverse doi:10.7910/DVN/NJTBEM; formats RDS, Parquet, .dta, .csv, .json; described as self-updating; no speaker-level field listed — [Scientific Data article](https://www.nature.com/articles/s41597-023-02044-y)

**MeetingBank**
- 1,366 city-council meetings, 3,579 hours, six jurisdictions: Seattle, King County, Denver, Boston, Long Beach and Alameda, CA (so yes, the City of Alameda is included — the only Bay Area city); speech-to-text transcripts with diarization; built for summarization (6,892 segment-summary pairs), no stance labels — [MeetingBank dataset page](https://meetingbank.github.io/dataset); [MeetingBank-utils](https://github.com/YebowenHu/MeetingBank-utils)
- Downloads: Hugging Face `huuuyeah/meetingbank` (fields `id`, `summary`, `transcript`), audio at `huuuyeah/MeetingBank_Audio` (has an `Alameda` folder), transcripts on Zenodo record 7989108, video at `archive.org/details/meetingbank-alameda` — [MeetingBank-utils](https://github.com/YebowenHu/MeetingBank-utils); [HF audio repo](https://huggingface.co/datasets/huuuyeah/MeetingBank_Audio)

**Martin & Venugopal (Stanford, April 2026) — California councils**
- "Participation and Representation in Local Government Speech", arXiv:2604.21202 (23 Apr 2026): 25,414 council meetings from 115 California cities, 2015-2024, >75,000 audio hours, Whisper transcription + pyannote diarization; 150,000+ participants; an LLM gave 96,604 land-use speaker-issue comments a development-support score from -1 to 1; Bay Area cities named include San Francisco, Palo Alto, Los Gatos, San Jose. No data/code release URL found in the text; it uses L2 voter and CoreLogic data — [arXiv 2604.21202](https://arxiv.org/abs/2604.21202)
- Useful as method precedent and as the closest California replication of Neighborhood Defenders (finds speakers older, whiter, more male, more likely homeowners) — [arXiv 2604.21202](https://arxiv.org/abs/2604.21202)

**Other**
- tldrgov.pages.dev publishes per-meeting summaries (TL;DR, key decisions, agenda) for San Jose council; no transcripts, public-comment data, API or licence shown — [tldrgov](https://tldrgov.pages.dev/ca/san-jose/city-council/2025-08-26)
- California YIMBY's write-up confirms the Sahn SF study as the main California public-comment study (about 42,500 comments from SF Planning Commission minutes) — [CA YIMBY blog](https://cayimby.org/blog/unrepresentative-sample-how-public-meetings-weaken-fair-housing-outcomes/)

### Inferences
- Fastest viable plan: `git clone` the Sahn repo; train on rows where `position_source` = secretary's mark (human label) and hold out a test set from those only; treat classifier- and LLM-coded rows as silver labels or exclude them, otherwise the team evaluates a model against another model's output.
- Spoken-comment "text" in this dataset is most likely the clerk's short topic label (per the minutes format), so text is short and sometimes contains the word "support"/"opposed" itself (label leakage). The written-comment corpus (2017+) has longer, real prose but LLM-assigned labels. Read `codebook.md` first to confirm.
- A cross-domain test is cheap and interesting: train on SF, test on the Massachusetts EGP data (or vice versa), provided the EGP Dataverse files contain comment text and not just codes (unverified).
- Without voter-file matching, the team can still replicate descriptive shares (support vs oppose by project type, neighbourhood, year, repeat commenters, organisational affiliation via `person_roster.csv`) and link to project attributes/coordinates in `items.csv.gz`.
- LocalView stops at 2022 per the paper and has no speaker segmentation; isolating public comment on housing items would need LLM segmentation, heavy for 2 days. Good only as a supplementary unlabelled corpus.
- MeetingBank's Alameda subset is small, unlabelled and summarisation-oriented; low priority.

### Gaps
- Could not open Harvard Dataverse from here: file lists, sizes, access restrictions and licences for doi:10.7910/DVN/RRF7EU (EGP), doi:10.7910/DVN/WZOC7H (Sahn) and doi:10.7910/DVN/NJTBEM (LocalView) are unverified; AJPS/Dataverse archives are normally open download (CC0 by default) but confirm. Unknown whether the EGP archive includes comment text or only coded variables with names removed.
- The LocalView DOI printed in the article extraction had a trailing "41" (likely a footnote number); the correct DOI is believed to be 10.7910/DVN/NJTBEM. Which California/Bay Area places LocalView covers, and whether it has been updated past 2022, not verified; localview.net status not checked.
- Sahn repo: exact file sizes, per-file row counts, last commit date and the exact content of the comment-text column were not visible; repo listed 12 commits and coverage to March 2026.
- MeetingBank licence terms and Alameda's per-city meeting count/year range not retrieved.
- Council Data Project: could not load councildataproject.org (blocked); search results suggest an Oakland connection via OpenOakland and that CDP instances are mostly outside California, but no current Bay Area instance was confirmed. Background knowledge (unconfirmed) is that CDP once ran Oakland, Alameda, Mountain View and Richmond instances and that the project has been wound down/archived.
- No public-comment dataset found from UC Berkeley Terner Center or a Berkeley/Stanford group with released data; Martin & Venugopal have not (as far as could be seen) released theirs.
- citymeetings.nyc-style projects for Bay Area cities: only tldrgov found; none with downloadable transcripts.

## Q3. Do YouTube / Granicus auto-captions offer a practical route to verbatim comment text?

### Takeaway
Technically yes for cities that stream on YouTube, and it is the established research method (LocalView is built entirely on YouTube captions), but captions are unsegmented and unlabelled, and YouTube blocks caption requests from cloud IPs — so it is a stretch goal for a 2-day event, worth doing only for a handful of specific hearings.

### Cited Findings
- LocalView's 139,616 transcripts are YouTube caption text, either channel-uploaded or auto-generated, with about 90% of videos having a transcript — [Scientific Data article](https://www.nature.com/articles/s41597-023-02044-y)
- `youtube-transcript-api` (MIT) retrieves auto-generated captions (`find_generated_transcript`); its README warns that YouTube blocks most cloud-provider IPs (`RequestBlocked` / `IpBlocked`), that self-hosted setups can be blocked after too many requests, and suggests rotating residential proxies without guaranteeing success — [youtube-transcript-api README](https://github.com/jdepoix/youtube-transcript-api)
- Martin & Venugopal instead downloaded audio from municipal sites and official YouTube channels and ran Whisper plus pyannote diarization, then used LLMs to label speakers as government vs public and to score stance — [arXiv 2604.21202](https://arxiv.org/abs/2604.21202)
- Oakland Planning Commission video is on Granicus (`oakland.granicus.com/player/clip/<id>`), not shown as YouTube on its archive page — [Oakland PC archive](https://www.oaklandca.gov/Government/Boards-Commissions/Planning-Commission/Archive-of-Planning-Commission-Meetings-and-Documents)
- MeetingBank shows the diarized-transcript format obtainable from council video (word-level timing, speaker diarization) for Alameda — [MeetingBank dataset page](https://meetingbank.github.io/dataset)

### Inferences
- Run caption pulls from laptops on campus/home networks, not Colab/cloud VMs, and keep volume low (tens of videos), given the IP-blocking behaviour.
- Auto-captions lack speaker turns and agenda-item boundaries. A feasible mini-pipeline: pick 5-10 known contentious housing hearings, pull captions, have an LLM split into speaker turns and tag public commenters and stance, then hand-check a sample. This yields verbatim text the SF minutes lack and a nice out-of-distribution test set for a classifier trained on Sahn's data.
- Whisper + diarization at scale (as in the Stanford paper) is not realistic in 2 days without GPUs and prepared audio.

### Gaps
- Not verified which Bay Area bodies stream to YouTube vs Granicus/SFGovTV only (e.g. whether SF Planning Commission hearings on SFGovTV have downloadable caption files; whether Berkeley/Oakland/San Jose council channels on YouTube have auto-captions enabled).
- Not verified whether Granicus players for Oakland/SFGovTV expose caption/transcript files (some Granicus sites offer a closed-caption text download; unconfirmed here).
- Background knowledge only: Berkeley City Council posts a "captioner's record" for some meetings; a search for it returned nothing confirming this.

## Q4. Terms-of-use and rate-limit issues

### Takeaway
None of the recommended sources requires an application; the Sahn data is explicitly CC BY 4.0 and city records are public documents. The practical constraints are the Legistar 1000-row page cap and possible per-client tokens, YouTube's IP blocking, and research-ethics care around naming private individuals.

### Cited Findings
- Sahn repo: data CC BY 4.0, code MIT; cite Sahn (2025) and the dataset `CITATION.cff`; contact details redacted and written-comment senders hashed by the author — [GitHub repo](https://github.com/alexandersahn/sf-planning-public-comment-data)
- Legistar Web API: 1000 records per response, paging via `$top`/`$skip`; some clients require a token; no rate limits or terms stated on the examples page — [Legistar Web API examples](https://webapi.legistar.com/Home/Examples)
- YouTube captions: cloud IPs largely blocked; high request volume can trigger blocks even on residential IPs — [youtube-transcript-api README](https://github.com/jdepoix/youtube-transcript-api)
- LocalView: the Scientific Data article is CC BY 4.0; the dataset's own licence is not stated in the article — [Scientific Data article](https://www.nature.com/articles/s41597-023-02044-y)
- Both the Sahn and Einstein-Glick-Palmer studies relied on voter-file matching (commercial vendor / Massachusetts voter file) for demographics; that step is out of scope here and is not needed to use the comment/position data — [Sahn paper PDF](https://alexandersahn.com/papers/public_meetings_paper.pdf); [EGP paper](https://maxwellpalmer.com/docs/articles/Einstein_Glick_Palmer_Participation.pdf)

### Inferences
- Feasibility ranking for a 2-day datathon: (1) Sahn GitHub CSVs — minutes to obtain, labelled, Bay Area, open licence: HIGH. (2) EGP and Sahn Dataverse replication archives — direct download if unrestricted: HIGH/MEDIUM pending check. (3) Raw SF Planning minutes PDFs for post-March-2026 meetings or validation: MEDIUM (regular `SPEAKERS:` format, easy regex). (4) Legistar API for San Jose/Hayward/Alameda etc. item metadata + PDF minutes: MEDIUM-LOW (no coded positions; PDF parsing). (5) YouTube captions for a few hearings: MEDIUM-LOW, stretch goal. (6) LocalView / MeetingBank: LOW value for stance labels. (7) Berkeley and Oakland Planning Commission minutes: LOW (counts only / unstructured PDFs).
- Even though speakers' names are public record, presenting results in aggregate and not publishing named individuals' stances is the prudent default for a student project; Sahn's own redaction choices are a good template.

### Gaps
- No robots.txt or terms pages were checked for sfplanning.org, oaklandca.gov, berkeleyca.gov or Granicus-hosted video.
- Dataverse terms for the three archives unverified (see Q2 Gaps).
- YouTube Terms of Service position on automated caption retrieval was not reviewed from a primary source.
