.PHONY: build test typecheck package clean

build:
	poetry install

test:
	python -c "import aw_watcher_screenshot"
	python -m pytest tests -v

typecheck:
	python -m mypy aw_watcher_screenshot --ignore-missing-imports

package:
	pyinstaller aw-watcher-screenshot.spec --clean --noconfirm

clean:
	rm -rf build dist
	rm -rf aw_watcher_screenshot/__pycache__
