document.addEventListener('DOMContentLoaded', function () {
    var burger = document.getElementById('burger-btn');
    var nav = document.getElementById('main-nav');

    if (burger && nav) {
        burger.addEventListener('click', function () {
            nav.classList.toggle('open');
        });
    }

    var email = document.querySelector('input[type="email"]');
    var pass1 = document.querySelector('input[name="password1"]');
    var pass2 = document.querySelector('input[name="password2"]');
    var form = document.querySelector('form[method="POST"]');

    if (form && (email || pass1)) {
        form.addEventListener('submit', function (e) {
            if (email && email.value.indexOf('@') === -1) {
                e.preventDefault();
                alert('Введите корректный email, в нем должен быть символ @');
                return;
            }
            if (pass1 && pass1.value.length <= 5) {
                e.preventDefault();
                alert('Пароль должен быть больше 5 символов');
                return;
            }
            if (pass2 && pass1 && pass2.value !== pass1.value) {
                e.preventDefault();
                alert('Пароли не совпадают');
            }
        });
    }

    var input = document.getElementById('search-input');
    var grid = document.getElementById('catalog-grid');
    var loading = document.getElementById('loading');
    var timer = null;

    if (!input || !grid || !loading) {
        return;
    }

    var startCards = grid.innerHTML;

    input.addEventListener('input', function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
            var text = input.value.trim();

            if (text === '') {
                grid.innerHTML = startCards;
                loading.style.display = 'none';
                return;
            }

            loading.style.display = 'block';
            fetch('/api/search/?q=' + encodeURIComponent(text))
                .then(function (response) { return response.json(); })
                .then(function (data) {
                    loading.style.display = 'none';
                    grid.innerHTML = '';

                    if (data.bouquets.length === 0) {
                        grid.innerHTML = '<div class="empty-state"><p>По вашему запросу ничего не найдено</p></div>';
                        return;
                    }

                    data.bouquets.forEach(function (item) {
                        var card = document.createElement('div');
                        card.className = 'card';

                        var photo = '<div class="no-photo">Нет фото</div>';
                        if (item.photo) {
                            photo = '<img src="' + item.photo + '" alt="' + item.name + '" width="300" height="300" loading="lazy">';
                        }

                        card.innerHTML =
                            '<div class="card-image">' + photo + '</div>' +
                            '<div class="card-body">' +
                                '<h3>' + item.name + '</h3>' +
                                '<p class="price">' + Number(item.price).toFixed(2) + ' ₽' + '</p>' +
                                '<a href="/buy/' + item.id + '/" class="btn-buy card-btn">В корзину</a>' +
                            '</div>';

                        grid.appendChild(card);
                    });
                })
                .catch(function () {
                    loading.style.display = 'none';
                });
        }, 300);
    });
});
