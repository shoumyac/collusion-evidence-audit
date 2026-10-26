# Submission checklist (humans click Submit)

Deadline: Mon 26 Oct 2026, 22:59 Melbourne time (= Sun 25 Oct 11:59 PM AoE). Aim to submit by about 20:00.

## Before submitting
- [ ] Each author recomputes the five numbers in `VERIFY_YOURSELF.md` and reads two transcripts.
- [ ] Both authors read `report/report.pdf` end to end and edit the wording into their own words.
- [ ] Add one sentence to the LLM Usage Statement saying you checked the results yourselves (only if true).
- [ ] If you want the official Google Doc format: copy https://docs.google.com/document/d/1Y5wd3VRbXU5N08BvAGiJUQTaWbMCSPjhzXsR-ozuehg/copy and paste the text, tables and figures in. The template asks for about 4 pages of main text and at most 8 (references and appendices excluded). Delete the instruction text.
- [ ] Check the PDF: abstract is 150 to 250 words, both author names and "University of Melbourne", the footnote mentions the sprint, no placeholder text.
- [ ] Confirm the repo is public and has no keys: https://github.com/shoumyac/collusion-evidence-audit
- [ ] Check Anthropic and Modal spend and stop anything still running (`modal app list`).

## Form fields (from the sprint page)
- Project title: Auditing a Collusion Detector: Unit of Replication, Calibration and Say-versus-Do Gaps in LLM Pricing Agents
- Project summary: use the abstract.
- PDF report (up to 25 MB): `report/report.pdf` (about 0.6 MB).
- Track: Track 2 (Detection and Audit).
- Interested in publication: your choice.
- Optional: code link (the GitHub repo), presentation recording, slides.
- Team: Shoumya Chowdhury, Anmita Das; same title and names everywhere. To replace a PDF later, submit again with a slightly different title or email sprints@apartresearch.com before the deadline.

## 3 to 5 minute video script (optional)
1. (0:00 to 0:30) The question: when a detector says "collusion", what unit of evidence stands behind it? Show Figure 1: 22,127 logged runs, 3,918 distinct within files, 2,740 across files.
2. (0:30 to 1:30) Held-out batches. Show Figure 2: shipped p-values flag 99% of honest pricing batches. Show Figure 3: about 20 independent honest batches give a 5% false-positive rate, and the Beta curve matches. Say plainly that 10^-3 would need about 3,000 units.
3. (1:30 to 2:30) LLM game with six models. Show Figure 4 (prices against cost, Nash 4.6, joint maximum 5.5). Say honest LLMs price below Nash.
4. (2:30 to 3:45) Say versus do. Read two lines of an honest Haiku transcript ("I'll hold 1.75 as long as you do") and one collusion-condition refusal. Show Figure 5 and Table 3: swap control keeps the price rise, so it is parallel obedience, not communication.
5. (3:45 to 4:30) Evidence ladder and the audit kit; limitations (one game, prompt sensitivity, small batch counts per LLM condition). Close with the repo link.
