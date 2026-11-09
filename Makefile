.PHONY: check package
check:
	python3 -m unittest discover -s tests -v
	python3 scripts/package_skill.py
package:
	python3 scripts/package_skill.py
