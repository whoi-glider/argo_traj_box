import os
import pandas as pd
from ftplib import FTP 
import argparse
import folium
import folium.plugins
import numpy as np
from itertools import cycle

parser = argparse.ArgumentParser()
parser.add_argument("lllon", help="lower left longitude of box to plot",
                    type=float)
parser.add_argument("lllat", help="lower left latitude of box to plot",
                    type=float)
parser.add_argument("urlon", help="upper right longitude of box to plot",
                    type=float)
parser.add_argument("urlat", help="upper right latitude of box to plot",
                    type=float)
parser.add_argument("--recompile", help="downloads and recompiles the trajectory df",
                    action="store_true")
parser.add_argument("--markers", help="shows the deployment and end transmission locations of all argo floats",
					action="store_true")



def wrap_lon180(lon):
    lon = np.atleast_1d(lon).copy()
    angles = np.logical_or((lon < -180), (180 < lon))
    lon[angles] = wrap_lon360(lon[angles] + 180) - 180
    return lon

def wrap_lon360(lon):
    lon = np.atleast_1d(lon).copy()
    positive = lon > 0
    lon = lon % 360
    lon[np.logical_and(lon == 0, positive)] = 360
    return lon

def plot_the_cruises(df_):
	colorlist = ['red', 'blue', 'green', 'purple', 'orange', 'darkred',
                  'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue',
                  'darkpurple', 'pink', 'lightgreen',
                  'gray']
	color=cycle(colorlist)
	map=folium.Map(location=[0,0],zoom_start=2,tiles='Mapbox bright')
	marker_cluster = folium.plugins.MarkerCluster().add_to(map)
	for cruise in df_['Cruise'].unique():
		c = next(color)
		df_holder = df_[df_.Cruise==cruise]
		# if (df_holder.longitude.diff()<180).all()
		df_holder['wrap']=df_holder.longitude.diff().abs()>180
		df_holder['wrap'] = df_holder.wrap.apply(lambda x: 1 if x else 0).cumsum()
		for g in df_holder.groupby('wrap').groups:
			frame = df_holder.groupby('wrap').get_group(g)
			points = [tuple(dummy) for dummy in frame[['latitude','longitude']].values]
			folium.PolyLine(points, color=c, weight=1, opacity=0.7,popup='WMO ID # %s' %cruise).add_to(map)
		if args.markers:
			folium.Marker(tuple(df_holder[['latitude','longitude']].values[0]),popup='WMO ID # %s Deployed' %cruise, icon = folium.Icon(color=c)).add_to(marker_cluster)
			folium.Marker(tuple(df_holder[['latitude','longitude']].values[-1]),popup='WMO ID # %s Last Transmission' %cruise, icon = folium.Icon(color=c)).add_to(marker_cluster)
	folium.PolyLine([(lllat,lllon),(urlat,lllon),(urlat,urlon),(lllat,urlon),(lllat,lllon)],popup='Bounding Box', color='black', weight=7, opacity=1).add_to(map)
	map.save(outfile='map.html')
	os.system('open map.html')

def download_meta_file_and_compile_df():
	link = 'usgodae.org'
	ftp = FTP(link) 
	ftp.login()
	ftp.cwd('pub/outgoing/argo')
	filename = 'ar_index_global_prof.txt'
	file = open(filename, 'wb')
	ftp.retrbinary('RETR %s' % filename,file.write,8*1024)
	file.close()
	ftp.close()
	df_ = pd.read_csv(filename,skiprows=8)
	df_['Cruise'] = [dummy.split('/')[1] for dummy in df_['file'].values]
	df_ = df_[['Cruise','latitude','longitude']]
	df_ = df_[df_.longitude!=99999]
	df_ = df_[df_.longitude!=-999]
	df_ = df_[df_.longitude<=180]
	assert df_.longitude.min()>-180
	assert df_.longitude.max()<=180
	assert df_.latitude.min()>-90
	assert df_.latitude.max()<90
	df_.to_pickle('traj_df.pickle')
	print('trajectory data has been downloaded and recompiled')
	return df_

args = parser.parse_args()
if args.recompile:
	print('Redownloading and recompiling the trajectory dataframe')
	df = download_meta_file_and_compile_df()
try:
	df = pd.read_pickle('traj_df.pickle')
except IOError:
	print('No trajectory dataframe found, redownloading and recompiling trajectory dataframe')
	df = download_meta_file_and_compile_df()

lllon = args.lllon
lllat = args.lllat
urlon = args.urlon
urlat = args.urlat

if urlon<lllon:
	df['longitude']=wrap_lon360(df['longitude'].values)
	urlon = wrap_lon360(urlon)[0]
	lllon = wrap_lon360(lllon)[0]

assert lllat<urlat, "lllat must be less than urlat"
assert lllat!=urlat, "The latitudes cannot be the same"
assert lllon!=urlon, "The longitudes cannot be the same"
assert (abs(urlon-lllon)<180)|(abs(wrap_lon360(urlon)[0]-lllon)<180), "the box can only be 180 degrees big"

if urlon<lllon:
	df['longitude']=wrap_lon360(df['longitude'].values)
	urlon = wrap_lon360(urlon)[0]
	lllon = wrap_lon360(lllon)[0]

df_holder = df[(df.latitude>lllat)&(df.latitude<urlat)]
cruise_list = df_holder[(df_holder.longitude<urlon)&(df_holder.longitude>lllon)].Cruise.unique()
df = df[df.Cruise.isin(cruise_list)]

df['longitude']=wrap_lon180(df['longitude'].values)
urlon = wrap_lon180(urlon)[0]
lllon = wrap_lon180(lllon)[0]


plot_the_cruises(df)