ReTiCo is a python framework to enable real time incremental conversational spoken dialogue systems.
The architecture is based on the paper of Schlangen and Skantze "A General, Abstract Model of Incremental Dialogue Processing" (2011).

## Framework

The framework provides base classes for modules and *incremental units* that can be used to write asynchronous data processing pipelines.

## ReTiCo Builder

The ReTiCo Builder provides a graphical user interface for building networks with the modules available.

## Installing

You need to have portaudio installed.

```
$ pip install Cython==0.26.1
```

```
$ pip install https://github.com/kivy/kivy/archive/master.zip
```

```
$ python setup.py
```

Start the ReTiCo Builder with:

```
$ retico-builder
```