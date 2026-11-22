function getCookie(name) {
    var value = null;
    document.cookie.split(';').forEach(function (part) {
        var item = part.trim();
        if (item.indexOf(name + '=') === 0) {
            value = decodeURIComponent(item.slice(name.length + 1));
        }
    });
    return value;
}

document.addEventListener('DOMContentLoaded', function () {
    var burger = document.getElementById('burger-btn');
    var nav = document.getElementById('main-nav');

    if (burger && nav) {
        burger.addEventListener('click', function () {
            nav.classList.toggle('open');
        });
    }

    var form = document.querySelector('form[data-check="form"]');
    if (form) {
        form.addEventListener('submit', function (e) {
            var problems = [];
            var fields = form.querySelectorAll('input, textarea, select');

            fields.forEach(function (field) {
                var value = field.value.trim();
                var text = (field.getAttribute('placeholder') || field.name).toLowerCase();

                if (field.name === 'slot' && value === '') {
                    problems.push('Выберите интервал доставки');
                } else if (field.required && value === '') {
                    problems.push('Заполните все обязательные поля');
                }
                if (value.indexOf('@') !== -1 && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value)) {
                    problems.push('Проверьте адрес почты');
                }
                if (text.indexOf('телефон') !== -1 && value !== '' && value.replace(/\D/g, '').length < 10) {
                    problems.push('В телефоне должно быть не меньше 10 цифр');
                }
                if (field.name === 'password1' && value.length > 0 && value.length <= 5) {
                    problems.push('Пароль должен быть больше 5 символов');
                }
                if (field.name === 'card_text' && value.length > 255) {
                    problems.push('Текст открытки слишком длинный, максимум 255 символов');
                }
                if (field.type === 'file' && field.files.length > 0 && field.files[0].size > 5 * 1024 * 1024) {
                    problems.push('Файл слишком большой, максимум 5 МБ');
                }
            });

            if (problems.length > 0) {
                e.preventDefault();
                alert(problems[0]);
            }
        });
    }

    var section = document.querySelector('[data-search-url]');
    var input = document.getElementById('search-input');
    var grid = document.getElementById('catalog-grid');
    var loading = document.getElementById('loading');

    if (section && input && grid && loading) {
        var searchUrl = section.getAttribute('data-search-url');
        var buyUrl = section.getAttribute('data-buy-url');
        var detailUrl = section.getAttribute('data-detail-url');
        var startCards = grid.innerHTML;
        var timer = null;

        var makeText = function (tag, className, text) {
            var node = document.createElement(tag);
            node.className = className;
            node.textContent = text;
            return node;
        };

        var makeCard = function (item) {
            var card = document.createElement('article');
            card.className = 'card';

            var imageBox = document.createElement('div');
            imageBox.className = 'card-image';

            if (item.photo) {
                var img = document.createElement('img');
                img.src = item.photo;
                img.alt = item.name;
                img.width = 300;
                img.height = 300;
                img.loading = 'lazy';
                imageBox.appendChild(img);
            } else {
                imageBox.appendChild(makeText('div', 'no-photo', 'Нет фото'));
            }

            var body = document.createElement('div');
            body.className = 'card-body';

            var title = document.createElement('h3');
            var link = document.createElement('a');
            link.className = 'card-link';
            link.href = detailUrl.replace('/0/', '/' + item.id + '/');
            link.textContent = item.name;
            title.appendChild(link);

            var price = makeText('p', 'price', item.price + ' \u20BD');

            var buy = document.createElement('a');
            buy.className = 'btn-buy card-btn';
            buy.href = buyUrl.replace('/0/', '/' + item.id + '/');
            buy.textContent = 'В корзину';

            body.appendChild(title);
            body.appendChild(price);
            body.appendChild(buy);
            card.appendChild(imageBox);
            card.appendChild(body);

            return card;
        };

        input.addEventListener('input', function () {
            clearTimeout(timer);
            timer = setTimeout(function () {
                var text = input.value.trim();

                if (text === '') {
                    grid.innerHTML = startCards;
                    loading.hidden = true;
                    return;
                }

                loading.hidden = false;

                fetch(searchUrl + '?q=' + encodeURIComponent(text))
                    .then(function (response) { return response.json(); })
                    .then(function (data) {
                        loading.hidden = true;
                        grid.innerHTML = '';

                        if (data.bouquets.length === 0) {
                            var empty = document.createElement('div');
                            empty.className = 'empty-state';
                            empty.appendChild(makeText('p', '', 'По вашему запросу ничего не найдено'));
                            grid.appendChild(empty);
                            return;
                        }

                        data.bouquets.forEach(function (item) {
                            grid.appendChild(makeCard(item));
                        });
                    })
                    .catch(function () {
                        loading.hidden = true;
                    });
            }, 300);
        });
    }

    var cartBox = document.querySelector('.cart-box');

    if (cartBox) {
        var totals = document.querySelectorAll('.cart-sum');

        cartBox.addEventListener('click', function (e) {
            var link = e.target.closest('[data-action]');
            if (!link) {
                return;
            }

            e.preventDefault();

            fetch(link.href, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    if (!data.ok) {
                        return;
                    }

                    if (data.removed) {
                        var row = cartBox.querySelector('[data-item="' + data.item + '"]');
                        if (row) {
                            row.remove();
                        }
                    } else {
                        var counter = cartBox.querySelector('[data-item="' + data.item + '"] .qty-value');
                        if (counter) {
                            counter.textContent = data.count;
                        }
                    }

                    totals.forEach(function (node) {
                        node.textContent = data.total + ' \u20BD';
                    });

                    if (!cartBox.querySelector('[data-item]')) {
                        window.location.reload();
                    }
                });
        });
    }
});
