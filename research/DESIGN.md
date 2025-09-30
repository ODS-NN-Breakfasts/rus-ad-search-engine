# System Design

This is a main design document to document design principles, system architecture, performed investigations, and motivations for decisions.

## Review of Text Processing Tools

`TBD`

### Word Embeddings

#### Word2Vec
    
| Library                                                            | Licence  | Languages   | Models                                                                               | Model Licences | OOV | Comment                                    |
|--------------------------------------------------------------------|----------|-------------|--------------------------------------------------------------------------------------|----------------|-----|--------------------------------------------|
| [gensim](https://radimrehurek.com/gensim/auto_examples/index.html) | LGPL-2.1 | rus<br/>eng | "word2vec-ruscorpora-300" <br/> "word2vec-google-news-300"                               | CC-BY <br/>  ? | no  | rus - with POS-tags                        |
| [flair](https://flairnlp.github.io/docs/intro)                     | MIT      | rus<br/>eng | [ruwikiruscorpora_upos_cbow_300_10_2021](https://rusvectores.org/ru/models/)  <br/> ? | CC-BY <br/>  ? | no  | only text format, <br/> tokenizes POS-tags | 

#### FastText

#### GloVe

