# objetivo: Guardar y pasar información entre agentes sin meterlo todo en el prompt.
# memoria compartida del sistema

# Ejemplo:
# 	•	El worker A genera un análisis largo.
# 	•	El worker B solo necesita:
# 	•	un resumen
# 	•	3 puntos clave

# Eso lo decide y gestiona context.py.

# Aquí evitas:
# 	•	prompts gigantes
# 	•	pérdida de información
# 	•	la famosa dumb zone
