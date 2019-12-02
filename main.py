import os
import pandas as pd
from ftplib import FTP
import argparse
import folium
import folium.plugins
import numpy as np
from itertools import cycle
import requests
import json
import datetime
from netCDF4 import Dataset
import pickle

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
parser.add_argument("--full_traj", help="shows the full trajectory of the float from deployment to last transmission",
					action="store_true")
parser.add_argument("--forward", help="shows the trajectory since float entered box",
					action="store_true")
parser.add_argument("--reverse", help="shows the trajectory before float entered box",
					action="store_true")
parser.add_argument("--SOCCOM", help="shows only the SOCCOM floats in the map",
					action="store_true")
parser.add_argument("--iridium", help="shows only the IRIDIUM floats in the map",
					action="store_true")
parser.add_argument("--ARGOS", help="shows only the Argos floats in the map",
					action="store_true")
parser.add_argument("--line", help="displays trajectories as lines",
					action="store_true")
parser.add_argument("--dots", help="displays profiles as dots",
					action="store_true")
parser.add_argument("--box", help="shows the surrounding box",
					action="store_true")
parser.add_argument('--years',
                        action='store',
                        nargs=1,
                        type=float,
                        help='Number of years to plot')




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
                  'lightred', 'darkblue', 'darkgreen', 'cadetblue',
                  'darkpurple', 'pink', 'lightgreen',
                  'gray']
	color=cycle(colorlist)
	url = 'https://server.arcgisonline.com/arcgis/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}'
	map=folium.Map(location=[0,0],zoom_start=2)

	folium.TileLayer(tiles=url, attr='World_Ocean_Base').add_to(map)

	marker_cluster = folium.plugins.MarkerCluster().add_to(map)
	df_box = pd.DataFrame({})
	for cruise in df_['Cruise'].unique():
		c = next(color)
		df_holder = df_[df_.Cruise==cruise]
		# if (df_holder.longitude.diff()<180).all()
		df_holder['wrap']=df_holder.longitude.diff().abs()>180
		df_holder['wrap'] = df_holder.wrap.apply(lambda x: 1 if x else 0).cumsum()
		for g in df_holder.groupby('wrap').groups:
			frame = df_holder.groupby('wrap').get_group(g)
			points = [tuple(dummy) for dummy in frame[['latitude','longitude']].values]
			if (args.box)&(cruise=='BOX'):
				folium.PolyLine(points, color='black', weight=7, opacity=1).add_to(map)
				if df_holder['wrap'].sum()>0:
					folium.PolyLine([(urlat,lllon),(urlat,180)], color='black', weight=7, opacity=1).add_to(map)
					folium.PolyLine([(urlat,-180),(urlat,urlon)], color='black', weight=7, opacity=1).add_to(map)
					folium.PolyLine([(lllat,urlon),(lllat,-180)], color='black', weight=7, opacity=1).add_to(map)
					folium.PolyLine([(lllat,180),(lllat,lllon)], color='black', weight=7, opacity=1).add_to(map)
			elif (args.line)&(cruise!='BOX'):
				folium.PolyLine(points, color=c, weight=1, opacity=0.7).add_to(map)
			elif (args.markers)&(cruise!='BOX'):
				folium.Marker(tuple(df_holder[['latitude','longitude']].values[0]),popup='WMO ID # %s First Transmission' %cruise, icon = folium.Icon(color=c)).add_to(marker_cluster)
				folium.Marker(tuple(df_holder[['latitude','longitude']].values[-1]),popup='WMO ID # %s Last Transmission' %cruise, icon = folium.Icon(color=c)).add_to(marker_cluster)
			elif (args.dots)&(cruise!='BOX'):
				for ii in range(len(df_token)):
					folium.features.Circle(tuple(df_token[['latitude','longitude']].values[ii]), color=c).add_to(marker_cluster)

	# url = 'https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
	# antarctic_ice_edge = f'{url}/antarctic_ice_edge.json'
	# antarctic_ice_shelf_topo = f'{url}/antarctic_ice_shelf_topo.json'

	# folium.GeoJson(
	#     antarctic_ice_edge,
	#     name='geojson'
	# ).add_to(map)

	# folium.TopoJson(
	#     json.loads(requests.get(antarctic_ice_shelf_topo).text),
	#     'objects.antarctic_ice_shelf',
	#     name='topojson'
	# ).add_to(map)

	# url = 'https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.json?altitude%5B(-90.0):(90.0)%5D%5B(-180.0):(180.0)%5D&.draw=surface&.vars=longitude%7Clatitude%7Caltitude&.colorBar=%7C%7C%7C%7C%7C&.bgColor=0xffccccff'
	# folium.GeoJson(
	#     url,
	#     name='test'
	# ).add_to(map)


	# folium.LayerControl().add_to(map)
	map.save(outfile='map.html')
	os.system('open map.html')


def download_meta_file_and_compile_df():
	url = 'http://soccom.ucsd.edu/floats/SOCCOM_float_stats.html'
	html = requests.get(url).content
	df_list = pd.read_html(html)
	wmoID_list = df_list[-1]['TrajdataWMOID'].values
	wmoID_list = [str(dummy) for dummy in wmoID_list]

	def ftp_download(server_path,dummy=True):
		try:
			link = 'usgodae.org'
			ftp = FTP(link)
			ftp.login()
			filename = os.path.basename(server_path)
			relative_change = os.path.relpath(os.path.dirname(server_path),ftp.pwd())
			ftp.cwd(relative_change)
			if dummy:
				file = open('dummy','wb')
			else:
				file = open(filename, 'wb')
			ftp.retrbinary('RETR %s' % filename,file.write,8*1024)
			file.close()
			ftp.close()
		except TimeoutError:
			ftp_download(server_path,dummy=dummy)

	global_prof_filename = '/pub/outgoing/argo/ar_index_global_prof.txt'
	global_meta_filename = '/pub/outgoing/argo/ar_index_global_meta.txt'

	ftp_download(global_prof_filename,dummy=False)
	ftp_download(global_meta_filename,dummy=False)

	df_ = pd.read_csv(global_meta_filename.split('/')[-1],skiprows=8)
	df_['wmo_id']=[_[1].split('/')[1] for _ in df_.file.iteritems()]
	with open('position_system_list','rb') as fp:
		position_system_list = pickle.load(fp)
	wmo_list, position_list = zip(*position_system_list)
	df_query = df_[~df_['wmo_id'].isin(wmo_list)]
	for k,token in enumerate(df_query['file'].iteritems()):
		print('Hi Susan, im working on file '+str(k)+' of '+str(len(df_)))
		file = '/pub/outgoing/argo/dac/' + token[1]
		ftp_download(file)
		ncfid = Dataset('dummy')
		float_id = ncfid.variables['PLATFORM_NUMBER'][:]
		try:
			float_id = ''.join([_.decode("utf-8") for _ in float_id.data[~float_id.mask].tolist()])
		except AttributeError:
			float_id = ''.join([_.decode("utf-8") for _ in float_id.data[~float_id.mask].tolist()[0]])

		pos_system = ncfid.variables['POSITIONING_SYSTEM'][:]
		try:
			pos_system = ''.join([_.decode("utf-8") for _ in pos_system.data[~pos_system.mask].tolist()])
		except AttributeError:
			pos_system = ''.join([_.decode("utf-8") for _ in pos_system.data[~pos_system.mask].tolist()[0]])

		position_system_list.append((float_id,pos_system))
		if (token[0]%100)==0:
			with open('position_system_list', 'wb') as fp:
			    pickle.dump(position_system_list, fp)
	with open('position_system_list', 'wb') as fp:
	    pickle.dump(position_system_list, fp)
	position_type_dict = dict(position_system_list)
	df_ = pd.read_csv(os.path.basename(global_prof_filename),skiprows=8)
	df_ = df_.dropna(subset=['date'])
	df_['date'] = [int(_) for _ in df_.date.values]
	df_['date'] = pd.to_datetime(df_.date,format='%Y%m%d%H%M%S')
	df_['Cruise'] = [dummy.split('/')[1] for dummy in df_['file'].values]
	df_ = df_[['Cruise','date','latitude','longitude']]
	df_ = df_.sort_values(by=['Cruise','date'])
	df_ = df_[df_.longitude!=99999]
	df_ = df_[df_.longitude!=-999]
	df_ = df_[df_.longitude<=180]
	df_['SOCCOM'] = df_.Cruise.isin(wmoID_list)
	df_['Position Type']=[position_type_dict[_[1]] for _ in df_.Cruise.iteritems()]
	df_.loc[df_['Position Type']=='IRIDIUM','Position Type']='GPS'
	df_.loc[df_['Position Type']=='GPSIRIDIUM','Position Type']='GPS'
	df_.loc[df_['Position Type']=='IRIDIUMGPS','Position Type']='GPS'
	df_.loc[df_['Position Type']=='GTS','Position Type']='GPS'
	df_.loc[df_['Position Type']=='ARGOS','Position Type']='ARGOS'
	df_ = df_[df_['Position Type'].isin(['GPS','ARGOS'])]
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


print(args)

lllon = args.lllon
lllat = args.lllat
urlon = args.urlon
urlat = args.urlat
df = pd.concat([df,pd.DataFrame({'Cruise':'BOX','latitude':[lllat,urlat,urlat,lllat,lllat],'longitude':[lllon,lllon,urlon,urlon,lllon],'SOCCOM':[True,True,True,True,True]})])

if urlon<lllon:
	df['longitude']=wrap_lon360(df['longitude'].values)
	urlon = wrap_lon360(urlon)[0]
	lllon = wrap_lon360(lllon)[0]

assert lllat<urlat, "lllat must be less than urlat"
assert lllon<urlon, "lllon must be less than urllon"
assert lllat!=urlat, "The latitudes cannot be the same"
assert lllon!=urlon, "The longitudes cannot be the same"
assert (abs(urlon-lllon)<180)|(abs(wrap_lon360(urlon)[0]-lllon)<180), "the box can only be 180 degrees big"

if urlon<lllon:
	df['longitude']=wrap_lon360(df['longitude'].values)
	urlon = wrap_lon360(urlon)[0]
	lllon = wrap_lon360(lllon)[0]

df_holder = df[(df.latitude>=lllat)&(df.latitude<=urlat)]
cruise_list = df_holder[(df_holder.longitude<=urlon)&(df_holder.longitude>=lllon)].Cruise.unique()
df = df[df.Cruise.isin(cruise_list)]

if args.SOCCOM:
	print('Only SOCCOM trajectories will be plotted')
	df = df[df.SOCCOM==True]

if args.iridium:
	print('Only IRIDIUM trajectories will be plotted')
	df = df[df['Position Type']=='GPS']

if args.ARGOS:
	print('Only argos trajectories will be plotted')
	df = df[df['Position Type']=='ARGOS']

if args.full_traj:
	print('Full trajectories are included in the plots')
elif args.forward:
	print('Only trajectories starting in the box are included in the plots')
	frames = []
	for df_holder in [df[df.Cruise==dummy] for dummy in df.Cruise.unique()]:
		if df_holder.Cruise.isin(['BOX']).any():
			frames.append(df_holder)
			continue
		index = df_holder[(df_holder.latitude>=lllat)&(df_holder.latitude<=urlat)&(df_holder.longitude<=urlon)&(df_holder.longitude>=lllon)].index.min()
		df_holder = df_holder[df_holder.index>=index]
		if args.years:
			change = datetime.timedelta(days = int(365*args.years[0]))
			df_holder = df_holder[df_holder.date<(df_holder.date.min()+change)]
		frames.append(df_holder)
	df = pd.concat(frames)
elif args.reverse:
	print('Only trajectories ending in the box are included in the plots')
	frames = []
	for df_holder in [df[df.Cruise==dummy] for dummy in df.Cruise.unique()]:
		if df_holder.Cruise.isin(['BOX']).any():
			frames.append(df_holder)
			continue
		index = df_holder[(df_holder.latitude>=lllat)&(df_holder.latitude<=urlat)&(df_holder.longitude<=urlon)&(df_holder.longitude>=lllon)].index.min()
		df_holder = df_holder[df_holder.index<=index]
		if args.years[0]>0:
			change = datetime.timedelta(days = int(365*args.years[0]))
			df_holder = df_holder[df_holder.date>(df_holder.date.max()-change)]
		frames.append(df_holder)
	df = pd.concat(frames)
else:
	print ('Must specify forward, reverse, or full flags')
	raise

if args.years:
	print('Only trajectories '+str(args.years[0]) +' years from first entering box are included in the plots')

df['longitude']=wrap_lon180(df['longitude'].values)
urlon = wrap_lon180(urlon)[0]
lllon = wrap_lon180(lllon)[0]
plot_the_cruises(df)
