<!--
SPDX-FileCopyrightText: 2026 Spark Arena
SPDX-License-Identifier: Apache-2.0
-->

# OCI Relay

OCI Relay distributes container images from a local Docker store or remote OCI
registry to multiple Docker hosts. The Go relay handles verified transfers;
the Sparkrun plugin coordinates hosts, selects sources and transports, tunes
resource limits, and reports progress.

- Stream registry pulls directly to receivers without importing on the source.
- Reuse existing layers across classic overlay2 and containerd image stores.
- Transfer over authenticated HTTP/2, directly or through SSH forwarding/stdio.
- Use multiple TCP data paths with bounded memory and concurrency.

Native access supports qualified rootful Linux Docker 29+ stores. Real-engine
qualification currently covers Linux arm64. Linux amd64, Linux arm64 and macOS
arm64 bundles are built and tested on native runners. Windows x64/ARM64 bundles
are experimental, with native CI coverage; Docker Desktop and WSLC runtime
qualification remains pending. See [platform support](docs/platforms.md), [storage compatibility](docs/storage-compatibility.md) and
[validation](docs/validation.md). Published binaries are available from [GitHub releases](https://github.com/spark-arena/oci-relay/releases).

## Sparkrun integration

Sparkrun 0.4.0+ includes OCI Relay and enables it by default on every channel.
Run your recipes normally; Sparkrun handles relay binary setup, image distribution,
and progress reporting. See [plugin configuration](docs/sparkrun-plugin.md) for
optional tuning and opt-out settings.

## Development quick start

For contributors working on the relay or plugin, run from this checkout:

```bash
source dev.sh
sparkrun run YOUR_RECIPE
deactivate
```

This builds the relay and native decoder and installs OCI Relay and Sparkrun
editably, selecting the development adapter in a private configuration. See
[development setup](docs/development.md) for prerequisites and checkout paths.

To build the standalone executable:

```sh
CGO_ENABLED=0 go build -trimpath -o bin/oci-relay ./cmd/oci-relay
```

## Documentation

- [Sparkrun plugin](docs/sparkrun-plugin.md): configuration, transports, multiple
  links, adaptive limits, progress, and optional tuning.
- [Source modes and manifests](docs/source-modes.md) and
  [automatic selection](docs/source-selection.md).
- [Registry sources](docs/registry-source.md): authentication, caching, and limits.
- [Bundled receiver decoding](docs/bundled-decoder.md): helper installation, disk budgets, and fallback.
- [Storage compatibility](docs/storage-compatibility.md): native access, layer
  discovery, mixed stores, and hash identities.
- [Windows and runtime connections](docs/platforms.md): experimental support, Desktop/WSLC paths, and qualification limits.
- [Standalone commands](docs/standalone.md): sessions, events, and transfer-only validation.
- [Development](docs/development.md): tests, CI, versions, and vendoring;
  [release procedure](docs/releasing.md).
- [Validation and limitations](docs/validation.md).

## License and contributions

Copyright 2026 Spark Arena. OCI Relay and its Sparkrun plugin are licensed
under [Apache-2.0](LICENSE).

See [third-party notices](THIRD_PARTY_NOTICES.md) and
[dependency licenses](THIRD_PARTY_LICENSES.txt). See
[CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Sparkrun feedback

On hosts exposing `sparkrun.plugins.FEEDBACK_API_VERSION = 1`, the adapter
publishes structured receiver stages, byte counters, rates, extraction/cache
metrics, heartbeats, and verified outcomes. CLI messages remain available;
library subscribers use `sctx.events`, and daemon consumers follow the job's
`/v1/jobs/{job_id}/events` stream. Transfer totals use `upper_bound` semantics and
must not be treated as exact completion percentages. Older hosts retain text
logging. The Sparkrun [feedback guide](https://github.com/spark-arena/sparkrun/blob/main/docs/FEEDBACK.md)
describes the public contract.

## Diagnostic bundles

When Sparkrun diagnostic capture is enabled, the plugin contributes source and transport decisions, failure tails before receiver cleanup, and transfer/cleanup outcomes. Snapshots select bounded state already available during the operation; they do not add remote probes or per-chunk reporting.

Use `sparkrun.api.capture_diagnostics(...)` around library operations, or `collect_diagnostics: true` on supported daemon jobs. The host owns redaction, bundle limits, access, and retention. Existing structured feedback continues to provide live progress. With capture disabled, snapshot builders do not run. Hosts without the optional diagnostics API retain normal plugin behavior. See the [Sparkrun diagnostics API](https://github.com/spark-arena/sparkrun/blob/main/docs/DIAGNOSTICS_API.md) for the capture interface.
