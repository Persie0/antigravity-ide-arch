# Antigravity IDE for Arch Linux / CachyOS

Unofficial, community-maintained **`antigravity-ide-bin`** package of the **standalone Antigravity IDE**. This is **not** the separately branded Antigravity 2.0 application or the Antigravity CLI.

The package uses Google's official Linux x86-64 tarball and does **not** redistribute the proprietary application. CachyOS is Arch-based and uses the same `pacman`/`makepkg` package format.

## Install

Once this package has been published to the AUR:

```sh
yay -S antigravity-ide-bin
# or: paru -S antigravity-ide-bin
```

Until the first AUR publication, install directly from this repository:

```sh
sudo pacman -S --needed base-devel git
git clone https://github.com/Persie0/antigravity-ide-arch.git
cd antigravity-ide-arch
makepkg -si
```

Launch with `antigravity-ide` or the **Antigravity IDE** desktop entry. If your browser cannot return the OAuth redirect to the IDE, register the URL handler:

```sh
xdg-mime default antigravity-ide-url-handler.desktop x-scheme-handler/antigravity
```

## Automatic updates / publishing

The scheduled workflow lives in **[Persie0/Playground](https://github.com/Persie0/Playground/blob/main/.github/workflows/antigravity-ide-aur.yml)** to avoid consuming private-repository GitHub Actions minutes.

Every day it:

1. Checks the **Antigravity IDE (Standalone)** Linux x64 link on [Google's official download page](https://antigravity.google/download).
2. Checks the product version **and build ID**, without mistaking Antigravity 2.0 releases for IDE releases.
3. Downloads the official tarball only when the version/build changes, computes SHA-256, and updates `PKGBUILD`.
4. Regenerates `.SRCINFO` using Arch's `makepkg --printsrcinfo`, and validates a real package build in an Arch Linux container.
5. Commits any updated package metadata to this repository using the Playground secret `PRIVATE_REPO_TOKEN || GH_TOKEN || GH_RELEASE_TOKEN`.
6. Publishes the package files to the AUR **if** the Playground secret `AUR_SSH_PRIVATE_KEY` has been configured.

It can also be triggered manually from the Playground Actions tab, including before a release. An upstream download or packaging failure stops publication rather than releasing an unverified package.

### One-time AUR setup (required for publishing)

1. Create/login to an account at https://aur.archlinux.org/register (or https://aur.archlinux.org/).
2. Choose a unique AUR package name: this repository defaults to **`antigravity-ide-bin`**. Confirm it is not owned by someone else before first publication.
3. Generate a dedicated unencrypted automation key: `ssh-keygen -t ed25519 -N '' -f ~/.ssh/aur-antigravity -C 'antigravity-aur-publisher'`.
4. Add **`~/.ssh/aur-antigravity.pub`** to your AUR account's SSH Public Key field.
5. Add the **private** key's full contents to **Playground → Settings → Secrets and variables → Actions → New repository secret** named `AUR_SSH_PRIVATE_KEY`. Never commit it.
6. Ensure one of `PRIVATE_REPO_TOKEN`, `GH_TOKEN`, or `GH_RELEASE_TOKEN` in Playground can write **Contents** in **Persie0/antigravity-ide-arch**.
7. In Playground, run **Actions → Antigravity IDE AUR sync → Run workflow**. The AUR server accepts pushes only for package names available to your AUR account.

For strict AUR host verification the workflow also expects the secret `AUR_KNOWN_HOSTS`, containing the **verified** `aur.archlinux.org` SSH known-hosts entry. Determine and verify the fingerprint independently before saving the entry. The workflow deliberately never uses `StrictHostKeyChecking=no`.

An AUR package is a build recipe and metadata in the AUR Git repository, not a binary package hosted by AUR. The completed, locally built `*.pkg.tar.zst` is installed by `pacman`.

## Files

- `PKGBUILD`: binary packaging recipe for x86_64
- `.SRCINFO`: AUR metadata
- `antigravity-ide.desktop`, `antigravity-ide-url-handler.desktop`: launcher and OAuth deep-link handler
- `scripts/update_package.py`: official release detection and checksum refresh
- `tests/test_update_package.py`: updater regression tests

## Unofficial notice

Antigravity IDE is proprietary software from Google. This is an unofficial packaging project, not an endorsement by Google. The software's own terms apply.
