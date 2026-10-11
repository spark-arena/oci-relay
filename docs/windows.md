<!--
SPDX-FileCopyrightText: 2026 Spark Arena
SPDX-License-Identifier: Apache-2.0
-->

# Windows (experimental)

OCI Relay v0.1.4 adds experimental Windows x64 and ARM64 release bundles.
Native CI validates the executable and portable APIs; real Docker Desktop and
WSLC end-to-end qualification remains pending. Use the matching v0.1.4 plugin.
See [platform support](platforms.md) for the tested scope and remaining work.

## Standalone receiver

Create the session on the source, then copy that receiver's credential JSON over
an authenticated management channel into a private directory on Windows. Use
`oci-relay.exe private-directory --path C:\relay-operation` before placing
credentials there. Never copy the full session or another peer's key to a receiver.

Docker Desktop, using its selected context or default named pipe:

```powershell
oci-relay.exe peer --endpoint https://SOURCE:PORT `
  --session C:\relay-operation\peer.json --tag example/image:tag `
  --skip-present --import archive --max-import-bytes 68719476736
```

WSLC, with an explicit session and scratch parent:

```powershell
oci-relay.exe peer --endpoint https://SOURCE:PORT `
  --session C:\relay-operation\peer.json --tag example/image:tag `
  --runtime wslc --wslc-session sparkrun --skip-present `
  --import archive --max-import-bytes 68719476736 `
  --import-spool-dir D:\relay-scratch
```

The example cap is 64 GiB. It limits the archive; leave additional disk space for
Docker/WSLC extraction. WSLC adds a relay staging file, while Docker uses a
streaming API request. Transfers retain mutual TLS, SHA-256 verification,
backpressure and striping. The Windows archive path currently sends all layers
when import is needed; exact warm-image skips are supported.

For an already configured TCP daemon, append `--docker-host tcp://HOST:2376
--docker-tls --docker-ca C:\certs\ca.pem --docker-cert C:\certs\cert.pem
--docker-key C:\certs\key.pem`. Do not enable an unauthenticated daemon listener
as part of installation. A loopback TCP endpoint can also represent a separately
managed secure tunnel.

## Native Windows control node with Linux receivers

Use Sparkrun 0.4.0+ with the bundled OCI Relay v0.1.4 adapter. Contributors can
instead install matching Sparkrun and OCI Relay checkouts editably.

Configure Sparkrun as shown below. Ordinary
delegated Linux distribution downloads Linux binaries on the controller and
stages them over SSH; it needs no Windows relay binary.

For a Windows-local image source, the plugin downloads and verifies the matching
Windows and Linux release bundles and stages Linux binaries over SSH. Configure
the controller's Docker Desktop context if needed:

```yaml
container_distribution_provider: oci-relay
container_distribution_fallback: false  # Surface experimental-runtime failures.
plugins:
  oci-relay:
    runtime_connections:
      controller:
        docker_context: desktop-linux
    max_spool_bytes: 68719476736
    source_mode: auto
    allow_preparation_read: true
```

Executable architecture and image platform are separate: Linux ARM64 receivers
still receive Linux ARM64 images, even from an x64 Windows controller.
The context name must exist locally (`docker context ls`); omit
`runtime_connections.controller` to use the controller's normal Docker default.
The plugin chooses bounded `docker-save` for a VM source and preserves native
store reuse on qualified Linux receivers.

Replace the controller connection with this to select WSLC for a local source:

```yaml
runtime_connections:
  controller:
    runtime: wslc
    wslc_session: sparkrun
```

Runtime connection keys can also be Linux SSH hostnames/IPs for a nondefault
daemon there. Certificate and context paths belong to the host running the
relay. Such remote/VM receiver daemons automatically use archive import, with
`max_import_bytes` defaulting to 64 GiB unless explicitly configured.

Windows-local source operation directories use Windows ACLs. Linux remote paths
remain POSIX paths even when the controller runs Windows. For SSH stdio fallback,
the Windows source attachment uses loopback TCP carrying the same end-to-end TLS
stream; it does not use a Windows Unix socket. Direct HTTP/2 and SSH forwarding
are also available.

Windows release bundles use `.tar.gz` and contain `oci-relay.exe` and license
notices. They do not include or require `unpigz`. Release archive checksums are
pinned by the plugin. Standalone users can extract a bundle with Windows `tar`.
