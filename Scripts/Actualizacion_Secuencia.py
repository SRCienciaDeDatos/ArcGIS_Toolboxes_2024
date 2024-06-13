# Librerías
import os
import time
import json
import arcpy
import pyodbc
import folium
import warnings
import polyline
import requests
import numpy as np
import pandas as pd
import geopandas as gpd
from typing import Tuple
from folium import plugins
warnings.filterwarnings("ignore")

# URL para la imagen de VROOM
URL = "http://192.168.0.38:3000"

# --------------------------------------------------- Clases y Funciones --------------------------------------------------- #

class CargaDatosClientes:
    def __init__(self, une_list: list = False) -> None:
        """
        Clase que genera los datos necesarios para el VRP
        :param une_list: Lista de STR con los ID de las UNE seleccionadas, en caso de poner ['*'] se seleccionan todas
                         las UNE.
        """
        self.une_list = une_list
        # Creando conexión con la base de datos
        server= "192.168.0.192"
        database = "ASR" 
        usuarioDB= "consulta"
        passwordDB ="Consult@"
        # Generación de la conexión
        try:
            conexion = pyodbc.connect(
                'DRIVER={SQL SERVER};SERVER=' + server + ';DATABASE=' + database + ';UID=' + usuarioDB +
                ';PWD=' + passwordDB)
            self.conexion = conexion
        except Exception as e:
            print("Conexión fallida:", e)
        # Diccionario para cambiar el Día de visita a binario
        self.dia_binario = {'Lunes': '1000000',
                            'Martes': '0100000',
                            'Miercoles': '0010000',
                            'Jueves': '0001000',
                            'Viernes': '0000100',
                            'Sabado': '0000010'}
        # Datos de las UNE
        coordenadas_UNEs = {
            'Ubicaciones': {0: 'UNE Periferico Norte', 1: 'UNE Periferico Sur', 2: 'UNE Periferico Oriente',
                            3: 'UNE Periferico Poniente', 4: 'UNE Zapotlanejo', 5: 'UNE Chapala', 6: 'UNE Ocotlan',
                            7: 'UNE Tequila', 8: 'UNE Acatlan', 9: 'UNE Tepatitlan', 10: 'UNE Ameca',
                            11: 'UNE Autlán', 12: 'UNE Ciudad Guzman', 13: 'UNE Tomatlan',
                            14: 'UNE San Patricio Melaque', 15: 'UNE Colima', 16: 'UNE Tecoman',
                            17: 'UNE Manzanillo', 18: 'UNE Zacapu', 19: 'UNE Uruapan', 20: 'UNE Morelia',
                            21: 'UNE Zitacuaro', 22: 'UNE Aguascalientes', 23: 'UNE Nochistlan', 24: 'UNE Zamora',
                            25: 'UNE Ixtlan', 26: 'UNE Xalisco (Tepic)', 27: 'UNE Las Varas',
                            28: 'UNE Puerto Vallarta', 29: 'UNE Santiago', 30: 'UNE Acaponeta', 31: 'UNE Rosario',
                            32: 'UNE Mazatlan', 33: 'UNE Culiacan II', 34: 'UNE Guamuchil'},
            'latitud': {0: 20.74108812, 1: 20.55779994, 2: 20.67925813, 3: 20.64393476, 4: 20.62248961,
                        5: 20.32805521, 6: 20.39502715, 7: 20.87343535, 8: 20.42073653, 9: 20.86527,
                        10: 20.53983146, 11: 19.78357059, 12: 19.70762739, 13: 19.92406387, 14: 19.22603253,
                        15: 19.23872282, 16: 18.9371016, 17: 19.08800773, 18: 19.82660431, 19: 19.40814262,
                        20: 19.72770077, 21: 19.45230415, 22: 21.80205156, 23: 21.34980247, 24: 20.01699164,
                        25: 21.03674261, 26: 21.42791647, 27: 21.18918204, 28: 20.67920001, 29: 21.81743271,
                        30: 22.47995108, 31: 22.98510235, 32: 23.19361372, 33: 24.61487, 34: 25.47052649},
            'longitud': {0: -103.3972312, 1: -103.3656128, 2: -103.2352661, 3: -103.4446303, 4: -103.0459664,
                        5: -103.137919, 6: -102.7478122, 7: -103.8246571, 8: -103.6271771, 9: -102.72556,
                        10: -104.0341552, 11: -104.3654871, 12: -103.4956165, 13: -105.2639828, 14: -104.7025082,
                        15: -103.7591217, 16: -103.8915852, 17: -104.2881712, 18: -101.7709804, 19: -102.0672934,
                        20: -101.1517022, 21: -100.2911756, 22: -102.2859751, 23: -102.7843966, 24: -102.2840436,
                        25: -104.4000683, 26: -104.8992838, 27: -105.1458711, 28: -105.2454269, 29: -105.1897554,
                        30: -105.3812526, 31: -105.8723719, 32: -106.2776305, 33: -107.24976, 34: -108.1328638},
            'UNEID': {0: 'D001', 1: 'D002', 2: 'D003', 3: 'D004', 4: 'D006', 5: 'D007', 6: 'D040', 7: 'D041',
                    8: 'D042', 9: 'D043', 10: 'D044', 11: 'D045', 12: 'D046', 13: 'D047', 14: 'D048', 15: 'D049',
                    16: 'D050', 17: 'D051', 18: 'D080', 19: 'D081', 20: 'D082', 21: 'D083', 22: 'D085', 23: 'D091',
                    24: 'D095', 25: 'D120', 26: 'D121', 27: 'D123', 28: 'D124', 29: 'D125', 30: 'D126', 31: 'D127',
                    32: 'D128', 33: 'D130', 34: 'D131'}}
        # Pasamos el diccionario a un DF
        self.une_coords = pd.DataFrame(data=coordenadas_UNEs)

    def gen_rut_unes(self) -> pd.DataFrame:
        """
        Método para generar la tabla de rutas de cada UNE. Se toman de la tabla 'frecuencia'
        :return: DF con las claves de las rutas que tiene la UNE.
        """
        # Tabla con la UNE asociada a la ruta (Seleccionamos las dos columnas de la tabla y decimos que solo queremos
        # las UNE que empiecen con 'D###'
        unes_ruta = pd.read_sql("SELECT AlmacenID, AlmacenPadreId FROM Almacen WHERE AlmacenPadreID LIKE 'D___'",
                                self.conexion)
        # Cambiando el Nombre de las columnas
        unes_ruta.rename(columns={'AlmacenID': 'RUTClave', 'AlmacenPadreId': 'UNE_ID'}, inplace=True)
        # Borrando datos nulos
        unes_ruta = unes_ruta.dropna(subset=['UNE_ID']).reset_index(drop=True)
        # Cargando datos de secuencia de cada cliente
        secuencia = pd.read_sql(
            "SELECT ClienteClave, RUTClave, FrecuenciaClave, Orden FROM Secuencia WHERE RUTClave IS NOT NULL",
            self.conexion)
        secuencia['Orden'] = secuencia['Orden'].astype(int)
        # Haciendo un sliding de 'FrecuenciaClave' en una lista de caracteres
        secuencia['FrecuenciaClave'] = secuencia['FrecuenciaClave'].apply(lambda x: [*x])
        # Obteniendo el índice del '1' en la lista
        secuencia['Dia_Visita_Num'] = secuencia['FrecuenciaClave'].apply(lambda x: x.index('1'))
        # Quitando los Domingos (índice 6)
        secuencia = secuencia[secuencia['Dia_Visita_Num'] != 6]
        # Diccionario con el día que corresponde a cada día de la semana
        dic_dias = {0: 'Lunes', 1: 'Martes', 2: 'Miercoles', 3: 'Jueves', 4: 'Viernes', 5: 'Sabado'}
        # Haciendo el cambio con el diccionario
        secuencia['Dia_Visita'] = secuencia['Dia_Visita_Num'].apply(lambda x: dic_dias.get(x))
        # Juntando las dos tablas
        # Tabla con las rutas asociadas a una UNE y sus clientes
        rut_unes = secuencia.merge(unes_ruta, on='RUTClave')
        # Tomando las columnas que queremos y ordenando la tabla
        rut_unes = rut_unes[['UNE_ID', 'RUTClave', 'ClienteClave', 'Dia_Visita', 'Orden']]
        rut_unes = rut_unes.sort_values(['UNE_ID', 'RUTClave', 'Dia_Visita', 'Orden']).reset_index(drop=True)
        # Filtrando por la(s) UNE seleccionada(s)
        rut_unes = rut_unes[rut_unes['UNE_ID'].isin(self.une_list)]
        # Retornando la tabla final
        return rut_unes

    def gen_clientes_coords(self) -> pd.DataFrame:
        """
        Método para generar la tabla con el ClienteClave y las coordenadas de cada uno. Si no tiene coordenada se filtra
        el cliente.
        :return: DF con ClienteClave y coordenadas de los clientes.
        """
        clientes_coords = pd.read_sql("SELECT ClienteClave, CoordenadaX, CoordenadaY FROM ClienteDomicilio "
                                      "WHERE (CoordenadaX IS NOT NULL) AND (CoordenadaY IS NOT NULL)",
                                      self.conexion)
        # Renombrando las columnas a usar
        clientes_coords.rename(columns={'CoordenadaX': 'Longitud', 'CoordenadaY': 'Latitud'}, inplace=True)
        # Retornando la tabla creada
        return clientes_coords
    
    def gen_datos_clientes(self) -> pd.DataFrame:
        """
        Método para generar la tabla con los datos de los clientes
        :return datos_clientes: Obtener los datos de cada cliente clientes
        """
        # Carga de la Tabla
        datos_clientes = pd.read_sql("SELECT ClienteClave, RazonSocial, NombreCorto FROM Cliente", self.conexion)
        # Retornando la tabla
        return datos_clientes
    
    @staticmethod
    def limpieza_ventanas(df_ventanas: pd.DataFrame) -> pd.DataFrame:
        """
        Método para hacer la limpieza de las ventans de tiempo
        :param df_ventanas: DF con las ventanas de tiempo por clientes
        :return df_limpio: DF con las ventanas de tiempo por cliente limpias
        """
        df_limpio = df_ventanas.copy()
        # Función interna para el split y transformación a decimal
        def trans_decimal(dato):
            # Diccionario con los datos
            dict_datos = {'Hora': 0, 'Minutos': 0}
            # Haciendo un split de los datos con ':'
            split_dato = dato.split(':')
            # Checando que la longitu de cada parte sea mayor a 1
            for i in split_dato:
                if len(i) < 1:
                    split_dato.remove(i)
            # Si la longitud es = 1, es decir que solo tenemos la hora
            if len(split_dato) == 1:
                # Agregando la hora al diccionario
                dict_datos['Hora'] = int(split_dato[0])
            # Si la longitud es = 2, es decir tenemos la hora y los minutos
            elif len(split_dato) == 2:
                dict_datos['Hora'] = int(split_dato[0])
                dict_datos['Minutos'] = int(split_dato[1])
            # Else, se pone una hora normal
            else:
                dict_datos['Hora'] = 6
                dict_datos['Minutos'] = 0
            # Haciendo la suma decimal de la hora
            horas_decimal = dict_datos['Hora'] + (dict_datos['Minutos'] / 60)
            # Retornando el decimal
            return horas_decimal
        # Ciclo para movernos por cada ventana
        for tipo_ventana in ['HoraApertura', 'HoraCierre']:
            # Limpiando posibles puntos
            df_ventanas[tipo_ventana] = df_ventanas[tipo_ventana].apply(lambda x: x.replace('.', ':'))
            # Aplicando la limpieza de datos
            df_limpio[tipo_ventana] = df_ventanas[tipo_ventana].apply(lambda x: trans_decimal(x))
        # Retornando el df final
        return df_limpio

    def gen_ventanas_clientes(self) -> pd.DataFrame:
        """
        Método para obtener las ventanas de tiempos de cada cliente
        :return 
        """
        # Ventana de Tiempo
        ventana_tiempo = pd.read_sql("SELECT ClienteClave, HoraApertura, HoraCierre FROM tmp_VentanaTiempo",
                                     self.conexion)
        # Limpiando las ventas
        ventana_tiempo = self.limpieza_ventanas(ventana_tiempo)
        # Retornando la tabla
        return ventana_tiempo

    def gen_clientes(self) -> pd.DataFrame:
        """
        Método para generar una tabla con los datos de los clientes y las coordenadas; se juntan con ClienteClave
        Se llama a los métodos 'gen_datos_clientes' y 'gen_clientes_coords' para juntar las tablas que arrojan.
        :return: Tabla que se junta con los datos de los dos métodos
        """
        # Haciendo un DF final con todas los métodos anteriores de generación
        clientes = (self.gen_datos_clientes()).merge(self.gen_clientes_coords(), on='ClienteClave')
        clientes = clientes.merge(self.gen_rut_unes(), on='ClienteClave')
        # Haciendo que el día de la semana sea categórico con el orden natural
        clientes['Dia_Visita'] = pd.Categorical(clientes['Dia_Visita'],
                                                ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'])
        # Ordenando los valores y reiniciando el índice
        clientes = clientes.sort_values(['UNE_ID', 'RUTClave', 'Dia_Visita']).reset_index(drop=True)
        # Seleccionando las columnas
        clientes = clientes[['UNE_ID', 'RUTClave', 'Dia_Visita', 'ClienteClave', 'RazonSocial', 'NombreCorto',
                             'Longitud', 'Latitud']]
        # Filtrando por la(s) UNE seleccionada(s)
        clientes = clientes[clientes['UNE_ID'].isin(self.une_list)]
        # Filtrando las coordenadas
        clientes = clientes[clientes["Longitud"] <= -86]
        clientes = clientes[clientes["Longitud"] >= -117]
        clientes = clientes[clientes["Latitud"] <= 32]
        clientes = clientes[clientes["Latitud"] >= 15]
        # Cambiando los formatos de las columnas
        clientes['UNE_ID'] = clientes['UNE_ID'].astype(str)
        clientes['RUTClave'] = clientes['RUTClave'].astype(str)
        clientes['Dia_Visita'] = clientes['Dia_Visita'].astype(str)
        clientes['ClienteClave'] = clientes['ClienteClave'].astype(str)
        clientes['RazonSocial'] = clientes['RazonSocial'].astype(str)
        clientes['NombreCorto'] = clientes['NombreCorto'].astype(str)
        clientes['Longitud'] = clientes['Longitud'].astype(float)
        clientes['Latitud'] = clientes['Latitud'].astype(float)
        # Cambiando el Día_Visita a binario
        clientes['FrecuenciaClave'] = clientes['Dia_Visita'].apply(lambda x: self.dia_binario.get(x))
        # Cargando la tabla de ventana de tiempos de cada cliente
        vent_tiempos = self.gen_ventanas_clientes()
        # Juntando la tabla clientes con la ventana de tiempos
        clientes = clientes.merge(vent_tiempos, on='ClienteClave', how='left')
        # Rellenamos nulos con una ventana genérica
        clientes['HoraApertura'] = clientes['HoraApertura'].fillna(6.0)
        clientes['HoraCierre'] = clientes['HoraCierre'].fillna(22.0)
        # Poniendo el formato de fecha que requiere el VRP
        clientes['HoraApertura'] = clientes['HoraApertura'].apply(lambda x: int((x * 3600) + 1600000000))
        clientes['HoraCierre'] = clientes['HoraCierre'].apply(lambda x: int((x * 3600) + 1600000000))
        clientes['HoraCierre'] = clientes['HoraCierre'].apply(lambda x: int((x * 3600) + 1600000000))
        # Ordenando las columnas
        clientes['Dia_Visita'] = pd.Categorical(clientes['Dia_Visita'],
                                                ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado'])
        clientes = clientes.sort_values(['UNE_ID', 'RUTClave', 'Dia_Visita', 'ClienteClave']).reset_index(drop=True)
        # Creando la Columna ID
        clientes['ID'] = clientes.index
        # Haciendo la variable entera
        clientes['ID'] = clientes['ID'].astype(int)
        # Filtrando las columnas
        clientes = clientes[['UNE_ID', 'RUTClave', 'Dia_Visita', 'ID', 'ClienteClave', 'RazonSocial', 'NombreCorto',
                             'Longitud', 'Latitud', 'FrecuenciaClave', 'HoraApertura', 'HoraCierre']]
        # Poniendo un tiempo de servicio de 15 minutos
        clientes['TiempoServicio'] = 15*60 # BORRAR ESTA LINEA
        # Retornando tabla
        return clientes

    def gen_rutas(self, inicio_jornada: int = 6, final_jornada: int = 22, 
                  speed_fact: float = 0.73) -> pd.DataFrame:
        """
        Método para obtener la tabla de rutas para el VRP.
        Se toman las rutas de cada UNE, se les asigna un ID, las coords de las UNE, Inicio de jornada en Horas, Fin de
        jornada en hora y el speed_factor
        :param inicio_jornada: Inicio de jornada laboral, saliendo de la UNE (Horas en decimal)
        :param final_jornada: Fin de jornada laboral, llegar a la UNE (Horas en decimal)
        :param speed_fact: Qué tan rápido ir [0 - 1], se recomienda 0.73 para camiones en zonas urbanas.
        :return: Tabla con los datos de las rutas de cada UNE
        """
        # Creando la tabla con el método
        rutas = self.gen_rut_unes()
        # Dejando solo 1 vez la ruta
        rutas = rutas.drop_duplicates(['UNE_ID', 'RUTClave'])
        # Seleccionando columnas y reiniciando el índice
        rutas = rutas[['UNE_ID', 'RUTClave']]
        # Ordenando
        rutas = rutas.sort_values(['UNE_ID', 'RUTClave']).reset_index(drop=True)
        # Creando diccionario con el Número de rutas por UNE
        count_rutas = rutas.groupby('UNE_ID')['RUTClave'].nunique().to_dict()
        if len(self.une_list) >= 7:
            print(f'Rutas de {len(self.une_list)} UNE.')
        else:
            # Ciclo para imprimir el número de rutas por UNE
            for i in count_rutas:
                print(f"{i}: {count_rutas[i]} rutas.")
        # Obteniendo Latitud y Longitud de las UNE
        lat_lon = self.une_coords[['UNEID', 'latitud', 'longitud']]
        lat_lon = lat_lon[lat_lon['UNEID'].isin(self.une_list)]
        # Agregando los datos necesarios para el VRP a cada ruta
        # Agregando el índice como skill de las rutas
        rutas['Skills'] = rutas.index
        # Agregando la Latitud y Longitud correspondiente a cada UNE
        rutas = rutas.merge(lat_lon, left_on='UNE_ID', right_on='UNEID')
        # Speed Factor para las rutas
        rutas['speed_factor'] = speed_fact
        # Inicio de la jornada laboral en horas decimales
        rutas['Inicio_Jornada'] = (inicio_jornada * 3600) + 1600000000
        # Fin de la jornada laboral en horas decimales
        rutas['Fin_Jornada'] = (final_jornada * 3600) + 1600000000
        # Horas laborales
        rutas['Horas_Laborales'] = ((final_jornada - inicio_jornada) * 3600) + 1600000000
        rutas = rutas.rename(columns={'latitud': 'Latitud', 'longitud': 'Longitud'})
        # Limpiando la tabla
        rutas.drop(columns=['UNEID'], inplace=True)
        # Cambiando los formatos de las columnas
        rutas['UNE_ID'] = rutas['UNE_ID'].astype(str)
        rutas['RUTClave'] = rutas['RUTClave'].astype(str)
        rutas['Skills'] = rutas['Skills'].astype(int)
        rutas['Latitud'] = rutas['Latitud'].astype(float)
        rutas['speed_factor'] = rutas['speed_factor'].astype(float)
        rutas['Inicio_Jornada'] = rutas['Inicio_Jornada'].astype(int)
        rutas['Fin_Jornada'] = rutas['Fin_Jornada'].astype(int)
        rutas['Horas_Laborales'] = rutas['Horas_Laborales'].astype(int)
        return rutas

    def get_une(self) -> list:
        """
        Se usa este método para obtener los ID de las UNE en caso de seleccionar todas "['*']"
        :return: Lista con todos los ID de las UNE
        """
        return self.une_list
    

class EjecucionVRP:
    def __init__(self, df_rutas, df_clientes, unes, path_exportar):
        """
        Clase para la Ejecución y Exportación del VRP.
        :param df_rutas: DF con las rutas, generado por la Clase CargaDeDatos
        :param df_clientes: DF con los clientes, generado por la Clase CargaDeDatos
        :param unes: Lista con las UNE seleccionadas
        """
        self.df_rutas = df_rutas
        self.df_clientes = df_clientes
        self.unes_selec = unes
        self.path_exportar = path_exportar
        # Lista con los días de la semana
        self.dias = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado']
        # Datos de las UNE
        coordenadas_UNEs = {
            'Ubicaciones': {0: 'UNE Periferico Norte', 1: 'UNE Periferico Sur', 2: 'UNE Periferico Oriente',
                            3: 'UNE Periferico Poniente', 4: 'UNE Zapotlanejo', 5: 'UNE Chapala', 6: 'UNE Ocotlan',
                            7: 'UNE Tequila', 8: 'UNE Acatlan', 9: 'UNE Tepatitlan', 10: 'UNE Ameca',
                            11: 'UNE Autlán', 12: 'UNE Ciudad Guzman', 13: 'UNE Tomatlan',
                            14: 'UNE San Patricio Melaque', 15: 'UNE Colima', 16: 'UNE Tecoman',
                            17: 'UNE Manzanillo', 18: 'UNE Zacapu', 19: 'UNE Uruapan', 20: 'UNE Morelia',
                            21: 'UNE Zitacuaro', 22: 'UNE Aguascalientes', 23: 'UNE Nochistlan', 24: 'UNE Zamora',
                            25: 'UNE Ixtlan', 26: 'UNE Xalisco (Tepic)', 27: 'UNE Las Varas',
                            28: 'UNE Puerto Vallarta', 29: 'UNE Santiago', 30: 'UNE Acaponeta', 31: 'UNE Rosario',
                            32: 'UNE Mazatlan', 33: 'UNE Culiacan II', 34: 'UNE Guamuchil'},
            'latitud': {0: 20.74108812, 1: 20.55779994, 2: 20.67925813, 3: 20.64393476, 4: 20.62248961,
                        5: 20.32805521, 6: 20.39502715, 7: 20.87343535, 8: 20.42073653, 9: 20.86527,
                        10: 20.53983146, 11: 19.78357059, 12: 19.70762739, 13: 19.92406387, 14: 19.22603253,
                        15: 19.23872282, 16: 18.9371016, 17: 19.08800773, 18: 19.82660431, 19: 19.40814262,
                        20: 19.72770077, 21: 19.45230415, 22: 21.80205156, 23: 21.34980247, 24: 20.01699164,
                        25: 21.03674261, 26: 21.42791647, 27: 21.18918204, 28: 20.67920001, 29: 21.81743271,
                        30: 22.47995108, 31: 22.98510235, 32: 23.19361372, 33: 24.61487, 34: 25.47052649},
            'longitud': {0: -103.3972312, 1: -103.3656128, 2: -103.2352661, 3: -103.4446303, 4: -103.0459664,
                        5: -103.137919, 6: -102.7478122, 7: -103.8246571, 8: -103.6271771, 9: -102.72556,
                        10: -104.0341552, 11: -104.3654871, 12: -103.4956165, 13: -105.2639828, 14: -104.7025082,
                        15: -103.7591217, 16: -103.8915852, 17: -104.2881712, 18: -101.7709804, 19: -102.0672934,
                        20: -101.1517022, 21: -100.2911756, 22: -102.2859751, 23: -102.7843966, 24: -102.2840436,
                        25: -104.4000683, 26: -104.8992838, 27: -105.1458711, 28: -105.2454269, 29: -105.1897554,
                        30: -105.3812526, 31: -105.8723719, 32: -106.2776305, 33: -107.24976, 34: -108.1328638},
            'UNEID': {0: 'D001', 1: 'D002', 2: 'D003', 3: 'D004', 4: 'D006', 5: 'D007', 6: 'D040', 7: 'D041',
                    8: 'D042', 9: 'D043', 10: 'D044', 11: 'D045', 12: 'D046', 13: 'D047', 14: 'D048', 15: 'D049',
                    16: 'D050', 17: 'D051', 18: 'D080', 19: 'D081', 20: 'D082', 21: 'D083', 22: 'D085', 23: 'D091',
                    24: 'D095', 25: 'D120', 26: 'D121', 27: 'D123', 28: 'D124', 29: 'D125', 30: 'D126', 31: 'D127',
                    32: 'D128', 33: 'D130', 34: 'D131'}}
        # Pasamos el diccionario a un DF
        self.une_coords = pd.DataFrame(data=coordenadas_UNEs)

    def exe_vrp(self, exportar_indiv: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame, dict]:
        """
        Método para ejecutar el VRP y exportar datos
        :param exportar_indiv: En caso de que sea True, se exporta un .xlsx con el itinerario x UNE
        :param medir_tiempo: En caso de que sea True, se mide el tiempo de ejecución del ejercicio
        :return: DF con el itinerario general de todo el ejercicio
        """
        # Carga de los datos del constructor
        clientes = self.df_clientes
        rutas = self.df_rutas
        # Generando un DF general con los resultados de todo el ejercicio
        df_general = pd.DataFrame()
        rutas_general = pd.DataFrame()
        # Creando el diccionario de resp_gen
        res_gen = {}
        # Ciclo para movernos por las UNE
        for une in self.unes_selec:
            itinerario_une = pd.DataFrame()
            resp_une = {}
            # Haciendo DF filtrados por UNE
            clientes_temp_une = clientes[clientes['UNE_ID'] == une]
            rutas_une = rutas[rutas['UNE_ID'] == une].reset_index(drop=True)
            for dia in self.dias:
                # Haciendo un DF del anterior filtrando por día
                clientes_temp_dia = clientes_temp_une[clientes_temp_une['Dia_Visita'] == dia].reset_index(drop=True)
                # Headers
                json_headers = {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json'}
                payload = {
                    "jobs": [],
                    "vehicles": []}
                # Df con los clientes
                largo_clientes = len(clientes_temp_dia)
                # 1) Integración de los jobs (Clientes)
                for j in range(largo_clientes):
                    payload["jobs"].append({
                        "id": clientes_temp_dia["ID"][j].item(),  # Tiene que ser INT
                        "description": clientes_temp_dia["ClienteClave"][j],  # string, los string no se les pone .item
                        "location": [clientes_temp_dia["Longitud"][j].item(), clientes_temp_dia["Latitud"][j].item()],
                        "skills": [clientes_temp_dia["Skills"][j].item(), clientes_temp_dia["Skills"][j].item()],
                        "time_window": [clientes_temp_dia['HoraApertura'][j].item(),
                                         clientes_temp_dia['HoraCierre'][j].item()],
                        "service": clientes_temp_dia["TiempoServicio"][j].item()
                    }
                    )
                # Df con las rutas
                largo_rutas_une = len(rutas_une)
                for k in range(largo_rutas_une):
                    payload["vehicles"].append({
                        "id": rutas_une["Skills"][k].item(),  # Tiene que ser int
                        "start": [rutas_une["Longitud"][k].item(), rutas_une["Latitud"][k].item()],
                        "end": [rutas_une["Longitud"][k].item(), rutas_une["Latitud"][k].item()],
                        "speed_factor": rutas_une["speed_factor"][k].item(),
                        "skills": [rutas_une["Skills"][k].item(), rutas_une["Skills"][k].item()],
                        # tiene que ser int y array
                        "time_window": [rutas_une["Inicio_Jornada"][k].item(), rutas_une["Fin_Jornada"][k].item()]
                    }
                    )
                # Ejecución del query
                response_dia = requests.post(URL + "?api_key=",
                                             headers=json_headers,
                                             data=json.dumps(payload)).json()
                # Damos de alta un DF vació con las mismas columnas
                itinerario_dic = {'type': [], 'description': [], 'location': [], 'id': [], 'setup': [],
                                  'service': [], 'waiting_time': [], 'job': [], 'arrival': [], 'duration': [],
                                  'violations': [], 'distance': []}
                itinerario_dic = pd.DataFrame(itinerario_dic)
                # Generamos un loop para ir sacando y guardado cada lectura
                largo = len(response_dia["routes"])
                for h in range(largo):
                    itinerario = response_dia["routes"][h]["steps"]
                    itinerario = pd.DataFrame(itinerario)
                    itinerario["route_id"] = response_dia["routes"][h]["vehicle"]
                    itinerario_dic = [itinerario_dic, itinerario]
                    itinerario_dic = pd.concat(itinerario_dic)
                # Contabilización de cantidad de clientes por ruta
                # Le damos un count
                itinerario_dic["count"] = 1
                # Asignamos un valor de 0 bajo ciertas condiciones
                itinerario_dic.loc[itinerario_dic['job'] == 0, 'count'] = 0
                # CONTABILIZAR
                clientes_ruta = itinerario_dic.groupby(['route_id'])['count'].sum().reset_index()
                # Extracción de los resultados
                rutas_dia = response_dia["routes"]
                rutas_dia = pd.DataFrame(rutas_dia)
                # Nota: dato que estamos integrando ventanas de tiempo el costo de la ruta,
                # hace referencia a la duración total
                rutas_dia["Horas_Totales_Trabajo"] = (rutas_dia["duration"] + rutas_dia["service"]) / 3600
                rutas_dia["Horas_en_Transito"] = rutas_dia["duration"] / 3600
                rutas_dia["Horas_en_Servicio"] = rutas_dia["service"] / 3600
                rutas_dia["Distancia_Recorrida"] = rutas_dia["distance"] / 1000
                rutas_dia["Velocidad_Promedio"] = rutas_dia["Distancia_Recorrida"] / rutas_dia["Horas_en_Transito"]
                # Unimos con el contabilizador
                rutas_dia = pd.merge(rutas_dia, clientes_ruta, left_on="vehicle", right_on="route_id")
                # Cambio de nombre
                rutas_dia.rename(columns={'count': 'Total_Clientes'}, inplace=True)
                itinerario1 = itinerario_dic
                # Agregando el Día
                rutas_dia['Dia_Visita'] = dia
                rutas_dia['Skills'] = rutas_dia['vehicle']
                # Generación de la columna Secuencia
                itinerario1['Secuencia'] = itinerario1.groupby('route_id').cumcount()
                itinerario1["Secuencia"] = itinerario1["Secuencia"]
                # Itinerario Final
                clientes_temp_dia['ClienteClave'] = clientes_temp_dia['ClienteClave'].astype(str)
                itinerario = clientes_temp_dia.merge(
                    itinerario1[['arrival', 'duration', 'description', 'Secuencia', 'service']],
                    left_on='ClienteClave', right_on='description', how='inner')
                itinerario = itinerario.sort_values(['Skills', 'Secuencia'])
                itinerario.reset_index(inplace=True, drop=True)
                # Haciendo la hora de TimeStamp a Segundos
                itinerario['arrival'] = itinerario['arrival'].apply(lambda x: int(x) - 1600000000)
                itinerario['salida'] = itinerario['arrival'] + itinerario['service'].astype(int)
                # Convirtiendo los segundos a DateTime
                itinerario['Llegada_Estimada'] = pd.to_timedelta(itinerario['arrival'], unit='S')
                itinerario['Salida_Estimada'] = pd.to_timedelta(itinerario['salida'], unit='S')
                # Sacando las horas
                horas_llegada = []
                horas_salida = []
                # Ciclo para obtener la hora
                for i in itinerario.index:
                    llega = str(itinerario['Llegada_Estimada'][i])[7:12]
                    sale = str(itinerario['Salida_Estimada'][i])[7:12]
                    # Agregando los valores a las listas correspondientes
                    horas_llegada.append(llega)
                    horas_salida.append(sale)
                # Agregando las horas a las columnas
                itinerario['Hora_Llegada_Estimada'] = horas_llegada
                itinerario['Hora_Salida_Estimada'] = horas_salida
                # Agregando el Tiempo de servicio en minutos
                itinerario['service'] = itinerario['service'].apply(lambda x: int(x / 60))
                # Cambiando nombre a las columnas
                itinerario.rename(columns={'service': 'Minutos_Servicio'}, inplace=True)
                # Ordenando las columnas
                itinerario = itinerario[['UNE_ID', 'RUTClave', 'Skills', 'Dia_Visita', 'FrecuenciaClave',
                                         'ClienteClave', 'Latitud', 'Longitud', 'RazonSocial', 'NombreCorto',
                                         'Secuencia', 'Hora_Llegada_Estimada', 'Hora_Salida_Estimada',
                                         'Minutos_Servicio']]
                # Agregando el itinerario del Día al completo con toda la UNE
                itinerario_une = pd.concat([itinerario_une, itinerario], axis=0)
                rutas_general = pd.concat([rutas_general, rutas_dia])
                # Agregando el response del día al diccionario de respuesta final
                resp_une[dia] = {'unassigned': response_dia['unassigned'], 'len': len(response_dia['unassigned'])}
            # Ordenando las columnas
            rutas_general['Skills'] = rutas_general['vehicle']
            rutas_general = rutas_general[['Dia_Visita', 'Skills', 'vehicle', 'route_id', 'cost', 'duration',
                                           'distance', 'steps', 'geometry', 'Horas_Totales_Trabajo',
                                           'Horas_en_Transito', 'Distancia_Recorrida', 'Total_Clientes']]
            rutas_general['Trazo'] = rutas_general['geometry'].map(lambda x: polyline.decode(x))
            rutas_general.to_excel(rf'{self.path_exportar}/Resumen_Rutas_{une}.xlsx', index=False)
            # En caso de que sea True, se exporta los itinerarios por UNE. Si no, solo el general
            if exportar_indiv:
                # Exportando el Itinerario de toda la UNE
                itinerario_une.to_excel(rf'{self.path_exportar}Por_UNE/Itinerario_{une}.xlsx', index=False)
            else:
                pass
            # Juntando la iteración de la UNE al archivo generar
            df_general = pd.concat([df_general, itinerario_une], axis=0)
            # Agregando el response de la UNE al general
            res_gen[une] = resp_une
        # Exportando DF general
        df_general.to_excel(rf'{self.path_exportar}/Itinerario_General.xlsx', index=False)
        return df_general, rutas_general, res_gen

    def graficar(self, itinerario, rutas_general) -> None:
        """
        Método para graficar el itinerario de cada UNE
        :param itinerario: DF con el itinerario de cada UNE
        :param rutas_general: DF con el resumen de las rutas de cada UNE
        """
        for une in self.unes_selec:
            data = itinerario.merge(rutas_general, on=['Dia_Visita', 'Skills'])
            datos_une = self.unes_coords[self.unes_coords['UNEID'] == une].reset_index(drop=True)
            for dia in self.dias:
                data_dia = data[data['Dia_Visita'] == dia]
                rutas_dia = list(data_dia['Skills'].unique())
                for ruta_actual in rutas_dia:
                    data_ruta = data_dia[data_dia['Skills'] == ruta_actual]
                    ruta_clave_actual = data_ruta['RUTClave'].unique()[0]
                    # Creando el grupo de atributos
                    feature_group = folium.FeatureGroup(str(ruta_clave_actual))
                    # Creando un centroide con la Latitud y Longitud para el centro del mapa
                    lat_mean = data_ruta['Latitud'].mean()
                    lon_mean = data_ruta['Longitud'].mean()
                    # Obteniendo Trazo de la ruta
                    trazo_temp = data_ruta['Trazo'].drop_duplicates().reset_index(drop=True)[0]
                    trazo_temp_df = pd.DataFrame(trazo_temp)
                    # Cambiando el nombre de las columnas
                    trazo_temp_df.rename(columns={0: 'Latitud', 1: 'Longitud'}, inplace=True)
                    # Creando los límites del mapa
                    sw = trazo_temp_df[['Latitud', 'Longitud']].min().values.tolist()
                    sw = [value + 0.0001 for value in sw]
                    ne = trazo_temp_df[['Latitud', 'Longitud']].max().values.tolist()
                    ne = [value + 0.0001 for value in ne]
                    # Creando el mapa con los atributos especiales para la ruta (Centroide) el zoom es genérico
                    mapa = folium.Map(location=[lat_mean, lon_mean],
                                      # zoom_start=12,
                                      tiles="OpenStreetMap")
                    # Moviendonos en las filas del df en el día y ruta especificados
                    for row in data_ruta.itertuples():
                        # Cosas que vendrán en los globos de cada cliente
                        html = f"""
                        <h2>  Itinerario </h2>
                        <p> Dia: {row.Dia_Visita}  </p>
                        <p> Ruta: {row.RUTClave}  </p>
                        <p> Nombre: {row.NombreCorto}  </p>
                        """
                        iframe = folium.IFrame(html=html, width=210, height=250)
                        popup = folium.Popup(iframe, max_width=650)
                        # Marcador en cada cliente
                        folium.Marker(location=[row.Latitud, row.Longitud],
                                      popup=popup,
                                      icon=plugins.BeautifyIcon(icon="arrow-down",
                                                                icon_shape="marker",
                                                                number=row.Secuencia,
                                                                text_color='black',
                                                                background_color="#ff7075",
                                                                border_width=0  # Ancho del borde del icono
                                                                )
                                      ).add_to(feature_group)
                    # Agregando el trazo o ruta
                    folium.PolyLine(locations=row.Trazo).add_to(feature_group)
                    # Agregando todo lo anterior al objeto del mapa
                    feature_group.add_to(mapa)
                    folium.LayerControl().add_to(mapa)
                    # Creando el icono con la imagen
                    icon = icon=folium.Icon(icon='home', color='red')
                    folium.Marker(location=[datos_une["latitud"][0], datos_une["longitud"][0]], icon=icon).add_to(
                        mapa)  # Agregando el icono como marcador al mapa
                    # Poniendo los límites al mapa
                    mapa.fit_bounds([sw, ne])
                    # Checando que la ruta exista
                    path_mapa_exp = f'{self.path_exportar}/{une}/{dia}'
                    if not os.path.exists(path_mapa_exp):
                        os.makedirs(path_mapa_exp)
                    # Guardando el mapa (HTML) en cada carpeta
                    mapa_path = rf"{path_mapa_exp}/Mapa_{ruta_clave_actual}_Dia-{dia}.html"
                    mapa.save(mapa_path)

# -------------------------------------------------- Ejecución del script -------------------------------------------------- #

# Ejecución del script
if __name__ == '__main__':
    # Obteniendo la lista con las UNE a usar
    unes_selec = arcpy.GetParameterAsText(0)
    unes_selec = sorted(list(set(unes_selec.split(';'))))
    # Inicio y final de la jornada
    inicio_jornada = float(arcpy.GetParameterAsText(1))
    final_jornada = float(arcpy.GetParameterAsText(2))
    # Obteniendo el factor de velocidad
    speed_fact = float(arcpy.GetParameterAsText(3))
    # Obteniendo la ruta de exportación
    path_exportar = arcpy.GetParameterAsText(4)
    # Viendo si quieren los mapas o no
    mapas_bool = arcpy.GetParameterAsText(5)
    mapas_bool = True if mapas_bool == 'true' else False

    # Creando la carpeta de exportación
    if not os.path.exists(path_exportar):
        os.makedirs(path_exportar)
    
    # Ejecutando las clases
    rutas = CargaDatosClientes(une_list=unes_selec).gen_rutas(inicio_jornada=inicio_jornada, 
                                                              final_jornada=final_jornada, 
                                                              speed_fact=speed_fact)
    
    # Generando los clientes
    clientes = CargaDatosClientes(une_list=unes_selec).gen_clientes()
    clientes = clientes.merge(rutas[['RUTClave', 'Skills']], on=['RUTClave'])
    clientes.to_excel(f'{path_exportar}/Clientes.xlsx', index=False)
    
    # Ejecutando el VRP
    arcpy.AddMessage(f'Iniciando la ejecución del VRP')
    itinerario, rutas_general, resp_gen = EjecucionVRP(df_rutas=rutas, 
                                                       df_clientes=clientes, 
                                                       unes=unes_selec, 
                                                       path_exportar=path_exportar).exe_vrp(exportar_indiv=False)
    
    # En caso de que se quieran los mapas
    if mapas_bool:
       arcpy.AddMessage(f'\nCreación de mapas')
       EjecucionVRP(df_rutas=rutas, 
                    df_clientes=clientes, 
                    unes=unes_selec,
                    path_exportar=path_exportar).graficar(itinerario, rutas_general)
