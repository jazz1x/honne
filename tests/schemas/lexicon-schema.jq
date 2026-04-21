# Validates extract-lexicon.sh output structure
# Output should be an array of lexicon terms

(type == "array") and
(
  map(
    (type == "object") and
    (.term | type == "string") and
    (.count | type == "number" and . >= 0)
  ) | all
) and
(
  # Optional: check ordering (descending by count)
  (map(.count) as $counts |
   ($counts == ($counts | sort | reverse)) or ($counts | length <= 1))
)
