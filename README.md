ReTiCo is a python framework to enable real time incremental conversational spoken dialogue systems.
The architecture is based on the paper of Schlangen and Skantze "A General, Abstract Model of Incremental Dialogue Processing" (2011).

## Framework

The framework provides base classes for modules and *incremental units* that can be used to write asynchronous data processing pipelines.

## ReTiCo Builder

The ReTiCo Builder provides a graphical user interface for building networks with the modules available.

## Installing

### Requirements

Generally you need the following for running ReTiCo:

 - `Python 3`
 - `portaudio`
 - `pyaudio`
 - `flexx`

 Optionally you can use additional modules if you install:

 - `google-cloud-speech`
 - `rasa-nlu`

#### Portaudio

Because ReTiCo is handling all sorts of audio streams, you need to have `portaudio` installed.

On **Linux** this can be done via your favorite package-manager. For example:

```
$ sudo apt-get install portaudio
```

On **MacOS** you can install it via `brew`:

```
$ brew install portaudio
```

On **Windows** you need to google.

#### PyAudio

For this to work you need to install portaudio on your system first!

```
$ pip install pyaudio
```

### Flexx

To run the retico_builder frontend you need at least flexx 0.4.2. For this you can clone the repository from github and install it from there.

```
$ pip install https://github.com/flexxui/flexx/archive/master.zip
```

## Optional stuff

Some third party libraries are not included into ReTiCo and have to be installed manually. If you try to use those IncrementalModules before you installed the library you will get an error.

In the ReTiCo Builder, the modules won't appear in the list of available modules until you install the third pary library.

### Google Cloud Speech

To use the Automatic Speech Recognition module utilizing google cloud speech, you need to install the third party package first.

For this you may follow the first two steps of [this tutorial](https://cloud.google.com/speech-to-text/docs/quickstart-client-libraries#client-libraries-install-python).

Important is, that you create your **Google Application Credentials json file** and save the path to that file into the global variable `GOOGLE_APPLICATION_CREDENTIALS` (look for the "*Before you begin*" section on the tutorial page).

If this is setup and you've run

```
$ pip install google-cloud-speech
```

you are all set for using GoogleASR!

### Rasa NLU

For installing Rasa NLU, just install it via:

```
$ pip install rasa_nlu
```

## Installing Retico

To setup retico you can just run

```
$ python setup.py install
```

## Using Retico

### In Python

In Python you can now import the ReTiCo modules, connect them and run your network.

```python
m1 = MicrophoneModule(5000)
m2 = StreamingSpeakerModule(5000)

m1.subscribe(m2)

m1.run()
m2.run()

input()

m1.stop()
m2.stop()
```

This example will create a simple network consisting of a MicrophoneModule that gives its output to the StreamingSpeakerModule, which just outputs the incoming data to the speaker.


### With the GUI

If you have installed flexx, you can simply run

```
$ python -m retico_builder.builder
```
