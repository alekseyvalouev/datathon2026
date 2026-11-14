# Memo 1: stance classification [H1-H3]

**Task.** Predict support / oppose / neutral for a spoken comment from the secretary's note.

**Labels.** Only rows with `position_source == "stenographer"` (the commission secretary's +, −, = mark) and non-empty text, excluding Planning staff: 30,935 comments. 37% of texts are exact duplicates of another ("Support", "Staff report").

**Split.** Train on 2019 and earlier (21,376); test on 2021 onward (7,387); 2020 left out as a gap. Test class mix: support 53%, oppose 41%, neutral 6%.

**Models.** Majority class; a keyword rule; TF-IDF (word 1-2 grams plus character 2-5 grams) with class-weighted logistic regression; the same with stance words stripped; then added one-hot role, calendar section and case type; then TF-IDF of the agenda item description (first 1,500 characters), log comment length and log speaking order. No information from other comments on the same item is used, since that would leak labels.

**Results.** See FINDINGS section 2 and `results/02_…`, `results/03_…`.

**Why it is hard.** Notes such as "Family housing", "Owns a fitness studio a few blocks away" or "Read statement from a 92 yr. old neighbor" do not state a side. Neutral is the weakest class (F1 0.26): the model over-predicts it.

**Subgroup performance (full model).**
- Calendar: discretionary review 0.83 accuracy (n=923); regular calendar 0.63 (n=6,093).
- Role: project team 0.99; review requestors 0.96; construction 0.85; pro-housing advocacy 0.73; no affiliation 0.62; neighborhood associations 0.46; tenant associations 0.40.
- Length: 1-2 words 0.77; 3-5 words 0.63; 6-15 words 0.58; 16+ words 0.53.

**Limits.**
- The label is the secretary's judgment, recorded systematically only from about 2005 and with a coverage jump in 2018.
- The text is a third party's summary. The model learns the secretary's vocabulary as much as speakers' positions.
- In discretionary-review hearings a "+" may mean support for the requestor.
- Written comments have LLM labels; no human-labelled written test set exists.

**Next steps not done.** Hand-label 300-500 written comments; fine-tune a small transformer; add the stance of the same speaker on other projects as a prior.
