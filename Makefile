.PHONY: install build clean test package

install:
	pip install .

build:
	python -m build

clean:
	rm -rf build/ dist/ *.egg-info/ src/kira-repo/ pkg/ src/*.pkg.tar.*
	find . -type d -name "__pycache__" -exec rm -rf {} +

package:
	makepkg -f

package-install:
	makepkg -si
