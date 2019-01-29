Since the dataset with highest resolution is the DEM, we will align our datasets to it.

## Notes

* Saving `.nc` files aligned to a finer resolution is verbose and space inefficient, so we will just crop them first, and align them in runtime within the `STREAM` step (thus avoiding to store the files)

```mermaid
graph TD
DEM[DEM tif] --> CROP(Crop to watershed extent);
WSHED[Watershed shp] --> CROP;
CROP --> DEMC[Cropped DEM];

DEMC --> ALIGNL(Align to Cropped DEM);
LULC[LULC tif] --> ALIGNL;
ALIGNL --> LULCA[Aligned LULC];

LULCA --> MAPC(Map to crop factor);
MAPC --> CROPF[CROPF];

DEMC --> CROPT(Crop to watershed extent);
TEMP[TEMP nc] --> CROPT;
CROPT --> TEMPA[Cropped TEMP];

DEMC --> CROPP(Crop to watershed extent);
PREC[PREC nc] --> CROPP;
CROPP --> PRECA[Cropped PREC];

DEMC --> FILL(Fill pits);
FILL --> DEMF[Filled DEM];

DEMF --> STREAM[STREAM];
CROPF --> STREAM;
WHC[WHC tif] --> STREAM;
TEMPA --> STREAM;
PRECA --> STREAM;
STREAM --> FLOW[Flow];
```
