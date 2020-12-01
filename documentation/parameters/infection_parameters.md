# Table: Infection parameters
| Name | Value | Symbol | Description | Source | 
|  ---- | ---- | ---- | ---- | ---- |
| `n_seed_infection` | 5 | - | Number of infections seeded at simulation start | - |
| `mean_infectious_period` | 5.5 | &#956; | Mean of the generation time distribution (days) | Ferretti et al in prep 2020; Ferretti & Wymant et al 2020; Xia et al 2020; He et al 2020; Cheng et al 2020 |
| `sd_infectious_period` | 2.14 | &#963; | Standard deviation (days) of infectious period | Ferretti et al in prep 2020; Ferretti & Wymant et al 2020; Xia et al 2020; He et al 2020; Cheng et al 2020 |
| `infectious_rate` | 5.18 | *R* | Mean number of individuals infected by each infectious individual with moderate to severe symptoms | Derived from calibration |
| `asymptomatic_infectious_factor` | 0.33 | *A<sub>asym</sub>* | Infectious rate of asymptomatic individuals relative to symptomatic individuals | Personal communication, Sun |
| `mild_infectious_factor` | 0.72 | *A<sub>mild</sub>* | Infectious rate of mildly symptomatic individuals relative to symptomatic individuals | Personal communction, Sun |
| `relative_susceptibility_0_9` | 0.35 | *S<sub>0-9</sub>* | Relative susceptibility to infection, aged 0-9 | Zhang et al. 2020 |
| `relative_susceptibility_10_19` | 0.69 | *S<sub>10-19</sub>* | Relative susceptibility to infection, aged 10-19 | Zhang et al. 2020 |
| `relative_susceptibility_20_29` | 1.03 | *S<sub>20-29</sub>* | Relative susceptibility to infection, aged 20-29 | Zhang et al. 2020 |
| `relative_susceptibility_30_39` | 1.03 | *S<sub>30-39</sub>* | Relative susceptibility to infection, aged 30-39 | Zhang et al. 2020 |
| `relative_susceptibility_40_49` | 1.03 | *S<sub>40-49</sub>* | Relative susceptibility to infection, aged 40-49 | Zhang et al. 2020 |
| `relative_susceptibility_50_59` | 1.03 | *S<sub>50-59</sub>* | Relative susceptibility to infection, aged 50-59 | Zhang et al. 2020 |
| `relative_susceptibility_60_69` | 1.27 | *S<sub>60-69</sub>* | Relative susceptibility to infection, aged 60-69 | Zhang et al. 2020 |
| `relative_susceptibility_70_79` | 1.52 | *S<sub>70-79</sub>* | Relative susceptibility to infection, aged 70-79 | Zhang et al. 2020 |
| `relative_susceptibility_80` | 1.52 | *S<sub>80</sub>* | Relative susceptibility to infection, aged 80+ | Zhang et al. 2020 |
| `relative_transmission_household` | 2 | *B<sub>home</sub>* | Relative infectious rate of household interaction | - |
| `relative_transmission_occupation` | 1 | *B<sub>occupation</sub>* | Relative infectious rate of workplace interaction | - |
| `relative_transmission_random` | 1 | *B<sub>random</sub>* | Relative infectious rate of random interaction | - |
| `exposure_model_use` | 0 | - | Use the exposure model of including duration and distance of interaction | - |
| `exposure_model_distance_mean` | 1.0 | - | Mean distance of interaction in the exposure model (Gamma distributed) | - |
| `exposure_model_distance_sd` | 0.5 | - | Standard deviation of distance of interation in the exposure model (Gamma distributed) | - |
| `exposure_model_duration_min` | 1.0 | - | Minimum duration of an interaction in the exposure model (Pareto distributed) | - |
| `exposure_model_duration_mean` | 5.0 | - | Mean duration of an interaction in the exposure model (Pareto distributed) | - |
| `exposure_model_risk_distance_half` | 2.0 | - | Distance at which the risk of transimission is has a half of the maximum in the exposure model (logistic function) | - |
| `exposure_model_risk_distance_width` | 0.5 | - | Width of logisitc function in the risk of transimission in the exposure model (logistic function) | - |