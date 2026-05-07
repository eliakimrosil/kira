# Maintainer: Master Kim <eliakimrosilarts@gmail.com>
pkgname=kira
_pkgname=kira
pkgver=0.1.0.r23.g647ac75
pkgrel=1
pkgdesc="kira: a specialized expert in Arch Linux and Hyprland"
arch=('any')
url="https://github.com/eliakimrosil/Kira"
license=('MIT')
depends=('python' 'python-pyaudio' 'python-dotenv' 'python-rich')
optdepends=('grim: for screenshot support'
            'slurp: for region selection in screenshots'
            'hyprland: for window management integration'
            'mpv: for music playback'
            'bluez-utils: for bluetooth management')
makedepends=('git' 'python-build' 'python-installer' 'python-setuptools' 'python-wheel')
source=("$_pkgname-git::git+$url.git")
md5sums=('SKIP')

pkgver() {
  cd "$_pkgname-git"
  ( set -o pipefail
    git describe --long --tags 2>/dev/null | sed 's/\([^-]*-g\)/r\1/;s/-/./g' ||
    printf "0.1.0.r%s.g%s" "$(git rev-list --count HEAD)" "$(git rev-parse --short HEAD)"
  )
}

build() {
  cd "$_pkgname-git"
  python -m build --wheel --no-isolation
}

package() {
  cd "$_pkgname-git"
  python -m installer --destdir="$pkgdir" dist/*.whl

  # Install the .env.example as a reference
  install -Dm644 .env.example "$pkgdir/usr/share/$_pkgname/.env.example"

  # Install the License
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
