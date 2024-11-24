# Release process

Barring extenuating circumstances, all work is done in branches.
PRs are merged into `master` when they are ready to be released.
As PRs merge, draft release notes are updated.

When a release is ready to be published, the following steps are taken:

- Manually assign a new tag to the draft release.
- Un-draft the release.

When a release is published, more automation will bundle the release and publish it to PyPI.
