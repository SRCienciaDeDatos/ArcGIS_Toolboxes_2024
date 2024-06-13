# Librerias
import arcpy
from shapely.geometry import MultiLineString
from folium import plugins
import geopandas as gpd
import pandas as pd
import warnings
import folium
import os
import sys

warnings.filterwarnings("ignore")

arcpy.env.overwriteOutput =True
aprx = arcpy.mp.ArcGISProject("CURRENT")


# ---------------------------------------------- 1) Obtención de los inputs ---------------------------------------------- #

# 1.1) CAPA DE ORDENES Y SUS PARAMETROS
capa_ordenes = arcpy.GetParameterAsText(0) # Nombre de la capa de ordenes
fechas_ordenes = arcpy.GetParameterAsText(1) # Columna de fecha/dias
name_ordenes = arcpy.GetParameterAsText(2) # Columna de Name ordenes
description_ordenes = arcpy.GetParameterAsText(3) # Description ordenes
service_time = arcpy.GetParameterAsText(4) # Service time
start_time_orders = arcpy.GetParameterAsText(5) # Ventana de inicio
end_time_orders = arcpy.GetParameterAsText(6) # Ventana de cierre
secuencia_orders = arcpy.GetParameterAsText(7) # Secuencia definida


# 1.2) CAPA DE DEPOT Y SUS PARAMETROS
capa_depot = arcpy.GetParameterAsText(8) # Capa DEPOT
name_depot = arcpy.GetParameterAsText(9) # Nombre del DEPOT (ID)
description_depot = arcpy.GetParameterAsText(10) # Descripcion del DEPOT
start_time_depot = arcpy.GetParameterAsText(11) # Ventana inicio DEPOT
end_time_depot = arcpy.GetParameterAsText(12) # Ventana cierre DEPOT

# 1.3) CAPA DE RUTAS Y SUS PARAMETROS
capa_rutas = arcpy.GetParameterAsText(13) # Nombre de la capa de ruta
name_routes = arcpy.GetParameterAsText(14) # Nombre de la columnan de name  ruta
description_routes = arcpy.GetParameterAsText(15) # Description de  rutas
star_depot_name = arcpy.GetParameterAsText(16) # Start depot name
end_depot_name = arcpy.GetParameterAsText(17) # End depot name
start_time_routes = arcpy.GetParameterAsText(18) # Start time Routes
max_total_time = arcpy.GetParameterAsText(19) # Max total time
max_orders_count = arcpy.GetParameterAsText(20) # Maximo de ordenes por ruta

# 1.4) ORDENES ESPECIALIZADAS Y SUS PARAMETROS
capa_ordenes_especializadas = arcpy.GetParameterAsText(21)  # Nombre de la capa de ordenes epsecializadas
name_ordenes_specialized = arcpy.GetParameterAsText(22)  # Nombre de ordenes especializadas
especialidad_ordenes = arcpy.GetParameterAsText(23)  # Nombre de la especializada requerida por la orden
fechas_ordenes_especializadas = arcpy.GetParameterAsText(24)  # Columna del dia/fecha  de las ordenes especializadas

# 1.5) RUTAS ESPECIALIZADAS Y SUS PARAMETROS
capa_rutas_especializdas = arcpy.GetParameterAsText(25)
name_routes_especializadas = arcpy.GetParameterAsText(26)
especialidad_rutas = arcpy.GetParameterAsText(27)
fechas_rutas_especializadas = arcpy.GetParameterAsText(28)

# 1.6) DIRECCION DE EXPORTACION
direccion_exportacion = fr"{arcpy.GetParameterAsText(29)}"

# 1.7) WORKSPACE (GEODADATABASE)
work_space = arcpy.GetParameterAsText(30)

#  1.8) RED LOCAL
network_source = arcpy.GetParameterAsText(31)
local_network = arcpy.GetParameterAsText(32)
modalidad = arcpy.GetParameterAsText(33)

# 1.9) MODO DE EJECUCION
ejecution_mode  = arcpy.GetParameterAsText(34)

# 1.10) UNIDADES
distannce_units = arcpy.GetParameterAsText(35)
time_units = arcpy.GetParameterAsText(36)

# 1.11) IDIOMA
idioma = arcpy.GetParameterAsText(37)
if idioma == "Español":
    nombre_idioma_ordenes = "Órdenes"
    nombre_idioma_rutas = "Rutas"
else:
    nombre_idioma_ordenes = "Orders"
    nombre_idioma_rutas = "Routes"

# ---------------------------------------------- 2) Impresión de Parámetros ---------------------------------------------- #

# 2. 1) Parametros de orderes
arcpy.AddMessage("Capa de ordenes: {}".format(capa_ordenes))
arcpy.AddMessage("Columna de fecha/dia: {}".format(fechas_ordenes))
arcpy.AddMessage("Columna nombre de ordenes: {}".format(name_ordenes))
arcpy.AddMessage("Columna descrición de ordenes: {}".format(description_ordenes))
arcpy.AddMessage("Columna tiempos de servicio de ordenes: {}".format(service_time))
arcpy.AddMessage("Columna tiempos de Start Windows Orders: {}".format(start_time_orders))
arcpy.AddMessage("Columna tiempos de End Windows Orders: {}".format(end_time_orders))
arcpy.AddMessage("Columna de secuencia Orders: {}".format(secuencia_orders))

# 2.2) Parametros DEPOT
arcpy.AddMessage("Capa DEPOT: {}".format(capa_depot))
arcpy.AddMessage("Columna name DEPOT: {}".format(name_depot))
arcpy.AddMessage("Columna description DEPOT: {}".format(description_depot))
arcpy.AddMessage("Columna start time DEPOT: {}".format(start_time_depot))
arcpy.AddMessage("Columna end time  DEPOT: {}".format(end_time_depot))

# 2.3) Parametros RUTAS
arcpy.AddMessage("Capa de RUTAS: {}".format(capa_rutas))
arcpy.AddMessage("Columna nombre RUTAS: {}".format(name_routes))
arcpy.AddMessage("Columna de description de RUTAS: {}".format(description_routes))
arcpy.AddMessage("Columna de start depot name: {}".format(star_depot_name))
arcpy.AddMessage("Columna de end depot name: {}".format(end_depot_name))
arcpy.AddMessage("Columna de start time de rutas: {}".format(start_time_routes))
arcpy.AddMessage("Columna de Max total time de rutas: {}".format(max_total_time))
arcpy.AddMessage("Columna de Max orders count (rutas): {}".format(max_orders_count))

# 2.4) Ordenes especializadas
arcpy.AddMessage("Nombre de la capa de ordenens especializadas: {}".format(capa_ordenes_especializadas))
arcpy.AddMessage("Columna del nombre de las ordenens especializadas: {}".format(name_ordenes_specialized))
arcpy.AddMessage("Columna de la especialidad de la orden:{}".format(especialidad_ordenes))
arcpy.AddMessage("Columna de la fecha de la orden especializada:{}".format(fechas_ordenes_especializadas))

# 2.5) Rutas especializadas
arcpy.AddMessage("Nombre de la capa de rutas especializadas: {}".format(capa_rutas_especializdas))
arcpy.AddMessage("Columna del nombre de las rutas especializadas: {}".format(name_routes_especializadas))
arcpy.AddMessage("Columna de la especialización por ruta: {}".format(especialidad_rutas))
arcpy.AddMessage("Columna de la fecha de la ruta especializada:{}".format(fechas_rutas_especializadas))

# 2.6) Direccion de exportacion
arcpy.AddMessage("Direcciónn de exportación: {}".format(direccion_exportacion))

# 2.7) Geodatabase
arcpy.AddMessage("Geodatabase: {}".format(work_space))

# 2.8) Network
arcpy.AddMessage("Network Source: {}".format(network_source))
arcpy.AddMessage("Local Network: {}".format(local_network))
arcpy.AddMessage("Modalidad: {}".format(modalidad))

# 2.8) Idioma
arcpy.AddMessage("Idioma seleccionado: {}".format(idioma))

# -------------------------------------------------- 3) Inicio del VRP -------------------------------------------------- #

# 3.1) Obtencion de fechas unicas
# Crea un conjunto vacío para almacenar los valores únicos:
unique_values = set()
#Utiliza la función "arcpy.da.SearchCursor" para recorrer los registros de la capa y agregar los valores únicos a la lista:
with arcpy.da.SearchCursor(capa_ordenes, [fechas_ordenes]) as cursor:
    for row in cursor:
        #unique_values = unique_values + row[0]
        unique_values.add(row[0])

# Impresion del nombre de las fechas unincas
arcpy.AddMessage("Valores únicos: {}".format(unique_values))
aprx = arcpy.mp.ArcGISProject("CURRENT")
arcpy.env.workspace = work_space

# IMPORTANTE: Creacion de  las listas vacias que conncatenran con el método "append" a los data fame generados dentro de los ciclos
# Nota: Una lista puede tenern elementos internos de dataframes
lista_dataframes_ordenes = []
lista_dataframes_rutas = []

# 3.2) Inicio del ciclo
for i in unique_values:
    # 3.1) Creacion de los objetos VRP
    layer_VRP = f"Itinerario_Dia_{i}"  # Nombre del objeto VRP
    # 3.1.x) Parametros generales del VRP en funcion a la red base de eleccion
    if network_source == "Red Local":
        # Creacion del objeto VRP cos sus parametros generales
        result_object = arcpy.na.MakeVehicleRoutingProblemAnalysisLayer(
        network_data_source= local_network,  # URL_servicio, # Es URL cuando es en linea
        layer_name= layer_VRP,
        travel_mode=  modalidad, time_units= time_units,
        distance_units= distannce_units, line_shape="ALONG_NETWORK",
        ignore_invalid_locations="SKIP")

    elif network_source == "Red Online":
        # Creacion del objeto VRP cos sus parametros generales
        result_object = arcpy.na.MakeVehicleRoutingProblemAnalysisLayer(
            network_data_source="https://www.arcgis.com",  # URL_servicio, # Es URL cuando es en linea
            layer_name= layer_VRP,
            #travel_mode= "Car",
            time_units=time_units,
            distance_units=distannce_units, line_shape="ALONG_NETWORK",
            ignore_invalid_locations="SKIP")

    # 3.3) Obtencion de nombre de las subcapas del objeto VRP
    # Get the layer object form the result object. The route layer can now be
    # referenced using the layer object.
    layer_object = result_object.getOutput(0)

    # Get the names of all the sublayers within the VRP layer
    sub_layer_names = arcpy.na.GetNAClassNames(layer_object)

    # Guardamos el nombre de las sub capas del objeto VRP
    orders_layer_name = sub_layer_names["Orders"]
    depots_layer_name = sub_layer_names["Depots"]
    routes_layer_name = sub_layer_names["Routes"]
    routes_especializadas = sub_layer_names["RouteSpecialties"]
    ordenes_especializadas = sub_layer_names["OrderSpecialties"]

# ------------------------------------------------ 4) Carga de las Capas ------------------------------------------------ #
    # 4.1) AGREGAMOS LA SUBCAPA - ORDENES

    # Ejecucion de la seleccion de ordenes por dia de la semana
    arcpy.management.SelectLayerByAttribute(in_layer_or_view=capa_ordenes,
                                            selection_type="NEW_SELECTION",
                                            where_clause=f"{fechas_ordenes} = '{i}'")
    # Parametrización
    candidate_fields = arcpy.ListFields(capa_ordenes)
    order_field_mappings = arcpy.na.NAClassFieldMappings(layer_object, orders_layer_name)
    order_field_mappings["Name"].mappedFieldName = name_ordenes
    order_field_mappings["Description"].mappedFieldName = description_ordenes
    order_field_mappings["ServiceTime"].mappedFieldName = service_time
    order_field_mappings["TimeWindowStart"].mappedFieldName = start_time_orders
    order_field_mappings["TimeWindowEnd"].mappedFieldName = end_time_orders
     # IMPORTANTE. Si queremos que un paraetro tennga un valor constante, tnemos que cambiar de "mappedFieldName" a "defaultValue"

    # Integración a la subcapa de ordenes
    arcpy.na.AddLocations(in_network_analysis_layer= layer_object, sub_layer= orders_layer_name,
                          in_table= capa_ordenes,
                          field_mappings= order_field_mappings,
                          append= "CLEAR" ) # hará que se borre lo anteriormente añadido

    # 4.2) AGREGAMOS LA SUB-CAPA DE DEPOT
    # Parametrización
    depot_field_mappings = arcpy.na.NAClassFieldMappings(layer_object, depots_layer_name)
    depot_field_mappings["Name"].mappedFieldName = name_depot
    depot_field_mappings["Description"].mappedFieldName = description_depot
    depot_field_mappings["TimeWindowStart"].mappedFieldName = start_time_depot
    depot_field_mappings["TimeWindowEnd"].mappedFieldName = end_time_depot

    # Agregamos  los datos  a la sub capa del objeto VRP
    arcpy.na.AddLocations(in_network_analysis_layer=layer_object,
                          sub_layer=depots_layer_name,
                          in_table=capa_depot,
                          field_mappings=depot_field_mappings,
                          append="CLEAR"  # hará que se borre lo anteriormente añadido
                          )

    # 4.3) AGREGAMOS LA SUB-CAPA DE RUTAS
    routes_field_mappings = arcpy.na.NAClassFieldMappings(layer_object, routes_layer_name)

    # Parametros
    routes_field_mappings["Name"].mappedFieldName = name_routes
    routes_field_mappings["Description"].mappedFieldName = description_routes
    routes_field_mappings["StartDepotName"].mappedFieldName = star_depot_name
    routes_field_mappings["EndDepotName"].mappedFieldName = end_depot_name
    routes_field_mappings["MaxOrderCount"].mappedFieldName = max_orders_count
    routes_field_mappings["EarliestStartTime"].mappedFieldName = start_time_routes
    routes_field_mappings["MaxTotalTime"].mappedFieldName = max_total_time

    # Agregamos a la sub capa del objeto  VRP
    arcpy.na.AddLocations(in_network_analysis_layer=layer_object,
                          sub_layer=routes_layer_name,
                          in_table=capa_rutas,
                          field_mappings=routes_field_mappings,
                          append="CLEAR"  # hará que se borre lo anteriormente añadido
                          )
    
    # 4.4)  CAPA DE ORDENENS ESPECIALIZADAS         ####################
    # Al ser una capa opcional la tengo que agregar con una condicionnadante de aparacion
    if len(capa_ordenes_especializadas) > 1:

    # Tenemos que hacer un filtro tambien
        arcpy.management.SelectLayerByAttribute(in_layer_or_view= capa_ordenes_especializadas,
                                                selection_type="NEW_SELECTION",
                                                where_clause=f"{fechas_ordenes_especializadas} = '{i}'")

        ordenes_especializadas_field = arcpy.na.NAClassFieldMappings(layer_object, ordenes_especializadas)

        # Parametros
        ordenes_especializadas_field["OrderName"].mappedFieldName = name_ordenes_specialized
        ordenes_especializadas_field["SpecialtyName"].mappedFieldName = especialidad_ordenes

        # Agregar el depot al mapa
        arcpy.na.AddLocations(in_network_analysis_layer= layer_object,
                              sub_layer= ordenes_especializadas,
                              in_table= capa_ordenes_especializadas,
                              field_mappings= ordenes_especializadas_field,
                              append= "CLEAR") # hará que se borre lo anteriormente añadido

    # 4.5)  CAPA DE RUTAS EPECIALIZADAS        ###########
    # Al ser unan capa opcional la tenngo que poner dentro de una condicionannte
    if len(capa_rutas_especializdas) > 1:

        # Tenemos que hacer un filtro tambien
        arcpy.management.SelectLayerByAttribute(in_layer_or_view=capa_rutas_especializdas,
                                                selection_type="NEW_SELECTION",
                                                where_clause=f"{fechas_rutas_especializadas} = '{i}'")

       # Capa de la cual obtendremos los datos
        routes_especializadas_field = arcpy.na.NAClassFieldMappings(layer_object, routes_especializadas)

        # Parámetros
        routes_especializadas_field["RouteName"].mappedFieldName = name_routes_especializadas
        routes_especializadas_field["SpecialtyName"].mappedFieldName = especialidad_rutas

        # Agregar el location al layer general del VRP
        arcpy.na.AddLocations(in_network_analysis_layer=layer_object,
                              sub_layer=routes_especializadas,
                              in_table=capa_rutas_especializdas,
                              field_mappings=routes_especializadas_field,
                              append="CLEAR")  # hará que se borre lo anteriormente añadido

    # 4.6) SAVE AS A LAVEYER
    folder_path_layers = direccion_exportacion + "\\Layers"

    # Verifica si la carpeta ya existe
    if not os.path.exists(folder_path_layers):
        # Si no existe, crea la carpeta
        os.makedirs(folder_path_layers)

    # Save the solved VRP layer as a layer file on disk with relative paths
    output_layer_file = folder_path_layers +  f"\\Itinerario {i}.lyrx" # Le damos una direccion y nombre de archivo a exportacion
    arcpy.management.SaveToLayerFile(layer_object, output_layer_file, "RELATIVE") # lo exportamos
    aprxMap = aprx.listMaps()[0]  # me tomara el primer mapa que tenga
    layer_obj = arcpy.mp.LayerFile(output_layer_file) # la integramos al mapa
    aprxMap.addLayer(layer_obj) # la integramos al mapa


    # 4.7) RESOLVER CAPA VRP
    if ejecution_mode == "Ejecución manual":
        print("Ejecución manual")

    elif ejecution_mode == "Ejecución automática":
        arcpy.na.Solve(in_network_analysis_layer=layer_object, ignore_invalids="SKIP") # siguiente parametro: (terminate_on_solve_error="CONTINUE") en caso de que se quiera que se continue apesar de errores en algunos datos

    # 4.7.1) Agregamos un campo nuevo a la capa de ordenes y de rutas
        arcpy.management.CalculateField(fr"Itinerario_Dia_{i}\{nombre_idioma_ordenes}", "Dia", f'"{i}"', "PYTHON3", '', "TEXT",
                                        "NO_ENFORCE_DOMAINS")

        arcpy.management.CalculateField(fr"Itinerario_Dia_{i}\{nombre_idioma_rutas}", "Dia", f'"{i}"', "PYTHON3", '',
                                        "TEXT",
                                        "NO_ENFORCE_DOMAINS")


    # 4.7.2) EXPORTACION DE LA CAPA RUTAS
        folder_path_trazo = direccion_exportacion + f"\\Trazo"

        # Verifica si la carpeta ya existe
        if not os.path.exists(folder_path_trazo):
            # Si no existe, crea la carpeta
            os.makedirs(folder_path_trazo)

        # Exportacion de la capa rutas
        arcpy.conversion.ExportFeatures(in_features = f"Itinerario_Dia_{i}/{nombre_idioma_rutas}",
                                        out_features = rf"{folder_path_trazo}" + f"/Trazo dia {i}")

# -------------------------------------------- 5) Mapas y Resumenes por Ruta -------------------------------------------- #

       # 5.1) Geneeracion de 2 columas nuevas de geoemtria, latitud y longitud a la capa de ordenes
        arcpy.management.CalculateGeometryAttributes(in_features=fr"Itinerario_Dia_{i}\{nombre_idioma_ordenes}",
                                                     geometry_property="Latitud POINT_Y;Longitud POINT_X",
                                                     coordinate_system='PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]',
                                                     coordinate_format="DD"
                                                     )

        # 5.2) EXTRACCION DE LA TABLA DE ATRIBUTOS  DE ORDENES A UN DF: Pasar de la tabla de atributos de la capa de ordenes a un pandas dataframe de cada layer
        tabla_atributos_ordenens = f"Itinerario_Dia_{i}/{nombre_idioma_ordenes}"

        # 5.2.1) DF Ordenes: Convierte la tabla de atributos a un Pandas DataFrame
        data = [row for row in arcpy.da.SearchCursor(tabla_atributos_ordenens, "*")]
        df_ordenes = pd.DataFrame(data, columns=[f.name for f in arcpy.ListFields(tabla_atributos_ordenens)])

        # Utilizamos el método append para meter al data frame de ordenes en un lista, esta lista contendra todos los datafarmre generados de ordennens  del ciclo
        lista_dataframes_ordenes.append(df_ordenes)

        # 5.3) EXTRACCION DE LA TABLA DE ATRIBUTOS DE RUTAS A UN DF
        tabla_atributos_rutas = f"Itinerario_Dia_{i}/{nombre_idioma_rutas}"

        data = [row for row in arcpy.da.SearchCursor(tabla_atributos_rutas, "*")]
        df_rutas = pd.DataFrame(data, columns=[f.name for f in arcpy.ListFields(tabla_atributos_rutas)])

        # Utilizamos el método append para meter al data frame de ordenes en un lista, esta lista contendra todos los datafarmre generados de ordennens  del ciclo
        lista_dataframes_rutas.append(df_rutas)

        # 5.4) Lectura de ordenens y trazo de rutas, esto sigue estando para todas las rutas, esto se usara para la consturccion del mapa HTML
        gdf = gpd.read_file (folder_path_trazo + f"\\Trazo dia {i}.shp", crs="epsg:4326")
        gdf = gdf.to_crs(epsg=4326)

        # 5.5) Construccion del mapa
        # Idenntificacionn nde las rutas presentnes en este dia
        df_ordenes_sin_na = df_ordenes.copy()
        df_ordenes_sin_na.dropna(subset=["RouteName"], inplace=True)
        rutas_totales = list(df_ordenes_sin_na["RouteName"].drop_duplicates())

        # Iniciamos el ciclo para ir ruta por ruta
        for z in rutas_totales:
            # Selecionamos el geopandas datafrme por la ruta
            gdf_ruta = gdf[gdf["Name"] == f"{z}"]
            # Generamos una tabla con las líneas separadas
            gdf_lineas = gdf_ruta.explode()
            # Seleccionar todas las filas excepto la primera y la última
            gdf_lineas = gdf_lineas.iloc[1:-1]
            # Ya eliminadas las líneas que involucran la UNE, agrupamos
            linea = gdf_lineas.groupby("Name")
            # Convertir la serie de objetos "LineString" en objetos "Multilinestring"
            linea = linea.geometry.apply(lambda x: MultiLineString(x.tolist())).reset_index()

            # Seleccion del itinerario de cada ruta
            df_ordenes_ruta = df_ordenes_sin_na[df_ordenes_sin_na["RouteName"] == z]

            #  Seleccion del resumen de cada ruta
            df_rutas_por_ruta = df_rutas[df_rutas ["Name"] == z]

            # Especifica la ruta de la carpeta que deseas verificar
            folder_path_rutas_dia = direccion_exportacion + f"\\Ruta {z}\\Dia {i}"

            # Verifica si la carpeta ya existe
            if not os.path.exists(folder_path_rutas_dia):
                # Si no existe, crea la carpeta
                os.makedirs(folder_path_rutas_dia)

            # Exportacion del itinerario por ruta por dia
            df_ordenes_ruta.sort_values(by=["RouteName", "Dia", "Sequence"], ascending=True, inplace=True)
            df_ordenes_ruta.to_excel(folder_path_rutas_dia + f"\\Itinerario Ruta {z} Dia {i}.xlsx", index=False)

            # Exportacion ndel resumenn por ruta
            df_rutas_por_ruta.to_excel(folder_path_rutas_dia + f"\\Resumen Ruta {z} Dia {i}.xlsx", index=False)

            # INICIO DE LA CONSTRUCCION DEL MAPA
            lat_mean = df_ordenes_ruta["Latitud"].mean()
            lon_mean = df_ordenes_ruta["Longitud"].mean()

            titulo = f'Ruta {z}, Dia {i}'
            title_html = '''<h3 align="center" style="font-size:16px"><b>{}</b></h3>'''.format(titulo)
            # Creamos el feature group donde se cargaran los puntos
            feature_group = folium.FeatureGroup(str(z)) # Es el nombre de la RUTA
            # Centramos el mapa por los centroides generados
            mapa = folium.Map(location=[lat_mean, lon_mean], tiles="OpenStreetMap", zoom_start=14)

            for row in df_ordenes_ruta.itertuples():
                # Integracion de informacion a cada punto
                html = f"""
                        <h2>  Itinerario </h2>
                        <p> Ruta: {row.RouteName}  </p>
                        <p> Secuencia de visita: {row.Sequence}  </p>
                        <p> ID cliente: {row.Name}  </p>
                        """
                iframe = folium.IFrame(html=html, width=210, height=250)
                popup = folium.Popup(iframe, max_width=650)

                # Integramos un marcado para cada punto
                folium.Marker(location=[row.Latitud, row.Longitud], popup=popup,
                              icon=plugins.BeautifyIcon(icon="arrow-down", icon_shape="marker",
                                                        number=row.Sequence,
                                                        background_color="#ff7075",
                                                        border_width=0  # Ancho del borde del icono
                                                        )).add_to(feature_group)
            # Integramos el trazo de la ruta
            for l in gdf_lineas.geometry:
                coordenadas = list([(p[1], p[0]) for p in l.coords])
                folium.PolyLine(locations=coordenadas, color='blue').add_to(mapa)


            # Agregamos los features (puntos) al mapa
            feature_group.add_to(mapa)

            # Agregamos el título
            mapa.get_root().html.add_child(folium.Element(title_html))
            folium.LayerControl().add_to(mapa)
            # mapa.fit_bounds([sw, ne])

            # Guardamos mapa
            mapa.save(folder_path_rutas_dia + f"\\Mapa Ruta {z} Dia {i}.html")

# 5.3) Exportacion del datadrame global de itinerario y puntos no asinngados:
# Esto se tiene que hacer fuera del ciclo for, pero tendrá una condicionante
if ejecution_mode == "Ejecución automática":

    # Genneramos un DF vacio con el nombre de las columnas
    df_ordenes_global = pd.DataFrame(columns=df_ordenes.columns)
    df_rutas_global  =  pd.DataFrame(columns=df_rutas.columns)

    for z in range(0, len(lista_dataframes_ordenes)):
        # 4.3.1) Exportacionn de ordenens globales
        df_ordenes_por_dia = lista_dataframes_ordenes[z]
        df_ordenes_por_dia = pd.DataFrame(df_ordenes_por_dia)
        df_ordenes_por_dia.reset_index(drop=True, inplace=True)

        # Concatenamos los dataframes de los resultados por día de la semana en un DF global
        df_ordenes_global = pd.concat(objs=[df_ordenes_global, df_ordenes_por_dia], axis=0, ignore_index=True)

        # Identificaciónn y exportación de los clientes sin ruta asingnada
        puntos_no_asignados = df_ordenes_global[df_ordenes_global["RouteName"].isna()]
        puntos_no_asignados.to_excel(direccion_exportacion + "\\Puntos no asignados.xlsx", index=False)


        # Exportacion del DF global de ordenes, solo
        df_ordenes_global.dropna(subset=["RouteName"], inplace=True)

        # Ordenar por secuencia y ruta
        df_ordenes_global.sort_values(by=["RouteName", "Dia", "Sequence"], ascending=True, inplace=True)
        df_ordenes_global.to_excel(direccion_exportacion + "\\Itinerario global.xlsx", index=False)


        # 4.3.2) Exportacion de rutas globales
        df_rutas_por_dia = lista_dataframes_rutas[z]
        df_rutas_por_dia = pd.DataFrame(df_rutas_por_dia)
        df_rutas_por_dia.reset_index(drop=True, inplace=True)

        # Concatenamos los dataframes de los resultados por día de la semana en un DF global
        df_rutas_global = pd.concat(objs=[df_rutas_global, df_rutas_por_dia], axis=0, ignore_index=True)

        # Exportacionn
        df_rutas_global.to_excel(direccion_exportacion + "\\Resumen global de rutas.xlsx", index=False)

# Detiene la ejecución del código aquí
sys.exit()

## NOTAS:
# IMPORTANTE. Si queremos que un paraetro tennga un valor constante, tnemos que cambiar de "mappedFieldName" a "defaultValue"
