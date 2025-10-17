# trailpack

```{button-link} https://github.com/TimoDiepers/trailpack
:color: info
:expand:
Trailpack proposes a standard way to link data and specialized metadata in one single file. It provides a simple interface to link metadata to fixed ontologies, improving the accessibility and comparability of datasets from different sources.
It can be used in general to combine metadata and data into a [parquet](https://parquet.apache.org/) file. 
```
**Why?** The ultimate goal is to make open data accessible and sustainable. Trailpack takes one step into this direction by including standardised metadata directly into the data files. 

**Want to take a next step towards open data?** You could start preparing your datasets or participate in developing this tool! 

Trailpack collects metadata and directly validates it with the developed standard including
* general metadata for the datapackage, like name and license
* specialised metadata for each data column - linking both column names and units to fixed descriptions given in ontologies provided by [PySt](https://vocab.sentier.dev)   
The developed standard expands on and is compatible with the [datapackage](https://datapackage.org/) standard. The metadata is and included under the datapackage.json keyword.

Both formats for metadata and file format are chosen based on widespread usage and standardisation.
The output file is readbale using [pyarrow](https://arrow.apache.org/docs/python/index.html) and other data handlers - and will be compatible and consumable using (Sentier data tools)(https://github.com/sentier-dev/sentier_data_tools)

Tailpack was initially built during the hackathon of brightcon 2025 in Grenoble, as part of developing the standard data format for [Départ de Sentier](https://www.d-d-s.ch/) in [Issue 1](https://github.com/Depart-de-Sentier/brightcon-2025-material/issues/1). 
```{toctree}
---
hidden:
maxdepth: 1
---
self
content/usage
content/api/index
content/codeofconduct
content/contributing
content/license
content/changelog
```
