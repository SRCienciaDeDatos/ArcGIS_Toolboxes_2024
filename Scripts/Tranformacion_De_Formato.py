# Librerias
import arcpy
import pandas as pd
import os

# Haciendo que se pueda sobreescribir los archivos
arcpy.env.overwriteOutput =True

# ----------------------------------------------- 1) Obtención de los inputs ----------------------------------------------- #
# 1.1) Work Space (Geodatabase)
work_space = arcpy.GetParameterAsText(0)
# 1.2)  Obtenemos el  nombre del archivo a modifcar su formato
Nombre_capa = arcpy.GetParameterAsText(1)
# 1.3) Obtenemos el ID de la coluama de los clientes/punto
Columna_ID = arcpy.GetParameterAsText(2)
#1.4 Columna Ruta
Ruta_ID = arcpy.GetParameterAsText(3)
# 1.4) Latitud
latitud = arcpy.GetParameterAsText(4)
# 1.5) Longitud
longitud = arcpy.GetParameterAsText(5)
# 1.6) Dias
dias = (arcpy.GetParameterAsText(6).split(";")) # Esto lo hará que sea una lista
# 1.7) Direccion de salida junnto con el nombre de la capa
output_file = arcpy.GetParameterAsText(7)

# Exportacion de la tabla de atributos de la capa selecionada a excel
arcpy.conversion.TableToExcel(Input_Table = Nombre_capa,
                              Output_Excel_File = output_file,
                              Use_field_alias_as_column_header= "NAME")

# --------------------------------------------- 2) Procesamiento de los datos --------------------------------------------- #

# 2.1) Lectura de la tabla previamente exportada
data = pd.read_excel(f"{output_file}")
# 2.1) Obtencion de la frecuencia semanal en funcion al numero de veces que hay 1 en las lecturas
# convertimos a numericos las columnas de dias
data[dias] = data[dias].astype(int)
#data[f"{frecuencias}"] = data.loc[:, set(dias)].sum()

# 2.2) MELT dataframe
clientes_tranformado = pd.melt(frame=data,
    id_vars=[f'{Columna_ID}'],
    value_vars= dias,
    var_name='Dias', # Se crea esta columna
    value_name= "Visita")
clientes_tranformado.sort_values(by=[f"{Columna_ID}", "Dias"], inplace=True)
clientes_tranformado.reset_index(drop= True, inplace=True)
# Eliminación de Clientes con Frecuencia dia = 0 (son los que traian un 0 en ese dia de la semana)
clientes_tranformado = clientes_tranformado[clientes_tranformado["Visita"] == 1]
clientes_tranformado.reset_index(drop =True, inplace = True)
# Merge con el resto de los datos de los clientes
clientes_tranformado = pd.merge (left=clientes_tranformado, right=data, on=f"{Columna_ID}", how="left")
# Modificación de las columnas binarias por día
clientes_tranformado[dias] = clientes_tranformado[dias].astype(int)
clientes_tranformado[dias] = 0 #primero declaramos todas en 0
clientes_tranformado.reset_index(drop =True, inplace = True)

# Iniciamos ciclo para dar valores binarios a las columnas de las fechas/dias
for i in range(0, len(clientes_tranformado)):
    day = clientes_tranformado.loc[i, "Dias"]
    clientes_tranformado.loc[i, f"{day}"] = 1

# 2.3) Generación de la capa de tabla de ordenes especializadas
ordenes_epsecializadas = clientes_tranformado.copy()
ordenes_epsecializadas =  ordenes_epsecializadas [[f"{Columna_ID}", f"{Ruta_ID}", "Dias", f"{latitud}", f"{longitud}"]] # "Dias" , poner o quitar
#ordenes_epsecializadas.drop_duplicates(subset=[f"{Columna_ID}"] , inplace =True)
ordenes_epsecializadas.reset_index(drop=True, inplace =True)

# -------------------------------------------- 3) Exportación de los Resultados -------------------------------------------- #

# 3.1) Rescatamos el nombre de exportacion y la direccion de exportacion
nombre_exportacion = output_file.split("\\")
nombre_exportacion =  nombre_exportacion[-1]

# OBTENEMOS LA DIRECCION de un string por medio de os
ruta_exportacion = os.path.dirname(output_file)

# 3.2) Exportacion de clientes tranformados
#clientes_tranformado.to_excel( ruta_exportacionn +  f"/{nombre_exportacion}", index =False)
clientes_tranformado.to_excel( output_file, index =False, sheet_name="Hoja1")

# 3.3) Exportacion de ordeens especializadas
ordenes_epsecializadas.to_excel(ruta_exportacion + "/Ordenes y Rutas Especializadas.xlsx", index = False, sheet_name="Hoja1")

# Obtencion del nnombre de expoertacion sin espacios
nombre_exportacion_sin_espacio = nombre_exportacion.replace(" ", "_")
nombre_exportacion_sin_espacio = nombre_exportacion_sin_espacio.replace(".", "")
nombre_exportacion_sin_espacio = nombre_exportacion_sin_espacio.replace("xlsx", "")
nombre_exportacion_sin_espacio = nombre_exportacion_sin_espacio.replace("xsl", "")

# Impresion de los parámetros
arcpy.AddMessage("Direccion de trabajo: {}".format(work_space))
arcpy.AddMessage("Capa Selecionada: {}".format(Nombre_capa))
arcpy.AddMessage("Columna ID del puntio: {}".format(Columna_ID))
arcpy.AddMessage("Columna Ruta ID: {}".format(Ruta_ID))
arcpy.AddMessage("Columna latitud: {}".format(latitud))
arcpy.AddMessage("Columna longitud: {}".format(longitud))
arcpy.AddMessage("Dias selecionados: {}".format(dias))
arcpy.AddMessage("Archivo  de exportacion: {}".format(output_file))
arcpy.AddMessage("Ruta de exportación e importación: {}".format(ruta_exportacion))
arcpy.AddMessage("Nombre de exportación: {}".format(nombre_exportacion_sin_espacio))

## 3.3) Importacion del excel al geodatabase de las ordenes  tranformadas conn todos sus datos
arcpy.management.XYTableToPoint(in_table=  fr"{output_file}" + "/Hoja1$",
                                out_feature_class= work_space  + f"/{nombre_exportacion_sin_espacio}",
                                x_field= longitud,
                                y_field= latitud,
                                coordinate_system= 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision')

## 3.4) Importacion del excel de ordenes especializadas
arcpy.management.XYTableToPoint(in_table=    fr"{ruta_exportacion}" + "/Ordenes y Rutas Especializadas.xlsx/Hoja1$",
                                    out_feature_class= work_space  + "/Ordenes_y_Rutas_Especializadas",
                                    x_field= longitud,
                                    y_field= latitud,
                                    coordinate_system= 'GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]];-400 -400 1000000000;-100000 10000;-100000 10000;8.98315284119521E-09;0.001;0.001;IsHighPrecision')

# -------------------------------------------- 4) Integracion de los Resultados -------------------------------------------- #

# Lo intnegramos al mapa actual
aprx = arcpy.mp.ArcGISProject("CURRENT")
aprxMap = aprx.listMaps()[0] # me tomara el primer mapa que tenga
aprxMap.addDataFromPath(work_space + f"/{nombre_exportacion_sin_espacio}")   # Capa del geodatabase
aprxMap.addDataFromPath(work_space + "/Ordenes_y_Rutas_Especializadas")   # Capa del geodatabase
