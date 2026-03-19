from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file
import pandas as pd
import os
import base64
from datetime import datetime
import io
from PIL import Image
import json
import requests


# Para hacer seguro el sitio en desarrollo local con HTTPS con chrome
#chrome://flags/#unsafely-treat-insecure-origin-as-secure
#ingresa la URL

#Firefox
#about:config
#media.devices.insecure.enabled
#media.getusermedia.insecure.enabled -> true

app = Flask(__name__)

FOTOS_DIR = 'fotos_guardadas'

# Crear directorio si no existe
os.makedirs(FOTOS_DIR, exist_ok=True)


# Ruta para mostrar el formulario
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/visitantes')
def visitantes():
    return render_template('visitantes.html')

@app.route('/foto')
def foto():
    return render_template('foto.html')

@app.route('/informes')
def informes():
    return render_template('informes.html')

@app.route('/paqueteria')
def paqueteria():
    return render_template('paqueteria.html')

@app.route('/registrar_salida')
def registrar_salida():
    return render_template('registrar_salida.html')

@app.route('/proveedores')
def proveedores():
    return render_template('proveedores.html')

@app.route('/priv')
def priv():
    return render_template('priv.html')

@app.route('/reservationForm', methods=['POST'])
def reservationForm():
    if request.method == 'POST':
        nombre = request.form['firstName']
        apellidos = request.form['lastName']
        numerotel = request.form['phone']
        correo = request.form['email']
        servicio = request.form['serviceType']
        capofcina = request.form.get('officeCapacity','N/A')
        nomempresa = request.form['companyName']
        giroempresa = request.form['businessType']
        fechaAprox = request.form['startDate']
        notasAdicionales = request.form['additionalNotes']

        registro_informes= pd.DataFrame([[nombre, apellidos, numerotel, correo, servicio, capofcina, nomempresa, giroempresa, fechaAprox, notasAdicionales]], columns=['Nombre','Apellidos','Número de Teléfono','Correo Electrónico','Tipo de Servicio','Capacidad de Oficina','Nombre de la Empresa','Giro de la Empresa','Fecha Aproximada','Notas Adicionales'])
        archivo_informes = 'registros_informes.csv'
        if os.path.exists(archivo_informes):
            registro_informes.to_csv(archivo_informes, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            registro_informes.to_csv(archivo_informes, mode='w', header=True, index=False, encoding='utf-8-sig')
        
        return redirect(url_for('index'))
    



# Ruta para procesar el formulario
@app.route('/agregar_formulario', methods=['POST'])
def agregar_registro():
    if request.method == 'POST':
        fecha = request.form['fecha']
        nombre = request.form['nombre']
        apellidoPaterno = request.form['apePaterno']
        visitado = request.form['visitado']
        oficina = request.form['oficina']
        ruta_foto = request.form['ruta_foto']
        hora_entrada = request.form['horaEntrada']
        numGafe = request.form['numGafe']
        estatus = 'Activo'

        foto_base64 = request.form.get('fotoTomada', '')

        if foto_base64:
            try:
                # Limpiar y decodificar la imagen base64
                foto_base64 = foto_base64.split(",")[1]
                image_bytes = base64.b64decode(foto_base64)

                # Crear nombre y ruta del archivo
                fecha_hora = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{fecha_hora}_{nombre.replace(' ', '_')}.jpg"
                filepath = os.path.join(FOTOS_DIR, filename)

                # Guardar la imagen en el servidor
                with open(filepath, "wb") as f:
                    f.write(image_bytes)

                # Guardar la ruta relativa para Excel/CSV
                ruta_foto = f"fotos_guardadas/{filename}"
            except Exception as e:
                print("Error al guardar foto:", e)
                ruta_foto = "Error al guardar foto"
       
        
        # Crear un DataFrame con el nuevo registro
        nuevo_registro = pd.DataFrame([[fecha,nombre, apellidoPaterno, visitado, oficina,numGafe,hora_entrada,ruta_foto,estatus]], columns=['Fecha','Nombre del visitante','Apellidos', 'Nombre de quien visita o Empresa','Número de oficina','Numero Gafete','Hora de entrada','ruta_foto','Estatus'])

        # Verificar si el archivo CSV existe
        archivo = 'registrosregistros_visitantes.csv'
        if os.path.exists(archivo):
            # Si el archivo existe, agregar al final
            nuevo_registro.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            # Si no existe, crear el archivo con el encabezado
            nuevo_registro.to_csv(archivo, mode='w', header=True, index=False, encoding='utf-8-sig')
        
        return redirect(url_for('index'))

EXCEL_FILE = "registrosregistros_visitantes.csv"


@app.route('/paqueteria_form', methods=['POST'])
def paqueteria_form():
    if request.method == 'POST':
        fecha = request.form['fecha']
        hora = request.form['horaEntrada']
        empresa = request.form['empresa']
        nombre = request.form['nombre']
        departamento = request.form['departamento']
        numero_guia = request.form['numero_guia']
        comentarios = request.form['comentarios']

        # Guardar CSV (tu código original)
        nuevo_registro = pd.DataFrame([[fecha,hora,empresa, nombre, departamento, numero_guia, comentarios]], 
                                      columns=['Fecha','Hora','Empresa de paquetería','Nombre del remitente',
                                               'Departamento del destinatario','Número de guía','Comentarios'])

        archivo = 'registros_paqueteria.csv'
        if os.path.exists(archivo):
            nuevo_registro.to_csv(archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            nuevo_registro.to_csv(archivo, mode='w', header=True, index=False, encoding='utf-8-sig')

        return redirect(url_for('index'))

@app.post("/registrar_salida1")
def registrar_salida1():
    data = request.get_json()
    gafete = str(data.get("gafete"))

    try:
        df = pd.read_csv(EXCEL_FILE, encoding='utf-8')

        # Normalizar tipo de datos
        df["Numero Gafete"] = df["Numero Gafete"].astype(str)

        # FILTRAR SOLO LOS QUE ESTÁN ACTIVOS
        registro_activo = df[(df["Numero Gafete"] == gafete) & (df["Estatus"] == "Activo")]

        # Si no está activo → no tiene sentido registrar salida
        if registro_activo.empty:
            return jsonify({"ok": False, "msg": "⚠️ Este gafete no tiene un registro activo actualmente."})

        # Registrar hora de salida
        hora_salida = datetime.now().strftime("%H:%M:%S")

        # Crear columna si no existe
        if "Hora de salida" not in df.columns:
            df["Hora de salida"] = ""

        # Actualizar solo el registro activo
        idx = registro_activo.index[0]
        df.loc[idx, "Estatus"] = "Inactivo"
        df.loc[idx, "Hora de salida"] = hora_salida

        # Guardar CSV
        df.to_csv(EXCEL_FILE, index=False, encoding='utf-8')

        return jsonify({
            "ok": True,
            "msg": f"✅ Salida registrada correctamente (Hora: {hora_salida})."
        })

    except Exception as e:
        return jsonify({"ok": False, "msg": f"Error procesando salida: {e}"})
    

@app.route('/proveedorForm', methods=['POST'])
def proveedorForm():
    if request.method == 'POST':
        nombre = request.form['nombreProve']
        apellidos = request.form['apellidoProve']
        empresaProve = request.form['empresaProve']
        servicioProve = request.form['servicioProve']
        personaProve = request.form['personaProve']
        areaProve = request.form.get('areaProve')
        detalleServicioProve = request.form['detalleServicioProve']
        horaEntrada = request.form['horaEntrada']
        fecha = request.form['fecha']

        registro_informes= pd.DataFrame([[nombre, apellidos, empresaProve, servicioProve, personaProve, areaProve, detalleServicioProve, horaEntrada, fecha]], columns=['Nombre','Apellidos','Empresa proveedora','Servicio que realiza','Persona a quien visita','Área / Oficina','Detalle del servicio','Hora de Registro','Fecha'])
        archivo_informes = 'registros_proveedores.csv'
        if os.path.exists(archivo_informes):
            registro_informes.to_csv(archivo_informes, mode='a', header=False, index=False, encoding='utf-8-sig')
        else:
            registro_informes.to_csv(archivo_informes, mode='w', header=True, index=False, encoding='utf-8-sig')
        
        return redirect(url_for('index'))

    


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)