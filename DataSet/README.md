# Fruit dataset with big-cat prose edits

50 ASCII .txt files, with ten fruit names and versions _v1 through _v5.
Each file is exactly 10,000,000 bytes (decimal 10 MB); total text size is 500 MB.

The _v1 fruit-prose originals are unchanged. All subsequent versions have
been rebuilt from those originals, replacing the previous character-noise edits.
Each transition deletes 1,000 randomly chosen 1,000-byte paragraphs and adds
1,000 readable paragraphs about lions, leopards, tigers, jaguars, and cheetahs.
Each insertion batch has 200 paragraphs per species, shuffled into random order.
The new prose uses a separate wildlife vocabulary and paragraph structure,
not the fruit scenes. Paragraph variants and sentence patterns recur; this
is synthetic test prose, not a corpus of independently authored articles.

Each paragraph is 1,000 bytes, including LF line breaks, trailing space
padding, and a final blank line. Complete words and sentences are preserved.
Paragraphs are independent discussions, not chapters in a continuous story.
The added text discusses appearance, behavior, comparisons, and observation.

Deletion indices are sampled uniformly without replacement. Insertion
boundaries are sampled independently with replacement. Exactly 1 MB is
removed, 1 MB added, and 9 MB preserved byte-for-byte from the immediate
predecessor. Later deletions may remove either fruit or big-cat prose.
Survivors retain relative order but may shift position. A conventional diff
may count 2 MB of activity. The retention guarantee is not cumulative from v1.

manifest.json provides SHA-256 hashes and exact edit coordinates. Block
indices start at zero; insertion boundary i is before predecessor block i,
and boundary 10000 is after the last block. Edit positions use operating-system
randomness; prose choices use seed 20261007.

General background references (the prose is newly composed, not copied):
- https://animals.sandiegozoo.org/animals/lion
- https://animals.sandiegozoo.org/animals/leopard
- https://animals.sandiegozoo.org/animals/jaguar
- https://animals.sandiegozoo.org/animals/cheetah
- https://en.wikipedia.org/wiki/Big_cat
