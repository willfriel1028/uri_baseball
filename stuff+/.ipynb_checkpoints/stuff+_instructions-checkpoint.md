# Stuff+ Update Instructions

1. Start at `data_collect.ipynb` - only run each block for the year you are testing for, any previous seasons won't have any changes
2. Go to `data_combine.ipynb` to create one large csv file and save it as a csv locally
3. Go to `model_creation.ipynb` - run these blocks of code if you have new training data, otherwise you don't need to touch anything here
4. Go to `stuff_plus_{year}.ipynb` - create a new notebook for any given year you are testing on, running this notebook will produce `stuff.csv` and `stuff_table.csv`