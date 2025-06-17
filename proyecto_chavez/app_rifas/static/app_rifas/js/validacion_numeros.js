document.addEventListener('DOMContentLoaded', function () {
    const numeroInput = document.getElementById('numeroInput');
    const agregarBtn = document.getElementById('agregarNumeroBtn');
    const listaNumeros = document.getElementById('listaNumeros');
    const numerosFavoritosInput = document.getElementById('numerosFavoritosInput');
    const errorNumeros = document.getElementById('errorNumeros');
    const enviarPedidoBtn = document.getElementById('enviarPedidoBtn');
    const contadorNumeros = document.getElementById('contadorNumeros');
    const cedulaInput = document.getElementById('id_cedula');
    const metodoPago = document.getElementById('id_metodo_pago');
    const buscarBtn = document.getElementById('buscarCedulaBtn');
    const alertaCedula = document.getElementById('alertaCedula');

    const camposParticipante = [
        'id_cedula',
        'id_nombre',
        'id_apellido',
        'id_email',
        'id_telefono',
        'id_direccion',
        'id_ciudad',
        'id_provincia',
        'id_pais'
    ];

    const maxCantidad = parseInt(agregarBtn.dataset.max);
    let numerosSeleccionados = [];

    function validarCedula(cedula) {
        if (!/^\d{10}$/.test(cedula)) return false;
        let total = 0;
        for (let i = 0; i < 9; i++) {
            let digito = parseInt(cedula[i]);
            if (i % 2 === 0) {
                digito *= 2;
                if (digito > 9) digito -= 9;
            }
            total += digito;
        }
        let verificador = (10 - (total % 10)) % 10;
        return verificador === parseInt(cedula[9]);
    }

    function verificarFormularioCompleto() {
        const camposLlenos = camposParticipante.every(id => {
            const input = document.getElementById(id);
            return input && input.value.trim().length > 0;
        });

        const metodoPagoOk = metodoPago && metodoPago.value !== '';
        const cedulaOk = validarCedula(cedulaInput.value);
        const numerosOk = numerosSeleccionados.length === maxCantidad;

        const completo = camposLlenos && metodoPagoOk && cedulaOk && numerosOk;

        enviarPedidoBtn.disabled = !completo;
        enviarPedidoBtn.title = completo
            ? ''
            : 'Debe completar todos los campos obligatorios y seleccionar los números requeridos';
    }

    function actualizarListaNumeros() {
        listaNumeros.innerHTML = '';
        numerosSeleccionados.forEach((numero, index) => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.textContent = numero;

            const btnEliminar = document.createElement('button');
            btnEliminar.className = 'btn btn-danger btn-sm';
            btnEliminar.textContent = 'Eliminar';
            btnEliminar.onclick = () => {
                numerosSeleccionados.splice(index, 1);
                actualizarListaNumeros();
            };

            li.appendChild(btnEliminar);
            listaNumeros.appendChild(li);
        });

        numerosFavoritosInput.value = numerosSeleccionados.join(',');
        agregarBtn.disabled = numerosSeleccionados.length >= maxCantidad;
        contadorNumeros.textContent = `${numerosSeleccionados.length}/${maxCantidad} números agregados`;
        verificarFormularioCompleto();
    }

    agregarBtn.addEventListener('click', function () {
        const numero = numeroInput.value.trim();

        if (numerosSeleccionados.length >= maxCantidad) {
            errorNumeros.textContent = `⚠️ Ya has agregado el máximo de ${maxCantidad} números.`;
            return;
        }

        if (!/^\d{5}$/.test(numero)) {
            errorNumeros.textContent = '⚠️ El número debe tener 5 dígitos.';
            return;
        }

        if (numerosSeleccionados.includes(numero)) {
            errorNumeros.textContent = '⚠️ Este número ya fue agregado.';
            return;
        }

        fetch(`/verificar-numero/${numero}/`)
            .then(response => response.json())
            .then(data => {
                if (data.vendido) {
                    errorNumeros.textContent = `⚠️ El número ${numero} ya ha sido vendido.`;
                } else {
                    errorNumeros.textContent = '';
                    numerosSeleccionados.push(numero);
                    actualizarListaNumeros();
                    numeroInput.value = '';
                }
            })
            .catch(() => {
                errorNumeros.textContent = '⚠️ Error al verificar el número.';
            });
    });

    function autocompletarCedula() {
        const cedula = cedulaInput.value.trim();
        alertaCedula.classList.add('d-none');

        if (!validarCedula(cedula)) {
            alert('⚠️ La cédula ingresada no es válida.');
            cedulaInput.classList.add('is-invalid');
            return;
        }

        cedulaInput.classList.remove('is-invalid');

        fetch(`/verificar-participante/${cedula}/`)
            .then(response => response.json())
            .then(data => {
                if (data.existe) {
                    document.getElementById('id_nombre').value = data.nombre;
                    document.getElementById('id_apellido').value = data.apellido;
                    document.getElementById('id_email').value = data.email;
                    document.getElementById('id_telefono').value = data.telefono;
                    document.getElementById('id_direccion').value = data.direccion;
                    document.getElementById('id_ciudad').value = data.ciudad;
                    document.getElementById('id_provincia').value = data.provincia;
                    document.getElementById('id_pais').value = data.pais;
                } else {
                    alertaCedula.classList.remove('d-none');
                }
                verificarFormularioCompleto();
            })
            .catch(() => {
                console.error("Error al consultar cédula.");
            });
    }

    if (cedulaInput) {
        cedulaInput.addEventListener('blur', autocompletarCedula);
    }

    if (buscarBtn) {
        buscarBtn.addEventListener('click', autocompletarCedula);
    }

    camposParticipante.forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('input', verificarFormularioCompleto);
        }
    });

    if (metodoPago) {
        metodoPago.addEventListener('change', verificarFormularioCompleto);
    }

    contadorNumeros.textContent = `0/${maxCantidad} números agregados`;
    verificarFormularioCompleto();
});




