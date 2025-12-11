document.addEventListener("DOMContentLoaded", function () {
    const grid = document.getElementById("gridNumeros");
    const contadorSeleccion = document.getElementById("contadorSeleccion");
    const btnConfirmar = document.getElementById("confirmarSeleccionBtn");
    const inputBuscar = document.getElementById("buscarNumero");

    if (!grid || !contadorSeleccion || !btnConfirmar) return;

    let ultimoEncontrado = null;

    // ==========================
    // PARÁMETROS DESDE DJANGO
    // ==========================
    // numeros y vendidos vienen de json_script en el template
    const numeros = JSON.parse(
        document.getElementById("numeros-json").textContent || "[]"
    );
    const vendidosSet = new Set(
        JSON.parse(document.getElementById("vendidos-json").textContent || "[]")
    );

    const cantidadMaxima = parseInt(grid.dataset.cantidad || "1", 10);

    // ==========================
    // SELECCIONADOS
    // ==========================
    const seleccionados = new Set();

    // Cargar selección previa (si existe) desde localStorage
    const prev = (localStorage.getItem("numeros_seleccionados") || "")
        .split(",")
        .filter((n) => n);

    prev.forEach((n) => seleccionados.add(n));

    // ==========================
    // CREAR EL GRID
    // ==========================
    function crearGrid() {
        const fragment = document.createDocumentFragment();

        numeros.forEach((numStr) => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "numero-btn btn btn-sm";
            btn.textContent = numStr;
            btn.dataset.numero = numStr;

            const esVendido = vendidosSet.has(numStr);

            if (esVendido) {
                btn.classList.add("vendido");
                btn.disabled = true;
            }

            // Marcar seleccionados previamente (si no están vendidos)
            if (!esVendido && seleccionados.has(numStr)) {
                btn.classList.add("seleccionado");
            }

            btn.addEventListener("click", () => manejarClick(btn));
            fragment.appendChild(btn);
        });

        grid.innerHTML = "";
        grid.appendChild(fragment);
        actualizarUI();
    }

    // ==========================
    // MANEJAR SELECCIÓN
    // ==========================
    function manejarClick(btn) {
        const num = btn.dataset.numero;

        if (seleccionados.has(num)) {
            seleccionados.delete(num);
            btn.classList.remove("seleccionado");
        } else {
            if (seleccionados.size >= cantidadMaxima) {
                alert(`Solo puedes seleccionar ${cantidadMaxima} número(s).`);
                return;
            }
            seleccionados.add(num);
            btn.classList.add("seleccionado");
        }

        actualizarUI();
    }

    function actualizarUI() {
        contadorSeleccion.textContent = `${seleccionados.size}/${cantidadMaxima} números seleccionados`;
        btnConfirmar.disabled = seleccionados.size === 0;
    }

    // ==========================
    // CONFIRMAR SELECCIÓN
    // ==========================
    btnConfirmar.addEventListener("click", function () {
        const seleccionArray = Array.from(seleccionados).sort(
            (a, b) => parseInt(a, 10) - parseInt(b, 10)
        );

        // Mantener el mismo formato que usa validaciones.js:
        // "0001,0005,0120"
        localStorage.setItem("numeros_seleccionados", seleccionArray.join(","));

        window.close();
    });

    // ==========================
    // BÚSQUEDA
    // ==========================
    if (inputBuscar) {
        inputBuscar.addEventListener("input", function () {
            let valor = inputBuscar.value.trim();

            // Quitar resaltado previo
            if (ultimoEncontrado) {
                ultimoEncontrado.classList.remove("numero-encontrado");
                ultimoEncontrado = null;
            }

            if (!valor) return;

            // Buscar por coincidencia exacta
            const btn = [...grid.children].find(
                (b) => b.dataset.numero === valor
            );

            if (!btn) return;

            ultimoEncontrado = btn;
            btn.classList.add("numero-encontrado");

            btn.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });
        });
    }

    // ==========================
    // INICIALIZAR
    // ==========================
    crearGrid();
});
