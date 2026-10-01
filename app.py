import os
import sys
import webview
from fpdf import FPDF

# Función para resolver rutas tanto en desarrollo como empaquetado
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class FacturaAPI:
    def generar_pdf(self, payload):
        try:
            cliente = payload.get("cliente", {})
            conductor = payload.get("conductor", {})
            items = payload.get("items", [])
            nombre_archivo = payload.get("nombre_archivo", "factura_salida").strip()

            if not nombre_archivo:
                nombre_archivo = "factura_salida"

            # Formato en mm: (ancho, alto). Ajusta con las medidas que tomaste
            ancho_mm = float(payload.get("ancho_mm", 215.9))
            alto_mm = float(payload.get("alto_mm", 279.4))

            pdf = FPDF(orientation='P', unit='mm', format=(ancho_mm, alto_mm))
            pdf.add_page()
            pdf.set_font("Helvetica", size=10)

            # === ENCABEZADO / CLIENTE (Coordenadas milimétricas) ===
            pdf.set_xy(30, 40)
            pdf.cell(80, 5, txt=str(cliente.get("nombre", "")))
            
            pdf.set_xy(140, 40)
            pdf.cell(40, 5, txt=str(cliente.get("rif", "")))

            pdf.set_xy(30, 48)
            pdf.cell(100, 5, txt=str(cliente.get("domicilio", "")))

            pdf.set_xy(140, 48)
            pdf.cell(40, 5, txt=str(cliente.get("telefono", "")))

            # === FECHA / CONDUCTOR ===
            pdf.set_xy(140, 32)
            pdf.cell(40, 5, txt=str(payload.get("fecha", "")))

            pdf.set_xy(30, 60)
            pdf.cell(80, 5, txt=str(conductor.get("nombre", "")))

            pdf.set_xy(140, 60)
            pdf.cell(40, 5, txt=str(conductor.get("placa", "")))

            # === RENGLONES DE LA TABLA ===
            y_inicial = 85   # Milímetros desde arriba donde inicia el primer renglón
            alto_fila = 7.0  # Espacio entre cada renglón

            for i, item in enumerate(items):
                y = y_inicial + (i * alto_fila)
                
                pdf.set_xy(15, y)
                pdf.cell(15, 5, txt=str(item.get("cant", "")))
                
                pdf.set_xy(35, y)
                pdf.cell(90, 5, txt=str(item.get("descripcion", "")))
                
                pdf.set_xy(135, y)
                pdf.cell(25, 5, txt=f"{float(item.get('precio', 0)):.2f}")
                
                pdf.set_xy(165, y)
                pdf.cell(30, 5, txt=f"{float(item.get('total', 0)):.2f}")

            ruta_salida = f"{nombre_archivo}.pdf"
            pdf.output(ruta_salida)

            return {"exito": True, "mensaje": f"Archivo guardado como: {ruta_salida}"}
        except Exception as e:
            return {"exito": False, "mensaje": f"Error: {str(e)}"}

def main():
    api = FacturaAPI()
    html_path = get_resource_path(os.path.join("ui", "index.html"))

    # Crear ventana nativa con motor WebKit
    window = webview.create_window(
        title="Generador de Facturas",
        url=html_path,
        js_api=api,
        width=1100,
        height=720,
        min_size=(900, 600)
    )
    webview.start(debug=True)  # debug=True permite clic derecho -> inspeccionar elemento

if __name__ == "__main__":
    main()