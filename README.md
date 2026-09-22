# Kairos Labs

**Open and reproducible experiments in economics, public policy, decision science, and applied research.**

Kairos Labs is the research repository of **Kairos**, an independent project that explores economic, social, and decision-making problems through data, computational experiments, simulation, and reproducible analysis.

This repository contains selected research projects whose code, methodology, and results are suitable for public reproduction.

## Research

Research projects will be added progressively as they are reviewed and prepared for reproducibility.

Planned initial releases include:

- **Optimization Lab #1** — Targeting social transfers across 100,000 synthetic households.
- **Corruption Lab** — Strategic incentives, enforcement, and public value in a synthetic public procurement market.
- **Guatemala Growth & CO₂** — Economic growth, emissions, renewable energy, and carbon intensity in Guatemala.

## Reproducibility standard

Each published Lab should document:

1. Research question
2. Motivation
3. Methodology
4. Data and sources
5. Experimental structure
6. Main results
7. Reproduction instructions
8. Limitations
9. Related Kairos publication

Where stochastic processes are used, random seeds and relevant computational assumptions should also be documented.

## Repository structure

```text
kairos-labs/
├── README.md
├── LICENSE
├── .gitignore
├── optimization-lab-01/
├── corruption-lab/
└── guatemala-growth-co2/