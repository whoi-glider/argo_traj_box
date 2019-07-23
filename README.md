# Installation

I personally use the conda distribution of python. This file will only requrie the installation of 2 packages: pandas and folium. To install on conda, use the command "conda install pandas" and "conda install folium"

# argo_traj_box

This program will download argo trajectory data from the Gdac meta file and plot it. It will show all trajectories that pass through a given box. 

If the pandas dataframe generated from the trajectory metafile, it will download and recompile the necessary dataframe. To manually update new trajectories, use the flag --recompile when calling the program. 

The coordinates of the box you wish to plot are defined in the arguments of the python command execution with the following format: (lower left lon) (lower left lat) (upper right lon) (upper right lat). For example "python main.py 129 -50 130 -49" will show all trajectories passing through the box 129W 50S to 130W 49S. 

The flag --markers will show the deployment and last transmission locations of all floats which pass through the box. 

New flag "years" will now show a set number of years beyond when the float first entered the box. e.g. "python main.py -20 -50 -10 -40 --years .1 --box --line" The number of years is a float and need not be integer.

That is all. Carry on. 
