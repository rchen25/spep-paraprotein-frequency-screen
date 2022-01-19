# Serum protein electrophoresis paraprotein screening tool


## About

We provide a method for screening SPEPs for paraproteins.
The model parameters used for this tool were tuned based on a private dataset of samples from the authors' clinical laboratory. 


## Usage

The method takes as input, a serum protein electrophoresis densitometry curve as well as an associated control densitometry curve (does not contain a paraprotein). 


### Input format

Input file with columns:

* **sebiaSerumCurve**: string in hexadecimal format for serum curve from Sebia device
* **sebiaSerumGelControlCurve**: string in hexadecimal format for control curve from Sebia device

Sample input file is in `data/sample_input_data.csv`

### Steps to run screening tool
#### Step 1

Initialize environment

```
source env/bin/activate
```

#### Step 2

Run the algorithm with input

```
python paraprotein_screen.py data/sample_input_data.csv
```

Output will be generated by default in `./output.csv` and `./output.json`

Each item in output will have the following:

* **sebiaSerumCurve**: string in hexadecimal format for serum curve from Sebia device
* **sebiaSerumGelControlCurve**: string in hexadecimal format for control curve from Sebia device
* **sebiaSerumCurve_intArr**: serum curve as integer array 
* **sebiaSerumGelControlCurve_intArr**: control curve as integer array
* **gamma_region_cutoff**: index of element in integer array that delimits the gamma region (identified from control)
* **prediction**: predicted paraprotein status (1 = positive prediction, 0 = negative prediction)
