# Channel-realism audit of semantic communication for non-terrestrial networks

Artefact for a journal manuscript in preparation. Everything here is released so that each
number in the paper can be traced to the command that produced it.

## What this asks

Surveys of semantic communication for non-terrestrial networks map NTN limitations (large
propagation delay, Doppler shifts of hundreds of kilohertz, short visibility windows,
elevation-dependent path loss) onto the works said to address them. This artefact asks a
narrower question that those mappings leave open: **are the works cited as addressing a
limitation actually evaluated under that limitation?**

The question is not rhetorical and the answer is not assumed. The audit is pre-registered in
[`claim-structure.md`](claim-structure.md), which was written and gated **before** any
experiment ran, and which records what the paper would still contribute if the audit came back
negative.

## Layout

```
code/     experiments, one file per measurement, each writes to results/ by absolute path
data/     public inputs (Starlink TLE set from Celestrak)
results/  raw JSON output, committed rather than summarised
figures/  generators; every figure and table in the paper is produced here
paper/    manuscript
```

## E1: what the orbit actually does

`code/e1_orbital_reality.py` propagates a seeded sample of public Starlink TLEs with SGP4 and
measures, per pass, the quantities that NTN-specific evaluation would have to instantiate.

⚠ **It computes free-space path loss only.** Antenna pattern roll-off, atmospheric and rain
attenuation and receiver noise all *add* variation over a pass rather than removing it, so the
FSPL swing reported here is a **lower bound** on how much the link budget moves. A lower bound
needs no contested modelling, and the argument only requires a lower bound.

Reproduce:

```bash
curl -s "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle" -o data/starlink.tle
python3 code/e1_orbital_reality.py          # NTN_NSAT=1200 by default
```

Two properties of the E1 output are worth stating because they constrain how the numbers may be
used. Medians agree to within 0.6 % between a 150-satellite pilot and the 1200-satellite run,
and to 0.0 % for Doppler, so the figures are not artefacts of sample size. And they are nearly
identical across four ground stations spanning 0 to 65 degrees latitude, so they are properties
of the orbital shell rather than of a chosen site.

## Reproducibility

Every experiment writes JSON to `results/` using an absolute path, so running a script from
another working directory cannot overwrite a previous run's data. Sample sizes and seeds are
declared in the source rather than passed silently.
