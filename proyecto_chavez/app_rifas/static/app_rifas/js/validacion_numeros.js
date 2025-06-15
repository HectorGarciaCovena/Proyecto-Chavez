document.addEventListener('DOMContentLoaded', function () {
    const numeroInput = document.getElementById('numeroInput');
    const agregarBtn = document.getElementById('agregarNumeroBtn');
    const listaNumeros = document.getElementById('listaNumeros');
    const numerosFavoritosInput = document.getElementById('numerosFavoritosInput');
    const errorNumeros = document.getElementById('errorNumeros');
    const enviarPedidoBtn = document.getElementById('enviarPedidoBtn');
    const maxCantidad = parseInt(agregarBtn.dataset.max);
    const cedulaInput = document.getElementById('id_cedula');

    let numerosSeleccionados = [];

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
        enviarPedidoBtn.disabled = numerosSeleccionados.length !== maxCantidad;
    }

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
        let digitoVerificador = (10 - (total % 10)) % 10;
        return digitoVerificador === parseInt(cedula[9]);
    }

    if (cedulaInput) {
        cedulaInput.addEventListener('blur', function () {
            if (!validarCedula(this.value)) {
                alert('⚠️ La cédula ingresada no es válida.');
                this.classList.add('is-invalid');
            } else {
                this.classList.remove('is-invalid');
            }
        });
    }

    agregarBtn.addEventListener('click', function () {
        const numero = numeroInput.value.trim();

        if (!/^\d{6}$/.test(numero)) {
            errorNumeros.textContent = '⚠️ El número debe tener 6 dígitos.';
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
            .catch(error => {
                errorNumeros.textContent = '⚠️ Error al verificar el número.';
            });
    });
});


