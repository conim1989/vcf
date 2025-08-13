// App-specific JavaScript code

// Fetch and display titles from server
async function fetchAndDisplayTitles() {
    try {
        const response = await fetch('/get_titles');
        const data = await response.json();
        setState({ filteredTitles: data.titles });
    } catch (e) {
        console.error("Failed to fetch titles:", e);
        logMessage(`Erro ao carregar títulos: ${e.message}`);
    }
}

// Save titles to server
async function saveTitles() {
    setState({ isLoading: true });
    const currentTitles = state.filteredTitles;
    try {
        await fetch('/save_titles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ titles: currentTitles })
        });
        logMessage("Lista de títulos filtrados atualizada.");
    } catch (e) {
        logMessage(`Erro ao salvar títulos: ${e.message}`);
    } finally {
        setState({ isLoading: false });
    }
}

// Continue processing selected duplicates
async function continueProcessing(selected_duplicates) {
    setState({ isProcessing: true, duplicates: [], logMessages: [] });
    logMessage(`Continuando com ${selected_duplicates.length} duplicatas selecionadas...`);
    try {
        const response = await fetch('/reprocess_selected', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selected_to_reprocess: selected_duplicates })
        });
        const data = await response.json();
        if (response.ok) {
            if (data.output_file && data.output_file !== "None") {
                logMessage(`<strong>${data.message}</strong> Arquivo de saída: <a href="#" class="output-link" data-path="${data.output_file}">${data.output_file}</a>`);
            } else {
                logMessage(`<strong>${data.message}</strong> Nenhum arquivo de saída foi criado.`);
            }
        } else {
            throw new Error(data.error || 'An unknown server error occurred.');
        }
    } catch (error) {
        logMessage(`Erro: ${error.message}`);
    } finally {
        setState({ isProcessing: false, duplicates: [] });
    }
}

// Show duplicate selector and log message
function showDuplicateSelector(duplicates) {
    setState({ duplicates: duplicates });
    logMessage(`Encontradas ${duplicates.length} duplicatas. Por favor, faça sua seleção.`);
    
    // Optimize for large lists
    if (duplicates.length > 500) {
        requestAnimationFrame(() => {
            const style = document.createElement('style');
            style.textContent = `
                .duplicates-list { 
                    height: 400px; 
                    overflow-y: auto; 
                    contain: layout style paint;
                }
                .duplicate-item { 
                    height: 40px; 
                    display: flex; 
                    align-items: center;
                }
            `;
            document.head.appendChild(style);
        });
    }
}

// Update submit button text based on checked checkboxes
function updateSubmitButtonText() {
    const checkedCheckboxes = duplicatesList.querySelectorAll('input[type="checkbox"]:checked').length;
    if (checkedCheckboxes > 0) {
        submitButton.textContent = 'Processar Selecionados';
    } else {
        submitButton.textContent = 'Pular';
    }
}

// Event listeners setup after DOM ready
window.addEventListener('pywebviewready', () => {
    fetch('/get_light_mode')
        .then(response => response.json())
        .then(data => {
            lightMode = data.lightMode;
            document.getElementById('lightModeSwitch').checked = (lightMode === 'follow');
            updateLightPosition();
        });

    fetchAndDisplayTitles();
    render(state);

    titlesList.addEventListener('click', (e) => {
        if (e.target.classList.contains('delete-title-btn')) {
            const titleToRemove = e.target.parentElement.firstChild.textContent;
            setState({ filteredTitles: state.filteredTitles.filter(title => title !== titleToRemove) });
            saveTitles();
        }
    });

    addTitleBtn.addEventListener('click', () => {
        const newTitle = newTitleInput.value.trim();
        if (newTitle && !state.filteredTitles.includes(newTitle)) {
            setState({ filteredTitles: [...state.filteredTitles, newTitle] });
            newTitleInput.value = '';
            saveTitles();
        }
    });

    newTitleInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            const newTitle = newTitleInput.value.trim();
            if (newTitle && !state.filteredTitles.includes(newTitle)) {
                setState({ filteredTitles: [...state.filteredTitles, newTitle] });
                newTitleInput.value = '';
                await saveTitles();
                newTitleInput.focus();
                newTitleInput.select();
            }
        }
    });

    duplicatesList.addEventListener('change', (e) => {
        if (e.target.tagName === 'INPUT' && e.target.type === 'checkbox') {
            updateSubmitButtonText();
        }
    });

    duplicatesList.addEventListener('click', (e) => {
        const duplicateItem = e.target.closest('.duplicate-item');
        if (duplicateItem && !e.target.classList.contains('delete-title-btn') && e.target.tagName !== 'INPUT') {
            const checkbox = duplicateItem.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                updateSubmitButtonText();
            }
        }
    });

    submitButton.addEventListener('click', async (e) => {
        e.preventDefault();
        const checkedCheckboxes = duplicatesList.querySelectorAll('input[type="checkbox"]:checked');
        if (checkedCheckboxes.length > 0) {
            const selected_to_reprocess = Array.from(checkedCheckboxes)
                .map(cb => JSON.parse(cb.dataset.contact));
            await continueProcessing(selected_to_reprocess);
        } else {
            logMessage("Pulando processamento de duplicatas.");
            setState({ duplicates: [], isProcessing: false, isLoading: false });
        }
    });

    browseVcfBtn.addEventListener('click', async () => {
        const path = await window.pywebview.api.select_file();
        if (path && path.length > 0) {
            setState({ vcfPath: path[0] });
        }
    });

    selectAllBtn.addEventListener('click', () => {
        duplicatesList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
        updateSubmitButtonText();
    });

    selectNoneBtn.addEventListener('click', () => {
        duplicatesList.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
        updateSubmitButtonText();
    });

    startBtn.addEventListener('click', async () => {
        if (!state.vcfPath) {
            logMessage("Erro: Por favor, selecione um arquivo VCF primeiro.");
            return;
        }
        setState({ isLoading: true, logMessages: [] });
        logMessage("Iniciando processamento... Encontrando duplicatas...");
        try {
            const response = await fetch('/start_vcf_processing', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ vcf_path: state.vcfPath })
            });
            const data = await response.json();
            if (response.ok) {
                // Handle auto-processed files (exe mode)
                if (data.output_file && data.output_file !== "None") {
                    logMessage(`<strong>${data.message || 'Processing complete!'}</strong> Arquivo de saída: <a href="#" class="output-link" data-path="${data.output_file}">${data.output_file}</a>`);
                    setState({ isLoading: false, isProcessing: false, duplicates: [], vcfPath: '', error: null });
                } else if (data.duplicates && data.duplicates.length > 0) {
                    showDuplicateSelector(data.duplicates);
                    setState({ isLoading: false });
                    updateSubmitButtonText();
                } else {
                    logMessage("Nenhuma duplicata encontrada. Processando todos os contatos únicos...");
                    await continueProcessing([]);
                    setState({ isLoading: false, isProcessing: false, duplicates: [], vcfPath: '', error: null });
                }
            } else {
                throw new Error(data.error || 'An unknown server error occurred.');
            }
        } catch (error) {
            logMessage(`Erro: ${error.message}`);
            setState({ isLoading: false });
        }
    });

    viewLogBtn.addEventListener('click', async () => {
        window.pywebview.api.open_log_file_with_notepad();
    });

    logArea.addEventListener('click', (e) => {
        if (e.target.classList.contains('output-link')) {
            e.preventDefault();
            const filePath = e.target.dataset.path;
            window.pywebview.api.open_file_path(filePath);
            console.log(`Opening file: ${filePath}`);
        }
    });

    advancedToggleLink.addEventListener('click', (e) => {
        e.preventDefault();
        setState({ showAdvanced: !state.showAdvanced });
    });

    closeBtn.addEventListener('click', () => window.pywebview.api.close_window());
    minimizeBtn.addEventListener('click', () => window.pywebview.api.minimize_window());

    titlebar.addEventListener('mousedown', (e) => {
        if (e.button !== 0 || e.target.closest('.window-controls')) return;
        e.preventDefault();
        const dragOffsetX = e.screenX - window.screenX;
        const dragOffsetY = e.screenY - window.screenY;
        const originalLightMode = lightMode;
        lightMode = 'static';
        updateLightPosition();

        const onMouseMove = (ev) => window.pywebview.api.set_window_position(ev.screenX - dragOffsetX, ev.screenY - dragOffsetY);
        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            lightMode = originalLightMode;
        };
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });

    document.addEventListener('mousedown', (e) => {
        const panel = document.getElementById('advanced-panel');
        const toggle = document.getElementById('advanced-toggle-link');
        if (state.showAdvanced && !panel.contains(e.target) && !toggle.contains(e.target)) {
            setState({ showAdvanced: false });
        }
    });

    const initialDuplicatesData = JSON.parse('{{ initial_duplicates | safe }}');
    if (Array.isArray(initialDuplicatesData) && initialDuplicatesData.length > 0) {
        showDuplicateSelector(initialDuplicatesData);
        updateSubmitButtonText();
    } else if (vcfPathInput.value) {
        logMessage("Processamento sem interface concluído: Nenhuma duplicata encontrada.");
    }
});
