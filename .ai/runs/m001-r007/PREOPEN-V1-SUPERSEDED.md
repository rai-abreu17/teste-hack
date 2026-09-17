# Pre-Open Manifest v1 (SUPERSEDED)

The original pre-open manifest (hash `95e34ff6fb3f96fcbd2cc08182747d7c6db984854b732fb455c11bcbb7cbfe34`) was superseded and replaced with a v2 protocol and manifest.

## Reason for revocation
A vulnerability in the provenance chain was found during the initial pre-open review. The original architecture allowed a captured frame to be swapped post-capture with another frame of the same sequence (and same parameters but a different scene) without invalidating the manifest. 

To resolve this issue, the protocol was upgraded to V2, introducing `capture-plan-v2.json`, structural validation, and strict tampering checks in `validate_acquisition`.

## Preservation
To preserve the audit trail, the exact binary representation of the original V1 manifest has been preserved as `pre-open-manifest-v1.json`.
