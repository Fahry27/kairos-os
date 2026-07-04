# Release Process

To maintain system stability while rapidly iterating on autonomous capabilities, Kairos DOS adheres to a strict release pipeline.

## 1. Sprints
Work is organized into highly focused Sprints. A Sprint is bounded by a specific architectural or product goal (e.g., "Sprint 3: Provider Platform"). Code is merged into the `main` branch continuously via Pull Requests during a Sprint.

## 2. Release Candidates (RC)
Once a Sprint is feature-complete, a Release Candidate tag is cut (e.g., `v3.4.0-rc1`). 
RCs are deployed to staging environments and internal edge nodes for integration testing. 

## 3. Validation Phase
During validation, the RC is subjected to synthetic `Missions` designed to stress-test the `Approval Bridge` and `Provider Router` fallback logic. No RC graduates to General Availability (GA) if a synthetic test successfully bypasses an Approval block.

## 4. General Availability (GA)
Upon passing validation, the RC tag is promoted to a standard semver tag (e.g., `v3.4.0`). 
GA releases are published to Docker Hub and official package managers, accompanied by an updated Product Book and Changelog.
