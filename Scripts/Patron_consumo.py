###################                                  VENTAS POR CLIENTE                       #############################

# Este script esta enfocado en la descarga de datos de venta para su procesamiento y generar información de consumo total por semana y patrones de consumo

# Librerias
import arcpy
import pyodbc
import pandas as pd


##################                                   1) LECTURA DE PARAMETROS                                #########################

### 1.1) Lectura de las UNEs
unes = arcpy.GetParameterAsText(0)
unes = unes.split(';')  # Creando la lista con las UNE a usar
# Usando list comprehensions
unes = [item.split(" - ")[0].replace("'", "") for item in unes]
unes = tuple(unes) # lo paso a una tuple, asi lo usamos directametne en el query de SQL



### 1.2) Lectura de la fecha inicial
fecha_inicio = arcpy.GetParameterAsText(1)
fecha_inicio = fecha_inicio.split(" ")
fecha_inicio = fecha_inicio[0] # en estos 2 ultimas lineas hacemos que nos quedemos solo con la primera parte de la fecha/hora que es solo la fecha
# PROBLEMA, la fecha de arcgis es con formato: dia, mes y año, y yo la neceisto con año-mes-dia
fecha_inicio = fecha_inicio.split("/") # esto me hara una lista con string en el siguietne orden dia, mes y año
fecha_inicio = f"{fecha_inicio[2]}" + "-" + f"{fecha_inicio[1]}" + "-" + f"{fecha_inicio[0]}"





### 1.3) Lectura de la fecha final
fecha_final = arcpy.GetParameterAsText(2)
fecha_final = fecha_final.split(" ")
fecha_final = fecha_final[0] # me quedo con la pura fecha, que esta en formato de dia, mes año
fecha_final = fecha_final.split("/") # esto me hara una lista con string en el siguietne orden dia, mes y año
fecha_final = f"{fecha_final[2]}" + "-" + f"{fecha_final[1]}" + "-" + f"{fecha_final[0]}" # lo quiero en año , mes y dia



### 1.4) Lectura de la direccion de exportacion
folder = str(arcpy.GetParameterAsText(3))




####### 1.1) IMPRESION DE DATOS
arcpy.AddMessage("UNEs selecionadas: {}".format(unes))
arcpy.AddMessage("Fecha inicio: {}".format(fecha_inicio))
arcpy.AddMessage("Fecha final: {}".format(fecha_final))
arcpy.AddMessage("Dirección de exportación: {}".format(folder))



#####################                                            2) CONEXION A LA BD                             ####################
# Alta de datos del servidor
server = "192.168.0.192"
database = "ASR"
usuarioDB = "consulta"
passwordDB = "Consult@"

try:
    conexion = pyodbc.connect(
        'DRIVER={SQL SERVER};SERVER=' + server + ';DATABASE=' +
        database + ';UID=' + usuarioDB + ';PWD=' + passwordDB)
except Exception as e:
    conexion = "f"
    print("Conexión fallida:", e)




######################                          3) DESCARGA DE DATOS  VENTAS DETALLE                                 #########################
query = f"""
select TransProd.TransProdID,TransProd.ClienteClave, ClienteDomicilio.NombreTienda, ClienteDomicilio.Calle, ClienteDomicilio.Numero,
       ClienteDomicilio.CodigoPostal, ClienteDomicilio.Colonia, ClienteDomicilio.Localidad, ClienteDomicilio.Poblacion,
       ClienteDomicilio.Entidad, ClienteDomicilio.CoordenadaX, ClienteDomicilio.CoordenadaY, TransProd.DiaClave, TransProd.Tipo, TransProd.TipoFaseIntSal,
       TransProd.TipoFase, TransProd.TipoMovimiento, TransProd.Total as Total_Global, TransProd.MFechaHora, TransProd.MUsuarioID, Almacen.AlmacenPadreId,
        TransProdDetalle.ProductoClave, TransProdDetalle.Total as Total_Detalle
from TransProd
join Almacen on TransProd.MUsuarioID = Almacen.Clave
join TransProdDetalle on TransProd.TransProdID = TransProdDetalle.TransProdID
join ClienteDomicilio on TransProd.ClienteClave = ClienteDomicilio.ClienteClave
where Almacen.AlmacenPadreId in {unes} and TransProd.Tipo = 1 and TransProd.TipoFaseIntSal = 1 and TransProd.TipoFase !=0 and TransProd.TipoMovimiento =2
  and  cast(TransProd.MFechaHora as date)   >= '{fecha_inicio}' and cast (TransProd.MFechaHora as date)   <= '{fecha_final}'
"""





##################                                       4) TRATAMIENTO DE DATOS                                             #############################

### 4.1) Historico de ventas
ventas_detalle= pd.read_sql(sql=query, con=conexion)


#####     4.2) ANALISIS POR UNE
#### 4.2.1) Total de ventas por UNE
ventas_totales_UNE = ventas_detalle.groupby(by=["AlmacenPadreId"])["Total_Detalle"].sum().reset_index()
ventas_totales_UNE.rename(columns ={"Total_Detalle":"Total Global"}, inplace=True)


#### 4.2.2) Total de ventas por UNE por producto, con su respectivo porcentaje
ventas_detalle_UNE = ventas_detalle.groupby(by=["AlmacenPadreId", "ProductoClave"])["Total_Detalle"].sum().reset_index()

# Sacamos porcentaje
ventas_detalle_UNE = pd.merge(left=ventas_detalle_UNE, right=ventas_totales_UNE, on="AlmacenPadreId", how="left")
ventas_detalle_UNE["Porcentaje"] = (ventas_detalle_UNE["Total_Detalle"] / ventas_detalle_UNE["Total Global"])*100
ventas_detalle_UNE.sort_values(by=["AlmacenPadreId", "Porcentaje"], inplace=True, ascending=[True, False])



### 4.3) ANALISIS POR RUTA
ventas_totales_ruta = ventas_detalle.groupby(by=["AlmacenPadreId", "MUsuarioID"])["Total_Detalle"].sum().reset_index()
ventas_totales_ruta.rename(columns ={"Total_Detalle":"Total Global"}, inplace=True)



### 4.3.1) Total por ruta por producto por ruta, sacamos porcentaje
venta_detalle_ruta = ventas_detalle.groupby(by=["MUsuarioID",  "ProductoClave"])["Total_Detalle"].sum().reset_index()
venta_detalle_ruta = pd.merge(left=venta_detalle_ruta, right=ventas_totales_ruta, on="MUsuarioID", how="left")
venta_detalle_ruta["Porcentaje"] = (venta_detalle_ruta["Total_Detalle"]/ venta_detalle_ruta["Total Global"]) * 100
venta_detalle_ruta.sort_values(by=["AlmacenPadreId","MUsuarioID" , "Porcentaje"], inplace=True, ascending=[True, True,False])



#### 4.3) ANALISIS POR CLIENTE
# 4.3.1) Ventas totales por cliente
ventas_totales_cliente = ventas_detalle.groupby(by=["ClienteClave", "AlmacenPadreId",
                                                    "MUsuarioID", "CoordenadaX", "CoordenadaY"])["Total_Detalle"].sum().reset_index()

## 4.3.2) Venta por detalle por cliente
ventas_detalle_cliente  = ventas_detalle.groupby(by=["ClienteClave","ProductoClave", "AlmacenPadreId",
                                                    "MUsuarioID", "CoordenadaX", "CoordenadaY"])["Total_Detalle"].sum().reset_index()

## 4.3.4) Capa espacial  (limpieza de coordenadas)
ventas_detalle_cliente_spatial  = ventas_detalle_cliente.copy()
ventas_detalle_cliente_spatial = ventas_detalle_cliente_spatial.query("CoordenadaX > -105 and CoordenadaX < -92") # es mas sencillo utilizar esta funcion
ventas_detalle_cliente_spatial = ventas_detalle_cliente_spatial.query("CoordenadaY > 13 and CoordenadaY < 31") # es mas sencillo utilizar esta funcion



### 4.4) Ventas totales por UNE

# Exportacion
ventas_totales_UNE.to_csv(path_or_buf=folder + "/Ventas totales UNE.csv", index=False)
ventas_detalle_UNE.to_csv(path_or_buf=folder + "/Venta detalle UNE.csv", index=False)

ventas_totales_ruta.to_csv(path_or_buf=folder + "/Ventas totales Ruta.csv", index=False)
venta_detalle_ruta.to_csv(path_or_buf=folder + "/Venta detalle Ruta.csv", index=False)

ventas_totales_cliente.to_csv (path_or_buf=folder + "/Ventas totales Cliente.csv", index=False)
ventas_detalle_cliente.to_csv (path_or_buf=folder + "/Ventas detalle Cliente.csv", index=False)

ventas_detalle_cliente_spatial.to_csv (path_or_buf=folder + "/Ventas detalle Cliente espacial.csv", index=False)


### BORRAR
#df = pd.read_csv(r"C:\Users\OMBARRAZA\Desktop\Test\Ventas detalle Cliente espacial.csv")

#pivot_df = df.pivot(index='ClienteClave', columns='ProductoClave', values='Total_Detalle')
