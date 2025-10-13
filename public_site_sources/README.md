# History of Metrics

History of metrics is published on [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) by [GitHub Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

General publishing flow:
1. Metrics are stored in file `metrics.json` automatically on every pipeline evaluation
1. On every push GitHub action job is launched
   1. History of every metric in `metrics.json` is collected by `public_site_sources/get_metric_history.sh` script and saved to a local `metrics.csv` file
   1. Plot with metric history is created by `public_site_sources/image_generator.py` script from `metrics.csv` and saved to `metrics_history.png`
   1. `metrics_history.png` is used from `index.html` to show static content

