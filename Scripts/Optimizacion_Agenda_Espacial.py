# Librerias
import os
import arcpy
import warnings
import numpy as np
import pandas as pd
from k_means_constrained import KMeansConstrained
import routingpy

# Quitamos los warnings
warnings.filterwarnings("ignore")

# Haciendo que se pueda sobrescribir el Geodatabase
arcpy.env.overwriteOutput = True

# NOTA: Esto modificara los dias de atencion, lo que se quiere es que se respete la frecuencia, pero el dia al que está sujeto la visita de un cliente puede cambiar


#########################             1) OBTENCION DE LOS PARAMETROS DE ENTRADA                                ###############################

# Los siguientes parámetros son fijos, son las distintas combinaciones de visitas por semana que se pueden asignar a cada cliente en funcion a la frecuencia por semana

# 1.1) Combinación de visitas por frecuencia
combinacion_visitas  = {
    "1": ["L", "M", "R", "J", "V", "S"],        # 1 vez por semana
    "2": ["L-J", "M-V", "R-S"],         # 2 visitas por semana (hay 3 combinaciones posibles)
    "3": ["L-R-V", "M-J-S"],   # 3 veces por semana
    "4": ["L-M-R-J", "M-R-J-V"],  # 4 veces por semana
    "5": ["L-M-R-J-V", "M-R-J-V-S"]  # 5 veces por semana
}

# 1.2) Frecuencias que entraran dentro del cluster
frecuencias = [3,2,4,5] # Yo voy a poner las frecuencias, esmpezaremos con la de 3 y 2 que son las más imporantes, todas las demass las usaremos para balancear cada dia



# 1.3)  Obteniendo los parámetros del toolbox

Capa = arcpy.GetParameterAsText(0)
ID_Cliente = arcpy.GetParameterAsText(1)
Ruta = arcpy.GetParameterAsText(2)
Frecuencia = arcpy.GetParameterAsText(3)
Latitud = arcpy.GetParameterAsText(4)
Longitud = arcpy.GetParameterAsText(5)
lunes = arcpy.GetParameterAsText(6)
martes = arcpy.GetParameterAsText(7)
miercoles = arcpy.GetParameterAsText(8)
jueves = arcpy.GetParameterAsText(9)
viernes = arcpy.GetParameterAsText(10)
sabado = arcpy.GetParameterAsText(11)
sujeto_a_cambios = arcpy.GetParameterAsText(12) # es un valor de "Si" o "No"
path_exp = arcpy.GetParameterAsText(13)


# 1.4)  Impresion de parámetros
arcpy.AddMessage("Capa selecionada: {}".format(Capa))
arcpy.AddMessage("Columna ID Cliente: {}".format(ID_Cliente))
arcpy.AddMessage("Columna Ruta: {}".format(Ruta))
arcpy.AddMessage("Columna Frecuencia: {}".format(Frecuencia))
arcpy.AddMessage("Columna Latitud: {}".format(Latitud))
arcpy.AddMessage("Columna Longitud: {}".format(Longitud))
arcpy.AddMessage("Columna Lunes: {}".format(lunes))
arcpy.AddMessage("Columna Martes: {}".format(martes))
arcpy.AddMessage("Columna Miercoles: {}".format(miercoles))
arcpy.AddMessage("Columna Jueves: {}".format(jueves))
arcpy.AddMessage("Columna Viernes: {}".format(viernes))
arcpy.AddMessage("Columna Sábado: {}".format(sabado))
arcpy.AddMessage("Sujeto a Cambios: {}".format(sujeto_a_cambios))
arcpy.AddMessage("Dirección de exportación: {}".format(path_exp))





##########################                          2)  TRATAMIENTO DE DATOS                            ######################


# 2.1) Pasamos la tabla de atributos de la capa a un pandas DF
data = [row for row in arcpy.da.SearchCursor(Capa, "*")]
clientes = pd.DataFrame(data, columns=[f.name for f in arcpy.ListFields(Capa)])

# Nos aseguramos que ciertas columnas tengan el correcto tipo de variable
clientes[f"{Latitud}"] = clientes[f"{Latitud}"].astype(float)
clientes[f"{Longitud}"] = clientes[f"{Longitud}"].astype(float)
clientes[f"{sujeto_a_cambios}"] = clientes[f"{sujeto_a_cambios}"].astype(str)

# 2.2) Homogenizamos la columna de sujeto a cambios: esto lo haremo usando la funcion de apply de pandas
def homogenizacion(string):
    string = string.replace(" ", "")  # Elimino espacios en blanco
    string = string.lower()  #Pasamos todo a minisculas
    return string


# Aplicamos la función
clientes[f"{sujeto_a_cambios}"] = clientes[f"{sujeto_a_cambios}"].apply(func=homogenizacion)


# 2.3) Filtrado de clientes que no estén sujetos a cambios
clientes_sin_cambios  = clientes.copy()
clientes_sin_cambios  = clientes_sin_cambios.query(f'{sujeto_a_cambios}== "no"')
clientes_sin_cambios.reset_index(drop=True, inplace=True)



# 2.4) Filtro de clientes con visita 6 y 1 visita por semana
clientes_seis = clientes.query(f"{Frecuencia} == 6")
clientes_seis.reset_index(drop=True, inplace=True)

clientes_diarios = clientes.query(f"{Frecuencia} == 1")
clientes_diarios.reset_index(drop=True, inplace=True)

# 2.5) Clientes que si estara sujetos a cambios
clientes_sujetos_cambios =  clientes.query(f'{Frecuencia} != 6 & {Frecuencia} != 1 & {sujeto_a_cambios} == "si"') # Hacemos el filtrado de los que si estraran en  el clustering






###################                    3) CLUSTERING DE CLIENTES POR RUTA (frecuencia 2,3,4 y 5)           ##########################


# Lista de rutas (territorios) dentro del DF
rutas = list(clientes_sujetos_cambios[f"{Ruta}"].unique())


# Lista vacia a la que le integraremos todos los DF procesados
lista_clientes = []


# Funcion para la modificacion de los valores de las columa de dias
def actualizar_dias(row):
    dias = {'L': 0, 'M': 0, 'R': 0, 'J': 0, 'V': 0, 'S': 0}
    nuevos_dias = row['Nueva_Agenda'].split('-')
    for dia in nuevos_dias:
        if dia in dias:
            dias[dia] = 1
    return pd.Series([dias['L'], dias['M'], dias['R'], dias['J'], dias['V'], dias['S']])



### 3.1) Inicio del blucle, nos dara los clusters por ruta

## 3.2) Selección ruta a ruta
# Este bucle ira item por item dentro de la lista de rutas:
for i in rutas:
    # Selección solo de los clientes de una ruta en concreto
    clientes_ruta = clientes_sujetos_cambios.query(f"{Ruta}=={i}") # Es como si tuviera un select....

    # 3.3) Selección frecuencia a frecuencia a traves de un bucle
    for j in frecuencias:

        # 3.3.1) Filtro a los clientes de cada frecuencia
        clientes_ruta_frecuencia = clientes_ruta.query(f"{Frecuencia}=={j}") # Es como si tuviera un select....
        clientes_ruta_frecuencia.reset_index(drop=True, inplace=True)

        # 3.3.2) Contabilizamos los clientes por cada frecuencia
        # Condicional a ver si entra al proceso (tiene que tener un mininmo de clientes)
        num_clientes  = len(clientes_ruta_frecuencia)

        # 3.3.3) Codicionante, si los clientes totales son mayor a una "X" cantidad entonces entrarán al proceso de segmentaciín espacial
        if num_clientes >= 10: # establecemos el minimo de clientes por frecuencia

            # 3.3.4) Pasamos las columnes de geolocalización a un numpy array
            # Pasamos las columnas a un array
            X = clientes_ruta_frecuencia[[Latitud, Longitud]].to_numpy()


            # 3.3.5) Establecimiento  de algunos parametros para el modelo

            # Numero de cluster
            if j == 2:          # Si la frecuencia es igual a 2 entonces que el num_clusters = 3
                num_clusters = 3
            elif j == 3:      # Si la frecuencia es igual a 3 entoncees que el num_cluster = 2
                num_clusters = 2
            else: # este seria para los casos de frecuencias 4 y 5
                num_clusters = 2

            # Establecemos minimos y maximo de tamaño por cluster
            clientes_cluster_aprox = num_clientes / num_clusters

            minimo = clientes_cluster_aprox
            minimo = round(minimo)  # redondeo al más cercano
            minimo = minimo - 1

            maximo = clientes_cluster_aprox
            maximo = round(maximo)
            maximo = maximo + 1



            # 3.3.6) Creams el objeto K mean constrained
            # Le otorgamos los parametros necesarios
            clf = KMeansConstrained(
                n_clusters=num_clusters,
                size_min=minimo,
                size_max=maximo,
                random_state=0)

            # 3.3.7) Ejecucion de la predicción
            clf.fit_predict(X)

            # Etiquetas
            etiquetas =  pd.Series(clf.labels_) # lo meto en una Panda Serie
            clientes_ruta_frecuencia["Grupo"] = etiquetas  # lo pongo en una nueva variable


            # ASINGACION DE DIAS A LOS GRUPOS
            grupos = list(clientes_ruta_frecuencia["Grupo"].unique()) # Lista de los ID de los grupos creados

            for q in grupos:
                clientes_ruta_frecuencia_grupo = clientes_ruta_frecuencia.query(f"Grupo=={q}")
                clientes_ruta_frecuencia_grupo["Nueva_Agenda"] = combinacion_visitas[f"{j}"][q]



            # MODIFICACION de  las columnas de días (binarios 0 & 1)
            # Aplicar la función y actualizar el DataFrame
                clientes_ruta_frecuencia_grupo[['L', 'M', 'R', 'J', 'V', 'S']] = clientes_ruta_frecuencia_grupo.apply(actualizar_dias, axis=1)

                # 3.3.8) Integramos el resultado
                lista_clientes.append(clientes_ruta_frecuencia_grupo)
        else:
            print("No hay suficientes clientes")



# 3.4) DF global de clientes procesados , unios los resltados de los clientes con frecuencia 2,3,4 y 5
clientes_procesados = pd.concat(lista_clientes, ignore_index=True)







###############             4) GENERACION DE LOS CENTROIDES POR DIA POR RUTA (CLIENTES YA PROCESADOS)                    #######################

### 4.1) Generación de centroides por día de la semana de los clientes ya agendados

# 4.1.1) Defiinición de la clase padre
class centroides:

###### AQUI, tengo que poiner más bien una columna a la vez con los días de la semana

    # 4.1.2) definimos el método constructor
    def __init__(self, data_set:pd.DataFrame, lat:str, long:str, ruta:str):
        self.data_set = data_set
        self.lat = lat
        self.long = long
        self.ruta = ruta



    # 4.1.3) Definimos el método de obtención de centroides
    def get_centroids(self):

        # Creamos un DF vacio
        centroides_coordenadas = pd.DataFrame(columns=["Ruta", 'Dia', 'Latitud', 'Longitud'])

        rutas =  list(self.data_set[f"{self.ruta}"].unique())
        dias = [f"{lunes}", f"{martes}", f"{miercoles}", f"{jueves}", f"{viernes}", f"{sabado}"]

        # 4.1.4) Creación de un FOR para generar promedios de localización por día de la semana
        for i in rutas:
            clientes_ruta_centroide = self.data_set.query(f"{self.ruta} ==  {i}")
            clientes_ruta_centroide.reset_index(drop=True, inplace=True)


            for j in dias:
                # Hacemos el filtro a clientes por cada dia de la semana
                clientes_dia = clientes_ruta_centroide.query(f"{j} == 1")
                clientes_dia.reset_index(drop=True, inplace=True)

                resultados = {"Ruta":[i],
                              "Dia":[j],
                              "Latitud": [clientes_dia[f"{Latitud}"].mean()],
                              "Longitud": [clientes_dia[f"{Longitud}"].mean()]}

                resultados= pd.DataFrame(data=resultados)

                # Concatenamos
                centroides_coordenadas = pd.concat(objs=[centroides_coordenadas, resultados])

        # Acomodo del DF
        centroides_coordenadas.sort_values(by=["Ruta", "Dia"], ignore_index=True)
        return centroides_coordenadas


# Creación de un objeto
objeto = centroides(data_set=clientes_procesados, lat=f"{Latitud}",
                     long=f"{Longitud}", ruta=f"{Ruta}") # Le definimos los inputs que requiere la clase


# Accedemos al método del objeto
centroides_dia_clientes_procesados = objeto.get_centroids()








#####################             5) GENERACION DE CLUSTERS DE CLIENTES FRECUENCIA 1, POR RUTA             #####################
# Nota: Ahora que tenemos los clusters por día por ruta de los clientes ya procesados (con frecuencia 2,3,4 y 5)  vamos a generare el cluster de los clientes diarios

import math

# Lista con las rutas que tienen clientes diarios
rutas_clnts_frecuencia_uno =  list(clientes_diarios[f"{Ruta}"].unique())

lista_dfs =[]

# 5.1) Filtramos los clientes diarios por cada ruta
for i in rutas_clnts_frecuencia_uno:
    clientes_procesados_frec_uno = clientes_diarios.query(f"{Ruta} == {i}")
    clientes_procesados_frec_uno.reset_index(drop=True, inplace=True)

# 5.2) Generamos clusters uniformes a partir de los clientes diarios en cada ruta
    minimo_clientes_diarios = 6
    num_clientes_frecuncia_uno = len(clientes_procesados_frec_uno)

    if num_clientes_frecuncia_uno > minimo_clientes_diarios:

        num_clusters = 6
        minimo  = num_clientes_frecuncia_uno / 6
        minimo = math.floor(minimo)
        maximo = num_clientes_frecuncia_uno / 6
        maximo = round(maximo)
        maximo = maximo + 1

         # Pasamos los datos de latitud y longitude de los clientes diarios por ruta a un numpy array
        X = clientes_procesados_frec_uno[[Latitud, Longitud]].to_numpy()

        # Creams el objeto K mean constrained
        # Le otorgamos los parametros necesarios
        clf = KMeansConstrained(
            n_clusters=num_clusters,
            size_min=minimo,
            size_max=maximo,
            random_state=0)

        # 3.3.7) Ejecucion de la predicción
        clf.fit_predict(X)

        # Etiquetas
        etiquetas = pd.Series(clf.labels_)  # Extraccion de etiquetas a una serie de pandas

        clientes_procesados_frec_uno["Grupo"] = etiquetas  # lo pongo en una nueva variable

        # Meto el DF generado en una lista
        lista_dfs.append(clientes_procesados_frec_uno)



# Concatenamos todos los DFs de la lista
clientes_procesados_frec_uno = pd.concat(lista_dfs, ignore_index=True) # Uno todos en un mismo DF









##############     6) GENERACION DE CENTROIDES, DE CLIENTEs CON FRECUENCIA = 1 , POR CADA CLUSTER       ###############


lista_dfs = [] # De nuevo una lista vacia

# Clusters
clusters = list(clientes_procesados_frec_uno["Grupo"].unique())

# Rutas
rutas_clnts_frecuencia_uno = list(clientes_procesados_frec_uno[f"{Ruta}"].unique())

for i in rutas_clnts_frecuencia_uno:
    # Aqui ya tengo los clientes de una ruta en particular
    centroides_clientes_frec_uno  = clientes_procesados_frec_uno.query(f"{Ruta} == {i}")
    centroides_clientes_frec_uno.reset_index(drop=True, inplace=True)

    # Ahora filtro por grupo o clusters de cada ruta
    for j in clusters:
        #Diccionario vacio
        diccionario = {}

        centroides_clientes_frec_uno_2 = centroides_clientes_frec_uno.query(f"Grupo == {j}")
        centroides_clientes_frec_uno_2.reset_index(drop=True, inplace=True)

        if not centroides_clientes_frec_uno_2.empty:

            # Generamos la latitud y longitud
            Latitud_centroide = centroides_clientes_frec_uno_2[f"{Latitud}"].mean()
            Longitud_centroide = centroides_clientes_frec_uno_2[f"{Longitud}"].mean()

            # Integramos los datos al diccionario vacio creado anterirotmente
            diccionario [f"{Ruta}"] = [i]
            diccionario["Cluster"] = [j]
            diccionario[f"{Latitud}"] = [Latitud_centroide]
            diccionario[f"{Longitud}"] = [Longitud_centroide]

            # Lo hacemos DF
            centroides_clientes_frec_uno_df = pd.DataFrame(data=diccionario)

            # Integramos el DF a la lista
            lista_dfs.append(centroides_clientes_frec_uno_df)



# Concatenamos
centroides_clientes_frec_uno = pd.concat(objs=lista_dfs, axis=0)





############ AQUI VOY!


exit()



# Exportacion
centroides_clientes_frec_uno.to_csv(path_or_buf=path_exp + "\Frecuencia_uno.csv", index=False)
clientes_procesados_frec_uno.to_csv(path_or_buf=path_exp + "\Clientes procesados frec uno.csv", index=False)






#############               TEST



import pandas as pd

clientes_procesados_frec_uno = pd.read_csv(filepath_or_buffer=r"C:\Users\OMBARRAZA\Desktop\Test\Optimizacion espacial\Clientes procesados frec uno.csv")
clientes_procesados = pd.read_csv(filepath_or_buffer=r"C:\Users\OMBARRAZA\Desktop\Test\Optimizacion espacial\Clientes procesados.csv")


# Procesamiento
clientes_procesados_totales = pd.concat(objs=[clientes_procesados_frec_uno, clientes_procesados] ,ignore_index=True)
# Primero los clientes con

# 6.2) Procesamiento de los datos unidos
# Pasamos todos los valores de longitud y latitud a una lista
#lista_de_coordenadas = clientes_procesados_totales[[Longitud, Latitud]].values.tolist()
lista_de_coordenadas = clientes_procesados_totales[["Longitud", "Latitud"]].values.tolist()



# Generamos los ID (index) de los origenes
origenes = len(clientes_procesados)

indice_origenes = list(range(0,6))   # Modificar esto
indice_destinos = list(range(6,12)) # Modificar esto


# ORS es Open Route Services
# Una lista con 2 lista que serian mi origen - destino
key = "5b3ce3597851110001cf6248078a5dc2d57d4af0b2e8f9367af9c0eb"

# 1) Genero el objeto ORS
api = routingpy.ORS(api_key=key)

# 3) Con el objeto ORS usar la funcion matrix
matrix = api.matrix(locations=lista_de_coordenadas, profile="driving-car",
                    sources=indice_origenes, destinations=indice_destinos)

# Tratamiento de los resultados, lo pasamos a un DF

test= pd.DataFrame(data=matrix.durations, columns=["L", "M", "R", "J", "V", "S"])
test = pd.melt(frame=test, var_name="Dia", value_name="Registro", ignore_index=False)
test["Cluster"] = test.index
test.reset_index(drop=True, inplace=True)

# Ordenamos de menor a mayor
test.sort_values(by=["Registro", "Dia"], inplace=True)



test.to_csv(path_or_buf=path_exp + "\matriz.csv", index=False)
clientes_procesados_totales.to_csv(path_or_buf=path_exp + "\delate.csv", index=False)












#################          6)      COLOCACION DE CLIENTES FRECUENCIA 1 A LOS DEMAS DIAS             ##################

# DESCRIPCION: En esta sección se colocarán los clusters de los clientes de 1 vez por semana con el resto de los clientes ya procesados (clientes con frecuencia 2,3,4 y 5)

## 6.1) Union de los clientes procesados de frecuencia 1 con el resto
# Unimos los DF para tener uno solo con todas las goerreferencias
clientes_procesados_totales = pd.concat(objs=[clientes_procesados_frec_uno, clientes_procesados] ,ignore_index=True)
# Primero van los clientes de frecuencia uno y despues se uno con los clientes de frecuencia 2,3,4 y 5


# Generamos los ID (index) de los origenes
long_origenes = len(clientes_procesados_frec_uno)
long_destinos  = long_origenes + len(clientes_procesados)



indice_origenes = list(range(0,long_origenes))   # Modificar esto
indice_destinos = list(range(long_origenes, long_destinos)) # Modificar esto


# ORS es Open Route Services
# Una lista con 2 lista que serian mi origen - destino
key = "5b3ce3597851110001cf6248078a5dc2d57d4af0b2e8f9367af9c0eb"

# 1) Genero el objeto ORS
api = routingpy.ORS(api_key=key)


clientes_procesados_totales.to_csv(path_or_buf=path_exp + "\delate.csv", index=False)












# Exportación
clientes.to_csv(path_or_buf=path_exp + "\Clientes originales.csv", index=False)
clientes_procesados.to_csv(path_or_buf=path_exp + "\Clientes procesados.csv", index=False)
clientes_sin_cambios.to_csv(path_or_buf=path_exp + "\Clientes sin cambios.csv", index=False)
centroides_dia_clientes_procesados.to_csv(path_or_buf=path_exp + "\Centroides por dias clientes procesados.csv", index=False)
clientes_diarios.to_csv(path_or_buf=path_exp + "\Clientes diarios.csv", index=False)
clientes_procesados_frec_uno.to_csv(path_or_buf=path_exp + "\delete.csv", index=False)
#centroides_clientes_uno.to_csv(path_or_buf=path_exp + "\Centroides clientes diarios.csv", index=False)