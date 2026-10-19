# WLM pairwise evaluation

A simple Django tool, hosted on [Wikimedia Toolforge](https://wikitech.wikimedia.org/wiki/Portal:Toolforge), for judging the final round of photo contests such as **Wiki Loves Monuments Brasil**.

Instead of asking each juror to rank dozens of images at once, the tool shows **two Wikimedia Commons images at a time** and asks which one is better (or whether they tie). All votes from the whole jury are combined into a single ranking with the [**Bradley–Terry model**](https://en.wikipedia.org/wiki/Bradley%E2%80%93Terry_model), which also reports how reliable that ranking is.

Developed by [Wikimedia Brasil](https://br.wikimedia.org/).

> **Status:** active
>
> **Maintainers:** [EPorto (WMB)](https://meta.wikimedia.org/wiki/User:EPorto_(WMB)) and [ACorrêa (WMB)](https://meta.wikimedia.org/wiki/User:ACorr%C3%AAa_(WMB)), Wikimedia Brasil
>
> **Last documentation review:** 2026-10-19
>
> **Questions, bugs and data requests:** *add the issue tracker*
>
> **Security reports:** see [Security](#security)

---

## Features

- **Login with a Wikimedia account** (OAuth 1.0a via Meta-Wiki).
- **Pairwise voting** with mouse or keyboard: left, right or tie. No skipping.
- **Balanced pair schedule**: every juror sees every image the same number of times, and no pair of images is ever repeated across the jury.
- **Full vote history**: every vote and every change is logged with its timestamp.
- **Dashboard** with the live ranking (for organizers), a top-10 gallery, jury progress and per-juror rankings.
- **Jury agreement**: per-juror agreement with the rest of the jury and split-half reliability.
- **Fairness safeguards**: jurors can only see their own ranking while voting is open, and their votes lock once they open the dashboard, so that partial results cannot influence the voting (no [boca de urna](https://pt.wikipedia.org/wiki/Boca_de_urna)!).
- **Translatable interface** (English and Brazilian Portuguese included).

---

## Why a new tool?

Following the ABPD principle *reuse before rebuilding*, existing options were considered first. [Montage](https://montage.toolforge.org/), the jury tool used by many Wiki Loves Monuments national contests, covers yes/no, rating and ranking rounds, but has no pairwise comparison round with a statistical model behind it.

Due to the timeline of our Wiki Loves Monuments 2026 campaign, we implemented this tool, but we hope to contribute it as a pull request to Montage in 2027. This tool is deliberately narrow: it only replaces the **final round** (until now, the average of each juror's ranking), and earlier rounds keep using the existing workflow.

**Strategic link.** The tool serves the [Wikimedia Brasil Strategy 2026–2028](https://br.wikimedia.org/wiki/Estrat%C3%A9gia_Wikimedia_Brasil_2026-2028):

- **Axis 1, Sustain collaborative practices for free knowledge.** It gives Wiki Loves Monuments Brasil, one of WMB's main content-contribution campaigns, a tool that makes its jury work lighter and its outcome more robust (*"provide tools, resources and training to facilitate content contribution and the sustainability of projects"*). It also strengthens *"community governance practices that ensure democratic participation, transparency and co-responsibility in decision-making"*: every vote and every change is logged, every image gets the same exposure to every juror, and the jury can see how the final result was reached.
- **Strategic objective:** *"contribute to the improvement of free technologies and consolidate public-interest digital infrastructure according to regional realities and needs"*. The tool is free software, runs on Wikimedia's own infrastructure (Toolforge, Commons, Meta-Wiki login) and was built to answer a necessity Brazilian jurors have.
- **Principle:** *participatory critical documentation*, with its emphasis on rigour, transparency and equal treatment, which here means equal exposure of every image and an auditable result.

---

## How the method works

### Pairs are generated in blocks

A *block* is a set of pairs in which every image appears exactly once (N/2 pairs for N images). Blocks are built with the [round-robin *circle method*](https://pt.wikipedia.org/wiki/Round-robin), which splits all N(N−1)/2 possible pairs into N−1 disjoint blocks. Each juror receives a number of distinct blocks; inside each block the order of the pairs and the left/right side of each image are drawn at random.

Tha means:

- every image is shown to each juror the same number of times;
- no pair is judged twice by the whole jury, as long as the jury uses at most N−1 blocks;
- if a juror stops early, the images they did see are still evenly covered.

The draw is reproducible: the random **seed** and the number of blocks are stored with each campaign.

### How many blocks?

The target is about **54 comparisons per image across the whole jury**, which in simulations gave a 92–98% chance of reaching a reliability of 0.90 in a single round, even with some groups of very similar images.

```
blocks per juror = 54 ÷ number of jurors   (rounded up)
pairs per juror  = blocks per juror × ⌊N ÷ 2⌋
```

| Jurors | Blocks per juror | Pairs per juror (N = 60) |
|---|---|---|
| 5 | 11 | 330 |
| 6 | 9 | 270 |
| 7 | 8 | 240 |

### Ranking: Bradley–Terry

Each image *i* has a latent strength πᵢ, and the probability that *i* beats *j* is πᵢ / (πᵢ + πⱼ). Strengths are estimated by maximum likelihood with Hunter's MM algorithm. The score shown in the dashboard is ln πᵢ: 0 is average, and every +0.69 doubles the odds of winning a comparison.

- **Ties** count as half a win for each image.
- Each image also gets one **virtual tie** against a reference of strength 1. This light regularisation keeps the estimate finite for images that never lost or never won.
- Left/right position does not affect the model: sides are randomised so that any position bias of a juror averages out.

### Reliability and agreement (informative only)

- **Agreement with the others**: for each juror, the ranking is refitted without their votes, and the tool counts how often the juror chose the image the rest of the jury places higher. About 50 % means coin-flipping; 70–80 % is supposed typical.
- **Tie rate** per juror.
- **Split-half reliability**: the jury is split into two halves in every possible way, a ranking is fitted for each half, and the halves are correlated. The Spearman–Brown correction estimates the reliability of the full jury.

### References

- Bradley, R. A.; Terry, M. E. (1952). Rank analysis of incomplete block designs I. *Biometrika*, 39(3/4), 324–345.
- Davidson, R. R. (1970). On extending the Bradley–Terry model to accommodate ties in paired comparison experiments. *JASA*, 65(329), 317–328.
- Hunter, D. R. (2004). MM algorithms for generalized Bradley–Terry models. *Annals of Statistics*, 32(1), 384–406.
- Chen, Y.; Fan, J.; Ma, C.; Wang, K. (2019). Spectral method and regularized MLE are both optimal for top-K ranking. *Annals of Statistics*, 47(4), 2204–2235.
- Mantiuk, R. K.; Tomaszewska, A.; Mantiuk, R. (2012). Comparison of four subjective methods for image quality assessment. *Computer Graphics Forum*, 31(8), 2478–2491.
- Verhavert, S.; Bouwer, R.; Donche, V.; De Maeyer, S. (2019). A meta-analysis on the reliability of comparative judgement. *Assessment in Education*, 26(5), 541–562.

---

## Roles and permissions

| | Voting open | Voting closed, results not published | Closed and published |
|---|---|---|---|
| **Admin** (staff) | full dashboard, live updates | full dashboard | full dashboard |
| **Juror, still voting** | vote | — | full dashboard |
| **Juror, finished** | own ranking only (votes lock) | own ranking only | full dashboard |
| **Anyone else** | — | — | — |

Opening the dashboard **locks the juror's votes** for that campaign, so that seeing a ranking cannot influence later votes. The home page asks for confirmation before opening it.

---

## Using the tool

### Create a campaign (admins)

1. Log in and click **New campaign**.
2. Paste the Commons file names, one per line (the `File:` prefix is optional).
3. Paste the jurors' Wikimedia usernames, one per line.
4. Set the number of blocks per juror (see the table above) and save.

Pairs are generated immediately. Keep a copy of both lists and of the seed shown in the admin if you need to document how the pairs were drawn.

### Vote (jurors)

Open the campaign from the home page and choose the better image of each pair.

| Key | Action |
|---|---|
| `←` or `A` | left image is better |
| `→` or `D` | right image is better |
| `↓` or `S` | tie |
| `Z` | go back to the previous pair (to change a vote) |

Every vote is saved immediately, so judging can be split over several sessions.

### Close and publish (admins)

In **Admin → Campaigns**:

1. Untick **Open for voting**.
2. Review the dashboard.
3. Tick **Results published** to release the full results to the jury.

### Admin operations

- **Give a pair back to a juror**: *Admin → Pairs*, filter by campaign and juror, select the pairs and run **Reset vote**. The reset is recorded in the vote log.
- **Unlock a juror** who opened the dashboard by mistake: *Admin → Jurors*, open the juror and clear *dashboard first seen at*.
- **Audit votes**: *Admin → Votes* lists every vote and change, read-only.

---

## Local development

Requirements: Python 3.12+, and `gettext` for compiling translations.

```bash
git clone https://github.com/wikimediabrasil/wlmevaluation WLMEvaluation
cd WLMEvaluation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root (it is ignored by Git):

```
DJANGO_SECRET_KEY=<generate one, see below>
DEBUG=1
ALLOWED_HOSTS=127.0.0.1,localhost
OAUTH_KEY=<consumer key>
OAUTH_SECRET=<consumer secret>
OAUTH_CALLBACK=http://127.0.0.1:8000/oauth/complete/mediawiki/
```

Generate a secret key with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then:

```bash
python manage.py migrate
python manage.py compilemessages
python manage.py runserver
```

Open http://127.0.0.1:8000/ and log in with your Wikimedia account. To make yourself an admin after the first login:

```bash
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='YourUsername').update(is_staff=True, is_superuser=True)"
```

### OAuth consumer

Register an **OAuth 1.0a** consumer at [Special:OAuthConsumerRegistration](https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose/oauth1a) on Meta-Wiki:

- **Callback URL**: `http://127.0.0.1:8000/oauth/complete/mediawiki/`;
- tick **Allow consumer to specify a callback**;
- grants: **User identity verification only**.

Consumers usable by other accounts must be approved by a Meta-Wiki administrator, which can take a few days.

---

## Translations

Interface strings are written in English and marked for translation.

```bash
python manage.py makemessages -l pt_BR
# edit locale/pt_BR/LC_MESSAGES/django.po
python manage.py compilemessages
```

The language follows the browser; `LANGUAGE_CODE` in `settings.py` sets the default.

---

## Personal data and privacy (LGPD)

The tool follows the ABPD principle *privacy from the start*: it collects only what judging requires.

| Data | Where | Purpose | Who can see it                                                                                                                                |
|---|---|---|-----------------------------------------------------------------------------------------------------------------------------------------------|
| Wikimedia username | Django user, `Juror` | identify jurors and admins | admins; jurors see other jurors' usernames after results are published                                                                        |
| OAuth tokens returned by Meta-Wiki | `social_django` tables | complete the login | nobody through the interface                                                                                                                  |
| Each vote, its changes and timestamps | `Pair`, `Vote` | compute the ranking, audit changes | admins; after publication, the campaign's jurors (per-juror rankings), and after end of jury process, the ranking per jury member, anonymized |
| Time the juror first opened the dashboard | `Juror` | lock votes | admins                                                                                                                                        |
| Session cookie | browser | keep the user logged in | —                                                                                                                                             |

- **Not collected:** e-mail, real name, IP addresses (the OAuth grant is *User identity verification only*; Toolforge's own infrastructure logs are governed by the Wikimedia Cloud Services terms).
- **Retention:** *to be defined* — suggested: keep individual votes until the contest's results are final plus an appeal period, then keep only the published ranking and delete or anonymise per-juror data.
- **RIPD:** not required — no sensitive data, small volume, low risk to data subjects.
- **Data subject requests** (access, correction, deletion): through the contact channel at the top of this README.

---

## Security

- CSRF protection on every form (Django middleware), including login and logout.
- All database access goes through the Django ORM (parameterised queries); templates auto-escape output.
- Every permission is checked on the server (`PermissionDenied`), not only hidden in the interface.
- Views declare the HTTP methods they accept; votes only change through POST.
- External resources come only from Wikimedia domains (`tools-static.wmflabs.org`, `commons.wikimedia.org`).
- Secrets live in environment variables (`.env` locally, `toolforge envvars` in production) and are never committed. **Rotate** `DJANGO_SECRET_KEY` and the OAuth consumer secret whenever a maintainer leaves the project.
- **Reporting vulnerabilities:** contact the maintainers. Issues affecting Toolforge itself follow the [Wikimedia Foundation security process](https://www.mediawiki.org/wiki/Reporting_security_bugs).

---

## Accessibility

- Voting works entirely with the keyboard; every control is a real `<button>` with an accessible label.
- Visible focus outline, 40px touch targets, and text contrast above WCAG AA (accent `#990000` on white ≈ 8.9:1).
- Layouts adapt to phone screens; images are scaled to fit without cropping.

---

## Backup and discontinuation
- **Discontinuation plan:** when the tool is retired (for example, once the pairwise round is accepted and available in Montage), export the final rankings of every campaign to the contest's spreadsheet or wiki pages, apply the retention rule above to per-juror data, drop the ToolsDB database, stop the webservice, revoke the OAuth consumer, and mark the tool as *discontinued* in the future WMB tool catalog and this repository.

---

## Use of AI in development

In line with ABPD section 5.10, this is recorded: the methodology (choice of Bradley–Terry, sample-size simulations), large parts of the code, the interface texts, the Portuguese translation and this README were drafted with substantial help from a generative AI assistant (Claude, by Anthropic). Every piece was **extensively** reviewed, adapted and tested by the maintainers, who remain responsible for it. No personal data from jurors or contest participants, or credentials was entered into the assistant. Design decisions were made by a human :)

---

## Contributing

Good first tasks:

- automated tests for `pairing.py` (no repeated pairs, equal exposure per juror) and `ranking.py` (order follows strength, ties count as half);
- tests for the access rules in `views.py` (juror, finished juror, admin, published results);
- a "go to pair" field in the voting bar;
- a scheduled backup job (`toolforge jobs`);
- a GitHub Actions workflow running the tests, and Dependabot and SonarQube alerts.

Changes are reviewed by a second person before deployment; when no reviewer is available, record the decision and the reason in the pull request.

---

## ABPD self-assessment

Assessment against the [Development Best Practices Framework](https://meta.wikimedia.org/wiki/Wikimedia_Brasil/Development_Best_Practices_Framework) (section 5.11). Reviewed on 2026-10-19.

| # | Criterion | Status      | What is missing |
|---|---|-------------|---|
| 5.11.1 | Public repository and declared free license | **Present** | — |
| 5.11.2 | README with purpose, installation and execution | **Present** | — |
| 5.11.3 | Configuration and production documentation | **Present** | — |
| 5.11.4 | Automated tests for critical functions | **Absent**  | `evaluations/tests.py` is empty; see *Contributing* |
| 5.11.5 | Continuous integration | **Absent**  | GitHub Actions workflow |
| 5.11.6 | Reproducible and documented deployment | **Present** | — |
| 5.11.7 | Secrets out of the code, with planned rotation | **Present** | — |
| 5.11.8 | Maintainer identified | **Present** | — |
| 5.11.9 | More than one person able to maintain it | **Present** | — |
| 5.11.10 | Minimum security checklist applied | **Partial** | add secure cookie settings for production; enable dependency alerts |
| 5.11.11 | Basic accessibility verified | **Present** | — |
| 5.11.12 | Translatable interface text | **Present** | — |
| 5.11.13 | Substantial AI use recorded | **Present** | — |
| 5.11.14 | Personal data mapped; RIPD where applicable | **Present** | — |
| 5.11.15 | Backup and recovery | **Absent**  | scheduled dump job and a tested restore |
| 5.11.16 | Status declared | **Present** | active |

---

## Project structure

```
WLMEvaluation/          Django project settings and root URLs
users/                  logout route
evaluations/
    models.py           Campaign, Image, Juror, Pair, Vote
    pairing.py          round-robin block generation
    services.py         campaign creation
    ranking.py          Bradley–Terry fit
    agreement.py        juror agreement and split-half reliability
    views.py            home, voting, dashboard, campaign form
    admin.py            admin screens and the "Reset vote" action
templates/              base layout and home page
static/css/style.css    styles
locale/                 translations
```