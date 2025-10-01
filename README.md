# Search Engine for Russian Advertisements

All operations for project development and maintenance should be described on [Wiki page](https://github.com/ODS-NN-Breakfasts/rus-ad-search-engine/wiki).

## Directory and File Structure

```text
.
├── .dvc/ - settings for DVC tool
├── dataset_tools/ - tools to work with dataset
├── research/ - place for research-related code and docs
│   └── DESIGN.md - System Design Doc
├── search_pipeline/ - whole search process and calculation of metrics
├── .dvcignore - auxiliary file for DVC
├── .gitignore - important ignore settings (also needed for DVC)
├── README.md - this document
├── data.dvc - DVC info on tracked content of "data/" directory (managed automatically)
└── requirements.txt - list of Python packages for installation
```
