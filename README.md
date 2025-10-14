# Search Engine for Russian Advertisements

All design-related information is in [System Design Document](research/DESIGN.md).

History of main search metrics is shown on the [repo GitHub page](https://ods-nn-breakfasts.github.io/rus-ad-search-engine/).

All operations for project development and maintenance are described on [Wiki page](https://github.com/ODS-NN-Breakfasts/rus-ad-search-engine/wiki).

## Directory and File Structure

```text
.
├── .dvc/ - settings for DVC tool
├── .github/workflows/ - GitHub Actions script to generate report on GitHub Pages
├── dataset_tools/ - tools to work with dataset
├── gh_pages/ - source files for the report on GitHub Pages
├── research/ - place for research-related code and docs
│   └── DESIGN.md - System Design Doc
├── search_pipeline/ - whole search process and calculation of metrics
├── .dvcignore - auxiliary file for DVC
├── .gitignore - important ignore settings (also needed for DVC)
├── README.md - this document
├── data.dvc - DVC info on tracked content of "data/" directory (managed automatically)
├── metrics.json - search metrics, which are used to track history and generate the report on GitHub Pages
└── requirements.txt - list of Python packages for installation
```
