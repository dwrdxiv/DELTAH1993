let renglones = [];

const formItem = document.getElementById("form-item");
const tablaBody = document.getElementById("tabla-body");
const statusBadge = document.getElementById("status-badge");
const btnGenerar = document.getElementById("btn-generar");
const btnLimpiar = document.getElementById("btn-limpiar");

// Establecer fecha de hoy por defecto
document.getElementById("doc-fecha").valueAsDate = new Date();

function mostrarEstado(mensaje, tipo = "ok") {
  statusBadge.textContent = mensaje;
  statusBadge.className = `badge ${tipo}`;
}

function renderizarTabla() {
  tablaBody.innerHTML = "";
  renglones.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.cant}</td>
      <td>${item.descripcion}</td>
      <td>${item.precio.toFixed(2)}</td>
      <td>${item.alic}</td>
      <td>${item.total.toFixed(2)}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="eliminarRenglon(${index})">Quitar</button>
      </td>
    `;
    tablaBody.appendChild(tr);
  });
}

function eliminarRenglon(index) {
  renglones.splice(index, 1);
  renderizarTabla();
}

formItem.addEventListener("submit", (e) => {
  e.preventDefault();
  const cant = parseFloat(document.getElementById("item-cant").value);
  const descripcion = document.getElementById("item-desc").value.trim();
  const precio = parseFloat(document.getElementById("item-precio").value);
  const alic = document.getElementById("item-alic").value;

  if (!cant || !descripcion || isNaN(precio)) {
    mostrarEstado("Verifica los datos del renglón", "error");
    return;
  }

  renglones.push({
    cant,
    descripcion,
    precio,
    total: cant * precio
  });

  renderizarTabla();
  formItem.reset();
  document.getElementById("item-cant").focus();
  mostrarEstado(`Renglón agregado (${renglones.length})`);
});

btnLimpiar.addEventListener("click", () => {
  renglones = [];
  renderizarTabla();
  document.querySelectorAll("input").forEach(input => input.value = "");
  document.getElementById("doc-fecha").valueAsDate = new Date();
  mostrarEstado("Formulario limpiado");
});

btnGenerar.addEventListener("click", async () => {
  if (renglones.length === 0) {
    mostrarEstado("Debes ingresar al menos un renglón", "error");
    return;
  }

  const payload = {
    nombre_archivo: document.getElementById("pdf-nombre").value,
    fecha: document.getElementById("doc-fecha").value,
    cliente: {
      nombre: document.getElementById("cli-nombre").value,
      rif: document.getElementById("cli-rif").value,
      domicilio: document.getElementById("cli-domicilio").value,
      orden: document.getElementById("cli-orden").value
    },
    factura: {
      fecha: document.getElementById("doc-fecha").value,
      numero: document.getElementById("pdf-nombre").value
    },
    items: renglones,
    // Coloca aquí las medidas exactas en mm de la hoja que tienes:
    ancho_mm: 210,
    alto_mm: 281
  };

  mostrarEstado("Generando documento...", "ok");

  try {
    // pywebview inyecta la API nativamente en window.pywebview.api
    const respuesta = await window.pywebview.api.generar_pdf(payload);
    if (respuesta.exito) {
      mostrarEstado(respuesta.mensaje, "ok");
    } else {
      mostrarEstado(respuesta.mensaje, "error");
    }
  } catch (err) {
    mostrarEstado("Error al invocar API de Python: " + err, "error");
  }
});