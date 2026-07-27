.PHONY: bootstrap test evidence verify

bootstrap:
	bash scripts/bootstrap.sh

test:
	forge test -vv

evidence:
	python3 scripts/verify_evidence.py

verify:
	python3 scripts/verify_evidence.py
	forge test -vv
	git diff --exit-code
