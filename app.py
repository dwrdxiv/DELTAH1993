import os
import sys
import webview
from fpdf import FPDF

# Función para resolver rutas tanto en desarrollo como empaquetado
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def fmt_monto(valor):
    try:
        # Formato inicial: 1,000,000.00 -> convierte a 1.000.000,00
        return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

class FacturaAPI:
    def generar_pdf(self, payload):
        try:
            cliente = payload.get("cliente", {})
            factura = payload.get("factura", {})
            items = payload.get("items", [])
            nombre_archivo = payload.get("nombre_archivo", "factura_salida").strip()

            if not nombre_archivo:
                nombre_archivo = "factura"

            # Formato en mm: (ancho, alto). Ajusta con las medidas que tomaste
            ancho_mm = float(payload.get("ancho_mm", 216))
            alto_mm = float(payload.get("alto_mm", 279))

            pdf = FPDF(orientation='P', unit='mm', format=(ancho_mm, alto_mm))
            pdf.add_page()
            pdf.set_font("Helvetica", size=10)

            # === ENCABEZADO / CLIENTE (Coordenadas milimétricas) ===
            pdf.set_xy(42, 35)
            pdf.cell(120, 5, text=str(cliente.get("nombre", "")), border=1, align='C')
            
            pdf.set_xy(38, 40)
            pdf.cell(125, 5, text=str(cliente.get("domicilio", "")), border=1, align='C')
            
            pdf.set_xy(15, 55)
            pdf.cell(40, 5, text=str(cliente.get("rif", "")), border=1, align='C')

            pdf.set_xy(55, 55)
            pdf.cell(45, 5, text=str(cliente.get("orden", "")), border=1, align='C')

            # === FECHA / FACTURA ===
            pdf.set_xy(32, 30)
            pdf.cell(10, 5, text=str(factura.get("fecha", "").get("dia", "")), border=1, align='C')

            pdf.set_xy(42, 30)
            pdf.cell(10, 5, text=str(factura.get("fecha", "").get("mes", "")), border=1, align='C')

            pdf.set_xy(52, 30)
            pdf.cell(15, 5, text=str(factura.get("fecha", "").get("anio", "")), border=1, align='C')
            
            # === RENGLONES DE LA TABLA ===
            y_inicial = 65   # Milímetros desde arriba donde inicia el primer renglón
            alto_fila = 6  # Espacio entre cada renglón

            for i, item in enumerate(items):
                y = y_inicial + (i * alto_fila)
                
                cant = item.get("cant", "")
                descripcion = item.get("descripcion", "")
                precio_base = fmt_monto(item.get("precioBase", 0))
                tiene_iva = item.get("tieneIVA", False)
                total_renglon = fmt_monto(item.get("subtotal", 0))

                pdf.set_xy(15, y)
                pdf.cell(15, 5, text=str(cant), border=1, align='C')

                pdf.set_xy(35, y)
                pdf.cell(90, 5, text=str(descripcion), border=1, align='C')

                pdf.set_xy(135, y)
                pdf.cell(25, 5, text=str(precio_base), border=1, align='C')

                pdf.set_xy(165, y)
                pdf.cell(10, 5, text="16%" if tiene_iva else "E", border=1, align='C')

                # Este campo ya contiene el 16% sumado si el checkbox estaba marcado
                pdf.set_xy(175, y)
                pdf.cell(30, 5, text=str(total_renglon), border=1, align='C')

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
        width=800,
        height=600,
        min_size=(900, 600)
    )
    webview.start(debug=True)  # debug=True permite clic derecho -> inspeccionar elemento

if __name__ == "__main__":
    main()