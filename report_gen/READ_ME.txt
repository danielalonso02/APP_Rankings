Esta carpeta contiene tres archivos esenciales para la generación de informes de jugadores:

1. 2RFEF_wyscout.xlsx

Archivo principal de datos. Aquí se encuentra la información de todos los jugadores. Para generar un informe de un jugador concreto, primero hay que localizar su fila en este archivo.

2. jugadores_a_analizar.xlsx

Archivo de generación de informes. En la segunda columna se debe escribir el número de fila correspondiente al jugador (obtenido del archivo anterior) para generar su informe. Se puede añadir más de un jugador a la vez. 

3. parametros.xlsx

Archivo de configuración. Actualmente no es necesario modificarlo, pero desde aquí se puede ajustar:
	•	El mínimo de minutos jugados requeridos.
	•	El tipo de informe:
	•	0 para informe completo
	•	1 para resumen

El nuevo, o nuevos, informe se generará (2-3 minutos máximo) y se guardará en la carpeta Informes_Generados. 