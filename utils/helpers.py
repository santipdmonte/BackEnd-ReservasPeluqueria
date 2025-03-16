def fetchall_to_dict(cursor):

    if cursor.rowcount == 0:
        return None

    # Obtener los nombres de las columnas
    column_names = [desc[0] for desc in cursor.description]
    objects = cursor.fetchall()
    
    # Convertir cada tupla a un diccionario
    resultado = []
    for object in objects:
        object_dict = dict(zip(column_names, object))
        resultado.append(object_dict)

    return resultado

def fetchone_to_dict(cursor):

    if cursor.rowcount == 0:
        return None

    column_names = [desc[0] for desc in cursor.description]
    object = cursor.fetchone()
    return dict(zip(column_names, object))
