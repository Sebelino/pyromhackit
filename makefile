.PHONY: clean

coverage:
	rm -f .coverage  # May be needed; seen some strange behavior
	pytest \
		--verbose\
		--capture=no\
		--cov=pyromhackit\
		--cov-report=term\
		--cov-report=html\
		pyromhackit

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	virtualenv --no-site-packages venv
	source venv/bin/activate && \
	pip install -Ur requirements.txt;

# Beware of circular dependency black magic:
#requirements.txt: venv
#	source venv/bin/activate && \
#	pip freeze > requirements.txt;

clean:
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf .ropeproject
	find . -name .coverage | xargs rm -f
	rm -f coverage.xml
	rm -f .coverage.xml
	rm -rf htmlcov
	rm -f .syspath.txt
	rm -f .coverage.syspath.txt

majin-tensei-ii.ips:
	python majin-tensei-ii/majin-tensei-ii.py

patch: majin-tensei-ii.s(mc|fc) majin-tensei-ii/majin-tensei-ii.ips
