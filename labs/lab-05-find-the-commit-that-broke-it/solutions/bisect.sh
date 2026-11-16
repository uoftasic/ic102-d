#!/bin/bash
# A bisect script for Lab 05's history. git bisect run runs it from the top of the repository.
#   exit 0     the test ran and passed       (good)
#   exit 1     the test ran and failed       (bad)
#   exit 125   the test couldn't run at all  (skip: neither good nor bad)
TT=/foss/designs/modules/ic102-d/labs/common/tt-tools

rm -f test/results.xml
"$TT/run-test.sh" . > /tmp/bisect-$(git rev-parse --short HEAD).log 2>&1

if [ ! -f test/results.xml ]; then
    exit 125        # it didn't compile, so the test never ran
fi
if grep -q "<failure" test/results.xml; then
    exit 1          # a test ran and failed
fi
exit 0
