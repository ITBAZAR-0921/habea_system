(function () {
    'use strict';

    const formsetPrefix = 'materials';

    function initSelect2() {
        if (!window.jQuery || !jQuery.fn.select2) {
            return;
        }

        jQuery('.select2-multi').select2({
            width: '100%',
            closeOnSelect: false,
            allowClear: true,
            placeholder: 'Сонгох',
        });
    }

    // Initialize TinyMCE only for material text fields.
    function initMaterialEditor(targetTextareas) {
        if (!window.tinymce) {
            return;
        }

        const fields = targetTextareas || document.querySelectorAll('textarea.material-text-rich');
        fields.forEach(function (field) {
            if (!field.id || tinymce.get(field.id)) {
                return;
            }

            tinymce.init({
                target: field,
                menubar: false,
                statusbar: false,
                height: 300,
                mobile: { toolbar_mode: 'sliding' },
                plugins: 'lists',
                toolbar: 'undo redo | blocks | bold italic | bullist numlist',
                block_formats: 'Paragraph=p; Heading 1=h1; Heading 2=h2; Heading 3=h3;',
            });
        });
    }

    function updateMaterialCardNumbers() {
        const cards = document.querySelectorAll('#materials-container .material-item:not(.d-none)');
        cards.forEach(function (card, index) {
            const title = card.querySelector('strong');
            if (title) {
                title.textContent = 'Материал ' + (index + 1);
            }
        });
    }

    function removeMaterialCard(card) {
        const deleteInput = card.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteInput) {
            deleteInput.checked = true;
            card.classList.add('d-none');
        } else {
            card.remove();
        }

        updateMaterialCardNumbers();
    }

    function addMaterialCard() {
        const totalFormsInput = document.getElementById('id_' + formsetPrefix + '-TOTAL_FORMS');
        const template = document.getElementById('material-card-template');
        const container = document.getElementById('materials-container');
        if (!totalFormsInput || !template || !container) {
            return;
        }

        const index = parseInt(totalFormsInput.value, 10);
        let html = template.innerHTML;
        html = html.replace(/__prefix__/g, String(index));
        html = html.replace(/__number__/g, String(index + 1));

        container.insertAdjacentHTML('beforeend', html);
        totalFormsInput.value = String(index + 1);

        const newCard = container.lastElementChild;
        const newEditors = newCard ? newCard.querySelectorAll('textarea.material-text-rich') : [];
        initMaterialEditor(newEditors);
        updateMaterialCardNumbers();
    }

    function bindEvents() {
        const container = document.getElementById('materials-container');
        const addButton = document.getElementById('add-material-btn');

        if (container) {
            container.addEventListener('click', function (event) {
                const removeButton = event.target.closest('.remove-material-btn');
                if (!removeButton) {
                    return;
                }

                const card = removeButton.closest('.material-item');
                if (card) {
                    removeMaterialCard(card);
                }
            });
        }

        if (addButton) {
            addButton.addEventListener('click', addMaterialCard);
        }
    }

    function init() {
        initSelect2();
        initMaterialEditor();
        updateMaterialCardNumbers();
        bindEvents();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
