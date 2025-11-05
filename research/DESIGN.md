# System Design

This is a main design document to document design principles, system architecture, performed investigations, and motivations for decisions.

## Problem Statement

There is a set of advertisements in Russian (and partially English) language, which should be searcheable by user text request. The request can coincide with the advertisement only partially.

### Main Challenges

1. Request can contain too many details, which are absent in the advertisement, but not necessarily absent in the advertised product
1. Request can contain description of general product category, but not the description of category instances
1. Request and advertisement can contain misprints, punctuation and grammar errors, unexpected abbreviations, toponyms, etc.
1. Request can be written only as explanation to the image, without description of main product properties
1. Advertisement can tell not only about selling or giving, but also about buying or acceping
1. It is desirable to distingush proposals without any price from the proposals with price

## Review of Text Processing Tools

### Text Preprocessing

[Natasha](https://github.com/natasha/natasha) has:
* Tokenization
* Embeddings
* NER
* other ([overview article in Russian](https://habr.com/ru/articles/516098/))

[SpaCy](https://spacy.io/usage/models#quickstart) has:
* Tokenization
* POS Tagging
* Lemmatization
* Named Entity Recognition

Also [flair](https://flairnlp.github.io/docs/intro) has been considered, as it has multilingual POS-tagging and NER (and also [a wrapper for Russian FastText embeddings](https://flairnlp.github.io/flair/v0.15.1/tutorial/tutorial-embeddings/classic-word-embeddings.html)), but it does not look reliable, comparing with other alternatives.

#### Lemmatization
| Library         | Licence   | Languages  | Models    | Model Licences | OOV     | Comment |
| :--------------:|:---------:|:----------:|:---------:|:--------------:|:-------:|:-------:|
|pymorphy2/3      |MIT        |rus         |[OpenCorpora](https://opencorpora.org/) |  -            |module makes suggestion for OOV|https://github.com/no-plagiarism/pymorphy3|
|pymystem3        |MIT        |rus/eng     |  -        |  -             |module makes suggestion for OOV|https://github.com/nlpub/pymystem3|
|SpaCy            |MIT        |rus/eng     | ru_core_news_md/ru_core_news_lg <br/> en_core_web_md/en_core_web_lg |- |No|https://spacy.io/|

### Word Embeddings

#### Word2Vec
    
| Library                                                            | Licence  | Languages   | Models                                                                               | Model Licences | OOV | Comment                                    |
|--------------------------------------------------------------------|----------|-------------|--------------------------------------------------------------------------------------|----------------|-----|--------------------------------------------|
| [gensim](https://radimrehurek.com/gensim/auto_examples/index.html) | LGPL-2.1 | rus<br/>eng | "word2vec-ruscorpora-300" <br/> "word2vec-google-news-300"                               | CC-BY <br/>  ? | No  | rus - with POS-tags                        |
| [flair](https://flairnlp.github.io/docs/intro)                     | MIT      | rus<br/>eng | [ruwikiruscorpora_upos_cbow_300_10_2021](https://rusvectores.org/ru/models/)  <br/> ? | CC-BY <br/>  ? | No  | Only text format, <br/> Tokenizes POS-tags | 

#### FastText
| Library                                              | Licence  | Languages   | Models                                     | Model Licences            | OOV | Comment                                                                   |
|------------------------------------------------------|----------|-------------|--------------------------------------------|---------------------------|-----|---------------------------------------------------------------------------|
| [FastText](https://fasttext.cc/docs/en/support.html) | MIT | rus<br/>eng | "ru" <br/> "en"                            | CC BY-SA 3.0              | Yes | Subword tokenization, <br/> Sentence vectorization                        |
| [flair](https://flairnlp.github.io/docs/intro)                     | MIT      | rus<br/>eng | "ru" <br/> "en" <br/> or [fasttext original](https://fasttext.cc/docs/en/crawl-vectors.html) | MIT <br/> or CC BY-SA 3.0 | Yes | Fully trough `FastTextEmbeddings`, which is deprecated since version 0.14 | 

#### GloVe

| Library                                                            | Licence  | Languages   | Models                                                                                      | Model Licences | OOV | Comment                                                                                                                                                            |
|--------------------------------------------------------------------|----------|-------------|---------------------------------------------------------------------------------------------|----------------|-----|--------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [SpaCy](https://spacy.io/usage/models#quickstart) | MIT | rus<br/>eng | "ru_core_news_md"  <br/> "ru_core_news_lg" <br/> "en_core_news_md"  <br/> "en_core_news_lg" | MIT | No  | Only "md" / "lg" models have vector vocabulary support (see first important note [here](https://spacy.io/usage/linguistic-features#vectors-similarity)<br/> Similarity |
| [NeVec](https://github.com/natasha/navec) | MIT | rus | `navec_hudlit_v1_*.tar` | - | No | - |

## Data Format

All data is located in `data/` directory and [is tracked separately](#no-data-in-repository).

* `ads_db.txt` - plain text file with one advertisement per line (multiline advertisements are normalized to a single line with `\n`)
   * ID of advertisement is its line number (counted from 1), so to keep old IDs, new requests must be added below
* `request_db.txt` - plain text file with one search request per line
   * ID of request is its line number (counted from 1), so to keep old IDs, new requests must be added below
* `matching_db.txt` - matching file for requests and advertisements:
   * Each line contains matching info in a form like `1, 2, 4-7, 10 <=> 4, 10, 11, 18-20`, where a list of _request IDs_ is placed _before_ `<=>` separator, and a list of _advertisement IDs_ is placed _after_ it
   * Ranges of IDs can be written with `-` dash for short, both the start and the end are in cluded in the range: `18-20` equals to `18, 19, 20`
   * Comma-separated IDs is just a syntactic sugar, they can be equivalently written as `1 <=> 4`, `2 <=> 4`, `4 <=> 4`, `5 <=> 4`, `6 <=> 4`, `7 <=> 4`, `10 <=> 4`, `1 <=> 10`, and so on
   * IDs that were not mentioned in the matching file accounted as not matched

### Annotation Rules

No suitable data annotators were found after the quick search, so data is annotated manually in a plain text file.

To speed-up annotation, it can be useful to categorize requests in `request_db.txt` to categories (we stored them in `request_categories.txt` in the format `<category name>: request IDs`), then find these categoried in `ads_db.txt`. The markup process can be started from matching these categories, then matches for each category can be finally checked according to the rules below.

General matching rules:

1. All missed information (in request or in advertisement) is interpreted in favor of _match_
   1. "bed" matches "iron bed", "wooden bed", "a set of bed, mattress, and two chairs", etc.
1. If the "direction of action" differs (sell vs buy, take vs give), then there is _no match_
1. If the difference is only in price (but "direction of action" coincides), then it is _match_
   1. "I will accept a bed as a gift" matches "bed for $1M", "old bed for a chocolate", "I'm giving a bed away for free", etc.
1. Any difference in locations is _not a match_
   1. "looking for bed in NY" does not match "beds in LA for free"
1. Even clear difference in the product properties is still _a match_, as far as the main product _matches_ (_EXCLUSION:_ clothes size may be _not a match_)
   1. "wooden bed" matches "iron bed", "red shirt" matches "blue shirt", etc.
   1. "shoes of size 44" should not match "shoes of size 32", and also "children's clothes" should not match "plus size clothes", "clothes 6XL", etc.

## Tried Architectures

### Averaged Word Embedding in BOW

```mermaid
graph LR
  classDef inputData fill:#a9f5a9
  classDef intermediateData fill:#a9a9f5
  classDef outputData fill:#f6cef5

  ad[/Advertisement/]:::inputData
  sent_processor1[Averaged word embedding over bag of words]
  sent_processor2[Averaged word embedding over bag of words]
  ad_emb[Embedding of advertisement]:::intermediateData
  req[/User request/]:::inputData
  req_emb[Embedding of user request]:::intermediateData
  emb_compare{Vectors, closer<br>than threshold}
  data[Marked up Dataset]
  result_compare{Comparison with markup}
  metric[\Accuracy metric\]:::outputData

  ad==>sent_processor1
  sent_processor1==>ad_emb
  req==>sent_processor2
  sent_processor2==>req_emb
  ad_emb==>emb_compare
  req_emb==>emb_compare
  emb_compare==>result_compare
  data-->result_compare
  result_compare==>metric
```

## Images Usage
Since advertisements contain images of a product, it's reasonable to try to collect some extra info from them.

### Cases
In ideal advertisement should have all the info in the description (products, materials, colors, etc.). In reality some of advertisements provide all info only in image with no words about the product. Therefore we have 3 types of advertisements:
1) Description says all the information about the product -> there is no additional (and useful) info in the image. It's the majority of the ads and most of them is selling (or giving) plants or food. **About 80% of ads**
2) Description has some info, but it's not enough to fully descibe the product. It's the case with clothes and furniture. Image here can give information about materials, colors and condition of a product, that could be useful as addition for a product description. **About 5% of ads**
3) Description says nothing about the product. Here images is the only source of info. **About 15% of ads**

### Models
So we have about 20% of advertisements where image info might be useful. Now let's see which models could be useful.

#### YOLOv8/v11 pretrained on MS COCO
Advantages:
- 55 of 80 classes could be possible advertisement product 
- Even largest models are actually lightweight in terms of memory usage and inference speed
- Could be easily finetuned in future

Disadvantages:
- Classes are too general (for example, car could be detected, but no brend)
- Leak of the most common classes, such as clothes

Links: 
   [MS COCO Classes](https://docs.ultralytics.com/datasets/detect/coco/#dataset-yaml), 
   [YOLOv8](https://huggingface.co/Ultralytics/YOLOv8), 
   [YOLOv11](https://huggingface.co/Ultralytics/YOLO11),
   [YOLO License](https://choosealicense.com/licenses/agpl-3.0/)

#### CLIP
Advantages:
- Could be used for Zero-Shot classification
- Visual encoder could be used without text encoder to make embedding of images, that could be added to request embeddings
- Quite small size and fast inference (especially if only visual encoder used)

Disadvantages:
- Don't see any, atleast without testing 

Links:
   [CLIP API](https://github.com/openai/CLIP),
   [CLIP Visual Encoder](https://huggingface.co/openai/clip-vit-base-patch32) (there are more on HuggingFace),
   [CLIP License](https://github.com/openai/CLIP/blob/main/LICENSE)

#### Quantized VLMs
Advantages:
- The best in terms of getting information from images
- "Out of the box" usage, no need in futher finetuning

Disadvantages:
- Resource needs, even smallest of quantized VLMs weight around 1GB and may significantly increase the search time

Some of VLMs:
- **[LLaMa3.2](https://huggingface.co/unsloth/Llama-3.2-1B-Instruct-unsloth-bnb-4bit)**: ~1.03GB for 4bit quantization, [License](https://huggingface.co/meta-llama/Llama-3.2-1B/blob/main/LICENSE.txt)

## Architecture Decisions

### Python

Project is developed on Python 3.12

### No Data in Repository

Since real advertisements can contain personal information, we don't store them in the repository. Generally, we decided to not store any data in the repository at all, and work with it locally with [DVC](https://dvc.org/).

### Metrics

#### Optimal Threshold

Since the development workflow needs constant comparison between current metrics and the previously obtained ones, we decided to calculate metrics with best possible threshold. The best (most optimal) threshold is [calculated automatically](/utils/metrics.py) by maximization of F1 for the whole dataset, and after that it is used to calculate all threshold-based metrics. In our opinion, which should work better than ROC-AUC (which averages performance by _multiple_ thresholds, so two different models with the _fixed_ threshold can differ in opposite direction) or a static fixed threshold (which can be not the best one for each model).

#### Monitoring

Monitoring system was implemented through the [metrics.json](/metrics.json) file, which contains search metrics. Its history is obtained from Git and visualised on GitHub Pages. More details are in the [corresponding README](/gh_pages/README.md).

Main requirements to metrics monitoring system:
* Metrics should be tied to the code, which produced them
   * Partly done through the `metrics.json`, which should be generated by code in the same commit
* There should be a plot of metrics history to track their changes visually
   * Done by the plot on GitHub Pages, which is generated by GitHub Actions from the history of `metrics.json`
* Metrics, that were obtained from the different data, should not be compared directly
   * Can be done by controlling checksums of data files, which are also stored in `metrics.json`
