"use strict";

(function () {
    const root = document.getElementById("appRoot");
    if (!root) {
        return;
    }

    const SAMPLE_DATA = safeParseJson(root.dataset.sample, {});

    const ruleListEl = document.getElementById("ruleList");
    const factsInput = document.getElementById("factsInput");
    const goalsInput = document.getElementById("goalsInput");
    const statusBox = document.getElementById("statusBox");
    const summaryBadges = document.getElementById("summaryBadges");
    const historyTable = document.getElementById("historyTable");
    const stepsList = document.getElementById("stepsList");
    const forwardResult = document.getElementById("forwardResult");
    const backwardResult = document.getElementById("backwardResult");
    const graphViewer = document.getElementById("graphViewer");
    const graphTabs = document.getElementById("graphTabs");
    const graphDeck = document.getElementById("graphDeck");
    const runBtn = document.getElementById("btnRun");
    const resetBtn = document.getElementById("btnReset");
    const sampleBtn = document.getElementById("btnSample");
    const addRuleBtn = document.getElementById("btnAddRule");
    const clearRulesBtn = document.getElementById("btnClearRules");

    const GRAPH_LABELS = {
        fpg: "Đồ thị FPG",
        rpg: "Đồ thị RPG",
    };

    let graphState = {
        activeTab: null,
        tabs: [],
        sources: {},
    };

    let rulesState = [];

    function safeParseJson(raw, fallback) {
        if (!raw) {
            return fallback;
        }
        try {
            return JSON.parse(raw);
        } catch (error) {
            return fallback;
        }
    }

    function handleRulePaste(event) {
        const clipboard =
            event.clipboardData?.getData("text") ||
            window.clipboardData?.getData("text");
        if (!clipboard) {
            return;
        }

        const segments = clipboard
            .split(/\r?\n|;/)
            .map((segment) => segment.trim())
            .filter((segment) => segment.length > 0);

        const row = event.target.closest(".rule-item");
        if (!row) {
            return;
        }
        const index = Number(row.dataset.index || 0);

        if (segments.length <= 1) {
            setTimeout(() => {
                rulesState[index] = event.target.value.trim();
            }, 0);
            return;
        }

        event.preventDefault();
        rulesState.splice(index, 1, segments[0]);
        for (let i = 1; i < segments.length; i += 1) {
            rulesState.splice(index + i, 0, segments[i]);
        }
        renderRuleList();
    }

    function createRuleRow(index, value) {
        const row = document.createElement("div");
        row.className = "rule-item";
        row.dataset.index = String(index);

        const label = document.createElement("span");
        label.className = "rule-label";
        label.textContent = `R${index + 1}`;

        const input = document.createElement("input");
        input.className = "rule-input";
        input.type = "text";
        input.value = value;
        input.placeholder = "a ^ b -> c";
        input.addEventListener("input", () => {
            rulesState[index] = input.value.trim();
        });
        input.addEventListener("paste", handleRulePaste);

        const removeBtn = document.createElement("button");
        removeBtn.type = "button";
        removeBtn.className = "btn-icon";
        removeBtn.title = "Xóa luật này";
        removeBtn.innerHTML = "&times;";
        removeBtn.addEventListener("click", () => {
            removeRule(index);
        });

        row.appendChild(label);
        row.appendChild(input);
        row.appendChild(removeBtn);
        return row;
    }

    function renderRuleList() {
        ruleListEl.innerHTML = "";
        if (!rulesState.length) {
            const empty = document.createElement("div");
            empty.className = "graph-placeholder";
            empty.textContent = "Chưa có luật. Thêm luật mới hoặc tải dữ liệu mẫu.";
            ruleListEl.appendChild(empty);
            return;
        }
        rulesState.forEach((value, idx) => {
            const row = createRuleRow(idx, value);
            ruleListEl.appendChild(row);
        });
    }

    function addRule(value = "") {
        rulesState.push(value);
        renderRuleList();
    }

    function removeRule(index) {
        rulesState.splice(index, 1);
        renderRuleList();
    }

    function loadSample() {
        rulesState = [...(SAMPLE_DATA.rules || [])];
        factsInput.value = (SAMPLE_DATA.facts || []).join(", ");
        goalsInput.value = (SAMPLE_DATA.goals || []).join(", ");
        document.querySelector('input[name="mode"][value="forward"]').checked = true;
        document.querySelector('input[name="structure"][value="stack"]').checked = true;
        document.querySelector('input[name="forwardIndexMode"][value="min"]').checked = true;
        document.querySelector('input[name="backwardIndexMode"][value="min"]').checked = true;
        updateOptionVisibility();
        renderRuleList();
        setStatus("Đã tải dữ liệu mẫu tam giác. Bạn có thể chỉnh sửa và chạy suy diễn.", "info");
        clearResults();
    }

    function clearResults() {
        summaryBadges.innerHTML = "";
        forwardResult.hidden = true;
        backwardResult.hidden = true;
        historyTable.innerHTML = "<tr><td colspan=\"7\" style=\"text-align:center; padding:18px;\">Chưa có dữ liệu.</td></tr>";
        stepsList.textContent = "Chưa có dữ liệu.";
        showGraphPlaceholder("Chưa có dữ liệu.");
    }

    function resetAll() {
        rulesState = [""];
        factsInput.value = "";
        goalsInput.value = "";
        document.querySelector('input[name="mode"][value="forward"]').checked = true;
        document.querySelector('input[name="structure"][value="stack"]').checked = true;
        document.querySelector('input[name="forwardIndexMode"][value="min"]').checked = true;
        document.querySelector('input[name="backwardIndexMode"][value="min"]').checked = true;
        updateOptionVisibility();
        renderRuleList();
        clearResults();
        setStatus("Đã đặt lại dữ liệu. Nhập luật và giả thiết để bắt đầu.", "info");
    }

    function setStatus(message, type = "info") {
        statusBox.textContent = message;
        statusBox.className = `status status-${type}`;
    }

    function parseAtoms(text) {
        if (!text) {
            return [];
        }
        return text
            .split(/\s*(?:,|&|\?|\^|and)\s*/i)
            .map((token) => token.trim())
            .filter(Boolean);
    }

    function gatherPayload() {
        const mode = document.querySelector('input[name="mode"]:checked').value;

        const payload = {
            mode,
            rules: rulesState.filter((rule) => rule.trim().length > 0),
            facts: parseAtoms(factsInput.value),
            goals: parseAtoms(goalsInput.value),
            options: {},
        };

        let indexMode;
        if (mode === "forward") {
            payload.options.structure = document.querySelector('input[name="structure"]:checked').value;
            indexMode = document.querySelector('input[name="forwardIndexMode"]:checked').value;
        } else {
            indexMode = document.querySelector('input[name="backwardIndexMode"]:checked').value;
        }
        payload.options.index_mode = indexMode;

        return payload;
    }

    async function runInference() {
        const payload = gatherPayload();

        if (!payload.rules.length) {
            setStatus("Vui lòng nhập ít nhất một luật.", "warn");
            return;
        }
        if (!payload.facts.length) {
            setStatus("Vui lòng nhập tối thiểu một giả thiết (GT).", "warn");
            return;
        }
        if (!payload.goals.length) {
            setStatus("Vui lòng nhập ít nhất một mục tiêu (KL).", "warn");
            return;
        }

        runBtn.disabled = true;
        setStatus("Đang thực thi suy diễn, vui lòng đợi...", "info");

        try {
            const response = await fetch("/lab/api/infer", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (!response.ok || !data.ok) {
                throw new Error(data.error || "Không thể thực thi suy diễn.");
            }

            displayResults(data);
        } catch (error) {
            setStatus(error.message || "Đã xảy ra lỗi không xác định.", "failure");
            clearResults();
        } finally {
            runBtn.disabled = false;
        }
    }

    function displayResults(data) {
        const result = data.result;
        const success = result.success;
        setStatus(success ? "Thành công! Đã đạt mục tiêu." : "Không đạt mục tiêu.", success ? "success" : "failure");

        renderSummaryBadges(data.mode, result);

        if (data.mode === "forward") {
            forwardResult.hidden = false;
            backwardResult.hidden = true;
            renderForwardHistory(result.history);
        } else {
            forwardResult.hidden = true;
            backwardResult.hidden = false;
            renderBackwardSteps(result.steps);
        }

        configureGraphTabs(data.mode, result.graphs || {});
    }

    function renderSummaryBadges(mode, result) {
        summaryBadges.innerHTML = "";
        const badgeGroups = [];
        const goals = result.goals || [];

        if (goals.length) {
            badgeGroups.push({
                title: "Mục tiêu",
                className: "badge-goal",
                items: goals,
            });
        }

        if (mode === "forward") {
            badgeGroups.push({
                title: "Sự kiện cuối",
                className: "badge-fact",
                items: result.finalFacts || [],
            });
            badgeGroups.push({
                title: "Luật đã bắn (VET)",
                className: "badge-rule",
                items: (result.firedRules || []).map((r) => `R${r}`),
            });
        } else {
            badgeGroups.push({
                title: "Sự kiện biết cuối",
                className: "badge-fact",
                items: result.finalKnown || [],
            });
            badgeGroups.push({
                title: "Luật sử dụng",
                className: "badge-rule",
                items: (result.usedRules || []).map((r) => `R${r}`),
            });
        }

        badgeGroups.forEach((group, index) => {
            const fragment = document.createElement("div");
            fragment.style.display = "grid";
            fragment.style.gridTemplateColumns = "auto 1fr";
            fragment.style.gap = "8px 14px";
            fragment.style.alignItems = "start";

            const title = document.createElement("strong");
            title.textContent = group.title;
            title.style.fontSize = "0.92rem";
            title.style.color = "#64748b";
            title.style.fontWeight = "700";
            title.style.whiteSpace = "nowrap";
            fragment.appendChild(title);

            const row = document.createElement("div");
            row.className = "badge-row";
            if (group.className === "badge-rule") {
                row.classList.add("vertical");
            }
            if (!group.items.length) {
                const badge = document.createElement("span");
                badge.className = "badge";
                badge.textContent = "∅";
                row.appendChild(badge);
            } else {
                group.items.forEach((item, idx) => {
                    const badge = document.createElement("span");
                    badge.className = `badge ${group.className}`;
                    badge.textContent = item;
                    badge.style.animationDelay = `${idx * 0.05}s`;
                    row.appendChild(badge);
                });
            }
            fragment.appendChild(row);
            summaryBadges.appendChild(fragment);
        });
    }

    function renderForwardHistory(history) {
        if (!history || !history.length) {
            historyTable.innerHTML = "<tr><td colspan=\"7\" style=\"text-align:center; padding:18px;\">Không có nhật ký để hiển thị.</td></tr>";
            return;
        }
        historyTable.innerHTML = "";
        history.forEach((trace) => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td>${trace.step}</td>
                <td>${trace.rule ? `R${trace.rule}` : '-'}</td>
                <td>${formatRuleList(trace.thoa)}</td>
                <td>${formatAtomList(trace.known)}</td>
                <td>${formatRuleList(trace.remaining)}</td>
                <td>${formatRuleList(trace.fired)}</td>
                <td>${trace.note || ''}</td>
            `;
            historyTable.appendChild(row);
        });
    }

    function renderBackwardSteps(steps) {
        if (!steps || !steps.length) {
            stepsList.textContent = "Không có nhật ký để hiển thị.";
            return;
        }
        const list = document.createElement("ol");
        list.style.margin = "0";
        list.style.paddingLeft = "18px";
        steps.forEach((step) => {
            const item = document.createElement("li");
            item.textContent = step;
            list.appendChild(item);
        });
        stepsList.innerHTML = "";
        stepsList.appendChild(list);
    }

    function formatRuleList(rules) {
        if (!rules || !rules.length) {
            return "∅";
        }
        return rules.map((r) => (typeof r === "number" ? `R${r}` : r)).join(", ");
    }

    function formatAtomList(atoms) {
        if (!atoms || !atoms.length) {
            return "∅";
        }
        return atoms.join(", ");
    }

    function updateOptionVisibility() {
        const mode = document.querySelector('input[name="mode"]:checked').value;
        document.querySelectorAll("[data-options]").forEach((el) => {
            el.hidden = el.dataset.options !== mode;
        });
    }

    function configureGraphTabs(mode, graphs) {
        graphTabs.innerHTML = "";
        graphDeck.innerHTML = "";
        graphState.activeTab = null;
        graphState.tabs = [];
        graphState.sources = {};

        const availableTabs = [];

        if (graphs.fpg) {
            availableTabs.push({ id: "fpg", label: GRAPH_LABELS.fpg, src: graphs.fpg });
        }
        if (mode === "forward" && graphs.rpg) {
            availableTabs.push({ id: "rpg", label: GRAPH_LABELS.rpg, src: graphs.rpg });
        }

        if (!availableTabs.length) {
            showGraphPlaceholder("Chưa có dữ liệu.");
            return;
        }

        graphState.tabs = availableTabs;
        graphState.sources = Object.fromEntries(availableTabs.map((tab) => [tab.id, tab.src]));
        graphState.activeTab = availableTabs[0].id;

        availableTabs.forEach((tab) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "graph-tab";
            button.dataset.tab = tab.id;
            button.textContent = tab.label;
            button.addEventListener("click", () => {
                if (graphState.activeTab === tab.id) {
                    return;
                }
                graphState.activeTab = tab.id;
                renderActiveGraph();
            });
            graphTabs.appendChild(button);
        });

        renderActiveGraph();
    }

    function renderActiveGraph() {
        const { activeTab, tabs, sources } = graphState;
        graphTabs.querySelectorAll(".graph-tab").forEach((button) => {
            const isActive = button.dataset.tab === activeTab;
            button.classList.toggle("is-active", isActive);
            button.setAttribute("aria-selected", isActive ? "true" : "false");
        });

        graphDeck.innerHTML = "";

        const active = tabs.find((tab) => tab.id === activeTab);
        if (!active) {
            showGraphPlaceholder("Chưa có dữ liệu.");
            return;
        }

        const src = sources[active.id];
        if (!src) {
            showGraphPlaceholder("Không có dữ liệu.");
            return;
        }

        const card = document.createElement("div");
        card.className = "graph-card is-active";

        // Controls
        const controls = document.createElement("div");
        controls.className = "graph-controls";

        const primaryGroup = document.createElement("div");
        primaryGroup.className = "graph-controls-group";

        const zoomInBtn = createControlButton("+", "zoom-in");
        const zoomOutBtn = createControlButton("−", "zoom-out");
        const fitBtn = createControlButton("Vừa khung", "fit");
        const resetBtn = createControlButton("100%", "reset");
        const zoomLevel = document.createElement("span");
        zoomLevel.className = "graph-zoom-level";
        zoomLevel.textContent = "100%";
        zoomLevel.dataset.zoomLevel = "";

        primaryGroup.append(fitBtn, zoomOutBtn, resetBtn, zoomInBtn, zoomLevel);
        controls.appendChild(primaryGroup);
        card.appendChild(controls);

        // Frame
        const frame = document.createElement("div");
        frame.className = "graph-frame";
        frame.dataset.graphFrame = "";

        const container = document.createElement("div");
        container.className = "graph-container";

        const img = document.createElement("img");
        img.src = `${src}?t=${Date.now()}`;
        img.alt = active.label;
        img.dataset.graphImg = "";
        img.draggable = false;
        img.style.display = "block";
        img.style.margin = "0";
        // no extra padding to maximize visible area
        container.appendChild(img);
        frame.appendChild(container);
        card.appendChild(frame);
        graphDeck.appendChild(card);

        initGraphZoom(card, img, zoomLevel);
    }

    function createControlButton(label, action) {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "graph-ctrl-btn";
        btn.textContent = label;
        btn.dataset.action = action;
        return btn;
    }

    function initGraphZoom(card, img, zoomDisplay) {
        let scale = 1;
        let baseWidth = 0;
        let baseHeight = 0;
        const minScale = 0.3;
        const maxScale = 4;

        function applyScale() {
            if (!baseWidth) return;
            img.style.width = `${Math.max(1, Math.round(baseWidth * scale))}px`;
            img.style.height = `${Math.max(1, Math.round(baseHeight * scale))}px`;
            if (zoomDisplay) {
                zoomDisplay.textContent = `${Math.round(scale * 100)}%`;
            }
        }

        function updateZoom(newScale) {
            scale = Math.max(minScale, Math.min(maxScale, newScale));
            applyScale();
        }

        function fitToFrame() {
            const frame = card.querySelector("[data-graph-frame]");
            if (!frame || !baseWidth || !baseHeight) {
                scale = 1;
            } else {
                const rect = frame.getBoundingClientRect();
                const container = img.parentElement;
                const csC = container ? getComputedStyle(container) : null;
                const csI = getComputedStyle(img);
                const padX = (csC ? (parseFloat(csC.paddingLeft) + parseFloat(csC.paddingRight)) : 0)
                    + (parseFloat(csI.paddingLeft) + parseFloat(csI.paddingRight));
                const padY = (csC ? (parseFloat(csC.paddingTop) + parseFloat(csC.paddingBottom)) : 0)
                    + (parseFloat(csI.paddingTop) + parseFloat(csI.paddingBottom));
                const availWidth = rect.width - (isFinite(padX) ? padX : 0);
                const availHeight = rect.height - (isFinite(padY) ? padY : 0);
                const scaleX = availWidth / baseWidth;
                const scaleY = availHeight / baseHeight;
                // Fit: allow scale nhỏ hơn minScale để luôn nhìn trọn vẹn
                scale = Math.min(scaleX, scaleY);
            }
            applyScale();
        }

        img.addEventListener("load", () => {
            baseWidth = img.naturalWidth || img.width;
            baseHeight = img.naturalHeight || img.height;
            // Fit once image sizes are known and frame is in layout
            requestAnimationFrame(() => {
                fitToFrame();
            });
        });

        // Refit on window resize to keep full view without scrolling
        window.addEventListener("resize", () => {
            fitToFrame();
        });

        card.addEventListener("click", (e) => {
            const btn = e.target.closest("[data-action]");
            if (!btn) return;
            e.preventDefault();
            const action = btn.dataset.action;
            switch (action) {
                case "zoom-in":
                    updateZoom(scale * 1.2);
                    break;
                case "zoom-out":
                    updateZoom(scale / 1.2);
                    break;
                case "fit":
                    fitToFrame();
                    break;
                case "reset":
                    updateZoom(1);
                    break;
            }
        });

        const frame = card.querySelector("[data-graph-frame]");
        if (frame) {
            frame.addEventListener("wheel", (e) => {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    updateZoom(scale * delta);
                }
            }, { passive: false });
        }
    }

    function showGraphPlaceholder(message) {
        graphTabs.innerHTML = "";
        graphDeck.innerHTML = "";
        const placeholder = document.createElement("div");
        placeholder.className = "graph-placeholder-message";
        placeholder.textContent = message;
        graphDeck.appendChild(placeholder);
    }

    document
        .querySelectorAll('input[name="mode"]')
        .forEach((radio) => radio.addEventListener("change", updateOptionVisibility));
    runBtn.addEventListener("click", runInference);
    resetBtn.addEventListener("click", () => {
        resetAll();
    });
    sampleBtn.addEventListener("click", () => {
        loadSample();
    });
    addRuleBtn.addEventListener("click", () => addRule(""));
    clearRulesBtn.addEventListener("click", () => {
        rulesState = [];
        renderRuleList();
    });

    loadSample();
})();

