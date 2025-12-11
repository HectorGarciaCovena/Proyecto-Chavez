document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("form");
    if (!form) return;

    const listaNumeros = document.getElementById("listaNumeros");
    const numerosFavoritosInput = document.getElementById("numerosFavoritosInput");
    const contadorNumeros = document.getElementById("contadorNumeros");
    const cedulaInput = document.getElementById("id_cedula");
    const buscarCedulaBtn = document.getElementById("buscarCedulaBtn");
    const metodoPagoInput = document.getElementById("metodo_pago");
    const btnContinuarPago = document.getElementById("continuarPagoBtn");

    const cantidadInput = document.querySelector('input[name="cantidad"]');
    const cantidadMaxima = cantidadInput ? parseInt(cantidadInput.value) : 0;

    const camposParticipante = [
        "id_cedula",
        "id_nombre",
        "id_apellido",
        "id_email",
        "id_telefono",
        "id_direccion",
        "id_ciudad",
        "id_provincia",
        "id_pais",
    ];

    // ========= VALIDAR CÉDULA =========
    function validarCedula(cedula) {
        if (!/^\d{10}$/.test(cedula)) return false;
        let total = 0;
        for (let i = 0; i < 9; i++) {
            let digito = parseInt(cedula[i], 10);
            if (i % 2 === 0) {
                digito *= 2;
                if (digito > 9) digito -= 9;
            }
            total += digito;
        }
        const verificador = (10 - (total % 10)) % 10;
        return verificador === parseInt(cedula[9], 10);
    }

    // ========= VALIDAR FORMULARIO COMPLETO =========
    function verificarFormularioCompleto() {
        const camposLlenos = camposParticipante.every((id) => {
            const input = document.getElementById(id);
            return !input || input.value.trim().length > 0;
        });

        const cedulaOk = cedulaInput ? validarCedula(cedulaInput.value) : true;

        const numeros =
            numerosFavoritosInput && numerosFavoritosInput.value.trim()
                ? numerosFavoritosInput.value.split(",").filter((n) => n)
                : [];

        const numerosOk = cantidadMaxima
            ? numeros.length === cantidadMaxima
            : true;

        const metodoPagoSeleccionado =
            metodoPagoInput && metodoPagoInput.value.trim() !== "";

        return camposLlenos && cedulaOk && numerosOk && metodoPagoSeleccionado;
    }

    // ========= SUBMIT GENERAL (sin comprobante, eso va en metodo_pago.js) =========
    form.addEventListener("submit", function (event) {
        if (!verificarFormularioCompleto()) {
            event.preventDefault();
            alert(
                "⚠️ Debes completar todos los campos, seleccionar exactamente " +
                    cantidadMaxima +
                    " números y elegir un método de pago."
            );
        }
    });

    // ========= NÚMEROS SELECCIONADOS =========
    function mostrarNumerosSeleccionados(numeros) {
        if (!listaNumeros || !contadorNumeros) return;

        listaNumeros.innerHTML =
            '<h6 class="mb-2">Números seleccionados:</h6>';
        const ul = document.createElement("ul");
        ul.className = "list-group";

        numeros.forEach((n, idx) => {
            const li = document.createElement("li");
            li.className =
                "list-group-item d-flex justify-content-between align-items-center";
            li.textContent = n;

            const btnEliminar = document.createElement("button");
            btnEliminar.className = "btn btn-danger btn-sm ms-2";
            btnEliminar.textContent = "Eliminar";
            btnEliminar.onclick = () => {
                numeros.splice(idx, 1);
                localStorage.setItem(
                    "numeros_seleccionados",
                    numeros.join(",")
                );
                if (numerosFavoritosInput) {
                    numerosFavoritosInput.value = numeros.join(",");
                }
                mostrarNumerosSeleccionados(numeros);
            };

            li.appendChild(btnEliminar);
            ul.appendChild(li);
        });

        listaNumeros.appendChild(ul);
        contadorNumeros.textContent = `${numeros.length}/${cantidadMaxima} números agregados`;

        if (numerosFavoritosInput) {
            numerosFavoritosInput.value = numeros.join(",");
        }
    }

    function cargarNumerosDesdeLocalStorage() {
        const seleccion = localStorage.getItem("numeros_seleccionados");
        if (seleccion) {
            const numeros = seleccion.split(",").filter((n) => n);
            mostrarNumerosSeleccionados(numeros);
        }
    }

    window.addEventListener("focus", cargarNumerosDesdeLocalStorage);
    cargarNumerosDesdeLocalStorage();

    // ========= BÚSQUEDA POR CÉDULA =========
    function buscarCedula() {
        if (!cedulaInput) return;
        const cedula = cedulaInput.value.trim();
        if (!validarCedula(cedula)) {
            alert("⚠️ La cédula ingresada no es válida.");
            cedulaInput.classList.add("is-invalid");
            return;
        }

        fetch(`/verificar-participante/${cedula}/`)
            .then((response) => response.json())
            .then((data) => {
                if (data.existe) {
                    document.getElementById("id_nombre").value = data.nombre;
                    document.getElementById("id_apellido").value =
                        data.apellido;
                    document.getElementById("id_email").value = data.email;
                    document.getElementById("id_telefono").value =
                        data.telefono;
                    document.getElementById("id_direccion").value =
                        data.direccion;
                    document.getElementById("id_ciudad").value = data.ciudad;
                    document.getElementById("id_provincia").value =
                        data.provincia;
                    document.getElementById("id_pais").value = data.pais;
                } else {
                    alert(
                        "⚠️ No se encontraron datos para esta cédula. Por favor, complete el formulario."
                    );
                }
            });
    }

    if (cedulaInput) cedulaInput.addEventListener("blur", buscarCedula);
    if (buscarCedulaBtn)
        buscarCedulaBtn.addEventListener("click", buscarCedula);

    camposParticipante.forEach((id) => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener("input", () => {
                // hook para futuro
            });
        }
    });

    // ========= PAYPAL (detalle_pedido.html) =========
    if (btnContinuarPago) {
        btnContinuarPago.addEventListener("click", function () {
            const ordenId = this.dataset.ordenId;

            fetch(`/paypal/create/${ordenId}/`)
                .then((response) => response.json())
                .then((data) => {
                    if (data && data.links) {
                        const approveUrl = data.links.find(
                            (link) => link.rel === "approve"
                        );
                        if (approveUrl) {
                            window.location.href = approveUrl.href;
                        } else {
                            alert(
                                "No se pudo encontrar la URL de aprobación de PayPal."
                            );
                        }
                    } else {
                        alert(
                            "Error al crear la orden de pago en PayPal."
                        );
                    }
                })
                .catch((error) => {
                    console.error("Error al conectar con PayPal:", error);
                    alert("Ocurrió un error al procesar el pago.");
                });
        });
    }
});
