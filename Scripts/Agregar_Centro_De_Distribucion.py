# Librerías
import os
import shutil
import arcpy
import pandas as pd

# ----------------------------------------------------- Clase ----------------------------------------------------- #

# Clase para crear una tabla
class AgregarUNE:
    def __init__(self) -> None:
        """
        Esta clase crea una tabla con los parámetros de entrada del toolbox y la agrega a la vista de mapa.
        """
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
        self.nombre_geodatabase = nombre_geodatabase
        self.global_path = global_path
    
    def crear_tabla(self, name, description, start_time, end_time, latitud, longitud) -> pd.DataFrame:
        """
        Con este método se cear una tabla y se guarda en una carpeta temporal.
        :param name: Nombre del centro de distribución.
        :param description: Descripción del centro de distribución.
        :param start_time: Hora de inicio de operaciones.
        :param end_time: Hora de fin de operaciones.
        :param latitud: Latitud del centro de distribución.
        :param longitud: Longitud del centro de distribución.
        :return: Retorna el dataframe y la ruta de la carpeta temporal.
        """
        workspace = fr'{self.global_path}/{self.nombre_geodatabase}.gdb'
        # Nombre y campos de la tabla
        df = pd.DataFrame(columns=['Name', 'Descrpition', 'Start_Time', 'End_Time', 'Latitud', 'Longitud'])
        df.loc[0] = [str(name), str(description), str(start_time), str(end_time), float(latitud), float(longitud)]
        # Creando carpeta temporal
        path_temp = f'{self.global_path}/temp'
        if not os.path.exists(path_temp):
            os.mkdir(path_temp)
        # Guardando el dataframe en un csv
        df.to_csv(fr'{path_temp}/UNE.csv', index=False)
        return df, path_temp

    # Función para agregar la tabla a la vista de mapa
    def agg_csv_mapa(self, nombre_csv: str, nombre_capa: str, path: str) -> None:
        """
        Método para agregar la tabla a la vista de mapa.
        :param nombre_csv: Nombre del archivo CSV.
        :param nombre_capa: Nombre de la capa de puntos.
        :param path: Ruta de la carpeta temporal.
        """
        # Especifica la ruta a la geodatabase en la que deseas cargar la capa de puntos
        workspace = fr"{self.global_path}{self.nombre_geodatabase}.gdb"
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
    
    # Función para eliminar la carpeta temporal
    def eliminar_carpeta_temp(self, path) -> None:
        """
        Método para eliminar la carpeta temporal.
        :param path: Ruta de la carpeta temporal.
        """
        for archivo in os.listdir(path):
            archivo_path = os.path.join(path, archivo)
            if os.path.isfile(archivo_path):
                os.remove(archivo_path)
            elif os.path.isdir(archivo_path):
                shutil.rmtree(archivo_path)
        os.rmdir(path)

# --------------------------------------------------- Ejecución --------------------------------------------------- #

# Ejecutando la clase con los parámetros de entrada del toolbox
if __name__ == '__main__':
    # Habilitando la sobrescritura de archivos
    arcpy.env.overwriteOutput = True
    # Accediendo a los parámetros de entrada
    name = arcpy.GetParameterAsText(0)
    description = arcpy.GetParameterAsText(1)
    start_time = arcpy.GetParameterAsText(2)
    end_time = arcpy.GetParameterAsText(3)
    latitud = arcpy.GetParameterAsText(4)
    longitud = arcpy.GetParameterAsText(5)
    # Ejecutando la clase
    agregar_une, path_temp = AgregarUNE().crear_tabla(name, description, start_time, end_time, latitud, longitud)
    # Agregando la tabla a la vista de mapa
    AgregarUNE().agg_csv_mapa(nombre_csv='UNE', nombre_capa='UNE', path=path_temp)
    # Eliminando la carpeta temporal
    AgregarUNE().eliminar_carpeta_temp(path_temp)
