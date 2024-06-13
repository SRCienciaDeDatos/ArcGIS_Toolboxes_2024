# Librerías
import os
import arcpy
import pyodbc
import numpy as np
import pandas as pd
from typing import Tuple

# --------------------------------------------------- Clases y Funciones --------------------------------------------------- #

# Clase para obtener los datos
class VisualizacionDatos:
    # Constructor
    def __init__(self) -> None:
        """
        Clase para Visualizar los datos en ArcGIS Pro.
        """
        # Credenciales para la base de datos
        server = "192.168.0.192"
        database = "ASR"
        usuarioDB = "consulta"
        passwordDB = "Consult@"
        # Generación de la conexión
        self.conexion = pyodbc.connect('DRIVER={SQL SERVER};SERVER=' + server +
                                       ';DATABASE=' + database +
                                       ';UID=' + usuarioDB +
                                       ';PWD=' + passwordDB)

    def get_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Método para obtener las tablas de la Base de Datos.

        """
        # Rutas almacen
        rutas_almacen = pd.read_sql("SELECT RUTClave, Tipo, AlmacenID FROM Ruta",
                                    self.conexion)
        # Clientes Coordenadas
        clientes_coords = pd.read_sql("""
                                        SELECT ClienteClave, CoordenadaX, CoordenadaY,
                                        TipoEstado, Calle, Colonia, Localidad, Entidad,
                                        CodigoPostal
                                        FROM ClienteDomicilio
                                      """,
                                      self.conexion)
        # Secuencia
        secuencia = pd.read_sql("""
                                SELECT * FROM Secuencia
                                WHERE FrecuenciaClave in ('0000010', '0000100', '0001000', '0010000', '0100000', '1000000')
                                """
                                ,
                                self.conexion)
        # Cliente UNE
        cliente_UNE = pd.read_sql("""SELECT ClienteClave, AlmacenID, IdFiscal
                                  FROM Cliente""",
                                  self.conexion)
        # Ventana de Tiempo
        ventana_tiempo = pd.read_sql("SELECT ClienteClave, HoraApertura, HoraCierre FROM tmp_VentanaTiempo",
                                     self.conexion)
        # Nombre del cliente
        cliente_nombre = pd.read_sql("""
                                    SELECT c.ClienteClave, c.NombreCorto as ClienteNombre, S.FrecuenciaClave
                                    FROM Cliente c
                                    JOIN Secuencia S on c.ClienteClave = S.ClienteClave
                                    """,
                                     self.conexion)

        # Retornando las tablas
        return rutas_almacen, clientes_coords, secuencia, cliente_UNE, ventana_tiempo, cliente_nombre
    
def crear_df(unes: list, path: str, filtro: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Función para crear los DF de clientes totales, clientes por UNE y la relación entre clientes totales y clientes con coordenadas.
    :return: clientes_totales, clientes_por_UNE, relacion
    """
    # Obteniendo los datos
    rutas_almacen, clientes_coords, secuencia, cliente_UNE, ventana_tiempo, cliente_nombre = VisualizacionDatos().get_data()
    rfc = cliente_UNE[['ClienteClave', 'IdFiscal']]
    # Filtrando por UNEs de interés
    rutas_UNEs = rutas_almacen[rutas_almacen['AlmacenID'].isin(unes)]
    rutas_UNEs.reset_index(drop=True, inplace=True)
    # Nos quedamos con la secuencia de visita
    secuencia = secuencia[secuencia["RUTClave"].isin(rutas_UNEs["RUTClave"])]
    secuencia = secuencia.drop(columns=['SECId', 'Orden', 'MFechaHora', 'MUsuarioID'])
    secuencia.reset_index(drop=True, inplace=True)
    # nos quedamos con los clientes activos
    if filtro == 'TipoEstado':
        clientes = clientes_coords[clientes_coords["TipoEstado"] == 1]
    # Filtramos por los clientes que están en secuencia
    elif filtro == 'Secuencia':
        clientes = clientes_coords.merge(secuencia['ClienteClave'], on='ClienteClave')
    # Nos quedamos con los clientes de las rutas de las UNEs de interés
    cliente_ruta = secuencia[["ClienteClave", "RUTClave"]]
    cliente_ruta.drop_duplicates(subset="ClienteClave", inplace=True)
    clientes = pd.merge(clientes, cliente_ruta, on="ClienteClave", how="left")
    clientes = pd.merge(clientes, rutas_almacen, on="RUTClave", how="left")
    clientes.drop(columns="Tipo", inplace=True)
    clientes = clientes[clientes["RUTClave"].isin(rutas_UNEs["RUTClave"])]
    clientes.reset_index(drop=True, inplace=True)
    # Este DF lo usaré más tarde para agregar los clientes que no tienen coordenada
    # Nos quedamos con los clientes que tienen coordenada
    clientes.reset_index(drop=True, inplace=True)
    clientes_activos = clientes.copy()
    clientes_activos["count"] = 1
    clientes_por_UNE =  clientes_activos.groupby(['AlmacenID'])['count'].sum().reset_index()
    clientes_location = clientes.dropna(subset=["CoordenadaX"])
    clientes_location["count"] = 1
    clientes_georreferencia = clientes_location.copy()
    clientes_activos=  clientes_activos.groupby(['RUTClave'])['count'].sum().reset_index()
    clientes_activos.rename(columns={'count': 'Total Clientes'}, inplace=True)
    clientes_location = clientes_location.groupby(['RUTClave'])['count'].sum().reset_index()
    clientes_location.rename(columns={'count': 'Clientes coordenadas'}, inplace=True)
    # Unir
    relacion = pd.merge(clientes_activos, clientes_location, on="RUTClave", how="left")
    relacion ["% de captura"] = (relacion["Clientes coordenadas"] / relacion["Total Clientes"]) * 100
    # FillNa con ceros
    relacion.fillna(value= 0, inplace=True)
    clientes_sin_coordenadas= clientes[~clientes.ClienteClave.isin(clientes_georreferencia.ClienteClave)]
    clientes_sin_coordenadas.reset_index(drop=True, inplace=True)
    clientes_UNEs =  clientes_georreferencia.groupby(['AlmacenID'])['count'].sum().reset_index()
    clientes_UNEs.rename(columns={'count': 'Clientes coordenadas'}, inplace=True)
    clientes_por_UNE = pd.merge(clientes_por_UNE, clientes_UNEs , on="AlmacenID")
    clientes_por_UNE ["Porcentaje avance"] =  (clientes_por_UNE["Clientes coordenadas"] / clientes_por_UNE["count"])*100
    clientes_por_UNE.rename (columns = {'count':'Cliente totales'}, inplace = True)
    #Fill Na con 0
    clientes_por_UNE.fillna(value=0, inplace=True)
    clientes_georreferencia = pd.merge(clientes_georreferencia , ventana_tiempo, on="ClienteClave", how="left")
    clientes_georreferencia = pd.concat([clientes_georreferencia, clientes_sin_coordenadas], axis=0)
    clientes_totales = clientes_georreferencia.merge(cliente_nombre, on='ClienteClave')
    # Eliminando columnas
    clientes_totales.drop(columns=['TipoEstado', 'count'], inplace=True)
    # Cambiando nombre de las columnas
    clientes_por_UNE.rename(columns={'AlmacenID': 'UNEID'}, inplace=True)
    clientes_por_UNE.columns = ['UNEID', 'Cliente Totales', 'Clientes con Coordenada', '% Captura']
    relacion.rename(columns={'Clientes coordenadas': 'Clientes con Coordenada', '% de captura': '% Captura', 'Total Clientes': 'Clientes Totales', 'Cliente totales':'Clientes Totales'}, inplace=True)
    # Retornando las tablas
    return clientes_totales, clientes_por_UNE, relacion, rfc

def get_clientes(clientes_totales: pd.DataFrame, rfc:pd.DataFrame) -> pd.DataFrame:
    """
    Función para obtener los clientes con sus coordenadas y frecuencias
    :param clientes_totales: DataFrame con los clientes totales
    :return: df_clientes
    """
    # Df con una sola aparición por cliente
    df_clientes = clientes_totales.drop_duplicates(subset=['ClienteClave']).drop(columns=['FrecuenciaClave']).reset_index(drop=True)
    # Lista con las frecuencias
    frec_clave = []
    suma_frec = []
    # Ciclo para movernos por clientes
    for i in clientes_totales['ClienteClave'].unique():
        # Seleccionando las filas del cliente
        temp = clientes_totales[clientes_totales['ClienteClave'] == i].reset_index(drop=True)
        # Creando un diccionario con las posiciones de los días
        dict_posi = {'0': 0, '1': 0, '2': 0, '3': 0, '4': 0, '5': 0, '6': 0}
        # Tomando las frecuencias
        temp_frec = temp['FrecuenciaClave']
        # Ciclo para movernos por las secuencias
        for j in temp_frec.index:
            # Tomando la fila de las secuencias
            fila = temp_frec[temp_frec.index == j][j]
            # Haciendo un número con la posición en la que está el 1
            posi = 0
            # Ciclo para movernos por el str de la fila
            for h in fila:
                # En caso de que el elemento sea '1'
                if h == '1':
                    # Agregamos 1 al diccionario en la posición del día correspondiente
                    dict_posi[f'{posi}'] = 1
                # Siguiente posición
                posi += 1
        suma_frec.append(sum(list(dict_posi.values())))
        # Haciendo un str con todo
        frecuencia_str = ''.join([str(i) for i in list(dict_posi.values())])
        # Agregando a la lista
        frec_clave.append(frecuencia_str)
    # Agregando la lista como columna
    df_clientes['FrecuenciaClave'] = frec_clave
    # Agregando la lista de suma de frecuencia como columna
    df_clientes['FrecuenciaSemanal'] = suma_frec
    # Agregando las columnas de los días
    df_clientes['L'] = [0] * len(df_clientes)
    df_clientes['M'] = [0] * len(df_clientes)
    df_clientes['R'] = [0] * len(df_clientes)
    df_clientes['J'] = [0] * len(df_clientes)
    df_clientes['V'] = [0] * len(df_clientes)
    df_clientes['S'] = [0] * len(df_clientes)
    df_clientes['D'] = [0] * len(df_clientes)
    # Df con las columnas de días rellanadas
    df_dias = pd.DataFrame()
    # Diccionario con los cambios
    dict_dias = {0:'L', 1:'M', 2:'R', 3:'J', 4:'V', 5:'S', 6:'D'}
    # Ciclo para movernos por clientes
    for i in clientes_totales['ClienteClave'].unique():
        # Seleccionando las filas del cliente
        temp = df_clientes[df_clientes['ClienteClave'] == i]
        temp_frec = temp['FrecuenciaClave'].reset_index(drop=True)[0]
        for pos, valor in enumerate(temp_frec):
            if valor == '1':
                dia = dict_dias.get(pos)
                temp[dia] = 1
        # Concatenando la fila
        df_dias = pd.concat([df_dias, temp], axis=0)
    # Cambiando el nombre del DF resultante
    df_clientes = df_dias.copy()
    # Agregando el RFC
    df_clientes = df_clientes.merge(rfc, on=['ClienteClave'])
    # Cambiando nombre de las columnas
    df_clientes.rename(columns={'CoordenadaX': 'Longitud', 'CoordenadaY': 'Latitud', 'AlmacenID': 'UNEID'}, inplace=True)
    # Ordenando las columnas
    df_clientes = df_clientes[['UNEID', 'RUTClave', 'IdFiscal', 'ClienteClave', 'ClienteNombre', 'Calle', 'Colonia', 'Localidad', 'CodigoPostal',
                               'Entidad', 'Latitud', 'Longitud', 'HoraApertura', 'HoraCierre', 'L', 'M', 'R', 'J', 'V', 'S', 'D']]
    # Cambiando el nombre de las columnas
    df_clientes = df_clientes.rename(columns={'UNEID': 'UNE', 'RUTClave': 'Ruta', 'IdFiscal': 'RFC', 'ClienteClave': 'ID Cte', 'ClienteNombre': 'Nombre',
                                              'Localidad': 'Municipio', 'Entidad': 'Estado'})
    # Poniendo las rutas en un formato entendible
    rutas = []
    for i in df_clientes.index:
        temp = df_clientes[df_clientes.index == i].reset_index(drop=True)
        temp_ruta = temp['Ruta'][0]
        rutas.append(int(temp_ruta[4:]))
    df_clientes['Ruta'] = rutas
    # Regresando el resultado
    return df_clientes
    
def agg_csv_mapa(nombre_csv: str, nombre_capa: str, path: str) -> None:
    """
    Función para agregar la tabla a la vista de mapa
    :param nombre_csv: Nombre del archivo CSV
    :param nombre_capa: Nombre de la capa
    :param path: Path donde se encuentra el archivo CSV
    """
    # Especifica la ruta a la geodatabase en la que deseas cargar la capa de puntos
    workspace = fr"{global_path}{nombre_geodatabase}.gdb"
    # Especifica la ruta al archivo CSV que contiene las coordenadas de los clientes
    csv_input = fr"{path}/{nombre_csv}.csv"
    if os.path.exists(csv_input):
        # Especifica el nombre que deseas darle a la capa de puntos
        # Crea una ruta completa para la capa de salida en la geodatabase
        capa_output = arcpy.ValidateTableName(nombre_capa, workspace)
        # Utiliza la herramienta "Make XY Event Layer" para crear una capa de puntos a partir del archivo CSV
        arcpy.MakeXYEventLayer_management(csv_input, "Longitud", "Latitud", nombre_capa)
        # Utiliza la herramienta "Copy Features" para guardar la capa de puntos en la geodatabase
        arcpy.CopyFeatures_management(nombre_capa, workspace + "/" + capa_output)
        # Lo integramos al mapa actual
        aprx = arcpy.mp.ArcGISProject("CURRENT")
        aprxMap = aprx.listMaps()[0]
        aprxMap.addDataFromPath(workspace + "/" + capa_output)
    
# --------------------------------------------------- Ejecución del Código --------------------------------------------------- #

if __name__ == '__main__':
    # Haciendo que todo se pueda sobrescribir
    arcpy.env.overwriteOutput = True
    # Parámetros de entrada
    unes = arcpy.GetParameterAsText(0)
    unes = unes.split(';')  # Creando la lista con las UNE a usar
    path = fr"{arcpy.GetParameterAsText(1)}"  # Path donde se exportarán los resultados

    # Sacando el directorio en el que se ejecuta
    list_dir = (arcpy.mp.ArcGISProject("CURRENT").filePath).split('\\')
    # Nombre del geodatabase
    nombre_geodatabase = list_dir[-1].split('.')[0]
    # Quitando la dirección de la última carpeta
    list_dir.remove(f'{nombre_geodatabase}.aprx')
    # Creando la ruta global
    global_path = '/'.join(list_dir)
    global_path = global_path + '/'
    # Haciendo las variables globales para la clase
    nombre_geodatabase = nombre_geodatabase
    global_path = global_path

    # Obnteniendo los datos de cada filtro
    clientes_totales_secuencia, clientes_por_UNE, relacion, rfc = crear_df(unes=unes, path=path, filtro='Secuencia')
    clientes_totales_TipoEstado, clientes_por_UNE, relacion, rfc = crear_df(unes=unes, path=path, filtro='TipoEstado')

    # Creando el DF de clientes para cada filtro
    df_clientes_secuencia = get_clientes(clientes_totales_secuencia, rfc)
    df_clientes_TipoEstado = get_clientes(clientes_totales_TipoEstado, rfc)

    # En caso de que no exista el path lo crea
    if not os.path.exists(path):
        os.mkdir(path)

    # Exportando las tablas
    relacion.to_csv(fr'{path}\Levantamiento_Coords_Ruta.csv', index=False)
    clientes_por_UNE.to_csv(fr'{path}\Levantamiento_Coords_UNE.csv', index=False)
    df_clientes_secuencia.to_csv(fr'{path}\Clientes_Coords_Secuencia.csv', index=False)
    df_clientes_TipoEstado.to_csv(fr'{path}\Clientes_Coords_TipoEstado.csv', index=False)

    # Agregando los clientes al mapa
    agg_csv_mapa(nombre_csv='Clientes_Coords_Secuencia', 
                 nombre_capa='Clientes_Coords',
                 path=path)
