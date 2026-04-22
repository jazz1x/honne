#!/usr/bin/env bash
# tests/snapshot_shim_compat.sh — T14: shim stdout/stderr snapshot comparison (Appendix C.4)
set -e
fail=0
for sh in scan-transcripts evidence-gather extract-lexicon \
          detect-recurrence query-assets record-claim \
          index-session purge; do
  bash "scripts/${sh}.sh" 2>/tmp/s.err >/tmp/s.out || true
  for stream in stdout stderr; do
    base="tests/fixtures/baseline_shim_stdout/${sh}.${stream}.txt"
    if [ "$stream" = "stdout" ]; then new=/tmp/s.out; else new=/tmp/s.err; fi
    if ! diff -q "$base" "$new" >/dev/null 2>&1; then
      echo "DIFF $sh $stream"; fail=1
    fi
  done
done
exit $fail
