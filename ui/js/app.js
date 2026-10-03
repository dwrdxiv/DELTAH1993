let renglones = [];

const formItem = document.getElementById("form-item");
const tablaBody = document.getElementById("tabla-body");
const statusBadge = document.getElementById("status-badge");
const btnGenerar = document.getElementById("btn-generar");
const btnLimpiar = document.getElementById("btn-limpiar");

const spanTotalBase = document.getElementById("total-base");
const spanTotalExento = document.getElementById("total-exento");
const spanTotalIva = document.getElementById("total-iva");
const spanTotalGeneral = document.getElementById("total-general");

const inputDia = document.getElementById("doc-dia");
const inputMes = document.getElementById("doc-mes");
const inputAno = document.getElementById("doc-anio");

// 1. Cargar fecha actual por defecto (DD, MM, AAAA)
function cargarFechaActual() {
  const hoy = new Date();
  inputDia.value = String(hoy.getDate()).padStart(2, "0");
  inputMes.value = String(hoy.getMonth() + 1).padStart(2, "0");
  inputAno.value = hoy.getFullYear();
}

cargarFechaActual();

// 2. Salto automático al siguiente campo cuando se completan los dígitos
function configurarSaltoAutomatico(actual, siguiente, longitud) {
  actual.addEventListener("input", () => {
    // Permitir solo números
    actual.value = actual.value.replace(/\D/g, "");
    if (actual.value.length >= longitud && siguiente) {
      siguiente.focus();
      siguiente.select();
    }
  });
}

configurarSaltoAutomatico(inputDia, inputMes, 2);
configurarSaltoAutomatico(inputMes, inputAno, 2);
configurarSaltoAutomatico(inputAno, null, 4);

function mostrarEstado(mensaje, tipo = "ok") {
  statusBadge.textContent = mensaje;
  statusBadge.className = `badge ${tipo}`;
}

function formatearMonto(monto) {
  const valor = Number(monto) || 0;
  return new Intl.NumberFormat("es-VE", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(valor);
}

function calcularTotales() {
  let baseImponible = 0;
  let exento = 0;

  renglones.forEach(item => {
    // subtotal = cant * precioBase
    if (item.tieneIVA === true) {
      baseImponible += item.subtotal;
    } else {
      exento += item.subtotal;
    }
  });

  const iva = baseImponible * 0.16;
  const totalGeneral = baseImponible + iva + exento;

  spanTotalBase.textContent = formatearMonto(baseImponible);
  spanTotalExento.textContent = formatearMonto(exento);
  spanTotalIva.textContent = formatearMonto(iva);
  spanTotalGeneral.textContent = formatearMonto(totalGeneral);

  // Retornamos el objeto para reutilizarlo al generar el PDF
  return {
    baseImponible,
    exento,
    iva,
    totalGeneral
  };
}

function renderizarTabla() {
  tablaBody.innerHTML = "";
  renglones.forEach((item, index) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${index + 1}</td>
      <td>${item.cant}</td>
      <td>${item.descripcion}</td>
      <td>${formatearMonto(item.precioBase)}</td>
      <td>${item.tieneIVA ? "16%" : "Exento"}</td>
      <td>${formatearMonto(item.subtotal)}</td>
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
  const precioBase = parseFloat(document.getElementById("item-precio").value);
  const tieneIVA = Boolean(document.getElementById("item-iva").checked);

  if (!cant || !descripcion || isNaN(precioBase) || precioBase <= 0) {
    mostrarEstado("Verifica los datos del renglón", "error");
    return;
  }
  
  const subtotal = cant * precioBase;
  const total = tieneIVA ? subtotal * 1.16 : subtotal;

  renglones.push({
    cant,
    descripcion,
    precioBase,
    tieneIVA,
    subtotal,
    total
  });

  renderizarTabla();
  calcularTotales();
  formItem.reset();
  document.getElementById("item-iva").checked = false;
  document.getElementById("item-cant").focus();
  mostrarEstado(`Renglón agregado (${renglones.length})`);
});

btnLimpiar.addEventListener("click", () => {
  renglones = [];
  renderizarTabla();
  calcularTotales();
  document.querySelectorAll("input").forEach(input => input.value = "");
  cargarFechaActual();
  mostrarEstado("Formulario limpiado");
});

btnGenerar.addEventListener("click", async () => {
  if (renglones.length === 0) {
    mostrarEstado("Debes ingresar al menos un renglón", "error");
    return;
  }

  const resumenTotales = calcularTotales();

  const payload = {
    nombre_archivo: document.getElementById("pdf-nombre").value,
    cliente: {
      nombre: document.getElementById("cli-nombre").value,
      rif: document.getElementById("cli-rif").value,
      domicilio: document.getElementById("cli-domicilio").value,
      orden: document.getElementById("cli-orden").value
    },
    factura: {
      fecha: {
        dia: document.getElementById("doc-dia").value,
        mes: document.getElementById("doc-mes").value,
        anio: document.getElementById("doc-anio").value
      },
      numero: document.getElementById("pdf-nombre").value
    },
    items: renglones,
    totales: resumenTotales,
    // Coloca aquí las medidas exactas en mm de la hoja que tienes:
    ancho_mm: 216,
    alto_mm: 279
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