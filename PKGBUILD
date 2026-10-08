# Maintainer: Persie0 <76871553+Persie0@users.noreply.github.com>
# Unofficial repackaging of Google's standalone Antigravity IDE for Arch/CachyOS.
pkgname=antigravity-ide-bin
pkgver=2.5.5
_buildid=4923483625488384
pkgrel=1
pkgdesc='Google Antigravity IDE (standalone) - official prebuilt Linux release'
arch=('x86_64')
url='https://antigravity.google/download'
license=('LicenseRef-proprietary')
depends=('alsa-lib' 'at-spi2-core' 'dbus' 'glibc' 'gtk3' 'libdrm' 'libnotify' 'libsecret' 'libxkbfile' 'libxss' 'mesa' 'nspr' 'nss' 'xdg-utils')
optdepends=('gnome-keyring: secure credential storage on GNOME'
            'kwallet: secure credential storage on KDE Plasma')
provides=('antigravity-ide')
conflicts=('antigravity-ide' 'google-antigravity-bin')
options=('!strip' '!debug')
source=("antigravity-ide-${pkgver}-${_buildid}-linux-x64.tar.gz::https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/${pkgver}-${_buildid}/linux-x64/Antigravity%20IDE.tar.gz"
        'antigravity-ide.desktop'
        'antigravity-ide-url-handler.desktop')
sha256sums=('0c5233b297d2b3aebb61af49f8944012c2953d361a5ebb16978490636917f831'
            'SKIP'
            'SKIP')

package() {
    local upstream="${srcdir}/Antigravity IDE"
    if [[ ! -f "${upstream}/bin/antigravity-ide" ]]; then
        printf 'Missing upstream launcher: %s\n' "${upstream}/bin/antigravity-ide" >&2
        return 1
    fi

    install -dm755 "${pkgdir}/opt/antigravity-ide" "${pkgdir}/usr/bin"
    cp -a -- "${upstream}/." "${pkgdir}/opt/antigravity-ide/"

    ln -s /opt/antigravity-ide/bin/antigravity-ide "${pkgdir}/usr/bin/antigravity-ide"

    # Chrome's sandbox helper must be root-owned and setuid for the SUID fallback.
    if [[ -f "${pkgdir}/opt/antigravity-ide/chrome-sandbox" ]]; then
        chmod 4755 "${pkgdir}/opt/antigravity-ide/chrome-sandbox"
    fi

    install -Dm644 "${srcdir}/antigravity-ide.desktop" \
        "${pkgdir}/usr/share/applications/antigravity-ide.desktop"
    install -Dm644 "${srcdir}/antigravity-ide-url-handler.desktop" \
        "${pkgdir}/usr/share/applications/antigravity-ide-url-handler.desktop"

    # Use the icon shipped by Google, never download an unverified third-party icon.
    local icon
    for icon in \
        "${upstream}/resources/app/resources/linux/code.png" \
        "${upstream}/resources/app/resources/linux/antigravity.png" \
        "${upstream}/resources/app/resources/linux/icon.png"; do
        if [[ -f "${icon}" ]]; then
            install -Dm644 "${icon}" "${pkgdir}/usr/share/pixmaps/antigravity-ide.png"
            return 0
        fi
    done
    printf 'Could not locate a supported upstream application icon\n' >&2
    return 1
}
