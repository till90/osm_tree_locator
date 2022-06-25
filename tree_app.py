from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import overpassQueryBuilder, Overpass
import osmnx as ox
import pandas as pd
import geopandas as gpd
from shapely.geometry import MultiPoint
import folium
import panel as pn

pn.extension(template='material', theme='dark')
pn.state.template.param.update(title="OSM Element Locator")

nominatim = Nominatim() # Resolve location
overpass = Overpass() # Querys

def get_tree_map(city, bundesland, land):
    # resolve location name to area id
    areaId = nominatim.query(f'{city}, {land}').areaId()

    #Build the Query
    query = overpassQueryBuilder(area=areaId, elementType='node', selector='"natural"="tree"', out='count', includeCenter=True)
    result = overpass.query(query)
    
    #Create DataFrame from list        
    df = pd.DataFrame({'Stadt' : city, 
                   'Bäume' :  result.countElements(),
                   'json' : [result.toJSON()['elements']]}).dropna()
    #Drop Rows with 0 Values
    df = df[df.Bäume > 0]
    #Create Geometry for Rows
    geometry_list = list()
    geometry_list.append(MultiPoint([(x.get('lon'),x.get('lat')) for x in df.json[0] if x.get('lon') is not None]))
    gdf_b = gpd.GeoDataFrame(df.drop('json', axis=1), geometry=geometry_list)
    gdf_b.to_file(f'/srv/data/tree_app/Bäume_{city}_{bundesland}_{land}.geojson')

    # define the place query
    query = [f'{city},{bundesland},{land}']

    # get the boundaries of the place
    gdf_c = ox.geocode_to_gdf(query)
    gdf_c['Stadt'] =[x.split(',')[0] for x in gdf_c['display_name']]
    gdf_c.to_file(f'/srv/data/tree_app/Staedte_{city}_{bundesland}_{land}.geojson')
    
    m = gdf_c[gdf_c.Stadt == city].explore(#tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=add_your_acces_token_here',
                        #attr='mapbox', 
                        legend=False, 
                        popup = True,
                        tooltip = False,
                        style_kwds={'fillOpacity':0.0, 'weight':4}, 
                        width=1400, height=800)
    
    gdf_b[gdf_b.Stadt == city].explore(column='Bäume', 
                                        m=m, 
                                        legend=False, 
                                        color='lime', 
                                        marker_type='circle_marker', 
                                        style_kwds={'color' : 'lime'}, 
                                        marker_kwds={'radius':1})
    
    m.save(f'/srv/data/tree_app/Bäume_{city}.html')
    
    return pn.Pane(m, width=1400, height=800)


def update_tree_map(event):
    print('start updating map')
    main_t1[0][0] = get_tree_map(city = w_adress.value.split(',')[0], 
                                bundesland = w_adress.value.split(',')[1][1:], 
                                land= w_adress.value.split(',')[2][1:])
    print('finish updating map')

def update_count(event):
    filename = w_adress.value.replace(', ','_')
    gdf = gpd.read_file(f'/srv/data/tree_app/Bäume_{filename}.geojson')
    side_t1[2].value = int(gdf.Bäume.values)
    
w_adress = pn.widgets.TextInput(name='Ort bsp.:[Frankfurt, Hessen, DE]', value='Darmstadt, Hessen, DE')
button = pn.widgets.Button(name = 'Lokation ändern', button_type = 'primary')
count = pn.indicators.Number(value = 5966, format='{value} Trees')
count.background = 'white'
author = pn.pane.HTML('<h2>Author: Till Müller</h2><br><h2>Website: <a href="http://www.enviai.de">enviai.de</a></h2><br><p>Actual only valid within Germany</p><br><p>Auswertung durch © enviai.de <br> Daten von © OpenStreetMap <br> <a href="https://opendatacommons.org/licenses/odbl/">"Open Data"</a></p>')
side_t1 = pn.panel(pn.Column(w_adress, button, count, author ))
side_t1.servable(area = 'sidebar')
element = pn.widgets.Select(name='Element', value='Trees', options=['Trees'])

main_t1 = pn.panel(pn.Column(pn.Row(get_tree_map(city = w_adress.value.split(',')[0], 
                                bundesland = w_adress.value.split(',')[1][1:], 
                                land= w_adress.value.split(',')[2][1:])
                            )))
main_t1.servable(area='main')



button.param.watch(update_tree_map, 'value') #First excecute
button.on_click(update_count) # Second excecute

