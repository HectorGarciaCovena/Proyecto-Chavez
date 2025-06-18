document.addEventListener('DOMContentLoaded', function () {
    const listaNumeros = document.getElementById('listaNumeros');
    const numerosFavoritosInput = document.getElementById('numerosFavoritosInput');
    const contadorNumeros = document.getElementById('contadorNumeros');
    const enviarPedidoBtn = document.getElementById('enviarPedidoBtn');
    const cedulaInput = document.getElementById('id_cedula');
    const metodoPago = document.getElementById('id_metodo_pago');
    const buscarCedulaBtn = document.getElementById('buscarCedulaBtn');

    const cantidadMaxima = parseInt(document.querySelector('input[name="cantidad"]').value);

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
        const numeros = numerosFavoritosInput.value.trim().split(',').filter(n => n);
        const numerosOk = numeros.length === cantidadMaxima;

        const completo = camposLlenos && metodoPagoOk && cedulaOk && numerosOk;

        enviarPedidoBtn.disabled = !completo;
        enviarPedidoBtn.title = completo
            ? ''
            : `Debe completar todos los campos y seleccionar exactamente ${cantidadMaxima} número(s).`;
    }

    function mostrarNumerosSeleccionados(numeros) {
        listaNumeros.innerHTML = '<h6 class="mb-2">Números seleccionados:</h6>';
        const ul = document.createElement('ul');
        ul.className = 'list-group';

        numeros.forEach(n => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = n;
            ul.appendChild(li);
        });

        listaNumeros.appendChild(ul);
        contadorNumeros.textContent = `${numeros.length}/${cantidadMaxima} números agregados`;
    }

    // ========== Cargar desde localStorage si hay datos ==========
    const seleccion = localStorage.getItem('numeros_seleccionados');
    if (seleccion) {
        const numeros = seleccion.split(',');
        numerosFavoritosInput.value = seleccion;
        mostrarNumerosSeleccionados(numeros);
        localStorage.removeItem('numeros_seleccionados');
    }

    // ========== Autocompletado por cédula ==========
    function buscarCedula() {
        const cedula = cedulaInput.value.trim();
        if (!validarCedula(cedula)) {
            alert('⚠️ La cédula ingresada no es válida.');
            cedulaInput.classList.add('is-invalid');
            return;
        }

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
                    alert('⚠️ No se encontraron datos para esta cédula. Por favor, complete el formulario.');
                }
                verificarFormularioCompleto();
            });
    }

    if (cedulaInput) {
        cedulaInput.addEventListener('blur', buscarCedula);
    }

    if (buscarCedulaBtn) {
        buscarCedulaBtn.addEventListener('click', buscarCedula);
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

    verificarFormularioCompleto();
});



