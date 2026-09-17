# R007 reserved simulated validation

**FAIL.** This is a SIMULATED reserved holdout result, not physical validation.

## Primary gate

- Total eligible: **7/12**.
- Total eligible and within 5%: **3/12**.
- Partial or ineligible: **5/12**.
- All 12 total eligible and each absolute relative total-volume error <=5%: **FAIL**.

Any partial result fails. Spatial error and cancellation are reported but do not alter the gate.

## Per scene

| scene | support | total error | spatial error | cancellation | pass |
|---|---:|---:|---:|---:|---:|
| r007_pyramid_low_left | 400/400 | 2.169% | 3.648% | 1.68x | PASS |
| r007_pyramid_high_right | 400/400 | 0.568% | 3.190% | 5.61x | PASS |
| r007_pyramid_mid_right_beam | 400/400 | 8.616% | 12.735% | 1.48x | FAIL |
| r007_pyramid_high_left_dropout35 | 385/400 | -- | 8.287% | 11.05x | FAIL |
| r007_two_stacks_low | 400/400 | 0.881% | 9.493% | 10.78x | PASS |
| r007_two_stacks_high_beam | 400/400 | 6.834% | 15.424% | 2.26x | FAIL |
| r007_prism_low_left | 400/400 | 10.105% | 20.307% | 2.01x | FAIL |
| r007_prism_high_right_beam_dropout10 | 339/400 | -- | 18.267% | 2.90x | FAIL |
| r007_ramp_low_left_beam | 400/400 | 41.770% | 43.496% | 1.04x | FAIL |
| r007_ramp_high_right_dropout25 | 344/400 | -- | 7.307% | 4.60x | FAIL |
| r007_layer_low_dropout10 | 324/400 | -- | 0.421% | 31.06x | FAIL |
| r007_layer_high_beam_dropout30 | 320/400 | -- | 0.195% | 1.90x | FAIL |

The scene table, candidate, estimator, runners, evaluator, tests, simulator, and gate were frozen before capture.
