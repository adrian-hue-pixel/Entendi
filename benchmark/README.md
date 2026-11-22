# Reproduce the Entendi evaluation

Start in the repository root. Install `requirements.txt` in a virtual environment.

```sh
python -m benchmark.generate
python -m benchmark.evaluate --out /tmp/entendi-rules.json
diff -u benchmark/results.rules.json /tmp/entendi-rules.json
python -m unittest discover -s tests -v
```

The committed baseline uses **only source text plus gold evidence spans**. It does not call a provider. It scores exact dates and decimal/currency pairs, ambiguous-date flags and adversarial changes to a proposed value. A missing value is correct only where the gold label is also null. Cases without a usable model response count as errors in image mode.

## Optional image evaluation

Install Noto Sans CJK (SC/JP/KR) and Noto Sans Thai to render the intended glyphs. On Debian/Ubuntu, Noto families are available through `fonts-noto-cjk` and `fonts-noto-core`. Point `--fonts` at their directory if the defaults do not apply.

```sh
python -m benchmark.render --out /tmp/entendi-images --fonts /usr/share/fonts
# Configure LETTER_API_URL, LETTER_API_MODEL, and LETTER_API_KEY if required.
python -m benchmark.evaluate --images /tmp/entendi-images --out /tmp/entendi-vision.json
```

The second command sends the fictional images to your chosen provider and may consume quota. Include the provider, exact model, run date and any rendering changes when publishing numbers. You can render the unscored Thai fixtures with `--language th`; they are not included in the first scored pass. No image/OCR or provider-backed translation results are claimed in this release.

See [dataset fields and license](data/README.md) and [the write-up](../docs/trust-benchmark.md).
