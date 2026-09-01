# Seed Data Notes

CSVs produced by `python src/data_generation/generate_sample_data.py`
with a fixed seed. Volumes: 10,000 customers, 100,000 orders, 500
products, 700 injected defect rows (460 exercise-required + 240
supplemental — see `data-quality-strategy.md`).

Uploaded to a Unity Catalog volume before Bronze reads them (`README.md`
section 3).
~~~~