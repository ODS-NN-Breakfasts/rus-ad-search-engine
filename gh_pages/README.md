# History of Metrics

History of metrics is published on [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site) by [GitHub Actions](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).

General publishing flow:
1. Metrics are stored in file `metrics.json` automatically on every pipeline evaluation
1. On every push (or pull request) on "main" branch GitHub action job is launched (see all actions in `.github/workflows/deploy_gh_pages.yaml`)
   1. History of every metric in `metrics.json` is collected by `gh_pages/get_metric_history.sh` script and saved to `gh_pages/metrics.csv` file
   1. Plot with metric history is created by `gh_pages/image_generator.py` script from `gh_pages/metrics.csv` and saved to `gh_pages/metrics_history.png`
   1. `gh_pages/metrics_history.png` is used from `gh_pages/index.html` to show static content
   1. Content is uploaded to [the page of this repo](https://ods-nn-breakfasts.github.io/rus-ad-search-engine/)

