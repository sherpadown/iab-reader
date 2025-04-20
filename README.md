# Immersive Audio Bitstream (IAB) Reader

iab-reader analyzes and explains IAB chunks.

Dolby Atmos uses IAB format. 


## Usage


### Installation 

```
$ uv venv
$ source .venv/bin/activate
$ uv sync
```

### Using

```
$ python -m iab_reader 
Usage: file.iab or directory contains iab files
```


You can use iab-reader on a specific chunk file :

```
$ python -m iab_reader tests/assets/silence.iab/000.iab
     ┌────────────────────────────────────────────────────────────────────────────────────────────────────
     │▐━━━━ IABitstream Frame ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▐  [1]
     │───── Preamble ────────────────────────────────────────────────────────────────────────  [1]
     │      PreambuleTag : 0x01
     │      PreambuleLength : 1603 bytes
     │      PreambuleValue : 11010e00000000000000000000000000(...1571 bytes...)00000000000000000000000000000000
     │───── IAFrame ─────────────────────────────────────────────────────────────────────────  [1]
     │      IAFrameTag : 0x02
     │      IAFrameLength : 32 bytes
     │      IAFrameValue : 081e01100a0110180050000400040034(...0 bytes...)0028009000e0020005800c000c000500
     │───── IAElement ───────────────────────────────────────────────────────────────────────  [1]
     │      ElementID : 0x08 (IAFrame: Frame Header)
     │      ElementSize : 0x1e (30 bytes)
     │      SubElementValue : 01100a01101800500004000400340028009000e0020005800c000c000500(..) (30 bytes)
     ┌     ┌────────────────────────────────────────────────────────────────────────────────────────────────────
     │     │▐━━━━ IAFrame ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▐  [2]
     │     │      IAVersion : 1
     │     │      SampleRate : 0b00 (48000 Hz)
	(...)
```


or directly on a directory :


```
$ python -m iab_reader tests/assets/atmos-stresstest-64objects.iab/
+++ tests/assets/atmos-stresstest-64objects.iab//00016524-060e2b34010201050e09060100000001-ImmersiveAudioDataElement.value.bin
     ┌────────────────────────────────────────────────────────────────────────────────────────────────────
     │▐━━━━ IABitstream Frame ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▐  [1]
     │───── Preamble ────────────────────────────────────────────────────────────────────────  [1]
     │      PreambuleTag : 0x01
     │      PreambuleLength : 1603 bytes
     │      PreambuleValue : 11010effffffffffffffffffffffffff(...1571 bytes...)ffffffffffffffffffffffffffffffff
     │───── IAFrame ─────────────────────────────────────────────────────────────────────────  [1]
     │      IAFrameTag : 0x02
     │      IAFrameLength : 44501 bytes
     │      IAFrameValue : 08ffadd10110529bff0200ff020e6402(...44469 bytes...)0173ffc1bfffc0300000200000000500
     │───── IAElement ───────────────────────────────────────────────────────────────────────  [1]
     │      ElementID : 0x08 (IAFrame: Frame Header)
     │      ElementSize : 0xadd1 (44497 bytes)
     │      SubElementValue : 0110529bff0200ff020e64020b12d0202aad16adb68b4ab6daa55b4ab4aa0a2a(..) (44497 bytes)
     ┌     ┌────────────────────────────────────────────────────────────────────────────────────────────────────
     │     │▐━━━━ IAFrame ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━▐  [2]
     │     │      IAVersion : 1
     │     │      SampleRate : 0b00 (48000 Hz)
	(...)


$ python -m iab_reader tests/assets/transformers.iab/ | grep '+++'
+++ tests/assets/transformers.iab//000.iab
+++ tests/assets/transformers.iab//001.iab
+++ tests/assets/transformers.iab//002.iab
+++ tests/assets/transformers.iab//003.iab
+++ tests/assets/transformers.iab//004.iab
+++ tests/assets/transformers.iab//005.iab
+++ tests/assets/transformers.iab//006.iab
(...)
```



### Use with Docker

```
$ make docker.build         # build docker
$ make docker.run.tests     # run tests
```

or

```
$ docker run -v "/local/path/assets:/assets" -it --rm iab-reader:latest -f /assets/iab
```

