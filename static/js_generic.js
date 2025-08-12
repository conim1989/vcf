// Generic JavaScript code

// Global State & Element References
const vcfPathInput = document.getElementById('vcf-path');
const startBtn = document.getElementById('start-btn');
const logArea = document.getElementById('log-area');
const initialForm = document.getElementById('initial-form');
const duplicateSelectionDiv1 = document.getElementById('duplicate-selection-1');
const duplicateSelectionDiv2 = document.getElementById('duplicate-selection-2');
const duplicatesForm = document.getElementById('duplicates-form');
const duplicatesList = document.getElementById('duplicates-list');
const titlesList = document.getElementById('filtered-titles-list');
const newTitleInput = document.getElementById('new-title-input');
const addTitleBtn = document.getElementById('add-title-btn');
const advancedPanel = document.getElementById('advanced-panel');
const selectAllBtn = document.getElementById('select-all-btn');
const selectNoneBtn = document.getElementById('select-none-btn');
const submitButton = document.getElementById('submit-button');
const viewLogBtn = document.getElementById('view-log-btn');
const browseVcfBtn = document.getElementById('browse-vcf-btn');
const advancedToggleLink = document.getElementById('advanced-toggle-link');
const closeBtn = document.getElementById('close-btn');
const minimizeBtn = document.getElementById('minimize-btn');
const titlebar = document.getElementById('titlebar');

// State Management
let state = {
    isLoading: false,
    isProcessing: false,
    showAdvanced: false,
    vcfPath: vcfPathInput.value,
    duplicates: [],
    filteredTitles: [],
    logMessages: [],
    error: null
};

function setState(newState) {
    state = { ...state, ...newState };
    render(state);
}

// Helper Functions
function logMessage(message) {
    const newLogMessages = [...state.logMessages, message];
    setState({ logMessages: newLogMessages });
}

// Render Function
function render(state) {
    vcfPathInput.value = state.vcfPath;

    const showInitialForm = !state.isLoading && !state.isProcessing && state.duplicates.length === 0;
    const showDuplicateSelection = state.duplicates.length > 0 && !state.isProcessing;

    initialForm.style.display = showInitialForm ? 'block' : 'none';
    duplicateSelectionDiv1.style.display = showDuplicateSelection ? 'block' : 'none';
    duplicateSelectionDiv2.style.display = showDuplicateSelection ? 'block' : 'none';

    startBtn.disabled = state.isLoading || state.isProcessing || !state.vcfPath;
    selectAllBtn.disabled = state.isLoading || state.isProcessing || state.duplicates.length === 0;
    selectNoneBtn.disabled = state.isLoading || state.isProcessing || state.duplicates.length === 0;
    browseVcfBtn.disabled = state.isLoading || state.isProcessing;
    addTitleBtn.disabled = state.isLoading || state.isProcessing;
    viewLogBtn.disabled = state.isLoading || state.isProcessing;
    newTitleInput.disabled = state.isLoading || state.isProcessing;

    const checkedCheckboxes = duplicatesList.querySelectorAll('input[type="checkbox"]:checked').length;
    if (state.duplicates.length > 0 && !state.isProcessing) {
        if (checkedCheckboxes > 0) {
            submitButton.textContent = 'Processar Selecionados';
            submitButton.disabled = state.isLoading || state.isProcessing;
        } else {
            submitButton.textContent = 'Pular';
            submitButton.disabled = state.isLoading || state.isProcessing;
        }
    } else {
        submitButton.textContent = 'Processar Selecionados';
        submitButton.disabled = true;
    }

    duplicatesList.innerHTML = '';
    if (state.duplicates.length > 0) {
        state.duplicates.forEach((contact, index) => {
            const div = document.createElement('div');
            div.className = 'duplicate-item';
            div.innerHTML = `<input type="checkbox" id="dup-${index}" name="selected_duplicates" data-contact='${JSON.stringify(contact)}'><label for="dup-${index}">${contact.original_name} (${contact.cleaned_number})</label>`;
            duplicatesList.appendChild(div);
        });
    }

    titlesList.innerHTML = '';
    if (state.filteredTitles.length > 0) {
        state.filteredTitles.forEach(title => {
            const li = document.createElement('li');
            li.textContent = title;
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = '×';
            deleteBtn.className = 'delete-title-btn';
            li.appendChild(deleteBtn);
            titlesList.appendChild(li);
        });
    }

    advancedPanel.classList.toggle('visible', state.showAdvanced);

    logArea.style.display = state.logMessages.length > 0 ? 'block' : 'none';
    logArea.innerHTML = state.logMessages.join('<br>');
    logArea.scrollTop = logArea.scrollHeight;
}

// Light effects management
let lightMode = 'follow';

function updateLightPosition() {
    let light = document.querySelector('.light');
    if (!light) {
        light = document.createElement('div');
        light.className = 'light';
        document.body.appendChild(light);
    }
    if (lightMode === 'static') {
        light.style.left = `${window.innerWidth / 2}px`;
        light.style.top = `${window.innerHeight / 2}px`;
    }
}

document.addEventListener('mousemove', (e) => {
    let light = document.querySelector('.light');
    if (!light) {
        light = document.createElement('div');
        light.className = 'light';
        document.body.appendChild(light);
    }
    if (lightMode === 'follow') {
        light.style.left = `${e.clientX}px`;
        light.style.top = `${e.clientY}px`;
    }
    document.querySelectorAll('*').forEach(el => {
        const rect = el.getBoundingClientRect();
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const lightX = (lightMode === 'follow') ? e.clientX : window.innerWidth / 2;
        const lightY = (lightMode === 'follow') ? e.clientY : window.innerHeight / 2;
        const dx = centerX - lightX;
        const dy = centerY - lightY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const offsetX = dist > 0 ? (dx / dist) * 2 : 0;
        const offsetY = dist > 0 ? (dy / dist) * 2 : 0;
        el.style.textShadow = `${offsetX}px ${offsetY}px 5px rgba(0,0,0,0.5)`;
        if(el.classList.contains('input-style') || el.classList.contains('advanced-panel')) {
            el.style.boxShadow = `${offsetX}px ${offsetY}px 10px rgba(0,0,0,0.3)`;
        }
    });
});

if (lightMode === 'static') updateLightPosition();
