.PHONY: clean

coverage:
	@nosetests -vs --with-coverage \
	               --cover-package=reader \

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

majin-tensei-ii.ips:
	python majin-tensei-ii/majin-tensei-ii.py

patch: majin-tensei-ii.s(mc|fc) majin-tensei-ii/majin-tensei-ii.ips
