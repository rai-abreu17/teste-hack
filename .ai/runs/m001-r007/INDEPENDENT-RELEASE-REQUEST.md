# Independent release requested — R007 pre-open

Please review the frozen R007 preregistration and recalculate every SHA-256 entry in `pre-open-manifest.json` before authorizing any simulator invocation.

The review should confirm:

- exactly 12 fixed, nonempty scenes and no post-open selection/removal;
- all five supported shapes, low/high fills, shifted pyramids, beam-obstacle stress, and dropout stress;
- exactly the D004 candidate poses and unchanged D003 estimator;
- exactly 60 newly generated frames, five per scene, sequences 701–705, with no development-frame reuse;
- the 12/12 primary gate and automatic failure for any partial result;
- spatial error and cancellation are reported without changing the primary gate;
- acquisition code cannot import the estimator or truth;
- scoring completes every truth-free reconstruction before evaluator-only truth import;
- hashes cover the protocol, estimator, both runners, evaluator, tests, simulator source/binary, runtime geometry, requirements, and preregistration material;
- no R007 frames, commands, acquisition manifests, validations, reports, or results exist.

If and only if every check passes, create `independent-pre-open-release.json` using the schema in `README.md` and bind it to the exact SHA-256 of `pre-open-manifest.json`. No release is present now, so capture remains blocked.
