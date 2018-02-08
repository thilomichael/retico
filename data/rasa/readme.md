# Training and using the rasa NLU model

For using the Rasa NLU in ReTiCo the python package rasa_nlu and all dependencies for the pipeline have to be installed

## Quick setup

Make sure python is installed and execute

```bash
$ bash train_nlu.sh
```

This will install rasa_nlu with all required dependencies, it will also download the english language model and will train the model with the information provided by `data/franken_data.json`.

## Step by step

Install rasa_nlu and dependencies by executing:

```bash
$ python -m pip install rasa_nlu spacy sklearn_crfsuite sklearn
```

Then, download the english model of spacy by executing:

```bash
$ python -m spacy download en_core_web_lg
$ python -m spacy link en_core_web_lg en
```

Finally, train the model by executing:

```bash
$ python -m rasa_nlu.train -c nlu_model_config.json
```
