// Главный JavaScript файл для админ-панели

document.addEventListener('DOMContentLoaded', function() {
    console.log('Discord Universe Admin Panel loaded');

    // Плавное появление элементов
    const faders = document.querySelectorAll('.fade-in');
    const appearOptions = {
        threshold: 0.15,
        rootMargin: "0px 0px -100px 0px"
    };

    const appearOnScroll = new IntersectionObserver(function(entries, appearOnScroll) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            } else {
                entry.target.classList.add('appear');
                appearOnScroll.unobserve(entry.target);
            }
        });
    }, appearOptions);

    faders.forEach(fader => {
        appearOnScroll.observe(fader);
    });

    // Обработка модальных окон
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        modal.addEventListener('shown.bs.modal', function () {
            const input = modal.querySelector('input, textarea, select');
            if (input) {
                input.focus();
            }
        });
    });

    // Обработка кнопок удаления с подтверждением
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm') || 'Вы уверены?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // AJAX для динамических действий
    const ajaxForms = document.querySelectorAll('[data-ajax]');
    ajaxForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            const url = this.action;

            fetch(url, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Успешно!');
                    if (data.redirect) {
                        window.location.href = data.redirect;
                    }
                    if (data.reload) {
                        location.reload();
                    }
                } else {
                    alert('Ошибка: ' + (data.message || 'Неизвестная ошибка'));
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при выполнении запроса');
            });
        });
    });

    // Обновление значений ползунков
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        const output = document.getElementById(input.id + 'Value');
        if (output) {
            output.textContent = input.value + (input.getAttribute('data-unit') || '');
            input.addEventListener('input', function() {
                output.textContent = this.value + (this.getAttribute('data-unit') || '');
            });
        }
    });

    // Мобильное меню
    const mobileToggle = document.querySelector('.navbar-toggler');
    const sidebar = document.querySelector('#sidebar');
    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Toasts
    const toastTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="toast"]'));
    const toastList = toastTriggerList.map(function (toastTriggerEl) {
        return new bootstrap.Toast(toastTriggerEl);
    });
});

// Функция для обновления данных без перезагрузки страницы
function refreshData(containerId, url) {
    fetch(url)
        .then(response => response.text())
        .then(html => {
            const container = document.getElementById(containerId);
            if (container) {
                container.innerHTML = html;
            }
        })
        .catch(error => {
            console.error('Error refreshing data:', error);
        });
}

// Функция для отображения уведомлений
function showNotification(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.role = 'alert';
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');

    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    // Автоматическое удаление через 5 секунд
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// Функция для загрузки индикатора
function showLoading(selector) {
    const element = document.querySelector(selector);
    if (element) {
        element.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Загрузка...</span></div></div>';
    }
}

// Функция для обработки загрузки файлов
function handleFileUpload(inputId, previewId) {
    const input = document.getElementById(inputId);
    const preview = document.getElementById(previewId);

    if (!input || !preview) return;

    input.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });
}

// Экспорт функций для глобального использования
window.refreshData = refreshData;
window.showNotification = showNotification;
window.showLoading = showLoading;
window.handleFileUpload = handleFileUpload;